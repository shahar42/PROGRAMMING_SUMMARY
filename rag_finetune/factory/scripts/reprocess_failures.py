#!/usr/bin/env python3
"""
Reprocess Failed Chunks - Re-extract concepts from chunks that had JSON parse errors
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
FACTORY_DIR = BASE_DIR / "rag_finetune/factory"
TEMPLATE_DIR = FACTORY_DIR / "templates"
OUTPUT_DIR = FACTORY_DIR / "output"
ENV_FILE = BASE_DIR / "rag_finetune/apikeys.env"

# Load environment variables
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


def parse_error_log(log_text: str) -> List[Tuple[int, str]]:
    """
    Extract failed chunk numbers and error types from error log output.

    Returns: List of (chunk_number, error_message) tuples
    """
    failures = []

    # Pattern: [ERROR] JSON parse error in chunk N: <error message>
    pattern = r'\[ERROR\] JSON parse error in chunk (\d+): (.+)'

    for line in log_text.split('\n'):
        match = re.search(pattern, line)
        if match:
            chunk_num = int(match.group(1))
            error_msg = match.group(2)
            failures.append((chunk_num, error_msg))

    return failures


def reprocess_chunk(processor, chunk_text: str, chunk_num: int, max_retries: int = 3) -> List[Dict]:
    """
    Reprocess a single chunk with retry logic and adaptive strategies.

    Strategies:
    1. First retry: Same prompt
    2. Second retry: Reduce temperature, increase timeout
    3. Third retry: Ask for fewer concepts (1-2 instead of 2-5)
    """
    print(f"\n{'='*80}")
    print(f"Reprocessing chunk {chunk_num}")
    print(f"{'='*80}\n")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")

            # Adaptive strategy based on attempt
            if attempt == 1:
                # Standard retry
                temperature = 0.7
                timeout = 120
                concept_guidance = "Extract 2-5 distinct, well-defined concepts from the text."
            elif attempt == 2:
                # More conservative
                temperature = 0.5
                timeout = 180
                concept_guidance = "Extract 2-5 distinct, well-defined concepts from the text."
            else:
                # Most conservative - ask for fewer concepts
                temperature = 0.3
                timeout = 240
                concept_guidance = "Extract 1-3 distinct, well-defined concepts from the text. Focus on the most important concepts only."

            # Build prompt with adaptive guidance
            prompt = f"""{processor.extraction_prompt.replace('Extract 2-5 distinct, well-defined concepts from the text.', concept_guidance)}

---

## Book Information
- Title: {processor.config['title']}
- Chapter/Section: Chunk {chunk_num} (RETRY ATTEMPT {attempt})

## Text Chunk

{chunk_text}

---

Extract concepts from this text. Return ONLY valid JSON array, no markdown:
"""

            # Configure generation
            generation_config = genai.GenerationConfig(
                max_output_tokens=8192,
                temperature=temperature,
            )

            response = processor.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={'timeout': timeout}
            )
            response_text = response.text.strip()

            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            concepts = json.loads(response_text)

            # Success!
            print(f"✅ Successfully extracted {len(concepts)} concepts on attempt {attempt}")

            # Add metadata and IDs
            for concept in concepts:
                concept["id"] = processor.generate_concept_id(
                    concept["topic"],
                    concept.get("category", "core")
                )
                concept["book"] = processor.config["full_title"]

            return concepts

        except json.JSONDecodeError as e:
            print(f"❌ Attempt {attempt} failed: JSON parse error: {e}")
            if attempt == max_retries:
                print(f"⚠️  All retries exhausted for chunk {chunk_num}")
                print(f"    Last response snippet: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
                return []
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt == max_retries:
                print(f"⚠️  All retries exhausted for chunk {chunk_num}")
                return []

    return []


def main():
    import argparse
    from book_processor import BookProcessor

    parser = argparse.ArgumentParser(
        description="Reprocess failed chunks from book extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reprocess specific chunks
  python3 reprocess_failures.py "The C++ Standard Library.pdf" --chunks 4,19,35 --pages 37-69

  # Reprocess from error log
  python3 reprocess_failures.py "The C++ Standard Library.pdf" --error-log errors.txt --pages 37-69
"""
    )

    parser.add_argument("book_file", type=str, help="Path to book file (PDF)")
    parser.add_argument("--chunks", type=str, help="Comma-separated chunk numbers to reprocess (e.g., 4,19,35)")
    parser.add_argument("--error-log", type=str, help="Path to error log file containing failure messages")
    parser.add_argument("--pages", type=str, required=True, help="Page range (e.g., 37-69)")
    parser.add_argument("--template", type=str, help="Extraction template filename")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts per chunk (default: 3)")

    args = parser.parse_args()

    # Validate inputs
    if not args.chunks and not args.error_log:
        print("Error: Must specify either --chunks or --error-log")
        sys.exit(1)

    # Parse page range
    parts = args.pages.split('-')
    page_range = (int(parts[0]), int(parts[1]))

    # Load book processor (to get config and extraction logic)
    book_path = Path(args.book_file)
    processor = BookProcessor(
        book_path=book_path,
        page_range=page_range,
        template_override=args.template
    )

    # Read book and chunk
    print("📖 Reading book content...")
    text = processor.read_book()
    print(f"✓ Read {len(text)} characters\n")

    print("✂️  Chunking text...")
    chunks = processor.chunk_text(text)
    print(f"✓ Created {len(chunks)} chunks\n")

    # Determine which chunks to reprocess
    if args.chunks:
        chunk_numbers = [int(x.strip()) for x in args.chunks.split(',')]
    else:
        # Parse error log
        with open(args.error_log, 'r') as f:
            log_text = f.read()
        failures = parse_error_log(log_text)
        chunk_numbers = [chunk_num for chunk_num, _ in failures]

    print(f"🔄 Reprocessing {len(chunk_numbers)} failed chunks: {chunk_numbers}\n")

    # Reprocess each failed chunk
    total_extracted = 0
    total_failed = 0

    for chunk_num in chunk_numbers:
        # Validate chunk number
        if chunk_num < 1 or chunk_num > len(chunks):
            print(f"⚠️  Warning: Chunk {chunk_num} out of range (1-{len(chunks)}), skipping")
            continue

        # Get chunk text (chunk_num is 1-indexed)
        chunk_text = chunks[chunk_num - 1]

        # Reprocess
        concepts = reprocess_chunk(processor, chunk_text, chunk_num, args.max_retries)

        if concepts:
            # Save concepts
            for concept in concepts:
                processor.save_concept(concept)
                total_extracted += 1
            print(f"✅ Saved {len(concepts)} concepts from chunk {chunk_num}")
        else:
            total_failed += 1
            print(f"❌ Failed to extract concepts from chunk {chunk_num}")

    # Summary
    print(f"\n{'='*80}")
    print(f"✅ Reprocessing Complete!")
    print(f"{'='*80}")
    print(f"Concepts extracted: {total_extracted}")
    print(f"Chunks failed: {total_failed}")
    print(f"Output directory: {processor.output_dir}")
    print()


if __name__ == "__main__":
    main()
