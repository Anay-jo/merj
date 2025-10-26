# Merge Conflict Test Pipeline

This test pipeline simulates merge conflicts in isolated environments to test the `merj pull` functionality without affecting your actual repository.

## ✅ Fixed Issues

The initial version had a fundamental misunderstanding of how `merj pull` works. The test now correctly:
1. **Sets up a proper remote repository** using a bare git repo
2. **Creates divergent changes** between local and remote branches
3. **Uses `merj pull` to fetch and merge**, which naturally creates conflicts
4. **Bypasses editor prompts** to avoid test timeouts

### Why the Original Test Failed
- `merj pull` expects to **start from a clean state** and pull from a remote
- The original test created conflicts locally first, then tried to pull (which git refuses)
- There was no actual remote repository set up (missing `origin/main`)

## Features

- Creates temporary git repositories in `/tmp` directory
- Simulates realistic merge conflicts in different file types:
  - Python files (with function and class changes)
  - JavaScript files (with module system conflicts)
  - JSON configuration files (package.json conflicts)
- Generates conflict data in the format expected by the RAG pipeline
- Tests the `merj pull` command on simulated conflicts
- Validates RAG pipeline processing
- Automatic cleanup of temporary files

## Usage

### Quick Test (Single Scenario)
```bash
# Test with a Python conflict
python test_merge_conflict_pipeline.py --quick

# Test specific scenario
python test_merge_conflict_pipeline.py --scenario python
python test_merge_conflict_pipeline.py --scenario javascript
python test_merge_conflict_pipeline.py --scenario config
```

### Full Test Pipeline
```bash
# Run all tests
python test_merge_conflict_pipeline.py

# This will:
# 1. Create temporary git repository
# 2. Simulate all three conflict types
# 3. Test merj pull command
# 4. Test RAG pipeline integration
# 5. Clean up automatically
```

## What Gets Created

### Simulated Conflicts

1. **Python Conflict** (`order_processor.py`):
   - Base: Simple calculate_total and process_order functions
   - Feature branch: Adds tax calculation and validation
   - Main branch: Adds discount and shipping calculation
   - Result: Conflict between different pricing strategies

2. **JavaScript Conflict** (`services/user_service.js`):
   - Base: Basic UserService class
   - API branch: Adds caching and validation with Map storage
   - Main branch: Adds event emitter and password verification
   - Result: Conflict between different architectural approaches

3. **JSON Config Conflict** (`package.json`):
   - Base: Basic package.json
   - Deps branch: Updates dependencies and adds dev tools
   - Main branch: Adds TypeScript and Docker support
   - Result: Conflict in dependencies and scripts

### Output Files

- `conflict_data.json`: JSON format with lbd/rbd keys for RAG pipeline
- `test_rag_output/`: Directory with RAG pipeline outputs
  - `rag_chunks.json`: Extracted code chunks
  - `llm_context.txt`: Formatted context for LLM

## Test Results

The pipeline reports:
- Number of conflicts successfully created
- Whether `merj pull` executed (may fail if merj not installed)
- RAG pipeline processing status
- Any errors encountered

## How It Works

1. **MergeConflictSimulator Class**:
   - Creates isolated git repositories in temp directories
   - Manages git operations (branches, commits, merges)
   - Generates conflicts through divergent changes
   - Extracts conflict markers and line numbers

2. **Conflict Generation**:
   - Creates base version and commits
   - Creates feature branch with changes
   - Returns to main and makes different changes
   - Attempts merge to create conflict

3. **JSON Generation**:
   - Parses conflict markers from files
   - Generates lbd (local vs base diff) entries
   - Generates rbd (remote vs base diff) entries
   - Matches expected format for RAG pipeline

4. **Testing Integration**:
   - Tests `merj pull` command execution
   - Validates RAG pipeline can process the conflicts
   - Checks output file generation

## Safety

- All operations happen in `/tmp` directory
- Automatic cleanup with context manager
- No changes to your actual repository
- Isolated git repositories for testing

## Requirements

- Python 3.8+
- Git installed and configured
- merj tool (optional, for merj pull testing)
- RAG pipeline dependencies (tree-sitter, voyage, chromadb)

## Troubleshooting

### merj command not found
- The test will continue but skip merj pull testing
- Install merj to enable full testing

### No conflicts created
- Check git is properly installed
- Ensure temp directory is writable

### RAG pipeline errors
- Verify VOYAGE_API_KEY is set
- Check tree-sitter parsers are installed