#!/usr/bin/env python3
"""
Test search quality with various queries to identify improvement areas.
"""

import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
INDEX_FILE = BASE_DIR / "rag_finetune/data/concept_index.pkl"

# Test queries covering different search patterns
TEST_QUERIES = [
    # Abbreviations
    ("RAII", "Should find Resource Acquisition Is Initialization"),
    ("vtable", "Should find virtual function table concepts"),
    ("RTTI", "Should find runtime type information"),
    ("ADL", "Should find argument-dependent lookup"),

    # C++ syntax
    ("std::vector", "Should find vector container concepts"),
    ("operator new", "Should find operator new vs new operator"),
    ("std::move", "Should find move semantics"),

    # Conceptual questions
    ("what is perfect forwarding", "Question format - should find forwarding"),
    ("how does virtual dispatch work", "Question format - should find vtable"),
    ("memory leak", "Should find RAII, smart pointers"),

    # Technical terms
    ("undefined behavior", "Should find UB examples"),
    ("dangling pointer", "Should find pointer safety"),
    ("template metaprogramming", "Should find TMP concepts"),

    # Common confusions
    ("new vs malloc", "Should find memory allocation comparison"),
    ("reference vs pointer", "Should find reference concepts"),
    ("const vs constexpr", "Should find const qualifier concepts"),
]


class SearchAnalyzer:
    def __init__(self, index_path: Path, use_reranker: bool = True):
        """Load pre-built index"""
        with open(index_path, 'rb') as f:
            data = pickle.load(f)

        self.concepts = data["concepts"]
        self.embeddings = data["embeddings"]
        self.model_name = data["model_name"]
        self.model = SentenceTransformer(self.model_name)

        # Load reranker
        if use_reranker:
            print("Loading cross-encoder reranker...")
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        else:
            self.reranker = None

    def search(self, query: str, top_k: int = 10, rerank_k: int = 20) -> List[Tuple[Dict, float]]:
        """Search with keyword boost and optional reranking"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:max(top_k, rerank_k)]

        results = []
        query_words = set(query.lower().split())

        for idx in top_indices:
            concept = self.concepts[idx]
            semantic_score = float(similarities[idx])

            # Load concept JSON to check keywords
            file_path = Path(concept["file_path"])
            if not file_path.is_absolute():
                file_path = BASE_DIR / file_path

            try:
                with open(file_path, 'r') as f:
                    full_data = json.load(f)

                keywords = full_data.get("keywords", "")
                if isinstance(keywords, list):
                    keywords = ", ".join(keywords)

                # Keyword boost
                keyword_boost = 0
                if keywords:
                    keyword_words = set(keywords.lower().replace(",", " ").split())
                    matches = query_words & keyword_words
                    keyword_boost = len(matches) * 0.08

                final_score = min(semantic_score + keyword_boost, 1.0)
                results.append((concept, final_score, semantic_score, keyword_boost, full_data))
            except Exception:
                results.append((concept, semantic_score, semantic_score, 0.0, None))

        results.sort(key=lambda x: x[1], reverse=True)

        # Apply reranking if enabled
        if self.reranker and len(results) > 0:
            rerank_candidates = results[:rerank_k]

            # Prepare pairs for reranking
            pairs = []
            for concept, score, sem_score, kw_boost, full_data in rerank_candidates:
                if full_data:
                    doc_text = f"{concept['topic']}. {full_data.get('explanation', '')[:300]}"
                else:
                    doc_text = concept['topic']
                pairs.append([query, doc_text])

            # Get reranker scores
            rerank_scores = self.reranker.predict(pairs)

            # Blend scores
            reranked = []
            for i, (concept, orig_score, sem_score, kw_boost, full_data) in enumerate(rerank_candidates):
                rerank_score = float(rerank_scores[i])
                normalized_rerank = 1 / (1 + np.exp(-rerank_score))
                blended_score = 0.6 * orig_score + 0.4 * normalized_rerank
                reranked.append((concept, blended_score, sem_score, kw_boost))

            # Keep non-reranked
            remaining = [(c, s, ss, kb) for c, s, ss, kb, _ in results[rerank_k:]]
            results = reranked + remaining
            results.sort(key=lambda x: x[1], reverse=True)
        else:
            results = [(c, s, ss, kb) for c, s, ss, kb, _ in results]

        return results[:top_k]

    def analyze_query(self, query: str, expected: str, top_k: int = 5):
        """Analyze a single query and print results"""
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        print(f"{'='*80}")

        results = self.search(query, top_k=top_k)

        for i, (concept, final_score, sem_score, kw_boost) in enumerate(results, 1):
            topic = concept['topic']
            if len(topic) > 70:
                topic = topic[:67] + "..."

            book = concept.get('book', 'Unknown')[:30]

            boost_indicator = f" (+{kw_boost:.2f})" if kw_boost > 0 else ""
            print(f"\n[{i}] {final_score:.3f} ({sem_score:.3f}{boost_indicator}) | {book}")
            print(f"    {topic}")

        # Quality check
        if results:
            top_score = results[0][1]
            if top_score < 0.4:
                print(f"\n⚠️  LOW CONFIDENCE: Top result only {top_score:.1%}")
            elif top_score < 0.6:
                print(f"\n⚠️  MEDIUM CONFIDENCE: Top result {top_score:.1%}")
            else:
                print(f"\n✓ HIGH CONFIDENCE: Top result {top_score:.1%}")


def main():
    print("Loading search index...")
    analyzer = SearchAnalyzer(INDEX_FILE, use_reranker=True)
    print(f"✓ Loaded {len(analyzer.concepts)} concepts")
    print(f"✓ Model: {analyzer.model_name}")
    print(f"✓ Reranker: {'Enabled' if analyzer.reranker else 'Disabled'}")

    print("\n" + "="*80)
    print("IMPROVED SEARCH QUALITY ANALYSIS")
    print("="*80)
    print("Upgrades: all-mpnet-base-v2 (768-dim) + cross-encoder reranking")
    print("="*80)

    for query, expected in TEST_QUERIES:
        analyzer.analyze_query(query, expected)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nExpected improvements vs old system:")
    print("- Higher semantic scores (better embeddings)")
    print("- More accurate top-5 results (reranker filtering)")
    print("- Better handling of comparison queries")
    print("- Fewer false positives")


if __name__ == "__main__":
    main()
