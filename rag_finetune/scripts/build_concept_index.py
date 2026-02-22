#!/usr/bin/env python3
"""
Build searchable index from concept JSON files.
Creates embeddings for fast semantic search.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configuration
CONCEPTS_DIR = Path("rag_finetune/data/concepts")
INDEX_DIR = Path("rag_finetune/data")
EMBEDDING_MODEL = "all-mpnet-base-v2"  # Better quality (420MB), 768-dim, ~5-10% more accurate


def load_all_concepts() -> List[Dict]:
    """Load all JSON concept files"""
    concepts = []

    print("Loading concepts from JSON files...")
    for json_file in tqdm(list(CONCEPTS_DIR.glob("*.json"))):
        try:
            with open(json_file, 'r') as f:
                concept_data = json.load(f)

            # Extract metadata
            book_name = concept_data.get("book", "unknown")  # Book stored in JSON
            concept_id = json_file.stem

            # Create searchable text (topic + keywords + explanation snippet)
            topic = concept_data.get("topic", "")
            keywords = concept_data.get("keywords", "")
            explanation = concept_data.get("explanation", "")

            # Handle keywords as either string or list
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)

            # Build searchable text with keywords for better matching
            searchable_parts = [topic]
            if keywords:
                searchable_parts.append(keywords)
            searchable_parts.append(explanation[:500])

            concepts.append({
                "id": concept_id,
                "book": book_name,
                "topic": topic,
                "explanation": explanation,
                "searchable_text": ". ".join(searchable_parts),
                "file_path": str(json_file)
            })
        except Exception as e:
            print(f"\n✗ ERROR: Failed to load {json_file.name}")
            print(f"  Reason: {e}")
            import traceback
            traceback.print_exc()
            continue

    return concepts


def build_embeddings(concepts: List[Dict], model_name: str) -> np.ndarray:
    """Create embeddings for all concepts"""
    print(f"\nLoading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    print("Generating embeddings...")
    texts = [c["searchable_text"] for c in concepts]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    return embeddings


def main():
    # Load concepts
    concepts = load_all_concepts()
    print(f"\n✅ Loaded {len(concepts)} concepts")

    # Build embeddings
    embeddings = build_embeddings(concepts, EMBEDDING_MODEL)
    print(f"✅ Created embeddings: {embeddings.shape}")

    # Save index
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    index_data = {
        "concepts": concepts,
        "embeddings": embeddings,
        "model_name": EMBEDDING_MODEL
    }

    index_file = INDEX_DIR / "concept_index.pkl"
    print(f"\nSaving index to {index_file}...")
    with open(index_file, 'wb') as f:
        pickle.dump(index_data, f)

    # Save metadata separately (for quick inspection)
    metadata_file = INDEX_DIR / "concept_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump({
            "total_concepts": len(concepts),
            "books": list(set(c["book"] for c in concepts)),
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": embeddings.shape[1]
        }, f, indent=2)

    print(f"✅ Index built successfully!")
    print(f"   Total concepts: {len(concepts)}")
    print(f"   Index size: {index_file.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
