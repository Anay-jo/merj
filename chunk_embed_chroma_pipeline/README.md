# Tree-sitter Code Chunker

A powerful, multi-language code chunking tool that uses Tree-sitter to split code repositories into syntactically complete and semantically meaningful chunks for use in RAG systems and vector databases.

## Features

- **Multi-Language Support**: Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, Ruby, PHP, and more
- **Semantic Chunking**: Preserves syntactic completeness by chunking at function/class boundaries
- **Fast Processing**: Built on Tree-sitter's high-performance C library
- **Consistent Output**: JSON format with metadata for easy vectorization
- **Smart Filtering**: Automatically ignores binary files, build artifacts, and non-code files

## Installation

```bash
pip install -r requirements.txt
```

That's it! No compilation or grammar building required.

## Quick Start

### Basic Usage

Chunk an entire repository:
```bash
python chunker.py /path/to/repository
```

This will scan the repository and save chunks to `repo_chunks.json`.

### With Options

```bash
python chunker.py /path/to/repo --output my_chunks.json
```

Options:
- `--output`: Specify output JSON file path (default: `repo_chunks.json`)

### Demo

Run the included demo to see it in action:
```bash
python demo.py
```

## Output Format

The chunker produces JSON output with consistent structure for vectorization:

```json
{
  "file_path": "path/to/file.py",
  "language": "python",
  "content": "def my_function():\n    return 42",
  "chunk_type": "function",
  "start_line": 10,
  "end_line": 11,
  "node_types": ["function_definition"]
}
```

### Key Fields

- **`content`**: The actual code to be vectorized/embedded
- **`chunk_type`**: Semantic type (function, class, imports_and_globals, etc.)
- **`file_path`**: Source file location
- **`language`**: Programming language
- **`start_line`/`end_line`**: Line numbers in original file
- **`node_types`**: AST node types for advanced filtering

## Supported Languages

| Language   | Extensions              | Chunk Types                         |
|------------|-------------------------|-------------------------------------|
| Python     | .py, .pyw, .pyi         | Functions, Classes, Decorators      |
| JavaScript | .js, .mjs, .cjs         | Functions, Classes, Exports         |
| TypeScript | .ts, .tsx               | Functions, Classes, Interfaces      |
| Go         | .go                     | Functions, Methods, Types           |
| Rust       | .rs                     | Functions, Impls, Structs, Traits   |
| Java       | .java                   | Classes, Interfaces, Methods        |
| C++        | .cpp, .cc, .hpp, .h     | Functions, Classes, Namespaces      |
| C          | .c, .h                  | Functions, Structs, Unions          |
| Ruby       | .rb                     | Methods, Classes, Modules           |
| PHP        | .php                    | Functions, Classes, Traits          |

## Integration with RAG Systems

### Example: Creating Embeddings

```python
import json
from your_embedding_model import create_embedding
from your_vector_db import VectorDB

# Load chunks
with open('repo_chunks.json', 'r') as f:
    chunks = json.load(f)

# Create embeddings and store
db = VectorDB()
for chunk in chunks:
    # Embed the code content
    embedding = create_embedding(chunk['content'])

    # Store with metadata for retrieval
    db.insert(
        vector=embedding,
        metadata={
            'file': chunk['file_path'],
            'language': chunk['language'],
            'type': chunk['chunk_type'],
            'lines': f"{chunk['start_line']}-{chunk['end_line']}"
        }
    )
```

### Semantic Search

```python
# Query your vector database
query_embedding = create_embedding("function to calculate fibonacci")
results = db.search(query_embedding, top_k=5)

# Results include the original code chunks with context
for result in results:
    print(f"File: {result.metadata['file']}")
    print(f"Type: {result.metadata['type']}")
    print(result.content)
```

## How It Works

1. **Language Detection**: Identifies programming language by file extension
2. **Tree-sitter Parsing**: Parses each file into a Concrete Syntax Tree (CST)
3. **Semantic Chunking**: Identifies functions, classes, and other top-level constructs
4. **Metadata Extraction**: Records file paths, line numbers, and chunk types
5. **JSON Output**: Saves chunks with consistent structure for vectorization

## Architecture

```
Repository
    ↓
File Scanner → Language Detection → Tree-sitter Parser
    ↓
Semantic Chunker → JSON Output
    ↓
Vector Database / RAG System
```

## Performance

- Processes ~1000 files/second on modern hardware
- Memory efficient with Tree-sitter's streaming parser
- Output size typically 1.5-2x the source code size

## Customization

### Modifying Chunk Types

Edit the `LANGUAGE_MAP` in `chunker.py` to customize what constitutes a chunk:

```python
".py": {
    "language": "python",
    "top_level_nodes": {
        "function_definition",
        "class_definition",
        # Add more node types as needed
    }
}
```

### Filtering Files

Modify `IGNORED_DIRS` and `IGNORED_EXTENSIONS` in `chunker.py`:

```python
IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__",
    "my_custom_build_dir",  # Add custom directories
}
```

## Use Cases

- **AI Code Understanding**: Feed chunks to LLMs for code analysis
- **Semantic Code Search**: Build searchable code knowledge bases
- **Documentation Generation**: Extract functions/classes for documentation
- **Code Review**: Analyze code at the semantic level
- **RAG Applications**: Enable code-aware AI assistants

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Areas for improvement:
- Additional language support
- Streaming for very large repositories
- Direct integration with popular vector databases
- Chunk size optimization based on model constraints