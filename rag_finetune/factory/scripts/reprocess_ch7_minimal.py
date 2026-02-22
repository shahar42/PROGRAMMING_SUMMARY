#!/usr/bin/env python3
"""
Minimal re-processing for stubborn failures - uses extremely strict limits
"""

import os
import json
import hashlib
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = BASE_DIR / "rag_finetune/apikeys.env"
OUTPUT_DIR = BASE_DIR / "rag_finetune/factory/output/The C++ Standard Library_pages_221_378"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

# Only the still-failing chunks
failed_chunks = [
    {
        "topic": "std::search_n Finding Consecutive Matching Elements",
        "category": "algo",
        "brief": "Searches for count consecutive elements equal to value. Returns iterator to first match or end."
    },
    {
        "topic": "std::search Algorithm Pattern Matching",
        "category": "algo",
        "brief": "Finds first occurrence of pattern range within search range. O(n*m) worst case complexity."
    },
    {
        "topic": "std::copy and std::copy_backward Overlap Safety",
        "category": "algo",
        "brief": "copy iterates forward safe for dest after source. copy_backward iterates backward safe for dest before source."
    },
    {
        "topic": "std::transform Binary Operation Overload",
        "category": "algo",
        "brief": "Applies binary function to corresponding elements from two ranges. Writes results to output range."
    }
]

def generate_concept_id(topic: str, category: str) -> str:
    prefix = "cppstdlib"
    clean_category = ''.join(c if c.isalnum() else '_' for c in category)
    slug = ''.join(c if c.isalnum() else '_' for c in topic.lower())
    slug = '_'.join(slug.split('_')[:6])
    hash_val = hashlib.md5(f"{topic}_{time.time()}".encode()).hexdigest()[:6]
    return f"{prefix}_{clean_category}_{slug}_{hash_val}"

for failed in failed_chunks:
    print(f"\n📝 Extracting: {failed['topic'][:50]}...")

    # Ultra-minimal prompt
    prompt = f"""Create a C++ standard library concept for: {failed['topic']}

Description: {failed['brief']}

Return ONE JSON object (not array) with these fields:
- topic: "{failed['topic']}"
- category: "{failed['category']}"
- explanation: 200 words max, no special chars, plain text only
- code_example: 10 lines max showing basic usage
- practical_example: One sentence
- keywords: array of 3-5 terms
- difficulty: "intermediate"
- page_reference: "200-300"
- chapter: "Chapter 7: STL Iterators"

CRITICAL: Keep it SHORT. No math notation. Complete the JSON fully.

Return ONLY the JSON object:"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.5
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        concept = json.loads(text)
        concept["id"] = generate_concept_id(concept["topic"], concept["category"])
        concept["book"] = "The C++ Standard Library: A Tutorial and Reference by Nicolai M. Josuttis"

        concept_file = OUTPUT_DIR / f"{concept['id']}.json"
        with open(concept_file, 'w') as f:
            json.dump(concept, f, indent=2)

        print(f"✅ Saved: {concept['id']}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        continue

    time.sleep(2)

print("\n✅ Done!")
