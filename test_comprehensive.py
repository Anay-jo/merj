#!/usr/bin/env python3
"""
Comprehensive Test Suite for MergeConflictResolver
Tests Flask API, RAG pipeline, LCA detection, and ChromaDB integration
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# For API testing
import requests

# Add paths for local imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_pipeline'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Configuration
BASE_URL = "http://127.0.0.1:5000"
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB")

# Test result tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print('─' * 40)


def test_decorator(test_name: str):
    """Decorator for test functions to track results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"\n🧪 {test_name}...")
            try:
                result = func(*args, **kwargs)
                if result:
                    test_results["passed"] += 1
                    print(f"  ✅ PASSED: {test_name}")
                else:
                    test_results["failed"] += 1
                    print(f"  ❌ FAILED: {test_name}")
                return result
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append({
                    "test": test_name,
                    "error": str(e)
                })
                print(f"  ❌ ERROR in {test_name}: {e}")
                return False
        return wrapper
    return decorator


def git(*args, cwd=None) -> str:
    """Execute git command and return output."""
    cmd = ["git"] + list(args)
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(cmd)}\n{p.stderr or p.stdout}")
    return p.stdout.strip()


def check_server_running() -> bool:
    """Check if Flask server is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# =============================================================================
# API TESTS
# =============================================================================

@test_decorator("API Health Check")
def test_health_check() -> bool:
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print(f"    Status code: {response.status_code}")
            return False

        data = response.json()
        print(f"    API Status: {data.get('api')}")
        print(f"    Voyage API Key: {'✓' if data.get('voyage_api_key') else '✗'}")
        print(f"    ChromaDB: {'✓' if data.get('chromadb') else '✗'}")
        print(f"    Collections: {len(data.get('collections', []))}")

        if 'current_lca' in data:
            lca = data['current_lca']
            print(f"    LCA: {lca['lca'][:8]}")

        return data.get('api') == 'healthy'
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("LCA Detection")
def test_lca_detection() -> bool:
    """Test LCA detection through the API."""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()

        if 'current_lca' in data:
            lca_info = data['current_lca']
            print(f"    LCA Commit: {lca_info['lca']}")
            print(f"    Local Tip: {lca_info['local']}")
            print(f"    Remote Ref: {lca_info['remote']}")
            return True
        else:
            print(f"    LCA detection not available: {data.get('lca_detection', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("LCA Collection Creation")
def test_lca_collection_creation() -> bool:
    """Test creating an LCA-based ChromaDB collection."""
    if not VOYAGE_API_KEY:
        print("    ⚠️  Skipping: No Voyage API key")
        test_results["skipped"] += 1
        return True

    try:
        response = requests.post(
            f"{BASE_URL}/api/lca/create",
            json={}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"    Collection: {data['collection_name']}")
            print(f"    LCA: {data['lca_commit']}")
            return True
        else:
            print(f"    Status: {response.status_code}")
            print(f"    Error: {response.json().get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("Diff Processing with RAG")
def test_diff_processing() -> bool:
    """Test diff processing endpoint with RAG enhancement."""
    test_data = {
        "lbd": [
            {
                "filefrom": "rag_pipeline/chunker.py",
                "lns": [50, 100, 150, 200]
            }
        ],
        "rbd": [
            {
                "filefrom": "rag_pipeline/embedder.py",
                "lns": [10, 20, 30]
            }
        ],
        "k": 3,
        "threshold": 0.5
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/data",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            print(f"    Status: {response.status_code}")
            return False

        data = response.json()
        print(f"    Status: {data.get('status')}")
        print(f"    Local chunks: {data.get('local_chunks', 0)}")
        print(f"    Remote chunks: {data.get('remote_chunks', 0)}")
        print(f"    Similar code found: {data.get('similar_code_found', 0)}")

        if data.get('collection_used'):
            print(f"    Collection: {data['collection_used']}")

        return data.get('status') in ['success', 'partial_success']
    except Exception as e:
        print(f"    Error: {e}")
        return False


# =============================================================================
# UNIT TESTS
# =============================================================================

@test_decorator("Chunker Module Import")
def test_chunker_import() -> bool:
    """Test that chunker module can be imported."""
    try:
        from rag_pipeline.chunker import Chunker
        chunker = Chunker()
        print(f"    Chunker initialized successfully")
        return True
    except Exception as e:
        print(f"    Import error: {e}")
        return False


@test_decorator("Chunker Functionality")
def test_chunker_functionality() -> bool:
    """Test chunking a Python file."""
    try:
        from rag_pipeline.chunker import Chunker

        chunker = Chunker()
        test_file = Path("rag_pipeline/chunker.py")

        if not test_file.exists():
            print(f"    Test file not found: {test_file}")
            return False

        config = {
            "language": "python",
            "top_level_nodes": {
                "function_definition",
                "class_definition",
                "decorated_definition"
            }
        }

        chunks = chunker.chunk_file(test_file, config)
        print(f"    Chunked into {len(chunks)} code objects")

        if chunks:
            sample = chunks[0]
            print(f"    Sample chunk: {sample.file_path}:{sample.start_line}-{sample.end_line}")

        return len(chunks) > 0
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("Embedder Module Import")
def test_embedder_import() -> bool:
    """Test that embedder module can be imported."""
    try:
        from rag_pipeline.embedder import embed_chunks
        print(f"    Embedder imported successfully")
        return True
    except Exception as e:
        print(f"    Import error: {e}")
        return False


@test_decorator("ChromaDB Module Import")
def test_chroma_import() -> bool:
    """Test that ChromaDB module can be imported."""
    try:
        from rag_pipeline.chroma import insert_to_chroma
        import chromadb
        print(f"    ChromaDB modules imported successfully")
        return True
    except Exception as e:
        print(f"    Import error: {e}")
        return False


@test_decorator("ChromaDB Connection")
def test_chromadb_connection() -> bool:
    """Test ChromaDB connection and basic operations."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path='./rag_pipeline/demo_chroma_db')
        collections = client.list_collections()

        print(f"    Connected to ChromaDB")
        print(f"    Collections found: {len(collections)}")

        for col in collections[:3]:  # Show first 3
            print(f"      - {col.name}")

        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@test_decorator("End-to-End RAG Pipeline")
def test_end_to_end_rag() -> bool:
    """Test complete RAG pipeline from chunking to retrieval."""
    if not VOYAGE_API_KEY:
        print("    ⚠️  Skipping: No Voyage API key")
        test_results["skipped"] += 1
        return True

    try:
        from rag_pipeline.chunker import Chunker
        from rag_pipeline.embedder import embed_chunks
        from rag_pipeline.chroma import insert_to_chroma
        import chromadb

        # 1. Chunk a file
        chunker = Chunker()
        test_file = Path("rag_pipeline/chunker.py")
        config = {
            "language": "python",
            "top_level_nodes": {
                "function_definition",
                "class_definition",
                "decorated_definition"
            }
        }
        chunks = chunker.chunk_file(test_file, config)[:2]  # Just test 2 chunks
        print(f"    ✓ Chunked {len(chunks)} objects")

        # 2. Embed chunks
        results = embed_chunks(chunks)
        print(f"    ✓ Generated {len(results)} embeddings")

        # 3. Store in ChromaDB
        collection_name = f"test_collection_{int(time.time())}"
        insert_to_chroma(results, collection_name, "./rag_pipeline/demo_chroma_db")
        print(f"    ✓ Stored in collection: {collection_name}")

        # 4. Verify storage
        client = chromadb.PersistentClient(path='./rag_pipeline/demo_chroma_db')
        collection = client.get_collection(collection_name)
        count = collection.count()
        print(f"    ✓ Verified {count} items in collection")

        # 5. Cleanup
        client.delete_collection(collection_name)
        print(f"    ✓ Cleaned up test collection")

        return count > 0
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("Git Operations")
def test_git_operations() -> bool:
    """Test git operations for LCA detection."""
    try:
        # Get repo root
        repo = git("rev-parse", "--show-toplevel")
        print(f"    Repository: {Path(repo).name}")

        # Get current branch
        branch = git("branch", "--show-current")
        print(f"    Current branch: {branch}")

        # Get HEAD commit
        head = git("rev-parse", "HEAD")
        print(f"    HEAD: {head[:8]}")

        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

@test_decorator("API Response Time")
def test_api_performance() -> bool:
    """Test API response times."""
    endpoints = [
        ("GET", "/api/health", None),
    ]

    all_passed = True
    for method, endpoint, data in endpoints:
        start = time.time()

        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data or {})

            elapsed = time.time() - start
            status = "✓" if elapsed < 1.0 else "⚠️"
            print(f"    {status} {method} {endpoint}: {elapsed:.3f}s")

            if elapsed > 2.0:
                all_passed = False
        except Exception as e:
            print(f"    ✗ {method} {endpoint}: {e}")
            all_passed = False

    return all_passed


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@test_decorator("Invalid Endpoint Handling")
def test_invalid_endpoint() -> bool:
    """Test handling of invalid endpoints."""
    try:
        response = requests.get(f"{BASE_URL}/api/nonexistent")
        print(f"    Status code: {response.status_code}")
        return response.status_code == 404
    except Exception as e:
        print(f"    Error: {e}")
        return False


@test_decorator("Malformed Request Handling")
def test_malformed_request() -> bool:
    """Test handling of malformed requests."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/data",
            data="not json",
            headers={'Content-Type': 'application/json'}
        )
        print(f"    Status code: {response.status_code}")
        return response.status_code in [400, 500]
    except Exception as e:
        print(f"    Error: {e}")
        return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_tests(test_suite: str = "all", start_server: bool = False):
    """Run the comprehensive test suite."""
    print_header("COMPREHENSIVE TEST SUITE")
    print(f"Test Suite: {test_suite.upper()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check server
    if not check_server_running():
        if start_server:
            print("\n⚠️  Flask server not running. Starting server...")
            # Start server in background
            subprocess.Popen(
                [sys.executable, "flask_backend/app.py"],
                env={**os.environ, "VOYAGE_API_KEY": VOYAGE_API_KEY}
            )
            time.sleep(3)
        else:
            print("\n❌ Flask server is not running!")
            print("   Start the server with: python flask_backend/app.py")
            print("   Or run tests with --start-server flag")
            return 1
    else:
        print("\n✅ Flask server is running")

    # Run test suites
    if test_suite in ["all", "api"]:
        print_header("API TESTS")
        test_health_check()
        test_lca_detection()
        test_lca_collection_creation()
        test_diff_processing()
        test_invalid_endpoint()
        test_malformed_request()

    if test_suite in ["all", "unit"]:
        print_header("UNIT TESTS")
        test_chunker_import()
        test_chunker_functionality()
        test_embedder_import()
        test_chroma_import()
        test_chromadb_connection()
        test_git_operations()

    if test_suite in ["all", "integration"]:
        print_header("INTEGRATION TESTS")
        test_end_to_end_rag()

    if test_suite in ["all", "performance"]:
        print_header("PERFORMANCE TESTS")
        test_api_performance()

    # Print summary
    print_header("TEST SUMMARY")
    total = test_results["passed"] + test_results["failed"]
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    if test_results["skipped"] > 0:
        print(f"⚠️  Skipped: {test_results['skipped']}")

    if test_results["errors"]:
        print("\nErrors encountered:")
        for error in test_results["errors"]:
            print(f"  • {error['test']}: {error['error']}")

    success_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if test_results["failed"] == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {test_results['failed']} test(s) failed")
        return 1


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Comprehensive test suite for MergeConflictResolver")
    parser.add_argument(
        "--suite",
        choices=["all", "api", "unit", "integration", "performance"],
        default="all",
        help="Test suite to run (default: all)"
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start Flask server if not running"
    )
    parser.add_argument(
        "--api-key",
        help="Voyage API key for testing"
    )

    args = parser.parse_args()

    # Set API key if provided
    if args.api_key:
        global VOYAGE_API_KEY
        VOYAGE_API_KEY = args.api_key
        os.environ["VOYAGE_API_KEY"] = args.api_key

    # Run tests
    sys.exit(run_tests(args.suite, args.start_server))


if __name__ == "__main__":
    main()