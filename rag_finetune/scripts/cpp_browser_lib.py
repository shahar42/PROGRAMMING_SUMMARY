#!/usr/bin/env python3
"""
Core library for C++ Standard Library browser.
Handles data loading, taxonomy, and organization.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass
class ConceptInfo:
    """Represents a C++ concept with metadata."""
    concept_id: str
    topic: str
    explanation: str
    book: str
    category: str
    cpp_version: str
    file_path: Path

    def get_brief(self, max_length: int = 100) -> str:
        """Get brief description from explanation."""
        if not self.explanation:
            return ""

        # Clean up the explanation
        text = self.explanation.strip()

        # Take first sentence or max_length chars
        first_sentence = re.split(r'[.!?]\s', text)[0]
        if len(first_sentence) <= max_length:
            return first_sentence

        # Truncate to max_length
        return text[:max_length].rsplit(' ', 1)[0] + '...'


# Category taxonomy for C++ containers and algorithms
CATEGORY_TAXONOMY = {
    'containers': {
        'sequential': {
            'name': 'Sequential Containers',
            'items': ['vector', 'deque', 'list', 'array', 'forward_list']
        },
        'associative': {
            'name': 'Associative Containers',
            'items': ['set', 'multiset', 'map', 'multimap']
        },
        'unordered': {
            'name': 'Unordered Containers',
            'items': ['unordered_set', 'unordered_multiset',
                     'unordered_map', 'unordered_multimap']
        },
        'flat': {
            'name': 'Flat Containers (C++23)',
            'items': ['flat_set', 'flat_multiset', 'flat_map', 'flat_multimap']
        },
        'other': {
            'name': 'Other Containers',
            'items': ['bitset', 'span', 'mdspan', 'valarray']
        }
    },
    'adapters': {
        'name': 'Container Adapters',
        'items': ['stack', 'queue', 'priority_queue']
    },
    'algorithms': {
        'sorting': {
            'name': 'Sorting & Ordering',
            'items': ['sort', 'stable_sort', 'partial_sort', 'nth_element',
                     'is_sorted', 'is_sorted_until']
        },
        'searching': {
            'name': 'Searching',
            'items': ['find', 'find_if', 'find_if_not', 'find_end',
                     'find_first_of', 'search', 'binary_search',
                     'lower_bound', 'upper_bound', 'equal_range',
                     'contains', 'contains_subrange']
        },
        'modifying': {
            'name': 'Modifying Sequences',
            'items': ['copy', 'copy_if', 'copy_n', 'copy_backward',
                     'move', 'move_backward', 'fill', 'fill_n',
                     'transform', 'generate', 'replace', 'remove',
                     'unique', 'reverse', 'rotate', 'shuffle']
        },
        'partitioning': {
            'name': 'Partitioning',
            'items': ['partition', 'stable_partition', 'is_partitioned',
                     'partition_point']
        },
        'heap': {
            'name': 'Heap Operations',
            'items': ['make_heap', 'push_heap', 'pop_heap', 'sort_heap',
                     'is_heap', 'is_heap_until']
        },
        'minmax': {
            'name': 'Min/Max',
            'items': ['min', 'max', 'minmax', 'min_element', 'max_element',
                     'minmax_element', 'clamp']
        },
        'comparison': {
            'name': 'Comparison',
            'items': ['equal', 'mismatch', 'lexicographical_compare']
        },
        'permutation': {
            'name': 'Permutations',
            'items': ['next_permutation', 'prev_permutation', 'is_permutation']
        },
        'set_ops': {
            'name': 'Set Operations',
            'items': ['merge', 'inplace_merge', 'includes',
                     'set_union', 'set_intersection', 'set_difference',
                     'set_symmetric_difference']
        },
        'numeric': {
            'name': 'Numeric',
            'items': ['accumulate', 'inner_product', 'partial_sum',
                     'adjacent_difference', 'iota', 'reduce',
                     'transform_reduce', 'inclusive_scan', 'exclusive_scan']
        },
        'queries': {
            'name': 'Query Operations',
            'items': ['all_of', 'any_of', 'none_of', 'count', 'count_if',
                     'for_each', 'adjacent_find']
        }
    },
    'iterators': {
        'name': 'Iterators',
        'items': ['iterator', 'const_iterator', 'reverse_iterator',
                 'back_inserter', 'front_inserter', 'inserter',
                 'istream_iterator', 'ostream_iterator']
    },
    'smart_pointers': {
        'name': 'Smart Pointers',
        'items': ['unique_ptr', 'shared_ptr', 'weak_ptr', 'auto_ptr']
    }
}


class CppBrowserData:
    """Manages C++ concept data for browsing."""

    def __init__(self, concepts_dir: Path, version_map_file: Path,
                 config_file: Optional[Path] = None):
        """Initialize browser data."""
        self.concepts_dir = concepts_dir
        self.version_map_file = version_map_file
        self.config_file = config_file

        self.concepts: Dict[str, ConceptInfo] = {}
        self.version_map: Dict[str, str] = {}
        self.book_config: Dict = {}

        # Indexes for fast lookup
        self.by_category: Dict[str, List[ConceptInfo]] = defaultdict(list)
        self.by_version: Dict[str, List[ConceptInfo]] = defaultdict(list)
        self.by_feature: Dict[str, List[ConceptInfo]] = defaultdict(list)
        self.by_book: Dict[str, List[ConceptInfo]] = defaultdict(list)

    def load(self):
        """Load all data."""
        self._load_version_map()
        self._load_book_config()
        self._load_concepts()
        self._build_indexes()

    def _load_version_map(self):
        """Load C++ version map."""
        if not self.version_map_file.exists():
            print(f"Warning: Version map not found: {self.version_map_file}")
            return

        with open(self.version_map_file, 'r', encoding='utf-8') as f:
            self.version_map = json.load(f)

    def _load_book_config(self):
        """Load book configuration for colors."""
        if not self.config_file or not self.config_file.exists():
            return

        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.book_config = json.load(f)

    def _load_concepts(self):
        """Load all concept files."""
        concept_files = list(self.concepts_dir.glob('*.json'))

        for concept_file in concept_files:
            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                concept_id = concept_file.stem
                version = self.version_map.get(concept_id, 'unknown')

                concept = ConceptInfo(
                    concept_id=concept_id,
                    topic=data.get('topic', ''),
                    explanation=data.get('explanation', ''),
                    book=data.get('book', 'Unknown'),
                    category=data.get('category', 'unknown'),
                    cpp_version=version,
                    file_path=concept_file
                )

                self.concepts[concept_id] = concept

            except Exception as e:
                print(f"Error loading {concept_file.name}: {e}")

    def _build_indexes(self):
        """Build lookup indexes."""
        for concept in self.concepts.values():
            # Index by category
            self.by_category[concept.category].append(concept)

            # Index by version
            self.by_version[concept.cpp_version].append(concept)

            # Index by book
            self.by_book[concept.book].append(concept)

            # Index by feature (extracted from concept_id)
            features = self._extract_features(concept.concept_id)
            for feature in features:
                self.by_feature[feature].append(concept)

    def _extract_features(self, concept_id: str) -> List[str]:
        """Extract feature names from concept ID with strict matching."""
        import re
        features = []

        # Look for container/algorithm names with word boundaries
        for category_data in CATEGORY_TAXONOMY.values():
            if isinstance(category_data, dict):
                if 'items' in category_data:
                    # Direct items list
                    for item in category_data['items']:
                        # Use word boundaries and std:: prefix for precision
                        patterns = [
                            rf'\bstd::{re.escape(item)}\b',  # std::vector
                            rf'_{re.escape(item)}_',          # _vector_
                            rf'\b{re.escape(item)}\b',        # vector (word boundary)
                        ]
                        for pattern in patterns:
                            if re.search(pattern, concept_id.lower()):
                                features.append(item)
                                break
                else:
                    # Nested categories
                    for subcategory in category_data.values():
                        if isinstance(subcategory, dict) and 'items' in subcategory:
                            for item in subcategory['items']:
                                patterns = [
                                    rf'\bstd::{re.escape(item)}\b',
                                    rf'_{re.escape(item)}_',
                                    rf'\b{re.escape(item)}\b',
                                ]
                                for pattern in patterns:
                                    if re.search(pattern, concept_id.lower()):
                                        features.append(item)
                                        break

        return features

    def get_concepts_by_feature(self, feature: str) -> List[ConceptInfo]:
        """Get all concepts related to a specific feature."""
        results = self.by_feature.get(feature, [])

        # Manual mappings for features that don't match via ID patterns
        # Only search in topic (not explanation) and only for container categories
        manual_searches = {
            'unordered_map': 'unordered',
            'unordered_set': 'unordered',
            'unordered_multimap': 'unordered',
            'unordered_multiset': 'unordered',
        }

        # If feature has a manual search term and we got no results from ID matching
        if feature in manual_searches and len(results) == 0:
            search_term = manual_searches[feature]
            for concept in self.concepts.values():
                # Only search in topic and only container/adapter categories
                if concept.category in ['container', 'adapter']:
                    if search_term.lower() in concept.topic.lower():
                        if concept not in results:
                            results.append(concept)

        return results

    def get_concepts_by_version(self, version: str) -> List[ConceptInfo]:
        """Get all concepts for a specific C++ version."""
        return self.by_version.get(version, [])

    def get_concepts_by_category(self, category: str) -> List[ConceptInfo]:
        """Get all concepts in a specific category."""
        return self.by_category.get(category, [])

    def get_version_stats(self) -> Dict[str, int]:
        """Get statistics about version distribution."""
        return {version: len(concepts)
                for version, concepts in self.by_version.items()}

    def get_feature_stats(self) -> Dict[str, int]:
        """Get statistics about feature coverage."""
        return {feature: len(concepts)
                for feature, concepts in self.by_feature.items()}

    def search_concepts(self, query: str) -> List[ConceptInfo]:
        """Search concepts by query string."""
        query_lower = query.lower()
        results = []

        for concept in self.concepts.values():
            if (query_lower in concept.topic.lower() or
                query_lower in concept.explanation.lower() or
                query_lower in concept.concept_id.lower()):
                results.append(concept)

        return results

    def get_book_color(self, book_name: str) -> str:
        """Get color for a book."""
        if not self.book_config:
            return 'white'

        # book_config has structure: {"books": {"Book Name": {"color": "...", ...}}}
        books = self.book_config.get('books', {})
        book_info = books.get(book_name, {})
        return book_info.get('color', 'white')


def get_category_tree() -> Dict:
    """Get the category taxonomy tree."""
    return CATEGORY_TAXONOMY


def get_all_versions() -> List[str]:
    """Get list of all C++ versions in order."""
    return ['C++98', 'C++03', 'C++11', 'C++14', 'C++17', 'C++20', 'C++23']


def format_version_name(version: str) -> str:
    """Format version name for display."""
    if version == 'unknown':
        return 'Unknown Version'
    return version


def get_category_display_name(category_key: str) -> str:
    """Get display name for a category."""
    taxonomy = CATEGORY_TAXONOMY.get(category_key)
    if isinstance(taxonomy, dict):
        return taxonomy.get('name', category_key.title())
    return category_key.title()
