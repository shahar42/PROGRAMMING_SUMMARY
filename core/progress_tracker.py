#!/usr/bin/env python3
"""
Progress Tracker Core Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Tracks extraction progress for resumable operations across multiple books.
"""

import os
import json
from datetime import datetime


class ProgressTracker:
    """Tracks extraction progress for resumable operations"""
    
    def __init__(self, progress_file="progress.json"):
        self.progress_file = progress_file
        self.progress = self.load_progress()
    
    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Only parse if file has content
                        return json.loads(content)
                    else:
                        print("📝 Found empty progress file, initializing fresh...")
            except (json.JSONDecodeError, Exception) as e:
                print(f"📝 Progress file corrupted ({e}), initializing fresh...")
        
        # Return fresh progress structure
        return {
            "last_processed_page": 0,
            "total_concepts_extracted": 0,
            "extraction_sessions": [],
            "current_chapter": 1
        }
    
    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def update_progress(self, page_num, concepts_count, session_info):
        self.progress["last_processed_page"] = page_num
        self.progress["total_concepts_extracted"] += concepts_count
        self.progress["extraction_sessions"].append({
            "date": datetime.now().isoformat(),
            "concepts_extracted": concepts_count,
            "page_range": session_info.get("page_range", ""),
            "chapter": session_info.get("chapter", "")
        })
        self.save_progress()
