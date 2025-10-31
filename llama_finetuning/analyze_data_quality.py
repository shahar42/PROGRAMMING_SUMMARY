#!/usr/bin/env python3
"""
Analyze training data quality - detect repetition, inconsistent lengths, and other issues
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import re

def find_repeated_sentences(text: str, min_length: int = 50) -> List[Tuple[str, int]]:
    """Find sentences that are repeated in the text"""
    # Split into sentences (simple approach)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > min_length]

    # Count occurrences
    sentence_counts = Counter(sentences)

    # Return sentences that appear more than once
    return [(sent, count) for sent, count in sentence_counts.items() if count > 1]

def analyze_response_length(content: str) -> Dict[str, int]:
    """Analyze response metrics"""
    return {
        'char_count': len(content),
        'word_count': len(content.split()),
        'line_count': content.count('\n') + 1,
        'has_code': '```' in content,
        'has_syntax_section': '**Syntax:**' in content or '**Example:**' in content,
    }

def categorize_response_type(content: str) -> str:
    """Categorize the type of response"""
    word_count = len(content.split())

    if word_count < 50:
        return "VERY_SHORT"
    elif word_count < 150:
        return "SHORT"
    elif word_count < 400:
        return "MEDIUM"
    elif word_count < 800:
        return "LONG"
    else:
        return "VERY_LONG"

def analyze_conversation(conv: Dict, idx: int) -> Dict:
    """Analyze a single conversation for quality issues"""
    issues = []
    metrics = {}

    messages = conv.get('messages', [])

    # Find assistant messages
    assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']

    if not assistant_messages:
        return {'idx': idx, 'issues': ['No assistant message'], 'metrics': {}}

    for msg_idx, msg in enumerate(assistant_messages):
        content = msg.get('content', '')

        # Check for repetition within the message
        repeated = find_repeated_sentences(content)
        if repeated:
            for sent, count in repeated:
                issues.append({
                    'type': 'REPETITION',
                    'message_idx': msg_idx,
                    'count': count,
                    'text': sent[:100] + '...' if len(sent) > 100 else sent
                })

        # Analyze length
        metrics[f'assistant_{msg_idx}'] = analyze_response_length(content)
        response_type = categorize_response_type(content)
        metrics[f'assistant_{msg_idx}']['type'] = response_type

        # Check for very short responses (potential quality issue)
        if response_type == "VERY_SHORT":
            issues.append({
                'type': 'TOO_SHORT',
                'message_idx': msg_idx,
                'word_count': len(content.split()),
                'text': content[:100]
            })

    return {
        'idx': idx,
        'issues': issues,
        'metrics': metrics,
        'num_messages': len(messages),
        'num_assistant': len(assistant_messages)
    }

def analyze_dataset(filepath: str) -> Dict:
    """Analyze entire dataset"""
    print(f"\n📊 Analyzing {filepath}...")
    print("=" * 70)

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    results = []

    # Analyze each conversation
    for idx, conv in enumerate(data):
        result = analyze_conversation(conv, idx)
        results.append(result)

    # Aggregate statistics
    stats = {
        'total_conversations': total,
        'conversations_with_repetition': 0,
        'conversations_too_short': 0,
        'response_types': Counter(),
        'issues_by_type': Counter()
    }

    problematic_examples = []

    for result in results:
        issues = result['issues']

        if any(i['type'] == 'REPETITION' for i in issues):
            stats['conversations_with_repetition'] += 1
            problematic_examples.append((result['idx'], 'REPETITION', issues))

        if any(i['type'] == 'TOO_SHORT' for i in issues):
            stats['conversations_too_short'] += 1
            problematic_examples.append((result['idx'], 'TOO_SHORT', issues))

        for issue in issues:
            stats['issues_by_type'][issue['type']] += 1

        # Collect response types
        for key, metrics in result['metrics'].items():
            if 'type' in metrics:
                stats['response_types'][metrics['type']] += 1

    return {
        'stats': stats,
        'results': results,
        'problematic_examples': problematic_examples[:20]  # Top 20 issues
    }

def print_report(analysis: Dict, filename: str):
    """Print analysis report"""
    stats = analysis['stats']
    total = stats['total_conversations']

    print(f"\n{'='*70}")
    print(f"📈 QUALITY REPORT: {filename}")
    print(f"{'='*70}")

    print(f"\n📊 Overall Statistics:")
    print(f"   Total conversations: {total}")
    print(f"   With repetition: {stats['conversations_with_repetition']} ({stats['conversations_with_repetition']/total*100:.1f}%)")
    print(f"   Too short responses: {stats['conversations_too_short']} ({stats['conversations_too_short']/total*100:.1f}%)")

    print(f"\n📏 Response Length Distribution:")
    for resp_type, count in sorted(stats['response_types'].items()):
        print(f"   {resp_type:12s}: {count:4d} ({count/sum(stats['response_types'].values())*100:.1f}%)")

    print(f"\n⚠️  Issue Types:")
    for issue_type, count in stats['issues_by_type'].items():
        print(f"   {issue_type:12s}: {count} occurrences")

    # Show problematic examples
    if analysis['problematic_examples']:
        print(f"\n🔍 Problematic Examples (showing first 10):")
        print("-" * 70)
        for idx, issue_type, issues in analysis['problematic_examples'][:10]:
            print(f"\n   Example #{idx} - {issue_type}:")
            for issue in issues[:2]:  # Show first 2 issues per example
                if issue['type'] == 'REPETITION':
                    print(f"      • Repeated {issue['count']}x: \"{issue['text']}\"")
                elif issue['type'] == 'TOO_SHORT':
                    print(f"      • Only {issue['word_count']} words: \"{issue['text']}\"")

    # Recommendations
    print(f"\n{'='*70}")
    print("💡 RECOMMENDATIONS:")
    print("=" * 70)

    repetition_pct = stats['conversations_with_repetition'] / total * 100
    short_pct = stats['conversations_too_short'] / total * 100

    if repetition_pct > 5:
        print(f"⚠️  HIGH REPETITION: {repetition_pct:.1f}% of examples have repeated content")
        print("   → Consider removing duplicate sentences from assistant responses")

    if short_pct > 10:
        print(f"⚠️  MANY SHORT RESPONSES: {short_pct:.1f}% are very short")
        print("   → Consider expanding terse responses or removing them")

    inconsistency_score = len(stats['response_types'])
    if inconsistency_score >= 4:
        print(f"⚠️  HIGH INCONSISTENCY: Responses vary from very short to very long")
        print("   → Consider standardizing response structure/length")

    if repetition_pct < 5 and short_pct < 10 and inconsistency_score < 4:
        print("✅ Data quality looks good overall!")
        print("   → Minor cleanup recommended but not critical")

    print()

def main():
    print("=" * 70)
    print("🔬 TRAINING DATA QUALITY ANALYSIS")
    print("=" * 70)

    training_dir = Path("training_data")

    if not training_dir.exists():
        print("❌ Error: training_data directory not found!")
        return

    files_to_check = [
        training_dir / "train.json",
        training_dir / "val.json",
    ]

    all_analyses = {}

    for filepath in files_to_check:
        if not filepath.exists():
            print(f"\n⚠️  {filepath.name}: File not found, skipping...")
            continue

        analysis = analyze_dataset(str(filepath))
        all_analyses[filepath.name] = analysis
        print_report(analysis, filepath.name)

    # Final summary
    print("\n" + "=" * 70)
    print("🎯 FINAL RECOMMENDATION")
    print("=" * 70)

    if all_analyses:
        total_issues = sum(
            len(a['problematic_examples'])
            for a in all_analyses.values()
        )

        if total_issues > 100:
            print("❌ CRITICAL: Significant data quality issues detected")
            print("   → Strongly recommend cleaning data before training")
            print("   → Use Argilla or manual review to fix repetition and short responses")
        elif total_issues > 20:
            print("⚠️  MODERATE: Some data quality issues detected")
            print("   → Recommend cleaning data, but training may still work")
            print("   → Focus on fixing repetition in assistant responses")
        else:
            print("✅ GOOD: Minor issues only")
            print("   → Safe to proceed with training")
            print("   → Optional: Clean up the flagged examples for best results")

if __name__ == "__main__":
    main()
