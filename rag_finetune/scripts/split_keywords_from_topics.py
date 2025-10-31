#!/usr/bin/env python3
"""
Split prepended keywords from topic field into separate keywords field.
Safely handles topics with " - " delimiter by splitting on FIRST occurrence only.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"

def split_topic_keywords(concept_file, dry_run=True):
    """Split keywords from topic field in a single concept file."""
    with open(concept_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_topic = data.get('topic', '')

    # Skip if no delimiter (no keywords prepended)
    if ' - ' not in original_topic:
        return None

    # Split on FIRST occurrence only
    parts = original_topic.split(' - ', 1)
    if len(parts) != 2:
        return None

    keywords = parts[0].strip()
    clean_title = parts[1].strip()

    # Verify keywords look right (should contain commas)
    if ',' not in keywords:
        print(f"  ⚠ Warning: No commas in keywords for {concept_file.name}")
        print(f"    Topic: {original_topic[:100]}")
        return None

    if dry_run:
        return {
            'file': concept_file.name,
            'original': original_topic[:100] + ('...' if len(original_topic) > 100 else ''),
            'keywords': keywords[:80] + ('...' if len(keywords) > 80 else ''),
            'title': clean_title[:80] + ('...' if len(clean_title) > 80 else '')
        }
    else:
        # Update the data
        data['keywords'] = keywords
        data['topic'] = clean_title

        # Write back to file
        with open(concept_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            'file': concept_file.name,
            'title': clean_title[:60]
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Split keywords from topic field")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--limit", type=int, help="Limit number of files to process (for testing)")
    args = parser.parse_args()

    concept_files = sorted(CONCEPTS_DIR.glob("*.json"))

    if args.limit:
        concept_files = concept_files[:args.limit]

    print(f"Processing {len(concept_files)} concept files")
    if args.dry_run:
        print("DRY RUN - No files will be modified\n")

    processed_count = 0
    skipped_count = 0

    for concept_file in concept_files:
        try:
            result = split_topic_keywords(concept_file, dry_run=args.dry_run)

            if result:
                processed_count += 1
                if args.dry_run and processed_count <= 5:
                    print(f"\nFile: {result['file']}")
                    print(f"  Original: {result['original']}")
                    print(f"  Keywords: {result['keywords']}")
                    print(f"  Title:    {result['title']}")
                elif not args.dry_run and processed_count % 100 == 0:
                    print(f"  Processed {processed_count} files...")
            else:
                skipped_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {concept_file.name}: {e}")
            continue

    print(f"\n{'Would process' if args.dry_run else 'Processed'}: {processed_count} concepts")
    print(f"Skipped (no delimiter or invalid format): {skipped_count}")

    if args.dry_run:
        print("\nShowing first 5 examples above.")
        print("Run without --dry-run to apply changes to all files")
    else:
        print("\nNext step: Rebuild search index")
        print("  python3 rag_finetune/scripts/build_concept_index.py")

if __name__ == "__main__":
    main()
