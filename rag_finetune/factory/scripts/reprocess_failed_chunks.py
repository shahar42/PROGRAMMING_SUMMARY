#!/usr/bin/env python3
"""
Re-process failed chunks from book extraction
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = BASE_DIR / "rag_finetune/apikeys.env"
TEMPLATE_DIR = BASE_DIR / "rag_finetune/factory/templates"
OUTPUT_DIR = BASE_DIR / "rag_finetune/factory/output/The C++ Standard Library_pages_37_69"

# Load environment variables
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Setup LLM
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

# Load template
template_path = TEMPLATE_DIR / "cpp_stdlib_containers_iterators_io.txt"
with open(template_path, 'r') as f:
    template = f.read()

# Failed chunk texts (from error messages)
failed_chunks = [
    {
        "num": 4,
        "topic_hint": "std::make_pair() Utility, Convenience, and Zero Overhead Guarantee",
        "category": "util"
    },
    {
        "num": 19,
        "topic_hint": "std::auto_ptr Destructive Copy Semantics and Ownership Transfer",
        "category": "util"
    },
    {
        "num": 35,
        "topic_hint": "Generic std::swap Definition and Copy Requirements",
        "category": "util"
    }
]

def generate_concept_id(topic: str, category: str) -> str:
    """Generate unique concept ID"""
    prefix = "cppstdlib"
    slug = topic.lower()
    slug = ''.join(c if c.isalnum() else '_' for c in slug)
    slug = '_'.join(slug.split('_')[:8])
    hash_val = hashlib.md5(f"{topic}_{time.time()}".encode()).hexdigest()[:6]
    return f"{prefix}_{category}_{slug}_{hash_val}"

def extract_single_concept(topic_hint: str, category: str, chunk_num: int):
    """Extract a single concept with more focused prompt"""
    
    prompt = f"""{template}

---

IMPORTANT: You are re-extracting a SINGLE concept that failed previously due to truncation.

Focus ONLY on this topic:
**{topic_hint}**

Expected category: {category}

Requirements:
1. Return ONLY ONE concept (not an array of multiple)
2. Keep explanation under 800 words
3. Keep code example under 15 lines
4. Ensure the JSON is complete and valid

Return format:
```json
{{
  "topic": "...",
  "category": "{category}",
  "explanation": "...",
  "code_example": "...",
  "practical_example": "...",
  "keywords": [...],
  "difficulty": "...",
  "page_reference": "...",
  "chapter": "Chapter 4: Utilities"
}}
```

Extract this concept now. Return ONLY valid JSON, no markdown:
"""

    try:
        generation_config = genai.GenerationConfig(
            max_output_tokens=4096,  # Reduced to prevent truncation
            temperature=0.7,
        )

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            request_options={'timeout': 120}
        )
        response_text = response.text.strip()

        # Clean up response
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Parse JSON
        concept = json.loads(response_text)
        
        # Add metadata
        concept["id"] = generate_concept_id(concept["topic"], concept.get("category", category))
        concept["book"] = "The C++ Standard Library: A Tutorial and Reference by Nicolai M. Josuttis"
        
        return concept

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
        print(f"[ERROR] Response text: {response_text[:500]}")
        return None
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "="*80)
    print("Re-processing Failed Chunks")
    print("="*80 + "\n")
    
    for failed in failed_chunks:
        print(f"\n📝 Re-extracting chunk {failed['num']}: {failed['topic_hint'][:60]}...")
        
        concept = extract_single_concept(
            failed['topic_hint'],
            failed['category'],
            failed['num']
        )
        
        if concept:
            # Save concept
            concept_file = OUTPUT_DIR / f"{concept['id']}.json"
            with open(concept_file, 'w') as f:
                json.dump(concept, f, indent=2)
            print(f"✅ Saved: {concept['id']}")
        else:
            print(f"❌ Failed to extract chunk {failed['num']}")
        
        # Rate limit
        time.sleep(2)
    
    print("\n" + "="*80)
    print("✅ Re-processing Complete!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
