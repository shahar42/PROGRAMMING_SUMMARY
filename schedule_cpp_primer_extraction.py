#!/usr/bin/env python3
"""
C++ Primer Extraction Scheduler
Runs extraction every 13 minutes until PDF is complete

Features:
- Automatic extraction every 13 minutes
- Progress tracking
- Estimated completion time
- Graceful shutdown on Ctrl+C
- Logging
"""

import time
import subprocess
import signal
import sys
from datetime import datetime, timedelta
import json
from pathlib import Path

class CppPrimerScheduler:
    def __init__(self):
        self.is_running = True
        self.extraction_script = "books/extract_cpp_primer.py"
        self.progress_file = Path("outputs/cpp_primer/progress.json")
        self.total_pages = 1282
        self.interval_minutes = 13
        self.max_concepts_per_session = 17
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🔄 C++ Primer Extraction Scheduler Started")
        print(f"📚 Total pages to process: {self.total_pages}")
        print(f"⏰ Extraction interval: {self.interval_minutes} minutes")
        print(f"📄 Max concepts per session: {self.max_concepts_per_session}")
        print(f"🛑 Press Ctrl+C to stop gracefully")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
        self.is_running = False
        
    def get_current_progress(self):
        """Get current extraction progress"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                return {
                    "last_page": progress.get("last_processed_page", 0),
                    "total_concepts": progress.get("total_concepts_extracted", 0)
                }
            else:
                return {"last_page": 0, "total_concepts": 0}
        except Exception as e:
            print(f"⚠️  Error reading progress: {e}")
            return {"last_page": 0, "total_concepts": 0}
    
    def calculate_stats(self, progress):
        """Calculate extraction statistics"""
        pages_processed = progress["last_page"]
        concepts_extracted = progress["total_concepts"]
        pages_remaining = self.total_pages - pages_processed
        
        # Calculate ratios
        if pages_processed > 0:
            concepts_per_page = concepts_extracted / pages_processed
            pages_per_concept = pages_processed / concepts_extracted if concepts_extracted > 0 else 0
        else:
            concepts_per_page = 0
            pages_per_concept = 0
            
        # Estimate completion
        if concepts_per_page > 0:
            estimated_sessions_remaining = pages_remaining / 40  # 40 pages per session
            estimated_time_remaining = estimated_sessions_remaining * self.interval_minutes
            completion_time = datetime.now() + timedelta(minutes=estimated_time_remaining)
        else:
            completion_time = None
            estimated_time_remaining = 0
            
        return {
            "pages_processed": pages_processed,
            "pages_remaining": pages_remaining,
            "progress_percentage": (pages_processed / self.total_pages) * 100,
            "concepts_extracted": concepts_extracted,
            "concepts_per_page": concepts_per_page,
            "pages_per_concept": pages_per_concept,
            "estimated_completion": completion_time,
            "estimated_minutes_remaining": estimated_time_remaining
        }
    
    def run_extraction(self):
        """Run a single extraction session"""
        print(f"\n🚀 Starting extraction session at {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # Run the extraction script
            result = subprocess.run(
                ["python", self.extraction_script],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Extraction session completed successfully")
                # Show last few lines of output
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
                return True
            else:
                print("❌ Extraction session failed")
                print(f"   Error: {result.stderr[-200:]}")  # Last 200 chars of error
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Extraction session timed out (10 minutes)")
            return False
        except Exception as e:
            print(f"❌ Error running extraction: {e}")
            return False
    
    def print_status(self, stats):
        """Print current status"""
        print(f"\n📊 C++ Primer Extraction Status")
        print(f"={'='*50}")
        print(f"📄 Pages processed: {stats['pages_processed']}/{self.total_pages} ({stats['progress_percentage']:.1f}%)")
        print(f"📚 Concepts extracted: {stats['concepts_extracted']}")
        print(f"📊 Ratio: {stats['concepts_per_page']:.3f} concepts/page")
        print(f"📊 Ratio: {stats['pages_per_concept']:.1f} pages/concept")
        
        if stats['estimated_completion']:
            print(f"⏱️  Estimated completion: {stats['estimated_completion'].strftime('%Y-%m-%d %H:%M')}")
            print(f"⏳ Time remaining: {stats['estimated_minutes_remaining']:.0f} minutes ({stats['estimated_minutes_remaining']/60:.1f} hours)")
        
        print(f"⏰ Next extraction: {(datetime.now() + timedelta(minutes=self.interval_minutes)).strftime('%H:%M:%S')}")
        print(f"={'='*50}")
    
    def is_complete(self, progress):
        """Check if extraction is complete"""
        return progress["last_page"] >= self.total_pages
    
    def run(self):
        """Main scheduler loop"""
        session_count = 0
        
        while self.is_running:
            session_count += 1
            print(f"\n🔄 Session #{session_count}")
            
            # Get current progress
            progress = self.get_current_progress()
            stats = self.calculate_stats(progress)
            
            # Check if complete
            if self.is_complete(progress):
                print("\n🎉 Extraction complete! All pages processed.")
                break
            
            # Print status
            self.print_status(stats)
            
            # Run extraction
            success = self.run_extraction()
            
            if not success:
                print("⚠️  Session failed, will retry next cycle")
            
            # Wait for next cycle
            if self.is_running:
                print(f"\n💤 Waiting {self.interval_minutes} minutes until next extraction...")
                
                for i in range(self.interval_minutes * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
                    # Show countdown every minute
                    if i % 60 == 0:
                        minutes_left = self.interval_minutes - (i // 60)
                        if minutes_left > 0:
                            print(f"   ⏳ {minutes_left} minutes remaining...")
        
        print("\n👋 Scheduler stopped. Goodbye!")

def main():
    """Main function"""
    scheduler = CppPrimerScheduler()
    
    # Show initial status
    progress = scheduler.get_current_progress()
    stats = scheduler.calculate_stats(progress)
    scheduler.print_status(stats)
    
    # Check if already complete
    if scheduler.is_complete(progress):
        print("\n🎉 Extraction already complete!")
        return
        
    # Start scheduling
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()