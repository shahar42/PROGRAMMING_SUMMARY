#!/usr/bin/env python3
"""
Add searchable keywords to concept topics using Gemini API.
Prepends relevant search terms to improve semantic search matching.
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / "rag_finetune/apikeys.env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"

def generate_keywords(topic, explanation):
    """Ask Gemini to generate searchable keywords for a concept."""
    prompt = f"""Given this C/C++ programming concept:

Title: {topic}
Explanation: {explanation[:500]}...

Generate 2-4 highly searchable keywords or short phrases that users would likely search for to find this concept. These should be common terms, abbreviations, or alternative names.

Return ONLY the keywords separated by commas, nothing else. Be concise.

Examples:
- For "Copy-and-Swap Idiom" → "assignment operator, operator=, copy assignment"
- For "RAII Pattern" → "RAII, resource management, automatic cleanup"
- For "Virtual Function Tables" → "vtable, virtual functions, polymorphism"
"""

    try:
        response = model.generate_content(prompt)
        keywords = response.text.strip()
        return keywords
    except Exception as e:
        print(f"  Error generating keywords: {e}")
        return None

def update_concept_topic(concept_file, dry_run=True):
    """Update a single concept file with searchable keywords."""
    with open(concept_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_topic = data['topic']

    # Check if already has keywords (simple heuristic: starts with keywords followed by -)
    if original_topic.count(':') > 0 or original_topic.startswith('['):
        print(f"  Skipping (already has structure): {original_topic[:60]}...")
        return False

    print(f"\nProcessing: {original_topic}")

    # Generate keywords
    keywords = generate_keywords(original_topic, data['explanation'])
    if not keywords:
        return False

    print(f"  Keywords: {keywords}")

    # Create new topic with keywords prepended
    new_topic = f"{keywords} - {original_topic}"

    if dry_run:
        print(f"  Would update to: {new_topic[:80]}...")
    else:
        data['topic'] = new_topic
        with open(concept_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Updated: {concept_file.name}")

    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add searchable keywords to concept topics")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--limit", type=int, help="Limit number of concepts to process (for testing)")
    args = parser.parse_args()

    concept_files = sorted(CONCEPTS_DIR.glob("*.json"))

    if args.limit:
        concept_files = concept_files[:args.limit]

    print(f"Found {len(concept_files)} concept files")
    if args.dry_run:
        print("DRY RUN - No files will be modified\n")

    updated_count = 0

    for i, concept_file in enumerate(concept_files, 1):
        try:
            if update_concept_topic(concept_file, dry_run=args.dry_run):
                updated_count += 1
                # Rate limit to avoid API throttling
                if i < len(concept_files):
                    time.sleep(0.5)
        except Exception as e:
            print(f"  Error processing {concept_file.name}: {e}")
            continue

    print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated_count} concepts")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")
    else:
        print("\nRebuild index: python3 rag_finetune/scripts/build_concept_index.py")

if __name__ == "__main__":
    main()
