#!/usr/bin/env python3
"""
Operating Systems Concept Extraction Engine
Content-Intelligent extraction for Operating Systems: Three Easy Pieces

Archaeologically extracts atomic OS concepts from the Three Easy Pieces book
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
from core.concept_detector import ConceptBoundaryDetector
from processors.grok_processor import GrokAtomicProcessor


class OSExtractionEngine:
    """Main orchestrator for Operating Systems concept extraction"""
    
    def __init__(self, pdf_path, output_dir, config_file="config/config.env"):
        load_dotenv(config_file)
        
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create progress tracker with book-specific path
        progress_file = self.output_dir / "progress.json"
        
        # Verify API key is loaded
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            print(f"❌ GROK_API_KEY not found in {config_file}")
            print(f"📝 Please ensure config.env contains: GROK_API_KEY=your_actual_api_key")
            raise ValueError("Missing GROK_API_KEY")
        
        print(f"✅ Grok API key loaded successfully (length: {len(api_key)} chars)")
        
        # Initialize components
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.processor = GrokAtomicProcessor(api_key)
        
        print(f"🏛️  Operating Systems Archaeological Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts extracted")
    
    def run_extraction_session(self, max_concepts=4):
        """Run one extraction session with daily summary generation"""
        session_start = datetime.now()
        print(f"\n🔍 Starting Operating Systems extraction session...")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []  # Track what we extracted for summary
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            # Extract structured content
            print(f"📖 Extracting OS content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=15)
            
            if not content_blocks:
                print("🏁 No more content found. OS extraction complete!")
                self._generate_completion_summary(session_start)
                return False
            
            # Detect atomic concept boundaries
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential OS atomic concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing OS concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Update metadata for OS book
                concept["source_title"] = "Operating Systems - Three Easy Pieces"
                
                # Generate atomic training data
                processed_concept = self.processor.process_concept(concept)
                
                if processed_concept:
                    # Update source in metadata
                    processed_concept["extraction_metadata"]["source"] = "Operating Systems - Three Easy Pieces"
                    
                    # Save concept
                    filename = self._save_concept(processed_concept, concepts_extracted)
                    concepts_extracted += 1
                    
                    # Track for summary
                    extracted_concepts.append({
                        "topic": processed_concept.get('topic', 'Unknown'),
                        "explanation": processed_concept.get('explanation', 'No explanation available'),
                        "filename": filename,
                        "page_range": processed_concept["extraction_metadata"]["page_range"]
                    })
                    
                    print(f"✅ Saved OS concept: {processed_concept.get('topic', 'Unknown')}")
                else:
                    print(f"❌ Failed to process OS concept")
        
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
        
        print(f"\n📊 OS session complete: {concepts_extracted} atomic concepts extracted")
        print(f"📈 Total OS progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
        
        return concepts_extracted > 0
    
    def _save_concept(self, concept, concept_number):
        """Save atomic concept to JSON file"""
        filename = f"os_concept_{self.progress_tracker.progress['total_concepts_extracted'] + concept_number + 1:03d}_{self._safe_filename(concept.get('topic', 'unknown'))}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)
        
        return filename
    
    def _generate_daily_summary(self, session_start, extracted_concepts, session_info):
        """Generate daily summary report"""
        session_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"os_daily_summary_{session_date}.md"
        summary_path = self.output_dir / summary_filename
        
        duration = datetime.now() - session_start
        
        summary_content = f"""# Daily Operating Systems Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {duration.total_seconds():.1f} seconds
**Page Range:** {session_info['page_range']}
**Book:** Operating Systems - Three Easy Pieces

## OS Concepts Extracted Today: {len(extracted_concepts)}

"""
        
        for i, concept in enumerate(extracted_concepts, 1):
            summary_content += f"""### {i}. {concept['topic']}
**What it's about:** {concept['explanation'][:200]}{'...' if len(concept['explanation']) > 200 else ''}

- **File:** `{concept['filename']}`
- **Pages:** {concept['page_range']}

"""
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        summary_content += f"""## OS Progress Summary
- **Total OS Concepts Extracted:** {total_concepts}
- **Extraction Sessions Completed:** {len(self.progress_tracker.progress['extraction_sessions'])}
- **Last Processed Page:** {self.progress_tracker.progress['last_processed_page']}

## Next Session
Run the OS extraction script again tomorrow to continue processing.

---
*Generated by OS Archaeological Extraction Engine*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 OS daily summary saved: {summary_filename}")
    
    def _generate_completion_summary(self, session_start):
        """Generate final completion summary"""
        completion_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"os_extraction_complete_{completion_date}.md"
        summary_path = self.output_dir / summary_filename
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        total_sessions = len(self.progress_tracker.progress['extraction_sessions'])
        
        summary_content = f"""# 🎉 Operating Systems Book Extraction Complete!

**Completion Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}

## Final Statistics
- **Total OS Atomic Concepts Extracted:** {total_concepts}
- **Total Extraction Sessions:** {total_sessions}
- **Total Pages Processed:** {self.progress_tracker.progress['last_processed_page']}

## All Extracted OS Concepts
Your complete Operating Systems training dataset is now ready in the `outputs/os_three_pieces/` directory.

Each concept follows the atomic structure:
- ✅ Concept Definition
- ✅ Syntax Pattern  
- ✅ Compilable Example
- ✅ Example Explanation

---
*Archaeological excavation of "Operating Systems - Three Easy Pieces" complete!*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"🏆 OS completion summary saved: {summary_filename}")
    
    def _safe_filename(self, topic):
        """Create safe filename from topic"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:30]


def main():
    """Main execution for Operating Systems extraction"""
    # Configuration
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/Operating Systems - Three Easy Pieces.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/os_three_pieces"
    
    # Verify files exist
    if not os.path.exists(pdf_path):
        print(f"❌ OS PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found. Please create config/config.env with GROK_API_KEY=your_key")
        return
    
    # Initialize and run extraction engine
    engine = OSExtractionEngine(pdf_path, output_dir)
    
    # Run extraction session
    continue_extraction = engine.run_extraction_session(max_concepts=4)
    
    if not continue_extraction:
        print("\n🎉 Operating Systems book extraction complete! All atomic concepts have been archaeologically excavated.")
    else:
        print(f"\n⏳ Run OS script again tomorrow to continue extraction...")


if __name__ == "__main__":
    main()
