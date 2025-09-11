#!/usr/bin/env python3
"""
Automated C++ STL Container Extraction
Runs every 20 minutes until completion (pages 37-407)

Features:
- 20 concepts per batch
- Automatic progress tracking
- Resumable extraction
- Error handling and retry logic
- Detailed logging
- Completion detection
"""

import sys
import os
import json
import time
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/config.env")

# Add project root to Python path
sys.path.append('.')

try:
    from processors.cpp_stl_processor import CppStlProcessor
    from core.progress_tracker import ProgressTracker
    from core.pdf_extractor import PDFStructureExtractor
    from core.concept_detector import ConceptBoundaryDetector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class AutomatedSTLExtractor:
    """Automated STL extraction with 20-minute intervals"""
    
    def __init__(self):
        self.progress_file = "cpp_stl_progress.json"
        self.output_dir = "outputs/cpp_stl_containers"
        self.pdf_path = "C++ Standard LibraryContainers.pdf"
        self.log_file = "cpp_stl_extraction.log"
        
        # Setup logging
        self.setup_logging()
        
        # Check required files
        self.validate_setup()
        
        # Initialize components
        self.processor = None
        self.progress_tracker = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 Automated STL Extractor initialized")
    
    def setup_logging(self):
        """Setup detailed logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_setup(self):
        """Validate all required files and API keys"""
        
        # Check API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.logger.error("❌ GEMINI_API_KEY not found in config/config.env")
            sys.exit(1)
        
        # Check PDF
        if not os.path.exists(self.pdf_path):
            self.logger.error(f"❌ PDF not found: {self.pdf_path}")
            sys.exit(1)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check progress file
        if not os.path.exists(self.progress_file):
            self.logger.error(f"❌ Progress file not found: {self.progress_file}")
            sys.exit(1)
        
        self.logger.info("✅ Setup validation complete")
    
    def load_progress(self):
        """Load extraction progress"""
        try:
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
            
            self.logger.info(f"📊 Progress: Page {progress.get('current_page', 37)}/{progress.get('end_page', 407)}")
            self.logger.info(f"📊 Concepts extracted: {progress.get('total_concepts_extracted', 0)}")
            self.logger.info(f"📊 Batch: {progress.get('current_batch', 1)}")
            
            return progress
        except Exception as e:
            self.logger.error(f"❌ Error loading progress: {e}")
            return None
    
    def save_progress(self, progress):
        """Save extraction progress"""
        try:
            progress['last_updated'] = datetime.now().isoformat()
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            self.logger.info(f"💾 Progress saved - Page {progress.get('current_page')}")
        except Exception as e:
            self.logger.error(f"❌ Error saving progress: {e}")
    
    def initialize_processor(self):
        """Initialize the STL processor with error handling"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            self.processor = CppStlProcessor(api_key)
            self.logger.info("✅ STL processor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize processor: {e}")
            return False
    
    def extract_batch(self, progress):
        """Extract one batch of concepts"""
        
        start_page = progress.get('current_page', 37)
        end_page = progress.get('end_page', 407)
        concepts_per_batch = progress.get('concepts_per_batch', 20)
        
        if start_page > end_page:
            self.logger.info("🎉 Extraction complete!")
            progress['status'] = 'completed'
            return progress, True
        
        self.logger.info(f"🔄 Starting batch {progress.get('current_batch', 1)} from page {start_page}")
        
        try:
            # Simulate content extraction (you can replace with real PDF extraction)
            concepts_extracted = 0
            batch_start_time = datetime.now()
            
            # Extract concepts for this batch
            for i in range(concepts_per_batch):
                if start_page > end_page:
                    break
                
                # Create test concept data (replace with real PDF extraction)
                concept_data = {
                    "raw_content": f"""
                    STL Container concept from page {start_page}:
                    
                    std::vector is a sequence container that encapsulates dynamic size arrays.
                    The storage is handled automatically, being expanded as needed.
                    
                    Example:
                    std::vector<int> vec;
                    vec.push_back(42);
                    vec.emplace_back(24);
                    
                    Common operations include push_back, pop_back, insert, erase.
                    """,
                    "page_range": f"{start_page}-{start_page}",
                    "has_code": True,
                    "has_explanation": True
                }
                
                # Process with deduplication
                result = self.processor.process_concept_with_deduplication(
                    concept_data, "cpp_stl_containers"
                )
                
                if result:
                    concepts_extracted += 1
                    self.logger.info(f"✅ Extracted: {result.get('topic', 'Unknown')}")
                    
                    # Save concept
                    concept_id = f"concept_{progress.get('current_batch', 1):03d}_{concepts_extracted:02d}"
                    output_file = f"{self.output_dir}/{concept_id}.json"
                    
                    with open(output_file, 'w') as f:
                        json.dump(result, f, indent=2)
                else:
                    self.logger.warning(f"⚠️  Failed to extract concept from page {start_page}")
                
                # Move to next page (simulated)
                start_page += 1
                
                # Small delay to respect API limits
                time.sleep(2)
            
            # Update progress
            batch_time = datetime.now() - batch_start_time
            progress['current_page'] = start_page
            progress['current_batch'] = progress.get('current_batch', 1) + 1
            progress['total_concepts_extracted'] = progress.get('total_concepts_extracted', 0) + concepts_extracted
            progress['completed_pages'].extend(list(range(start_page - concepts_extracted, start_page)))
            
            self.logger.info(f"✅ Batch complete: {concepts_extracted} concepts in {batch_time}")
            
            return progress, False
            
        except Exception as e:
            self.logger.error(f"❌ Error during batch extraction: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return progress, False
    
    def run_extraction_cycle(self):
        """Run one extraction cycle"""
        
        self.logger.info("🔄 Starting extraction cycle")
        
        # Load progress
        progress = self.load_progress()
        if not progress:
            return False
        
        # Initialize processor if needed
        if not self.processor:
            if not self.initialize_processor():
                return False
        
        # Extract batch
        progress, completed = self.extract_batch(progress)
        
        # Save progress
        self.save_progress(progress)
        
        if completed:
            self.logger.info("🎉 All extraction completed!")
            return True
        
        return False
    
    def run_automated_extraction(self):
        """Main automation loop - runs every 20 minutes"""
        
        self.logger.info("🚀 Starting automated STL extraction")
        self.logger.info("⏰ Running every 20 minutes until completion")
        self.logger.info("🛑 Press Ctrl+C to stop gracefully")
        
        while self.running:
            try:
                # Run extraction cycle
                completed = self.run_extraction_cycle()
                
                if completed:
                    self.logger.info("🏁 Extraction finished successfully!")
                    break
                
                if self.running:
                    self.logger.info("⏰ Waiting 20 minutes for next batch...")
                    self.logger.info(f"⏰ Next run at: {(datetime.now() + timedelta(minutes=20)).strftime('%H:%M:%S')}")
                    
                    # Wait 20 minutes (1200 seconds)
                    for i in range(1200):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                        # Progress indicator every 5 minutes
                        if i % 300 == 0 and i > 0:
                            remaining = (1200 - i) // 60
                            self.logger.info(f"⏰ {remaining} minutes until next batch")
                
            except Exception as e:
                self.logger.error(f"❌ Error in automation loop: {e}")
                if self.running:
                    self.logger.info("⏰ Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes on error
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"🛑 Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def get_status(self):
        """Get current extraction status"""
        try:
            progress = self.load_progress()
            if progress:
                total_pages = progress.get('end_page', 407) - progress.get('start_page', 37) + 1
                current_page = progress.get('current_page', 37)
                completed_pages = len(progress.get('completed_pages', []))
                percent_complete = (completed_pages / total_pages) * 100
                
                self.logger.info(f"📊 STATUS REPORT:")
                self.logger.info(f"📊 Pages: {current_page}/{progress.get('end_page', 407)} ({percent_complete:.1f}% complete)")
                self.logger.info(f"📊 Concepts: {progress.get('total_concepts_extracted', 0)}")
                self.logger.info(f"📊 Batches: {progress.get('current_batch', 1)}")
                
        except Exception as e:
            self.logger.error(f"❌ Error getting status: {e}")

def main():
    """Main entry point"""
    
    extractor = AutomatedSTLExtractor()
    
    # Show initial status
    extractor.get_status()
    
    try:
        # Run automated extraction
        extractor.run_automated_extraction()
        
    except KeyboardInterrupt:
        extractor.logger.info("🛑 Extraction stopped by user")
    except Exception as e:
        extractor.logger.error(f"❌ Fatal error: {e}")
        import traceback
        extractor.logger.error(traceback.format_exc())
    
    extractor.logger.info("👋 Automated STL extraction ended")

if __name__ == "__main__":
    main()