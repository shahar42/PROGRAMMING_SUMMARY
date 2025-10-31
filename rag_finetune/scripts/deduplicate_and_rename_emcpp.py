#!/usr/bin/env python3
"""
Deduplicate and rename Effective Modern C++ concepts using Gemini.
1. Find exact duplicates (100% same explanation) → delete
2. Find concepts with same title → rename with specific titles using Gemini
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import google.generativeai as genai
from tqdm import tqdm
import time

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
FACTORY_OUTPUT = BASE_DIR / "rag_finetune/factory/output"

# Find all Effective Modern C++ directories
EMCPP_DIRS = list(FACTORY_OUTPUT.glob("Scott_Meyers_Effective_Modern_C++*"))


def compute_content_hash(concept: Dict) -> str:
    """Compute hash of explanation + code to detect exact duplicates"""
    explanation = concept.get('explanation', '')
    code = concept.get('code_example', '')
    content = f"{explanation}{code}".strip()
    return hashlib.sha256(content.encode()).hexdigest()


def load_all_concepts(directories: List[Path]) -> List[Tuple[Path, Dict]]:
    """Load all concept files from given directories"""
    concepts = []
    for directory in directories:
        if not directory.exists():
            continue
        for json_file in directory.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                concepts.append((json_file, data))
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")
    return concepts


def find_exact_duplicates(concepts: List[Tuple[Path, Dict]]) -> Dict[str, List[Path]]:
    """Find concepts with identical content"""
    hash_to_files = defaultdict(list)

    for file_path, concept_data in concepts:
        content_hash = compute_content_hash(concept_data)
        hash_to_files[content_hash].append(file_path)

    # Return only groups with duplicates
    return {h: files for h, files in hash_to_files.items() if len(files) > 1}


def find_duplicate_titles(concepts: List[Tuple[Path, Dict]]) -> Dict[str, List[Tuple[Path, Dict]]]:
    """Find concepts with the same title"""
    title_to_concepts = defaultdict(list)

    for file_path, concept_data in concepts:
        title = concept_data.get('topic', '')
        if title and title != 'null':  # Skip empty/null titles
            title_to_concepts[title].append((file_path, concept_data))

    # Return only groups with duplicates
    return {title: concepts for title, concepts in title_to_concepts.items() if len(concepts) > 1}


def generate_specific_title(concept: Dict, existing_titles: List[str], model) -> str:
    """Use Gemini to generate a more specific, unique title"""

    prompt = f"""You are renaming a C++ concept to be more specific and unique.

Current title: {concept.get('topic', '')}
Explanation: {concept.get('explanation', '')[:500]}

Existing titles (must be different from these):
{chr(10).join(f"- {t}" for t in existing_titles)}

Generate a NEW, more specific title that:
1. Is different from all existing titles
2. Captures the specific aspect/context of this concept
3. Is concise (max 8 words)
4. Uses technical terms when appropriate
5. Follows pattern: "[Main Concept]: [Specific Context/Issue]"

Examples:
- "Auto Type Deduction" → "Auto Type Deduction: Proxy Type Pitfalls"
- "Shared Pointer" → "Shared Pointer: Control Block Construction Cost"
- "Template Deduction" → "Template Deduction: Universal Reference Collapse"

Return ONLY the new title, nothing else."""

    try:
        response = model.generate_content(prompt)
        new_title = response.text.strip()
        # Clean up any markdown or quotes
        new_title = new_title.strip('"\'`')
        return new_title
    except Exception as e:
        print(f"Error generating title: {e}")
        # Fallback: append explanation snippet
        snippet = concept.get('explanation', '')[:50].replace('\n', ' ')
        return f"{concept.get('topic', 'Concept')}: {snippet}"


def delete_exact_duplicates(duplicate_groups: Dict[str, List[Path]], dry_run: bool = True) -> int:
    """Delete exact duplicate files, keeping only the first one"""
    deleted_count = 0

    print("\n" + "="*80)
    print("EXACT DUPLICATES (100% same content)")
    print("="*80)

    for content_hash, files in duplicate_groups.items():
        print(f"\nDuplicate group ({len(files)} files):")
        print(f"  Keeping: {files[0]}")

        for duplicate_file in files[1:]:
            print(f"  {'[DRY RUN] Would delete' if dry_run else 'Deleting'}: {duplicate_file}")
            if not dry_run:
                duplicate_file.unlink()
            deleted_count += 1

    return deleted_count


def rename_duplicate_titles(title_groups: Dict[str, List[Tuple[Path, Dict]]],
                           model, dry_run: bool = True) -> int:
    """Rename concepts with duplicate titles using Gemini"""
    renamed_count = 0

    print("\n" + "="*80)
    print("DUPLICATE TITLES (same title, different content)")
    print("="*80)

    for title, concept_list in tqdm(title_groups.items(), desc="Renaming concepts"):
        print(f"\n[Title: {title}] - {len(concept_list)} concepts")

        existing_titles = [title]  # Start with original

        for file_path, concept_data in concept_list:
            # Generate new specific title
            new_title = generate_specific_title(concept_data, existing_titles, model)
            existing_titles.append(new_title)

            print(f"  {file_path.name}")
            print(f"    Old: {concept_data.get('topic', 'N/A')}")
            print(f"    New: {new_title}")

            if not dry_run:
                # Update the concept data
                concept_data['topic'] = new_title

                # Save back to file
                with open(file_path, 'w') as f:
                    json.dump(concept_data, f, indent=2)

            renamed_count += 1

            # Rate limiting
            time.sleep(0.5)

    return renamed_count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deduplicate and rename Effective Modern C++ concepts")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--skip-delete', action='store_true', help='Skip deleting exact duplicates')
    parser.add_argument('--skip-rename', action='store_true', help='Skip renaming duplicate titles')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("Effective Modern C++ Deduplication & Renaming")
    print(f"{'='*80}")
    print(f"Mode: {'DRY RUN (no changes will be made)' if args.dry_run else 'ACTIVE (will modify files)'}")
    print(f"\nSearching in:")
    for d in EMCPP_DIRS:
        print(f"  - {d}")

    # Load all concepts
    print("\nLoading concepts...")
    all_concepts = load_all_concepts(EMCPP_DIRS)
    print(f"Loaded {len(all_concepts)} concepts")

    # Find exact duplicates
    if not args.skip_delete:
        exact_dupes = find_exact_duplicates(all_concepts)
        if exact_dupes:
            deleted = delete_exact_duplicates(exact_dupes, dry_run=args.dry_run)
            print(f"\n{'Would delete' if args.dry_run else 'Deleted'} {deleted} exact duplicate(s)")
        else:
            print("\n✓ No exact duplicates found")

    # Find and rename duplicate titles
    if not args.skip_rename:
        duplicate_titles = find_duplicate_titles(all_concepts)
        if duplicate_titles:
            print(f"\nFound {len(duplicate_titles)} titles with duplicates")

            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

            renamed = rename_duplicate_titles(duplicate_titles, model, dry_run=args.dry_run)
            print(f"\n{'Would rename' if args.dry_run else 'Renamed'} {renamed} concept(s)")
        else:
            print("\n✓ No duplicate titles found")

    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    if args.dry_run:
        print("DRY RUN completed. Run without --dry-run to apply changes.")
    else:
        print("Processing complete!")
        print("\nNext steps:")
        print("1. Review the changes in factory/output/Scott_Meyers_Effective_Modern_C++*/")
        print("2. Merge all page ranges:")
        print("   mkdir -p factory/output/Scott_Meyers_Effective_Modern_C++_complete")
        print("   for dir in factory/output/Scott_Meyers_Effective_Modern_C++_pages_*/; do")
        print("       cp \"$dir\"/*.json factory/output/Scott_Meyers_Effective_Modern_C++_complete/")
        print("   done")
        print("3. Integrate into main database:")
        print("   python3 rag_finetune/factory/scripts/batch_integrate.py \\")
        print("       factory/output/Scott_Meyers_Effective_Modern_C++_complete/")
        print("4. Rebuild search index:")
        print("   python3 rag_finetune/scripts/build_concept_index.py")


if __name__ == "__main__":
    main()
