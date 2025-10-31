#!/usr/bin/env python3
"""Clean assembly blocks in training data to remove noise and keep only relevant instructions"""

import json
import re
from typing import List

def clean_assembly_block(asm: str) -> str:
    """
    Clean assembly code by removing:
    - Compiler directives (.cfi_*, .file, .section, etc.)
    - Debug info (.L labels for debug)
    - Stack canary checks
    - Excessive whitespace
    Keep:
    - Function labels (main:, function_name:)
    - Actual instructions
    - String literals (.LC0:, .string)
    - Comments with #
    """

    lines = asm.split('\n')
    cleaned_lines = []

    # Directives to completely remove
    skip_patterns = [
        r'^\s*\.file\s',
        r'^\s*\.cfi_',
        r'^\s*\.ident\s',
        r'^\s*\.section\s',
        r'^\s*\.text\s*$',
        r'^\s*\.p2align\s',
        r'^\s*\.globl\s',
        r'^\s*\.type\s',
        r'^\s*\.size\s',
        r'^\s*\.LFE\d+:',
        r'^\s*\.LFB\d+:',
        r'^\s*\.align\s',
        r'^\s*#\s*\.eh_frame',
        r'^\s*\.eh_frame',
        r'^\s*\.note\.GNU-stack',
        r'^\s*endbr64\s*$',  # Remove standalone endbr64 (security feature, not relevant)
    ]

    # Track if we're in stack canary code
    in_canary_check = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Skip lines matching skip patterns
        if any(re.match(pattern, line) for pattern in skip_patterns):
            continue

        # Skip numeric labels that are just linker artifacts
        if re.match(r'^\d+:\s*$', stripped):
            continue

        # Detect and skip stack canary code blocks
        if 'fs:40' in line or '__stack_chk_fail' in line:
            in_canary_check = True
            continue

        # Skip canary-related jumps
        if in_canary_check and (stripped.startswith('je') or stripped.startswith('call')):
            in_canary_check = False
            continue

        if in_canary_check:
            continue

        # Keep function labels
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:', stripped):
            cleaned_lines.append(line)
            continue

        # Keep .LC labels (string constants)
        if stripped.startswith('.LC') and ':' in stripped:
            cleaned_lines.append(line)
            continue

        # Keep .string directives
        if '.string' in stripped:
            cleaned_lines.append(line)
            continue

        # Keep actual assembly instructions (lines with tabs or that start with instruction mnemonics)
        # Common instructions: mov, add, sub, lea, push, pop, call, ret, jmp, je, jne, cmp, etc.
        if (line.startswith('\t') or
            re.match(r'^\s+(mov|add|sub|lea|push|pop|call|ret|leave|jmp|je|jne|jg|jl|jge|jle|cmp|test|xor|and|or|shl|shr|imul|idiv|neg|not|inc|dec|pxor|movaps|movq|xmm)', stripped)):
            cleaned_lines.append(line)
            continue

        # Keep local labels for jumps (.L followed by number)
        if re.match(r'^\.L\d+:', stripped):
            cleaned_lines.append(line)
            continue

    # Join and clean up excessive newlines
    result = '\n'.join(cleaned_lines)

    # Remove multiple consecutive blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()

def process_training_file(input_file: str, output_file: str):
    """Process a training JSON file and clean all assembly blocks"""

    print(f"Processing {input_file}...")

    with open(input_file, 'r') as f:
        data = json.load(f)

    print(f"  Total examples: {len(data)}")

    cleaned_count = 0
    assembly_blocks_found = 0

    for example in data:
        if 'messages' not in example:
            continue

        for message in example['messages']:
            if message['role'] != 'assistant':
                continue

            content = message['content']

            # Find assembly blocks (marked with ```asm or ```assembly)
            asm_pattern = r'```(?:asm|assembly)\n(.*?)```'

            matches = list(re.finditer(asm_pattern, content, re.DOTALL))

            if not matches:
                continue

            assembly_blocks_found += len(matches)

            # Clean each assembly block
            new_content = content
            for match in reversed(matches):  # Reverse to maintain indices
                original_asm = match.group(1)
                cleaned_asm = clean_assembly_block(original_asm)

                # Replace the assembly block
                new_content = (
                    new_content[:match.start(1)] +
                    cleaned_asm +
                    new_content[match.end(1):]
                )

                cleaned_count += 1

            message['content'] = new_content

    print(f"  Assembly blocks found: {assembly_blocks_found}")
    print(f"  Blocks cleaned: {cleaned_count}")

    # Save cleaned data
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  ✅ Saved to {output_file}")

    return assembly_blocks_found, cleaned_count

def main():
    """Clean assembly in both train.json and val.json"""

    print("=" * 70)
    print("Assembly Cleaning Script")
    print("=" * 70)
    print()
    print("This will:")
    print("  • Remove .cfi_*, .file, .section, and other compiler directives")
    print("  • Remove stack canary checks (fs:40, __stack_chk_fail)")
    print("  • Remove debug labels and linker artifacts")
    print("  • Keep only relevant assembly instructions")
    print()

    # Backup originals
    print("Creating backups...")
    import shutil
    shutil.copy('training_data/train.json', 'training_data/train_before_asm_cleaning.json')
    shutil.copy('training_data/val.json', 'training_data/val_before_asm_cleaning.json')
    print("  ✅ Backups created")
    print()

    # Process train.json
    train_blocks, train_cleaned = process_training_file(
        'training_data/train.json',
        'training_data/train.json'
    )
    print()

    # Process val.json
    val_blocks, val_cleaned = process_training_file(
        'training_data/val.json',
        'training_data/val.json'
    )
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total assembly blocks cleaned: {train_cleaned + val_cleaned}")
    print(f"  train.json: {train_cleaned} blocks")
    print(f"  val.json:   {val_cleaned} blocks")
    print()
    print("Backups saved:")
    print("  training_data/train_before_asm_cleaning.json")
    print("  training_data/val_before_asm_cleaning.json")
    print()
    print("✅ Assembly cleaning complete!")
    print()
    print("Next steps:")
    print("  1. Review a few examples to verify cleaning quality")
    print("  2. Retrain model as V11 with cleaned assembly")
    print("  3. Test if model gives cleaner, more focused answers")

if __name__ == "__main__":
    main()
