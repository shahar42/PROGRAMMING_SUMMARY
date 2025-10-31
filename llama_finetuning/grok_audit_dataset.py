#!/usr/bin/env python3 -u
"""
Grok-Based Dataset Corruption Audit for V7
Uses xAI Grok API to grade Q&A pairs for conceptual correctness

Industry best practice: LLM grading with expert validation
Model: grok-4-fast-reasoning
"""

import json
import os
import sys
import time
import requests
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

# Load environment variables
load_dotenv()

GROK_API_KEY = os.getenv('GROK_API_KEY')
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

# Rate limiting configuration
REQUESTS_PER_MINUTE = 30  # Conservative (API limit is 480/min)
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE  # 2 seconds

# Progress tracking
CHECKPOINT_FILE = "fine_tuning_llama_v7_sizeof/grok_audit_checkpoint.json"
RESULTS_FILE = "fine_tuning_llama_v7_sizeof/grok_audit_results.json"
ERROR_LOG = "fine_tuning_llama_v7_sizeof/grok_audit_errors.log"
PROGRESS_MD = "fine_tuning_llama_v7_sizeof/progress.md"

# Setup error logging
def log_error(msg):
    """Log errors to file for debugging"""
    with open(ERROR_LOG, 'a') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(f"ERROR: {msg}", file=sys.stderr)

def load_dataset(path: str) -> List[Dict]:
    """Load training dataset"""
    with open(path, 'r') as f:
        return json.load(f)

def create_grading_prompt(question: str, answer: str) -> str:
    """Create prompt for Grok to grade Q&A pair"""
    # Truncate answer to 2000 chars for API efficiency
    answer_truncated = answer[:2000] + ("..." if len(answer) > 2000 else "")

    return f"""You are auditing a C/C++ programming Q&A dataset for corruption. Grade this Q&A pair for conceptual correctness.

**Known corruption patterns:**
1. **Concept mismatch**: Question asks about X, answer explains Y
   Example: "using declaration" question → "using namespace directive" answer
2. **Factual errors**: Wrong sizeof values, wrong behavior, hallucinated keywords
   Example: sizeof(struct{{char;int}}) = 4 bytes (actually 8 with padding)
3. **Misleading explanations**: Incomplete/wrong purpose
   Example: inline = "optimization only" (missing ODR compliance - the PRIMARY purpose)
4. **Impossible claims**: explicit on function templates (compile error)

**Question:**
{question}

**Answer:**
{answer_truncated}

**Grade this Q&A pair:**
1. Does answer correctly address the question?
2. Are technical facts accurate?
3. Any conceptual mismatches or misleading info?

**Respond ONLY with this format (no extra text):**
VERDICT: [PASS/FAIL/SUSPICIOUS]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASON: [One brief sentence if FAIL or SUSPICIOUS, otherwise leave blank]

Examples:
- PASS answer: "VERDICT: PASS\\nCONFIDENCE: HIGH\\nREASON:"
- FAIL answer: "VERDICT: FAIL\\nCONFIDENCE: HIGH\\nREASON: Asks about using declaration but answer only discusses using namespace directive"
- SUSPICIOUS answer: "VERDICT: SUSPICIOUS\\nCONFIDENCE: MEDIUM\\nREASON: Explains inline without mentioning ODR compliance"

Be strict but avoid false positives. Only flag clear errors."""

def call_grok_api(prompt: str) -> str:
    """Call Grok API and return response"""
    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not found in environment")

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-4-fast",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,  # Deterministic grading
        "max_tokens": 200
    }

    # Retry logic for timeouts
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                log_error(f"API timeout (attempt {attempt+1}/{max_retries}), retrying...")
                time.sleep(5)
                continue
            else:
                log_error(f"API timeout after {max_retries} attempts")
                raise
        except requests.exceptions.HTTPError as e:
            log_error(f"HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            raise
        except Exception as e:
            log_error(f"API call failed: {str(e)}")
            raise

def parse_grok_response(response: str) -> Tuple[str, str, str]:
    """Parse Grok's response into verdict, confidence, reason"""
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

def load_checkpoint() -> Dict:
    """Load progress checkpoint if exists"""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_index': -1,
        'results': {
            'total': 0,
            'pass': 0,
            'fail': [],
            'suspicious': [],
            'errors': []
        }
    }

def save_checkpoint(checkpoint: Dict):
    """Save progress checkpoint"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def save_final_results(results: Dict):
    """Save final audit results"""
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

def audit_example(example: Dict, index: int) -> Tuple[str, str, str]:
    """Audit a single Q&A pair using Grok"""
    messages = example.get('messages', [])

    question = ""
    answer = ""
    for msg in messages:
        if msg['role'] == 'user':
            question = msg['content']
        elif msg['role'] == 'assistant':
            answer = msg['content']

    if not question or not answer:
        return "PASS", "HIGH", ""

    # Create grading prompt
    prompt = create_grading_prompt(question, answer)

    # Call Grok API
    try:
        response = call_grok_api(prompt)
        verdict, confidence, reason = parse_grok_response(response)
        return verdict, confidence, reason
    except Exception as e:
        return "ERROR", "N/A", str(e)

def main():
    print("🤖 GROK-BASED DATASET CORRUPTION AUDIT")
    print("=" * 80)
    print("Model: grok-4-fast")
    print("Rate limit: 30 requests/min (2 sec delay)")
    print("=" * 80)

    # Load dataset
    print("\n📂 Loading training dataset...")
    train_data = load_dataset('fine_tuning_llama_v7_sizeof/train.json')
    total_examples = len(train_data)
    print(f"   Total examples: {total_examples}")

    # Load checkpoint
    checkpoint = load_checkpoint()
    start_index = checkpoint['last_index'] + 1
    results = checkpoint['results']

    if start_index > 0:
        print(f"\n♻️  Resuming from checkpoint: index {start_index}")
        print(f"   Progress: {start_index}/{total_examples} ({start_index/total_examples*100:.1f}%)")

    # Estimate time and cost
    remaining = total_examples - start_index
    estimated_time_hours = (remaining * DELAY_BETWEEN_REQUESTS) / 3600
    estimated_cost_min = (remaining * 300) * 0.20 / 1_000_000  # Input tokens
    estimated_cost_max = estimated_cost_min + (remaining * 200) * 0.50 / 1_000_000  # + Output tokens

    print(f"\n📊 Audit plan:")
    print(f"   Remaining examples: {remaining}")
    print(f"   Estimated time: {estimated_time_hours:.1f} hours")
    print(f"   Estimated cost: ${estimated_cost_min:.2f} - ${estimated_cost_max:.2f}")
    print()

    # Audit examples
    print(f"🔍 Starting audit...")
    print(f"   Progress will be saved every 100 examples")
    print()

    start_time = time.time()

    for idx in range(start_index, total_examples):
        try:
            # Audit example
            verdict, confidence, reason = audit_example(train_data[idx], idx)

            # Record result
            if verdict == "FAIL":
                results['fail'].append({
                    'index': idx,
                    'confidence': confidence,
                    'reason': reason,
                    'question': train_data[idx]['messages'][1]['content'][:200] if len(train_data[idx]['messages']) > 1 else ""
                })
            elif verdict == "SUSPICIOUS":
                results['suspicious'].append({
                    'index': idx,
                    'confidence': confidence,
                    'reason': reason,
                    'question': train_data[idx]['messages'][1]['content'][:200] if len(train_data[idx]['messages']) > 1 else ""
                })
            elif verdict == "ERROR":
                results['errors'].append({
                    'index': idx,
                    'error': reason
                })
            else:
                results['pass'] += 1

            # Update checkpoint
            checkpoint['last_index'] = idx
            results['total'] = idx + 1

            # Save checkpoint every 100 examples
            if (idx + 1) % 100 == 0:
                save_checkpoint(checkpoint)
                elapsed = time.time() - start_time
                rate = (idx + 1 - start_index) / elapsed
                remaining_time = (total_examples - idx - 1) / rate / 3600

                print(f"   [{idx + 1}/{total_examples}] "
                      f"Pass: {results['pass']}, "
                      f"Fail: {len(results['fail'])}, "
                      f"Suspicious: {len(results['suspicious'])}, "
                      f"ETA: {remaining_time:.1f}h")

            # Rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            print(f"   Progress saved at index {idx}")
            print(f"   Resume by running this script again")
            save_checkpoint(checkpoint)
            return
        except Exception as e:
            print(f"\n❌ Error at index {idx}: {e}")
            results['errors'].append({'index': idx, 'error': str(e)})
            # Continue with next example
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Final results
    print(f"\n{'=' * 80}")
    print("AUDIT COMPLETE")
    print(f"{'=' * 80}")
    print(f"Total examples: {results['total']}")
    print(f"✅ Pass: {results['pass']}")
    print(f"❌ Fail: {len(results['fail'])}")
    print(f"⚠️  Suspicious: {len(results['suspicious'])}")
    print(f"🔴 Errors: {len(results['errors'])}")

    # Show failures
    if results['fail']:
        print(f"\n{'=' * 80}")
        print("FAILURES (High Priority)")
        print(f"{'=' * 80}")
        for item in results['fail'][:20]:
            print(f"\nIndex: {item['index']}")
            print(f"Confidence: {item['confidence']}")
            print(f"Reason: {item['reason']}")
            print(f"Question: {item['question']}...")
        if len(results['fail']) > 20:
            print(f"\n... and {len(results['fail']) - 20} more failures")

    # Show suspicious
    if results['suspicious']:
        print(f"\n{'=' * 80}")
        print("SUSPICIOUS (Manual Review Needed)")
        print(f"{'=' * 80}")
        for item in results['suspicious'][:10]:
            print(f"\nIndex: {item['index']}")
            print(f"Confidence: {item['confidence']}")
            print(f"Reason: {item['reason']}")
            print(f"Question: {item['question']}...")
        if len(results['suspicious']) > 10:
            print(f"\n... and {len(results['suspicious']) - 10} more suspicious")

    # Save final results
    save_final_results(results)
    print(f"\n💾 Results saved to: {RESULTS_FILE}")

    # Generate removal list
    if results['fail']:
        fail_indices = [item['index'] for item in results['fail']]
        with open('grok_corruption_removal.txt', 'w') as f:
            for idx in fail_indices:
                f.write(f"{idx}\n")
        print(f"   Failure indices saved to: grok_corruption_removal.txt")

    # Clean up checkpoint
    if Path(CHECKPOINT_FILE).exists():
        Path(CHECKPOINT_FILE).unlink()
        print(f"   Checkpoint file removed")

    print(f"\n{'=' * 80}")
    print("NEXT STEPS")
    print(f"{'=' * 80}")
    if results['fail'] or results['suspicious']:
        print(f"1. Review {len(results['fail'])} FAIL examples")
        print(f"2. Manually inspect {len(results['suspicious'])} SUSPICIOUS examples")
        print(f"3. Remove/fix confirmed corruptions")
        print(f"4. Proceed with training")
    else:
        print("✅ No corruption detected!")
        print("   Dataset is ready for training")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    main()
