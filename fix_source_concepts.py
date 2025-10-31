#!/usr/bin/env python3
"""
Fix corrupted source concept files where code_example is an array instead of string.
Converts list format to proper newline-joined string.
"""

import json
from pathlib import Path

def fix_concept_file(filepath):
    """Fix a single concept file if code_example is a list."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Check if code_example needs fixing
    code_example = data.get('code_example')

    if isinstance(code_example, list):
        # Join array lines with newlines
        data['code_example'] = '\n'.join(code_example)

        # Write back
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return True  # Fixed

    return False  # Already correct

def main():
    print("🔧 Fixing Corrupted Source Concepts")
    print("="*80)
    print()

    # Find all concept JSON files
    concept_files = list(Path('outputs').rglob('*.json'))
    concept_files = [f for f in concept_files if f.name not in ['progress.json', 'concept_cache.json']]

    print(f"Found {len(concept_files)} concept files")
    print()

    fixed_count = 0
    error_count = 0

    for filepath in concept_files:
        try:
            if fix_concept_file(filepath):
                fixed_count += 1
                if fixed_count <= 10:  # Show first 10
                    print(f"✓ Fixed: {filepath.name}")
        except Exception as e:
            error_count += 1
            print(f"✗ Error fixing {filepath}: {e}")

    print()
    print("="*80)
    print(f"✅ Complete!")
    print(f"  Total files:     {len(concept_files)}")
    print(f"  Fixed:           {fixed_count}")
    print(f"  Errors:          {error_count}")
    print(f"  Already correct: {len(concept_files) - fixed_count - error_count}")

if __name__ == '__main__':
    main()
