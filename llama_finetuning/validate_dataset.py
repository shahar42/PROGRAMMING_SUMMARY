#!/usr/bin/env python3
"""
Validate that all training examples follow the correct Llama 3.1 chat format
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

def validate_message(message: Dict, index: int) -> List[str]:
    """Validate a single message object"""
    errors = []

    # Check required fields
    if 'role' not in message:
        errors.append(f"Message {index}: Missing 'role' field")
    elif message['role'] not in ['system', 'user', 'assistant']:
        errors.append(f"Message {index}: Invalid role '{message['role']}' (must be system/user/assistant)")

    if 'content' not in message:
        errors.append(f"Message {index}: Missing 'content' field")
    elif not isinstance(message['content'], str):
        errors.append(f"Message {index}: 'content' must be a string")
    elif len(message['content'].strip()) == 0:
        errors.append(f"Message {index}: 'content' is empty")

    return errors

def validate_conversation(conv: Dict, conv_idx: int) -> Tuple[bool, List[str]]:
    """Validate a single conversation"""
    errors = []

    # Check if 'messages' field exists
    if 'messages' not in conv:
        errors.append(f"Conversation {conv_idx}: Missing 'messages' field")
        return False, errors

    messages = conv['messages']

    # Check if messages is a list
    if not isinstance(messages, list):
        errors.append(f"Conversation {conv_idx}: 'messages' must be a list")
        return False, errors

    # Check if there are messages
    if len(messages) == 0:
        errors.append(f"Conversation {conv_idx}: 'messages' list is empty")
        return False, errors

    # Validate each message
    for idx, message in enumerate(messages):
        if not isinstance(message, dict):
            errors.append(f"Conversation {conv_idx}, Message {idx}: Must be a dictionary")
            continue

        msg_errors = validate_message(message, idx)
        errors.extend([f"Conversation {conv_idx}, {err}" for err in msg_errors])

    # Check conversation structure
    roles = [msg.get('role') for msg in messages]

    # Should have at least user and assistant
    if 'user' not in roles:
        errors.append(f"Conversation {conv_idx}: No 'user' message found")
    if 'assistant' not in roles:
        errors.append(f"Conversation {conv_idx}: No 'assistant' message found")

    # System message should be first if present
    if 'system' in roles and roles[0] != 'system':
        errors.append(f"Conversation {conv_idx}: 'system' message should be first")

    # Check for alternating user/assistant pattern (after system)
    start_idx = 1 if roles[0] == 'system' else 0
    for i in range(start_idx, len(roles) - 1):
        if roles[i] == 'user' and roles[i + 1] not in ['assistant', 'user']:
            errors.append(f"Conversation {conv_idx}: Unexpected role sequence at position {i}")

    return len(errors) == 0, errors

def validate_dataset_file(filepath: str) -> Tuple[int, int, List[str]]:
    """Validate an entire dataset file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return 0, 0, [f"Invalid JSON: {e}"]
    except Exception as e:
        return 0, 0, [f"Error reading file: {e}"]

    if not isinstance(data, list):
        return 0, 0, ["Dataset must be a list of conversations"]

    total = len(data)
    valid = 0
    all_errors = []

    for idx, conv in enumerate(data):
        is_valid, errors = validate_conversation(conv, idx)
        if is_valid:
            valid += 1
        else:
            all_errors.extend(errors)
            # Only show first 5 errors per file to avoid spam
            if len(all_errors) >= 5:
                all_errors.append(f"... and more errors (showing first 5)")
                break

    return total, valid, all_errors

def main():
    print("=" * 70)
    print("🔍 VALIDATING LLAMA 3.1 DATASET FORMAT")
    print("=" * 70)

    training_dir = Path("training_data")

    if not training_dir.exists():
        print("❌ Error: training_data directory not found!")
        return

    files_to_check = [
        training_dir / "train.json",
        training_dir / "val.json",
        training_dir / "sample.json"
    ]

    total_conversations = 0
    total_valid = 0
    files_with_errors = []

    for filepath in files_to_check:
        if not filepath.exists():
            print(f"\n⚠️  {filepath.name}: File not found, skipping...")
            continue

        print(f"\n📄 Checking {filepath.name}...")
        print("-" * 70)

        total, valid, errors = validate_dataset_file(str(filepath))
        total_conversations += total
        total_valid += valid

        if errors:
            files_with_errors.append(filepath.name)
            print(f"❌ Found {len(errors)} errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors")
        else:
            print(f"✅ All {total} conversations are valid!")

        print(f"📊 Valid: {valid}/{total} ({valid/total*100:.1f}%)")

    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total conversations checked: {total_conversations}")
    print(f"Valid conversations: {total_valid}")
    print(f"Invalid conversations: {total_conversations - total_valid}")
    print(f"Success rate: {total_valid/total_conversations*100:.1f}%")

    if files_with_errors:
        print(f"\n⚠️  Files with errors: {', '.join(files_with_errors)}")
        print("\n💡 Tip: Check the error messages above to fix the issues")
    else:
        print("\n✅ ALL FILES ARE VALID! Ready for training! 🚀")

    # Show example of valid format
    print("\n" + "=" * 70)
    print("📝 EXPECTED FORMAT EXAMPLE")
    print("=" * 70)
    print("""
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert programming instructor..."
    },
    {
      "role": "user",
      "content": "Explain pointers in C"
    },
    {
      "role": "assistant",
      "content": "Pointers are variables that store memory addresses..."
    }
  ]
}
    """)

    # Additional checks
    print("\n" + "=" * 70)
    print("🔬 ADDITIONAL CHECKS")
    print("=" * 70)

    # Check for common issues
    sample_file = training_dir / "sample.json"
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            sample_data = json.load(f)

        if len(sample_data) > 0:
            first_conv = sample_data[0]

            # Check if system message exists
            if first_conv['messages'][0]['role'] == 'system':
                print("✅ System messages present")
            else:
                print("⚠️  No system messages (optional but recommended)")

            # Check average length
            avg_length = sum(len(json.dumps(conv)) for conv in sample_data) / len(sample_data)
            print(f"📏 Average conversation length: {avg_length:.0f} characters")

            if avg_length > 4000:
                print("   ⚠️  Some conversations might be long (watch token limits)")

            # Check for code examples
            has_code = any('```' in msg['content']
                          for conv in sample_data
                          for msg in conv['messages']
                          if msg['role'] == 'assistant')

            if has_code:
                print("✅ Code examples detected in assistant responses")
            else:
                print("ℹ️  No code blocks detected (might be text-only)")

if __name__ == "__main__":
    main()
