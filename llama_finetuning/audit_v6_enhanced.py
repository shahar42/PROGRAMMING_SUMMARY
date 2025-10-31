#!/usr/bin/env python3
"""
Comprehensive audit of V6 Enhanced dataset for deep reference assistant task.
Checks:
1. Assembly-level content coverage
2. Low-level detail depth
3. Answer quality and completeness
4. Topic distribution
5. Potential issues (truncation, hallucinations, vagueness)
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List

def load_dataset(filepath: Path) -> List[Dict]:
    """Load training dataset."""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_assembly_coverage(examples: List[Dict]) -> Dict:
    """Analyze assembly-level content."""
    assembly_indicators = {
        'assembly_code': r'```(asm|assembly|nasm|gas)',
        'registers': r'\b(rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|r[8-9]|r1[0-5]|eax|ebx|ecx|edx|esi|edi)\b',
        'instructions': r'\b(mov|push|pop|call|ret|add|sub|jmp|je|jne|cmp|lea|xor)\b',
        'x86_64_abi': r'\b(System V ABI|calling convention|red zone|stack frame)\b',
        'gcc_output': r'(gcc -S|objdump|disassembly|AT&T syntax|Intel syntax)',
        'memory_layout': r'\b(stack layout|heap layout|alignment|padding|offset)\b',
        'compiler_behavior': r'\b(compiler generates|optimization level|-O[0-3]|inlining|register allocation)\b',
    }

    results = {key: 0 for key in assembly_indicators}
    examples_with_assembly = 0

    for ex in examples:
        answer = ex['messages'][2]['content']
        has_assembly = False

        for key, pattern in assembly_indicators.items():
            if re.search(pattern, answer, re.IGNORECASE):
                results[key] += 1
                has_assembly = True

        if has_assembly:
            examples_with_assembly += 1

    results['total_with_assembly'] = examples_with_assembly
    results['assembly_percentage'] = (examples_with_assembly / len(examples)) * 100

    return results

def analyze_depth_quality(examples: List[Dict]) -> Dict:
    """Analyze technical depth and quality."""
    depth_indicators = {
        'concrete_examples': 0,  # Has actual code
        'tool_output': 0,        # Shows gcc/gdb/pahole output
        'numeric_specifics': 0,  # Specific sizes/offsets
        'multi_paragraph': 0,    # Detailed explanation
        'references': 0,         # Cites K&R, CSAPP, C++ Standard
        'hedge_words': 0,        # "might", "usually", "typically" (vagueness)
        'incomplete': 0,         # Ends mid-sentence
    }

    code_pattern = r'```'
    tool_output_pattern = r'(sizeof|pahole|nm|readelf|objdump|gdb).*?(\d+|0x[0-9a-f]+)'
    numeric_pattern = r'\b(\d+) byte|offset \d+|0x[0-9a-f]+'
    reference_pattern = r'\b(K&R|Kernighan|Ritchie|CSAPP|C\+\+ Standard|ISO C|C11|C17|C\+\+17|C\+\+20)\b'
    hedge_pattern = r'\b(might|may|usually|typically|often|sometimes|likely|probably|depends on)\b'

    lengths = []
    paragraph_counts = []

    for ex in examples:
        answer = ex['messages'][2]['content']
        lengths.append(len(answer))

        # Count paragraphs
        paragraphs = [p for p in answer.split('\n\n') if p.strip()]
        paragraph_counts.append(len(paragraphs))

        if re.search(code_pattern, answer):
            depth_indicators['concrete_examples'] += 1

        if re.search(tool_output_pattern, answer, re.IGNORECASE):
            depth_indicators['tool_output'] += 1

        if re.search(numeric_pattern, answer, re.IGNORECASE):
            depth_indicators['numeric_specifics'] += 1

        if len(paragraphs) >= 3:
            depth_indicators['multi_paragraph'] += 1

        if re.search(reference_pattern, answer):
            depth_indicators['references'] += 1

        hedge_count = len(re.findall(hedge_pattern, answer, re.IGNORECASE))
        if hedge_count >= 3:  # 3+ hedge words = potentially vague
            depth_indicators['hedge_words'] += 1

        # Check for incomplete answers
        if answer.strip().endswith(('`', '"', '(', '[', '{')) or len(answer) < 100:
            depth_indicators['incomplete'] += 1

    depth_indicators['avg_length'] = sum(lengths) / len(lengths)
    depth_indicators['avg_paragraphs'] = sum(paragraph_counts) / len(paragraph_counts)
    depth_indicators['min_length'] = min(lengths)
    depth_indicators['max_length'] = max(lengths)

    return depth_indicators

def analyze_topic_distribution(examples: List[Dict]) -> Dict:
    """Analyze topic coverage."""
    topics = Counter()
    question_patterns = Counter()

    assembly_topics = 0
    memory_topics = 0
    compiler_topics = 0
    abi_topics = 0

    for ex in examples:
        topic = ex.get('metadata', {}).get('topic', 'unknown')
        topics[topic] += 1

        question = ex['messages'][1]['content'].lower()
        answer = ex['messages'][2]['content'].lower()

        # Categorize by deep reference topics
        if any(kw in answer for kw in ['assembly', 'instruction', 'register', 'x86']):
            assembly_topics += 1
        if any(kw in answer for kw in ['memory layout', 'alignment', 'padding', 'vtable', 'stack']):
            memory_topics += 1
        if any(kw in answer for kw in ['compiler', 'optimization', 'generates', 'gcc', 'clang']):
            compiler_topics += 1
        if any(kw in answer for kw in ['abi', 'calling convention', 'linkage', 'symbol']):
            abi_topics += 1

        # Question patterns
        if 'how does' in question:
            question_patterns['how_does'] += 1
        elif 'what' in question:
            question_patterns['what'] += 1
        elif 'explain' in question:
            question_patterns['explain'] += 1
        elif 'why' in question:
            question_patterns['why'] += 1
        elif 'show' in question or 'example' in question:
            question_patterns['example_request'] += 1

    return {
        'top_topics': topics.most_common(10),
        'question_patterns': dict(question_patterns),
        'deep_reference_coverage': {
            'assembly_level': assembly_topics,
            'memory_internals': memory_topics,
            'compiler_details': compiler_topics,
            'abi_linkage': abi_topics,
        }
    }

def find_potential_issues(examples: List[Dict]) -> Dict:
    """Find potential data quality issues."""
    issues = {
        'very_short_answers': [],      # < 300 chars
        'suspiciously_long': [],       # > 5000 chars
        'missing_code_examples': [],   # Question asks for example, no code block
        'vague_answers': [],           # Many hedge words, no specifics
        'truncated': [],               # Ends abruptly
        'no_assembly_when_expected': [], # Question about low-level, answer is high-level
    }

    for i, ex in enumerate(examples):
        question = ex['messages'][1]['content']
        answer = ex['messages'][2]['content']

        # Very short
        if len(answer) < 300:
            issues['very_short_answers'].append({
                'index': i,
                'length': len(answer),
                'question': question[:100]
            })

        # Suspiciously long
        if len(answer) > 5000:
            issues['suspiciously_long'].append({
                'index': i,
                'length': len(answer),
                'question': question[:100]
            })

        # Missing code when requested
        if ('example' in question.lower() or 'show' in question.lower()) and '```' not in answer:
            issues['missing_code_examples'].append({
                'index': i,
                'question': question[:100]
            })

        # Vague answers (many hedges, no concrete details)
        hedge_count = len(re.findall(r'\b(might|may|usually|typically|often|sometimes|likely|probably)\b', answer, re.IGNORECASE))
        has_concrete = bool(re.search(r'```|sizeof.*?\d+|\d+ byte|0x[0-9a-f]+', answer))
        if hedge_count >= 4 and not has_concrete:
            issues['vague_answers'].append({
                'index': i,
                'hedge_count': hedge_count,
                'question': question[:100]
            })

        # Truncated
        if answer.strip().endswith(('`', '"', '(', '...')) or (len(answer) > 500 and not answer.strip()[-1] in '.!'):
            issues['truncated'].append({
                'index': i,
                'last_50_chars': answer[-50:]
            })

        # No assembly when expected
        if any(kw in question.lower() for kw in ['assembly', 'instruction', 'register', 'compile']):
            if not re.search(r'\b(mov|push|rax|assembly|instruction)\b', answer, re.IGNORECASE):
                issues['no_assembly_when_expected'].append({
                    'index': i,
                    'question': question[:100]
                })

    return issues

def main():
    print("="*80)
    print("V6 Enhanced Dataset Audit - Deep Reference Assistant Fitness")
    print("="*80)
    print()

    # Load dataset
    train_path = Path('fine_tuning_llama_v6_enhanced_final/train.json')
    if not train_path.exists():
        print(f"❌ Training dataset not found: {train_path}")
        return

    print("📂 Loading dataset...")
    examples = load_dataset(train_path)
    print(f"   ✓ Loaded {len(examples)} training examples")
    print()

    # Assembly coverage
    print("="*80)
    print("🔧 Assembly-Level Content Coverage")
    print("="*80)
    assembly_stats = analyze_assembly_coverage(examples)
    print(f"   Examples with assembly content: {assembly_stats['total_with_assembly']} ({assembly_stats['assembly_percentage']:.1f}%)")
    print(f"\n   Breakdown:")
    print(f"     Assembly code blocks:     {assembly_stats['assembly_code']:5d} ({assembly_stats['assembly_code']/len(examples)*100:5.1f}%)")
    print(f"     Register references:      {assembly_stats['registers']:5d} ({assembly_stats['registers']/len(examples)*100:5.1f}%)")
    print(f"     Assembly instructions:    {assembly_stats['instructions']:5d} ({assembly_stats['instructions']/len(examples)*100:5.1f}%)")
    print(f"     x86-64 ABI details:       {assembly_stats['x86_64_abi']:5d} ({assembly_stats['x86_64_abi']/len(examples)*100:5.1f}%)")
    print(f"     GCC/compiler output:      {assembly_stats['gcc_output']:5d} ({assembly_stats['gcc_output']/len(examples)*100:5.1f}%)")
    print(f"     Memory layout details:    {assembly_stats['memory_layout']:5d} ({assembly_stats['memory_layout']/len(examples)*100:5.1f}%)")
    print(f"     Compiler behavior:        {assembly_stats['compiler_behavior']:5d} ({assembly_stats['compiler_behavior']/len(examples)*100:5.1f}%)")
    print()

    # Depth quality
    print("="*80)
    print("📊 Technical Depth & Quality")
    print("="*80)
    depth_stats = analyze_depth_quality(examples)
    print(f"   Average answer length:    {depth_stats['avg_length']:.0f} chars")
    print(f"   Average paragraphs:       {depth_stats['avg_paragraphs']:.1f}")
    print(f"   Min/Max length:           {depth_stats['min_length']} / {depth_stats['max_length']} chars")
    print(f"\n   Deep reference indicators:")
    print(f"     Concrete code examples:   {depth_stats['concrete_examples']:5d} ({depth_stats['concrete_examples']/len(examples)*100:5.1f}%)")
    print(f"     Tool output (gcc/gdb):    {depth_stats['tool_output']:5d} ({depth_stats['tool_output']/len(examples)*100:5.1f}%)")
    print(f"     Numeric specifics:        {depth_stats['numeric_specifics']:5d} ({depth_stats['numeric_specifics']/len(examples)*100:5.1f}%)")
    print(f"     Multi-paragraph (3+):     {depth_stats['multi_paragraph']:5d} ({depth_stats['multi_paragraph']/len(examples)*100:5.1f}%)")
    print(f"     Authoritative refs:       {depth_stats['references']:5d} ({depth_stats['references']/len(examples)*100:5.1f}%)")
    print(f"\n   ⚠️  Quality concerns:")
    print(f"     Vague/hedging answers:    {depth_stats['hedge_words']:5d} ({depth_stats['hedge_words']/len(examples)*100:5.1f}%)")
    print(f"     Incomplete answers:       {depth_stats['incomplete']:5d} ({depth_stats['incomplete']/len(examples)*100:5.1f}%)")
    print()

    # Topic distribution
    print("="*80)
    print("🎯 Topic Distribution & Deep Reference Coverage")
    print("="*80)
    topic_stats = analyze_topic_distribution(examples)
    print(f"   Deep reference topic coverage:")
    coverage = topic_stats['deep_reference_coverage']
    print(f"     Assembly-level content:   {coverage['assembly_level']:5d} ({coverage['assembly_level']/len(examples)*100:5.1f}%)")
    print(f"     Memory internals:         {coverage['memory_internals']:5d} ({coverage['memory_internals']/len(examples)*100:5.1f}%)")
    print(f"     Compiler details:         {coverage['compiler_details']:5d} ({coverage['compiler_details']/len(examples)*100:5.1f}%)")
    print(f"     ABI/Linkage:              {coverage['abi_linkage']:5d} ({coverage['abi_linkage']/len(examples)*100:5.1f}%)")
    print(f"\n   Question patterns:")
    for pattern, count in topic_stats['question_patterns'].items():
        print(f"     {pattern:25s} {count:5d} ({count/len(examples)*100:5.1f}%)")
    print()

    # Issues
    print("="*80)
    print("🔍 Potential Data Quality Issues")
    print("="*80)
    issues = find_potential_issues(examples)
    print(f"   Very short answers (<300 chars):  {len(issues['very_short_answers']):5d}")
    print(f"   Suspiciously long (>5000 chars):  {len(issues['suspiciously_long']):5d}")
    print(f"   Missing code when requested:      {len(issues['missing_code_examples']):5d}")
    print(f"   Vague/non-specific answers:       {len(issues['vague_answers']):5d}")
    print(f"   Truncated answers:                {len(issues['truncated']):5d}")
    print(f"   No assembly when expected:        {len(issues['no_assembly_when_expected']):5d}")

    # Show examples of issues
    if issues['vague_answers'][:3]:
        print(f"\n   Sample vague answers:")
        for issue in issues['vague_answers'][:3]:
            print(f"     [{issue['index']}] {issue['question']}... ({issue['hedge_count']} hedge words)")

    if issues['no_assembly_when_expected'][:3]:
        print(f"\n   Sample missing assembly:")
        for issue in issues['no_assembly_when_expected'][:3]:
            print(f"     [{issue['index']}] {issue['question']}...")

    print()

    # Overall assessment
    print("="*80)
    print("📈 Overall Assessment for Deep Reference Assistant Task")
    print("="*80)

    # Calculate fitness score
    assembly_score = assembly_stats['assembly_percentage']
    depth_score = (depth_stats['concrete_examples'] + depth_stats['tool_output']) / len(examples) * 100
    quality_score = 100 - (depth_stats['hedge_words'] + depth_stats['incomplete']) / len(examples) * 100

    overall_fitness = (assembly_score + depth_score + quality_score) / 3

    print(f"   Assembly coverage:     {assembly_score:5.1f}%")
    print(f"   Deep detail score:     {depth_score:5.1f}%")
    print(f"   Quality score:         {quality_score:5.1f}%")
    print(f"   ---")
    print(f"   Overall fitness:       {overall_fitness:5.1f}%")
    print()

    if overall_fitness >= 70:
        print("   ✅ Dataset is READY for deep reference assistant training")
    elif overall_fitness >= 50:
        print("   ⚠️  Dataset is ACCEPTABLE but could be improved")
    else:
        print("   ❌ Dataset needs MORE assembly-level content before training")

    print()
    print("="*80)

    # Save detailed report
    report = {
        'total_examples': len(examples),
        'assembly_coverage': assembly_stats,
        'depth_quality': depth_stats,
        'topic_distribution': topic_stats,
        'issues': {k: len(v) for k, v in issues.items()},
        'fitness_scores': {
            'assembly': assembly_score,
            'depth': depth_score,
            'quality': quality_score,
            'overall': overall_fitness
        }
    }

    with open('v6_enhanced_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📄 Detailed report saved to: v6_enhanced_audit_report.json")
    print()

if __name__ == '__main__':
    main()
