#!/usr/bin/env python3
"""
Flask Backend for Merj Merge Conflict Tool
Receives diff data from merj.js and processes it through RAG pipeline
Includes LCA detection and knowledge base creation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for rag_pipeline imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import RAG pipeline components
from rag_pipeline.local_remote_rag import process_git_diff_json
from rag_pipeline.chunker import Chunker
from rag_pipeline.embedder import embed_chunks
from rag_pipeline.chroma import insert_to_chroma

# Import LCA detection from scripts
try:
    from review_two_sides_with_cr import detect_rebase_context, git, repo_root
except ImportError:
    # Fallback implementations if script not available
    def git(*args, cwd=None):
        """Run git command and return output."""
        cmd = ["git"] + list(args)
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        if p.returncode != 0:
            raise RuntimeError(f"git command failed: {' '.join(cmd)}\n{p.stderr or p.stdout}")
        return p.stdout.strip()

    def repo_root():
        """Get repository root."""
        return git("rev-parse", "--show-toplevel")

    def detect_rebase_context(repo):
        """Detect LCA and branch tips."""
        # Get current HEAD
        local_tip = git("rev-parse", "HEAD", cwd=repo)
        # Get main branch reference
        main_ref = os.environ.get("MAIN_REF", "origin/main")
        # Find merge base (LCA)
        base = git("merge-base", local_tip, main_ref, cwd=repo)
        return base, local_tip, main_ref

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for requests from Node.js frontend

# Global cache for LCA collections
lca_cache = {}

def create_worktree(repo_path: str, commit: str, worktree_name: str = None) -> str:
    """
    Create a git worktree for a specific commit.
    Returns the path to the worktree.
    """
    if worktree_name is None:
        # Generate unique name based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worktree_name = f"lca_worktree_{timestamp}"

    # Create worktree in temp directory
    worktree_path = os.path.join(tempfile.gettempdir(), worktree_name)

    # Remove if exists
    if os.path.exists(worktree_path):
        cleanup_worktree(repo_path, worktree_path)

    # Create new worktree
    git("worktree", "add", worktree_path, commit, cwd=repo_path)
    return worktree_path

def cleanup_worktree(repo_path: str, worktree_path: str):
    """
    Clean up a git worktree.
    """
    try:
        # Remove worktree from git
        git("worktree", "remove", worktree_path, "--force", cwd=repo_path)
    except:
        # If git removal fails, try manual cleanup
        if os.path.exists(worktree_path):
            shutil.rmtree(worktree_path, ignore_errors=True)

def get_or_create_lca_collection(lca_commit: str, repo_path: str, collection_prefix: str = "lca") -> str:
    """
    Get or create a ChromaDB collection for the LCA commit.
    Returns the collection name.
    """
    collection_name = f"{collection_prefix}_{lca_commit[:8]}"

    # Check cache
    if collection_name in lca_cache:
        print(f"✅ Using cached LCA collection: {collection_name}")
        return collection_name

    # Check if collection exists in ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path='./rag_pipeline/demo_chroma_db')
        existing_collections = [col.name for col in client.list_collections()]

        if collection_name in existing_collections:
            print(f"✅ Found existing LCA collection: {collection_name}")
            lca_cache[collection_name] = True
            return collection_name
    except Exception as e:
        print(f"⚠️  ChromaDB check failed: {e}")

    # Create new collection from LCA
    print(f"🔨 Creating new LCA collection: {collection_name}")
    worktree_path = None

    try:
        # Create worktree at LCA
        worktree_path = create_worktree(repo_path, lca_commit)
        print(f"📁 Created worktree at: {worktree_path}")

        # Initialize chunker
        chunker = Chunker()

        # Process all Python files in the worktree
        all_chunks = []
        for root, dirs, files in os.walk(worktree_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        # Chunk the file directly using its path
                        # Use full Python config with top_level_nodes
                        config = {
                            "language": "python",
                            "top_level_nodes": {
                                "function_definition",
                                "class_definition",
                                "decorated_definition"
                            }
                        }
                        file_chunks = chunker.chunk_file(Path(file_path), config)
                        all_chunks.extend(file_chunks)
                    except Exception as e:
                        print(f"⚠️  Error processing {file_path}: {e}")

        print(f"📊 Chunked {len(all_chunks)} code objects from LCA")

        if all_chunks:
            # Embed chunks - this returns list of {"chunk": chunk, "embedding": vector}
            results = embed_chunks(all_chunks)
            print(f"🔢 Generated {len(results)} embeddings")

            # Store in ChromaDB
            insert_to_chroma(
                results,
                collection_name=collection_name,
                db_path='./rag_pipeline/demo_chroma_db'
            )
            print(f"💾 Stored in ChromaDB collection: {collection_name}")

            # Cache the collection
            lca_cache[collection_name] = True
        else:
            print(f"⚠️  No Python files found in LCA worktree")

    except Exception as e:
        print(f"❌ Error creating LCA collection: {e}")
        raise
    finally:
        # Cleanup worktree
        if worktree_path:
            cleanup_worktree(repo_path, worktree_path)
            print(f"🧹 Cleaned up worktree")

    return collection_name

@app.route('/api/data', methods=['POST'])
def receive_diff_data():
    """
    POST endpoint to receive diff data from merj.js
    Expected JSON structure:
    {
        "lbd": [...],  # Local vs Base diff
        "rbd": [...],  # Remote vs Base diff  
        "lrd": [...]   # Local vs Remote diff
    }
    """
    try:
        # Get JSON data from request body
        data = request.get_json()
        # Validate that data was received
        if not data:
            return jsonify({
                'error': 'No JSON data received',
                'status': 'error'
            }), 400
        # Extract diff data
        remote_vs_base_diff = data.get('rbd', [])
        local_vs_base_diff = data.get('lbd', [])

        # Combine into expected format for RAG pipeline
        diff_input = {
            "lbd": local_vs_base_diff,
            "rbd": remote_vs_base_diff
        }

        # Process through RAG pipeline
        try:
            # Check if API key is available
            if not os.environ.get("VOYAGE_API_KEY"):
                print("⚠️  Warning: VOYAGE_API_KEY not set, RAG features disabled")
                raise ValueError("VOYAGE_API_KEY not configured")

            # Detect LCA and get repository root
            print("🔍 Detecting LCA (Least Common Ancestor)...")
            try:
                repo = repo_root()
                lca_commit, local_tip, remote_ref = detect_rebase_context(repo)
                print(f"📍 LCA detected: {lca_commit[:8]}")
                print(f"   Local tip: {local_tip[:8]}")
                print(f"   Remote ref: {remote_ref}")

                # Get or create LCA collection
                collection_name = get_or_create_lca_collection(
                    lca_commit,
                    repo,
                    collection_prefix=data.get('collection_prefix', 'lca')
                )
                print(f"📚 Using collection: {collection_name}")

            except Exception as lca_error:
                print(f"⚠️  LCA detection failed: {lca_error}")
                print("   Falling back to default collection")
                # Fall back to default collection if LCA detection fails
                collection_name = data.get('collection', 'demo_code_chunks')

            # Process diffs through RAG pipeline
            print(f"📝 Processing diffs through RAG pipeline...")
            print(f"   Local diffs: {len(local_vs_base_diff)} files")
            print(f"   Remote diffs: {len(remote_vs_base_diff)} files")

            rag_results = process_git_diff_json(
                diff_input,
                collection_name=collection_name,
                k=data.get('k', 5),  # Allow client to specify k
                distance_threshold=data.get('threshold', 0.5),
                db_path='./rag_pipeline/demo_chroma_db',
                verbose=False,  # Don't print to console in API
                save_to_file=True,  # Save RAG context for LLM
                output_dir='../rag_output'  # Output directory for files (relative to flask_backend)
            )

            # Return enhanced results
            response_data = {
                'message': 'Diff data processed with RAG enhancement',
                'status': 'success',
                'local_chunks': len(rag_results.get('local_chunks', [])),
                'remote_chunks': len(rag_results.get('remote_chunks', [])),
                'total_chunks': rag_results.get('total_chunks', 0),
                'similar_code_found': sum(len(r.get('similar_code', [])) for r in rag_results.get('rag_results', [])),
                'collection_used': collection_name,
                'rag_results': rag_results  # Full results for client processing
            }

            # Add LCA info if available
            if 'lca_commit' in locals():
                response_data['lca_info'] = {
                    'lca_commit': lca_commit[:8],
                    'local_tip': local_tip[:8],
                    'remote_ref': remote_ref
                }

            return jsonify(response_data), 200

        except Exception as rag_error:
            print(f"⚠️  RAG processing error: {rag_error}")
            # Fallback to basic response if RAG fails
            return jsonify({
                'message': 'Diff data received (RAG unavailable)',
                'status': 'partial_success',
                'warning': f'RAG enhancement failed: {str(rag_error)}',
                'data_received': {
                    'local_diffs': len(local_vs_base_diff),
                    'remote_diffs': len(remote_vs_base_diff)
                }
            }), 200
        
    except Exception as e:
        # Handle any errors
        print(f"❌ Error processing request: {str(e)}")
        return jsonify({
            'error': f'Failed to process request: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/lca/create', methods=['POST'])
def create_lca_collection():
    """
    Endpoint to explicitly create an LCA collection
    Expected JSON:
    {
        "lca_commit": "commit_sha",  # Optional, will auto-detect if not provided
        "collection_prefix": "lca",  # Optional prefix for collection name
        "force_recreate": false  # Optional, force recreation even if exists
    }
    """
    try:
        data = request.get_json() or {}

        # Get LCA commit (auto-detect if not provided)
        lca_commit = data.get('lca_commit')
        if not lca_commit:
            print("🔍 Auto-detecting LCA...")
            repo = repo_root()
            lca_commit, local_tip, remote_ref = detect_rebase_context(repo)
            print(f"📍 Detected LCA: {lca_commit[:8]}")
        else:
            repo = repo_root()
            print(f"📍 Using provided LCA: {lca_commit[:8]}")

        # Force recreate if requested
        collection_prefix = data.get('collection_prefix', 'lca')
        if data.get('force_recreate'):
            collection_name = f"{collection_prefix}_{lca_commit[:8]}"
            if collection_name in lca_cache:
                del lca_cache[collection_name]
            print(f"🔄 Force recreating collection: {collection_name}")

        # Create or get collection
        collection_name = get_or_create_lca_collection(
            lca_commit,
            repo,
            collection_prefix=collection_prefix
        )

        return jsonify({
            'status': 'success',
            'message': f'LCA collection created/retrieved successfully',
            'collection_name': collection_name,
            'lca_commit': lca_commit[:8]
        }), 200

    except Exception as e:
        print(f"❌ Error creating LCA collection: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify RAG pipeline status
    """
    try:
        import chromadb

        health_status = {
            'api': 'healthy',
            'voyage_api_key': bool(os.environ.get("VOYAGE_API_KEY")),
            'chromadb': False,
            'collections': [],
            'lca_cache': list(lca_cache.keys())
        }

        # Try to connect to ChromaDB
        try:
            client = chromadb.PersistentClient(path='./rag_pipeline/demo_chroma_db')
            collections = client.list_collections()
            health_status['chromadb'] = True
            health_status['collections'] = [col.name for col in collections]

            # Identify LCA collections
            health_status['lca_collections'] = [
                col.name for col in collections
                if col.name.startswith('lca_')
            ]
        except Exception as e:
            health_status['chromadb_error'] = str(e)

        # Try to detect current LCA
        try:
            repo = repo_root()
            lca_commit, local_tip, remote_ref = detect_rebase_context(repo)
            health_status['current_lca'] = {
                'lca': lca_commit[:8],
                'local': local_tip[:8],
                'remote': remote_ref
            }
        except Exception as e:
            health_status['lca_detection'] = f"Not available: {str(e)}"

        return jsonify(health_status), 200

    except Exception as e:
        return jsonify({
            'api': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
