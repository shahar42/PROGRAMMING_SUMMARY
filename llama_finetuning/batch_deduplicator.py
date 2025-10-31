import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Set
import re
from difflib import SequenceMatcher
import sys
from itertools import combinations

def _normalize_text(text: str) -> str:
    """Normalize text for better comparison"""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[(){}\[\];,.]', ' ', text)
    return text.strip()

def _text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings"""
    if not text1 or not text2:
        return 0.0
    text1_norm = _normalize_text(text1)
    text2_norm = _normalize_text(text2)
    return SequenceMatcher(None, text1_norm, text2_norm).ratio()

def _extract_concept_text(concept: Dict) -> str:
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

def _keyword_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on keyword overlap"""
    stopwords = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'can', 'use', 'used'}
    def extract_keywords(text):
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return set(word for word in words if word not in stopwords)
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)
    if not keywords1 or not keywords2:
        return 0.0
    intersection = len(keywords1.intersection(keywords2))
    union = len(keywords1.union(keywords2))
    return intersection / union if union > 0 else 0.0

def _calculate_similarity(concept1: Dict, concept2: Dict) -> float:
    """Calculate semantic similarity between two concepts"""
    topic_sim = _text_similarity(concept1.get('topic', ''), concept2.get('topic', ''))
    explanation_sim = _text_similarity(concept1.get('explanation', ''), concept2.get('explanation', ''))
    code_sim = 0.0
    if (concept1.get('code_example') and concept2.get('code_example')):
        code1 = '\n'.join(concept1['code_example'])
        code2 = '\n'.join(concept2['code_example'])
        code_sim = _text_similarity(code1, code2)
    text1 = _extract_concept_text(concept1)
    text2 = _extract_concept_text(concept2)
    keyword_sim = _keyword_similarity(text1, text2)
    final_score = (
        topic_sim * 0.35 +
        explanation_sim * 0.35 +
        code_sim * 0.20 +
        keyword_sim * 0.10
    )
    return min(final_score, 1.0)

def find_duplicates(directory: str, similarity_threshold: float) -> Tuple[Set[str], Dict[str, str]]:
    """Find duplicate files in a directory"""
    concept_files = list(Path(directory).glob("*.json"))
    if not concept_files:
        print(f"No JSON files found in {directory}")
        return set(), {}

    concepts = []
    for file_path in concept_files:
        try:
            with open(file_path, 'r') as f:
                concept = json.load(f)
                concepts.append({'_source_file': file_path, 'content': concept})
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not load {file_path}: {e}")

    duplicates_to_exclude = set()
    duplicate_reasons = {}

    for (concept1, concept2) in combinations(concepts, 2):
        if str(concept1['_source_file']) in duplicates_to_exclude or str(concept2['_source_file']) in duplicates_to_exclude:
            continue

        score = _calculate_similarity(concept1['content'], concept2['content'])
        if score >= similarity_threshold:
            # Mark the second file as a duplicate to be excluded
            duplicates_to_exclude.add(str(concept2['_source_file']))
            duplicate_reasons[str(concept2['_source_file'])] = f"Duplicate of {concept1['_source_file']} (score: {score:.3f})"

    return duplicates_to_exclude, duplicate_reasons

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python batch_deduplicator.py <directory> [similarity_threshold]")
        sys.exit(1)

    directory = sys.argv[1]
    similarity_threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.95

    print(f"🔍 Starting de-duplication process for directory: {directory}")
    print(f"   Similarity threshold: {similarity_threshold}")

    duplicates_to_exclude, duplicate_reasons = find_duplicates(directory, similarity_threshold)

    all_files = {str(p) for p in Path(directory).glob("*.json")}
    unique_files = all_files - duplicates_to_exclude

    print(f"\n📊 De-duplication Summary:")
    print(f"   Total files found: {len(all_files)}")
    print(f"   Duplicate files found: {len(duplicates_to_exclude)}")
    print(f"   Unique files remaining: {len(unique_files)}")

    if duplicates_to_exclude:
        print("\n🚮 Files marked for exclusion:")
        for i, (dup_file, reason) in enumerate(duplicate_reasons.items()):
            if i < 10: # Print first 10
                print(f"   - {Path(dup_file).name} ({reason})")
        if len(duplicates_to_exclude) > 10:
            print(f"   ... and {len(duplicates_to_exclude) - 10} more.")


    print("\n✅ Unique files to be used for generation:")
    for i, unique_file in enumerate(sorted(list(unique_files))):
         if i < 10: # Print first 10
            print(f"   - {Path(unique_file).name}")
    if len(unique_files) > 10:
        print(f"   ... and {len(unique_files) - 10} more.")


if __name__ == "__main__":
    main()
