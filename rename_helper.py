#!/usr/bin/env python3
import os
import re
import uuid
from pathlib import Path

# --- Configuration ---

# The directory to scan for old-style concept files.
TARGET_DIR = Path("./outputs/linkers_loaders")

# The book code to use in the new filenames.
BOOK_CODE = "linkers_loaders"

# Mapping of keywords found in old filenames to the new category codes.
# The order matters: more specific keywords should come first.
CATEGORY_MAP = {
    # Linking Process
    "linking": "process",
    "static_linking": "process",
    "dynamic_linking": "process",
    "lto": "process",
    "incremental_linking": "process",

    # Symbols
    "symbol_resolution": "symbols",
    "symbol_tables": "symbols",
    "name_mangling": "symbols",

    # Relocation
    "relocation": "relocation",
    "address_patching": "relocation",

    # File Formats
    "elf": "formats",
    "pe_file": "formats",
    "object_file": "formats",
    "comdats": "formats",

    # Loading
    "loading": "loading",
    "address_space": "loading",
    "overlay": "loading",

    # Code & Libraries
    "position_independent_code": "code",
    "pic": "code",
    "got": "code",
    "plt": "code",
    "shared_libraries": "libs",
    "dlls": "libs",
    "stub_libraries": "libs",

    # C Basics
    "variable": "c_basics",
    "header_files": "c_basics",
    "program_structure": "c_basics",
}

# --- Script Logic ---

def clean_topic(filename_part):
    """Cleans the topic part of the filename."""
    # Remove the initial 'linkers_concept_..._' part
    topic = re.sub(r'linkers_concept_\d+_', '', filename_part)
    topic = topic.replace('_', '-')
    return topic[:50]

def guess_category(filename):
    """Guesses the category based on keywords in the filename."""
    clean_filename = filename.lower().replace('_', '')
    for keyword, category in CATEGORY_MAP.items():
        clean_keyword = keyword.replace('_', '')
        if clean_keyword in clean_filename:
            return category
    return None

def main():
    """Main function to find, prompt, and rename files."""
    if not TARGET_DIR.is_dir():
        print(f"Error: Directory not found at '{TARGET_DIR}'")
        return

    files_to_rename = []
    files_to_check_manually = []

    for filepath in sorted(TARGET_DIR.iterdir()):
        # Target files starting with 'linkers_concept_'
        if filepath.is_file() and filepath.name.startswith("linkers_concept_") and filepath.name.endswith(".json") and ".backup" not in filepath.name:
            filename_stem = filepath.stem
            category = guess_category(filename_stem)

            if category:
                topic = clean_topic(filename_stem)
                unique_hash = uuid.uuid4().hex[:6]
                new_filename = f"{BOOK_CODE}_{category}_{topic}_{unique_hash}.json"
                files_to_rename.append((filepath, TARGET_DIR / new_filename))
            else:
                files_to_check_manually.append(filepath)

    if not files_to_rename:
        print("No old-style concept files found to rename in this directory.")
        if files_to_check_manually:
             print(f"\nFound {len(files_to_check_manually)} files that may need manual review.")
        return

    # --- Prompt for approval ---
    print(f"# Found {len(files_to_rename)} old-style files to rename in '{TARGET_DIR}'.")
    print("# Here is a sample of the proposed changes:")
    for old_path, new_path in files_to_rename[:5]:
        print(f"  - {old_path.name}  ->  {new_path.name}")

    print("\n# ---")
    try:
        approval = input(f"# Do you want to proceed with renaming these {len(files_to_rename)} files? (yes/no): ")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return

    # --- Execute renaming if approved ---
    if approval.lower().strip() == 'yes':
        print(f"\n# Proceeding with renaming {len(files_to_rename)} files...")
        renamed_count = 0
        error_count = 0
        for old_path, new_path in files_to_rename:
            try:
                old_path.rename(new_path)
                renamed_count += 1
            except OSError as e:
                print(f"Error renaming {old_path}: {e}")
                error_count += 1
        print(f"\n# Renaming complete. {renamed_count} files were successfully renamed.")
        if error_count > 0:
            print(f"# {error_count} errors occurred.")
    else:
        print("\n# Operation cancelled. No files were changed.")

    # --- Report files needing manual check ---
    if files_to_check_manually:
        print("\n# --- Files needing manual categorization ---")
        print("# The script could not guess a category for these files:")
        for filepath in files_to_check_manually:
            print(f"# {filepath.name}")

if __name__ == "__main__":
    main()
