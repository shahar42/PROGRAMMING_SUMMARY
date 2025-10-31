#!/usr/bin/env python3
"""
Generate MCP tool-use training dataset from concept JSON files.
Uses Gemini Flash to create realistic user questions and tool call sequences.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from tqdm import tqdm
import time
import hashlib

# Configuration
GEMINI_MODEL = "gemini-1.5-flash"
CONCEPTS_DIR = Path("outputs")
OUTPUT_DIR = Path("rag_finetune/data")
TRAIN_SPLIT = 0.9  # 90% train, 10% validation

# MCP tool schemas (will be imported)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_concepts",
            "description": "Search the programming concepts database by keywords or topics",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords, concept names, or topics)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_concept_details",
            "description": "Get full details of a specific concept by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept_id": {
                        "type": "string",
                        "description": "The unique concept ID"
                    }
                },
                "required": ["concept_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_concepts",
            "description": "Compare two concepts side-by-side",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept1_id": {"type": "string"},
                    "concept2_id": {"type": "string"}
                },
                "required": ["concept1_id", "concept2_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_book",
            "description": "Search concepts within a specific book",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_name": {"type": "string"},
                    "query": {"type": "string", "default": ""}
                },
                "required": ["book_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_category",
            "description": "Search concepts by category (mem, ptr, func, io, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "book_name": {"type": "string", "default": None},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["category"]
            }
        }
    }
]


def load_all_concepts() -> List[Dict]:
    """Load all JSON concept files from outputs/"""
    concepts = []

    for json_file in CONCEPTS_DIR.rglob("*.json"):
        # Skip cache and progress files
        if json_file.name in ["concept_cache.json", "progress.json"]:
            continue

        try:
            with open(json_file, 'r') as f:
                concept_data = json.load(f)

            # Extract book name and concept ID from path
            book_name = json_file.parent.name
            concept_id = json_file.stem

            concepts.append({
                "id": concept_id,
                "book": book_name,
                "topic": concept_data.get("topic", ""),
                "explanation": concept_data.get("explanation", ""),
                "source": concept_data.get("extraction_metadata", {}).get("source", ""),
                "file_path": str(json_file)
            })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Skipping {json_file}: {e}")
            continue

    return concepts


def generate_questions_and_tools(concept: Dict, model) -> Optional[Dict]:
    """
    Use Gemini to generate:
    1. Natural user question
    2. Expected tool call sequence
    3. Simulated tool response
    4. Brief answer
    """

    prompt = f"""You are creating training data for a small language model that uses MCP tools to retrieve C/C++ programming concepts.

Given this concept:
Topic: {concept['topic']}
Explanation: {concept['explanation'][:500]}...
Book: {concept['book']}
Concept ID: {concept['id']}

Generate training data in this EXACT JSON format:

{{
  "user_question": "<natural question a programmer might ask>",
  "tool_sequence": [
    {{
      "tool": "search_concepts",
      "arguments": {{"query": "relevant keywords", "limit": 5}}
    }},
    {{
      "tool": "get_concept_details",
      "arguments": {{"concept_id": "{concept['id']}"}}
    }}
  ],
  "final_answer": "<concise answer using the retrieved concept (2-3 sentences max)>"
}}

Requirements:
- User question should be natural and conversational
- Tool sequence should be realistic (search first, then get_details)
- Final answer should be brief and factual (you're not Claude, just a retrieval assistant)
- Use ONLY these tool names: search_concepts, get_concept_details, compare_concepts, search_by_book, search_by_category

Generate 1 example as valid JSON only (no markdown, no explanation):"""

    try:
        response = model.generate_content(prompt)

        # Extract JSON from response
        text = response.text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text.strip())

        # Validate structure
        required_keys = ["user_question", "tool_sequence", "final_answer"]
        if not all(k in data for k in required_keys):
            print(f"Warning: Missing keys in generated data for {concept['id']}")
            return None

        return data

    except Exception as e:
        print(f"Error generating for {concept['id']}: {e}")
        return None


def format_as_training_example(concept: Dict, generated_data: Dict) -> Dict:
    """Format as OpenAI chat completion with tool calls"""

    messages = [
        {
            "role": "system",
            "content": "You are a C/C++ programming assistant with access to a concepts database via MCP tools. Use tools to retrieve information, then provide concise answers."
        },
        {
            "role": "user",
            "content": generated_data["user_question"]
        }
    ]

    # Add tool call sequence
    for i, tool_call in enumerate(generated_data["tool_sequence"]):
        # Assistant makes tool call
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": f"call_{hashlib.md5(f'{concept["id"]}_{i}'.encode()).hexdigest()[:8]}",
                "type": "function",
                "function": {
                    "name": tool_call["tool"],
                    "arguments": json.dumps(tool_call["arguments"])
                }
            }]
        })

        # Simulate tool response
        if tool_call["tool"] == "search_concepts":
            tool_response = json.dumps([{
                "id": concept["id"],
                "title": concept["topic"],
                "book": concept["book"]
            }])
        elif tool_call["tool"] == "get_concept_details":
            tool_response = json.dumps({
                "id": concept["id"],
                "topic": concept["topic"],
                "explanation": concept["explanation"][:300] + "...",
                "source": concept["source"]
            })
        else:
            tool_response = "{}"

        messages.append({
            "role": "tool",
            "tool_call_id": messages[-1]["tool_calls"][0]["id"],
            "name": tool_call["tool"],
            "content": tool_response
        })

    # Final answer
    messages.append({
        "role": "assistant",
        "content": generated_data["final_answer"]
    })

    return {"messages": messages}


def main():
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    print("Loading concepts...")
    concepts = load_all_concepts()
    print(f"Found {len(concepts)} concepts")

    # Sample evenly across books
    books = {}
    for c in concepts:
        books.setdefault(c["book"], []).append(c)

    print(f"Books found: {list(books.keys())}")

    # Generate dataset
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_file = OUTPUT_DIR / "train.jsonl"
    val_file = OUTPUT_DIR / "validation.jsonl"

    training_examples = []

    print("\nGenerating training data with Gemini Flash...")
    for concept in tqdm(concepts, desc="Processing concepts"):
        generated = generate_questions_and_tools(concept, model)

        if generated:
            example = format_as_training_example(concept, generated)
            training_examples.append(example)

        # Rate limiting: Gemini Flash = 15 RPM free tier
        time.sleep(4)  # Safe rate: ~15 requests/minute

    # Shuffle and split
    import random
    random.shuffle(training_examples)

    split_idx = int(len(training_examples) * TRAIN_SPLIT)
    train_data = training_examples[:split_idx]
    val_data = training_examples[split_idx:]

    # Write JSONL files
    print(f"\nWriting {len(train_data)} training examples...")
    with open(train_file, 'w') as f:
        for example in train_data:
            f.write(json.dumps(example) + '\n')

    print(f"Writing {len(val_data)} validation examples...")
    with open(val_file, 'w') as f:
        for example in val_data:
            f.write(json.dumps(example) + '\n')

    print(f"\n✅ Dataset generation complete!")
    print(f"   Train: {train_file} ({len(train_data)} examples)")
    print(f"   Val:   {val_file} ({len(val_data)} examples)")

    # Save tool schemas
    schemas_file = OUTPUT_DIR / "tool_schemas.json"
    with open(schemas_file, 'w') as f:
        json.dump(TOOL_SCHEMAS, f, indent=2)
    print(f"   Tools: {schemas_file}")


if __name__ == "__main__":
    main()
