# Flask Backend with RAG Pipeline Integration

## Overview
Flask backend that receives diff data from the merj CLI tool and processes it through the RAG (Retrieval-Augmented Generation) pipeline for enhanced merge conflict resolution.

## Setup Instructions

### Step 1: Create Virtual Environment
```bash
cd flask_backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Environment Variables
```bash
export VOYAGE_API_KEY="your-voyage-ai-api-key"
```

### Step 4: Prepare ChromaDB (from project root)
```bash
python rag_pipeline/chunk_lca.py  # Populate knowledge base
```

### Step 5: Run the Flask Server
```bash
python app.py
```

The server will start on http://127.0.0.1:5000

## API Endpoints

### Health Check
**GET** `/api/health`

Check RAG pipeline status:
```json
{
    "api": "healthy",
    "voyage_api_key": true,
    "chromadb": true,
    "collections": ["demo_code_chunks"]
}
```

### Process Diff Data
**POST** `/api/data`

Process git diff data through RAG pipeline.

Request body:
```json
{
    "lbd": [
        {"filefrom": "src/file.js", "lns": [11, 12, 30]}
    ],
    "rbd": [
        {"filefrom": "src/file.js", "lns": [15, 16, 35]}
    ],
    "collection": "demo_code_chunks",  // Optional
    "k": 5,                            // Optional: neighbors to retrieve
    "threshold": 0.5                   // Optional: distance threshold
}
```

Response:
```json
{
    "message": "Diff data processed with RAG enhancement",
    "status": "success",
    "local_chunks": 3,
    "remote_chunks": 2,
    "total_chunks": 5,
    "similar_code_found": 12,
    "rag_results": { /* Full RAG results */ }
}
```

## Testing

Run the test script:
```bash
python test_api.py
```

## Project Structure
```
flask_backend/
├── app.py              # Main Flask application with RAG integration
├── requirements.txt    # Python dependencies
├── test_api.py        # API testing script
├── venv/              # Virtual environment (created after setup)
└── README.md          # This file
```

## Dependencies
- Flask 2.3.3: Web framework
- Flask-CORS 4.0.0: Cross-Origin Resource Sharing support
- chromadb: Vector database for code similarity search
- voyageai: Code embedding service
- tree-sitter-languages: Code parsing for chunking

## RAG Pipeline Features

1. **Code Chunking**: Extracts functions containing conflict lines using Tree-sitter
2. **Semantic Embedding**: Creates code embeddings via Voyage AI (voyage-code-3 model)
3. **Similarity Search**: Finds k-nearest neighbors from LCA codebase
4. **Context Enhancement**: Returns relevant historical code patterns for better resolution

## Error Handling

The API gracefully handles RAG pipeline failures:
- If VOYAGE_API_KEY is not set, returns partial success
- If ChromaDB is unavailable, falls back to basic diff processing
- All errors are logged and returned in the response

## Integration with Merj CLI

This backend is designed to work with the merj CLI tool. When merge conflicts are detected:
1. Merj sends diff data to this Flask backend
2. Backend processes diffs through RAG pipeline
3. Returns enhanced context with similar code examples
4. Merj uses this context to suggest better conflict resolutions