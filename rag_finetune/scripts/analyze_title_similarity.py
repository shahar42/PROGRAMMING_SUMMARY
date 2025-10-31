#!/usr/bin/env python3
"""
Analyze semantic similarity between concept titles to find potential duplicates
that have different wording but mean the same thing.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

CONCEPTS_DIR = Path("rag_finetune/factory/output")
SIMILARITY_THRESHOLD = 0.85  # Titles above this threshold are considered similar


def load_all_concepts() -> List[Dict]:
    """Load all concepts from Effective Modern C++"""
    concepts = []
    target_book = "Effective Modern C++: 42 Specific Ways to Improve Your Use of C++11 and C++14 by Scott Meyers"

    for json_file in CONCEPTS_DIR.rglob("*.json"):
        if json_file.name in ["concept_cache.json", "progress.json"]:
            continue

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Filter by book
            book = data.get("book", "")
            if book != target_book:
                continue

            topic = data.get("topic", "").strip()
            if topic:  # Skip empty topics
                concepts.append({
                    "file_path": json_file,
                    "topic": topic,
                    "book": json_file.parent.name,
                    "concept_id": json_file.stem
                })
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return concepts


def find_similar_titles(concepts: List[Dict], threshold: float = SIMILARITY_THRESHOLD):
    """Find semantically similar titles using embeddings"""

    print(f"Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Encoding {len(concepts)} titles...")
    titles = [c["topic"] for c in concepts]
    embeddings = model.encode(titles, show_progress_bar=True, convert_to_numpy=True)

    print(f"Computing similarity matrix...")
    similarity_matrix = cosine_similarity(embeddings)

    # Find similar pairs
    similar_groups = []
    processed = set()

    for i in range(len(concepts)):
        if i in processed:
            continue

        # Find all concepts similar to concept i
        similar_indices = np.where(similarity_matrix[i] >= threshold)[0]

        # Exclude self-similarity
        similar_indices = [idx for idx in similar_indices if idx != i]

        if similar_indices:
            group = [i] + list(similar_indices)
            similar_groups.append([concepts[idx] for idx in group])
            processed.update(group)

    return similar_groups, similarity_matrix


def display_similar_groups(groups: List[List[Dict]]):
    """Display groups of similar titles"""

    print(f"\n{'='*80}")
    print(f"Found {len(groups)} groups of semantically similar titles")
    print(f"{'='*80}\n")

    for i, group in enumerate(groups, 1):
        print(f"Group {i} ({len(group)} concepts):")
        print("-" * 60)

        for concept in group:
            print(f"  • {concept['topic']}")
            print(f"    [{concept['book']}] {concept['concept_id']}")

        print()


def generate_statistics(concepts: List[Dict], groups: List[List[Dict]],
                        similarity_matrix: np.ndarray):
    """Generate statistics about title similarity"""

    print(f"\n{'='*80}")
    print("SIMILARITY STATISTICS")
    print(f"{'='*80}\n")

    print(f"Total concepts analyzed: {len(concepts)}")
    print(f"Similar groups found (≥{SIMILARITY_THRESHOLD:.0%} similarity): {len(groups)}")

    # Count concepts in groups
    concepts_in_groups = sum(len(g) for g in groups)
    print(f"Concepts in similar groups: {concepts_in_groups}")
    print(f"Unique concepts: {len(concepts) - concepts_in_groups}")

    # Average similarity
    # Get upper triangle of similarity matrix (excluding diagonal)
    upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
    avg_similarity = upper_triangle.mean()
    max_similarity = upper_triangle.max()

    print(f"\nAverage title similarity: {avg_similarity:.2%}")
    print(f"Maximum title similarity: {max_similarity:.2%}")

    # Distribution
    bins = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
    print("\nSimilarity distribution:")
    for i in range(len(bins) - 1):
        count = np.sum((upper_triangle >= bins[i]) & (upper_triangle < bins[i+1]))
        pct = count / len(upper_triangle) * 100
        print(f"  {bins[i]:.2f} - {bins[i+1]:.2f}: {count:6d} pairs ({pct:5.2f}%)")


def export_similar_groups(groups: List[List[Dict]], output_file: Path):
    """Export similar groups to JSON for review"""

    export_data = []
    for group in groups:
        export_data.append({
            "representative_title": group[0]["topic"],
            "count": len(group),
            "concepts": [
                {
                    "topic": c["topic"],
                    "book": c["book"],
                    "concept_id": c["concept_id"],
                    "file_path": str(c["file_path"])
                }
                for c in group
            ]
        })

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"\n✅ Similar groups exported to: {output_file}")


def main():
    print("Loading Effective Modern C++ concepts...")
    concepts = load_all_concepts()
    print(f"Loaded {len(concepts)} Effective Modern C++ concepts\n")

    if len(concepts) == 0:
        print("No concepts found. Please check the book metadata and path.")
        return

    # Find similar titles
    similar_groups, similarity_matrix = find_similar_titles(concepts, SIMILARITY_THRESHOLD)

    # Display results
    display_similar_groups(similar_groups)

    # Generate statistics
    generate_statistics(concepts, similar_groups, similarity_matrix)

    # Export for review
    output_file = Path("rag_finetune/data/similar_titles.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    export_similar_groups(similar_groups, output_file)

    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}")
    print(f"1. Review similar_titles.json to identify true duplicates")
    print(f"2. Run deduplicate_concepts.py to clean up exact duplicates first")
    print(f"3. Use Gemini to rename semantically similar concepts")
    print()


if __name__ == "__main__":
    main()
