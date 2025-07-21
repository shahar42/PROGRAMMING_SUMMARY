#!/usr/bin/env python3
"""
Concept Memory Manager - Prevents duplicate concept extraction
This is the core deduplication system that sits between AI processing and file creation.
"""
from datetime import datetime
import json
import hashlib
import pickle
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ConceptMemoryManager:
    """Manages concept deduplication and similarity detection"""
    
    def __init__(self, project_root="/home/shahar42/Suumerizing_C_holy_grale_book"):
        self.project_root = Path(project_root)
        self.outputs_dir = self.project_root / "outputs"
        
        # Memory caches
        self.concept_index = {}  # {concept_id: concept_data}
        self.topic_to_ids = {}   # {topic_normalized: [concept_ids]}
        self.embeddings_cache = {}  # {concept_id: embedding_vector}
        
        # Similarity thresholds
        self.DUPLICATE_THRESHOLD = 0.85  # 85% similar = duplicate
        self.MERGE_THRESHOLD = 0.70      # 70-85% = consider merging
        
        # Initialize embedding model
        print("🧠 Loading sentence transformer for similarity detection...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load existing concepts on startup
        self._load_existing_concepts()
    
    def _load_existing_concepts(self):
        """Load all existing concepts from outputs directory"""
        print("📚 Loading existing concepts into memory...")
        
        for book_dir in self.outputs_dir.iterdir():
            if not book_dir.is_dir():
                continue
                
            print(f"  📖 Loading {book_dir.name} concepts...")
            concept_count = 0
            
            for concept_file in book_dir.glob("*concept_*.json"):
                try:
                    with open(concept_file, 'r', encoding='utf-8') as f:
                        concept_data = json.load(f)
                    
                    # Create unique concept ID
                    concept_id = f"{book_dir.name}_{concept_file.stem}"
                    
                    # Store in memory
                    self.concept_index[concept_id] = {
                        'data': concept_data,
                        'file_path': concept_file,
                        'book': book_dir.name
                    }
                    
                    # Index by normalized topic
                    normalized_topic = self._normalize_topic(concept_data.get('topic', ''))
                    if normalized_topic not in self.topic_to_ids:
                        self.topic_to_ids[normalized_topic] = []
                    self.topic_to_ids[normalized_topic].append(concept_id)
                    
                    concept_count += 1
                    
                except Exception as e:
                    print(f"    ⚠️  Error loading {concept_file}: {e}")
            
            print(f"    ✅ Loaded {concept_count} concepts from {book_dir.name}")
        
        print(f"🎯 Total concepts in memory: {len(self.concept_index)}")
    
    def _normalize_topic(self, topic):
        """Normalize topic for consistent comparison"""
        return topic.lower().strip().replace(' ', '_').replace('-', '_')
    
    def _get_concept_embedding(self, concept_data):
        """Get embedding for concept content"""
        # Combine topic and explanation for embedding
        text = f"{concept_data.get('topic', '')} {concept_data.get('explanation', '')}"
        return self.embedding_model.encode([text])[0]
    
    def check_for_duplicates(self, new_concept):
        """
        Check if new concept is duplicate of existing concepts
        Returns: (is_duplicate, similar_concepts, similarity_scores)
        """
        print(f"🔍 Checking for duplicates of: {new_concept.get('topic', 'Unknown')}")
        
        new_topic_normalized = self._normalize_topic(new_concept.get('topic', ''))
        similar_concepts = []
        
        # Step 1: Quick topic-based filtering
        potential_matches = []
        for topic, concept_ids in self.topic_to_ids.items():
            topic_similarity = fuzz.ratio(new_topic_normalized, topic) / 100.0
            if topic_similarity > 0.5:  # At least 50% topic similarity
                potential_matches.extend(concept_ids)
        
        print(f"  📋 Found {len(potential_matches)} potential matches based on topic")
        
        if not potential_matches:
            return False, [], []
        
        # Step 2: Detailed similarity analysis
        new_embedding = self._get_concept_embedding(new_concept)
        
        for concept_id in potential_matches:
            existing_concept = self.concept_index[concept_id]['data']
            similarity_score = self._calculate_similarity(new_concept, existing_concept, new_embedding)
            
            if similarity_score > self.MERGE_THRESHOLD:
                similar_concepts.append({
                    'concept_id': concept_id,
                    'concept_data': existing_concept,
                    'similarity_score': similarity_score,
                    'file_path': self.concept_index[concept_id]['file_path']
                })
        
        # Sort by similarity score (highest first)
        similar_concepts.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Check if highest similarity is above duplicate threshold
        is_duplicate = len(similar_concepts) > 0 and similar_concepts[0]['similarity_score'] > self.DUPLICATE_THRESHOLD
        
        if similar_concepts:
            print(f"  🎯 Found {len(similar_concepts)} similar concepts")
            print(f"  📊 Highest similarity: {similar_concepts[0]['similarity_score']:.2f}")
            if is_duplicate:
                print(f"  🚨 DUPLICATE DETECTED (>{self.DUPLICATE_THRESHOLD})")
            else:
                print(f"  ⚠️  Similar concept found (>{self.MERGE_THRESHOLD})")
        
        return is_duplicate, similar_concepts, [c['similarity_score'] for c in similar_concepts]
    
    def _calculate_similarity(self, concept_a, concept_b, embedding_a=None):
        """Calculate comprehensive similarity score between two concepts"""
        
        # 1. Topic name similarity (fuzzy string matching)
        topic_a = concept_a.get('topic', '')
        topic_b = concept_b.get('topic', '')
        topic_similarity = fuzz.ratio(topic_a, topic_b) / 100.0
        
        # 2. Content embedding similarity
        if embedding_a is None:
            embedding_a = self._get_concept_embedding(concept_a)
        embedding_b = self._get_concept_embedding(concept_b)
        content_similarity = cosine_similarity([embedding_a], [embedding_b])[0][0]
        
        # 3. Code example similarity (if both have code)
        code_similarity = 0.0
        code_a = concept_a.get('code_example', [])
        code_b = concept_b.get('code_example', [])
        
        if code_a and code_b:
            # Simple line-based comparison
            code_text_a = '\n'.join(code_a) if isinstance(code_a, list) else str(code_a)
            code_text_b = '\n'.join(code_b) if isinstance(code_b, list) else str(code_b)
            code_similarity = fuzz.ratio(code_text_a, code_text_b) / 100.0
        
        # 4. Syntax similarity
        syntax_similarity = 0.0
        syntax_a = concept_a.get('syntax', '')
        syntax_b = concept_b.get('syntax', '')
        if syntax_a and syntax_b:
            syntax_similarity = fuzz.ratio(syntax_a, syntax_b) / 100.0
        
        # Weighted combination
        # Topic and content are most important, code and syntax are secondary
        weights = {
            'topic': 0.3,
            'content': 0.4,
            'code': 0.2,
            'syntax': 0.1
        }
        
        combined_score = (
            topic_similarity * weights['topic'] +
            content_similarity * weights['content'] +
            code_similarity * weights['code'] +
            syntax_similarity * weights['syntax']
        )
        
        return combined_score
    
    def merge_concepts(self, new_concept, existing_similar):
        """Intelligently merge new concept with most similar existing concept"""
        
        best_match = existing_similar[0]  # Already sorted by similarity
        existing_concept = best_match['concept_data']
        
        print(f"🔄 Merging concepts:")
        print(f"  📌 Existing: {existing_concept.get('topic', 'Unknown')}")
        print(f"  📋 New: {new_concept.get('topic', 'Unknown')}")
        print(f"  📊 Similarity: {best_match['similarity_score']:.2f}")
        
        # Start with the existing concept as base
        merged_concept = existing_concept.copy()
        
        # Choose better title (usually longer, more descriptive)
        if len(new_concept.get('topic', '')) > len(existing_concept.get('topic', '')):
            merged_concept['topic'] = new_concept['topic']
        
        # Combine explanations (take longer, more detailed one)
        existing_explanation = existing_concept.get('explanation', '')
        new_explanation = new_concept.get('explanation', '')
        
        if len(new_explanation) > len(existing_explanation):
            merged_concept['explanation'] = new_explanation
        elif len(new_explanation) > 0 and new_explanation not in existing_explanation:
            # Append unique information
            merged_concept['explanation'] = existing_explanation + "\n\n" + new_explanation
        
        # Combine code examples (keep unique examples)
        existing_code = existing_concept.get('code_example', [])
        new_code = new_concept.get('code_example', [])
        
        if isinstance(existing_code, list) and isinstance(new_code, list):
            # If code examples are different, keep the longer/more complete one
            if len(new_code) > len(existing_code):
                merged_concept['code_example'] = new_code
                merged_concept['example_explanation'] = new_concept.get('example_explanation', '')
        
        # Update syntax if new one is more detailed
        existing_syntax = existing_concept.get('syntax', '')
        new_syntax = new_concept.get('syntax', '')
        if len(new_syntax) > len(existing_syntax):
            merged_concept['syntax'] = new_syntax
        
        # Update metadata
        merged_concept['extraction_metadata'] = existing_concept.get('extraction_metadata', {})
        merged_concept['extraction_metadata']['merged_on'] = datetime.now().isoformat()
        merged_concept['extraction_metadata']['merged_from'] = new_concept.get('extraction_metadata', {})
        merged_concept['extraction_metadata']['merge_similarity_score'] = float(best_match['similarity_score'])

        
        return merged_concept, best_match['file_path']
    
    def add_concept_to_memory(self, concept_data, file_path, book_name):
        """Add a new concept to memory after it's been saved"""
        
        concept_id = f"{book_name}_{Path(file_path).stem}"
        
        self.concept_index[concept_id] = {
            'data': concept_data,
            'file_path': file_path,
            'book': book_name
        }
        
        # Index by topic
        normalized_topic = self._normalize_topic(concept_data.get('topic', ''))
        if normalized_topic not in self.topic_to_ids:
            self.topic_to_ids[normalized_topic] = []
        self.topic_to_ids[normalized_topic].append(concept_id)
        
        print(f"  💾 Added concept to memory: {concept_data.get('topic', 'Unknown')}")
    
    def get_duplicate_report(self):
        """Generate a report of all duplicate concepts in the system"""
        print("📊 Generating duplicate analysis report...")
        
        all_concept_ids = list(self.concept_index.keys())
        duplicates_found = []
        processed_ids = set()
        
        for i, concept_id_a in enumerate(all_concept_ids):
            if concept_id_a in processed_ids:
                continue
                
            concept_a = self.concept_index[concept_id_a]['data']
            similar_group = [concept_id_a]
            
            for j, concept_id_b in enumerate(all_concept_ids[i+1:], i+1):
                if concept_id_b in processed_ids:
                    continue
                    
                concept_b = self.concept_index[concept_id_b]['data']
                similarity = self._calculate_similarity(concept_a, concept_b)
                
                if similarity > self.DUPLICATE_THRESHOLD:
                    similar_group.append(concept_id_b)
                    processed_ids.add(concept_id_b)
            
            if len(similar_group) > 1:
                duplicates_found.append(similar_group)
                for concept_id in similar_group:
                    processed_ids.add(concept_id)
        
        return duplicates_found
