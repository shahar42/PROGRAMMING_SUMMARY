#!/usr/bin/env python3
"""
Cache Explanator - Refine concept explanations using Gemini LLM

Reads JSON concept files and uses Gemini to create concise, professional
explanations while preserving technical accuracy and all metadata.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import google.generativeai as genai
from tqdm import tqdm


class CacheExplanator:
    def __init__(self, dry_run: bool = False, delay: float = 1.0):
        """
        Initialize the explanator with Gemini API

        Args:
            dry_run: If True, don't write changes to files
            delay: Delay between API calls in seconds
        """
        self.dry_run = dry_run
        self.delay = delay

        # Setup Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

        # Statistics
        self.stats = {
            "processed": 0,
            "skipped": 0,
            "improved": 0,
            "errors": 0,
            "error_details": []
        }

        # Refinement prompt
        self.prompt_template = """You are a technical writing expert specializing in computer science and programming concepts.

Your task: you are an expert on cache and caching starategies Refine the following explanation to be CONCISE, PROFESSIONAL, and TECHNICALLY ACCURATE.

Requirements:
1. Keep it brief (2-8 sentences max for simple concepts, 4-10 for complex)
2. Lead with the core concept definition
3. Use precise technical terminology
4. Focus on practical understanding
8. NO introductory phrases like "This concept explains..." or "Understanding this is important..."
9. Get straight to the point

Original Topic: {topic}

Original Explanation:
{explanation}

Return ONLY the refined explanation text. No preamble, no meta-commentary, just the improved explanation."""

    def refine_explanation(self, topic: str, explanation: str) -> Optional[str]:
        """
        Use Gemini to refine an explanation

        Args:
            topic: The concept topic
            explanation: The original explanation

        Returns:
            Refined explanation or None if error
        """
        prompt = self.prompt_template.format(
            topic=topic,
            explanation=explanation
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.3,  # Lower temperature for consistency
                )
            )

            refined = response.text.strip()

            # Basic validation
            if len(refined) < 50:
                print(f"  ⚠️  Warning: Refined explanation seems too short ({len(refined)} chars)")
                return None

            if refined.lower().startswith(("this concept", "understanding", "this explains")):
                print(f"  ⚠️  Warning: Refined text has unwanted preamble")
                # Still return it, just warn

            return refined

        except Exception as e:
            print(f"  ❌ API Error: {e}")
            return None

    def process_concept(self, concept_file: Path) -> bool:
        """
        Process a single concept file

        Args:
            concept_file: Path to JSON concept file

        Returns:
            True if processed successfully
        """
        try:
            # Load concept
            with open(concept_file, 'r') as f:
                concept = json.load(f)

            # Check required fields
            if "topic" not in concept or "explanation" not in concept:
                print(f"  ⚠️  Skipping: Missing required fields")
                self.stats["skipped"] += 1
                return False

            original_explanation = concept["explanation"]
            topic = concept["topic"]

            # Refine explanation
            print(f"  🔄 Refining... (original: {len(original_explanation)} chars)")
            refined = self.refine_explanation(topic, original_explanation)

            if refined is None:
                self.stats["errors"] += 1
                return False

            # Show refinement result
            reduction = 100 * (1 - len(refined)/len(original_explanation)) if len(original_explanation) > 0 else 0
            print(f"  ✅ Refined: {len(original_explanation)} → {len(refined)} chars "
                  f"({reduction:.1f}% reduction)")

            # Update concept
            concept["explanation"] = refined

            # Add metadata about refinement
            if "extraction_metadata" not in concept:
                concept["extraction_metadata"] = {}

            concept["extraction_metadata"]["explanation_refined"] = True
            concept["extraction_metadata"]["refinement_date"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            concept["extraction_metadata"]["original_length"] = len(original_explanation)
            concept["extraction_metadata"]["refined_length"] = len(refined)

            # Write back (unless dry run)
            if not self.dry_run:
                with open(concept_file, 'w') as f:
                    json.dump(concept, f, indent=2, ensure_ascii=False)
                print(f"  💾 Saved")
            else:
                print(f"  🔍 DRY RUN - would save")

            self.stats["improved"] += 1
            return True

        except json.JSONDecodeError as e:
            error = f"JSON parse error in {concept_file.name}: {e}"
            print(f"  ❌ {error}")
            self.stats["errors"] += 1
            self.stats["error_details"].append(error)
            return False

        except Exception as e:
            error = f"Error processing {concept_file.name}: {e}"
            print(f"  ❌ {error}")
            self.stats["errors"] += 1
            self.stats["error_details"].append(error)
            return False

        finally:
            self.stats["processed"] += 1

    def process_directory(self, directory: Path, pattern: str = "*.json"):
        """
        Process all JSON files in a directory

        Args:
            directory: Directory containing concept files
            pattern: Glob pattern for files to process
        """
        concept_files = list(directory.glob(pattern))

        print(f"\n{'='*80}")
        print(f"Cache Explanator")
        print(f"{'='*80}")
        print(f"Directory: {directory}")
        print(f"Pattern: {pattern}")
        print(f"Files found: {len(concept_files)}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"{'='*80}\n")

        if not concept_files:
            print("No files to process!")
            return

        # Process each file
        for concept_file in tqdm(concept_files, desc="Processing concepts"):
            print(f"\n📄 {concept_file.name}")
            self.process_concept(concept_file)

            # Rate limiting
            if self.delay > 0:
                time.sleep(self.delay)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        print(f"\n{'='*80}")
        print(f"Summary")
        print(f"{'='*80}")
        print(f"Files processed: {self.stats['processed']}")
        print(f"Explanations improved: {self.stats['improved']}")
        print(f"Files skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")

        if self.stats["error_details"]:
            print(f"\nErrors encountered:")
            for error in self.stats["error_details"][:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.stats["error_details"]) > 10:
                print(f"  ... and {len(self.stats['error_details']) - 10} more")

        if self.stats['improved'] > 0:
            print(f"\n✅ Successfully refined {self.stats['improved']} explanations")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Refine concept explanations using Gemini LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on memory hierarchy concepts
  python3 cache_explanator.py --pattern "csap_*_memory_hierarchy_*.json" --dry-run

  # Process all concepts in directory
  python3 cache_explanator.py /path/to/concepts/

  # Process specific pattern with custom delay
  python3 cache_explanator.py --pattern "csap_ctrl_*.json" --delay 2.0

  # Live run (actually modify files)
  python3 cache_explanator.py --pattern "csap_*_memory_hierarchy_*.json"
"""
    )

    parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        default="rag_finetune/data/concepts",
        help="Directory containing concept JSON files (default: rag_finetune/data/concepts)"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="Glob pattern for files to process (default: *.json)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API calls in seconds (default: 1.0)"
    )

    args = parser.parse_args()

    # Resolve directory path
    directory = Path(args.directory)
    if not directory.is_absolute():
        # Assume relative to project root
        base_dir = Path(__file__).parent.parent.parent
        directory = base_dir / directory

    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}")
        sys.exit(1)

    # Create explanator and process
    explanator = CacheExplanator(dry_run=args.dry_run, delay=args.delay)
    explanator.process_directory(directory, pattern=args.pattern)


if __name__ == "__main__":
    main()
