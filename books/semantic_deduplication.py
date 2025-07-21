"""
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
            code1 = '\n'.join(concept1['code_example'])
            code2 = '\n'.join(concept2['code_example'])
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
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common programming punctuation that doesn't affect meaning
        text = re.sub(r'[(){}\[\];,.]', ' ', text)
        
        return text.strip()
    
    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on keyword overlap"""
        # Extract meaningful keywords (3+ characters, not common words)
        stopwords = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'can', 'use', 'used'}
        
        def extract_keywords(text):
            words = re.findall(r'\b\w{3,}\b', text.lower())
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
