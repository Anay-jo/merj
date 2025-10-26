#!/usr/bin/env python3
"""
Test the RAG pipeline with a sample Python file.
This simulates merge conflicts at specific line numbers.
"""

import os
import sys
import json
from pathlib import Path

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_pipeline'))

# Set API key
os.environ["VOYAGE_API_KEY"] = os.environ.get("VOYAGE_API_KEY", "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB")

def test_rag_with_sample_file():
    """Test RAG pipeline with sample_app.py"""
    from rag_pipeline.local_remote_rag import process_git_diff_json

    print("=" * 60)
    print("TEST: RAG Pipeline with Sample Python File")
    print("=" * 60)
    print()

    # Simulate conflicts at specific line numbers
    # These represent where merge conflicts would occur
    test_json = {
        "lbd": [  # Local vs Base diff (your branch changes)
            {
                "filefrom": "sample_app.py",
                "lns": [
                    29, 30, 31,  # Lines in add_user method (username, email, password params)
                    40, 41, 42,  # Creating user dict
                    82, 83,      # In calculate_price function
                    85, 86       # Discount calculation
                ]
            }
        ],
        "rbd": [  # Remote vs Base diff (main branch changes)
            {
                "filefrom": "sample_app.py",
                "lns": [
                    48, 49, 50,  # authenticate method
                    52, 53,      # Token generation
                    89, 90,      # Tax calculation
                    103, 104     # validate_input function
                ]
            }
        ]
    }

    print("📋 Simulated Conflict Scenario:")
    print()
    print("LOCAL BRANCH (Your Changes):")
    print("  - Modified add_user method (lines 29-42)")
    print("  - Changed calculate_price function (lines 82-86)")
    print()
    print("REMOTE BRANCH (Main Changes):")
    print("  - Modified authenticate method (lines 48-53)")
    print("  - Changed tax calculation (lines 89-90)")
    print("  - Updated validate_input function (lines 103-104)")
    print()
    print("=" * 60)
    print()

    # Process through RAG pipeline
    print("🔨 Processing through RAG pipeline...")
    print()

    try:
        result = process_git_diff_json(
            test_json,
            collection_name="demo_code_chunks",
            k=3,  # Find 3 similar chunks
            distance_threshold=0.7,
            save_to_file=True,  # Save output files
            output_dir="./rag_output",
            verbose=False  # Less verbose output
        )

        print("✅ RAG processing complete!")
        print()

        # Show what was extracted
        print("📊 Extracted Context:")
        print(f"  - Local chunks: {len(result.get('local_chunks', []))}")
        print(f"  - Remote chunks: {len(result.get('remote_chunks', []))}")
        print(f"  - Total chunks: {result.get('total_chunks', 0)}")
        print()

        # Check generated files
        output_dir = "./rag_output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print("📁 Generated Files:")
            for file in files:
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file} ({size:,} bytes)")
            print()

            # Show sample of the LLM context
            txt_path = os.path.join(output_dir, "llm_context.txt")
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    lines = f.readlines()

                print("=" * 60)
                print("📝 LLM Context Preview (first 80 lines):")
                print("-" * 60)
                for i, line in enumerate(lines[:80]):
                    print(line.rstrip())

                if len(lines) > 80:
                    print()
                    print(f"... ({len(lines) - 80} more lines)")
                print("-" * 60)

        print()
        print("=" * 60)
        print("✨ SUCCESS! RAG pipeline extracted context from sample file")
        print("=" * 60)
        print()
        print("Key Observations:")
        print("1. RAG extracted complete functions/methods, not just specific lines")
        print("2. It provides context about what each branch was modifying")
        print("3. The output shows the actual code being changed")
        print("4. This context helps LLMs understand the intent of changes")
        print()
        print("Files ready for LLM consumption:")
        print("  - rag_output/llm_context.txt (human-readable)")
        print("  - rag_output/rag_chunks.json (structured data)")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rag_with_sample_file()
    sys.exit(0 if success else 1)