#!/usr/bin/env python3
"""
Run batch deduplication on all book directories and save unique file lists.
"""

import json
import subprocess
from pathlib import Path

# All book directories to process
BOOK_DIRS = [
    'cpp_primer',
    'cpp_standard',
    'cpp_stl_containers',
    'csapp_2016',
    'expert_c_programming',
    'Inside_the_C++_Object_Model',
    'kernighan_ritchie',
    'linkers_loaders',
    'os_three_pieces',
    'posix_manpages',
    'posix_manpages_concepts',
    'unix_env',
]

OUTPUTS_DIR = Path('../outputs')
SIMILARITY_THRESHOLD = 0.95

def run_deduplication_for_book(book_name: str) -> dict:
    """Run deduplication for a single book and return results."""

    book_path = OUTPUTS_DIR / book_name

    if not book_path.exists():
        print(f"⚠️  Skipping {book_name} - directory not found")
        return None

    print(f"\n{'='*80}")
    print(f"Processing: {book_name}")
    print(f"{'='*80}")

    # Import the deduplication logic
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from batch_deduplicator import find_duplicates

    # Run deduplication
    duplicates_to_exclude, duplicate_reasons = find_duplicates(str(book_path), SIMILARITY_THRESHOLD)

    # Get all files and unique files
    all_files = {str(p) for p in book_path.glob("*.json")}
    unique_files = sorted(list(all_files - duplicates_to_exclude))

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total files:     {len(all_files)}")
    print(f"   Duplicates:      {len(duplicates_to_exclude)}")
    print(f"   Unique files:    {len(unique_files)}")

    return {
        'book': book_name,
        'total_files': len(all_files),
        'duplicates': len(duplicates_to_exclude),
        'unique_files': unique_files,
        'duplicate_list': list(duplicates_to_exclude),
    }

def main():
    print("="*80)
    print("Running Deduplication on All Books")
    print("="*80)

    all_results = {}
    total_concepts = 0
    total_unique = 0
    total_duplicates = 0

    for book_name in BOOK_DIRS:
        result = run_deduplication_for_book(book_name)
        if result:
            all_results[book_name] = result
            total_concepts += result['total_files']
            total_unique += len(result['unique_files'])
            total_duplicates += result['duplicates']

    # Save results to JSON
    output_file = Path('deduplicated_concepts.json')
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*80}")
    print("✅ Deduplication Complete!")
    print(f"{'='*80}")
    print(f"\n📊 Overall Statistics:")
    print(f"   Books processed:    {len(all_results)}")
    print(f"   Total concepts:     {total_concepts}")
    print(f"   Unique concepts:    {total_unique}")
    print(f"   Duplicates removed: {total_duplicates}")
    print(f"   Deduplication rate: {(total_duplicates/total_concepts*100):.1f}%")
    print(f"\n💾 Results saved to: {output_file}")
    print(f"\n🚀 Ready for dataset generation!")

if __name__ == '__main__':
    main()
