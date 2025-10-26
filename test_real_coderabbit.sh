#!/usr/bin/env bash
# Test with REAL CodeRabbit logic and MOCK RAG context
# Creates a temporary merge conflict similar to full_demo_run.sh

set -euo pipefail

echo "======================================================================="
echo "  TEST: Real CodeRabbit + Mock RAG Integration"
echo "======================================================================="
echo ""
echo "This test will:"
echo "  1. Create a temporary git repo with merge conflict"
echo "  2. Generate MOCK RAG context (since RAG pipeline is faulty)"
echo "  3. Run REAL CodeRabbit analysis (actual API calls)"
echo "  4. Run Claude AI resolution with real CodeRabbit + mock RAG"
echo ""

# Check for required tools
if ! command -v coderabbit &> /dev/null; then
    echo "❌ ERROR: coderabbit CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @coderabbit/cli"
    echo "  # or"
    echo "  yarn global add @coderabbit/cli"
    echo ""
    exit 1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set"
    echo ""
    echo "Set it with:"
    echo "  export ANTHROPIC_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "✅ coderabbit CLI found"
echo "✅ ANTHROPIC_API_KEY is set"
echo ""
echo "Press Enter to start..."
read

# Save original directory
ORIGINAL_DIR="$(pwd)"

# ============================================================================
# STEP 1: Create temporary git structure (similar to demo_conflict.sh)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Creating temporary git repositories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TMP_BASE="$(mktemp -d /tmp/merj-test-cr.XXXXXX)"
REMOTE="$TMP_BASE/remote.git"
WORK_MAIN="$TMP_BASE/work-main"
WORK_FEAT="$TMP_BASE/work-feature"

echo "📦 Creating bare remote at: $REMOTE"
git init --bare "$REMOTE" &>/dev/null

echo "🌱 Seeding initial commit..."
SEED="$TMP_BASE/seed"
git clone "$REMOTE" "$SEED" &>/dev/null
cd "$SEED"
git checkout -b main &>/dev/null

cat > app.txt <<'EOF'
// Base implementation
export function processData(input) {
  return input;
}

export function validateInput(data) {
  return true;
}
EOF

git add app.txt
git commit -m "initial commit" &>/dev/null
git push -u origin main &>/dev/null
cd "$TMP_BASE"

echo "✅ Initial commit created"
echo ""

echo "🧭 Cloning work repositories from common base..."
git clone "$REMOTE" "$WORK_MAIN" &>/dev/null
git clone "$REMOTE" "$WORK_FEAT" &>/dev/null

# Explicitly checkout main in both repos to ensure they have the base commit
cd "$WORK_MAIN"
git checkout main &>/dev/null
BASE_COMMIT=$(git rev-parse HEAD)

cd "$WORK_FEAT"
git checkout main &>/dev/null
FEAT_BASE=$(git rev-parse HEAD)

if [ "$BASE_COMMIT" != "$FEAT_BASE" ]; then
    echo "❌ ERROR: Repos have different base commits!"
    exit 1
fi

echo "✅ Both repos cloned from same base (commit: ${BASE_COMMIT:0:7})"
echo ""

# ============================================================================
# STEP 2: Create main branch changes
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Creating MAIN branch changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$WORK_MAIN"

cat > app.txt <<'EOF'
// MAIN BRANCH: Retry logic implementation
export async function processData(input) {
  // Add retry logic
  const maxRetries = 3;
  let attempts = 0;

  while (attempts < maxRetries) {
    try {
      const result = await fetch(input);
      return result.json();
    } catch (error) {
      attempts++;
      if (attempts >= maxRetries) throw error;
      await new Promise(r => setTimeout(r, 100));
    }
  }
}

export function validateInput(data) {
  // Add type checking
  if (typeof data !== 'object') {
    throw new Error('Input must be an object');
  }
  return data !== null;
}
EOF

git add app.txt
git commit -m "main: add retry logic and type checking" &>/dev/null
git push &>/dev/null

echo "✅ Main branch updated with retry logic"
echo ""

# ============================================================================
# STEP 3: Create feature branch changes (conflicting)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Creating FEATURE branch changes (conflicting)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$WORK_FEAT"

# Verify we're on main before creating feature branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch, checking out main first..."
    git checkout main &>/dev/null
fi

# Create feature branch from main
git checkout -b feature &>/dev/null

# Verify feature branch has the base commit in its history
if ! git log --oneline | grep -q "${BASE_COMMIT:0:7}"; then
    echo "❌ ERROR: Feature branch doesn't have base commit in history!"
    echo "Git log:"
    git log --oneline
    exit 1
fi

cat > app.txt <<'EOF'
// FEATURE BRANCH: Logging and caching implementation
import logger from './logger';

export async function processData(input) {
  // Add logging and caching
  logger.info('Processing data:', input);

  const cached = cache.get(input);
  if (cached) {
    logger.info('Cache hit');
    return cached;
  }

  const result = await computeExpensive(input);
  cache.set(input, result);
  return result;
}

export function validateInput(data) {
  // Add detailed validation with logging
  if (!data) {
    logger.error('Validation failed: null or undefined');
    return false;
  }

  if (typeof data !== 'object') {
    logger.error('Validation failed: not an object');
    return false;
  }

  return true;
}
EOF

git add app.txt
git commit -m "feature: add logging and caching" &>/dev/null

echo "✅ Feature branch created with logging and caching"
echo ""

# ============================================================================
# STEP 4: Trigger merge conflict
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Creating merge conflict"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$WORK_FEAT"

# Fetch to update our knowledge of origin/main
git fetch origin &>/dev/null

# Verify we're on feature branch and have changes
echo "📊 Current state before merge:"
echo "   Branch: $(git branch --show-current)"
echo "   Feature commits: $(git log --oneline --no-merges | wc -l | tr -d ' ')"
echo "   Origin/main commits: $(git log --oneline origin/main --no-merges | wc -l | tr -d ' ')"

# Check if there's a common ancestor
MERGE_BASE=$(git merge-base HEAD origin/main 2>/dev/null || echo "none")
if [ "$MERGE_BASE" = "none" ]; then
    echo "   ❌ No common ancestor found!"
    echo ""
    echo "   Feature history:"
    git log --oneline --all --graph | head -10
    exit 1
else
    echo "   Common ancestor: ${MERGE_BASE:0:7}"
fi
echo ""

echo "🔄 Running: git pull --no-rebase origin main"
# Use --no-rebase to force merge (not rebase)
if git pull --no-rebase origin main 2>&1; then
    echo ""
    echo "⚠️  Pull succeeded without conflict?"
else
    echo ""
    echo "Git pull exited with error (expected if conflict)"
fi

echo ""
if grep -q "<<<<<<< HEAD" app.txt 2>/dev/null; then
    echo "✅ Merge conflict created successfully!"
else
    echo "❌ ERROR: No conflict created!"
    echo ""
    echo "Debug info:"
    echo "Current branch: $(git branch --show-current)"
    echo ""
    echo "Git log (last 3 commits):"
    git log --oneline -3
    echo ""
    echo "Git status:"
    git status
    echo ""
    echo "File content:"
    cat app.txt
    exit 1
fi

echo ""
echo "📄 Conflicted file preview:"
echo "─────────────────────────────────────────"
head -20 app.txt
echo "..."
echo "─────────────────────────────────────────"
echo ""

# ============================================================================
# STEP 5: Generate MOCK RAG context
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Generating MOCK RAG context"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p rag_output

cat > rag_output/llm_context.txt <<'EOF'
============================================================
MERGE CONFLICT CONTEXT FOR LLM
============================================================

LOCAL CHANGES (Your Branch - Feature):
----------------------------------------

[1] File: app.txt
    Lines: 1-36
    Type: functions (processData, validateInput)
    Code:
    // FEATURE BRANCH: Logging and caching implementation
    import logger from './logger';

    export async function processData(input) {
      // Add logging and caching
      logger.info('Processing data:', input);

      const cached = cache.get(input);
      if (cached) {
        logger.info('Cache hit');
        return cached;
      }

      const result = await computeExpensive(input);
      cache.set(input, result);
      return result;
    }

    export function validateInput(data) {
      // Add detailed validation with logging
      if (!data) {
        logger.error('Validation failed: null or undefined');
        return false;
      }

      if (typeof data !== 'object') {
        logger.error('Validation failed: not an object');
        return false;
      }

      return true;
    }


REMOTE CHANGES (Main Branch):
----------------------------------------

[1] File: app.txt
    Lines: 1-33
    Type: functions (processData, validateInput)
    Code:
    // MAIN BRANCH: Retry logic implementation
    export async function processData(input) {
      // Add retry logic
      const maxRetries = 3;
      let attempts = 0;

      while (attempts < maxRetries) {
        try {
          const result = await fetch(input);
          return result.json();
        } catch (error) {
          attempts++;
          if (attempts >= maxRetries) throw error;
          await new Promise(r => setTimeout(r, 100));
        }
      }
    }

    export function validateInput(data) {
      // Add type checking
      if (typeof data !== 'object') {
        throw new Error('Input must be an object');
      }
      return data !== null;
    }


SIMILAR CODE PATTERNS FOUND:
----------------------------------------
  (Mock RAG - No similar patterns found in LCA codebase)

CONTEXT NOTES:
- Both branches completely rewrote processData() and validateInput()
- Main branch: Focuses on retry logic and strict type checking
- Feature branch: Focuses on logging, caching, and detailed validation
- Both implementations are async but use different approaches
EOF

echo "✅ Created mock RAG context at: rag_output/llm_context.txt"
echo "   Size: $(wc -c < rag_output/llm_context.txt) bytes"
echo ""

# ============================================================================
# STEP 6: Run REAL CodeRabbit analysis
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: Running REAL CodeRabbit analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📞 Calling scripts/review_two_sides_with_cr.py..."
echo ""

# Set MAIN_REF for the script
export MAIN_REF="origin/main"

# Run the CodeRabbit script
cd "$WORK_FEAT"
if python3 "$ORIGINAL_DIR/scripts/review_two_sides_with_cr.py" > /tmp/cr_output.txt 2>&1; then
    echo "✅ CodeRabbit analysis completed"

    # Read the output paths
    MAIN_JSON=$(sed -n '1p' /tmp/cr_output.txt)
    LOCAL_JSON=$(sed -n '2p' /tmp/cr_output.txt)

    echo "   Main review:  $MAIN_JSON"
    echo "   Local review: $LOCAL_JSON"

    # Check if files exist and copy to rag_output
    if [ -f "$MAIN_JSON" ] && [ -f "$LOCAL_JSON" ]; then
        # Create the CodeRabbit output structure
        cat > rag_output/coderabbit_review.json <<CREOF
{
  "mainBranchReview": $(cat "$MAIN_JSON"),
  "localBranchReview": $(cat "$LOCAL_JSON"),
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")"
}
CREOF

        echo "✅ Created rag_output/coderabbit_review.json"
        echo ""

        # Show preview
        echo "🐰 CodeRabbit findings preview:"
        echo "─────────────────────────────────────────"
        cat rag_output/coderabbit_review.json | head -20
        echo "..."
        echo "─────────────────────────────────────────"
    else
        echo "⚠️  WARNING: CodeRabbit JSON files not found"
        echo "   Creating empty findings..."
        cat > rag_output/coderabbit_review.json <<'CREOF'
{
  "mainBranchReview": {"issues": []},
  "localBranchReview": {"issues": []},
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")"
}
CREOF
    fi
else
    echo "⚠️  CodeRabbit analysis failed (see /tmp/cr_output.txt for details)"
    echo ""
    echo "Error output:"
    cat /tmp/cr_output.txt
    echo ""
    echo "Creating empty CodeRabbit findings to continue test..."

    mkdir -p rag_output
    cat > rag_output/coderabbit_review.json <<'CREOF'
{
  "mainBranchReview": {"issues": []},
  "localBranchReview": {"issues": []},
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")"
}
CREOF
fi

echo ""

# ============================================================================
# STEP 7: Run Claude AI resolution
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 7: Running Claude AI resolution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will use:"
echo "  ✓ REAL CodeRabbit findings from rag_output/coderabbit_review.json"
echo "  ✓ MOCK RAG context from rag_output/llm_context.txt"
echo ""
echo "Press Enter to continue..."
read
echo ""

cd "$WORK_FEAT"

if [ ! -f "$ORIGINAL_DIR/bin/resolve_with_prompt.js" ]; then
    echo "❌ ERROR: resolve_with_prompt.js not found"
    exit 1
fi

node "$ORIGINAL_DIR/bin/resolve_with_prompt.js" --file app.txt

RESOLUTION_EXIT=$?
echo ""

# ============================================================================
# STEP 8: Show results
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $RESOLUTION_EXIT -eq 0 ]; then
    echo "✅ Resolution accepted and applied!"
    echo ""
    echo "📄 Resolved file content:"
    echo "─────────────────────────────────────────"
    cat app.txt
    echo "─────────────────────────────────────────"
    echo ""
    echo "📊 Git status:"
    git status --short
elif [ $RESOLUTION_EXIT -eq 1 ]; then
    echo "⚠️  Resolution rejected by user"
    echo ""
    echo "Suggestion saved at: /tmp/merged_suggestions/app.txt"
else
    echo "❌ Resolution failed (exit code: $RESOLUTION_EXIT)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test location: $TMP_BASE"
echo ""
echo "To inspect:"
echo "  cd $WORK_FEAT"
echo "  cat rag_output/llm_context.txt"
echo "  cat rag_output/coderabbit_review.json"
echo "  git status"
echo ""
echo "To clean up:"
echo "  rm -rf $TMP_BASE"
echo ""
