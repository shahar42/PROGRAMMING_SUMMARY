#!/usr/bin/env python3
"""
Expert C Programming Concept Extraction Engine
Content-Intelligent extraction for Expert C Programming: Deep C Secrets

Archaeologically extracts advanced C programming concepts from Expert C Programming book
"""

import sys
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Add project root to Python path for module imports  
sys.path.append('.')

# Import modular components
from core.progress_tracker import ProgressTracker
from core.pdf_extractor import PDFStructureExtractor
from processors.gpt4_nano_processor import GPT4NanoAtomicProcessor
# Semantic Deduplication Module
from semantic_deduplication import SemanticDeduplicator


class ExpertCConceptDetector:
    """Specialized concept detector for Expert C Programming book only"""
    
    def detect_atomic_concepts(self, content_blocks):
        """Group content blocks into atomic concepts - Expert C specific logic"""
        concepts = []
        current_concept = []
        
        for block in content_blocks:
            # Start new concept on headers
            if block["type"] == "header":
                if current_concept:
                    concepts.append(self._finalize_concept(current_concept))
                current_concept = [block]
            
            # Add to current concept
            else:
                current_concept.append(block)
                
                # Check if we have a complete atomic concept
                if self._is_complete_concept(current_concept):
                    concepts.append(self._finalize_concept(current_concept))
                    current_concept = []
        
        # Don't forget the last concept
        if current_concept:
            concepts.append(self._finalize_concept(current_concept))
        
        return concepts
    
    def _is_complete_concept(self, blocks):
        """Check if we have a complete atomic concept - Expert C specific"""
        has_explanation = any(b["type"] == "text" for b in blocks)
        has_code = any(b["type"] == "code" for b in blocks)
        
        # Calculate word count for substantial explanations
        total_words = 0
        for block in blocks:
            if block["type"] == "text":
                text = "\n".join(block["content"])
                total_words += len(text.split())
        
        # Expert C specific logic:
        # 1. Code examples (explanation + code) - traditional
        # 2. Substantial narrative concepts (150+ words) - for Expert C content
        # 3. Multiple blocks with good content
        return (
            (has_explanation and has_code) or                    # Code examples
            (has_explanation and total_words >= 150) or         # Narrative concepts
            len(blocks) > 3                                      # Substantial content
        )
    
    def _finalize_concept(self, blocks):
        """Convert block sequence into structured concept"""
        concept = {
            "blocks": blocks,
            "page_range": f"{blocks[0]['page']}-{blocks[-1]['page']}",
            "has_code": any(b["type"] == "code" for b in blocks),
            "has_explanation": any(b["type"] == "text" for b in blocks),
            "raw_content": self._extract_raw_content(blocks)
        }
        return concept
    
    def _extract_raw_content(self, blocks):
        """Extract clean text from blocks"""
        content = []
        for block in blocks:
            content.extend(block["content"])
        return "\n".join(content)


class ExpertCExtractionEngine:
    """Main orchestrator for Expert C Programming concept extraction"""
    
    def __init__(self, pdf_path, output_dir, config_file="config/config.env"):
        load_dotenv(config_file)
        
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create progress tracker with book-specific path
        progress_file = self.output_dir / "progress.json"
        
        # Verify API key is loaded
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print(f"❌ OPENAI_API_KEY not found in {config_file}")
            print(f"📝 Please ensure config.env contains: OPENAI_API_KEY=your_actual_api_key")
            raise ValueError("Missing OPENAI_API_KEY")
        
        print(f"✅ OpenAI API key loaded successfully (length: {len(api_key)} chars)")
        
        # Initialize components
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.processor = GPT4NanoAtomicProcessor(api_key)
        
        print(f"🏛️  Expert C Programming Archaeological Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts extracted")
    
    def run_extraction_session(self, max_concepts=4):
        """Run one extraction session with daily summary generation"""
        session_start = datetime.now()
        print(f"\n🔍 Starting Expert C Programming extraction session...")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []  # Track what we extracted for summary
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            # Extract structured content
            print(f"📖 Extracting Expert C content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=15)
            
            if not content_blocks:
                print("🏁 No more content found. Expert C Programming extraction complete!")
                self._generate_completion_summary(session_start)
                return False
            
            # Use Expert C specific concept detector
            detector = ExpertCConceptDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential Expert C atomic concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing Expert C concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Update metadata for Expert C Programming book
                concept["source_title"] = "Expert C Programming: Deep C Secrets"
                
                # Generate atomic training data
                processed_concept = self.processor.process_concept(concept, "expert_c_programming")
                
                if processed_concept:
                    # Update source in metadata
                    processed_concept["extraction_metadata"]["source"] = "Expert C Programming: Deep C Secrets"
                    
                    # Save concept
                    filename = self._save_concept(processed_concept, concepts_extracted)
                    
                    if filename:  # Only count if successfully saved (not duplicate)
                        concepts_extracted += 1
                        
                        # Track for summary
                        extracted_concepts.append({
                            "topic": processed_concept.get('topic', 'Unknown'),
                            "explanation": processed_concept.get('explanation', 'No explanation available'),
                            "filename": filename,
                            "page_range": processed_concept["extraction_metadata"]["page_range"]
                        })
                        
                        print(f"✅ Saved Expert C concept: {processed_concept.get('topic', 'Unknown')}")
                else:
                    print(f"❌ Failed to process Expert C concept")
        
        # Update progress
        last_page = max(block["page"] for concept in concepts for block in concept["blocks"])
        session_info = {"page_range": f"{start_page + 1}-{last_page}", "chapter": "Auto-detected"}
        
        self.progress_tracker.update_progress(
            last_page,
            concepts_extracted,
            session_info
        )
        
        # Generate daily summary
        self._generate_daily_summary(session_start, extracted_concepts, session_info)
        
        print(f"\n📊 Expert C session complete: {concepts_extracted} atomic concepts extracted")
        print(f"📈 Total Expert C progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
        
        return concepts_extracted > 0
    
    def _save_concept(self, concept, concept_number):
        """Save atomic concept to JSON file with deduplication check"""
        
        # Initialize deduplicator if not exists
        if not hasattr(self, '_deduplicator'):
            self._deduplicator = SemanticDeduplicator(
                output_dir=self.output_dir,
                similarity_threshold=0.80  # 80% similarity threshold
            )
            print(f"🛡️  Semantic deduplication enabled (threshold: 80%)")
        
        # Check for duplicates
        dup_result = self._deduplicator.check_for_duplicates(concept)
        
        if dup_result.is_duplicate:
            print(f"🔄 Skipping duplicate concept: {concept.get('topic', 'Unknown')[:50]}...")
            print(f"   💡 Similar to: {dup_result.existing_concept_file}")
            print(f"   📊 Similarity: {dup_result.similarity_score:.3f}")
            return None  # Skip saving duplicate
        
        # Original save logic
        filename = f"expert_c_concept_{self.progress_tracker.progress['total_concepts_extracted'] + concept_number + 1:03d}_{self._safe_filename(concept.get('topic', 'unknown'))}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)
        
        # Add to deduplicator cache for future comparisons
        self._deduplicator.add_concept_to_cache(concept, filename)
        print(f"✅ Saved unique concept: {concept.get('topic', 'Unknown')[:50]}...")
        
        return filename
    
    def _generate_daily_summary(self, session_start, extracted_concepts, session_info):
        """Generate daily summary report"""
        session_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"expert_c_daily_summary_{session_date}.md"
        summary_path = self.output_dir / summary_filename
        
        duration = datetime.now() - session_start
        
        summary_content = f"""# Daily Expert C Programming Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {duration.total_seconds():.1f} seconds
**Page Range:** {session_info['page_range']}
**Book:** Expert C Programming: Deep C Secrets

## Expert C Concepts Extracted Today: {len(extracted_concepts)}

"""
        
        for i, concept in enumerate(extracted_concepts, 1):
            summary_content += f"""### {i}. {concept['topic']}
**What it's about:** {concept['explanation'][:200]}{'...' if len(concept['explanation']) > 200 else ''}

- **File:** `{concept['filename']}`
- **Pages:** {concept['page_range']}

"""
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        summary_content += f"""## Expert C Progress Summary
- **Total Expert C Concepts Extracted:** {total_concepts}
- **Extraction Sessions Completed:** {len(self.progress_tracker.progress['extraction_sessions'])}
- **Last Processed Page:** {self.progress_tracker.progress['last_processed_page']}

## Next Session
Run the Expert C Programming extraction script again tomorrow to continue processing.

---
*Generated by Expert C Programming Archaeological Extraction Engine*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 Expert C daily summary saved: {summary_filename}")
    
    def _generate_completion_summary(self, session_start):
        """Generate final completion summary"""
        completion_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"expert_c_extraction_complete_{completion_date}.md"
        summary_path = self.output_dir / summary_filename
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        total_sessions = len(self.progress_tracker.progress['extraction_sessions'])
        
        summary_content = f"""# 🎉 Expert C Programming Book Extraction Complete!

**Completion Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}

## Final Statistics
- **Total Expert C Atomic Concepts Extracted:** {total_concepts}
- **Total Extraction Sessions:** {total_sessions}
- **Total Pages Processed:** {self.progress_tracker.progress['last_processed_page']}

## All Extracted Expert C Concepts
Your complete Expert C Programming training dataset is now ready in the `outputs/expert_c_programming/` directory.

Each concept follows the atomic structure:
- ✅ Concept Definition
- ✅ Syntax Pattern  
- ✅ Compilable Example
- ✅ Example Explanation

---
*Archaeological excavation of "Expert C Programming: Deep C Secrets" complete!*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"🏆 Expert C completion summary saved: {summary_filename}")
    
    def _safe_filename(self, topic):
        """Create safe filename from topic"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:30]


def main():
    """Main execution for Expert C Programming extraction"""
    # Configuration
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/Expert C Programming Deep C Secrets.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/expert_c_programming"
    
    # Verify files exist
    if not os.path.exists(pdf_path):
        print(f"❌ Expert C Programming PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found. Please create config/config.env with OPENAI_API_KEY=your_key")
        return
    
    # Initialize and run extraction engine
    engine = ExpertCExtractionEngine(pdf_path, output_dir)
    
    # Run extraction session
    continue_extraction = engine.run_extraction_session(max_concepts=4)
    
    if not continue_extraction:
        print("\n🎉 Expert C Programming book extraction complete! All atomic concepts have been archaeologically excavated.")
    else:
        print(f"\n⏳ Run Expert C script again tomorrow to continue extraction...")


if __name__ == "__main__":
    main()
