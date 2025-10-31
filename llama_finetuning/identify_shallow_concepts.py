#!/usr/bin/env python3
"""
Identify shallow concepts that need enhancement.

Criteria for shallow:
- Explanation < 600 chars
- Missing code examples
- No assembly/memory details mentioned
"""

import json
from pathlib import Path
from typing import Dict, List

def analyze_concept_depth(concept: Dict) -> Dict:
    """Analyze if concept needs enhancement."""

    explanation = concept.get('explanation', '')
    code_example = concept.get('code_example', '')

    # Check for implementation keywords
    impl_keywords = [
        'assembly', 'register', 'vtable', 'memory layout',
        'byte', 'offset', 'alignment', 'padding', 'abi',
        'compiler generates', 'mov', 'lea', 'push', 'call'
    ]

    has_impl_details = any(kw in explanation.lower() + str(code_example).lower()
                           for kw in impl_keywords)

    return {
        'explanation_length': len(explanation),
        'has_code': bool(code_example),
        'has_impl_details': has_impl_details,
        'needs_enhancement': (
            len(explanation) < 600 or
            not code_example or
            not has_impl_details
        )
    }

def main():
    print("="*80)
    print("Identifying Shallow Concepts for Enhancement")
    print("="*80)
    print()

    # Load deduplicated concepts
    with open('deduplicated_concepts.json', 'r') as f:
        dedup_data = json.load(f)

    shallow_concepts = []
    stats = {
        'total': 0,
        'shallow': 0,
        'missing_code': 0,
        'missing_impl': 0,
        'short_explanation': 0
    }

    for book_name, book_data in dedup_data.items():
        print(f"📚 Analyzing {book_name}...")

        for filepath in book_data['unique_files']:
            stats['total'] += 1

            try:
                with open(filepath, 'r') as f:
                    concept = json.load(f)

                analysis = analyze_concept_depth(concept)

                if analysis['needs_enhancement']:
                    stats['shallow'] += 1

                    if not analysis['has_code']:
                        stats['missing_code'] += 1
                    if not analysis['has_impl_details']:
                        stats['missing_impl'] += 1
                    if analysis['explanation_length'] < 600:
                        stats['short_explanation'] += 1

                    shallow_concepts.append({
                        'filepath': filepath,
                        'topic': concept.get('topic', 'Unknown'),
                        'book': book_name,
                        'analysis': analysis
                    })

            except Exception as e:
                print(f"   ⚠️  Error loading {filepath}: {e}")

        print(f"   ✓ {len(book_data['unique_files'])} concepts analyzed")

    print()
    print("="*80)
    print("📊 Analysis Results")
    print("="*80)
    print(f"Total concepts:          {stats['total']}")
    print(f"Shallow concepts:        {stats['shallow']} ({stats['shallow']/stats['total']*100:.1f}%)")
    print(f"  - Missing code:        {stats['missing_code']}")
    print(f"  - Missing impl details: {stats['missing_impl']}")
    print(f"  - Short explanation:   {stats['short_explanation']}")
    print()

    # Save results
    output_file = Path('shallow_concepts.json')
    with open(output_file, 'w') as f:
        json.dump({
            'statistics': stats,
            'shallow_concepts': shallow_concepts
        }, f, indent=2)

    print(f"💾 Saved to: {output_file}")
    print(f"📋 {len(shallow_concepts)} concepts need enhancement")
    print()

    # Show sample shallow concepts
    print("Sample shallow concepts:")
    for i, sc in enumerate(shallow_concepts[:5]):
        print(f"\n{i+1}. {sc['topic']} ({sc['book']})")
        print(f"   Length: {sc['analysis']['explanation_length']} chars")
        print(f"   Has code: {sc['analysis']['has_code']}")
        print(f"   Has impl: {sc['analysis']['has_impl_details']}")

if __name__ == '__main__':
    main()
