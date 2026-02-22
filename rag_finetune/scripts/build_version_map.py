#!/usr/bin/env python3
"""
Build C++ version map from concept files.
Extracts C++ standard version (C++98/11/14/17/20/23) from concept content.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict

# C++ version patterns
VERSION_PATTERNS = [
    r'C\+\+(\d{2})',                    # C++11, C++14, etc.
    r'since C\+\+(\d{2})',              # "since C++11"
    r'introduced in C\+\+(\d{2})',      # "introduced in C++11"
    r'added in C\+\+(\d{2})',           # "added in C++11"
    r'new in C\+\+(\d{2})',             # "new in C++11"
    r'\(C\+\+(\d{2})\)',                # "(C++11)"
]

# Container/feature to version mapping (known facts from Perplexity)
KNOWN_VERSIONS = {
    # Containers C++98
    'vector': '98', 'deque': '98', 'list': '98', 'bitset': '98',
    'map': '98', 'multimap': '98', 'set': '98', 'multiset': '98',
    'stack': '98', 'queue': '98', 'priority_queue': '98',

    # Containers C++11
    'array': '11', 'forward_list': '11',
    'unordered_map': '11', 'unordered_multimap': '11',
    'unordered_set': '11', 'unordered_multiset': '11',

    # Containers C++20
    'span': '20',

    # Containers C++23
    'mdspan': '23', 'flat_map': '23', 'flat_multimap': '23',
    'flat_set': '23', 'flat_multiset': '23',

    # Algorithms C++11
    'all_of': '11', 'any_of': '11', 'none_of': '11', 'find_if_not': '11',
    'copy_if': '11', 'copy_n': '11', 'move': '11', 'move_backward': '11',
    'minmax': '11', 'minmax_element': '11',
    'is_heap': '11', 'is_heap_until': '11', 'is_partitioned': '11',
    'is_permutation': '11', 'is_sorted': '11', 'is_sorted_until': '11',

    # Algorithms C++17
    'clamp': '17', 'sample': '17', 'shuffle': '17',

    # Algorithms C++20/23
    'shift_left': '20', 'shift_right': '20',
    'contains': '23', 'contains_subrange': '23',
    'starts_with': '23', 'ends_with': '23',

    # Language features
    'auto_ptr': '98',
    'unique_ptr': '11', 'shared_ptr': '11', 'weak_ptr': '11',
    'move_semantics': '11', 'rvalue': '11', 'emplace': '11',
    'constexpr': '11', 'nullptr': '11', 'range_based_for': '11',
    'lambda': '11', 'variadic_template': '11',
    'decltype': '11', 'noexcept': '11',
    'structured_binding': '17', 'if_constexpr': '17', 'fold_expression': '17',
    'concepts': '20', 'coroutine': '20', 'module': '20', 'ranges': '20',
}


def normalize_version(version_str: str) -> Optional[str]:
    """Normalize version string to standard format (98/03/11/14/17/20/23)."""
    if not version_str:
        return None

    # Extract just the number
    match = re.search(r'(\d{2})', version_str)
    if not match:
        return None

    version = match.group(1)

    # Normalize
    if version in ['98', '03']:
        return '98'  # Treat C++03 as C++98
    elif version in ['11', '14', '17', '20', '23', '26']:
        return version
    else:
        return None


def extract_version_from_text(text: str) -> Optional[str]:
    """Extract C++ version from text using regex patterns."""
    if not text:
        return None

    for pattern in VERSION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first version mentioned
            version = normalize_version(matches[0])
            if version:
                return version

    return None


def extract_version_from_filename(filename: str) -> Optional[str]:
    """Extract C++ version from concept filename."""
    # Look for known container/algorithm names
    filename_lower = filename.lower()

    for feature, version in KNOWN_VERSIONS.items():
        # Match whole words to avoid false positives
        if re.search(rf'\b{re.escape(feature)}\b', filename_lower):
            return version

    return None


def extract_version_from_concept(concept_data: dict, filename: str) -> str:
    """
    Extract C++ version from a concept using multiple strategies.
    Returns version string or 'unknown'.
    """
    # Strategy 1: Check topic field
    topic = concept_data.get('topic', '')
    version = extract_version_from_text(topic)
    if version:
        return version

    # Strategy 2: Check explanation field (first 500 chars for performance)
    explanation = concept_data.get('explanation', '')[:500]
    version = extract_version_from_text(explanation)
    if version:
        return version

    # Strategy 3: Check filename for known features
    version = extract_version_from_filename(filename)
    if version:
        return version

    # Strategy 4: Check specific keywords in full explanation
    explanation_full = concept_data.get('explanation', '').lower()

    # Look for C++11 indicators
    cpp11_indicators = ['move semantic', 'rvalue reference', 'emplace', 'lambda',
                        'auto keyword', 'range-based for', 'nullptr', 'constexpr']
    if any(indicator in explanation_full for indicator in cpp11_indicators):
        return '11'

    # Look for C++17 indicators
    cpp17_indicators = ['structured binding', 'if constexpr', 'fold expression',
                        'std::optional', 'std::variant', 'std::any']
    if any(indicator in explanation_full for indicator in cpp17_indicators):
        return '17'

    # Look for C++20 indicators
    cpp20_indicators = ['concept', 'coroutine', 'module', 'ranges', 'spaceship operator']
    if any(indicator in explanation_full for indicator in cpp20_indicators):
        return '20'

    # Default: assume C++98 for older concepts, unknown for others
    return 'unknown'


def build_version_map(concepts_dir: Path) -> Dict[str, str]:
    """
    Build version map from all concept files.
    Returns dict: {concept_id: cpp_version}
    """
    version_map = {}
    stats = defaultdict(int)

    concept_files = list(concepts_dir.glob('*.json'))
    total = len(concept_files)

    print(f"Processing {total} concept files...")

    for i, concept_file in enumerate(concept_files, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{total}...")

        try:
            with open(concept_file, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)

            concept_id = concept_file.stem
            version = extract_version_from_concept(concept_data, concept_file.stem)

            version_map[concept_id] = f"C++{version}" if version != 'unknown' else 'unknown'
            stats[version] += 1

        except Exception as e:
            print(f"  Error processing {concept_file.name}: {e}")
            version_map[concept_file.stem] = 'unknown'
            stats['unknown'] += 1

    # Print statistics
    print("\nVersion distribution:")
    for version in sorted(stats.keys(), key=lambda x: (x == 'unknown', x)):
        count = stats[version]
        percentage = (count / total) * 100
        print(f"  C++{version if version != 'unknown' else 'unknown'}: {count:4d} ({percentage:5.1f}%)")

    return version_map


def main():
    """Main entry point."""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    concepts_dir = project_root / 'data' / 'concepts'
    output_file = project_root / 'data' / 'cpp_version_map.json'

    if not concepts_dir.exists():
        print(f"Error: Concepts directory not found: {concepts_dir}")
        return 1

    print("Building C++ version map...")
    print(f"Concepts directory: {concepts_dir}")
    print(f"Output file: {output_file}")
    print()

    # Build version map
    version_map = build_version_map(concepts_dir)

    # Save to file
    print(f"\nSaving version map to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(version_map, f, indent=2, sort_keys=True)

    print(f"Done! Version map saved with {len(version_map)} entries.")
    return 0


if __name__ == '__main__':
    exit(main())
