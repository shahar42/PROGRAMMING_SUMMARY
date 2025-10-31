#!/usr/bin/env python3
"""
Comprehensive dataset audit for V2 model issues
Checks:
1. Calibration percentage (expected 7%, actual?)
2. Semantic alignment of Q&A pairs
3. Duplicate detection
4. Question variation analysis
"""

import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple

def load_dataset(filepath: str) -> List[Dict]:
    """Load dataset from JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_calibration(data: List[Dict]) -> Dict:
    """Analyze calibration examples"""
    calibration_phrases = [
        # General clarification
        'i need more context', 'could you clarify', 'provide the complete',
        'provide code context', 'for specific analysis', 'for conceptual guidance',
        # Scope-related
        'out of scope', 'this model explains',
        # Specificity requests
        'specify which aspect', 'depends on',
        # Debugging redirection
        'not debugging', 'common pointer issues include',
        # Broader phrases from prepare_dataset.py
        'is a broad topic', 'has several aspects',
    ]

    cal_examples = []
    for idx, ex in enumerate(data):
        if len(ex['messages']) >= 3:
            answer = ex['messages'][2]['content'].lower()
            if any(phrase in answer for phrase in calibration_phrases):
                cal_examples.append({
                    'idx': idx,
                    'question': ex['messages'][1]['content'],
                    'answer_preview': ex['messages'][2]['content'][:150]
                })

    return {
        'count': len(cal_examples),
        'percentage': len(cal_examples) / len(data) * 100,
        'examples': cal_examples[:5],  # First 5 for inspection
        'total': len(data)
    }

def analyze_question_diversity(data: List[Dict]) -> Dict:
    """Analyze question diversity and variations"""
    questions = []
    for ex in data:
        if len(ex['messages']) >= 2:
            questions.append(ex['messages'][1]['content'])

    question_counts = Counter(questions)
    duplicates = {q: c for q, c in question_counts.items() if c > 1}

    # Analyze question patterns
    patterns = defaultdict(list)
    for q in questions:
        # Extract question type by first few words
        words = q.split()[:3]
        pattern = ' '.join(words)
        patterns[pattern].append(q)

    return {
        'total_questions': len(questions),
        'unique_questions': len(set(questions)),
        'uniqueness_pct': len(set(questions)) / len(questions) * 100,
        'duplicates': len(duplicates),
        'top_duplicates': sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10],
        'top_patterns': sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    }

def analyze_semantic_alignment(data: List[Dict]) -> Dict:
    """Check if questions and answers are semantically aligned"""
    misalignments = []

    # Keywords that should match between question and answer
    expert_keywords = {
        'performance': ['performance', 'speed', 'efficiency', 'overhead', 'cost'],
        'compiler': ['compiler', 'optimization', 'compile', 'optimized'],
        'memory': ['memory', 'layout', 'allocation', 'heap', 'stack'],
        'implementation': ['implementation', 'implement', 'how it works', 'internally'],
        'trade-off': ['trade-off', 'advantage', 'disadvantage', 'pros', 'cons'],
        'gotcha': ['gotcha', 'pitfall', 'problem', 'issue', 'careful', 'warning'],
    }

    for idx, ex in enumerate(data):
        if len(ex['messages']) >= 3:
            question = ex['messages'][1]['content'].lower()
            answer = ex['messages'][2]['content'].lower()

            # Skip calibration examples
            if 'i need more context' in answer or 'could you clarify' in answer:
                continue

            # Check for expert question keywords
            for category, keywords in expert_keywords.items():
                if any(kw in question for kw in keywords):
                    # Question asks about this topic, does answer address it?
                    if not any(kw in answer for kw in keywords):
                        misalignments.append({
                            'idx': idx,
                            'category': category,
                            'question': question[:100],
                            'answer_preview': answer[:150]
                        })
                    break

    return {
        'total_checked': len([ex for ex in data if len(ex['messages']) >= 3]),
        'misalignments': len(misalignments),
        'misalignment_pct': len(misalignments) / len(data) * 100,
        'examples': misalignments[:10]  # First 10 for inspection
    }

def analyze_answer_reuse(data: List[Dict]) -> Dict:
    """Check if same answers are used for different questions"""
    answer_to_questions = defaultdict(list)

    for idx, ex in enumerate(data):
        if len(ex['messages']) >= 3:
            # Skip calibration examples
            answer = ex['messages'][2]['content']
            if 'i need more context' in answer.lower():
                continue

            question = ex['messages'][1]['content']
            answer_key = answer
            answer_to_questions[answer_key].append({
                'idx': idx,
                'question': question
            })

    # Find answers used for multiple different questions
    reused_answers = {
        ans: qs for ans, qs in answer_to_questions.items()
        if len(qs) > 1 and len(set(q['question'] for q in qs)) > 1
    }

    return {
        'unique_answers': len(answer_to_questions),
        'reused_count': len(reused_answers),
        'examples': [
            {
                'answer_preview': ans[:100],
                'question_count': len(qs),
                'questions': [q['question'][:80] for q in qs[:3]]
            }
            for ans, qs in sorted(reused_answers.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        ]
    }

def main():
    print("=" * 80)
    print("🔍 COMPREHENSIVE DATASET AUDIT - V2 Model")
    print("=" * 80)
    print()

    # Load datasets
    train_file = Path("/home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning/fine_tuning_llama_v6/train.json")
    val_file = Path("/home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning/fine_tuning_llama_v6/val.json")

    if not train_file.exists():
        print("❌ Training file not found:", train_file)
        return

    print("📂 Loading datasets...")
    train_data = load_dataset(train_file)
    val_data = load_dataset(val_file) if val_file.exists() else []

    print(f"✅ Loaded {len(train_data)} training examples")
    print(f"✅ Loaded {len(val_data)} validation examples")
    print()

    # 1. Calibration Analysis
    print("=" * 80)
    print("📊 CALIBRATION ANALYSIS")
    print("=" * 80)
    cal_analysis = analyze_calibration(train_data)
    print(f"Total examples: {cal_analysis['total']}")
    print(f"Calibration examples: {cal_analysis['count']}")
    print(f"Actual percentage: {cal_analysis['percentage']:.2f}%")
    print(f"Expected percentage: 7.00%")
    print(f"Gap: {7.0 - cal_analysis['percentage']:.2f}%")

    if cal_analysis['percentage'] < 5.0:
        print("⚠️  WARNING: Calibration percentage below optimal range (5-10%)")
    elif cal_analysis['percentage'] > 10.0:
        print("⚠️  WARNING: Calibration percentage above optimal range (5-10%)")
    else:
        print("✅ Calibration percentage within optimal range")

    print("\nSample calibration questions:")
    for ex in cal_analysis['examples'][:3]:
        print(f"  Q: {ex['question'][:70]}...")
        print(f"  A: {ex['answer_preview'][:70]}...")
        print()

    # 2. Question Diversity
    print("=" * 80)
    print("📊 QUESTION DIVERSITY ANALYSIS")
    print("=" * 80)
    div_analysis = analyze_question_diversity(train_data)
    print(f"Total questions: {div_analysis['total_questions']}")
    print(f"Unique questions: {div_analysis['unique_questions']}")
    print(f"Uniqueness: {div_analysis['uniqueness_pct']:.1f}%")
    print(f"Duplicate questions: {div_analysis['duplicates']}")

    if div_analysis['duplicates'] > 0:
        print("\nTop duplicate questions:")
        for q, count in div_analysis['top_duplicates'][:5]:
            print(f"  [{count}x] {q[:70]}...")

    print("\nTop question patterns:")
    for pattern, questions in div_analysis['top_patterns'][:5]:
        print(f"  '{pattern}...': {len(questions)} variations")

    print()

    # 3. Semantic Alignment
    print("=" * 80)
    print("📊 SEMANTIC ALIGNMENT ANALYSIS")
    print("=" * 80)
    sem_analysis = analyze_semantic_alignment(train_data)
    print(f"Total Q&A pairs checked: {sem_analysis['total_checked']}")
    print(f"Potential misalignments: {sem_analysis['misalignments']}")
    print(f"Misalignment rate: {sem_analysis['misalignment_pct']:.2f}%")

    if sem_analysis['misalignments'] > 0:
        print("\n⚠️  WARNING: Found semantic misalignments")
        print("\nExamples of misaligned Q&A pairs:")
        for ex in sem_analysis['examples'][:5]:
            print(f"  Category: {ex['category']}")
            print(f"  Q: {ex['question'][:70]}...")
            print(f"  A: {ex['answer_preview'][:70]}...")
            print()
    else:
        print("✅ No semantic misalignments detected")

    print()

    # 4. Answer Reuse
    print("=" * 80)
    print("📊 ANSWER REUSE ANALYSIS")
    print("=" * 80)
    reuse_analysis = analyze_answer_reuse(train_data)
    print(f"Unique answers: {reuse_analysis['unique_answers']}")
    print(f"Answers reused for different questions: {reuse_analysis['reused_count']}")

    if reuse_analysis['reused_count'] > 0:
        print("\n⚠️  WARNING: Same answers used for different questions")
        print("\nTop reused answers:")
        for ex in reuse_analysis['examples'][:3]:
            print(f"  Answer: {ex['answer_preview']}...")
            print(f"  Used for {ex['question_count']} different questions:")
            for q in ex['questions']:
                print(f"    - {q}...")
            print()
    else:
        print("✅ No significant answer reuse detected")

    print()

    # Summary
    print("=" * 80)
    print("📋 AUDIT SUMMARY")
    print("=" * 80)

    issues = []

    if cal_analysis['percentage'] < 5.0 or cal_analysis['percentage'] > 10.0:
        issues.append(f"❌ Calibration percentage ({cal_analysis['percentage']:.2f}%) outside optimal range (5-10%)")

    if div_analysis['uniqueness_pct'] < 75.0:
        issues.append(f"❌ Low question uniqueness ({div_analysis['uniqueness_pct']:.1f}%)")

    if sem_analysis['misalignment_pct'] > 5.0:
        issues.append(f"❌ High semantic misalignment rate ({sem_analysis['misalignment_pct']:.2f}%)")

    if reuse_analysis['reused_count'] > 100:
        issues.append(f"❌ Excessive answer reuse ({reuse_analysis['reused_count']} cases)")

    if issues:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\n🔧 ACTION REQUIRED: Dataset needs to be regenerated with fixes")
    else:
        print("✅ No critical issues found")
        print("📊 Dataset appears to be within acceptable parameters")

    print()
    print("=" * 80)
    print("Audit complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
