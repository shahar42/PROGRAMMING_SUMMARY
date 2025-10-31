#!/usr/bin/env python3
"""
Remove 100% exact title duplicates from concept files.

Strategy:
1. Find all concepts with EXACT same title (case-insensitive)
2. For each duplicate group:
   - Compare content similarity
   - Keep the one with most detailed explanation
   - Delete others
3. Generate report of what was removed
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import hashlib

# Paths
BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"
FACTORY_OUTPUT = BASE_DIR / "rag_finetune/factory/output"


def normalize_title(title: str) -> str:
    """Normalize title for comparison (lowercase, strip whitespace)"""
    return title.strip().lower()


def compute_content_hash(concept: Dict) -> str:
    """Hash explanation + code to detect identical content"""
    explanation = concept.get('explanation', '')
    code = concept.get('code_example', '')
    combined = f"{explanation}{code}".strip()
    return hashlib.sha256(combined.encode()).hexdigest()


def get_content_quality_score(concept: Dict) -> int:
    """Score concept quality based on content length and presence"""
    score = 0

    # Explanation quality
    explanation = concept.get('explanation', '')
    score += len(explanation)

    # Code example presence
    if concept.get('code_example', ''):
        score += 500  # Bonus for having code

    # Metadata completeness
    if concept.get('book', '') and concept.get('book', '') != 'Unknown':
        score += 100

    return score


def find_exact_title_duplicates(directory: Path) -> Dict[str, List[Tuple[Path, Dict]]]:
    """Find all concepts with exact same title"""
    title_to_concepts = defaultdict(list)

    print(f"Scanning {directory}...")
    json_files = list(directory.glob("*.json"))

    for json_file in json_files:
        if json_file.name in ['metadata.json', 'concept_metadata.json']:
            continue

        try:
            with open(json_file, 'r') as f:
                concept = json.load(f)

            title = concept.get('topic', '')
            if not title or title == 'null':
                continue

            normalized = normalize_title(title)
            title_to_concepts[normalized].append((json_file, concept))

        except Exception as e:
            print(f"Warning: Failed to load {json_file.name}: {e}")

    # Return only groups with duplicates
    duplicates = {title: concepts for title, concepts in title_to_concepts.items()
                  if len(concepts) > 1}

    return duplicates


def select_best_concept(concepts: List[Tuple[Path, Dict]]) -> Tuple[Path, Dict]:
    """Select the best concept to keep from duplicates"""
    # First check if they're 100% identical content
    content_hashes = [compute_content_hash(c) for _, c in concepts]

    if len(set(content_hashes)) == 1:
        # All identical - just keep first
        return concepts[0]

    # Different content - keep the one with highest quality score
    scored = [(path, concept, get_content_quality_score(concept))
              for path, concept in concepts]
    scored.sort(key=lambda x: x[2], reverse=True)

    return scored[0][0], scored[0][1]


def remove_duplicates(duplicates: Dict[str, List[Tuple[Path, Dict]]],
                     dry_run: bool = True) -> Dict:
    """Remove duplicate concepts, keeping the best one"""

    stats = {
        "total_duplicate_groups": len(duplicates),
        "concepts_to_delete": 0,
        "concepts_kept": 0,
        "bytes_saved": 0,
        "deletions": []
    }

    print(f"\n{'='*80}")
    print(f"100% EXACT TITLE DUPLICATES")
    print(f"{'='*80}")
    print(f"Found {len(duplicates)} titles with duplicates\n")

    for normalized_title, concept_list in sorted(duplicates.items()):
        # Get original title from first concept
        original_title = concept_list[0][1].get('topic', normalized_title)

        print(f"\n[{len(concept_list)} duplicates] {original_title}")

        # Select best concept to keep
        keep_path, keep_concept = select_best_concept(concept_list)
        keep_score = get_content_quality_score(keep_concept)

        print(f"  ✓ KEEPING: {keep_path.name}")
        print(f"    - Book: {keep_concept.get('book', 'N/A')}")
        print(f"    - Quality Score: {keep_score}")
        print(f"    - Explanation: {len(keep_concept.get('explanation', ''))} chars")
        print(f"    - Has Code: {'Yes' if keep_concept.get('code_example') else 'No'}")

        stats["concepts_kept"] += 1

        # Mark others for deletion
        for path, concept in concept_list:
            if path == keep_path:
                continue

            score = get_content_quality_score(concept)
            content_hash = compute_content_hash(concept)
            keep_hash = compute_content_hash(keep_concept)

            identical = "IDENTICAL CONTENT" if content_hash == keep_hash else "different content"

            print(f"  ✗ {'[DRY RUN] Would delete' if dry_run else 'DELETING'}: {path.name}")
            print(f"    - Quality Score: {score} (kept has {keep_score})")
            print(f"    - Content: {identical}")

            stats["concepts_to_delete"] += 1
            stats["bytes_saved"] += path.stat().st_size
            stats["deletions"].append({
                "file": str(path),
                "title": original_title,
                "book": concept.get('book', 'N/A'),
                "identical_content": content_hash == keep_hash,
                "quality_score": score
            })

            if not dry_run:
                path.unlink()

    return stats


def generate_report(stats: Dict, output_file: Path):
    """Generate JSON report of deletions"""
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\n📄 Report saved to: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove 100% exact title duplicates from concept files"
    )
    parser.add_argument(
        '--directory',
        type=Path,
        default=CONCEPTS_DIR,
        help='Directory to scan (default: data/concepts)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without deleting files'
    )
    parser.add_argument(
        '--report',
        type=Path,
        default=BASE_DIR / "rag_finetune/data/deduplication_report.json",
        help='Output report file path'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)

    print(f"{'='*80}")
    print(f"100% Exact Title Duplicate Removal")
    print(f"{'='*80}")
    print(f"Directory: {args.directory}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'ACTIVE (will delete files)'}")
    print(f"{'='*80}\n")

    # Find duplicates
    duplicates = find_exact_title_duplicates(args.directory)

    if not duplicates:
        print("\n✅ No exact title duplicates found!")
        sys.exit(0)

    # Count total files involved
    total_files = sum(len(concepts) for concepts in duplicates.values())
    files_to_delete = total_files - len(duplicates)  # Keep one per group

    print(f"\n📊 Summary:")
    print(f"  - Duplicate title groups: {len(duplicates)}")
    print(f"  - Total files involved: {total_files}")
    print(f"  - Files to delete: {files_to_delete}")
    print(f"  - Files to keep: {len(duplicates)}")

    # Confirm if not dry run
    if not args.dry_run and not args.yes:
        print(f"\n⚠️  WARNING: This will DELETE {files_to_delete} files!")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Remove duplicates
    stats = remove_duplicates(duplicates, dry_run=args.dry_run)

    # Generate report
    if not args.dry_run:
        generate_report(stats, args.report)

    # Final summary
    print(f"\n{'='*80}")
    print(f"{'DRY RUN ' if args.dry_run else ''}COMPLETE")
    print(f"{'='*80}")
    print(f"Duplicate groups found:    {stats['total_duplicate_groups']}")
    print(f"Concepts kept:             {stats['concepts_kept']}")
    print(f"Concepts {'would be ' if args.dry_run else ''}deleted:       {stats['concepts_to_delete']}")
    print(f"Disk space {'would be ' if args.dry_run else ''}saved:    {stats['bytes_saved'] / 1024:.1f} KB")

    if args.dry_run:
        print(f"\n💡 Run without --dry-run to apply changes")
        print(f"   Then rebuild index: python3 rag_finetune/scripts/build_concept_index.py")
    else:
        print(f"\n✅ Files deleted successfully!")
        print(f"\n📋 Next steps:")
        print(f"   1. Review report: {args.report}")
        print(f"   2. Rebuild search index:")
        print(f"      cd /home/shahar42/Suumerizing_C_holy_grale_book/")
        print(f"      rm rag_finetune/data/concept_index.pkl")
        print(f"      python3 rag_finetune/scripts/build_concept_index.py")


if __name__ == "__main__":
    main()
