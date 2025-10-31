#!/usr/bin/env python3
"""
CRITICAL SCRIPT: Add permanent book metadata to all concept JSON files.
This ensures book information is NEVER lost regardless of file location.

This script:
1. Scans all concepts in outputs/
2. Extracts book name from directory structure and extraction_metadata.source
3. Adds a top-level "book" field to each JSON file
4. Creates backups before modification
5. Logs all changes
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
OUTPUTS_DIR = Path("outputs")
BACKUP_DIR = Path("rag_finetune/data/book_metadata_backup")
LOG_FILE = Path("rag_finetune/data/book_metadata_recovery.log")

# Book name mapping (directory -> canonical name)
BOOK_CANONICAL_NAMES = {
    "cpp_primer": "C++ Primer (5th Edition)",
    "cpp_standard": "ISO/IEC 14882:2014 C++ Standard",
    "cpp_stl_containers": "C++ STL Containers",
    "csapp_2016": "Computer Systems: A Programmer's Perspective (3rd Edition)",
    "expert_c_programming": "Expert C Programming: Deep C Secrets",
    "kernighan_ritchie": "The C Programming Language - Kernighan & Ritchie",
    "linkers_loaders": "Linkers and Loaders",
    "os_three_pieces": "Operating Systems - Three Easy Pieces",
    "posix_manpages_concepts": "POSIX System Call Manual",
    "unix_env": "Advanced Programming in the UNIX Environment (3rd Edition)",
    "Inside_the_C++_Object_Model": "Inside the C++ Object Model by Stanley B. Lippman"
}


def extract_book_info(json_file: Path) -> dict:
    """Extract book information from directory and metadata"""
    # Get directory-based book name
    dir_book = json_file.parent.name

    # Skip cleanup backups - use their parent directory instead
    if "cleanup_backup" in dir_book:
        dir_book = json_file.parent.parent.name

    # Get canonical name
    canonical = BOOK_CANONICAL_NAMES.get(dir_book, dir_book)

    # Load and check extraction_metadata
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        source = data.get("extraction_metadata", {}).get("source", "")

        return {
            "directory_book": dir_book,
            "canonical_name": canonical,
            "metadata_source": source,
            "has_book_field": "book" in data
        }
    except Exception as e:
        return {
            "directory_book": dir_book,
            "canonical_name": canonical,
            "metadata_source": "",
            "has_book_field": False,
            "error": str(e)
        }


def add_book_field(json_file: Path, book_name: str, dry_run: bool = False) -> bool:
    """Add book field to a concept JSON file"""
    try:
        # Read existing data
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Skip if already has book field
        if "book" in data:
            return False

        # Add book field at the top level
        data["book"] = book_name

        # Also add to extraction_metadata for redundancy
        if "extraction_metadata" not in data:
            data["extraction_metadata"] = {}

        # Keep original source if exists, otherwise use book name
        if "source" not in data["extraction_metadata"]:
            data["extraction_metadata"]["source"] = book_name

        # Add recovery timestamp
        data["extraction_metadata"]["book_metadata_added"] = datetime.now().isoformat()

        if not dry_run:
            # Write back with proper formatting
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"ERROR processing {json_file}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add book metadata to all concept files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--backup", action="store_true", help="Create backup of entire outputs/ directory")
    args = parser.parse_args()

    print("=" * 80)
    print("BOOK METADATA RECOVERY SCRIPT")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MODIFICATION'}")
    print(f"Target: {OUTPUTS_DIR}")
    print()

    # Create backup if requested
    if args.backup and not args.dry_run:
        print("Creating backup...")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"outputs_backup_{timestamp}"
        shutil.copytree(OUTPUTS_DIR, backup_path)
        print(f"✓ Backup created: {backup_path}\n")

    # Scan all concepts
    stats = defaultdict(int)
    modifications = []
    errors = []

    for json_file in OUTPUTS_DIR.rglob("*.json"):
        # Skip cache/progress files
        if json_file.name in ["concept_cache.json", "progress.json"]:
            continue

        # Extract book info
        info = extract_book_info(json_file)
        book_name = info["canonical_name"]

        # Track stats
        stats[book_name] += 1

        # Add book field if missing
        if not info["has_book_field"]:
            modified = add_book_field(json_file, book_name, dry_run=args.dry_run)
            if modified:
                modifications.append({
                    "file": str(json_file),
                    "book": book_name,
                    "metadata_source": info["metadata_source"]
                })

        if "error" in info:
            errors.append({
                "file": str(json_file),
                "error": info["error"]
            })

    # Report
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total concepts processed: {sum(stats.values())}")
    print(f"Files modified: {len(modifications)}")
    print(f"Errors: {len(errors)}")
    print()

    print("Concepts per book:")
    for book, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {book:60s} {count:5d}")

    # Write log
    if not args.dry_run and modifications:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            f.write(f"Book Metadata Recovery Log\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total modifications: {len(modifications)}\n\n")

            for mod in modifications:
                f.write(f"File: {mod['file']}\n")
                f.write(f"Book: {mod['book']}\n")
                f.write(f"Original source: {mod['metadata_source']}\n")
                f.write("-" * 80 + "\n")

        print(f"\n✓ Log written to: {LOG_FILE}")

    if errors:
        print(f"\n⚠ {len(errors)} errors occurred. Check output above.")

    if args.dry_run:
        print("\n⚠ DRY RUN - No files were modified")
        print("Run without --dry-run to apply changes")
    else:
        print("\n✓ Book metadata successfully added to all concept files")

    print("=" * 80)


if __name__ == "__main__":
    main()
