#!/usr/bin/env python3
"""
Batch Integrate - Move extracted concepts into main database
"""

import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent.parent.parent.parent
FACTORY_OUTPUT = BASE_DIR / "rag_finetune/factory/output"
CONCEPTS_DIR = BASE_DIR / "rag_finetune/data/concepts"
BOOK_CONFIG = BASE_DIR / "rag_finetune/config/book_config.json"


class BatchIntegrator:
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.metadata_file = source_dir / "metadata.json"

        if not self.metadata_file.exists():
            raise ValueError(f"No metadata.json found in {source_dir}")

        with open(self.metadata_file, 'r') as f:
            self.metadata = json.load(f)

        self.stats = {
            "concepts_copied": 0,
            "concepts_skipped": 0,
            "book_configured": False,
            "errors": []
        }

    def get_concept_files(self) -> List[Path]:
        """Get all concept JSON files (excluding metadata)"""
        files = []
        for f in self.source_dir.glob("*.json"):
            if f.name != "metadata.json":
                files.append(f)
        return files

    def validate_concept(self, concept: Dict) -> bool:
        """Validate concept has required fields"""
        required = ["id", "topic", "book", "explanation"]
        for field in required:
            if field not in concept:
                return False
        return True

    def copy_concepts(self):
        """Copy concept files to main database"""
        print(f"\n📦 Copying concepts to {CONCEPTS_DIR}...")

        CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)

        concept_files = self.get_concept_files()

        for concept_file in concept_files:
            try:
                # Load and validate
                with open(concept_file, 'r') as f:
                    concept = json.load(f)

                if not self.validate_concept(concept):
                    print(f"⚠️  Skipping invalid concept: {concept_file.name}")
                    self.stats["concepts_skipped"] += 1
                    continue

                # Check for duplicates
                dest_file = CONCEPTS_DIR / concept_file.name
                if dest_file.exists():
                    print(f"⚠️  Skipping duplicate: {concept_file.name}")
                    self.stats["concepts_skipped"] += 1
                    continue

                # Copy
                shutil.copy2(concept_file, dest_file)
                self.stats["concepts_copied"] += 1

            except Exception as e:
                error = f"Error copying {concept_file.name}: {e}"
                print(f"❌ {error}")
                self.stats["errors"].append(error)

        print(f"✓ Copied {self.stats['concepts_copied']} concepts")
        print(f"✓ Skipped {self.stats['concepts_skipped']} concepts")

    def update_book_config(self):
        """Add book to book_config.json if not present"""
        print(f"\n📚 Updating book configuration...")

        try:
            # Load existing config
            with open(BOOK_CONFIG, 'r') as f:
                config = json.load(f)

            book_title = self.metadata.get("full_title")
            if not book_title:
                print("⚠️  No book title in metadata, skipping config update")
                return

            # Check if already configured
            if book_title in config['books']:
                print(f"✓ Book already configured: {book_title}")
                return

            # Generate short name and display name
            title = self.metadata.get("title", book_title)
            short = title[:15] if len(title) > 15 else title

            # Find unused color
            used_colors = {b['color'] for b in config['books'].values()}
            available = [c for c in config['available_colors'] if c not in used_colors]
            color = available[0] if available else "white"

            # Add to config
            config['books'][book_title] = {
                "color": color,
                "short": short,
                "display": title
            }

            # Save
            with open(BOOK_CONFIG, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"✓ Added book to config: {title}")
            print(f"  Color: {color}")
            self.stats["book_configured"] = True

        except Exception as e:
            error = f"Error updating book config: {e}"
            print(f"❌ {error}")
            self.stats["errors"].append(error)

    def rebuild_index(self):
        """Rebuild search index"""
        print(f"\n🔨 Rebuilding search index...")

        index_builder = BASE_DIR / "rag_finetune/scripts/build_concept_index.py"

        if not index_builder.exists():
            print("⚠️  Index builder not found, skipping rebuild")
            print(f"   Run manually: python3 {index_builder}")
            return

        import subprocess
        try:
            result = subprocess.run(
                ["python3", str(index_builder)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("✓ Index rebuilt successfully")
            else:
                print(f"⚠️  Index rebuild failed:")
                print(result.stderr)

        except subprocess.TimeoutExpired:
            print("⚠️  Index rebuild timed out (>5 min)")
        except Exception as e:
            print(f"⚠️  Error rebuilding index: {e}")

    def integrate(self):
        """Run full integration pipeline"""
        print(f"\n{'='*80}")
        print(f"Batch Integration")
        print(f"{'='*80}")
        print(f"Source: {self.source_dir}")
        print(f"Book: {self.metadata.get('title', 'Unknown')}")
        print(f"Concepts: {self.metadata.get('concepts_extracted', 0)}")
        print(f"{'='*80}\n")

        # Copy concepts
        self.copy_concepts()

        # Update config
        self.update_book_config()

        # Rebuild index
        self.rebuild_index()

        # Summary
        print(f"\n{'='*80}")
        print(f"✅ Integration Complete!")
        print(f"{'='*80}")
        print(f"Concepts copied: {self.stats['concepts_copied']}")
        print(f"Concepts skipped: {self.stats['concepts_skipped']}")
        print(f"Book configured: {'Yes' if self.stats['book_configured'] else 'Already configured'}")
        print(f"Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in self.stats['errors']:
                print(f"  - {error}")

        print(f"\nNext steps:")
        print(f"1. Test search: cppfind \"topic from {self.metadata.get('title')}\"")
        print(f"2. Verify book display in results")
        print(f"3. Check concept quality")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_integrate.py <source_directory>")
        print("Example: python3 batch_integrate.py factory/output/my_book/")
        sys.exit(1)

    source_dir = Path(sys.argv[1])

    if not source_dir.exists():
        print(f"Error: Directory not found: {source_dir}")
        sys.exit(1)

    if not source_dir.is_dir():
        print(f"Error: Not a directory: {source_dir}")
        sys.exit(1)

    integrator = BatchIntegrator(source_dir)
    integrator.integrate()


if __name__ == "__main__":
    main()
