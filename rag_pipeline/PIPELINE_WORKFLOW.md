# RAG Pipeline Workflow Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow](#data-flow)
4. [Component Connections](#component-connections)
5. [Storage Schema](#storage-schema)
6. [Execution Paths](#execution-paths)
7. [Integration Points](#integration-points)
8. [Configuration & Deployment](#configuration--deployment)
9. [Testing](#testing)

## Architecture Overview

The RAG (Retrieval-Augmented Generation) pipeline is designed to enhance merge conflict resolution by providing relevant context from the codebase history.

```
                MergeConflictResolver RAG Pipeline Flow
                ========================================

1. Git Merge Conflict Detection (merj pull)
              ↓
2. CodeRabbit Analysis (review_two_sides_with_cr.py)
              ↓
3. LCA Detection & Chunking (chunk_lca.py)
              ↓
4. Code Embedding (embedder.py → Voyage AI)
              ↓
5. Vector Storage (chroma.py → ChromaDB)
              ↓
6. RAG Retrieval (local_remote_rag.py)
              ↓
7. Context Enhancement for Conflict Resolution
```

### Internal Workflow Stages

```
Stage 1: PREPARATION (chunk_lca.py)
├── Find LCA (git merge-base)
├── Create worktree at LCA
├── Chunk repository → CodeChunk objects
├── Embed chunks → vectors
└── Store in ChromaDB collection

Stage 2: RETRIEVAL (local_remote_rag.py)
├── Receive conflict chunks
├── Embed incoming chunks
├── Query ChromaDB (k-NN search)
├── Filter by distance threshold
└── Return similar code context

Stage 3: DEMONSTRATION (demo.py)
└── Shows full pipeline on sample code
```

## Component Breakdown

### Core Pipeline Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `chunker.py` | Tree-sitter based code parser | `chunk_repository()`, `chunk_file()` |
| `embedder.py` | Voyage AI integration | `embed_chunk()`, `embed_chunks()` |
| `chroma.py` | ChromaDB storage | `insert_to_chroma()` |

### Integration Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `chunk_lca.py` | LCA chunking orchestrator | `create_lca_worktree()`, `main()` |
| `local_remote_rag.py` | RAG retrieval system | `process_chunks()`, `query_similar_chunks()` |

### CLI Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `bin/merj.js` | Main CLI entry point | `pull()`, `hasConflicts()` |
| `scripts/review_two_sides_with_cr.py` | CodeRabbit integration | `detect_rebase_context()`, `add_worktree()` |

## Data Flow

### CodeChunk Data Structure

```python
@dataclass
class CodeChunk:
    file_path: str       # Path to source file
    language: str        # Programming language
    signature: str       # Function/class signature
    content: str         # Actual code content
    chunk_type: str      # function/class/imports
    start_line: int      # Line range start
    end_line: int        # Line range end
    node_types: List[str] # AST node types
```

### Data Transformation Pipeline

```
CodeChunk → Embedding Vector → ChromaDB Document → Retrieved Context
```

## Component Connections

### A. chunker.py → embedder.py
- Chunker creates `CodeChunk` objects with code content
- Embedder extracts `content` field for vectorization
- Returns: `[{"chunk": CodeChunk, "embedding": vector}]`

### B. embedder.py → chroma.py
- Embedder output feeds directly into ChromaDB storage
- Chroma unpacks chunk/embedding pairs
- Stores with metadata for efficient filtering

### C. chunk_lca.py (Stage 1 Orchestrator)
```python
# Lines 78-87 show the connection flow:
chunks = chunker.chunk_repository(Path(worktree_path))
results = embed_chunks(chunks)  # embedder.py
insert_to_chroma(results, collection_name=collection_name)  # chroma.py
```

### D. local_remote_rag.py (Stage 2 Retrieval)
- Receives `CodeChunk` objects from conflict processing
- Embeds using same Voyage AI model for consistency
- Queries ChromaDB for k-nearest neighbors
- Returns enhanced context with similarity scores

## Storage Schema

### ChromaDB Document Structure

```python
{
    "id": "file_path:start_line-end_line",
    "document": chunk.content,  # The actual code
    "embedding": [1024 float values],  # Voyage AI vectors
    "metadata": {
        "file_path": str,
        "language": str,
        "chunk_type": str,  # function/class/imports
        "start_line": int,
        "end_line": int
    }
}
```

### Collection Naming Convention
- Format: `lca_YYYYMMDD_<commit_sha[:8]>`
- Example: `lca_20241025_abc123de`

## Execution Paths

### Path 1: Pre-populate ChromaDB with Base Code

```bash
# Automatically finds LCA and chunks repository
python rag_pipeline/chunk_lca.py

# With custom main branch reference
MAIN_REF=origin/develop python rag_pipeline/chunk_lca.py

# JSON output format
python rag_pipeline/chunk_lca.py --json
```

### Path 2: Query for Similar Code (RAG)

```bash
# Basic query
python rag_pipeline/local_remote_rag.py \
  --collection lca_20241025_abc123de \
  --k 5 \
  --threshold 0.5

# Test mode with sample chunks
python rag_pipeline/local_remote_rag.py \
  --collection lca_20241025_abc123de \
  --test

# JSON output
python rag_pipeline/local_remote_rag.py \
  --collection lca_20241025_abc123de \
  --json
```

### Path 3: Demo Complete Flow

```bash
# Run full demonstration
python rag_pipeline/demo.py
```

## Integration Points

### Current Integration Flow

```
Git Conflicts → [MISSING: Conflict Parser] → CodeChunks → local_remote_rag.py
                                                              ↓
                                                    Similar Context
                                                              ↓
                                              [MISSING: Resolution Engine]
```

### Missing Components

1. **Conflict Parser**: Extract and chunk actual conflict markers
2. **Diff Chunker**: Convert git diff output to CodeChunk objects
3. **Resolution Engine**: LLM-based component using RAG context
4. **Integration Script**: Connect RAG output to merge resolution

### Required Integration Code

```python
# Missing: conflict_processor.py
def process_conflicts():
    # 1. Parse conflict files
    # 2. Extract local/remote changes
    # 3. Chunk the changes
    # 4. Pass to local_remote_rag
    # 5. Use context for resolution
```

## Configuration & Deployment

### Environment Variables

```bash
# Required for embeddings
export VOYAGE_API_KEY="your-voyage-ai-api-key"

# Optional: Override main branch reference
export MAIN_REF="origin/main"  # default: origin/main
```

### Installation Requirements

```bash
# Python dependencies
pip install chromadb voyageai tree-sitter-languages

# Node.js dependencies (for CLI)
npm install

# Link CLI globally
npm link
```

### Deployment Checklist

1. **Install all dependencies**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **Configure API keys**
   ```bash
   export VOYAGE_API_KEY="your-key"
   ```

3. **Pre-populate ChromaDB**
   ```bash
   python rag_pipeline/chunk_lca.py
   ```

4. **Verify RAG retrieval**
   ```bash
   python rag_pipeline/local_remote_rag.py --collection lca_* --test
   ```

5. **Test complete pipeline**
   ```bash
   python rag_pipeline/demo.py
   ```

## Testing

### Component Tests

```bash
# Test chunker
python rag_pipeline/chunker.py ./demo_code

# Test embedder (requires API key)
python -c "from rag_pipeline.embedder import embed_chunk; print('OK')"

# Test ChromaDB connection
python -c "import chromadb; client = chromadb.PersistentClient('./my_chroma_db'); print('OK')"
```

### Integration Test Flow

1. Create test repository with conflicts
2. Run `chunk_lca.py` to populate ChromaDB
3. Create sample CodeChunk objects
4. Run `local_remote_rag.py` with test chunks
5. Verify context retrieval accuracy

### RAG Accuracy Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k` | 5 | Number of similar chunks to retrieve |
| `distance_threshold` | 0.5 | Maximum distance (0.0=identical, 1.0=very different) |
| `max_context_length` | None | Optional truncation for LLM context |

### Distance Metrics

- **Cosine Distance**: Used by ChromaDB
- Range: 0.0 (identical) to 1.0 (completely different)
- Typical good matches: < 0.3
- Threshold tuning: Start at 0.5, adjust based on results

## Workflow Summary

### Complete Execution Flow

```python
# Stage 1: Setup (run once per merge conflict)
chunk_lca.py:
  detect_rebase_context() → finds LCA commit
  create_lca_worktree() → temporary git checkout
  Chunker().chunk_repository() → semantic chunks
  embed_chunks() → vectors via Voyage AI
  insert_to_chroma() → store in ChromaDB

# Stage 2: Runtime (for each conflict)
local_remote_rag.py:
  LocalRemoteRAG(collection_name) → connect to DB
  process_chunks(conflict_chunks) → embed & search
  compile_context_for_llm() → format results

# Stage 3: Resolution (not yet implemented)
  [Missing component to use RAG context for resolution]
```

### Key Design Decisions

1. **Tree-sitter for Chunking**: Language-aware parsing for better semantic units
2. **Voyage AI Code Model**: Specialized embeddings for code understanding
3. **ChromaDB**: Local vector database for fast retrieval
4. **Git Worktrees**: Lightweight method to access different commits
5. **Distance Threshold**: Configurable quality control for retrieved context

## Next Steps

### To Complete the Pipeline

1. **Create conflict_extractor.py**
   - Parse git conflict markers
   - Extract local and remote changes
   - Convert to CodeChunk objects

2. **Create merge_resolver.py**
   - Integrate RAG context with LLM
   - Generate resolution suggestions
   - Format output for user review

3. **Update merj.js**
   - Call Python RAG pipeline after CodeRabbit
   - Pass conflict information to RAG system
   - Present enhanced resolution options

4. **Add Integration Tests**
   - End-to-end conflict resolution tests
   - RAG accuracy evaluation
   - Performance benchmarks

5. **Tune Parameters**
   - Optimize distance threshold
   - Adjust k-value for context size
   - Balance speed vs accuracy

## Troubleshooting

### Common Issues

1. **VOYAGE_API_KEY not set**
   ```bash
   export VOYAGE_API_KEY="your-key"
   ```

2. **ChromaDB collection not found**
   - Run `chunk_lca.py` first to create collection
   - Check collection name matches

3. **No chunks retrieved**
   - Verify distance threshold isn't too strict
   - Check if ChromaDB has data: `collection.count()`

4. **Git worktree errors**
   - Ensure no existing worktrees conflict
   - Clean up: `git worktree prune`

### Debug Commands

```bash
# List ChromaDB collections
python -c "import chromadb; c = chromadb.PersistentClient('./my_chroma_db'); print(c.list_collections())"

# Check collection size
python -c "import chromadb; c = chromadb.PersistentClient('./my_chroma_db'); col = c.get_collection('lca_...'); print(col.count())"

# Test embedding
python -c "from rag_pipeline.embedder import embed_chunk; class C: content='test'; print(len(embed_chunk(C())))"
```

## Architecture Strengths

1. **Modular Design**: Each component has single responsibility
2. **Consistent Data Format**: CodeChunk objects throughout
3. **Scalable Storage**: ChromaDB handles large codebases
4. **Language Agnostic**: Tree-sitter supports many languages
5. **Configurable Retrieval**: Tunable parameters for different use cases

## Current Limitations

1. **Incomplete Integration**: Missing connection to actual conflicts
2. **No Resolution Logic**: RAG context not used for suggestions
3. **Limited Testing**: No end-to-end validation
4. **Manual Setup**: Requires manual ChromaDB population
5. **No Evaluation Metrics**: No way to measure retrieval quality

---

*Last Updated: October 2024*
*Version: 1.0 (Pre-integration)*