#!/usr/bin/env python3
"""
demo.py - Demonstration of the Tree-sitter chunker, embedder, and ChromaDB storage.
"""

import json
import os
from pathlib import Path
from chunker import Chunker
from embedder import embed_chunks
from chroma import insert_to_chroma
import chromadb


def run_demo():
    """Run a demonstration of the chunker, embedder, and ChromaDB storage."""

    print("=" * 60)
    print("CODE CHUNKER & EMBEDDER & CHROMADB DEMO")
    print("=" * 60)

    # ========================================
    # CREATE SAMPLE TEST CODE
    # Note: The Calculator, fibonacci, and process_data functions below
    # are NOT part of the chunking system - they're just sample code
    # that we create to demonstrate how the chunker works on real code
    # ========================================
    sample_dir = Path("demo_code")
    sample_dir.mkdir(exist_ok=True)

    sample_file = sample_dir / "sample.py"
    sample_file.write_text('''
"""Sample module for chunking demonstration."""

import math
import json
from typing import List, Dict

# Configuration
DEBUG = True
API_KEY = "secret"

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.history = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

def fibonacci(n: int) -> List[int]:
    """Generate Fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def process_data(data: Dict) -> Dict:
    """Process input data."""
    return {
        "processed": True,
        "count": len(data),
        "keys": list(data.keys())
    }

# Main execution
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(fibonacci(10))
''')

    print(f"Created sample code at: {sample_file}")

    # ========================================
    # PART 1: CHUNKING
    # ========================================
    print("\n" + "=" * 60)
    print("PART 1: CHUNKING")
    print("=" * 60)

    # Initialize chunker
    print("\nInitializing chunker...")
    chunker = Chunker()

    # Chunk the sample code
    print("Chunking sample code...")
    chunks = chunker.chunk_repository(sample_dir)

    print(f"\nGenerated {len(chunks)} chunks")

    # ========================================
    # PART 1.5: LINE-BASED CHUNKING (NEW FEATURE)
    # ========================================
    print("\n" + "=" * 60)
    print("PART 1.5: LINE-BASED CHUNKING (NEW FEATURE)")
    print("=" * 60)
    print("\nTesting the new line-based function chunking capabilities...")

    # Test 1: chunk_functions_from_lines with duplicate lines
    print("\n[TEST 1: chunk_functions_from_lines()]")
    print("-" * 40)

    # Line numbers from different parts of the sample code
    # Including duplicates and lines outside functions
    test_lines = [
        49, 50,  # Calculator.add method (49 twice for duplicate test)
        49,      # Duplicate line - should only get one chunk
        56,      # Calculator.multiply method
        63, 65,  # fibonacci function (multiple lines from same function)
        77,      # process_data function
        40,      # Global variable (outside any function)
        86,      # Main block
        100      # Invalid line number (beyond file)
    ]

    print(f"Input line numbers: {test_lines}")
    print("\nFinding unique function chunks containing these lines...")

    line_chunks = chunker.chunk_functions_from_lines(sample_file, test_lines)

    print(f"\n✓ Found {len(line_chunks)} unique function/class chunks:")
    for i, chunk in enumerate(line_chunks, 1):
        print(f"\n  [{i}] {chunk.chunk_type.upper()}")
        print(f"      Signature: {chunk.signature[:60]}...")
        print(f"      Lines: {chunk.start_line}-{chunk.end_line}")
        print(f"      First line of content: {chunk.content.splitlines()[0][:60]}...")

    # Test 2: map_lines_to_functions
    print("\n[TEST 2: map_lines_to_functions()]")
    print("-" * 40)

    # Smaller set of lines for clearer mapping demonstration
    mapping_test_lines = [35, 40, 49, 63, 77, 86, 100]

    print(f"Input line numbers: {mapping_test_lines}")
    print("\nMapping each line to its containing function/class...")

    line_to_chunk_map = chunker.map_lines_to_functions(sample_file, mapping_test_lines)

    print("\nLine → Function/Class Mapping:")
    for line_num in sorted(mapping_test_lines):
        chunk = line_to_chunk_map.get(line_num)
        if chunk:
            print(f"  Line {line_num:3d} → {chunk.chunk_type}: {chunk.signature[:40]}...")
        else:
            print(f"  Line {line_num:3d} → (not in any function/class)")

    # Test 3: Simulating a merge conflict scenario
    print("\n[TEST 3: Merge Conflict Scenario]")
    print("-" * 40)
    print("\nSimulating merge conflict resolution...")
    print("Imagine we have conflicts at these lines:")

    conflict_lines = [48, 49, 50, 51, 52]  # All within Calculator.add method

    print(f"  Conflict markers at lines: {conflict_lines}")
    print("\nGetting function context for conflict resolution...")

    conflict_chunks = chunker.chunk_functions_from_lines(sample_file, conflict_lines)

    if conflict_chunks:
        print(f"\n✓ Conflict is within {len(conflict_chunks)} function(s):")
        for chunk in conflict_chunks:
            print(f"\n  Function: {chunk.signature}")
            print(f"  Full context (lines {chunk.start_line}-{chunk.end_line}):")
            print("  " + "-" * 36)
            for line in chunk.content.splitlines()[:8]:  # Show first 8 lines
                print(f"    {line}")
            if len(chunk.content.splitlines()) > 8:
                print(f"    ... ({len(chunk.content.splitlines()) - 8} more lines)")
            print("  " + "-" * 36)
            print("\n  → This context helps understand what the conflicting code does!")

    # Summary comparison
    print("\n[COMPARISON: Regular vs Line-Based Chunking]")
    print("-" * 40)
    print(f"Regular chunking (entire file):     {len(chunks)} chunks")
    print(f"Line-based chunking (specific lines): {len(line_chunks)} chunks")
    print("\nKey advantages of line-based chunking:")
    print("  • Get only the relevant functions for specific lines")
    print("  • No duplicate chunks even with duplicate line numbers")
    print("  • Perfect for merge conflicts, error tracing, code review")
    print("  • More efficient for targeted analysis")

    # ========================================
    # PART 2: EMBEDDING
    # ========================================
    print("\n" + "=" * 60)
    print("PART 2: EMBEDDING")
    print("=" * 60)

    # Check for API key
    api_key = os.environ.get("VOYAGE_API_KEY") or "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB"

    if not api_key or api_key == "your-api-key-here":
        print("\n⚠️  No API key found. Skipping embedding demo.")
        print("To run embedding demo, set VOYAGE_API_KEY environment variable:")
        print("  export VOYAGE_API_KEY='your-api-key'")
        return

    try:
        print("\nEmbedding chunks using Voyage AI Code-3...")

        # Embed all chunks
        results = embed_chunks(chunks, api_key=api_key)

        print(f"✓ Successfully embedded {len(results)} chunks\n")

        # ========================================
        # PART 3: EMBEDDING-CODE PAIRS
        # ========================================
        print("=" * 60)
        print("PART 3: EMBEDDING-CODE PAIRS")
        print("=" * 60)

        # Show first 2 pairs only for brevity
        for i, item in enumerate(results[:2], 1):
            chunk = item["chunk"]
            embedding = item["embedding"]

            print(f"\n[PAIR {i}]")
            print(f"Type: {chunk.chunk_type}")
            print(f"Lines: {chunk.start_line}-{chunk.end_line}")
            print(f"Content preview: {chunk.content[:50]}...")
            print(f"Embedding: {len(embedding)} dimensions")
            print(f"First 5 values: {embedding[:5]}")

        if len(results) > 2:
            print(f"\n... and {len(results) - 2} more pairs")

        # ========================================
        # PART 4: STORING IN CHROMADB
        # ========================================
        print("\n" + "=" * 60)
        print("PART 4: STORING IN CHROMADB")
        print("=" * 60)

        print("\nInserting chunks and embeddings into ChromaDB...")

        # Store in ChromaDB
        collection_name = "demo_code_chunks"
        db_path = "./demo_chroma_db"

        num_inserted = insert_to_chroma(
            results,
            collection_name=collection_name,
            db_path=db_path
        )

        print(f"Database location: {db_path}")
        print(f"Collection: {collection_name}")

        # ========================================
        # DISPLAY ALL DATABASE CONTENTS
        # ========================================
        print("\n" + "=" * 60)
        print("DATABASE CONTENTS (All Stored Items)")
        print("=" * 60)

        # Connect to ChromaDB and get all items
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(collection_name)

        # Get all items from the collection
        all_items = collection.get(include=["documents", "metadatas", "embeddings"])

        print(f"\nTotal items in database: {len(all_items['ids'])}")
        print("-" * 60)

        # Display each stored item
        for i, (doc_id, doc, metadata, embedding) in enumerate(zip(
            all_items['ids'],
            all_items['documents'],
            all_items['metadatas'],
            all_items['embeddings']
        ), 1):
            print(f"\n[ITEM {i}]")
            print(f"ID: {doc_id}")
            print(f"Metadata:")
            print(f"  - Type: {metadata.get('chunk_type', 'unknown')}")
            print(f"  - File: {metadata.get('file_path', 'unknown')}")
            print(f"  - Language: {metadata.get('language', 'unknown')}")
            print(f"  - Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}")
            print(f"Embedding: {len(embedding)} dimensions")
            print(f"  First 5 values: {embedding[:5]}")
            print(f"Code content:")
            print("-" * 40)
            # Indent the code content for readability
            for line in doc.splitlines():
                print(f"  {line}")
            print("-" * 40)

        # ========================================
        # PART 5: QUERYING CHROMADB
        # ========================================
        print("\n" + "=" * 60)
        print("PART 5: QUERYING CHROMADB")
        print("=" * 60)

        print("\nTesting semantic search in ChromaDB...")

        # Test queries (using same collection from above)
        test_queries = [
            "fibonacci sequence",
            "calculator class with history",
            "process data function"
        ]

        for query in test_queries:
            print(f"\n[Query: '{query}']")

            # First embed the query using our embedder
            from embedder import embed_chunk

            # Create a dummy chunk with the query text to embed it
            class DummyChunk:
                def __init__(self, content):
                    self.content = content

            query_embedding = embed_chunk(DummyChunk(query), api_key=api_key)

            # Search in ChromaDB using the embedding
            search_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=1
            )

            if search_results['documents'][0]:
                doc = search_results['documents'][0][0]
                metadata = search_results['metadatas'][0][0]
                distance = search_results['distances'][0][0] if 'distances' in search_results else 'N/A'

                print(f"  Best match:")
                print(f"    Type: {metadata.get('chunk_type', 'unknown')}")
                print(f"    File: {metadata.get('file_path', 'unknown')}")
                print(f"    Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}")
                print(f"    Distance: {distance}")
                print(f"    Content preview: {doc[:80]}...")

        # Show collection stats
        print(f"\n[ChromaDB Collection Stats]")
        print(f"Total items stored: {collection.count()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have a valid API key set.")
        return

    # ========================================
    # DEMO COMPLETE
    # ========================================
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nWhat you learned:")
    print("1. How to chunk code into semantic units")
    print("2. How to embed chunks into vectors")
    print("3. How to store chunks in ChromaDB")
    print("4. How to perform semantic search on code")
    print("\nPersistent storage created:")
    print(f"  - ChromaDB: {db_path}/{collection_name}")
    print("\nTo query your stored code later:")
    print(f"  client = chromadb.PersistentClient(path='{db_path}')")
    print(f"  collection = client.get_collection('{collection_name}')")
    print("  results = collection.query(query_texts=['your query'], n_results=5)")


if __name__ == "__main__":
    run_demo()