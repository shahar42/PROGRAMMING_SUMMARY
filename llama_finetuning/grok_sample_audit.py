#!/usr/bin/env python3 -u
"""
Grok Sample Audit - Industry Best Practice
Audits 500 stratified random samples instead of full dataset
Runtime: ~30 minutes vs 1-2 days for full audit
"""

import json
import os
import sys
import time
import requests
import random
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

load_dotenv()

GROK_API_KEY = os.getenv('GROK_API_KEY')
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

# Sample configuration
SAMPLE_SIZE = 100
REQUESTS_PER_MINUTE = 30
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE

# Output files
RESULTS_FILE = "fine_tuning_llama_v9_clean/grok_sample_audit_results.json"
ERROR_LOG = "fine_tuning_llama_v9_clean/grok_sample_audit_errors.log"

def log_error(msg):
    """Log errors to file"""
    with open(ERROR_LOG, 'a') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(f"ERROR: {msg}", file=sys.stderr)

def load_dataset(path: str) -> List[Dict]:
    """Load training dataset"""
    with open(path, 'r') as f:
        return json.load(f)

def stratified_sample(dataset: List[Dict], sample_size: int) -> List[Tuple[int, Dict]]:
    """
    Stratified sampling: ensure diverse representation
    - Long answers (complex concepts)
    - Short answers (simple facts)
    - Assembly examples
    - sizeof examples
    - Random mix
    """
    print("📊 Creating stratified sample...")

    # Categorize examples
    long_answers = []
    short_answers = []
    assembly_examples = []
    sizeof_examples = []

    for idx, ex in enumerate(dataset):
        answer = ""
        question = ""
        for msg in ex.get('messages', []):
            if msg['role'] == 'user':
                question = msg['content'].lower()
            elif msg['role'] == 'assistant':
                answer = msg['content']

        # Categorize
        if 'sizeof' in question:
            sizeof_examples.append((idx, ex))
        elif 'assembly' in question or '```asm' in answer.lower():
            assembly_examples.append((idx, ex))
        elif len(answer) > 2000:
            long_answers.append((idx, ex))
        elif len(answer) < 500:
            short_answers.append((idx, ex))

    # Sample proportionally (adjusted for 100 samples)
    samples = []
    samples.extend(random.sample(sizeof_examples, min(10, len(sizeof_examples))))
    samples.extend(random.sample(assembly_examples, min(10, len(assembly_examples))))
    samples.extend(random.sample(long_answers, min(30, len(long_answers))))
    samples.extend(random.sample(short_answers, min(20, len(short_answers))))

    # Fill remaining with pure random
    remaining = sample_size - len(samples)
    if remaining > 0:
        all_indices = set(range(len(dataset)))
        sampled_indices = set(idx for idx, _ in samples)
        available = list(all_indices - sampled_indices)
        random_samples = random.sample(available, min(remaining, len(available)))
        samples.extend((idx, dataset[idx]) for idx in random_samples)

    print(f"   Sizeof: {min(10, len(sizeof_examples))}")
    print(f"   Assembly: {min(10, len(assembly_examples))}")
    print(f"   Long answers: {min(30, len(long_answers))}")
    print(f"   Short answers: {min(20, len(short_answers))}")
    print(f"   Random: {remaining}")
    print(f"   Total: {len(samples)}")

    return samples

def create_grading_prompt(question: str, answer: str) -> str:
    """Create grading prompt for Grok"""
    answer_truncated = answer[:2000] + ("..." if len(answer) > 2000 else "")

    return f"""Grade this C/C++ Q&A pair for corruption.

**Question:**
{question}

**Answer:**
{answer_truncated}

**Check for:**
1. Concept mismatch (asks about X, answers about Y)
2. Factual errors (wrong sizeof, wrong behavior, hallucinated keywords)
3. Misleading/incomplete explanations

**Respond ONLY:**
VERDICT: [PASS/FAIL/SUSPICIOUS]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASON: [One sentence if FAIL/SUSPICIOUS, blank if PASS]

Be strict but avoid false positives."""

def call_grok_api(prompt: str) -> str:
    """Call Grok API with retry logic"""
    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not found")

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-4-fast",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 200
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            raise
        except Exception as e:
            log_error(f"API error: {str(e)}")
            raise

def parse_response(response: str) -> Tuple[str, str, str]:
    """Parse Grok response"""
    lines = response.strip().split('\n')
    verdict = "UNKNOWN"
    confidence = "UNKNOWN"
    reason = ""

    for line in lines:
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            confidence = line.split(":", 1)[1].strip()
        elif line.startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    return verdict, confidence, reason

def main():
    print("🤖 GROK SAMPLE AUDIT (100 Examples)")
    print("=" * 80)
    print("Strategy: Stratified sampling (industry best practice)")
    print("Runtime: ~6 minutes")
    print("=" * 80)

    # Load dataset
    print("\n📂 Loading dataset...")
    dataset = load_dataset('fine_tuning_llama_v9_clean/train.json')
    print(f"   Total: {len(dataset)} examples")

    # Create stratified sample
    samples = stratified_sample(dataset, SAMPLE_SIZE)

    # Estimate
    estimated_time = (len(samples) * DELAY_BETWEEN_REQUESTS) / 60
    print(f"\n⏱️  Estimated time: {estimated_time:.1f} minutes")
    print()

    # Audit samples
    results = {
        'total_dataset': len(dataset),
        'sample_size': len(samples),
        'pass': 0,
        'fail': [],
        'suspicious': [],
        'errors': []
    }

    start_time = time.time()

    for i, (idx, example) in enumerate(samples):
        try:
            print(f"   Processing {i+1}/{len(samples)} (index {idx})...", end='', flush=True)

            # Extract Q&A
            question = ""
            answer = ""
            for msg in example.get('messages', []):
                if msg['role'] == 'user':
                    question = msg['content']
                elif msg['role'] == 'assistant':
                    answer = msg['content']

            if not question or not answer:
                print(" SKIP (no Q&A)")
                continue

            # Grade with Grok
            prompt = create_grading_prompt(question, answer)
            response = call_grok_api(prompt)
            print(" DONE", flush=True)
            verdict, confidence, reason = parse_response(response)

            # Record result
            if verdict == "FAIL":
                results['fail'].append({
                    'index': idx,
                    'confidence': confidence,
                    'reason': reason,
                    'question': question[:200]
                })
            elif verdict == "SUSPICIOUS":
                results['suspicious'].append({
                    'index': idx,
                    'confidence': confidence,
                    'reason': reason,
                    'question': question[:200]
                })
            else:
                results['pass'] += 1

            # Progress update every 25
            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(samples) - i - 1) / rate / 60
                print(f"   [{i + 1}/{len(samples)}] Pass: {results['pass']}, "
                      f"Fail: {len(results['fail'])}, "
                      f"Suspicious: {len(results['suspicious'])}, "
                      f"ETA: {remaining:.1f}m")

            # Rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            results['errors'].append({'index': idx, 'error': str(e)})

    # Calculate statistics
    total_issues = len(results['fail']) + len(results['suspicious'])
    error_rate = (total_issues / len(samples)) * 100

    # Extrapolate to full dataset
    estimated_full_issues = int((total_issues / len(samples)) * len(dataset))

    print(f"\n{'=' * 80}")
    print("SAMPLE AUDIT COMPLETE")
    print(f"{'=' * 80}")
    print(f"Sample size: {len(samples)} / {len(dataset)} ({len(samples)/len(dataset)*100:.1f}%)")
    print(f"✅ Pass: {results['pass']}")
    print(f"❌ Fail: {len(results['fail'])}")
    print(f"⚠️  Suspicious: {len(results['suspicious'])}")
    print(f"🔴 Errors: {len(results['errors'])}")
    print()
    print(f"📊 Sample error rate: {error_rate:.2f}%")
    print(f"📊 Estimated full dataset issues: ~{estimated_full_issues} examples")
    print(f"📊 Estimated clean: {100 - error_rate:.2f}%")

    # Show failures
    if results['fail']:
        print(f"\n{'=' * 80}")
        print("FAILURES")
        print(f"{'=' * 80}")
        for item in results['fail'][:10]:
            print(f"\nIndex: {item['index']}")
            print(f"Reason: {item['reason']}")
            print(f"Question: {item['question']}...")

    # Show suspicious
    if results['suspicious']:
        print(f"\n{'=' * 80}")
        print("SUSPICIOUS")
        print(f"{'=' * 80}")
        for item in results['suspicious'][:10]:
            print(f"\nIndex: {item['index']}")
            print(f"Reason: {item['reason']}")
            print(f"Question: {item['question']}...")

    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {RESULTS_FILE}")

    # Recommendation
    print(f"\n{'=' * 80}")
    print("RECOMMENDATION")
    print(f"{'=' * 80}")
    if error_rate < 1.0:
        print("✅ Dataset quality is EXCELLENT (<1% issues)")
        print("   Proceed with training")
    elif error_rate < 5.0:
        print("⚠️  Dataset quality is GOOD (1-5% issues)")
        print("   Review failures, then proceed")
    else:
        print("🔴 Dataset quality needs work (>5% issues)")
        print("   Fix identified issues before training")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    random.seed(42)  # Reproducible sampling
    main()
