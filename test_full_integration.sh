#!/bin/bash
# Complete integration test with mock RAG and CodeRabbit data
# Tests the full resolution flow without needing RAG pipeline or CodeRabbit API

set -e  # Exit on any error

echo "======================================================================="
echo "  FULL INTEGRATION TEST - AI Merge Conflict Resolution"
echo "======================================================================="
echo ""
echo "This test simulates the complete merj pull flow:"
echo "  1. Create a test git repo with merge conflict"
echo "  2. Generate mock RAG context (llm_context.txt)"
echo "  3. Generate mock CodeRabbit findings (coderabbit_review.json)"
echo "  4. Run Claude AI resolution with full context"
echo "  5. Show user the CLI confirmation flow"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set"
    echo ""
    echo "To run this test, set your API key:"
    echo "  export ANTHROPIC_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "✅ ANTHROPIC_API_KEY is set"
echo ""
echo "Press Enter to start test..."
read

# Save original directory
ORIGINAL_DIR="$(pwd)"

# Create test directory
TEST_DIR="/tmp/merj_full_test_$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Test directory: $TEST_DIR"
echo ""

# ============================================================================
# STEP 1: Create Test Repo with Conflict
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Creating test repository with merge conflict"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Create base file
cat > auth.py << 'EOF'
class AuthManager:
    """Basic authentication manager."""

    def __init__(self):
        self.users = {}

    def authenticate(self, username, password):
        """Authenticate a user."""
        if username in self.users:
            if self.users[username] == password:
                return True
        return False
EOF

git add auth.py
git commit -q -m "Initial auth manager"

MAIN_BRANCH=$(git branch --show-current)
echo "📌 Main branch: $MAIN_BRANCH"
echo ""

# Create feature branch - adds bcrypt security
git checkout -q -b feature
cat > auth.py << 'EOF'
import bcrypt

class AuthManager:
    """Authentication manager with bcrypt security."""

    def __init__(self):
        self.users = {}

    def authenticate(self, username, password):
        """Authenticate with secure bcrypt hashing."""
        if username in self.users:
            stored_hash = self.users[username]
            if bcrypt.checkpw(password.encode(), stored_hash):
                return True
        return False

    def register(self, username, password):
        """Register new user with hashed password."""
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username] = hashed
        return True
EOF

git add auth.py
git commit -q -m "Add bcrypt security and registration"

# Main branch - adds rate limiting
git checkout -q "$MAIN_BRANCH"
cat > auth.py << 'EOF'
import time

class AuthManager:
    """Authentication manager with rate limiting."""

    def __init__(self):
        self.users = {}
        self.failed_attempts = {}

    def authenticate(self, username, password):
        """Authenticate with rate limiting protection."""
        if not self._check_rate_limit(username):
            raise Exception("Too many failed attempts")

        if username in self.users:
            if self.users[username] == password:
                self._reset_attempts(username)
                return True
            else:
                self._record_failure(username)
        return False

    def _check_rate_limit(self, username):
        if username in self.failed_attempts:
            attempts, last_time = self.failed_attempts[username]
            if attempts >= 3 and time.time() - last_time < 300:
                return False
        return True

    def _record_failure(self, username):
        if username not in self.failed_attempts:
            self.failed_attempts[username] = [0, time.time()]
        self.failed_attempts[username][0] += 1
        self.failed_attempts[username][1] = time.time()

    def _reset_attempts(self, username):
        if username in self.failed_attempts:
            del self.failed_attempts[username]
EOF

git add auth.py
git commit -q -m "Add rate limiting protection"

# Create the merge conflict
echo "🔄 Creating merge conflict..."
git merge feature 2>&1 | grep -E "CONFLICT|Automatic" || true

# Verify conflict exists
if grep -q "<<<<<<< HEAD" auth.py 2>/dev/null; then
    echo "✅ Conflict created in auth.py"
    echo ""
else
    echo "❌ ERROR: No conflict created!"
    exit 1
fi

# ============================================================================
# STEP 2: Create Mock RAG Context
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Creating mock RAG context"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p rag_output

cat > rag_output/llm_context.txt << 'EOF'
============================================================
MERGE CONFLICT CONTEXT FOR LLM
============================================================

LOCAL CHANGES (Your Branch):
----------------------------------------

[1] File: auth.py
    Lines: 1-24
    Type: class
    Code:
    import bcrypt

    class AuthManager:
        """Authentication manager with bcrypt security."""

        def __init__(self):
            self.users = {}

        def authenticate(self, username, password):
            """Authenticate with secure bcrypt hashing."""
            if username in self.users:
                stored_hash = self.users[username]
                if bcrypt.checkpw(password.encode(), stored_hash):
                    return True
            return False

        def register(self, username, password):
            """Register new user with hashed password."""
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            self.users[username] = hashed
            return True


REMOTE CHANGES (Main Branch):
----------------------------------------

[1] File: auth.py
    Lines: 1-42
    Type: class
    Code:
    import time

    class AuthManager:
        """Authentication manager with rate limiting."""

        def __init__(self):
            self.users = {}
            self.failed_attempts = {}

        def authenticate(self, username, password):
            """Authenticate with rate limiting protection."""
            if not self._check_rate_limit(username):
                raise Exception("Too many failed attempts")

            if username in self.users:
                if self.users[username] == password:
                    self._reset_attempts(username)
                    return True
                else:
                    self._record_failure(username)
            return False

        def _check_rate_limit(self, username):
            if username in self.failed_attempts:
                attempts, last_time = self.failed_attempts[username]
                if attempts >= 3 and time.time() - last_time < 300:
                    return False
            return True

        def _record_failure(self, username):
            if username not in self.failed_attempts:
                self.failed_attempts[username] = [0, time.time()]
            self.failed_attempts[username][0] += 1
            self.failed_attempts[username][1] = time.time()

        def _reset_attempts(self, username):
            if username in self.failed_attempts:
                del self.failed_attempts[username]


SIMILAR CODE PATTERNS FOUND:
----------------------------------------
  (No similar code patterns found in LCA codebase)
EOF

echo "✅ Created rag_output/llm_context.txt"
echo "   Size: $(wc -c < rag_output/llm_context.txt) bytes"
echo ""

# ============================================================================
# STEP 3: Create Mock CodeRabbit Findings
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Creating mock CodeRabbit findings"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat > rag_output/coderabbit_review.json << 'EOF'
{
  "mainBranchReview": {
    "issues": [
      {
        "file": "auth.py",
        "line": 21,
        "message": "Consider storing passwords hashed instead of plaintext in the users dict",
        "severity": "high"
      },
      {
        "file": "auth.py",
        "line": 28,
        "message": "The rate limiting logic could be extracted into a separate RateLimiter class for better separation of concerns",
        "severity": "medium"
      }
    ]
  },
  "localBranchReview": {
    "issues": [
      {
        "file": "auth.py",
        "line": 19,
        "message": "Good use of bcrypt for password hashing",
        "severity": "info"
      },
      {
        "file": "auth.py",
        "line": 21,
        "message": "Consider adding input validation for username and password (length, characters, etc.)",
        "severity": "medium"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
EOF

echo "✅ Created rag_output/coderabbit_review.json"
echo "   Size: $(wc -c < rag_output/coderabbit_review.json) bytes"
echo ""

# ============================================================================
# STEP 4: Show Context Files
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Verifying mock data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📄 Conflicted file (auth.py):"
echo "─────────────────────────────────────────"
head -20 auth.py
echo "..."
echo "─────────────────────────────────────────"
echo ""

echo "📚 RAG Context preview:"
echo "─────────────────────────────────────────"
head -15 rag_output/llm_context.txt
echo "..."
echo "─────────────────────────────────────────"
echo ""

echo "🐰 CodeRabbit Findings preview:"
echo "─────────────────────────────────────────"
cat rag_output/coderabbit_review.json | head -15
echo "..."
echo "─────────────────────────────────────────"
echo ""

# ============================================================================
# STEP 5: Run Claude AI Resolution
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Running Claude AI resolution with full context"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will:"
echo "  1. Load RAG context from rag_output/llm_context.txt"
echo "  2. Load CodeRabbit findings from rag_output/coderabbit_review.json"
echo "  3. Call Claude API to analyze the conflict"
echo "  4. Call Claude API to generate resolved code"
echo "  5. Prompt you to accept/reject the resolution"
echo ""
echo "Press Enter to continue..."
read
echo ""

# Run the resolution
if [ ! -f "$ORIGINAL_DIR/bin/resolve_with_prompt.js" ]; then
    echo "❌ ERROR: resolve_with_prompt.js not found"
    echo "   Expected at: $ORIGINAL_DIR/bin/resolve_with_prompt.js"
    exit 1
fi

node "$ORIGINAL_DIR/bin/resolve_with_prompt.js" --file auth.py

RESOLUTION_EXIT=$?
echo ""

# ============================================================================
# STEP 6: Show Results
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $RESOLUTION_EXIT -eq 0 ]; then
    echo "✅ Resolution accepted and applied!"
    echo ""
    echo "📄 Resolved file content:"
    echo "─────────────────────────────────────────"
    cat auth.py
    echo "─────────────────────────────────────────"
    echo ""
    echo "📊 Git status:"
    git status --short
elif [ $RESOLUTION_EXIT -eq 1 ]; then
    echo "⚠️  Resolution rejected by user"
    echo ""
    echo "The resolved suggestion is saved at:"
    echo "  /tmp/merged_suggestions/auth.py"
else
    echo "❌ Resolution failed (exit code: $RESOLUTION_EXIT)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test directory: $TEST_DIR"
echo ""
echo "To inspect manually:"
echo "  cd $TEST_DIR"
echo "  ls -la"
echo "  cat rag_output/llm_context.txt"
echo "  cat rag_output/coderabbit_review.json"
echo ""
echo "To clean up:"
echo "  rm -rf $TEST_DIR"
echo ""
