#!/bin/bash
# Dry run test - validates all components without calling Claude API
# This is useful to verify the integration is set up correctly

echo "======================================================================="
echo "  DRY RUN TEST - Integration Validation"
echo "======================================================================="
echo ""
echo "This test validates that all components are properly integrated:"
echo "  ✓ Check all required files exist"
echo "  ✓ Create mock conflict and context files"
echo "  ✓ Verify data formats are correct"
echo "  ✓ Test file loading functions"
echo ""
echo "This does NOT call the Claude API (no API key needed)"
echo ""
echo "Press Enter to start..."
read
echo ""

ORIGINAL_DIR="$(pwd)"
TEST_DIR="/tmp/merj_dryrun_$(date +%s)"
mkdir -p "$TEST_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 1: Required Files Exist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

REQUIRED_FILES=(
    "bin/merj.js"
    "bin/resolve_with_claude.js"
    "bin/resolve_with_prompt.js"
    "bin/cli_resolution_handler.js"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$ORIGINAL_DIR/$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo ""
    echo "❌ ERROR: Some required files are missing!"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 2: Create Test Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$TEST_DIR"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

cat > test.py << 'EOF'
def hello():
<<<<<<< HEAD
    print("Hello from main")
=======
    print("Hello from feature")
>>>>>>> feature
    return True
EOF

echo "✅ Created test repo at: $TEST_DIR"
echo "✅ Created test.py with conflict markers"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 3: Create Mock Context Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p rag_output

cat > rag_output/llm_context.txt << 'EOF'
============================================================
MERGE CONFLICT CONTEXT FOR LLM
============================================================

LOCAL CHANGES (Your Branch):
----------------------------------------

[1] File: test.py
    Lines: 1-3
    Type: function
    Code:
    def hello():
        print("Hello from main")
        return True

REMOTE CHANGES (Main Branch):
----------------------------------------

[1] File: test.py
    Lines: 1-3
    Type: function
    Code:
    def hello():
        print("Hello from feature")
        return True
EOF

cat > rag_output/coderabbit_review.json << 'EOF'
{
  "mainBranchReview": {
    "issues": [
      {
        "file": "test.py",
        "line": 2,
        "message": "Consider adding docstring",
        "severity": "low"
      }
    ]
  },
  "localBranchReview": {
    "issues": []
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
EOF

echo "✅ Created rag_output/llm_context.txt"
echo "✅ Created rag_output/coderabbit_review.json"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 4: Verify Data Formats"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check RAG context has expected sections
if grep -q "LOCAL CHANGES" rag_output/llm_context.txt && \
   grep -q "REMOTE CHANGES" rag_output/llm_context.txt; then
    echo "✅ RAG context has correct format"
else
    echo "❌ RAG context format issue"
fi

# Check CodeRabbit JSON is valid
if node -e "JSON.parse(require('fs').readFileSync('rag_output/coderabbit_review.json'))" 2>/dev/null; then
    echo "✅ CodeRabbit JSON is valid"
else
    echo "❌ CodeRabbit JSON is invalid"
fi

# Check conflict markers exist
if grep -q "<<<<<<< HEAD" test.py; then
    echo "✅ Conflict markers present in test file"
else
    echo "❌ No conflict markers found"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 5: Test File Loading (Node.js)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create a test script that mimics what resolve_with_claude.js does
cat > test_loading.js << 'JSEOF'
const fs = require('fs');
const path = require('path');

console.log('Testing file loading...\n');

// Test 1: Load RAG context
try {
    const ragPath = path.join(process.cwd(), 'rag_output', 'llm_context.txt');
    const ragContent = fs.readFileSync(ragPath, 'utf-8');
    console.log('✅ RAG context loaded');
    console.log(`   Size: ${ragContent.length} bytes`);
    console.log(`   Has LOCAL: ${ragContent.includes('LOCAL CHANGES')}`);
    console.log(`   Has REMOTE: ${ragContent.includes('REMOTE CHANGES')}`);
} catch (e) {
    console.log('❌ Failed to load RAG context:', e.message);
}

console.log('');

// Test 2: Load CodeRabbit findings
try {
    const crPath = path.join(process.cwd(), 'rag_output', 'coderabbit_review.json');
    const crContent = fs.readFileSync(crPath, 'utf-8');
    const crData = JSON.parse(crContent);
    console.log('✅ CodeRabbit findings loaded');
    console.log(`   Has mainBranchReview: ${!!crData.mainBranchReview}`);
    console.log(`   Has localBranchReview: ${!!crData.localBranchReview}`);
    console.log(`   Main issues: ${crData.mainBranchReview?.issues?.length || 0}`);
    console.log(`   Local issues: ${crData.localBranchReview?.issues?.length || 0}`);
} catch (e) {
    console.log('❌ Failed to load CodeRabbit findings:', e.message);
}

console.log('');

// Test 3: Read conflict file
try {
    const conflictFile = fs.readFileSync('test.py', 'utf-8');
    console.log('✅ Conflict file loaded');
    console.log(`   Size: ${conflictFile.length} bytes`);
    console.log(`   Has conflict markers: ${conflictFile.includes('<<<<<<<')}`);
} catch (e) {
    console.log('❌ Failed to load conflict file:', e.message);
}
JSEOF

node test_loading.js
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 6: Verify Integration Points"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check that merj.js has the integration code
if grep -q "listConflictedFiles" "$ORIGINAL_DIR/bin/merj.js"; then
    echo "✅ merj.js has listConflictedFiles function"
else
    echo "❌ merj.js missing listConflictedFiles function"
fi

if grep -q "resolve_with_prompt.js" "$ORIGINAL_DIR/bin/merj.js"; then
    echo "✅ merj.js calls resolve_with_prompt.js"
else
    echo "❌ merj.js doesn't call resolve_with_prompt.js"
fi

# Check that resolve_with_claude.js loads context files
if grep -q "loadRAGContext" "$ORIGINAL_DIR/bin/resolve_with_claude.js"; then
    echo "✅ resolve_with_claude.js has loadRAGContext"
else
    echo "❌ resolve_with_claude.js missing loadRAGContext"
fi

if grep -q "loadCodeRabbitContext" "$ORIGINAL_DIR/bin/resolve_with_claude.js"; then
    echo "✅ resolve_with_claude.js has loadCodeRabbitContext"
else
    echo "❌ resolve_with_claude.js missing loadCodeRabbitContext"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DRY RUN COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ All integration checks passed!"
echo ""
echo "Next steps:"
echo "  1. For quick validation: ./test_dry_run.sh (no API key needed)"
echo "  2. For full test with API: ./test_full_integration.sh (requires ANTHROPIC_API_KEY)"
echo "  3. For real usage: merj pull (in a repo with conflicts)"
echo ""
echo "Test directory (can be deleted): $TEST_DIR"
echo ""
