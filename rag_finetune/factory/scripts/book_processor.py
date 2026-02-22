#!/usr/bin/env python3
"""
Book Processor - Extract concepts from books using LLM
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
FACTORY_DIR = BASE_DIR / "rag_finetune/factory"
TEMPLATE_DIR = FACTORY_DIR / "templates"
OUTPUT_DIR = FACTORY_DIR / "output"
LOG_DIR = FACTORY_DIR / "logs"
ENV_FILE = BASE_DIR / "rag_finetune/apikeys.env"

# Load environment variables from .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Try loading from current directory as fallback
    load_dotenv()

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


class BookProcessor:
    def __init__(self, book_path: Path, config: Optional[Dict] = None, page_range: Optional[tuple] = None, template_override: Optional[str] = None):
        self.book_path = book_path
        self.book_name = book_path.stem
        self.config = config or self.load_config()
        self.page_range = page_range  # (start, end) tuple or None
        self.template_override = template_override  # CLI-specified template

        # Setup LLM
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        # Use Gemini 2.5 Flash Preview (September 2025 version)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

        # Load extraction prompt (with priority: CLI > config > default)
        self.extraction_prompt = self.load_prompt()

        # Output directory for this book (include page range if specified)
        if page_range:
            dir_name = f"{self.book_name}_pages_{page_range[0]}_{page_range[1]}"
        else:
            dir_name = self.book_name
        self.output_dir = OUTPUT_DIR / dir_name
        self.output_dir.mkdir(exist_ok=True)

        # Metadata
        self.metadata = {
            "book": self.config.get("title", self.book_name),
            "full_title": self.config.get("full_title", self.book_name),
            "author": self.config.get("author", "Unknown"),
            "year": self.config.get("year", None),
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "concepts_extracted": 0,
            "chunks_processed": 0,
            "errors": []
        }

    def load_config(self) -> Dict:
        """Load book configuration if exists"""
        config_path = self.book_path.with_suffix('.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)

        # Default config
        return {
            "title": self.book_name.replace('_', ' ').title(),
            "full_title": self.book_name.replace('_', ' ').title(),
            "category_prefix": self.book_name.lower()[:10],
            "chunk_size": 2000,
            "chunk_overlap": 200,
            "rate_limit_delay": 1.0
        }

    def load_prompt(self) -> str:
        """Load extraction prompt template with priority: CLI > config > default"""
        # Priority 1: CLI override
        if self.template_override:
            template_name = self.template_override
        # Priority 2: Config specification
        elif "extraction_template" in self.config:
            template_name = self.config["extraction_template"]
        # Priority 3: Default
        else:
            template_name = "extraction.txt"

        prompt_path = TEMPLATE_DIR / template_name

        if not prompt_path.exists():
            print(f"⚠️  Warning: Template not found: {prompt_path}")
            print(f"    Falling back to default: extraction.txt")
            prompt_path = TEMPLATE_DIR / "extraction.txt"

        print(f"📝 Using extraction template: {template_name}")

        with open(prompt_path, 'r') as f:
            return f.read()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into processable chunks"""
        chunk_size = self.config.get("chunk_size", 2000)
        overlap = self.config.get("chunk_overlap", 200)

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks

    def generate_concept_id(self, topic: str, category: str) -> str:
        """Generate unique concept ID"""
        prefix = self.config.get("category_prefix", "book")

        # Clean category - remove slashes and invalid filename chars
        clean_category = category.replace('/', '_').replace('\\', '_')
        clean_category = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean_category)

        # Create slug from topic
        slug = topic.lower()
        slug = ''.join(c if c.isalnum() else '_' for c in slug)
        slug = '_'.join(slug.split('_')[:5])  # Max 5 words

        # Generate hash for uniqueness
        hash_input = f"{self.book_name}_{topic}_{time.time()}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:6]

        return f"{prefix}_{clean_category}_{slug}_{hash_val}"

    def extract_concepts_from_chunk(self, chunk: str, chunk_num: int) -> List[Dict]:
        """Extract concepts from a text chunk using LLM"""
        prompt = f"""{self.extraction_prompt}

---

## Book Information
- Title: {self.config['title']}
- Chapter/Section: Chunk {chunk_num}

## Text Chunk

{chunk}

---

Extract concepts from this text. Return ONLY valid JSON array, no markdown:
"""

        try:
            # Configure generation with high output token limit to prevent truncation
            generation_config = genai.GenerationConfig(
                max_output_tokens=8192,  # High limit to prevent truncation
                temperature=0.7,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={'timeout': 120}  # 2 minute timeout
            )
            response_text = response.text.strip()

            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            concepts = json.loads(response_text)

            # Add metadata and generate IDs
            for concept in concepts:
                concept["id"] = self.generate_concept_id(
                    concept["topic"],
                    concept.get("category", "core")
                )
                concept["book"] = self.config["full_title"]

            return concepts

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error in chunk {chunk_num}: {e}"
            print(f"\n[ERROR] {error_msg}")
            print(f"[ERROR] Response text: {response_text[:500]}")
            self.metadata["errors"].append(error_msg)
            return []
        except Exception as e:
            error_msg = f"Error processing chunk {chunk_num}: {e}"
            print(f"\n[ERROR] {error_msg}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            self.metadata["errors"].append(error_msg)
            return []

    def save_concept(self, concept: Dict):
        """Save a concept to JSON file"""
        concept_file = self.output_dir / f"{concept['id']}.json"
        with open(concept_file, 'w') as f:
            json.dump(concept, f, indent=2)

    def load_checkpoint(self) -> int:
        """Load checkpoint to resume from last processed chunk"""
        checkpoint_file = self.output_dir / ".checkpoint"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_chunk', 0)
            except:
                return 0
        return 0

    def save_checkpoint(self, chunk_num: int):
        """Save checkpoint for resume capability"""
        checkpoint_file = self.output_dir / ".checkpoint"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'last_chunk': chunk_num,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

    def save_metadata(self):
        """Save processing metadata"""
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def read_book(self) -> str:
        """Read book content from file, optionally with page range"""
        suffix = self.book_path.suffix.lower()

        if suffix == '.txt':
            with open(self.book_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Page ranges don't apply to plain text files
            if self.page_range:
                print("⚠️  Warning: Page range specified but file is plain text. Processing entire file.")
            return content

        elif suffix == '.md':
            with open(self.book_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if self.page_range:
                print("⚠️  Warning: Page range specified but file is markdown. Processing entire file.")
            return content

        elif suffix == '.pdf':
            try:
                import PyPDF2
                with open(self.book_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    total_pages = len(reader.pages)

                    # Determine page range
                    if self.page_range:
                        start_page, end_page = self.page_range
                        # Convert to 0-indexed and validate
                        start_idx = start_page - 1  # PDF pages are 1-indexed in book
                        end_idx = end_page  # Inclusive end

                        if start_idx < 0 or end_idx > total_pages:
                            print(f"⚠️  Warning: Page range {start_page}-{end_page} out of bounds (PDF has {total_pages} pages)")
                            start_idx = max(0, start_idx)
                            end_idx = min(total_pages, end_idx)

                        print(f"📄 Extracting pages {start_page}-{end_page} (indices {start_idx}-{end_idx-1}) from {total_pages} total pages")
                        pages_to_read = reader.pages[start_idx:end_idx]
                    else:
                        print(f"📄 Reading all {total_pages} pages")
                        pages_to_read = reader.pages

                    text = []
                    for page in pages_to_read:
                        text.append(page.extract_text())
                    return '\n\n'.join(text)
            except ImportError:
                print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
                sys.exit(1)

        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def process(self):
        """Main processing pipeline"""
        print(f"\n{'='*80}")
        print(f"Processing: {self.book_name}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*80}\n")

        # Read book
        print("📖 Reading book content...")
        text = self.read_book()
        print(f"✓ Read {len(text)} characters\n")

        # Chunk text
        print("✂️  Chunking text...")
        chunks = self.chunk_text(text)
        print(f"✓ Created {len(chunks)} chunks\n")

        # Process chunks
        print(f"🤖 Extracting concepts with LLM...\n")
        rate_limit = self.config.get("rate_limit_delay", 1.0)

        # Load checkpoint for resume
        start_chunk = self.load_checkpoint()
        if start_chunk > 0:
            print(f"📍 Resuming from chunk {start_chunk + 1} (already processed {start_chunk} chunks)\n")

        # Early checkpoint milestones for quality review
        early_checkpoints = [1, 3, 10]

        all_concepts = []
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks", initial=start_chunk, total=len(chunks))):
            # Skip already processed chunks
            if i < start_chunk:
                continue

            concepts = self.extract_concepts_from_chunk(chunk, i + 1)
            all_concepts.extend(concepts)

            # Save concepts immediately
            for concept in concepts:
                self.save_concept(concept)

            self.metadata["chunks_processed"] += 1
            self.metadata["concepts_extracted"] += len(concepts)

            # Save checkpoint after each chunk
            self.save_checkpoint(i + 1)

            # Early checkpoint - pause for review
            total_concepts = self.metadata["concepts_extracted"]
            if total_concepts in early_checkpoints:
                print(f"\n\n{'='*80}")
                print(f"⏸️  CHECKPOINT: {total_concepts} concepts extracted")
                print(f"{'='*80}")
                print(f"\nReview the extracted concepts:")
                print(f"  cd {self.output_dir}")
                print(f"  ls -l")
                print(f"  cat <concept_file>.json")
                print(f"\nCheck:")
                print(f"  - Topic quality")
                print(f"  - Explanation clarity")
                print(f"  - Code examples present")
                print(f"  - Category assignment correct")

                user_input = input(f"\n✋ Continue processing? (y/n/q): ").lower().strip()

                if user_input == 'q':
                    print("\n🛑 Processing aborted by user.")
                    self.save_metadata()
                    print(f"📊 Progress saved: {total_concepts} concepts extracted")
                    sys.exit(0)
                elif user_input == 'n':
                    print("\n⏹️  Processing paused.")
                    print(f"💡 To resume, delete bad concepts and adjust config/prompts, then re-run.")
                    self.save_metadata()
                    sys.exit(0)
                elif user_input == 'y':
                    print("\n✅ Continuing...\n")
                else:
                    print("\n⚠️  Invalid input, treating as 'y' (continue)\n")

            # Rate limiting
            if i < len(chunks) - 1:
                time.sleep(rate_limit)

        # Save metadata
        self.save_metadata()

        # Summary
        print(f"\n{'='*80}")
        print(f"✅ Processing Complete!")
        print(f"{'='*80}")
        print(f"Concepts extracted: {self.metadata['concepts_extracted']}")
        print(f"Chunks processed: {self.metadata['chunks_processed']}")
        print(f"Errors: {len(self.metadata['errors'])}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nNext steps:")
        print(f"1. Review concepts: ls {self.output_dir}")
        print(f"2. Integrate: python3 factory/scripts/batch_integrate.py {self.output_dir}")
        print()


def parse_page_range(range_str: str) -> tuple:
    """Parse page range string like '29-67' into (29, 67)"""
    try:
        parts = range_str.split('-')
        if len(parts) != 2:
            raise ValueError("Page range must be START-END")
        start = int(parts[0])
        end = int(parts[1])
        if start >= end:
            raise ValueError("Start page must be less than end page")
        return (start, end)
    except Exception as e:
        print(f"Error: Invalid page range '{range_str}': {e}")
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract concepts from programming books using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process entire book
  python3 book_processor.py factory/books/my_book.pdf

  # Process specific pages
  python3 book_processor.py factory/books/my_book.pdf --pages 29-67

  # Use custom template
  python3 book_processor.py factory/books/my_book.pdf --template custom.txt

  # Combine options
  python3 book_processor.py factory/books/my_book.pdf --pages 29-67 --template effective_modern_cpp_type_deduction.txt
"""
    )

    parser.add_argument("book_file", type=str, help="Path to book file (PDF, TXT, MD)")
    parser.add_argument("--pages", type=str, help="Page range to process (e.g., 29-67)")
    parser.add_argument("--template", type=str, help="Custom extraction template filename")

    args = parser.parse_args()

    # Validate book file
    book_path = Path(args.book_file)
    if not book_path.exists():
        print(f"Error: File not found: {book_path}")
        sys.exit(1)

    # Parse page range if specified
    page_range = None
    if args.pages:
        page_range = parse_page_range(args.pages)
        print(f"Page range: {page_range[0]}-{page_range[1]}")

    # Create processor
    processor = BookProcessor(
        book_path=book_path,
        page_range=page_range,
        template_override=args.template
    )
    processor.process()


if __name__ == "__main__":
    main()
