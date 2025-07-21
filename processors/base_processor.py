#!/usr/bin/env python3
"""
Base Atomic Processor - Provides deduplication functionality to all processors
This is the parent class that adds duplicate detection to existing processors
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from processors.concept_memory import ConceptMemoryManager

class BaseAtomicProcessor:
    """
    Base class that provides deduplication functionality to all AI processors
    
    This class should be inherited by:
    - GeminiAtomicProcessor
    - GrokAtomicProcessor  
    - GPT4NanoAtomicProcessor
    """
    
    def __init__(self, project_root=PROJECT_ROOT):
        self.project_root = Path(project_root)
        
        # Initialize concept memory manager (shared across all processors)
        print("🧠 Initializing concept memory for duplicate detection...")
        self.memory = ConceptMemoryManager(project_root)
        
        # Track statistics
        self.stats = {
            'concepts_processed': 0,
            'duplicates_prevented': 0,
            'concepts_merged': 0,
            'concepts_created': 0
        }
    
    def process_concept_with_deduplication(self, concept_data, book_name):
        """
        Main processing method that includes deduplication
        
        This method should be called INSTEAD of the original process_concept method
        
        Args:
            concept_data: Raw concept data from extractor
            book_name: Name of the book (e.g., "expert_c_programming")
        
        Returns:
            dict: Processed concept ready for saving, or None if duplicate rejected
        """
        
        self.stats['concepts_processed'] += 1
        
        print(f"\n🔄 Processing concept with deduplication...")
        print(f"📖 Book: {book_name}")
        
        # Step 1: Use AI to extract concept (call child class method)
        print("🤖 Extracting concept using AI...")
        ai_extracted_concept = self._extract_with_ai(concept_data)
        
        if not ai_extracted_concept:
            print("❌ AI extraction failed")
            return None
        
        print(f"✅ AI extracted: {ai_extracted_concept.get('topic', 'Unknown Topic')}")
        
        # Step 2: Check for duplicates
        print("🔍 Checking for duplicates...")
        is_duplicate, similar_concepts, similarity_scores = self.memory.check_for_duplicates(ai_extracted_concept)
        
        if is_duplicate:
            # It's a clear duplicate - decide whether to merge or skip
            print("🚨 DUPLICATE DETECTED!")
            
            action = self._decide_duplicate_action(ai_extracted_concept, similar_concepts[0])
            
            if action == "skip":
                print("⏭️  Skipping duplicate concept")
                self.stats['duplicates_prevented'] += 1
                return None
            
            elif action == "merge":
                print("🔄 Merging with existing concept...")
                merged_concept, existing_file_path = self.memory.merge_concepts(ai_extracted_concept, similar_concepts)
                
                # Save merged concept over existing file
                self._save_merged_concept(merged_concept, existing_file_path)
                self.stats['concepts_merged'] += 1
                
                print(f"✅ Merged concept saved to: {existing_file_path}")
                return merged_concept
        
        elif similar_concepts:
            # Similar but not duplicate - prompt for decision
            print(f"⚠️  Found similar concept (similarity: {similarity_scores[0]:.2f})")
            print("🤔 Creating new concept since similarity is below duplicate threshold")
        
        # Step 3: Create new concept
        print("✨ Creating new concept...")
        
        # Add to memory before saving
        output_dir = self.project_root / "outputs" / book_name
        concept_filename = self._generate_concept_filename(ai_extracted_concept, output_dir)
        concept_file_path = output_dir / concept_filename
        
        # Save new concept
        self._save_new_concept(ai_extracted_concept, concept_file_path)
        
        # Add to memory
        self.memory.add_concept_to_memory(ai_extracted_concept, concept_file_path, book_name)
        
        self.stats['concepts_created'] += 1
        print(f"✅ New concept saved to: {concept_file_path}")
        
        return ai_extracted_concept
    
    def _extract_with_ai(self, concept_data):
        """
        This method should be overridden by child classes
        (GeminiAtomicProcessor, GrokAtomicProcessor, etc.)
        """
        raise NotImplementedError("Child classes must implement _extract_with_ai method")
    
    def _decide_duplicate_action(self, new_concept, similar_concept):
        """
        Decide what to do with a duplicate concept
        
        Returns:
            "skip" - Don't create the concept
            "merge" - Merge with existing concept
            "create" - Create anyway (for edge cases)
        """
        
        # For now, always merge duplicates
        # In the future, we could add more sophisticated logic
        similarity_score = similar_concept['similarity_score']
        
        if similarity_score > 0.95:
            # Almost identical - skip
            return "skip"
        elif similarity_score > 0.85:
            # Very similar - merge
            return "merge"
        else:
            # Shouldn't happen (duplicate threshold is 0.85), but create new anyway
            return "create"
    
    def _generate_concept_filename(self, concept_data, output_dir):
        """Generate filename for new concept"""
        
        # Get existing concept count for numbering
        existing_files = list(output_dir.glob("*concept_*.json"))
        next_number = len(existing_files) + 1
        
        # Generate clean filename from topic
        topic = concept_data.get('topic', 'unknown_concept')
        clean_topic = topic.lower().replace(' ', '_').replace('-', '_')
        
        # Remove special characters
        import re
        clean_topic = re.sub(r'[^a-z0-9_]', '', clean_topic)
        
        # Limit length
        if len(clean_topic) > 30:
            clean_topic = clean_topic[:30]
        
        filename = f"concept_{next_number:03d}_{clean_topic}.json"
        return filename
    
    def _save_new_concept(self, concept_data, file_path):
        """Save new concept to file"""
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save concept
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(concept_data, f, indent=2, ensure_ascii=False)
    
    def _save_merged_concept(self, merged_concept, existing_file_path):
        """Save merged concept over existing file"""
        
        # Backup original file
        backup_path = str(existing_file_path) + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        import shutil
        shutil.copy2(existing_file_path, backup_path)
        print(f"  💾 Backed up original to: {backup_path}")
        
        # Save merged concept
        with open(existing_file_path, 'w', encoding='utf-8') as f:
            json.dump(merged_concept, f, indent=2, ensure_ascii=False)
    
    def print_stats(self):
        """Print processing statistics"""
        print("\n📊 Processing Statistics:")
        print(f"  📝 Concepts processed: {self.stats['concepts_processed']}")
        print(f"  ✨ New concepts created: {self.stats['concepts_created']}")
        print(f"  🔄 Concepts merged: {self.stats['concepts_merged']}")
        print(f"  🚨 Duplicates prevented: {self.stats['duplicates_prevented']}")
        
        if self.stats['concepts_processed'] > 0:
            efficiency = (self.stats['duplicates_prevented'] + self.stats['concepts_merged']) / self.stats['concepts_processed'] * 100
            print(f"  🎯 Deduplication efficiency: {efficiency:.1f}%")
