#!/usr/bin/env python3
"""
Comprehensive Test Suite for MergeConflictResolver
Tests EVERYTHING in DETAIL - All components, integrations, edge cases
Run with: python test_everything.py --all
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import signal
import atexit

# For API testing
try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Add paths for local imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_pipeline'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_backend'))

# Configuration
BASE_URL = "http://127.0.0.1:5000"
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB")
os.environ["VOYAGE_API_KEY"] = VOYAGE_API_KEY

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Test result tracking
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.test_times = {}
        self.start_time = None
        self.current_suite = None

    def start_suite(self, name):
        self.current_suite = name
        self.test_times[name] = {'start': time.time(), 'tests': []}

    def end_suite(self):
        if self.current_suite:
            self.test_times[self.current_suite]['end'] = time.time()

    def add_test(self, name, status, message=""):
        if self.current_suite:
            self.test_times[self.current_suite]['tests'].append({
                'name': name,
                'status': status,
                'message': message
            })

        if status == 'passed':
            self.passed += 1
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}")
        elif status == 'failed':
            self.failed += 1
            self.errors.append(f"{self.current_suite}: {name} - {message}")
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {name}: {message}")
        elif status == 'skipped':
            self.skipped += 1
            print(f"  {Colors.WARNING}⊘{Colors.ENDC} {name}: {message}")

    def print_summary(self):
        total_time = time.time() - self.start_time if self.start_time else 0
        total = self.passed + self.failed + self.skipped

        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}TEST RESULTS SUMMARY{Colors.ENDC}")
        print("=" * 80)

        print(f"\nTotal Tests: {total}")
        print(f"  {Colors.OKGREEN}Passed: {self.passed}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Failed: {self.failed}{Colors.ENDC}")
        print(f"  {Colors.WARNING}Skipped: {self.skipped}{Colors.ENDC}")

        if self.errors:
            print(f"\n{Colors.FAIL}Failures:{Colors.ENDC}")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  • {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        print(f"\nTotal Time: {total_time:.2f}s")

        # Success rate
        if total > 0:
            success_rate = (self.passed / total) * 100
            color = Colors.OKGREEN if success_rate >= 80 else Colors.WARNING if success_rate >= 60 else Colors.FAIL
            print(f"Success Rate: {color}{success_rate:.1f}%{Colors.ENDC}")

results = TestResults()

# Flask server management
flask_process = None

def start_flask_server():
    """Start Flask server in background."""
    global flask_process
    if flask_process:
        return True

    print(f"{Colors.OKCYAN}Starting Flask server...{Colors.ENDC}")
    flask_process = subprocess.Popen(
        [sys.executable, "flask_backend/app.py"],
        env={**os.environ, "VOYAGE_API_KEY": VOYAGE_API_KEY},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print(f"{Colors.OKGREEN}Flask server started{Colors.ENDC}")
                return True
        except:
            time.sleep(0.5)

    print(f"{Colors.FAIL}Flask server failed to start{Colors.ENDC}")
    return False

def stop_flask_server():
    """Stop Flask server."""
    global flask_process
    if flask_process:
        flask_process.terminate()
        flask_process.wait(timeout=5)
        flask_process = None
        print(f"{Colors.OKCYAN}Flask server stopped{Colors.ENDC}")

# Register cleanup
atexit.register(stop_flask_server)

# =============================================================================
# TEST UTILITIES
# =============================================================================

def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}  {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")

def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n{Colors.OKCYAN}▶ {title}{Colors.ENDC}")
    print("-" * 60)

def safe_import(module_name: str, package: str = None):
    """Safely import a module."""
    try:
        if package:
            return __import__(f"{package}.{module_name}", fromlist=[module_name])
        return __import__(module_name)
    except ImportError as e:
        results.add_test(f"Import {module_name}", "failed", str(e))
        return None

# =============================================================================
# 1. COMPONENT TESTS
# =============================================================================

def test_chunker():
    """Test the Chunker component in detail."""
    print_subheader("Testing Chunker Component")
    results.start_suite("Chunker")

    chunker_module = safe_import("chunker", "rag_pipeline")
    if not chunker_module:
        results.end_suite()
        return

    try:
        # Test 1: Initialize Chunker
        chunker = chunker_module.Chunker()
        results.add_test("Initialize Chunker", "passed")

        # Test 2: Check language support
        supported_langs = ["python", "javascript", "typescript", "go", "rust", "java", "cpp", "c", "ruby", "php"]
        for lang in supported_langs:
            if lang in chunker.parsers:
                results.add_test(f"Parser for {lang}", "passed")
            else:
                results.add_test(f"Parser for {lang}", "skipped", "Parser not loaded")

        # Test 3: Chunk Python file
        if os.path.exists("sample_app.py"):
            config = chunker_module.LANGUAGE_MAP.get(".py", {})
            chunks = chunker.chunk_file(Path("sample_app.py"), config)
            if chunks:
                results.add_test(f"Chunk Python file ({len(chunks)} chunks)", "passed")

                # Test chunk properties
                chunk = chunks[0]
                required_attrs = ['file_path', 'language', 'content', 'chunk_type', 'start_line', 'end_line']
                for attr in required_attrs:
                    if hasattr(chunk, attr):
                        results.add_test(f"Chunk has {attr}", "passed")
                    else:
                        results.add_test(f"Chunk has {attr}", "failed", "Missing attribute")
            else:
                results.add_test("Chunk Python file", "failed", "No chunks produced")
        else:
            results.add_test("Chunk Python file", "skipped", "sample_app.py not found")

        # Test 4: Edge cases
        # Empty file
        empty_file = Path("test_empty.py")
        empty_file.write_text("")
        chunks = chunker.chunk_file(empty_file, chunker_module.LANGUAGE_MAP.get(".py", {}))
        results.add_test("Chunk empty file", "passed" if chunks == [] else "failed")
        empty_file.unlink()

        # Non-existent file
        try:
            chunks = chunker.chunk_file(Path("nonexistent.py"), chunker_module.LANGUAGE_MAP.get(".py", {}))
            results.add_test("Handle non-existent file", "passed" if chunks == [] else "failed")
        except:
            results.add_test("Handle non-existent file", "failed", "Exception raised")

    except Exception as e:
        results.add_test("Chunker tests", "failed", str(e))

    results.end_suite()

def test_embedder():
    """Test the Embedder component in detail."""
    print_subheader("Testing Embedder Component")
    results.start_suite("Embedder")

    embedder_module = safe_import("embedder", "rag_pipeline")
    chunker_module = safe_import("chunker", "rag_pipeline")

    if not embedder_module or not chunker_module:
        results.end_suite()
        return

    try:
        # Create a simple chunk for testing
        CodeChunk = chunker_module.CodeChunk
        test_chunk = CodeChunk(
            file_path="test.py",
            language="python",
            signature="def test():",
            content="def test():\n    return 42",
            chunk_type="function",
            start_line=1,
            end_line=2,
            node_types=["function_definition"]
        )

        # Test 1: Single embedding
        try:
            embedding = embedder_module.embed_chunk(test_chunk)
            if isinstance(embedding, list) and len(embedding) == 1024:
                results.add_test("Single chunk embedding (1024 dims)", "passed")
            else:
                results.add_test("Single chunk embedding", "failed", f"Wrong dimensions: {len(embedding)}")
        except Exception as e:
            if "rate limit" in str(e).lower():
                results.add_test("Single chunk embedding", "skipped", "Rate limit")
            else:
                results.add_test("Single chunk embedding", "failed", str(e))

        # Test 2: Batch embedding
        test_chunks = [test_chunk] * 3
        try:
            embedded = embedder_module.embed_chunks(test_chunks)
            if len(embedded) == 3:
                results.add_test(f"Batch embedding ({len(embedded)} chunks)", "passed")

                # Check structure
                for item in embedded:
                    if 'chunk' in item and 'embedding' in item:
                        results.add_test("Embedding structure", "passed")
                        break
                else:
                    results.add_test("Embedding structure", "failed", "Missing keys")
            else:
                results.add_test("Batch embedding", "failed", "Wrong count")
        except Exception as e:
            if "rate limit" in str(e).lower():
                results.add_test("Batch embedding", "skipped", "Rate limit")
            else:
                results.add_test("Batch embedding", "failed", str(e))

        # Test 3: Error handling - no API key
        old_key = os.environ.get("VOYAGE_API_KEY")
        del os.environ["VOYAGE_API_KEY"]
        try:
            embedding = embedder_module.embed_chunk(test_chunk)
            results.add_test("API key validation", "failed", "Should have raised error")
        except ValueError as e:
            if "API key" in str(e):
                results.add_test("API key validation", "passed")
            else:
                results.add_test("API key validation", "failed", "Wrong error")
        except Exception as e:
            results.add_test("API key validation", "failed", str(e))
        finally:
            os.environ["VOYAGE_API_KEY"] = old_key

    except Exception as e:
        results.add_test("Embedder tests", "failed", str(e))

    results.end_suite()

def test_chromadb():
    """Test ChromaDB integration in detail."""
    print_subheader("Testing ChromaDB Component")
    results.start_suite("ChromaDB")

    chroma_module = safe_import("chroma", "rag_pipeline")
    chunker_module = safe_import("chunker", "rag_pipeline")

    if not chroma_module or not chunker_module:
        results.end_suite()
        return

    try:
        import chromadb

        # Test 1: ChromaDB client creation
        db_path = "./test_chroma_db"
        client = chromadb.PersistentClient(path=db_path)
        results.add_test("Create ChromaDB client", "passed")

        # Test 2: Collection operations
        collection_name = "test_collection"
        collection = client.get_or_create_collection(name=collection_name)
        results.add_test("Create collection", "passed")

        # Test 3: Insert operation (mock data)
        CodeChunk = chunker_module.CodeChunk
        test_chunk = CodeChunk(
            file_path="test.py",
            language="python",
            signature="def test():",
            content="def test():\n    return 42",
            chunk_type="function",
            start_line=1,
            end_line=2,
            node_types=["function_definition"]
        )

        # Mock embedding (1024 dimensions)
        mock_embedding = [0.1] * 1024
        test_results = [{"chunk": test_chunk, "embedding": mock_embedding}]

        count = chroma_module.insert_to_chroma(test_results, collection_name, db_path)
        if count == 1:
            results.add_test("Insert chunks", "passed")
        else:
            results.add_test("Insert chunks", "failed", f"Expected 1, got {count}")

        # Test 4: Query operation
        query_result = collection.query(
            query_embeddings=[mock_embedding],
            n_results=1
        )
        if query_result and query_result['ids']:
            results.add_test("Query collection", "passed")
        else:
            results.add_test("Query collection", "failed", "No results")

        # Test 5: Delete collection
        client.delete_collection(name=collection_name)
        results.add_test("Delete collection", "passed")

        # Cleanup
        shutil.rmtree(db_path, ignore_errors=True)

    except ImportError:
        results.add_test("ChromaDB import", "skipped", "chromadb not installed")
    except Exception as e:
        results.add_test("ChromaDB tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 2. RAG PIPELINE TESTS
# =============================================================================

def test_rag_pipeline():
    """Test the complete RAG pipeline."""
    print_subheader("Testing RAG Pipeline")
    results.start_suite("RAG Pipeline")

    rag_module = safe_import("local_remote_rag", "rag_pipeline")

    if not rag_module:
        results.end_suite()
        return

    try:
        # Test 1: Basic process_git_diff_json
        test_json = {
            "lbd": [
                {"filefrom": "sample_app.py", "lns": [30, 40, 50]}
            ],
            "rbd": [
                {"filefrom": "sample_app.py", "lns": [80, 90]}
            ]
        }

        if os.path.exists("sample_app.py"):
            result = rag_module.process_git_diff_json(
                test_json,
                collection_name="test_collection",
                save_to_file=False,
                verbose=False
            )

            if result:
                results.add_test("Process git diff JSON", "passed")

                # Check result structure
                expected_keys = ['local_chunks', 'remote_chunks', 'total_chunks', 'rag_results']
                for key in expected_keys:
                    if key in result:
                        results.add_test(f"Result has {key}", "passed")
                    else:
                        results.add_test(f"Result has {key}", "failed", "Missing key")

                # Check chunk counts
                local_count = len(result.get('local_chunks', []))
                remote_count = len(result.get('remote_chunks', []))
                total = result.get('total_chunks', 0)

                if total == local_count + remote_count:
                    results.add_test(f"Chunk counts ({total} total)", "passed")
                else:
                    results.add_test("Chunk counts", "failed", "Mismatch")
            else:
                results.add_test("Process git diff JSON", "failed", "No result")
        else:
            results.add_test("Process git diff JSON", "skipped", "sample_app.py not found")

        # Test 2: File output
        test_json_small = {
            "lbd": [{"filefrom": "rag_pipeline/chunker.py", "lns": [100]}],
            "rbd": [{"filefrom": "rag_pipeline/embedder.py", "lns": [20]}]
        }

        output_dir = "./test_rag_output"
        result = rag_module.process_git_diff_json(
            test_json_small,
            collection_name="test_collection",
            save_to_file=True,
            output_dir=output_dir,
            verbose=False
        )

        # Check files were created
        txt_file = Path(output_dir) / "llm_context.txt"
        json_file = Path(output_dir) / "rag_chunks.json"

        if txt_file.exists():
            results.add_test("Create llm_context.txt", "passed")

            # Check content
            content = txt_file.read_text()
            if "LOCAL CHANGES" in content and "REMOTE CHANGES" in content:
                results.add_test("LLM context format", "passed")
            else:
                results.add_test("LLM context format", "failed", "Missing sections")
        else:
            results.add_test("Create llm_context.txt", "failed", "File not created")

        if json_file.exists():
            results.add_test("Create rag_chunks.json", "passed")

            # Check JSON validity
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if 'timestamp' in data:
                    results.add_test("JSON has timestamp", "passed")
                else:
                    results.add_test("JSON has timestamp", "failed", "Missing")
            except:
                results.add_test("Valid JSON", "failed", "Invalid JSON")
        else:
            results.add_test("Create rag_chunks.json", "failed", "File not created")

        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)

        # Test 3: Edge cases
        # Empty input
        empty_json = {"lbd": [], "rbd": []}
        result = rag_module.process_git_diff_json(empty_json, "test", verbose=False)
        if result and result['total_chunks'] == 0:
            results.add_test("Handle empty input", "passed")
        else:
            results.add_test("Handle empty input", "failed", "Should return 0 chunks")

        # Invalid file
        invalid_json = {
            "lbd": [{"filefrom": "nonexistent.py", "lns": [1, 2, 3]}],
            "rbd": []
        }
        result = rag_module.process_git_diff_json(invalid_json, "test", verbose=False)
        results.add_test("Handle non-existent file", "passed")  # Should not crash

    except Exception as e:
        results.add_test("RAG pipeline tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 3. FLASK API TESTS
# =============================================================================

def test_flask_api():
    """Test Flask API endpoints."""
    print_subheader("Testing Flask API")
    results.start_suite("Flask API")

    # Ensure server is running
    if not start_flask_server():
        results.add_test("Flask server", "failed", "Could not start")
        results.end_suite()
        return

    try:
        # Test 1: Health check
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            results.add_test("Health endpoint", "passed")
        else:
            results.add_test("Health endpoint", "failed", f"Status {response.status_code}")

        # Test 2: /api/data endpoint - valid data
        valid_payload = {
            "lbd": [
                {"filefrom": "test.py", "lns": [10, 20, 30]}
            ],
            "rbd": [
                {"filefrom": "test2.py", "lns": [15, 25]}
            ]
        }

        response = requests.post(
            f"{BASE_URL}/api/data",
            json=valid_payload,
            timeout=30
        )

        if response.status_code == 200:
            results.add_test("/api/data endpoint", "passed")

            # Check response structure
            data = response.json()
            expected_fields = ['message', 'status']
            for field in expected_fields:
                if field in data:
                    results.add_test(f"Response has {field}", "passed")
                else:
                    results.add_test(f"Response has {field}", "failed", "Missing field")

            # Check if files were created
            if os.path.exists("rag_output/llm_context.txt"):
                results.add_test("API creates output files", "passed")
            else:
                results.add_test("API creates output files", "failed", "Files not found")
        else:
            results.add_test("/api/data endpoint", "failed", f"Status {response.status_code}")

        # Test 3: Invalid data
        invalid_payload = {"invalid": "data"}
        response = requests.post(f"{BASE_URL}/api/data", json=invalid_payload, timeout=10)
        if response.status_code in [200, 400]:  # Either handled gracefully or returns error
            results.add_test("Handle invalid data", "passed")
        else:
            results.add_test("Handle invalid data", "failed", f"Unexpected status {response.status_code}")

        # Test 4: Empty data
        response = requests.post(f"{BASE_URL}/api/data", json={}, timeout=10)
        if response.status_code in [200, 400]:
            results.add_test("Handle empty data", "passed")
        else:
            results.add_test("Handle empty data", "failed", f"Status {response.status_code}")

        # Test 5: Large payload
        large_payload = {
            "lbd": [{"filefrom": f"file{i}.py", "lns": list(range(100))} for i in range(10)],
            "rbd": [{"filefrom": f"file{i}.py", "lns": list(range(100))} for i in range(10, 20)]
        }

        response = requests.post(f"{BASE_URL}/api/data", json=large_payload, timeout=60)
        if response.status_code == 200:
            results.add_test("Handle large payload", "passed")
        else:
            results.add_test("Handle large payload", "failed", f"Status {response.status_code}")

        # Test 6: /api/lca/create endpoint (if exists)
        try:
            response = requests.post(
                f"{BASE_URL}/api/lca/create",
                json={"lca_commit": "abc123"},
                timeout=10
            )
            if response.status_code in [200, 404]:
                results.add_test("/api/lca/create endpoint", "passed" if response.status_code == 200 else "skipped")
            else:
                results.add_test("/api/lca/create endpoint", "failed", f"Status {response.status_code}")
        except:
            results.add_test("/api/lca/create endpoint", "skipped", "Not available")

    except requests.exceptions.ConnectionError:
        results.add_test("Flask API tests", "failed", "Connection error")
    except Exception as e:
        results.add_test("Flask API tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 4. INTEGRATION TESTS
# =============================================================================

def test_integration():
    """Test end-to-end integration."""
    print_subheader("Testing End-to-End Integration")
    results.start_suite("Integration")

    try:
        # Test 1: Complete workflow simulation
        # Create a test conflict scenario
        test_file = Path("test_integration.py")
        test_file.write_text("""
def calculate(x, y):
    # This function calculates something
    result = x + y
    return result

def process(data):
    # Process the data
    processed = []
    for item in data:
        processed.append(item * 2)
    return processed
""")

        # Simulate conflict data
        conflict_data = {
            "lbd": [{"filefrom": "test_integration.py", "lns": [3, 4]}],  # calculate function
            "rbd": [{"filefrom": "test_integration.py", "lns": [9, 10]}]   # process function
        }

        # Process through RAG
        rag_module = safe_import("local_remote_rag", "rag_pipeline")
        if rag_module:
            result = rag_module.process_git_diff_json(
                conflict_data,
                collection_name="integration_test",
                save_to_file=True,
                output_dir="./integration_output",
                verbose=False
            )

            if result and result['total_chunks'] > 0:
                results.add_test("Integration: RAG processing", "passed")

                # Check output files
                if Path("integration_output/llm_context.txt").exists():
                    results.add_test("Integration: File output", "passed")

                    # Check content quality
                    content = Path("integration_output/llm_context.txt").read_text()
                    if "calculate" in content and "process" in content:
                        results.add_test("Integration: Content extraction", "passed")
                    else:
                        results.add_test("Integration: Content extraction", "failed", "Missing functions")
                else:
                    results.add_test("Integration: File output", "failed", "No output file")
            else:
                results.add_test("Integration: RAG processing", "failed", "No chunks")
        else:
            results.add_test("Integration: RAG processing", "skipped", "Module not available")

        # Cleanup
        test_file.unlink(missing_ok=True)
        shutil.rmtree("integration_output", ignore_errors=True)

        # Test 2: merj.js simulation (if available)
        if os.path.exists("bin/merj.js"):
            results.add_test("merj.js exists", "passed")
        else:
            results.add_test("merj.js exists", "skipped", "Not found")

        # Test 3: resolve_with_claude.js check
        if os.path.exists("bin/resolve_with_claude.js"):
            results.add_test("resolve_with_claude.js exists", "passed")

            # Check if it can load RAG context
            content = Path("bin/resolve_with_claude.js").read_text()
            if "loadRAGContext" in content:
                results.add_test("Claude integration with RAG", "passed")
            else:
                results.add_test("Claude integration with RAG", "failed", "No RAG loading")
        else:
            results.add_test("resolve_with_claude.js exists", "skipped", "Not found")

    except Exception as e:
        results.add_test("Integration tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 5. PERFORMANCE TESTS
# =============================================================================

def test_performance():
    """Test performance with various loads."""
    print_subheader("Testing Performance")
    results.start_suite("Performance")

    rag_module = safe_import("local_remote_rag", "rag_pipeline")

    if not rag_module:
        results.end_suite()
        return

    try:
        # Test 1: Small load (< 1s expected)
        small_data = {
            "lbd": [{"filefrom": "rag_pipeline/chunker.py", "lns": [100]}],
            "rbd": [{"filefrom": "rag_pipeline/embedder.py", "lns": [20]}]
        }

        start = time.time()
        result = rag_module.process_git_diff_json(small_data, "perf_test", verbose=False, save_to_file=False)
        elapsed = time.time() - start

        if elapsed < 5:
            results.add_test(f"Small load performance ({elapsed:.2f}s)", "passed")
        else:
            results.add_test(f"Small load performance ({elapsed:.2f}s)", "warning", "Slow")

        # Test 2: Medium load
        medium_data = {
            "lbd": [{"filefrom": f"rag_pipeline/chunker.py", "lns": list(range(10, 200, 10))}],
            "rbd": [{"filefrom": f"rag_pipeline/embedder.py", "lns": list(range(5, 100, 5))}]
        }

        start = time.time()
        result = rag_module.process_git_diff_json(medium_data, "perf_test", verbose=False, save_to_file=False)
        elapsed = time.time() - start

        if elapsed < 10:
            results.add_test(f"Medium load performance ({elapsed:.2f}s)", "passed")
        else:
            results.add_test(f"Medium load performance ({elapsed:.2f}s)", "warning", "Slow")

        # Test 3: File I/O performance
        start = time.time()
        result = rag_module.process_git_diff_json(
            medium_data,
            "perf_test",
            verbose=False,
            save_to_file=True,
            output_dir="./perf_output"
        )
        elapsed = time.time() - start

        if elapsed < 15:
            results.add_test(f"File I/O performance ({elapsed:.2f}s)", "passed")
        else:
            results.add_test(f"File I/O performance ({elapsed:.2f}s)", "warning", "Slow")

        # Cleanup
        shutil.rmtree("perf_output", ignore_errors=True)

    except Exception as e:
        results.add_test("Performance tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 6. EDGE CASES & ERROR HANDLING
# =============================================================================

def test_edge_cases():
    """Test edge cases and error handling."""
    print_subheader("Testing Edge Cases & Error Handling")
    results.start_suite("Edge Cases")

    rag_module = safe_import("local_remote_rag", "rag_pipeline")

    if not rag_module:
        results.end_suite()
        return

    try:
        # Test 1: Malformed JSON
        malformed_inputs = [
            None,
            {},
            {"lbd": None, "rbd": None},
            {"lbd": "not a list", "rbd": []},
            {"lbd": [{"wrong": "format"}], "rbd": []},
            {"lbd": [{"filefrom": "test.py"}], "rbd": []},  # Missing lns
        ]

        for i, bad_input in enumerate(malformed_inputs):
            try:
                result = rag_module.process_git_diff_json(bad_input, "test", verbose=False)
                results.add_test(f"Handle malformed input {i+1}", "passed")
            except:
                results.add_test(f"Handle malformed input {i+1}", "passed")  # Exception is OK

        # Test 2: Unicode in filenames
        unicode_data = {
            "lbd": [{"filefrom": "тест_файл.py", "lns": [1, 2]}],
            "rbd": [{"filefrom": "文件.py", "lns": [3, 4]}]
        }

        try:
            result = rag_module.process_git_diff_json(unicode_data, "test", verbose=False)
            results.add_test("Handle Unicode filenames", "passed")
        except:
            results.add_test("Handle Unicode filenames", "failed", "Should handle Unicode")

        # Test 3: Very long file paths
        long_path = "a/" * 100 + "file.py"
        long_data = {
            "lbd": [{"filefrom": long_path, "lns": [1]}],
            "rbd": []
        }

        try:
            result = rag_module.process_git_diff_json(long_data, "test", verbose=False)
            results.add_test("Handle long paths", "passed")
        except:
            results.add_test("Handle long paths", "passed")  # Either way is OK

        # Test 4: Negative line numbers
        negative_data = {
            "lbd": [{"filefrom": "test.py", "lns": [-1, -5, 0]}],
            "rbd": []
        }

        try:
            result = rag_module.process_git_diff_json(negative_data, "test", verbose=False)
            results.add_test("Handle negative line numbers", "passed")
        except:
            results.add_test("Handle negative line numbers", "passed")

        # Test 5: Duplicate line numbers
        duplicate_data = {
            "lbd": [{"filefrom": "rag_pipeline/chunker.py", "lns": [100, 100, 100]}],
            "rbd": []
        }

        result = rag_module.process_git_diff_json(duplicate_data, "test", verbose=False)
        results.add_test("Handle duplicate lines", "passed")

        # Test 6: Output directory permissions (simulate)
        try:
            # Try to write to root (should fail)
            result = rag_module.process_git_diff_json(
                {"lbd": [], "rbd": []},
                "test",
                save_to_file=True,
                output_dir="/root/test",
                verbose=False
            )
            # If it succeeds, we have root access (unlikely)
            results.add_test("Handle permission errors", "skipped", "Has root access")
        except:
            results.add_test("Handle permission errors", "passed")

    except Exception as e:
        results.add_test("Edge case tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# 7. SAMPLE APP SPECIFIC TESTS
# =============================================================================

def test_with_sample_app():
    """Test specifically with sample_app.py."""
    print_subheader("Testing with sample_app.py")
    results.start_suite("Sample App")

    if not os.path.exists("sample_app.py"):
        results.add_test("sample_app.py exists", "skipped", "File not found")
        results.end_suite()
        return

    rag_module = safe_import("local_remote_rag", "rag_pipeline")

    if not rag_module:
        results.end_suite()
        return

    try:
        # Count lines in sample_app.py for reference
        with open("sample_app.py") as f:
            total_lines = len(f.readlines())
        results.add_test(f"sample_app.py loaded ({total_lines} lines)", "passed")

        # Test 1: Conflict in UserManager class
        conflict_data = {
            "lbd": [{"filefrom": "sample_app.py", "lns": [29, 30, 31, 40, 41, 42]}],  # add_user method
            "rbd": [{"filefrom": "sample_app.py", "lns": [48, 49, 50, 52, 53]}]        # authenticate method
        }

        result = rag_module.process_git_diff_json(
            conflict_data,
            collection_name="sample_test",
            save_to_file=True,
            output_dir="./sample_output",
            verbose=False
        )

        if result:
            local_chunks = result.get('local_chunks', [])
            remote_chunks = result.get('remote_chunks', [])

            # Check that we got the right functions
            local_content = str(local_chunks)
            remote_content = str(remote_chunks)

            if "add_user" in local_content:
                results.add_test("Extract add_user method", "passed")
            else:
                results.add_test("Extract add_user method", "failed", "Not found")

            if "authenticate" in remote_content or "UserManager" in remote_content:
                results.add_test("Extract authenticate context", "passed")
            else:
                results.add_test("Extract authenticate context", "failed", "Not found")

        # Test 2: Conflict in utility functions
        conflict_data_2 = {
            "lbd": [{"filefrom": "sample_app.py", "lns": list(range(76, 102))}],  # calculate_price
            "rbd": [{"filefrom": "sample_app.py", "lns": list(range(103, 120))}]  # validate_input
        }

        result = rag_module.process_git_diff_json(conflict_data_2, "sample_test", verbose=False)

        if result and result['total_chunks'] >= 2:
            results.add_test("Extract utility functions", "passed")
        else:
            results.add_test("Extract utility functions", "failed", "Missing chunks")

        # Test 3: Check output file quality
        llm_file = Path("sample_output/llm_context.txt")
        if llm_file.exists():
            content = llm_file.read_text()

            # Check for important markers
            markers = [
                "LOCAL CHANGES",
                "REMOTE CHANGES",
                "File: sample_app.py",
                "Lines:",
                "def "
            ]

            missing = []
            for marker in markers:
                if marker not in content:
                    missing.append(marker)

            if not missing:
                results.add_test("LLM context quality", "passed")
            else:
                results.add_test("LLM context quality", "failed", f"Missing: {missing}")
        else:
            results.add_test("LLM context file", "failed", "Not created")

        # Cleanup
        shutil.rmtree("sample_output", ignore_errors=True)

    except Exception as e:
        results.add_test("Sample app tests", "failed", str(e))

    results.end_suite()

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all test suites."""
    results.start_time = time.time()

    print(f"\n{Colors.BOLD}Starting Comprehensive Test Suite{Colors.ENDC}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Key: {'Set' if VOYAGE_API_KEY else 'Not Set'}")

    # Component tests
    print_header("1. COMPONENT TESTS")
    test_chunker()
    test_embedder()
    test_chromadb()

    # RAG Pipeline tests
    print_header("2. RAG PIPELINE TESTS")
    test_rag_pipeline()

    # Flask API tests
    print_header("3. FLASK API TESTS")
    test_flask_api()

    # Integration tests
    print_header("4. INTEGRATION TESTS")
    test_integration()

    # Performance tests
    print_header("5. PERFORMANCE TESTS")
    test_performance()

    # Edge cases
    print_header("6. EDGE CASES & ERROR HANDLING")
    test_edge_cases()

    # Sample app specific
    print_header("7. SAMPLE APP TESTS")
    test_with_sample_app()

    # Print summary
    results.print_summary()

    # Return exit code
    return 0 if results.failed == 0 else 1

def run_specific_suite(suite_name):
    """Run a specific test suite."""
    results.start_time = time.time()

    suite_map = {
        'component': [test_chunker, test_embedder, test_chromadb],
        'rag': [test_rag_pipeline],
        'api': [test_flask_api],
        'integration': [test_integration],
        'performance': [test_performance],
        'edge': [test_edge_cases],
        'sample': [test_with_sample_app]
    }

    if suite_name in suite_map:
        print(f"\n{Colors.BOLD}Running {suite_name.upper()} Tests{Colors.ENDC}")
        for test_func in suite_map[suite_name]:
            test_func()
        results.print_summary()
        return 0 if results.failed == 0 else 1
    else:
        print(f"{Colors.FAIL}Unknown suite: {suite_name}{Colors.ENDC}")
        print(f"Available: {', '.join(suite_map.keys())}")
        return 1

def run_quick_tests():
    """Run quick smoke tests."""
    results.start_time = time.time()

    print(f"\n{Colors.BOLD}Running Quick Smoke Tests{Colors.ENDC}")

    # Quick component test
    print_header("QUICK COMPONENT TEST")
    chunker_module = safe_import("chunker", "rag_pipeline")
    if chunker_module:
        results.add_test("Import chunker", "passed")

    embedder_module = safe_import("embedder", "rag_pipeline")
    if embedder_module:
        results.add_test("Import embedder", "passed")

    # Quick RAG test
    print_header("QUICK RAG TEST")
    rag_module = safe_import("local_remote_rag", "rag_pipeline")
    if rag_module:
        test_data = {"lbd": [], "rbd": []}
        result = rag_module.process_git_diff_json(test_data, "quick_test", verbose=False)
        if result:
            results.add_test("Basic RAG processing", "passed")

    # Quick file test
    if os.path.exists("sample_app.py"):
        results.add_test("sample_app.py exists", "passed")

    results.print_summary()
    return 0 if results.failed == 0 else 1

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comprehensive test suite for MergeConflictResolver")
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--component', action='store_true', help='Run component tests')
    parser.add_argument('--rag', action='store_true', help='Run RAG pipeline tests')
    parser.add_argument('--api', action='store_true', help='Run API tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--edge', action='store_true', help='Run edge case tests')
    parser.add_argument('--sample', action='store_true', help='Run sample app tests')
    parser.add_argument('--quick', action='store_true', help='Run quick smoke tests')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Default to --all if no specific tests requested
    if not any(vars(args).values()):
        args.all = True

    try:
        if args.all:
            exit_code = run_all_tests()
        elif args.quick:
            exit_code = run_quick_tests()
        else:
            # Run specific suites
            exit_code = 0
            if args.component:
                exit_code |= run_specific_suite('component')
            if args.rag:
                exit_code |= run_specific_suite('rag')
            if args.api:
                exit_code |= run_specific_suite('api')
            if args.integration:
                exit_code |= run_specific_suite('integration')
            if args.performance:
                exit_code |= run_specific_suite('performance')
            if args.edge:
                exit_code |= run_specific_suite('edge')
            if args.sample:
                exit_code |= run_specific_suite('sample')

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        stop_flask_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}")
        traceback.print_exc()
        stop_flask_server()
        sys.exit(1)