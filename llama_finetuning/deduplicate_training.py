#!/usr/bin/env python3
"""
Deduplicate training data by removing duplicate assistant responses
within the same concept variations
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set


def hash_content(text: str) -> str:
    """Create hash of content for comparison"""
    # Normalize whitespace and create hash
    normalized = ' '.join(text.split())
    return hashlib.md5(normalized.encode()).hexdigest()


def deduplicate_conversations(conversations: List[Dict]) -> List[Dict]:
    """
    Remove conversations with duplicate assistant responses
    Keep first occurrence, remove subsequent duplicates
    """
    seen_responses: Set[str] = set()
    unique_conversations = []
    duplicates_removed = 0

    for conv in conversations:
        messages = conv.get('messages', [])

        # Extract assistant response
        assistant_content = None
        for msg in messages:
            if msg.get('role') == 'assistant':
                assistant_content = msg.get('content', '')
                break

        if not assistant_content:
            # No assistant message, keep it anyway
            unique_conversations.append(conv)
            continue

        # Check if we've seen this response before
        content_hash = hash_content(assistant_content)

        if content_hash in seen_responses:
            duplicates_removed += 1
            continue

        # New unique response
        seen_responses.add(content_hash)
        unique_conversations.append(conv)

    return unique_conversations, duplicates_removed


def remove_duplicate_explanations(conversations: List[Dict]) -> List[Dict]:
    """
    Remove duplicate explanations WITHIN a single assistant response
    (e.g., when explanation is repeated 3 times in same message)
    """
    cleaned_conversations = []
    explanations_cleaned = 0

    for conv in conversations:
        messages = conv.get('messages', [])
        modified = False

        for msg in messages:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')

                # Split by double newlines (paragraph breaks)
                paragraphs = content.split('\n\n')

                # Remove duplicate consecutive paragraphs
                unique_paragraphs = []
                prev_hash = None

                for para in paragraphs:
                    para_hash = hash_content(para)

                    # Keep if different from previous
                    if para_hash != prev_hash:
                        unique_paragraphs.append(para)
                        prev_hash = para_hash
                    else:
                        modified = True

                if modified:
                    msg['content'] = '\n\n'.join(unique_paragraphs)
                    explanations_cleaned += 1

        cleaned_conversations.append(conv)

    return cleaned_conversations, explanations_cleaned


def deduplicate_file(input_file: str, output_file: str) -> Dict[str, int]:
    """Deduplicate a single training file"""
    print(f"\n📄 Processing {Path(input_file).name}...")

    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_count = len(data)
    print(f"   Original: {original_count} conversations")

    # Step 1: Remove duplicate explanations within messages
    data, explanations_cleaned = remove_duplicate_explanations(data)
    if explanations_cleaned > 0:
        print(f"   Cleaned {explanations_cleaned} messages with duplicate paragraphs")

    # Step 2: Remove completely duplicate conversations
    data, duplicates_removed = deduplicate_conversations(data)
    final_count = len(data)

    print(f"   Removed {duplicates_removed} duplicate conversations")
    print(f"   Final: {final_count} conversations ({final_count/original_count*100:.1f}% kept)")

    # Save deduplicated data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        'original': original_count,
        'final': final_count,
        'duplicates_removed': duplicates_removed,
        'explanations_cleaned': explanations_cleaned
    }


def main():
    print("=" * 70)
    print("🧹 DEDUPLICATING TRAINING DATA")
    print("=" * 70)

    training_dir = Path("training_data")

    if not training_dir.exists():
        print("❌ Error: training_data directory not found!")
        return

    files_to_process = [
        ('train.json', 'train.json'),
        ('val.json', 'val.json'),
    ]

    total_stats = {
        'original': 0,
        'final': 0,
        'duplicates_removed': 0,
        'explanations_cleaned': 0
    }

    for input_name, output_name in files_to_process:
        input_path = training_dir / input_name
        output_path = training_dir / output_name

        if not input_path.exists():
            print(f"\n⚠️  {input_name}: File not found, skipping...")
            continue

        stats = deduplicate_file(str(input_path), str(output_path))

        for key in total_stats:
            total_stats[key] += stats[key]

    # Update sample.json from deduplicated train
    print("\n📝 Updating sample.json from deduplicated training data...")
    train_path = training_dir / "train.json"
    sample_path = training_dir / "sample.json"

    if train_path.exists():
        with open(train_path, 'r') as f:
            train_data = json.load(f)

        # Take first 5 examples
        with open(sample_path, 'w') as f:
            json.dump(train_data[:5], f, indent=2, ensure_ascii=False)
        print(f"   Updated sample.json with 5 examples")

    # Summary
    print("\n" + "=" * 70)
    print("📊 DEDUPLICATION SUMMARY")
    print("=" * 70)
    print(f"Total conversations processed: {total_stats['original']}")
    print(f"Duplicate conversations removed: {total_stats['duplicates_removed']}")
    print(f"Messages with cleaned paragraphs: {total_stats['explanations_cleaned']}")
    print(f"Final conversation count: {total_stats['final']}")

    reduction = total_stats['original'] - total_stats['final']
    if total_stats['original'] > 0:
        print(f"Total reduction: {reduction} ({reduction/total_stats['original']*100:.1f}%)")

    print("\n✅ Deduplication complete!")
    print(f"💾 Deduplicated files saved in {training_dir}/")


if __name__ == "__main__":
    main()
