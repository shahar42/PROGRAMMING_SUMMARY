#!/usr/bin/env python3
"""
Generate code examples for flagged concepts using LLM.
Creates a separate JSON file with concept_id -> code_example mapping.
"""

import json
import os
import signal
import sys
from pathlib import Path
from typing import Dict
from tqdm import tqdm
import google.generativeai as genai
import time

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set")
    sys.exit(1)
genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
FLAGGED_FILE = BASE_DIR / "rag_finetune/data/concepts_needing_examples.json"
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"
OUTPUT_FILE = BASE_DIR / "rag_finetune/data/code_examples.json"


def generate_code_example(topic: str, explanation: str, example_type: str, reason: str, model) -> str:
    """Generate a focused code example for the concept"""

    prompt = f"""You are writing code snippets for a reference card, NOT a tutorial.

Topic: {topic}
Context: {explanation[:500]}

Think "flash card" - show the essence in <15 lines.

Examples of reference card style:
```cpp
class Resource {{
    int* data;
    explicit Resource(size_t s) : data(new int[s]) {{}}
    ~Resource() {{ delete[] data; }}
}};
```

```cpp
constexpr int square(int x) {{ return x * x; }}
constexpr int val = square(5);  // Compile-time
```

```c
int* ptr = malloc(sizeof(int) * 10);
ptr[0] = 42;
free(ptr);
```

NOT like this (too much boilerplate):
```cpp
#include <iostream>
int main() {{
    // ... lots of setup
    return 0;
}}
```

Generate ONLY the minimal code snippet (no includes, no main, no markdown markers).
"""

    try:
        response = model.generate_content(prompt)
        code = response.text.strip()

        # Clean up markdown if present
        if "```cpp" in code:
            code = code.split("```cpp")[1].split("```")[0].strip()
        elif "```c++" in code:
            code = code.split("```c++")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return code

    except Exception as e:
        print(f"Error generating example: {e}")
        return f"// Error generating example: {e}"


def load_concept_data(file_path: str) -> Dict:
    """Load the full concept JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)


def should_save_checkpoint(count: int) -> bool:
    """Determine if we should save a checkpoint at this count"""
    checkpoints = [1, 10, 50, 500, 1000, 2000, 5000, 10000]
    return count in checkpoints


def save_checkpoint(code_examples: Dict, checkpoint_num: int):
    """Save a checkpoint file"""
    checkpoint_file = BASE_DIR / f"rag_finetune/data/code_examples_checkpoint_{checkpoint_num}.json"
    output_data = {
        "total_examples": len(code_examples),
        "checkpoint": checkpoint_num,
        "examples": code_examples
    }
    with open(checkpoint_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"\n💾 Checkpoint saved: {checkpoint_num} examples")


def generate_all_examples(model):
    """Generate code examples for all concepts"""

    # Load all concepts from directory
    concept_files = list(CONCEPTS_DIR.glob("*.json"))
    code_examples = {}

    print(f"Generating code examples for {len(concept_files)} concepts...")

    for concept_file in tqdm(concept_files):
        try:
            # Load concept data
            concept_data = load_concept_data(concept_file)
            concept_id = concept_data.get("id", concept_file.stem)
            topic = concept_data.get("topic", "")
            explanation = concept_data.get("explanation", "")

            # Skip if already has code example
            if "code_example" in concept_data and concept_data["code_example"]:
                continue

            # Determine example type and reason
            example_type = "demonstration"
            reason = f"Code example needed to demonstrate {topic}"

            # Generate code example
            code = generate_code_example(topic, explanation, example_type, reason, model)

            code_examples[concept_id] = {
                "topic": topic,
                "example_type": example_type,
                "code": code
            }

            # Save checkpoint if at milestone
            if should_save_checkpoint(len(code_examples)):
                save_checkpoint(code_examples, len(code_examples))

            # Rate limiting
            time.sleep(0.3)

        except Exception as e:
            print(f"\nError processing {concept_file.name}: {e}")
            continue

    return code_examples


def save_examples(code_examples):
    """Save code examples to file"""
    output_data = {
        "total_examples": len(code_examples),
        "examples": code_examples
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 Saved {len(code_examples)} examples to {OUTPUT_FILE}")


# Global variable for signal handler
current_examples = {}

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Interrupted! Saving progress...")
    save_examples(current_examples)
    print(f"✅ Progress saved! Generated {len(current_examples)} examples.")
    sys.exit(0)


def main():
    global current_examples

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

    # Generate examples
    code_examples = generate_all_examples(model)
    current_examples = code_examples

    # Save results
    save_examples(code_examples)
    print(f"\n✅ Code examples generated!")
    print(f"   Total examples: {len(code_examples)}")


if __name__ == "__main__":
    main()
