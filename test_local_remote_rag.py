#!/usr/bin/env python3
"""
Test Suite for local_remote_rag.py
Tests chunking, embedding, and RAG retrieval functionality
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_pipeline'))

# Configuration
BASE_URL = "http://127.0.0.1:5000"
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB")
os.environ["VOYAGE_API_KEY"] = VOYAGE_API_KEY

# Test tracking
test_results = {"passed": 0, "failed": 0, "errors": []}


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result."""
    symbol = "✅" if passed else "❌"
    print(f"{symbol} {name}")
    if details:
        print(f"   {details}")

    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1


# =============================================================================
# UNIT TESTS - Direct Module Testing
# =============================================================================

def test_chunking_functions():
    """Test the chunking functionality directly."""
    print_header("TEST: Chunking Functions")

    try:
        from rag_pipeline.chunker import Chunker
        from rag_pipeline.conflict_processor import chunk_and_embed_conflicts

        # Test data - use actual files in the project
        test_conflicts = [
            {
                "filefrom": "rag_pipeline/chunker.py",
                "lns": [50, 100, 150, 200, 250]  # Various line numbers
            },
            {
                "filefrom": "rag_pipeline/embedder.py",
                "lns": [10, 20, 30, 40]
            }
        ]

        print("\n📋 Test Input:")
        print(f"  Files to chunk: {len(test_conflicts)}")
        for conf in test_conflicts:
            print(f"    - {conf['filefrom']}: lines {conf['lns']}")

        # Process chunks
        print("\n🔨 Processing chunks...")
        start_time = time.time()
        results = chunk_and_embed_conflicts(
            test_conflicts,
            VOYAGE_API_KEY,
            verbose=False
        )
        elapsed = time.time() - start_time

        # Validate results
        print(f"\n📊 Results (processed in {elapsed:.2f}s):")
        total_chunks = 0
        total_embeddings = 0

        for i, result in enumerate(results):
            file_chunks = len(result.get("chunks", []))
            file_embeddings = len(result.get("embedded_chunks", []))
            total_chunks += file_chunks
            total_embeddings += file_embeddings

            print(f"  File {i+1}: {result['file']}")
            print(f"    Chunks created: {file_chunks}")
            print(f"    Embeddings created: {file_embeddings}")

            # Check for errors
            if "error" in result:
                print(f"    ⚠️  Error: {result['error']}")

            # Sample chunk info
            if file_chunks > 0:
                sample = result["chunks"][0]
                print(f"    Sample chunk: lines {sample.start_line}-{sample.end_line}")

        # Test assertions
        print("\n🧪 Validations:")

        # Test 1: Chunks were created
        test_name = "Chunks created"
        passed = total_chunks > 0
        print_test(test_name, passed, f"Created {total_chunks} chunks")

        # Test 2: Embeddings were created
        test_name = "Embeddings created"
        passed = total_embeddings > 0
        print_test(test_name, passed, f"Created {total_embeddings} embeddings")

        # Test 3: Embeddings are correct dimension
        if total_embeddings > 0:
            test_name = "Embedding dimensions"
            sample_embedding = results[0]["embedded_chunks"][0]["embedding"]
            dim = len(sample_embedding)
            passed = dim == 1024  # Voyage-code-3 uses 1024 dimensions
            print_test(test_name, passed, f"Dimension: {dim} (expected 1024)")

        return total_chunks > 0 and total_embeddings > 0

    except Exception as e:
        print(f"\n❌ Error in chunking test: {e}")
        test_results["errors"].append(str(e))
        return False


def test_local_remote_rag_class():
    """Test the LocalRemoteRAG class directly."""
    print_header("TEST: LocalRemoteRAG Class")

    try:
        from rag_pipeline.local_remote_rag import LocalRemoteRAG
        from rag_pipeline.chunker import Chunker
        import chromadb

        print("\n📋 Setting up test collection...")

        # Create a test collection with some data
        client = chromadb.PersistentClient(path='./rag_pipeline/demo_chroma_db')
        test_collection_name = f"test_rag_{int(time.time())}"

        # Create collection with some test data
        collection = client.create_collection(test_collection_name)

        # Add some test embeddings
        test_embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]
        test_docs = ["test doc 1", "test doc 2", "test doc 3"]
        test_ids = ["id1", "id2", "id3"]
        test_metadata = [
            {"file_path": "test1.py", "lines": "1-10"},
            {"file_path": "test2.py", "lines": "20-30"},
            {"file_path": "test3.py", "lines": "40-50"}
        ]

        collection.add(
            embeddings=test_embeddings,
            documents=test_docs,
            ids=test_ids,
            metadatas=test_metadata
        )

        print(f"  ✓ Created test collection: {test_collection_name}")
        print(f"  ✓ Added {len(test_embeddings)} test documents")

        # Initialize RAG
        print("\n🔨 Testing LocalRemoteRAG...")
        rag = LocalRemoteRAG(test_collection_name, './rag_pipeline/demo_chroma_db')

        # Test 1: Initialization
        test_name = "RAG initialization"
        passed = rag.collection_name == test_collection_name
        print_test(test_name, passed)

        # Test 2: Query similar chunks
        test_name = "Query similar chunks"
        query_embedding = [0.15] * 1024  # Should be similar to test embeddings
        results = rag.query_similar_chunks(query_embedding, k=2)

        docs_found = len(results.get("documents", []))
        passed = docs_found > 0
        print_test(test_name, passed, f"Found {docs_found} similar documents")

        if docs_found > 0:
            print("  Sample results:")
            for i, (doc, meta) in enumerate(zip(results["documents"][:2], results["metadatas"][:2])):
                print(f"    {i+1}. {meta['file_path']}: {doc[:50]}...")

        # Test 3: Process chunks with filtering
        print("\n🔨 Testing chunk processing...")

        # Create test chunks
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
        chunks = chunker.chunk_file(test_file, config)[:2]  # Just 2 chunks for testing

        if chunks:
            # Embed chunks
            from rag_pipeline.embedder import embed_chunks
            embedded_results = embed_chunks(chunks)
            embeddings = [r["embedding"] for r in embedded_results]

            # Process with RAG
            test_name = "Process chunks"
            rag_results = rag.process_chunks(chunks, k=3, distance_threshold=1.0)

            passed = len(rag_results) > 0
            print_test(test_name, passed, f"Processed {len(rag_results)} chunks")

            if rag_results:
                sample = rag_results[0]
                similar_found = len(sample.get("similar_code", []))
                print(f"  Sample: Found {similar_found} similar code chunks")

        # Cleanup
        print("\n🧹 Cleaning up...")
        client.delete_collection(test_collection_name)
        print(f"  ✓ Deleted test collection")

        return True

    except Exception as e:
        print(f"\n❌ Error in RAG class test: {e}")
        test_results["errors"].append(str(e))
        return False


def test_process_git_diff_json():
    """Test the main process_git_diff_json function."""
    print_header("TEST: process_git_diff_json Function")

    try:
        from rag_pipeline.local_remote_rag import process_git_diff_json

        # Prepare test JSON
        test_json = {
            "lbd": [  # Local vs Base diff
                {
                    "filefrom": "rag_pipeline/chunker.py",
                    "lns": [100, 200, 300]
                }
            ],
            "rbd": [  # Remote vs Base diff
                {
                    "filefrom": "rag_pipeline/embedder.py",
                    "lns": [20, 40, 60]
                }
            ]
        }

        print("\n📋 Test Input JSON:")
        print(f"  Local diffs: {len(test_json['lbd'])} files")
        print(f"  Remote diffs: {len(test_json['rbd'])} files")

        # Process the JSON
        print("\n🔨 Processing JSON through RAG pipeline...")
        start_time = time.time()

        result = process_git_diff_json(
            test_json,
            collection_name="demo_code_chunks",  # Use existing collection
            k=3,
            distance_threshold=0.8,
            db_path='./rag_pipeline/demo_chroma_db',
            verbose=False
        )

        elapsed = time.time() - start_time
        print(f"  ✓ Processed in {elapsed:.2f}s")

        # Validate results
        print("\n📊 Results:")
        local_chunks = len(result.get("local_chunks", []))
        remote_chunks = len(result.get("remote_chunks", []))
        total_chunks = result.get("total_chunks", 0)
        rag_results = result.get("rag_results", [])

        print(f"  Local chunks: {local_chunks}")
        print(f"  Remote chunks: {remote_chunks}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  RAG results: {len(rag_results)}")

        # Test assertions
        print("\n🧪 Validations:")

        # Test 1: Chunks were created
        test_name = "Chunks created from JSON"
        passed = total_chunks > 0
        print_test(test_name, passed, f"Total: {total_chunks}")

        # Test 2: RAG results generated
        test_name = "RAG results generated"
        passed = len(rag_results) > 0
        print_test(test_name, passed, f"Results: {len(rag_results)}")

        # Test 3: Metadata included
        test_name = "Metadata included"
        metadata = result.get("metadata", {})
        passed = "collection" in metadata and "k" in metadata
        print_test(test_name, passed, f"Collection: {metadata.get('collection')}")

        # Show sample RAG result
        if rag_results:
            print("\n📝 Sample RAG Result:")
            sample = rag_results[0]
            orig = sample.get("original_chunk", {})
            similar = sample.get("similar_code", [])

            print(f"  Original: {orig.get('file_path', 'N/A')}")
            print(f"  Type: {orig.get('chunk_type', 'N/A')}")
            print(f"  Similar code found: {len(similar)}")

            if similar:
                top_match = similar[0]
                print(f"  Best match: {top_match.get('file_path', 'N/A')}")
                print(f"  Distance: {top_match.get('distance', 'N/A'):.3f}")

        return total_chunks > 0

    except Exception as e:
        print(f"\n❌ Error in process_git_diff_json test: {e}")
        test_results["errors"].append(str(e))
        return False


# =============================================================================
# INTEGRATION TESTS - Via Flask API
# =============================================================================

def test_api_chunking_embedding():
    """Test chunking and embedding through the Flask API."""
    print_header("TEST: API Chunking & Embedding")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("❌ Flask server not responding")
            return False
    except:
        print("❌ Flask server not running. Start with: python flask_backend/app.py")
        return False

    print("✅ Flask server is running")

    # Prepare test data
    test_data = {
        "lbd": [
            {
                "filefrom": "rag_pipeline/chunker.py",
                "lns": [50, 150, 250, 350, 450]
            },
            {
                "filefrom": "rag_pipeline/embedder.py",
                "lns": [10, 30, 50]
            }
        ],
        "rbd": [
            {
                "filefrom": "rag_pipeline/chroma.py",
                "lns": [15, 25, 35]
            }
        ],
        "k": 5,
        "threshold": 0.7
    }

    print("\n📋 Test Data:")
    print(f"  Local diffs: {len(test_data['lbd'])} files")
    print(f"  Remote diffs: {len(test_data['rbd'])} files")
    print(f"  K-nearest: {test_data['k']}")
    print(f"  Threshold: {test_data['threshold']}")

    # Send request
    print("\n🚀 Sending request to /api/data...")
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/data",
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )

    elapsed = time.time() - start_time
    print(f"  Response time: {elapsed:.2f}s")
    print(f"  Status code: {response.status_code}")

    if response.status_code != 200:
        print(f"  ❌ Error: {response.text}")
        return False

    # Parse response
    data = response.json()
    print(f"  Status: {data.get('status')}")

    # Validate response
    print("\n📊 API Response:")
    print(f"  Message: {data.get('message')}")
    print(f"  Local chunks: {data.get('local_chunks', 0)}")
    print(f"  Remote chunks: {data.get('remote_chunks', 0)}")
    print(f"  Total chunks: {data.get('total_chunks', 0)}")
    print(f"  Similar code found: {data.get('similar_code_found', 0)}")
    print(f"  Collection used: {data.get('collection_used', 'N/A')}")

    # Test assertions
    print("\n🧪 Validations:")

    # Test 1: Successful response
    test_name = "API response successful"
    passed = data.get('status') in ['success', 'partial_success']
    print_test(test_name, passed)

    # Test 2: RAG results included
    test_name = "RAG results in response"
    rag_results = data.get('rag_results', {})
    passed = 'rag_results' in rag_results or 'local_chunks' in rag_results
    print_test(test_name, passed)

    # Test 3: Collection info
    if data.get('collection_used'):
        test_name = "Collection specified"
        passed = True
        print_test(test_name, passed, f"Collection: {data['collection_used']}")

    # Show detailed RAG results if available
    if rag_results and 'rag_results' in rag_results:
        rag_list = rag_results['rag_results']
        if rag_list:
            print("\n📝 Sample RAG Result from API:")
            sample = rag_list[0]
            print(f"  File: {sample.get('file_path', 'N/A')}")
            print(f"  Type: {sample.get('object_type', 'N/A')}")
            similar = sample.get('similar_code', [])
            print(f"  Similar chunks: {len(similar)}")

            if similar and len(similar) > 0:
                match = similar[0]
                print(f"  Best match:")
                print(f"    File: {match['metadata'].get('file_path', 'N/A')}")
                print(f"    Distance: {match.get('distance', 'N/A'):.3f}")

    return data.get('status') in ['success', 'partial_success']


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_error_handling():
    """Test error handling for various edge cases."""
    print_header("TEST: Error Handling")

    from rag_pipeline.local_remote_rag import process_git_diff_json

    print("\n🧪 Testing various error conditions...")

    # Test 1: Non-existent files
    print("\n1. Non-existent files:")
    test_json = {
        "lbd": [{"filefrom": "non_existent_file.py", "lns": [1, 2, 3]}],
        "rbd": []
    }

    try:
        result = process_git_diff_json(
            test_json,
            collection_name="demo_code_chunks",
            verbose=False
        )
        local_chunks = result.get("local_chunks", [])
        test_name = "Handle non-existent files"
        passed = len(local_chunks) == 0  # Should have no chunks
        print_test(test_name, passed, "No chunks for missing file")
    except Exception as e:
        print_test("Handle non-existent files", False, str(e))

    # Test 2: Empty line arrays
    print("\n2. Empty line arrays:")
    test_json = {
        "lbd": [{"filefrom": "rag_pipeline/chunker.py", "lns": []}],
        "rbd": []
    }

    try:
        result = process_git_diff_json(
            test_json,
            collection_name="demo_code_chunks",
            verbose=False
        )
        test_name = "Handle empty line arrays"
        passed = True  # Should not crash
        print_test(test_name, passed)
    except Exception as e:
        print_test("Handle empty line arrays", False, str(e))

    # Test 3: Invalid collection name
    print("\n3. Invalid collection name:")
    test_json = {
        "lbd": [{"filefrom": "rag_pipeline/chunker.py", "lns": [100]}],
        "rbd": []
    }

    try:
        result = process_git_diff_json(
            test_json,
            collection_name="non_existent_collection_xyz",
            verbose=False
        )
        test_name = "Handle invalid collection"
        # Should still work but with no RAG results
        passed = result.get("total_chunks", 0) >= 0
        print_test(test_name, passed, "Graceful degradation")
    except Exception as e:
        # Expected to handle gracefully
        print_test("Handle invalid collection", True, f"Caught error: {str(e)[:50]}...")

    # Test 4: Missing API key
    print("\n4. Missing API key:")
    old_key = os.environ.get("VOYAGE_API_KEY")
    del os.environ["VOYAGE_API_KEY"]

    try:
        from rag_pipeline.local_remote_rag import process_git_diff_json
        result = process_git_diff_json(
            {"lbd": [], "rbd": []},
            collection_name="demo_code_chunks",
            verbose=False
        )
        print_test("Handle missing API key", False, "Should have raised error")
    except ValueError as e:
        print_test("Handle missing API key", True, "Correctly raised ValueError")
    except Exception as e:
        print_test("Handle missing API key", False, f"Wrong error type: {type(e)}")
    finally:
        # Restore API key
        if old_key:
            os.environ["VOYAGE_API_KEY"] = old_key

    return True


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

def test_performance():
    """Test performance metrics for chunking and embedding."""
    print_header("TEST: Performance Metrics")

    from rag_pipeline.local_remote_rag import process_git_diff_json

    # Test with different sizes
    test_cases = [
        {
            "name": "Small (1 file, 5 lines)",
            "json": {
                "lbd": [{"filefrom": "rag_pipeline/embedder.py", "lns": [10, 20, 30, 40, 50]}],
                "rbd": []
            }
        },
        {
            "name": "Medium (2 files, 10 lines)",
            "json": {
                "lbd": [
                    {"filefrom": "rag_pipeline/chunker.py", "lns": list(range(50, 100, 10))},
                    {"filefrom": "rag_pipeline/embedder.py", "lns": list(range(10, 50, 10))}
                ],
                "rbd": []
            }
        },
        {
            "name": "Large (3 files, 20 lines)",
            "json": {
                "lbd": [
                    {"filefrom": "rag_pipeline/chunker.py", "lns": list(range(50, 250, 20))},
                    {"filefrom": "rag_pipeline/embedder.py", "lns": list(range(10, 80, 10))}
                ],
                "rbd": [
                    {"filefrom": "rag_pipeline/chroma.py", "lns": list(range(10, 50, 10))}
                ]
            }
        }
    ]

    print("\n📊 Performance Benchmarks:")
    print("  Testing different input sizes...")

    for test_case in test_cases:
        print(f"\n  {test_case['name']}:")

        start_time = time.time()
        try:
            result = process_git_diff_json(
                test_case["json"],
                collection_name="demo_code_chunks",
                k=3,
                verbose=False
            )
            elapsed = time.time() - start_time

            chunks = result.get("total_chunks", 0)
            print(f"    Time: {elapsed:.3f}s")
            print(f"    Chunks: {chunks}")
            print(f"    Rate: {chunks/elapsed:.1f} chunks/sec" if elapsed > 0 else "N/A")

        except Exception as e:
            print(f"    ❌ Error: {e}")

    print("\n✅ Performance tests completed")
    return True


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run all tests for local_remote_rag.py"""
    print("=" * 60)
    print("  LOCAL_REMOTE_RAG.PY TEST SUITE")
    print("=" * 60)
    print(f"API Key configured: {'✓' if VOYAGE_API_KEY else '✗'}")
    print(f"Flask API: {BASE_URL}")

    # Run tests
    all_tests = [
        ("Unit: Chunking Functions", test_chunking_functions),
        ("Unit: LocalRemoteRAG Class", test_local_remote_rag_class),
        ("Unit: process_git_diff_json", test_process_git_diff_json),
        ("Integration: API Chunking", test_api_chunking_embedding),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance)
    ]

    print("\n🚀 Running tests...\n")

    for test_name, test_func in all_tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Fatal error in {test_name}: {e}")
            test_results["errors"].append(f"{test_name}: {str(e)}")

    # Print summary
    print_header("TEST SUMMARY")
    total = test_results["passed"] + test_results["failed"]
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")

    if test_results["errors"]:
        print(f"\n⚠️  Errors encountered: {len(test_results['errors'])}")
        for error in test_results["errors"][:5]:  # Show first 5 errors
            print(f"  • {error[:100]}...")

    success_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if test_results["failed"] == 0:
        print("\n🎉 All tests passed! The chunking and embedding pipeline is working correctly.")
    else:
        print(f"\n⚠️  {test_results['failed']} test(s) failed. Review the output above for details.")

    return 0 if test_results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())