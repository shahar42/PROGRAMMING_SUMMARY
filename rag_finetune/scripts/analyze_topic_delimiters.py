#!/usr/bin/env python3
"""
Analyze topic fields to determine if splitting on " - " is safe.
READ-ONLY script - does not modify any files.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"

def analyze_topics():
    """Analyze all topic fields for delimiter patterns."""
    concept_files = sorted(CONCEPTS_DIR.glob("*.json"))

    stats = {
        'total': 0,
        'contains_delimiter': 0,
        'no_delimiter': 0,
        'keywords_detected': 0,
        'ambiguous': 0,
        'multiple_delimiters': 0
    }

    examples = defaultdict(list)

    print(f"Analyzing {len(concept_files)} concept files...\n")

    for concept_file in concept_files:
        try:
            with open(concept_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            topic = data.get('topic', '')
            stats['total'] += 1

            if ' - ' not in topic:
                stats['no_delimiter'] += 1
                if len(examples['no_delimiter']) < 3:
                    examples['no_delimiter'].append(topic)
                continue

            stats['contains_delimiter'] += 1

            # Count occurrences of delimiter
            delimiter_count = topic.count(' - ')
            if delimiter_count > 1:
                stats['multiple_delimiters'] += 1
                if len(examples['multiple_delimiters']) < 3:
                    examples['multiple_delimiters'].append(topic)

            # Split on first delimiter
            parts = topic.split(' - ', 1)
            left = parts[0]
            right = parts[1] if len(parts) > 1 else ''

            # Check if left part looks like keywords (contains commas)
            if ',' in left:
                stats['keywords_detected'] += 1
                if len(examples['keywords_detected']) < 3:
                    examples['keywords_detected'].append({
                        'keywords': left[:80],
                        'title': right[:80]
                    })
            else:
                # Might be original title with " - " in it
                stats['ambiguous'] += 1
                if len(examples['ambiguous']) < 5:
                    examples['ambiguous'].append(topic)

        except Exception as e:
            print(f"Error reading {concept_file.name}: {e}")
            continue

    # Print results
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\nTotal concepts analyzed: {stats['total']}")
    print(f"\nTopics WITHOUT ' - ' delimiter: {stats['no_delimiter']} ({stats['no_delimiter']/stats['total']*100:.1f}%)")
    print(f"Topics WITH ' - ' delimiter: {stats['contains_delimiter']} ({stats['contains_delimiter']/stats['total']*100:.1f}%)")

    print(f"\n--- Breakdown of topics with delimiter ---")
    print(f"Keywords detected (comma-separated before ' - '): {stats['keywords_detected']} ({stats['keywords_detected']/stats['contains_delimiter']*100:.1f}%)")
    print(f"Ambiguous (no commas before ' - '): {stats['ambiguous']} ({stats['ambiguous']/stats['contains_delimiter']*100:.1f}%)")
    print(f"Multiple ' - ' delimiters in topic: {stats['multiple_delimiters']} ({stats['multiple_delimiters']/stats['contains_delimiter']*100:.1f}%)")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    if examples['no_delimiter']:
        print("\n--- Topics WITHOUT delimiter (no keywords prepended) ---")
        for ex in examples['no_delimiter']:
            print(f"  • {ex}")

    if examples['keywords_detected']:
        print("\n--- Topics WITH keywords (safe to split) ---")
        for ex in examples['keywords_detected']:
            print(f"  Keywords: {ex['keywords']}")
            print(f"  Title:    {ex['title']}")
            print()

    if examples['ambiguous']:
        print("\n--- AMBIGUOUS topics (no commas, might be original title) ---")
        for ex in examples['ambiguous']:
            print(f"  • {ex}")

    if examples['multiple_delimiters']:
        print("\n--- Topics with MULTIPLE ' - ' delimiters ---")
        for ex in examples['multiple_delimiters']:
            print(f"  • {ex}")

    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    safe_ratio = stats['keywords_detected'] / stats['contains_delimiter'] * 100 if stats['contains_delimiter'] > 0 else 0

    if safe_ratio > 95:
        print(f"\n✓ SAFE TO SPLIT: {safe_ratio:.1f}% of delimited topics have keyword format.")
        print("  Strategy: Split on FIRST ' - ' only")
        print("  - Left side → keywords field")
        print("  - Right side → topic field")
        print(f"\n  {stats['ambiguous']} ambiguous cases need manual review.")
    elif safe_ratio > 80:
        print(f"\n⚠ MOSTLY SAFE: {safe_ratio:.1f}% have keyword format, but {stats['ambiguous']} are ambiguous.")
        print("  Recommendation: Review ambiguous cases before splitting.")
    else:
        print(f"\n✗ RISKY: Only {safe_ratio:.1f}% have clear keyword format.")
        print("  Many topics may have ' - ' as part of original title.")
        print("  Manual review required before automated splitting.")

if __name__ == "__main__":
    analyze_topics()
