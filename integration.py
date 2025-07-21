#!/usr/bin/env python3
"""
Integration Patch for Expert C Programming Extraction Engine
Applies semantic deduplication to prevent redundant concept extraction

This script modifies the existing Expert C extraction engine to include
deduplication capabilities without breaking existing functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

def apply_deduplication_patch():
    """
    Apply the semantic deduplication patch to Expert C extraction engine
    """
    
    print("🔧 Applying Semantic Deduplication Patch to Expert C Extraction Engine")
    print("=" * 70)
    
    # Path to the Expert C extraction file
    extraction_file = PROJECT_ROOT / "books" / "extract_Expert_C_Programming.py"
    
    if not extraction_file.exists():
        print(f"❌ Expert C extraction file not found: {extraction_file}")
        return False
    
    # Read the current extraction file
    with open(extraction_file, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file = extraction_file.with_suffix('.py.backup')
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"📋 Backup created: {backup_file}")
    
    # Add deduplication import and integration
    dedup_import = '''
# Semantic Deduplication Module
from semantic_deduplication import SemanticDeduplicator
'''
    
    # Add deduplication logic to the _save_concept method
    # Find the ExpertCExtractionEngine class and modify its _save_concept method
    
    # Modified _save_concept method with deduplication
    new_save_concept_method = '''    def _save_concept(self, concept, concept_number):
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
        
        return filename'''
    
    # Apply the modifications
    modified_content = content
    
    # Add import at the top (after existing imports)
    import_position = modified_content.find('import json')
    if import_position != -1:
        # Find the end of imports section
        lines = modified_content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_end = i
        
        # Insert deduplication import
        lines.insert(import_end + 1, dedup_import.strip())
        modified_content = '\n'.join(lines)
    
    # Replace the _save_concept method
    # Find the method definition
    method_start = modified_content.find('    def _save_concept(self, concept, concept_number):')
    if method_start != -1:
        # Find the end of the method (next method or class definition)
        lines = modified_content[method_start:].split('\n')
        method_end_line = 1
        
        for i in range(1, len(lines)):
            line = lines[i]
            # End of method when we hit another method definition or class definition
            if (line.strip().startswith('def ') and not line.startswith('    ')) or \
               (line.strip().startswith('class ')) or \
               (line.strip() and not line.startswith('    ') and not line.startswith('\t')):
                method_end_line = i
                break
            # Also check for another method at same indentation level
            if line.strip().startswith('    def ') and line.count('    ') == 1:
                method_end_line = i
                break
        
        # Replace the method
        before_method = modified_content[:method_start]
        after_method = '\n'.join(lines[method_end_line:])
        
        modified_content = before_method + new_save_concept_method + '\n\n' + after_method
    
    # Write the modified file
    with open(extraction_file, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Deduplication patch applied to: {extraction_file}")
    
    # Create the semantic_deduplication.py file in the books directory
    semantic_dedup_file = PROJECT_ROOT / "books" / "semantic_deduplication.py"
    
    # Copy the deduplication module (this would be the content from the first artifact)
    dedup_module_content = '''"""
Semantic Deduplication Module for Expert C Programming Extraction Engine
Prevents redundant concept extraction by detecting semantically similar concepts
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
from difflib import SequenceMatcher
from dataclasses import dataclass

@dataclass
class SimilarityResult:
    """Result of similarity comparison between concepts"""
    is_duplicate: bool
    similarity_score: float
    existing_concept_file: str
    reason: str

class SemanticDeduplicator:
    """
    Semantic deduplication system for preventing redundant concept extraction
    """
    
    def __init__(self, output_dir: str, similarity_threshold: float = 0.80):
        """
        Initialize the deduplicator
        
        Args:
            output_dir: Directory containing existing concept JSON files
            similarity_threshold: Minimum similarity score to consider duplicate (0.0-1.0)
        """
        self.output_dir = Path(output_dir)
        self.similarity_threshold = similarity_threshold
        self.existing_concepts = self._load_existing_concepts()
    
    def _load_existing_concepts(self) -> List[Dict]:
        """Load all existing concept files for comparison"""
        concepts = []
        
        if not self.output_dir.exists():
            return concepts
            
        for json_file in self.output_dir.glob("expert_c_concept_*.json"):
            try:
                with open(json_file, 'r') as f:
                    concept = json.load(f)
                    concept['_source_file'] = json_file.name
                    concepts.append(concept)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not load {json_file}: {e}")
        
        if concepts:
            print(f"📚 Loaded {len(concepts)} existing concepts for deduplication")
        return concepts
    
    def check_for_duplicates(self, new_concept: Dict) -> SimilarityResult:
        """
        Check if new concept is a duplicate of existing concepts
        
        Args:
            new_concept: The concept to check for duplicates
            
        Returns:
            SimilarityResult indicating if it's a duplicate and details
        """
        if not self.existing_concepts:
            return SimilarityResult(False, 0.0, "", "No existing concepts to compare")
        
        best_match = None
        highest_score = 0.0
        
        for existing in self.existing_concepts:
            score = self._calculate_similarity(new_concept, existing)
            
            if score > highest_score:
                highest_score = score
                best_match = existing
        
        is_duplicate = highest_score >= self.similarity_threshold
        
        if is_duplicate:
            reason = f"Similar to existing concept (score: {highest_score:.3f})"
            return SimilarityResult(
                is_duplicate=True,
                similarity_score=highest_score,
                existing_concept_file=best_match['_source_file'],
                reason=reason
            )
        else:
            return SimilarityResult(
                is_duplicate=False,
                similarity_score=highest_score,
                existing_concept_file="",
                reason=f"No similar concepts found (highest score: {highest_score:.3f})"
            )
    
    def _calculate_similarity(self, concept1: Dict, concept2: Dict) -> float:
        """
        Calculate semantic similarity between two concepts
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Calculate weighted similarity scores
        topic_sim = self._text_similarity(
            concept1.get('topic', ''), 
            concept2.get('topic', '')
        )
        
        explanation_sim = self._text_similarity(
            concept1.get('explanation', ''), 
            concept2.get('explanation', '')
        )
        
        # Code similarity (if both have code examples)
        code_sim = 0.0
        if (concept1.get('code_example') and concept2.get('code_example')):
            code1 = '\\n'.join(concept1['code_example'])
            code2 = '\\n'.join(concept2['code_example'])
            code_sim = self._text_similarity(code1, code2)
        
        # Keyword overlap similarity
        text1 = self._extract_concept_text(concept1)
        text2 = self._extract_concept_text(concept2)
        keyword_sim = self._keyword_similarity(text1, text2)
        
        # Weighted final score
        final_score = (
            topic_sim * 0.35 +           # Topic similarity (35%)
            explanation_sim * 0.35 +     # Explanation similarity (35%)
            code_sim * 0.20 +            # Code similarity (20%)
            keyword_sim * 0.10           # Keyword overlap (10%)
        )
        
        return min(final_score, 1.0)  # Ensure max score is 1.0
    
    def _extract_concept_text(self, concept: Dict) -> str:
        """Extract all text content from a concept for analysis"""
        text_parts = []
        
        if concept.get('topic'):
            text_parts.append(concept['topic'])
        if concept.get('explanation'):
            text_parts.append(concept['explanation'])
        if concept.get('example_explanation'):
            text_parts.append(concept['example_explanation'])
        if concept.get('syntax'):
            text_parts.append(concept['syntax'])
            
        return ' '.join(text_parts).lower()
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1_norm = self._normalize_text(text1)
        text2_norm = self._normalize_text(text2)
        
        # Use SequenceMatcher for string similarity
        return SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better comparison"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\\s+', ' ', text)
        
        # Remove common programming punctuation that doesn't affect meaning
        text = re.sub(r'[(){}\\[\\];,.]', ' ', text)
        
        return text.strip()
    
    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on keyword overlap"""
        # Extract meaningful keywords (3+ characters, not common words)
        stopwords = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'can', 'use', 'used'}
        
        def extract_keywords(text):
            words = re.findall(r'\\b\\w{3,}\\b', text.lower())
            return set(word for word in words if word not in stopwords)
        
        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def add_concept_to_cache(self, concept: Dict, filename: str):
        """Add a new concept to the existing concepts cache"""
        concept_copy = concept.copy()
        concept_copy['_source_file'] = filename
        self.existing_concepts.append(concept_copy)
'''
    
    with open(semantic_dedup_file, 'w') as f:
        f.write(dedup_module_content)
    
    print(f"✅ Semantic deduplication module created: {semantic_dedup_file}")
    
    print("\n🎉 Deduplication patch successfully applied!")
    print("\nNext Steps:")
    print("1. Test the modified extraction engine")
    print("2. Run a few extraction cycles to verify deduplication works")
    print("3. Adjust similarity threshold if needed (currently 80%)")
    print(f"\n📁 Backup of original file: {backup_file}")
    
    return True

def test_deduplication():
    """Test the deduplication system with existing concepts"""
    
    print("\n🧪 Testing Deduplication System")
    print("=" * 40)
    
    output_dir = PROJECT_ROOT / "outputs" / "expert_c_programming"
    
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return False
    
    # Import the deduplication module
    sys.path.append(str(PROJECT_ROOT / "books"))
    from semantic_deduplication import SemanticDeduplicator
    
    deduplicator = SemanticDeduplicator(output_dir, similarity_threshold=0.80)
    
    print(f"📊 Loaded {len(deduplicator.existing_concepts)} concepts for testing")
    
    # Test with some example function pointer concepts
    function_pointer_files = [f for f in output_dir.glob("*function_pointer*")]
    
    if len(function_pointer_files) >= 2:
        print("\\n🔍 Testing similarity between function pointer concepts:")
        
        # Load two concepts
        with open(function_pointer_files[0], 'r') as f:
            concept1 = json.load(f)
        
        with open(function_pointer_files[1], 'r') as f:
            concept2 = json.load(f)
        
        # Test similarity
        score = deduplicator._calculate_similarity(concept1, concept2)
        print(f"📈 Similarity score: {score:.3f}")
        print(f"🎯 Would be flagged as duplicate: {'YES' if score >= 0.80 else 'NO'}")
        
        return True
    else:
        print("⚠️  Not enough function pointer concepts found for testing")
        return False

if __name__ == "__main__":
    print("Expert C Programming Deduplication Integration Tool")
    print("=" * 55)
    
    import json  # Add this for the test function
    
    # Apply the patch
    success = apply_deduplication_patch()
    
    if success:
        # Test the system
        test_deduplication()
    else:
        print("❌ Failed to apply deduplication patch")
        sys.exit(1)
