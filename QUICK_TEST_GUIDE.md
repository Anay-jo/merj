# Quick Test Guide: RAG + CodeRabbit Integration

## 🚀 Fastest Way to Test

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your_key_here"

# 2. Run the full integration test
./test_full_integration.sh
```

This will automatically:
- Create a test repo with conflicts
- Generate mock RAG and CodeRabbit contexts
- Verify all 6 implementation steps
- Test the complete flow

---

## ✅ What to Look For

### Success Indicators:

```plaintext
✅ RAG Context: Loaded successfully
✅ CodeRabbit Context: Loaded successfully
✅ Combined Context: Both contexts available for appending
✅ Description Prompt: Contains Combined Context section
✅ Resolution Prompt: Contains Combined Context section
```

### What Each Step Verifies:

1. **Step 1**: CodeRabbit context has semantic headers
2. **Step 2**: RAG context has semantic headers
3. **Step 3**: Contexts are appended together
4. **Step 4**: Combined context in prompts
5. **Step 5**: Integration test passes
6. **Step 6**: Output verification succeeds

---

## 🔍 Quick Diagnostics

### Check if Contexts Exist
```bash
ls -la rag_output/
# Should see: llm_context.txt and coderabbit_review.json
```

### Verify Context Headers
```bash
# Check RAG context header
head -5 rag_output/llm_context.txt
# Should contain: === RAG CODE CHUNKS CONTEXT ===

# Check CodeRabbit has findings
cat rag_output/coderabbit_review.json | jq '.'
```

### Test Context Loading
```bash
# Run resolve script (will show Step 6 verification)
node bin/resolve_with_claude.js 2>&1 | grep "Step 6"
```

---

## 🛠️ Common Issues & Quick Fixes

### Issue: "RAG context file not found"
**Fix:**
```bash
./test_full_integration.sh  # Creates mock data automatically
```

### Issue: "CodeRabbit findings not found"
**Fix:**
```bash
./test_full_integration.sh  # Creates mock data automatically
```

### Issue: "fetch failed ENOTFOUND"
**Fix:**
```bash
# Test internet connection
ping api.anthropic.com

# Check API key is set
echo $ANTHROPIC_API_KEY
```

### Issue: "Combined Context: Missing"
**Fix:**
```bash
# Ensure both context files exist
ls -la rag_output/*.txt rag_output/*.json

# Re-run test to regenerate
./test_full_integration.sh
```

---

## 📋 Testing Checklist

Copy and run these commands in sequence:

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your_key_here"

# 2. Make test script executable
chmod +x test_full_integration.sh

# 3. Run full integration test
./test_full_integration.sh

# 4. Verify success (look for ✅ symbols)
# Should see all green checkmarks for:
# - RAG Context: Loaded successfully
# - CodeRabbit Context: Loaded successfully  
# - Combined Context: Both contexts available
# - Description Prompt: Contains Combined Context section
# - Resolution Prompt: Contains Combined Context section
```

---

## 💡 Pro Tips

### Tip 1: Test Without API Calls
```bash
# Just verify context loading (no Claude API call)
node -e "
const { loadRAGContext, loadCodeRabbitContext } = require('./bin/resolve_with_claude.js');
console.log('RAG loaded:', !!loadRAGContext());
console.log('CR loaded:', !!loadCodeRabbitContext());
"
```

### Tip 2: Inspect Prompt Content
```bash
# See what gets sent to Claude (without actually calling API)
node bin/resolve_with_claude.js 2>&1 | grep -A 5 "Verifying Description Prompt"
```

### Tip 3: Quick Context Check
```bash
# Verify both contexts have correct headers
grep -c "=== RAG CODE CHUNKS CONTEXT ===" rag_output/llm_context.txt
grep -c "=== CODERABBIT SEMANTIC CONTEXT ===" rag_output/llm_context.txt
```

---

## 🎯 Expected Test Output

When everything works, you'll see:

```plaintext
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Testing Combined Context Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RAG context found: rag_output/llm_context.txt
   Lines: 262
✅ CodeRabbit context found: rag_output/coderabbit_review.json
   Size: 1024 bytes

🧪 Testing resolve_with_claude.js context loading...
✅ SUCCESS: RAG context formatted for appending
✅ SUCCESS: CodeRabbit context formatted for appending
✅ SUCCESS: RAG context loaded
✅ SUCCESS: CodeRabbit context loaded

✅ Step 5 verification complete!

The system is now configured to:
  1. Load CodeRabbit semantic context with clear structure
  2. Load RAG code chunks with clear structure
  3. Append RAG chunks to CodeRabbit context in a combined section
  4. Pass combined context to Claude for merge resolution

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running Full Claude AI Resolution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

---

## 🎉 Success!

If you see all the ✅ checkmarks above, your RAG + CodeRabbit integration is working perfectly!

The system now:
1. ✅ Loads CodeRabbit semantic strings
2. ✅ Loads RAG code chunks  
3. ✅ Appends them together in a combined context
4. ✅ Passes combined context to Claude
5. ✅ Verifies everything is working correctly

---

**Need more details?** See `TESTING_RAG_CODERABBIT_INTEGRATION.md` for comprehensive testing methods.

