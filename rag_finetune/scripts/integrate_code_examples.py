#!/usr/bin/env python3
"""
Integrate generated code examples into concept JSON files.
Reads code_examples.json and updates corresponding concept files.
"""

import json
import sys
from pathlib import Path
from typing import Dict

# Paths
BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
CODE_EXAMPLES_FILE = BASE_DIR / "rag_finetune/data/code_examples.json"
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"


def load_code_examples() -> Dict:
    """Load generated code examples"""
    with open(CODE_EXAMPLES_FILE, 'r') as f:
        data = json.load(f)
    return data.get('examples', {})


def integrate_code_examples():
    """Add code examples to concept JSON files"""

    # Load code examples
    print(f"Loading code examples from {CODE_EXAMPLES_FILE}...")
    code_examples = load_code_examples()
    print(f"✓ Loaded {len(code_examples)} code examples\n")

    # Get all concept files
    concept_files = list(CONCEPTS_DIR.glob("*.json"))
    print(f"Found {len(concept_files)} concept files\n")

    # Track stats
    matched = 0
    skipped = 0
    updated = 0

    # Process each concept file
    for concept_file in concept_files:
        try:
            # Load concept
            with open(concept_file, 'r') as f:
                concept = json.load(f)

            # Get concept ID (from filename or id field)
            concept_id = concept.get('id', concept_file.stem)

            # Check if code example exists
            if concept_id in code_examples:
                matched += 1

                # Check if already has code example
                if 'code_example' in concept and concept['code_example']:
                    skipped += 1
                    print(f"[SKIP] {concept_id[:50]}... (already has code)")
                    continue

                # Add code example
                code_data = code_examples[concept_id]
                concept['code_example'] = code_data['code']

                # Save updated concept
                with open(concept_file, 'w') as f:
                    json.dump(concept, f, indent=2)

                updated += 1
                print(f"[✓] {concept_id[:50]}...")

        except Exception as e:
            print(f"[ERROR] Failed to process {concept_file.name}: {e}")
            continue

    # Report
    print(f"\n{'='*60}")
    print(f"Integration Complete!")
    print(f"{'='*60}")
    print(f"Total concept files:     {len(concept_files)}")
    print(f"Matched with examples:   {matched}")
    print(f"Updated:                 {updated}")
    print(f"Skipped (already had):   {skipped}")
    print(f"{'='*60}\n")


def main():
    # Verify files exist
    if not CODE_EXAMPLES_FILE.exists():
        print(f"✗ Error: Code examples file not found: {CODE_EXAMPLES_FILE}")
        sys.exit(1)

    if not CONCEPTS_DIR.exists():
        print(f"✗ Error: Concepts directory not found: {CONCEPTS_DIR}")
        sys.exit(1)

    # Run integration
    integrate_code_examples()


if __name__ == "__main__":
    main()
