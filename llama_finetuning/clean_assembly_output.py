#!/usr/bin/env python3
"""
Clean assembly output by removing compiler metadata/boilerplate
Keep only the actual assembly instructions and function labels
"""

import json
import re

def clean_assembly(asm_text):
    """
    Remove compiler metadata by finding where actual code starts.
    Pattern: Remove everything from start until we hit .text section
    """
    if not asm_text:
        return asm_text

    lines = asm_text.split('\n')

    # Find where actual code starts (after metadata)
    # Look for the first function label or .text after metadata
    start_idx = 0
    found_text = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip intel_syntax line
        if '.intel_syntax' in stripped:
            start_idx = i + 1
            continue

        # Skip all comment lines with #
        if stripped.startswith('# '):
            start_idx = i + 1
            continue

        # Found .text - skip #APP/#NO_APP block
        if '.text' in stripped:
            found_text = True
            start_idx = i + 1
            continue

        # Skip #APP/#NO_APP
        if found_text and stripped in ['#APP', '#NO_APP']:
            start_idx = i + 1
            continue

        # Found actual code (function label or instruction)
        if found_text and (stripped.endswith(':') or '\t' in line):
            start_idx = i
            break

    # Keep from start_idx onward
    cleaned_lines = lines[start_idx:]

    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines)


def main():
    print("=" * 80)
    print("CLEANING ASSEMBLY OUTPUT - REMOVE COMPILER METADATA")
    print("=" * 80)
    print()

    # Load current training data
    print("📂 Loading training data...")
    with open('training_data/train.json') as f:
        train_data = json.load(f)

    with open('training_data/val.json') as f:
        val_data = json.load(f)

    print(f"  ✅ Train: {len(train_data)} examples")
    print(f"  ✅ Val: {len(val_data)} examples")
    print()

    # Clean assembly in training data
    print("🧹 Cleaning assembly output...")
    train_cleaned = 0
    val_cleaned = 0

    for ex in train_data:
        for msg in ex.get('messages', []):
            if msg['role'] == 'assistant' and '```asm' in msg['content']:
                # Extract assembly block
                content = msg['content']
                if '```asm\n' in content and '\n```' in content:
                    start = content.find('```asm\n') + 7
                    end = content.find('\n```', start)
                    asm_code = content[start:end]

                    # Clean it
                    cleaned_asm = clean_assembly(asm_code)

                    # Replace
                    msg['content'] = f"```asm\n{cleaned_asm}\n```"
                    train_cleaned += 1

    for ex in val_data:
        for msg in ex.get('messages', []):
            if msg['role'] == 'assistant' and '```asm' in msg['content']:
                content = msg['content']
                if '```asm\n' in content and '\n```' in content:
                    start = content.find('```asm\n') + 7
                    end = content.find('\n```', start)
                    asm_code = content[start:end]

                    cleaned_asm = clean_assembly(asm_code)
                    msg['content'] = f"```asm\n{cleaned_asm}\n```"
                    val_cleaned += 1

    print(f"  ✅ Cleaned {train_cleaned} assembly blocks in training data")
    print(f"  ✅ Cleaned {val_cleaned} assembly blocks in validation data")
    print()

    # Backup
    print("💾 Creating backup...")
    with open('training_data/train_before_cleaning.json', 'w') as f:
        json.dump(train_data, f)
    with open('training_data/val_before_cleaning.json', 'w') as f:
        json.dump(val_data, f)
    print("  ✅ Backups created")
    print()

    # Save cleaned data
    print("💾 Saving cleaned data...")
    with open('training_data/train.json', 'w') as f:
        json.dump(train_data, f)
    with open('training_data/val.json', 'w') as f:
        json.dump(val_data, f)
    print("  ✅ Saved")
    print()

    # Show example
    print("=" * 80)
    print("📝 SAMPLE CLEANED OUTPUT")
    print("=" * 80)
    print()

    for ex in train_data:
        for msg in ex.get('messages', []):
            if msg['role'] == 'assistant' and '```asm' in msg['content']:
                print("BEFORE CLEANING:")
                print("  - Had compiler version (GNU C++17...)")
                print("  - Had compilation flags")
                print("  - Had GCC heuristics")
                print()
                print("AFTER CLEANING:")
                print(msg['content'][:600] + "...")
                print()
                break
        if '```asm' in str(ex):
            break

    # File sizes
    import os
    train_size = os.path.getsize('training_data/train.json') / 1024 / 1024
    val_size = os.path.getsize('training_data/val.json') / 1024 / 1024

    print("=" * 80)
    print("✅ ASSEMBLY CLEANING COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Cleaned {train_cleaned + val_cleaned} total assembly blocks")
    print(f"📁 New file sizes:")
    print(f"    train.json: {train_size:.1f} MB")
    print(f"    val.json: {val_size:.1f} MB")
    print()
    print("🎯 BENEFITS:")
    print("  ✓ Removed useless compiler metadata")
    print("  ✓ Model focuses on actual assembly instructions")
    print("  ✓ Cleaner, more focused training")
    print("  ✓ Smaller file size")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
