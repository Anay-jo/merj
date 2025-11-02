# Testing Guide: RAG + CodeRabbit Integration

This guide provides comprehensive methods to test the RAG + CodeRabbit integration in a real environment.

## Prerequisites

Before testing, ensure you have:

```bash
# 1. API keys set up
export ANTHROPIC_API_KEY="your_claude_api_key_here"
export VOYAGE_API_KEY="your_voyage_api_key_here"

# 2. Dependencies installed
npm install
pip install -r requirements.txt

# 3. Flask backend dependencies
cd flask_backend
pip install -r requirements.txt
cd ..
```

---

## Method 1: Use the Enhanced Test Script (Recommended)

The easiest way to test the complete integration:

```bash
# Make the test script executable
chmod +x test_full_integration.sh

# Run the comprehensive test
./test_full_integration.sh
```

### What This Tests:
- ✅ Creates a test repository with merge conflicts
- ✅ Generates mock RAG context
- ✅ Generates mock CodeRabbit findings
- ✅ Tests combined context loading
- ✅ Verifies Step 6 output verification
- ✅ Runs full Claude AI resolution

### Expected Output:
```
🔍 Step 5: Testing Combined Context Integration
==========================================
✅ RAG context found: rag_output/llm_context.txt
✅ CodeRabbit context found: rag_output/coderabbit_review.json
✅ SUCCESS: RAG context formatted for appending
✅ SUCCESS: CodeRabbit context formatted for appending
✅ SUCCESS: RAG context loaded
✅ SUCCESS: CodeRabbit context loaded

🔍 Step 6: Verifying Output...
✅ RAG Context: Loaded successfully
✅ CodeRabbit Context: Loaded successfully
✅ Combined Context: Both contexts available for appending
```

---

## Method 2: Test with Your Own Repository

### Step 1: Prepare Your Repository
```bash
# Navigate to your project
cd /path/to/your/project

# Set up API keys
export ANTHROPIC_API_KEY="your_claude_api_key_here"
export VOYAGE_API_KEY="your_voyage_api_key_here"

# Make sure you're on main branch
git checkout main
git pull origin main
```

### Step 2: Create a Test Conflict
```bash
# Create a feature branch
git checkout -b test-rag-integration

# Make some changes to a Python file
echo "
def new_feature():
    '''This is a new feature'''
    return 'hello world'
" >> your_file.py

git add your_file.py
git commit -m "Add new feature"

# Switch back to main and make conflicting changes
git checkout main
echo "
def conflicting_feature():
    '''This conflicts with the other feature'''
    return 'goodbye world'
" >> your_file.py

git add your_file.py
git commit -m "Add conflicting feature"

# Create merge conflict
git merge test-rag-integration
```

### Step 3: Test the Integration
```bash
# Check if contexts exist (if using real RAG pipeline)
ls -la rag_output/

# Test the combined context integration
node bin/resolve_with_claude.js

# Check the verification output
```

---

## Method 3: Test with Existing Conflicts

If you already have merge conflicts in your repository:

```bash
# Check for existing conflicts
git status

# If conflicts exist, test directly
node bin/resolve_with_claude.js

# Look for Step 6 verification messages in output
```

---

## Method 4: Manual Verification

### Check Context Files

```bash
# Verify RAG context was generated (if using real pipeline)
cat rag_output/llm_context.txt
# Should contain: === RAG CODE CHUNKS CONTEXT ===

# Verify CodeRabbit context was generated  
cat rag_output/coderabbit_review.json
# Should contain CodeRabbit findings

# Check if both contexts are properly formatted
grep -n "===.*CONTEXT.*===" rag_output/llm_context.txt
```

### Test Individual Components

```bash
# Test RAG pipeline only (requires Flask backend)
cd flask_backend
python app.py &
# Then in another terminal:
curl -X POST http://127.0.0.1:5000/api/health

# Test with mock data
./test_full_integration.sh
```

---

## Method 5: Step-by-Step Verification

### Prerequisites Check
```bash
# 1. Verify API keys are set
echo $ANTHROPIC_API_KEY
echo $VOYAGE_API_KEY

# 2. Check if all dependencies are installed
npm list
pip list | grep -E "(flask|chromadb|voyageai)"

# 3. Verify Node.js version
node --version  # Should be v14 or higher
```

### Verification Steps
```bash
# 1. Test context file existence
ls -la rag_output/

# 2. Test context loading
node bin/resolve_with_claude.js
# Should see Step 6 verification output

# 3. Verify combined context
node bin/resolve_with_claude.js 2>&1 | grep "Combined Context"
```

---

## Method 6: Testing Checklist

Run through this checklist to verify everything works:

- [ ] **Step 1 Verified**: CodeRabbit context loads with headers
  ```bash
  node bin/resolve_with_claude.js 2>&1 | grep "CODERABBIT SEMANTIC CONTEXT"
  ```

- [ ] **Step 2 Verified**: RAG context loads with headers
  ```bash
  node bin/resolve_with_claude.js 2>&1 | grep "RAG CODE CHUNKS CONTEXT"
  ```

- [ ] **Step 3 Verified**: Contexts are appended in prompts
  ```bash
  node bin/resolve_with_claude.js 2>&1 | grep "Combined Context (CodeRabbit + RAG)"
  ```

- [ ] **Step 4 Verified**: Prompt structure is correct
  ```bash
  node bin/resolve_with_claude.js 2>&1 | grep "--- RAG Context ---"
  ```

- [ ] **Step 5 Verified**: Integration test passes
  ```bash
  ./test_full_integration.sh
  ```

- [ ] **Step 6 Verified**: Output verification shows success
  ```bash
  node bin/resolve_with_claude.js 2>&1 | grep "✅"
  ```

---

## Expected Success Indicators

When everything is working correctly, you should see:

### 1. Context Generation
```
✅ RAG context found: rag_output/llm_context.txt
   Lines: 262
✅ CodeRabbit context found: rag_output/coderabbit_review.json
   Size: 1024 bytes
```

### 2. Context Loading
```
📚 Loaded RAG context from: rag_output/llm_context.txt
   RAG context formatted for CodeRabbit appending
🐰 Loaded CodeRabbit findings from: rag_output/coderabbit_review.json
   Context formatted for RAG chunk appending
```

### 3. Step 6 Verification
```
🔍 Step 6: Verifying Output...
==========================================
✅ RAG Context: Loaded successfully
   Size: 262 lines
✅ RAG Context: Properly formatted with headers
✅ CodeRabbit Context: Loaded successfully
   Size: 20 lines
✅ CodeRabbit Context: Properly formatted with headers
✅ Combined Context: Both contexts available for appending
==========================================

🔍 Verifying Description Prompt...
✅ Description Prompt: Contains Combined Context section
✅ Description Prompt: Contains CodeRabbit context
✅ Description Prompt: Contains RAG context
   Total prompt size: 2847 characters

🔍 Verifying Resolution Prompt...
✅ Resolution Prompt: Contains Combined Context section
✅ Resolution Prompt: Contains CodeRabbit context
✅ Resolution Prompt: Contains RAG context
   Total prompt size: 2156 characters
```

### 4. AI Resolution
```
Claude Analysis: [Detailed analysis using both contexts]
✅ Wrote merged suggestion to: /tmp/merged_suggestions/your_file.py
```

---

## Troubleshooting Common Issues

### Issue 1: RAG Context Missing

**Symptoms:**
```
⚠️  RAG context file not found at: rag_output/llm_context.txt
```

**Solutions:**
```bash
# Check if rag_output directory exists
ls -la rag_output/

# If using test script, it creates mock data automatically
./test_full_integration.sh

# For real RAG pipeline, ensure Flask backend is running
cd flask_backend
python app.py &
```

### Issue 2: CodeRabbit Context Missing

**Symptoms:**
```
⚠️  CodeRabbit findings not found at: rag_output/coderabbit_review.json
```

**Solutions:**
```bash
# Use test script which creates mock CodeRabbit data
./test_full_integration.sh

# Or manually create test data for development
mkdir -p rag_output
echo '{"mainBranchReview":{"issues":[]},"localBranchReview":{"issues":[]}}' > rag_output/coderabbit_review.json
```

### Issue 3: Network Connectivity Error

**Symptoms:**
```
TypeError: fetch failed
[cause]: Error: getaddrinfo ENOTFOUND api.anthropic.com
```

**Solutions:**
```bash
# Test internet connectivity
ping google.com
ping api.anthropic.com

# Test DNS resolution
nslookup api.anthropic.com

# Test API connectivity
curl -I https://api.anthropic.com

# If behind corporate firewall, check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

### Issue 4: Combined Context Not Appearing

**Symptoms:**
```
⚠️  Combined Context: Missing one or both contexts
```

**Solutions:**
```bash
# Verify both contexts exist
ls -la rag_output/llm_context.txt
ls -la rag_output/coderabbit_review.json

# Run test script to create both
./test_full_integration.sh

# Check if contexts are properly formatted
grep "=== CODERABBIT SEMANTIC CONTEXT ===" rag_output/llm_context.txt
grep "=== RAG CODE CHUNKS CONTEXT ===" rag_output/llm_context.txt
```

### Issue 5: API Key Issues

**Symptoms:**
```
❌ Missing ANTHROPIC_API_KEY (or ANTHROPIC) in environment.
```

**Solutions:**
```bash
# Set API key
export ANTHROPIC_API_KEY="your_key_here"

# Verify it's set
echo $ANTHROPIC_API_KEY

# Add to shell profile for persistence
echo 'export ANTHROPIC_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc
```

---

## Quick Test Commands

### Minimal Test (Fast)
```bash
# Just verify contexts can be loaded
node bin/resolve_with_claude.js --help
```

### Standard Test (Recommended)
```bash
# Full integration test with mock data
./test_full_integration.sh
```

### Verbose Test (Debug)
```bash
# Run with detailed output
DEBUG=true node bin/resolve_with_claude.js
```

---

## Summary

This integration has been successfully implemented with:
- ✅ Step 1: CodeRabbit context loading enhanced
- ✅ Step 2: RAG context loading enhanced
- ✅ Step 3: Simple context appender created
- ✅ Step 4: Prompt structure updated
- ✅ Step 5: Integration testing implemented
- ✅ Step 6: Output verification implemented

The MVP implementation allows RAG code chunks to be appended to CodeRabbit semantic context and passed to Claude for intelligent merge conflict resolution.

Run `./test_full_integration.sh` to verify everything works!

