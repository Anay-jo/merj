#!/bin/bash
# Test script to demonstrate the integrated flow
# Creates a mock conflict and runs the resolution

echo "======================================================================="
echo "  TEST: AI-POWERED MERGE CONFLICT RESOLUTION"
echo "======================================================================="
echo ""
echo "This test will:"
echo "  1. Create a test git repo with a merge conflict"
echo "  2. Run resolve_with_prompt.js to resolve it"
echo "  3. Show the complete flow"
echo ""
echo "Press Enter to start..."
read

# Save the original directory
ORIGINAL_DIR="$(pwd)"

# Setup test directory
TEST_DIR="/tmp/merj_test_$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Creating test repository at: $TEST_DIR"
echo ""

# Initialize git repo and immediately create first commit
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Create and commit base file
cat > auth.py << 'EOF'
def authenticate(username, password):
    """Authenticate a user."""
    if username == "admin" and password == "secret":
        return True
    return False
EOF

git add auth.py
git commit -q -m "Initial commit"

# Get the current branch name (could be master or main)
MAIN_BRANCH=$(git branch --show-current)
echo "📌 Main branch: $MAIN_BRANCH"

# Create feature branch with changes
git checkout -q -b feature

cat > auth.py << 'EOF'
import bcrypt

def authenticate(username, password):
    """Authenticate with bcrypt security."""
    stored_hash = get_password_hash(username)
    if bcrypt.checkpw(password.encode(), stored_hash):
        return True
    return False

def get_password_hash(username):
    return b"$2b$12$..."
EOF

git add auth.py
git commit -q -m "Add bcrypt"

# Go back to main branch and make conflicting changes
git checkout -q "$MAIN_BRANCH"

cat > auth.py << 'EOF'
import time

def authenticate(username, password):
    """Authenticate with rate limiting."""
    if not check_rate_limit(username):
        return False
    if username == "admin" and password == "secret":
        return True
    return False

def check_rate_limit(username):
    return True
EOF

git add auth.py
git commit -q -m "Add rate limiting"

# Try to merge - this MUST create a conflict
echo "🔄 Creating merge conflict..."
echo ""

# Attempt merge and capture result
MERGE_OUTPUT=$(git merge feature 2>&1)
MERGE_EXIT_CODE=$?

if [ $MERGE_EXIT_CODE -ne 0 ]; then
    echo "✅ Merge conflict created successfully!"
    echo ""
    # Show what git said
    echo "$MERGE_OUTPUT" | grep -E "CONFLICT|Automatic"
else
    echo "⚠️  WARNING: Merge succeeded without conflict (exit code: $MERGE_EXIT_CODE)"
    echo "Output: $MERGE_OUTPUT"
fi

echo ""

# Check for conflict markers
if grep -q "<<<<<<< HEAD" auth.py 2>/dev/null; then
    echo "✅ Confirmed: Conflict markers found in auth.py"
    echo ""
    echo "📄 Conflicted file content:"
    echo "==========================================="
    cat auth.py
    echo "==========================================="
else
    echo "❌ ERROR: No conflict markers found!"
    echo ""
    echo "Git status:"
    git status
    echo ""
    echo "File content:"
    cat auth.py
    echo ""
    echo "This test cannot continue without a conflict."
    exit 1
fi

echo ""

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "   The resolve step will fail without it."
    echo ""
    exit 1
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi

echo ""
echo "🚀 Running AI resolution..."
echo "======================================================================="
echo ""

# Run the integrated resolution
cd "$TEST_DIR"

# First check if the script exists
if [ ! -f "$ORIGINAL_DIR/bin/resolve_with_prompt.js" ]; then
    echo "❌ Error: resolve_with_prompt.js not found at:"
    echo "   $ORIGINAL_DIR/bin/resolve_with_prompt.js"
    echo ""
    echo "Directory contents:"
    ls -la "$ORIGINAL_DIR/bin/"
    exit 1
fi

# Run it
node "$ORIGINAL_DIR/bin/resolve_with_prompt.js" || {
    EXIT_CODE=$?
    echo ""
    echo "⚠️  Resolution script exited with code: $EXIT_CODE"
    echo ""
    echo "Debug info:"
    echo "  Working dir: $(pwd)"
    echo "  Script path: $ORIGINAL_DIR/bin/resolve_with_prompt.js"
    echo ""
    echo "Git status:"
    git status --short
    echo ""
    echo "To debug manually:"
    echo "  cd $TEST_DIR"
    echo "  node $ORIGINAL_DIR/bin/resolve_with_prompt.js"
}

echo ""
echo "Test complete!"
echo "Test directory: $TEST_DIR"
echo ""
echo "To clean up: rm -rf $TEST_DIR"
echo ""