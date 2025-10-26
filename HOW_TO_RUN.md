# How to Run the RAG-Enhanced Merge Conflict Resolution Pipeline

## Complete Workflow

### 1. Prerequisites
```bash
# Set API keys
export VOYAGE_API_KEY="pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB"  # For embeddings
export ANTHROPIC_API_KEY="your-anthropic-key"  # For Claude resolution
```

### 2. Start Flask Backend
```bash
# Start the Flask server (runs on port 5000)
VOYAGE_API_KEY="pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB" python flask_backend/app.py
```

### 3. Create a Merge Conflict (Test Scenario)
```bash
# Option A: Use the demo script
scripts/full_demo_run.sh

# Option B: If you have an existing conflict
merj pull
```

### 4. RAG Pipeline Processing
When you run `merj pull`, it automatically:
1. Detects merge conflicts
2. Sends diff data to Flask backend
3. Flask processes through RAG pipeline:
   - Chunks relevant code around conflict lines
   - Creates embeddings with Voyage AI
   - Searches for similar patterns (if ChromaDB collection exists)
   - **Saves output files to `rag_output/`**

### 5. Generated Files
After running the pipeline, you'll have:
- `rag_output/llm_context.txt` - Human-readable context for LLM
- `rag_output/rag_chunks.json` - Structured JSON data

### 6. Resolve with Claude
```bash
# Now run resolve_with_claude.js - it will automatically use RAG context
node bin/resolve_with_claude.js --file path/to/conflicted/file.js

# Or let it auto-detect first conflicted file
node bin/resolve_with_claude.js
```

The resolver will:
1. Load the conflicted file
2. **Load RAG context from `rag_output/llm_context.txt`** (NEW!)
3. Send both to Claude for intelligent resolution
4. Output merged file to `/tmp/merged_suggestions/`

## What's New with RAG Integration

### Before (without RAG):
- Claude only sees the raw conflicted file
- No context about what each branch was trying to achieve
- Limited understanding of surrounding code

### After (with RAG):
- Claude receives comprehensive context:
  - **Local changes**: What your branch modified
  - **Remote changes**: What main branch modified
  - **Similar patterns**: How similar code is structured
- Better informed merge decisions
- More intelligent conflict resolution

## Quick Test

```bash
# 1. Test RAG output generation
python test_output_chunks.py

# 2. Check generated files
ls -la rag_output/
cat rag_output/llm_context.txt | head -50

# 3. Test with a conflict file
echo "Setting up test conflict..."
node bin/resolve_with_claude.js --file test_conflict.txt
```

## API Endpoints

### POST /api/data
Send diff data for RAG processing:
```bash
curl -X POST http://127.0.0.1:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "lbd": [{"filefrom": "file1.py", "lns": [10, 20, 30]}],
    "rbd": [{"filefrom": "file2.py", "lns": [15, 25]}]
  }'
```

### POST /api/lca/create (Optional)
Create LCA collection for better context:
```bash
curl -X POST http://127.0.0.1:5000/api/lca/create \
  -H "Content-Type: application/json" \
  -d '{"lca_commit": "abc123"}'
```

## Troubleshooting

### If RAG context is not loading:
1. Check if `rag_output/` directory exists
2. Verify Flask backend is running with correct API key
3. Ensure `merj pull` or test script ran successfully
4. Look for "📚 Loaded RAG context" message when running resolve_with_claude.js

### If files are not being generated:
1. Check Flask logs for errors
2. Verify Voyage API key is set correctly
3. Ensure you have write permissions to `rag_output/`

## Architecture Flow
```
Merge Conflict → merj.js → Flask Backend → RAG Pipeline → File Output
                                                              ↓
                                                        rag_output/
                                                              ↓
                                                    resolve_with_claude.js
                                                              ↓
                                                     Intelligent Resolution
```