#!/usr/bin/env python3
"""
STL Extraction Control Script
Simple interface to start, stop, and monitor the automated extraction
"""

import sys
import os
import json
import subprocess
import signal
from datetime import datetime

def get_status():
    """Get current extraction status"""
    progress_file = "cpp_stl_progress.json"
    
    if not os.path.exists(progress_file):
        print("❌ Progress file not found")
        return
    
    try:
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        print("📊 C++ STL EXTRACTION STATUS")
        print("=" * 40)
        
        start_page = progress.get('start_page', 37)
        end_page = progress.get('end_page', 407)
        current_page = progress.get('current_page', 37)
        total_concepts = progress.get('total_concepts_extracted', 0)
        current_batch = progress.get('current_batch', 1)
        
        total_pages = end_page - start_page + 1
        pages_done = current_page - start_page
        percent_complete = (pages_done / total_pages) * 100
        
        print(f"📖 Book: C++ Standard LibraryContainers.pdf")
        print(f"📄 Pages: {current_page}/{end_page} ({percent_complete:.1f}% complete)")
        print(f"🎯 Concepts extracted: {total_concepts}")
        print(f"📦 Current batch: {current_batch}")
        print(f"📅 Last updated: {progress.get('last_updated', 'Unknown')}")
        print(f"🔄 Status: {progress.get('status', 'Unknown')}")
        
        if progress.get('status') == 'completed':
            print("🎉 EXTRACTION COMPLETED!")
        else:
            estimated_batches_left = (end_page - current_page) // progress.get('concepts_per_batch', 20)
            estimated_time = estimated_batches_left * 20  # minutes
            print(f"⏰ Estimated time remaining: ~{estimated_time} minutes ({estimated_batches_left} batches)")
        
    except Exception as e:
        print(f"❌ Error reading status: {e}")

def start_extraction():
    """Start the automated extraction"""
    print("🚀 Starting automated STL extraction...")
    print("⏰ Will run every 20 minutes until completion")
    print("🛑 Press Ctrl+C to stop gracefully")
    print("")
    
    try:
        # Run the automated extraction script
        subprocess.run(["python3", "automated_stl_extraction.py"])
    except KeyboardInterrupt:
        print("\n🛑 Extraction stopped by user")
    except Exception as e:
        print(f"❌ Error starting extraction: {e}")

def reset_progress():
    """Reset progress to start from page 37"""
    progress_file = "cpp_stl_progress.json"
    
    confirm = input("⚠️  Reset progress to page 37? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Reset cancelled")
        return
    
    progress = {
        "book_name": "C++ Standard LibraryContainers.pdf",
        "book_identifier": "cpp_stl_containers",
        "start_page": 37,
        "end_page": 407,
        "current_page": 37,
        "total_pages_to_process": 370,
        "concepts_per_batch": 20,
        "completed_pages": [],
        "current_batch": 1,
        "total_concepts_extracted": 0,
        "last_updated": datetime.now().isoformat(),
        "status": "ready",
        "processor_used": "cpp_stl_processor"
    }
    
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        print("✅ Progress reset to page 37")
    except Exception as e:
        print(f"❌ Error resetting progress: {e}")

def show_logs():
    """Show recent extraction logs"""
    log_file = "cpp_stl_extraction.log"
    
    if not os.path.exists(log_file):
        print("❌ Log file not found")
        return
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Show last 20 lines
        print("📋 RECENT LOGS (last 20 lines)")
        print("=" * 50)
        for line in lines[-20:]:
            print(line.strip())
            
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

def show_help():
    """Show help information"""
    print("🔧 STL EXTRACTION CONTROL")
    print("=" * 30)
    print("Commands:")
    print("  status    - Show current extraction progress")
    print("  start     - Start automated extraction (20-min intervals)")
    print("  logs      - Show recent extraction logs")
    print("  reset     - Reset progress to page 37")
    print("  help      - Show this help")
    print("")
    print("Files:")
    print("  cpp_stl_progress.json     - Progress tracking")
    print("  cpp_stl_extraction.log    - Extraction logs")
    print("  outputs/cpp_stl_containers/ - Generated concepts")

def main():
    """Main control interface"""
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        get_status()
    elif command == "start":
        start_extraction()
    elif command == "logs":
        show_logs()
    elif command == "reset":
        reset_progress()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python3 stl_control.py help' for available commands")

if __name__ == "__main__":
    main()