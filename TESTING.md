# Testing Guide

## Overview

There are four ways to test the AI-powered merge conflict resolution:

1. **Dry Run** - No API key needed, validates setup
2. **Full Integration Test** - Uses API, tests complete flow with mock RAG + mock CodeRabbit
3. **Real CodeRabbit Test** - Uses API, tests with mock RAG + REAL CodeRabbit
4. **Real Usage** - Test with actual merge conflicts in your repo

---

## Option 1: Dry Run (Recommended First)

**Purpose**: Validate that all components are properly integrated without calling the Claude API.

**Requirements**: None (no API key needed)

**What it checks**:
- ✓ All required files exist
- ✓ Mock conflict and context files can be created
- ✓ Data formats are correct
- ✓ File loading works
- ✓ Integration points are present in code

**Run it**:
```bash
./test_dry_run.sh
```

**Output**: Shows checkmarks for each validation step. Should see all green checkmarks if setup is correct.

---

## Option 2: Full Integration Test

**Purpose**: Test the complete resolution flow with Claude API using mock conflict and context data.

**Requirements**:
- `ANTHROPIC_API_KEY` environment variable set
- API credits available

**What it does**:
1. Creates test git repo with real merge conflict
2. Generates mock RAG context (llm_context.txt)
3. Generates mock CodeRabbit findings (coderabbit_review.json)
4. Calls Claude API to analyze conflict
5. Calls Claude API to generate resolved code
6. Shows CLI confirmation prompts
7. Tests accepting/rejecting resolutions

**Run it**:
```bash
export ANTHROPIC_API_KEY=your_key_here
./test_full_integration.sh
```

**What to expect**:
- You'll see the full flow from conflict creation to resolution
- Claude will analyze the conflict and explain it
- You'll be prompted to view/accept the resolved file
- Test directory is in `/tmp/merj_full_test_*`

**Example conflict**: A Python authentication class where:
- Local branch adds bcrypt security
- Main branch adds rate limiting
- Both modify the same `authenticate` method

---

## Option 3: Real CodeRabbit Test (Recommended for Production Testing)

**Purpose**: Test with REAL CodeRabbit API calls and MOCK RAG context. This is ideal when the RAG pipeline isn't fully working yet.

**Requirements**:
- `ANTHROPIC_API_KEY` environment variable set
- `coderabbit` CLI installed (`npm install -g @coderabbit/cli`)
- CodeRabbit API access

**What it does**:
1. Creates temporary git repos with real merge conflict
2. Generates MOCK RAG context (since RAG pipeline is faulty)
3. Runs REAL CodeRabbit analysis on both branches
4. Calls Claude API with real CodeRabbit findings + mock RAG
5. Shows CLI confirmation prompts
6. Tests complete resolution flow

**Run it**:
```bash
export ANTHROPIC_API_KEY=your_key_here
./test_real_coderabbit.sh
```

**What to expect**:
- Creates temporary repos in `/tmp/merj-test-cr.*`
- Real CodeRabbit analysis on both branches (may take 30-60 seconds)
- CodeRabbit findings saved to `rag_output/coderabbit_review.json`
- Claude uses real CodeRabbit findings for analysis
- You'll see actual code quality issues and suggestions

**Example conflict**: JavaScript functions where:
- Local branch adds logging and caching
- Main branch adds retry logic and validation
- Both rewrite the same functions completely

**Why use this**:
- Tests CodeRabbit integration without needing RAG pipeline
- Gets real code review insights from CodeRabbit
- Validates Claude can use actual CodeRabbit findings effectively
- No need to set up RAG ChromaDB, embeddings, etc.

---

## Option 4: Real Usage Test

**Purpose**: Test with actual merge conflicts in your repository.

**Requirements**:
- `ANTHROPIC_API_KEY` environment variable set
- RAG pipeline running (`cd rag_pipeline && python app.py`)
- CodeRabbit script available

**Setup**:
```bash
# 1. Start RAG pipeline (in separate terminal)
cd rag_pipeline
python app.py

# 2. Set API key
export ANTHROPIC_API_KEY=your_key_here

# 3. Create a test branch with conflicts
git checkout -b test-merge
echo "change A" >> test.txt
git add test.txt && git commit -m "Change A"

git checkout main
echo "change B" >> test.txt
git add test.txt && git commit -m "Change B"

# 4. Run merj pull
merj pull origin test-merge
```

**What happens**:
1. Git pull creates conflict
2. RAG pipeline analyzes changes
3. CodeRabbit reviews both branches
4. Claude AI resolves each conflict
5. You confirm/reject each resolution
6. Summary shows resolved/rejected/failed counts

---

## Troubleshooting

### Dry Run Fails

**"Missing: bin/resolve_with_claude.js"**
- Check that all files are present in bin/ directory
- Run `git status` to verify files aren't ignored

**"RAG context format issue"**
- Check that rag_output/llm_context.txt has correct headers
- Should have "LOCAL CHANGES" and "REMOTE CHANGES" sections

### Full Integration Test Fails

**"Missing ANTHROPIC_API_KEY"**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**"Claude API error 401"**
- API key is invalid or expired
- Get new key from https://console.anthropic.com

**"No conflict created"**
- This shouldn't happen with the test script
- Check git version: `git --version`

**"Resolution failed"**
- Check Claude API response
- May be rate limited or quota exceeded
- Check network connectivity

### Real Usage Fails

**"Error connecting to RAG pipeline"**
```bash
# Start the RAG pipeline
cd rag_pipeline
python app.py
# Should see "Running on http://127.0.0.1:5000"
```

**"CodeRabbit helper failed"**
- Check that `scripts/review_two_sides_with_cr.py` exists
- Check Python dependencies installed

**"Resolution rejected multiple times"**
- Review RAG context quality in `rag_output/llm_context.txt`
- Check CodeRabbit findings in `rag_output/coderabbit_review.json`
- Consider adjusting prompts in `resolve_with_claude.js`

---

## Test Outputs

### Dry Run Output Location
```
/tmp/merj_dryrun_<timestamp>/
├── test.py                          # Mock conflict file
├── rag_output/
│   ├── llm_context.txt             # Mock RAG context
│   └── coderabbit_review.json      # Mock CodeRabbit findings
└── test_loading.js                  # Validation script
```

### Full Integration Test Output
```
/tmp/merj_full_test_<timestamp>/
├── auth.py                          # Test conflict file
├── rag_output/
│   ├── llm_context.txt             # Mock RAG context
│   └── coderabbit_review.json      # Mock CodeRabbit findings
└── .git/                            # Test git repo
```

### Real CodeRabbit Test Output
```
/tmp/merj-test-cr.<random>/
├── remote.git/                      # Bare remote repo
├── work-main/                       # Main branch working copy
└── work-feature/                    # Feature branch (conflict happens here)
    ├── app.txt                      # Conflicted file
    ├── rag_output/
    │   ├── llm_context.txt         # Mock RAG context
    │   └── coderabbit_review.json  # REAL CodeRabbit findings
    └── .git/
```

### Resolved Files Location
```
/tmp/merged_suggestions/
└── auth.py                          # Claude's resolved version
```

---

## Understanding Test Results

### Exit Codes
- **0**: Resolution accepted successfully
- **1**: Resolution rejected by user
- **2+**: Error occurred

### Success Criteria

**Dry Run**:
- All checkmarks should be green ✅
- No red X marks ❌

**Full Integration**:
- Claude analysis shows understanding of conflict
- Resolved file has no conflict markers
- Resolved code makes logical sense
- Git status shows file is staged (if accepted)

**Real Usage**:
- RAG context shows relevant code from LCA
- CodeRabbit findings are appropriate
- All conflicts listed and processed
- Summary shows accurate counts

---

## Quick Reference

| Test Type | API Key | CodeRabbit CLI | RAG Pipeline | Time | Use Case |
|-----------|---------|----------------|--------------|------|----------|
| Dry Run | ❌ | ❌ | ❌ | 10s | Validate setup |
| Full Integration | ✅ | ❌ | ❌ | 30s | Test with all mocks |
| Real CodeRabbit | ✅ | ✅ | ❌ | 1-2min | Test CodeRabbit integration |
| Real Usage | ✅ | ✅ | ✅ | 2-3min | Production test |

---

## Next Steps After Testing

1. **If dry run passes**: Move to full integration test
2. **If full integration passes**: Try real CodeRabbit test
3. **If real CodeRabbit works**: Use in production with `merj pull`
4. **When RAG pipeline is fixed**: Enable full real usage test

## Cost Considerations

- **Dry run**: Free (no API calls)
- **Full integration test**: ~$0.01-0.02 per run (2 Claude API calls per conflict)
- **Real CodeRabbit test**: ~$0.01-0.02 per run (2 Claude + CodeRabbit API calls)
- **Real usage**: Depends on number of conflicts (Claude + CodeRabbit per conflict)

Each conflict makes 2 Claude API calls:
1. Description/analysis (typically 500-1000 tokens)
2. Resolution generation (typically 1000-2000 tokens)

---

## Getting Help

If tests fail consistently:

1. Check environment variables are set
2. Verify file paths in error messages
3. Review output logs in test directories
4. Check API rate limits and quotas
5. See MERJ_INTEGRATION_COMPLETE.md for detailed flow
