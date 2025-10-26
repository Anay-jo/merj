#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chunk_lca.py - Chunk repository at LCA and store in ChromaDB.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from review_two_sides_with_cr import detect_rebase_context, git, repo_root
    from chunker import Chunker
    from embedder import embed_chunks
    from chroma import insert_to_chroma
except ImportError as e:
    print(f"Error importing required modules: {e}", file=sys.stderr)
    sys.exit(1)


def create_lca_worktree(lca_sha: str, repo: str = None) -> str:
    """Create temporary worktree at LCA commit."""
    temp_dir = tempfile.mkdtemp(prefix=f"lca-{lca_sha[:8]}-")
    try:
        git("worktree", "add", "--detach", temp_dir, lca_sha, cwd=repo)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to create worktree: {e}")


def cleanup_worktree(worktree_path: str, repo: str = None) -> None:
    """Clean up git worktree."""
    try:
        git("worktree", "remove", "--force", worktree_path, cwd=repo)
    except:
        if os.path.exists(worktree_path):
            shutil.rmtree(worktree_path, ignore_errors=True)


def main():
    """Chunk repository at LCA and store in ChromaDB."""
    import argparse

    parser = argparse.ArgumentParser(description='Chunk repository at LCA and store in ChromaDB')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--main-ref', default=None, help='Main branch reference (default: origin/main)')
    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("VOYAGE_API_KEY"):
        print("Error: VOYAGE_API_KEY environment variable not set", file=sys.stderr)
        print("Please set: export VOYAGE_API_KEY='your-key'", file=sys.stderr)
        sys.exit(1)

    worktree_path = None

    try:
        # 1. Find LCA
        repo = repo_root()
        if args.main_ref:
            os.environ['MAIN_REF'] = args.main_ref

        base, local_tip, main_tip = detect_rebase_context(repo)

        # 2. Create worktree at LCA
        worktree_path = create_lca_worktree(base, repo)

        # 3. Chunk the repository
        chunker = Chunker()
        chunks = chunker.chunk_repository(Path(worktree_path))

        if not chunks:
            raise ValueError("No chunks generated from repository")

        # 4. Embed and store
        results = embed_chunks(chunks)
        collection_name = f"lca_{datetime.now():%Y%m%d}_{base[:8]}"
        insert_to_chroma(results, collection_name=collection_name)

        # Output results
        if args.json:
            output = {
                "lca": base,
                "chunks": len(chunks),
                "collection": collection_name
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"✓ Chunked {len(chunks)} pieces at LCA {base[:8]}")
            print(f"✓ Stored in ChromaDB: {collection_name}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        # Always cleanup worktree
        if worktree_path and os.path.exists(worktree_path):
            cleanup_worktree(worktree_path, repo)


if __name__ == "__main__":
    sys.exit(main())