#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_remote_rag.py - RAG system for code chunks.

Takes chunks from git diff, finds similar code from ChromaDB,
and compiles everything for LLM context.
"""

import sys
import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import asdict

# Add current directory to path for local imports
sys.path.append(os.path.dirname(__file__))

try:
    import chromadb
    from embedder import embed_chunk, embed_chunks
    from chunker import CodeChunk
    from conflict_processor import chunk_and_embed_conflicts
except ImportError as e:
    print(f"Error importing required modules: {e}", file=sys.stderr)
    sys.exit(1)


class LocalRemoteRAG:
    """RAG system for retrieving similar code chunks."""

    def __init__(self, collection_name: str, db_path: str = "./my_chroma_db"):
        """
        Initialize RAG system with ChromaDB collection.

        Args:
            collection_name: Name of ChromaDB collection to query
            db_path: Path to ChromaDB database
        """
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            self.collection = self.client.get_collection(collection_name)
            self.collection_name = collection_name
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found: {e}")

    def embed_chunks(self, chunks: List[CodeChunk]) -> List[List[float]]:
        """
        Embed a list of code chunks.

        Args:
            chunks: List of CodeChunk objects

        Returns:
            List of embedding vectors
        """
        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError("VOYAGE_API_KEY not set")

        # Use batch embedding for efficiency
        results = embed_chunks(chunks, api_key=api_key)
        return [r["embedding"] for r in results]

    def query_similar_chunks(self, embedding: List[float], k: int = 5) -> Dict[str, Any]:
        """
        Query ChromaDB for k nearest neighbors.

        Args:
            embedding: Query embedding vector
            k: Number of neighbors to retrieve

        Returns:
            Dict with documents, metadatas, and distances
        """
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k
        )

        # ChromaDB returns nested lists, extract first result
        return {
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0] if "distances" in results else []
        }

    def process_single_chunk(self, chunk: CodeChunk, embedding: List[float], k: int = 5, distance_threshold: float = 0.5) -> Dict:
        """
        Process a single chunk: query neighbors and format result.

        Args:
            chunk: Original CodeChunk object
            embedding: Chunk's embedding vector
            k: Number of neighbors to retrieve
            distance_threshold: Maximum distance to include (lower = more similar)

        Returns:
            Dict with original chunk and similar code
        """
        # Query for similar chunks
        neighbors = self.query_similar_chunks(embedding, k)

        # Format similar code entries, filtering by threshold
        similar_code = []
        for i, doc in enumerate(neighbors["documents"]):
            metadata = neighbors["metadatas"][i] if i < len(neighbors["metadatas"]) else {}
            distance = neighbors["distances"][i] if i < len(neighbors["distances"]) else None

            # Skip if distance is None or exceeds threshold
            if distance is None or distance > distance_threshold:
                continue

            similar_entry = {
                "content": doc,  # The actual code from ChromaDB
                "file_path": metadata.get("file_path", "unknown"),
                "chunk_type": metadata.get("chunk_type", "unknown"),
                "lines": f"{metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}",
                "distance": distance  # Keep raw distance instead of similarity score
            }

            similar_code.append(similar_entry)

        # Return structured result
        return {
            "original_chunk": {
                "file_path": chunk.file_path,
                "content": chunk.content,
                "chunk_type": chunk.chunk_type,
                "lines": f"{chunk.start_line}-{chunk.end_line}",
                "signature": chunk.signature
            },
            "similar_code": similar_code
        }

    def process_chunks(self, chunks: List[CodeChunk], k: int = 5, distance_threshold: float = 0.5) -> List[Dict]:
        """
        Process multiple chunks: embed, retrieve neighbors, and compile context.

        Args:
            chunks: List of CodeChunk objects
            k: Number of neighbors per chunk (max 5)
            distance_threshold: Maximum distance to include (lower = more similar)

        Returns:
            List of dicts with original chunks and their similar code
        """
        if not chunks:
            return []

        # Embed all chunks at once
        print(f"Embedding {len(chunks)} chunks...", file=sys.stderr)
        embeddings = self.embed_chunks(chunks)

        # Process each chunk with its embedding
        results = []
        for chunk, embedding in zip(chunks, embeddings):
            result = self.process_single_chunk(chunk, embedding, k, distance_threshold)
            results.append(result)

        return results


def process_git_diff_json(
    json_input: Dict[str, Any],
    collection_name: str,
    k: int = 5,
    distance_threshold: float = 0.5,
    db_path: str = "./my_chroma_db",
    api_key: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Process git diff JSON with local and remote changes.

    Args:
        json_input: Dict with 'lbd' (local vs base) and 'rbd' (remote vs base) keys
        collection_name: ChromaDB collection name for LCA chunks
        k: Number of neighbors to retrieve per chunk
        distance_threshold: Maximum distance for similar chunks
        db_path: Path to ChromaDB
        api_key: Voyage AI API key (or use env var)
        verbose: Print progress information

    Returns:
        Dict with local_analysis, remote_analysis, and combined RAG results
    """
    if verbose:
        print("=" * 60)
        print("PROCESSING GIT DIFF JSON")
        print("=" * 60)

    # Get API key
    api_key = api_key or os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError("VOYAGE_API_KEY not set")

    # Parse input
    local_diffs = json_input.get("lbd", [])
    remote_diffs = json_input.get("rbd", [])

    if verbose:
        print(f"Local diffs: {len(local_diffs)} files")
        print(f"Remote diffs: {len(remote_diffs)} files")
        print()

    # Process local changes
    local_results = []
    if local_diffs:
        if verbose:
            print("Processing LOCAL changes...")
        local_processed = chunk_and_embed_conflicts(
            local_diffs, api_key, verbose=verbose
        )
        # Extract chunks
        for file_result in local_processed:
            local_results.extend(file_result.get("chunks", []))

    # Process remote changes
    remote_results = []
    if remote_diffs:
        if verbose:
            print("\nProcessing REMOTE changes...")
        remote_processed = chunk_and_embed_conflicts(
            remote_diffs, api_key, verbose=verbose
        )
        # Extract chunks
        for file_result in remote_processed:
            remote_results.extend(file_result.get("chunks", []))

    # Combine all chunks for RAG
    all_chunks = local_results + remote_results

    if verbose:
        print(f"\n{'='*60}")
        print("RAG RETRIEVAL")
        print(f"{'='*60}")
        print(f"Total chunks to process: {len(all_chunks)}")
        print(f"  Local chunks: {len(local_results)}")
        print(f"  Remote chunks: {len(remote_results)}")

    # Initialize RAG and find similar code
    rag_results = []
    if all_chunks:
        try:
            rag = LocalRemoteRAG(collection_name, db_path)
            rag_results = rag.process_chunks(all_chunks, k, distance_threshold)

            if verbose:
                total_similar = sum(len(r.get("similar_code", [])) for r in rag_results)
                print(f"\n✓ Found {total_similar} similar code chunks total")
        except Exception as e:
            print(f"Warning: RAG retrieval failed: {e}", file=sys.stderr)

    # Structure final output
    output = {
        "local_chunks": local_results,
        "remote_chunks": remote_results,
        "total_chunks": len(all_chunks),
        "rag_results": rag_results,
        "metadata": {
            "collection": collection_name,
            "k": k,
            "threshold": distance_threshold
        }
    }

    if verbose:
        print(f"\n✓ Processing complete!")

    return output


def compile_context_for_llm(rag_results: List[Dict], max_context_length: Optional[int] = None) -> str:
    """
    Compile RAG results into a string format suitable for LLM context.

    Args:
        rag_results: Output from LocalRemoteRAG.process_chunks()
        max_context_length: Optional max length for context string

    Returns:
        Formatted string for LLM context
    """
    context_parts = []

    for i, result in enumerate(rag_results, 1):
        orig = result["original_chunk"]
        context_parts.append(f"=== Chunk {i}: {orig['file_path']} ({orig['chunk_type']}) ===")
        context_parts.append(f"Lines {orig['lines']}")
        context_parts.append("Original Code:")
        context_parts.append(orig["content"])
        context_parts.append("\nSimilar Code Found:")

        for j, similar in enumerate(result["similar_code"], 1):
            distance = similar.get("distance", "N/A")
            dist_str = f"{distance:.3f}" if isinstance(distance, float) else distance
            context_parts.append(f"\n  [{j}] {similar['file_path']} (distance: {dist_str})")
            context_parts.append(f"      Lines {similar['lines']}, Type: {similar['chunk_type']}")
            # Truncate long code blocks
            code_preview = similar["content"]
            if len(code_preview) > 200:
                code_preview = code_preview[:200] + "..."
            context_parts.append(f"      {code_preview}")

        context_parts.append("\n")

    context_str = "\n".join(context_parts)

    # Truncate if needed
    if max_context_length and len(context_str) > max_context_length:
        context_str = context_str[:max_context_length] + "\n... [truncated]"

    return context_str


def main():
    """Example usage of the RAG system."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description='RAG system for code chunks')
    parser.add_argument('--collection', required=True, help='ChromaDB collection name')
    parser.add_argument('--db-path', default='./my_chroma_db', help='ChromaDB path')
    parser.add_argument('-k', type=int, default=5, help='Number of neighbors to retrieve (max 5)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Distance threshold (0.0=identical, 1.0=very different)')
    parser.add_argument('--test', action='store_true', help='Run with test chunks')
    parser.add_argument('--diff-json', help='Path to git diff JSON file with lbd and rbd keys')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("VOYAGE_API_KEY"):
        print("Error: VOYAGE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    try:
        # Handle diff JSON input
        if args.diff_json:
            # Load and process git diff JSON
            with open(args.diff_json, 'r') as f:
                diff_data = json.load(f)

            results = process_git_diff_json(
                diff_data,
                args.collection,
                k=args.k,
                distance_threshold=args.threshold,
                db_path=args.db_path,
                verbose=not args.json
            )

            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                # Human-readable output
                print(f"\nProcessed {results['total_chunks']} chunks")
                print(f"  Local: {len(results['local_chunks'])}")
                print(f"  Remote: {len(results['remote_chunks'])}")

                if results['rag_results']:
                    context = compile_context_for_llm(results['rag_results'])
                    print(f"\nGenerated context ({len(context)} chars):")
                    print("-" * 40)
                    print(context[:1000])
                    if len(context) > 1000:
                        print("... [truncated]")

            return 0

        # Original test mode
        # Initialize RAG
        rag = LocalRemoteRAG(args.collection, args.db_path)

        if args.test:
            # Create test chunks for demonstration
            test_chunks = [
                CodeChunk(
                    file_path="test/example.py",
                    language="python",
                    signature="def process_data(items):",
                    content="def process_data(items):\n    return [x * 2 for x in items]",
                    chunk_type="function",
                    start_line=10,
                    end_line=12,
                    node_types=["function_definition"]
                )
            ]
            chunks = test_chunks
        else:
            # In real usage, chunks would come from git diff processing
            print("Note: In production, chunks would come from git diff", file=sys.stderr)
            chunks = []

        if not chunks:
            print("No chunks to process", file=sys.stderr)
            return 1

        # Process chunks
        results = rag.process_chunks(chunks, k=args.k, distance_threshold=args.threshold)

        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # Human-readable format
            context = compile_context_for_llm(results)
            print(context)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())