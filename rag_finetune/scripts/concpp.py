#!/usr/bin/env python3
"""
C++ Standard Library Reference
Clean, fast reference for C++ containers, algorithms, iterators, and smart pointers

Usage: python concpp.py
"""

import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    import questionary
    from questionary import Choice, Style
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install rich questionary")
    sys.exit(1)

console = Console()

QUESTIONARY_STYLE = Style([
    ("normal", "fg:#FFFFFF"),
    ("bright_blue", "fg:#5F87FF bold"),
    ("bright_cyan", "fg:#5FFFFF bold"),
    ("bright_green", "fg:#5FFF5F bold"),
    ("bright_yellow", "fg:#FFFF5F bold"),
    ("cyan", "fg:#5FAFAF bold"),
    ("yellow", "fg:#AFAF5F bold"),
    ("grey70", "fg:#BCBCBC"),
    ("white", "fg:#FFFFFF bold"),
])


@dataclass
class CppFeature:
    """C++ Standard Library feature."""
    name: str
    version: str
    description: str


@dataclass
class MemberFunction:
    """Member function or operation."""
    name: str
    description: str
    complexity: str = ""


@dataclass
class CppFeatureDetail:
    """Detailed reference information for a C++ feature."""
    name: str
    version: str
    description: str
    member_types: List[Tuple[str, str]] = None  # [(name, description), ...]
    member_functions: Dict[str, List[MemberFunction]] = None  # {category: [functions]}
    notes: List[str] = None  # Additional notes
    related_concepts: List[str] = None  # Optional links to extracted concepts


# ============================================================================
# CONTAINERS
# ============================================================================

CONTAINERS = {
    "Sequential Containers": [
        CppFeature("array", "C++11", "Fixed-size array container"),
        CppFeature("vector", "C++98", "Dynamic array with contiguous storage"),
        CppFeature("deque", "C++98", "Double-ended queue"),
        CppFeature("list", "C++98", "Doubly-linked list"),
        CppFeature("forward_list", "C++11", "Singly-linked list"),
    ],
    "Associative Containers": [
        CppFeature("set", "C++98", "Sorted unique keys"),
        CppFeature("multiset", "C++98", "Sorted keys with duplicates"),
        CppFeature("map", "C++98", "Sorted key-value pairs, unique keys"),
        CppFeature("multimap", "C++98", "Sorted key-value pairs with duplicates"),
    ],
    "Unordered Containers": [
        CppFeature("unordered_set", "C++11", "Hash table of unique keys"),
        CppFeature("unordered_multiset", "C++11", "Hash table with duplicate keys"),
        CppFeature("unordered_map", "C++11", "Hash table key-value pairs, unique keys"),
        CppFeature("unordered_multimap", "C++11", "Hash table key-value pairs with duplicates"),
    ],
    "Container Adapters": [
        CppFeature("stack", "C++98", "LIFO stack adapter"),
        CppFeature("queue", "C++98", "FIFO queue adapter"),
        CppFeature("priority_queue", "C++98", "Heap-based priority queue"),
    ],
    "Other Containers": [
        CppFeature("bitset", "C++98", "Fixed-size sequence of bits"),
        CppFeature("span", "C++20", "Non-owning view over contiguous sequence"),
    ],
}


# ============================================================================
# ALGORITHMS
# ============================================================================

ALGORITHMS = {
    "Non-modifying Sequence Operations": [
        CppFeature("all_of", "C++11", "Check if all elements satisfy condition"),
        CppFeature("any_of", "C++11", "Check if any element satisfies condition"),
        CppFeature("none_of", "C++11", "Check if no elements satisfy condition"),
        CppFeature("for_each", "C++98", "Apply function to range"),
        CppFeature("for_each_n", "C++17", "Apply function to first n elements"),
        CppFeature("count", "C++98", "Count occurrences of value"),
        CppFeature("count_if", "C++98", "Count elements satisfying condition"),
        CppFeature("find", "C++98", "Find first occurrence of value"),
        CppFeature("find_if", "C++98", "Find first element satisfying condition"),
        CppFeature("find_if_not", "C++11", "Find first element not satisfying condition"),
        CppFeature("find_end", "C++98", "Find last occurrence of subsequence"),
        CppFeature("find_first_of", "C++98", "Find first element from set"),
        CppFeature("adjacent_find", "C++98", "Find consecutive equal elements"),
        CppFeature("search", "C++98", "Find subsequence"),
        CppFeature("search_n", "C++98", "Find n consecutive equal values"),
        CppFeature("mismatch", "C++98", "Find first position where ranges differ"),
    ],
    "Modifying Sequence Operations": [
        CppFeature("copy", "C++98", "Copy range"),
        CppFeature("copy_if", "C++11", "Copy elements satisfying condition"),
        CppFeature("copy_n", "C++11", "Copy n elements"),
        CppFeature("copy_backward", "C++98", "Copy range backwards"),
        CppFeature("move", "C++11", "Move range"),
        CppFeature("move_backward", "C++11", "Move range backwards"),
        CppFeature("fill", "C++98", "Fill range with value"),
        CppFeature("fill_n", "C++98", "Fill n elements with value"),
        CppFeature("transform", "C++98", "Apply function and store result"),
        CppFeature("generate", "C++98", "Generate values using function"),
        CppFeature("generate_n", "C++98", "Generate n values using function"),
        CppFeature("remove", "C++98", "Remove elements equal to value"),
        CppFeature("remove_if", "C++98", "Remove elements satisfying condition"),
        CppFeature("remove_copy", "C++98", "Copy range excluding value"),
        CppFeature("remove_copy_if", "C++98", "Copy range excluding elements satisfying condition"),
        CppFeature("replace", "C++98", "Replace value with another"),
        CppFeature("replace_if", "C++98", "Replace elements satisfying condition"),
        CppFeature("replace_copy", "C++98", "Copy range replacing value"),
        CppFeature("replace_copy_if", "C++98", "Copy range replacing elements satisfying condition"),
        CppFeature("swap", "C++98", "Exchange values"),
        CppFeature("swap_ranges", "C++98", "Exchange ranges"),
        CppFeature("iter_swap", "C++98", "Exchange iterator values"),
        CppFeature("reverse", "C++98", "Reverse range"),
        CppFeature("reverse_copy", "C++98", "Copy range in reverse"),
        CppFeature("rotate", "C++98", "Rotate elements in range"),
        CppFeature("rotate_copy", "C++98", "Copy rotated range"),
        CppFeature("shuffle", "C++11", "Randomly reorder elements"),
        CppFeature("sample", "C++17", "Random sample from range"),
        CppFeature("unique", "C++98", "Remove consecutive duplicates"),
        CppFeature("unique_copy", "C++98", "Copy range removing consecutive duplicates"),
    ],
    "Partitioning Operations": [
        CppFeature("partition", "C++98", "Partition range by predicate"),
        CppFeature("stable_partition", "C++98", "Partition preserving relative order"),
        CppFeature("partition_copy", "C++11", "Copy partitioned elements"),
        CppFeature("is_partitioned", "C++11", "Check if range is partitioned"),
        CppFeature("partition_point", "C++11", "Find partition point"),
    ],
    "Sorting Operations": [
        CppFeature("sort", "C++98", "Sort range"),
        CppFeature("stable_sort", "C++98", "Sort preserving equal element order"),
        CppFeature("partial_sort", "C++98", "Partially sort range"),
        CppFeature("partial_sort_copy", "C++98", "Copy partially sorted range"),
        CppFeature("is_sorted", "C++11", "Check if range is sorted"),
        CppFeature("is_sorted_until", "C++11", "Find first unsorted element"),
        CppFeature("nth_element", "C++98", "Partition at nth position"),
    ],
    "Binary Search Operations (on sorted ranges)": [
        CppFeature("binary_search", "C++98", "Check if value exists"),
        CppFeature("lower_bound", "C++98", "Find first position not less than value"),
        CppFeature("upper_bound", "C++98", "Find first position greater than value"),
        CppFeature("equal_range", "C++98", "Find range of equal elements"),
    ],
    "Set Operations (on sorted ranges)": [
        CppFeature("merge", "C++98", "Merge sorted ranges"),
        CppFeature("inplace_merge", "C++98", "In-place merge of sorted ranges"),
        CppFeature("includes", "C++98", "Check if range includes another"),
        CppFeature("set_difference", "C++98", "Elements in first but not second"),
        CppFeature("set_intersection", "C++98", "Elements in both ranges"),
        CppFeature("set_symmetric_difference", "C++98", "Elements in one but not both"),
        CppFeature("set_union", "C++98", "Elements in either range"),
    ],
    "Heap Operations": [
        CppFeature("make_heap", "C++98", "Create heap from range"),
        CppFeature("push_heap", "C++98", "Add element to heap"),
        CppFeature("pop_heap", "C++98", "Remove largest element from heap"),
        CppFeature("sort_heap", "C++98", "Sort heap"),
        CppFeature("is_heap", "C++11", "Check if range is heap"),
        CppFeature("is_heap_until", "C++11", "Find first element not in heap"),
    ],
    "Min/Max Operations": [
        CppFeature("min", "C++98", "Return smaller value"),
        CppFeature("max", "C++98", "Return larger value"),
        CppFeature("minmax", "C++11", "Return both min and max"),
        CppFeature("min_element", "C++98", "Find smallest element"),
        CppFeature("max_element", "C++98", "Find largest element"),
        CppFeature("minmax_element", "C++11", "Find both smallest and largest"),
        CppFeature("clamp", "C++17", "Clamp value to range"),
    ],
    "Comparison Operations": [
        CppFeature("equal", "C++98", "Check if ranges are equal"),
        CppFeature("lexicographical_compare", "C++98", "Lexicographic comparison"),
    ],
    "Numeric Operations": [
        CppFeature("accumulate", "C++98", "Sum or accumulate values"),
        CppFeature("reduce", "C++17", "Parallel-friendly accumulation"),
        CppFeature("transform_reduce", "C++17", "Transform then reduce"),
        CppFeature("exclusive_scan", "C++17", "Exclusive prefix sum"),
        CppFeature("inclusive_scan", "C++17", "Inclusive prefix sum"),
        CppFeature("transform_exclusive_scan", "C++17", "Transform then exclusive scan"),
        CppFeature("transform_inclusive_scan", "C++17", "Transform then inclusive scan"),
        CppFeature("adjacent_difference", "C++98", "Compute differences between adjacent elements"),
        CppFeature("inner_product", "C++98", "Compute dot product"),
        CppFeature("gcd", "C++17", "Greatest common divisor"),
        CppFeature("lcm", "C++17", "Least common multiple"),
    ],
}


# ============================================================================
# ITERATORS
# ============================================================================

ITERATORS = {
    "Iterator Types": [
        CppFeature("iterator", "C++98", "Basic iterator type"),
        CppFeature("const_iterator", "C++98", "Constant iterator"),
        CppFeature("reverse_iterator", "C++98", "Reverse iteration"),
        CppFeature("const_reverse_iterator", "C++98", "Constant reverse iterator"),
    ],
    "Iterator Adaptors": [
        CppFeature("back_inserter", "C++98", "Insert at end"),
        CppFeature("front_inserter", "C++98", "Insert at beginning"),
        CppFeature("inserter", "C++98", "Insert at position"),
        CppFeature("move_iterator", "C++11", "Move elements during iteration"),
    ],
    "Stream Iterators": [
        CppFeature("istream_iterator", "C++98", "Read from input stream"),
        CppFeature("ostream_iterator", "C++98", "Write to output stream"),
        CppFeature("istreambuf_iterator", "C++98", "Read from stream buffer"),
        CppFeature("ostreambuf_iterator", "C++98", "Write to stream buffer"),
    ],
}


# ============================================================================
# SMART POINTERS
# ============================================================================

SMART_POINTERS = {
    "Smart Pointers": [
        CppFeature("unique_ptr", "C++11", "Exclusive ownership smart pointer"),
        CppFeature("shared_ptr", "C++11", "Shared ownership smart pointer"),
        CppFeature("weak_ptr", "C++11", "Non-owning reference to shared_ptr"),
    ],
    "Helper Functions": [
        CppFeature("make_unique", "C++14", "Create unique_ptr"),
        CppFeature("make_shared", "C++11", "Create shared_ptr"),
    ],
}


# ============================================================================
# DETAILED REFERENCE DATA
# ============================================================================

DETAIL_DATA = {
    # CONTAINERS
    "vector": CppFeatureDetail(
        name="std::vector",
        version="C++98",
        description="Dynamic contiguous array with automatic resizing",
        member_types=[
            ("value_type", "T"),
            ("size_type", "size_t"),
            ("reference", "value_type&"),
            ("const_reference", "const value_type&"),
            ("iterator", "Random access iterator"),
            ("const_iterator", "Const random access iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("at(pos)", "Access element with bounds checking", "O(1)"),
                MemberFunction("operator[]", "Access element without bounds checking", "O(1)"),
                MemberFunction("front()", "Access first element", "O(1)"),
                MemberFunction("back()", "Access last element", "O(1)"),
                MemberFunction("data()", "Direct access to underlying array", "O(1)"),
            ],
            "Iterators": [
                MemberFunction("begin(), end()", "Iterator to beginning/end", "O(1)"),
                MemberFunction("rbegin(), rend()", "Reverse iterator", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
                MemberFunction("capacity()", "Storage capacity", "O(1)"),
                MemberFunction("reserve(n)", "Reserve storage", "O(n)"),
                MemberFunction("shrink_to_fit()", "Reduce capacity to size", "O(n)"),
            ],
            "Modifiers": [
                MemberFunction("clear()", "Remove all elements", "O(n)"),
                MemberFunction("insert(pos, value)", "Insert element", "O(n)"),
                MemberFunction("erase(pos)", "Erase element", "O(n)"),
                MemberFunction("push_back(value)", "Add element at end", "Amortized O(1)"),
                MemberFunction("pop_back()", "Remove last element", "O(1)"),
                MemberFunction("resize(n)", "Change size", "O(n)"),
            ],
        },
        notes=[
            "Contiguous storage - cache friendly",
            "Amortized O(1) insertion at end",
            "Iterator invalidation on reallocation",
        ]
    ),

    "deque": CppFeatureDetail(
        name="std::deque",
        version="C++98",
        description="Double-ended queue with efficient insertion/deletion at both ends",
        member_types=[
            ("value_type", "T"),
            ("size_type", "size_t"),
            ("iterator", "Random access iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("at(pos)", "Access with bounds checking", "O(1)"),
                MemberFunction("operator[]", "Direct access", "O(1)"),
                MemberFunction("front()", "First element", "O(1)"),
                MemberFunction("back()", "Last element", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("push_back(value)", "Add at end", "O(1)"),
                MemberFunction("push_front(value)", "Add at beginning", "O(1)"),
                MemberFunction("pop_back()", "Remove from end", "O(1)"),
                MemberFunction("pop_front()", "Remove from beginning", "O(1)"),
                MemberFunction("insert(pos, value)", "Insert element", "O(n)"),
                MemberFunction("erase(pos)", "Remove element", "O(n)"),
            ],
        },
        notes=[
            "O(1) insertion/deletion at both ends",
            "Not contiguous in memory",
        ]
    ),

    "list": CppFeatureDetail(
        name="std::list",
        version="C++98",
        description="Doubly-linked list",
        member_types=[
            ("value_type", "T"),
            ("iterator", "Bidirectional iterator"),
        ],
        member_functions={
            "Modifiers": [
                MemberFunction("push_back(value)", "Add at end", "O(1)"),
                MemberFunction("push_front(value)", "Add at beginning", "O(1)"),
                MemberFunction("insert(pos, value)", "Insert before pos", "O(1)"),
                MemberFunction("erase(pos)", "Remove element", "O(1)"),
                MemberFunction("splice(pos, other)", "Transfer elements", "O(1) or O(n)"),
            ],
            "Operations": [
                MemberFunction("sort()", "Sort elements", "O(n log n)"),
                MemberFunction("merge(other)", "Merge sorted lists", "O(n)"),
                MemberFunction("unique()", "Remove consecutive duplicates", "O(n)"),
                MemberFunction("reverse()", "Reverse order", "O(n)"),
            ],
        },
        notes=[
            "No random access",
            "Iterators never invalidated except when element erased",
        ]
    ),

    "map": CppFeatureDetail(
        name="std::map",
        version="C++98",
        description="Sorted associative container with unique keys",
        member_types=[
            ("key_type", "Key"),
            ("mapped_type", "T"),
            ("value_type", "std::pair<const Key, T>"),
            ("iterator", "Bidirectional iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("at(key)", "Access with bounds checking", "O(log n)"),
                MemberFunction("operator[key]", "Access or insert", "O(log n)"),
            ],
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(log n)"),
                MemberFunction("count(key)", "Count elements (0 or 1)", "O(log n)"),
                MemberFunction("lower_bound(key)", "First not less than key", "O(log n)"),
                MemberFunction("upper_bound(key)", "First greater than key", "O(log n)"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(log n)"),
                MemberFunction("erase(key)", "Remove element", "O(log n)"),
                MemberFunction("clear()", "Remove all", "O(n)"),
            ],
        },
        notes=[
            "Keys are sorted (typically red-black tree)",
            "Unique keys only",
        ]
    ),

    "set": CppFeatureDetail(
        name="std::set",
        version="C++98",
        description="Sorted collection of unique keys",
        member_types=[
            ("key_type", "Key"),
            ("value_type", "Key"),
            ("iterator", "Bidirectional iterator to const"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(log n)"),
                MemberFunction("count(key)", "Count (0 or 1)", "O(log n)"),
                MemberFunction("contains(key)", "Check existence (C++20)", "O(log n)"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(log n)"),
                MemberFunction("erase(key)", "Remove element", "O(log n)"),
            ],
        },
        notes=[
            "Sorted unique elements",
            "Keys are immutable",
        ]
    ),

    "unordered_map": CppFeatureDetail(
        name="std::unordered_map",
        version="C++11",
        description="Hash table with unique keys",
        member_types=[
            ("key_type", "Key"),
            ("mapped_type", "T"),
            ("value_type", "std::pair<const Key, T>"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("at(key)", "Access with bounds checking", "O(1) avg"),
                MemberFunction("operator[key]", "Access or insert", "O(1) avg"),
            ],
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(1) avg, O(n) worst"),
                MemberFunction("count(key)", "Count (0 or 1)", "O(1) avg"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(1) avg"),
                MemberFunction("erase(key)", "Remove element", "O(1) avg"),
            ],
        },
        notes=[
            "Fast average-case lookup",
            "Unordered - no sorting",
        ]
    ),

    "array": CppFeatureDetail(
        name="std::array",
        version="C++11",
        description="Fixed-size array container",
        member_types=[
            ("value_type", "T"),
            ("size_type", "size_t"),
            ("iterator", "Random access iterator"),
            ("const_iterator", "Const random access iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("at(pos)", "Access with bounds checking", "O(1)"),
                MemberFunction("operator[]", "Direct access", "O(1)"),
                MemberFunction("front()", "First element", "O(1)"),
                MemberFunction("back()", "Last element", "O(1)"),
                MemberFunction("data()", "Pointer to underlying array", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
                MemberFunction("max_size()", "Maximum size", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("fill(value)", "Fill with value", "O(n)"),
                MemberFunction("swap(other)", "Swap contents", "O(n)"),
            ],
        },
        notes=[
            "Fixed size at compile time",
            "No dynamic allocation",
            "Zero overhead vs C array",
        ]
    ),

    "forward_list": CppFeatureDetail(
        name="std::forward_list",
        version="C++11",
        description="Singly-linked list",
        member_types=[
            ("value_type", "T"),
            ("iterator", "Forward iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("front()", "First element", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("push_front(value)", "Add at beginning", "O(1)"),
                MemberFunction("pop_front()", "Remove from beginning", "O(1)"),
                MemberFunction("insert_after(pos, value)", "Insert after position", "O(1)"),
                MemberFunction("erase_after(pos)", "Erase after position", "O(1)"),
            ],
            "Operations": [
                MemberFunction("sort()", "Sort elements", "O(n log n)"),
                MemberFunction("merge(other)", "Merge sorted lists", "O(n)"),
                MemberFunction("unique()", "Remove consecutive duplicates", "O(n)"),
                MemberFunction("reverse()", "Reverse order", "O(n)"),
            ],
        },
        notes=[
            "Singly-linked - forward iteration only",
            "No size() member",
            "Lower memory overhead than list",
        ]
    ),

    "multiset": CppFeatureDetail(
        name="std::multiset",
        version="C++98",
        description="Sorted collection allowing duplicate keys",
        member_types=[
            ("key_type", "Key"),
            ("value_type", "Key"),
            ("iterator", "Bidirectional iterator to const"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(log n)"),
                MemberFunction("count(key)", "Count occurrences", "O(log n) + k"),
                MemberFunction("equal_range(key)", "Range of equal elements", "O(log n)"),
                MemberFunction("lower_bound(key)", "First not less than key", "O(log n)"),
                MemberFunction("upper_bound(key)", "First greater than key", "O(log n)"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(log n)"),
                MemberFunction("erase(key)", "Remove all occurrences", "O(log n) + k"),
            ],
        },
        notes=[
            "Allows duplicate keys",
            "Elements sorted automatically",
        ]
    ),

    "multimap": CppFeatureDetail(
        name="std::multimap",
        version="C++98",
        description="Sorted associative container allowing duplicate keys",
        member_types=[
            ("key_type", "Key"),
            ("mapped_type", "T"),
            ("value_type", "std::pair<const Key, T>"),
            ("iterator", "Bidirectional iterator"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(log n)"),
                MemberFunction("count(key)", "Count occurrences", "O(log n) + k"),
                MemberFunction("equal_range(key)", "Range of equal keys", "O(log n)"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(log n)"),
                MemberFunction("erase(key)", "Remove all with key", "O(log n) + k"),
            ],
        },
        notes=[
            "Multiple values per key allowed",
            "Keys sorted automatically",
        ]
    ),

    "unordered_set": CppFeatureDetail(
        name="std::unordered_set",
        version="C++11",
        description="Hash table of unique keys",
        member_types=[
            ("key_type", "Key"),
            ("value_type", "Key"),
            ("hasher", "Hash function"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(1) avg, O(n) worst"),
                MemberFunction("count(key)", "Count (0 or 1)", "O(1) avg"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(1) avg"),
                MemberFunction("erase(key)", "Remove element", "O(1) avg"),
            ],
        },
        notes=[
            "Unique keys only",
            "Unordered - no sorting",
        ]
    ),

    "unordered_multiset": CppFeatureDetail(
        name="std::unordered_multiset",
        version="C++11",
        description="Hash table allowing duplicate keys",
        member_types=[
            ("key_type", "Key"),
            ("value_type", "Key"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(1) avg, O(n) worst"),
                MemberFunction("count(key)", "Count occurrences", "O(1) avg"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(1) avg"),
                MemberFunction("erase(key)", "Remove all occurrences", "O(1) avg"),
            ],
        },
        notes=[
            "Allows duplicate keys",
            "Unordered - no sorting",
        ]
    ),

    "unordered_multimap": CppFeatureDetail(
        name="std::unordered_multimap",
        version="C++11",
        description="Hash table allowing duplicate keys with mapped values",
        member_types=[
            ("key_type", "Key"),
            ("mapped_type", "T"),
            ("value_type", "std::pair<const Key, T>"),
        ],
        member_functions={
            "Lookup": [
                MemberFunction("find(key)", "Find element", "O(1) avg, O(n) worst"),
                MemberFunction("count(key)", "Count occurrences", "O(1) avg"),
            ],
            "Modifiers": [
                MemberFunction("insert(value)", "Insert element", "O(1) avg"),
                MemberFunction("erase(key)", "Remove all with key", "O(1) avg"),
            ],
        },
        notes=[
            "Multiple values per key",
            "Unordered - no sorting",
        ]
    ),

    "stack": CppFeatureDetail(
        name="std::stack",
        version="C++98",
        description="LIFO stack container adapter",
        member_types=[
            ("value_type", "Container::value_type"),
            ("container_type", "Container (default: deque)"),
            ("size_type", "Container::size_type"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("top()", "Access top element", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("push(value)", "Insert at top", "O(1)"),
                MemberFunction("pop()", "Remove top element", "O(1)"),
                MemberFunction("emplace(args)", "Construct at top", "O(1)"),
            ],
        },
        notes=[
            "LIFO - last in, first out",
            "Default container: deque",
            "No iterators",
        ]
    ),

    "queue": CppFeatureDetail(
        name="std::queue",
        version="C++98",
        description="FIFO queue container adapter",
        member_types=[
            ("value_type", "Container::value_type"),
            ("container_type", "Container (default: deque)"),
            ("size_type", "Container::size_type"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("front()", "Access first element", "O(1)"),
                MemberFunction("back()", "Access last element", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("push(value)", "Insert at end", "O(1)"),
                MemberFunction("pop()", "Remove from front", "O(1)"),
                MemberFunction("emplace(args)", "Construct at end", "O(1)"),
            ],
        },
        notes=[
            "FIFO - first in, first out",
            "Default container: deque",
            "No iterators",
        ]
    ),

    "priority_queue": CppFeatureDetail(
        name="std::priority_queue",
        version="C++98",
        description="Heap-based priority queue",
        member_types=[
            ("value_type", "Container::value_type"),
            ("container_type", "Container (default: vector)"),
            ("size_type", "Container::size_type"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("top()", "Access highest priority element", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("push(value)", "Insert element", "O(log n)"),
                MemberFunction("pop()", "Remove top element", "O(log n)"),
                MemberFunction("emplace(args)", "Construct element", "O(log n)"),
            ],
        },
        notes=[
            "Max heap by default",
            "Default container: vector",
            "No iterators",
        ]
    ),

    "bitset": CppFeatureDetail(
        name="std::bitset",
        version="C++98",
        description="Fixed-size sequence of bits",
        member_types=[
            ("size_type", "size_t"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("operator[]", "Access bit", "O(1)"),
                MemberFunction("test(pos)", "Test bit value", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("size()", "Number of bits", "O(1)"),
                MemberFunction("count()", "Count set bits", "O(n)"),
            ],
            "Modifiers": [
                MemberFunction("set()", "Set all bits", "O(n)"),
                MemberFunction("set(pos)", "Set specific bit", "O(1)"),
                MemberFunction("reset()", "Clear all bits", "O(n)"),
                MemberFunction("flip()", "Flip all bits", "O(n)"),
            ],
            "Query": [
                MemberFunction("all()", "Check if all bits set", "O(n)"),
                MemberFunction("any()", "Check if any bit set", "O(n)"),
                MemberFunction("none()", "Check if no bits set", "O(n)"),
            ],
        },
        notes=[
            "Fixed size at compile time",
            "Efficient bit storage",
            "Supports bitwise operations",
        ]
    ),

    "span": CppFeatureDetail(
        name="std::span",
        version="C++20",
        description="Non-owning view over contiguous sequence",
        member_types=[
            ("value_type", "T"),
            ("size_type", "size_t"),
            ("pointer", "T*"),
            ("iterator", "Random access iterator"),
        ],
        member_functions={
            "Element Access": [
                MemberFunction("operator[]", "Access element", "O(1)"),
                MemberFunction("front()", "First element", "O(1)"),
                MemberFunction("back()", "Last element", "O(1)"),
                MemberFunction("data()", "Pointer to data", "O(1)"),
            ],
            "Iterators": [
                MemberFunction("begin(), end()", "Iterator to beginning/end", "O(1)"),
                MemberFunction("rbegin(), rend()", "Reverse iterator", "O(1)"),
            ],
            "Capacity": [
                MemberFunction("empty()", "Check if empty", "O(1)"),
                MemberFunction("size()", "Number of elements", "O(1)"),
            ],
            "Subviews": [
                MemberFunction("first(n)", "First n elements", "O(1)"),
                MemberFunction("last(n)", "Last n elements", "O(1)"),
                MemberFunction("subspan(off, count)", "Subview", "O(1)"),
            ],
        },
        notes=[
            "Non-owning view - doesn't manage memory",
            "Can view array, vector, or raw pointer",
            "Safer alternative to pointer + size",
        ]
    ),

    # ALGORITHMS
    "all_of": CppFeatureDetail(
        name="std::all_of",
        version="C++11",
        description="Checks if all elements in the range satisfy the given predicate",
        member_functions={
            "Signature": [
                MemberFunction("all_of(InputIterator first, InputIterator last, Predicate pred)", "Returns true if pred(*i) is true for every iterator i in [first, last)", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Predicate must be a callable type that accepts the value_type and returns convertible to bool",
            "Returns true if [first, last) is empty",
        ]
    ),

    "any_of": CppFeatureDetail(
        name="std::any_of",
        version="C++11",
        description="Checks if any element in the range satisfies the given predicate",
        member_functions={
            "Signature": [
                MemberFunction("any_of(first, last, pred)", "Sequential version: returns true if pred is true for any element in [first, last)", "O(n)"),
                MemberFunction("any_of(policy, first, last, pred)", "Parallel version (C++17): returns true if pred is true for any element in [first, last)", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator (ForwardIterator for parallel version)",
            "UnaryPredicate must be callable with the element type and convertible to bool",
            "Short-circuits on first true result",
        ]
    ),

    "none_of": CppFeatureDetail(
        name="std::none_of",
        version="C++11",
        description="Checks if none of the elements in a range satisfy the given predicate",
        member_functions={
            "Signature": [
                MemberFunction("none_of(first, last, pred)", "Returns true if pred is false for all elements in [first, last)", "O(n)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "UnaryPredicate must be callable with the value type and return convertible to bool",
            "Short-circuits on first true pred result",
        ]
    ),

    "for_each": CppFeatureDetail(
        name="std::for_each",
        version="C++98",
        description="Applies a function to each element in the range [first, last)",
        member_functions={
            "Signature": [
                MemberFunction("for_each(first, last, f)", "Applies function f to each dereferenced iterator in the range", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator",
            "Function f must be callable with the value type of the iterator",
            "In C++20, returns f (moved or copied); pre-C++20 returns void",
            "constexpr in C++20",
            "The order of application is the order of incrementing the iterator",
        ]
    ),

    "for_each_n": CppFeatureDetail(
        name="std::for_each_n",
        version="C++17",
        description="Applies a function object to the first n elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("for_each_n(first, n, f)", "Apply f to each element in [first, first + n)", "O(n)"),
            ],
        },
        notes=[
            "Requires InputIterator for first",
            "n must be a non-negative integer type",
            "Returns InputIterator advanced by n",
            "Function f must be callable with dereferenced InputIterator",
        ]
    ),

    "count": CppFeatureDetail(
        name="std::count",
        version="C++98",
        description="Counts the number of elements in the range equal to a specified value",
        member_functions={
            "Signature": [
                MemberFunction("count(InputIt first, InputIt last, const T& value)", "Counts elements equal to value using operator==", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator",
            "Element requirement: *first is EqualityComparable with T (supports == and !=",
            "Returns difference_type (ptrdiff_t); n is distance from first to last",
        ]
    ),

    "count_if": CppFeatureDetail(
        name="std::count_if",
        version="C++98",
        description="Counts elements in a range that satisfy a predicate",
        member_functions={
            "Signature": [
                MemberFunction("count_if(first, last, pred)", "Counts elements for which pred returns true", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator",
            "Predicate requirement: UnaryPredicate callable with iterator's value_type",
            "Returns the number of satisfying elements",
        ]
    ),

    "find": CppFeatureDetail(
        name="std::find",
        version="C++98",
        description="Finds the first element in a range equal to a given value using operator==",
        member_functions={
            "Signature": [
                MemberFunction("find(first, last, value)", "Returns iterator to first element equal to value, or last if not found", "O(n)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Compares elements using operator==",
            "Returns last if not found",
        ]
    ),

    "find_if": CppFeatureDetail(
        name="std::find_if",
        version="C++98",
        description="Finds the first element in a range that satisfies a predicate",
        member_functions={
            "Signature": [
                MemberFunction("find_if(first, last, pred)", "Returns iterator to first element satisfying pred", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator",
            "Predicate must be callable with element type",
            "Returns last if no element satisfies pred",
        ]
    ),

    "find_if_not": CppFeatureDetail(
        name="std::find_if_not",
        version="C++11",
        description="Finds the first element in a range that does not satisfy the given predicate",
        member_functions={
            "Signature": [
                MemberFunction("find_if_not(first, last, pred)", "Returns iterator to first element where pred(element) is false", "O(n)"),
            ],
        },
        notes=[
            "Iterator requirement: InputIterator",
            "UnaryPredicate: must be callable with an element and return convertible to bool",
            "Returns last if no such element is found",
        ]
    ),

    "find_end": CppFeatureDetail(
        name="std::find_end",
        version="C++98",
        description="Finds the last occurrence of a subsequence in a range",
        member_functions={
            "Signature": [
                MemberFunction("find_end(first1, last1, first2, last2)", "Find last occurrence of [first2, last2) in [first1, last1)", "O(S*(N-S+1)) where N=last1-first1, S=last2-first2"),
                MemberFunction("find_end(first1, last1, first2, last2, pred)", "Same as above with custom binary predicate", "O(S*(N-S+1))"),
            ],
        },
        notes=[
            "Requires ForwardIterator for both ranges",
            "Returns last1 if [first2, last2) is empty or not found",
            "Overlapping matches OK",
        ]
    ),

    "find_first_of": CppFeatureDetail(
        name="std::find_first_of",
        version="C++98",
        description="Searches for the first occurrence of any element from a set in a range",
        member_functions={
            "Signature": [
                MemberFunction("find_first_of(first1, last1, first2, last2)", "Find first element in [first1, last1) that equals any in [first2, last2)", "O((last1 - first1) * (last2 - first2))"),
                MemberFunction("find_first_of(first1, last1, first2, last2, pred)", "Same with custom binary predicate", "O((last1 - first1) * (last2 - first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for first range, ForwardIterator for second",
            "Returns last1 if no match found",
            "Default uses operator==",
        ]
    ),

    "adjacent_find": CppFeatureDetail(
        name="std::adjacent_find",
        version="C++98",
        description="Finds the first occurrence of two consecutive equal elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("adjacent_find(first, last)", "Uses operator== to compare elements", "O(last - first)"),
                MemberFunction("adjacent_find(first, last, pred)", "Uses binary predicate to compare elements", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns iterator to the first of the pair, or last if none found",
            "Binary predicate must be callable with two arguments of the value_type",
        ]
    ),

    "search": CppFeatureDetail(
        name="std::search",
        version="C++98",
        description="Searches for the first occurrence of a subsequence within a range",
        member_functions={
            "Signature": [
                MemberFunction("search(first1, last1, first2, last2)", "Find first occurrence of [first2, last2) in [first1, last1)", "O((last1-first1)*(last2-first2))"),
                MemberFunction("search(first1, last1, first2, last2, pred)", "Same, with custom binary predicate", "O((last1-first1)*(last2-first2))"),
                MemberFunction("search(first, last, searcher)", "Use custom searcher object (C++17)", "Depends on searcher"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns last1 if [first2, last2) is empty or not found",
            "boyer_moore_searcher and boyer_moore_horspool_searcher available in C++17",
        ]
    ),

    "search_n": CppFeatureDetail(
        name="std::search_n",
        version="C++98",
        description="Searches for a sequence of n consecutive elements all equal to a given value",
        member_functions={
            "Signature": [
                MemberFunction("search_n(first, last, count, value)", "Search for count consecutive elements equal to value", "O(last - first)"),
                MemberFunction("search_n(first, last, count, value, pred)", "Same with custom binary predicate", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns iterator to beginning of the found sequence, or last if not found",
            "If count is zero or negative, returns first",
        ]
    ),

    "mismatch": CppFeatureDetail(
        name="std::mismatch",
        version="C++98",
        description="Finds the first position where two ranges differ",
        member_functions={
            "Signature": [
                MemberFunction("mismatch(first1, last1, first2)", "Returns pair of iterators to first mismatch", "O(last1 - first1)"),
                MemberFunction("mismatch(first1, last1, first2, last2)", "C++14: checks both ranges are same length", "O(min(last1-first1, last2-first2))"),
                MemberFunction("mismatch(first1, last1, first2, pred)", "Uses binary predicate", "O(last1 - first1)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Returns std::pair<InputIt1, InputIt2>",
            "If ranges match completely, returns (last1, first2 + (last1 - first1))",
        ]
    ),

    "copy": CppFeatureDetail(
        name="std::copy",
        version="C++98",
        description="Copies elements from one range to another",
        member_functions={
            "Signature": [
                MemberFunction("copy(first, last, d_first)", "Copy [first, last) to destination starting at d_first", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Destination must have enough space",
            "Returns iterator to element past the last copied element in destination",
            "For potentially overlapping ranges, use std::copy_backward or std::move",
        ]
    ),

    "copy_if": CppFeatureDetail(
        name="std::copy_if",
        version="C++11",
        description="Copies elements that satisfy a predicate from one range to another",
        member_functions={
            "Signature": [
                MemberFunction("copy_if(first, last, d_first, pred)", "Copies elements where pred returns true", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Predicate must be callable with element type",
            "Returns iterator to destination end",
        ]
    ),

    "copy_n": CppFeatureDetail(
        name="std::copy_n",
        version="C++11",
        description="Copies exactly n elements from one range to another",
        member_functions={
            "Signature": [
                MemberFunction("copy_n(first, count, result)", "Copy count elements from first to result", "O(count)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "If count is negative or zero, no copy occurs",
            "Returns iterator to destination past the last copied element",
        ]
    ),

    "copy_backward": CppFeatureDetail(
        name="std::copy_backward",
        version="C++98",
        description="Copies elements from one range to another in reverse order",
        member_functions={
            "Signature": [
                MemberFunction("copy_backward(first, last, d_last)", "Copies [first, last) to [d_last - (last-first), d_last) in reverse order", "O(last - first)"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator",
            "d_last is one past the end of the destination",
            "Safe for overlapping ranges where d_last is within [first, last)",
            "Returns iterator to the last element copied (d_last - (last - first))",
        ]
    ),

    "move": CppFeatureDetail(
        name="std::move",
        version="C++11",
        description="Moves elements from one range to another",
        member_functions={
            "Signature": [
                MemberFunction("move(first, last, d_first)", "Move elements using move semantics", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Elements in source range are left in valid but unspecified state",
            "Returns iterator to past-the-end of destination range",
            "More efficient than copy for move-assignable types",
        ]
    ),

    "move_backward": CppFeatureDetail(
        name="std::move_backward",
        version="C++11",
        description="Moves elements from one range to another in reverse order",
        member_functions={
            "Signature": [
                MemberFunction("move_backward(first, last, d_last)", "Moves [first, last) to destination ending at d_last, in reverse", "O(last - first)"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator",
            "Source elements left in valid but unspecified state",
            "Safe for overlapping ranges where d_last is in [first, last)",
            "Returns iterator to last element moved (d_last - (last-first))",
        ]
    ),

    "fill": CppFeatureDetail(
        name="std::fill",
        version="C++98",
        description="Assigns a given value to all elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("fill(first, last, value)", "Assigns value to each element in [first, last)", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Value type must be assignable to iterator's value_type",
            "constexpr in C++20",
        ]
    ),

    "fill_n": CppFeatureDetail(
        name="std::fill_n",
        version="C++98",
        description="Assigns a value to the first n elements of a range",
        member_functions={
            "Signature": [
                MemberFunction("fill_n(first, count, value)", "Assigns value to first count elements starting at first", "O(count)"),
            ],
        },
        notes=[
            "Requires OutputIterator",
            "Returns iterator to element past the last assigned element",
            "If count <= 0, no assignment occurs",
            "constexpr in C++20",
        ]
    ),

    "transform": CppFeatureDetail(
        name="std::transform",
        version="C++98",
        description="Applies a function to a range and stores the result in another range",
        member_functions={
            "Signature": [
                MemberFunction("transform(first, last, d_first, unary_op)", "Apply unary_op to each element", "O(last - first)"),
                MemberFunction("transform(first1, last1, first2, d_first, binary_op)", "Apply binary_op to pairs of elements from two ranges", "O(last1 - first1)"),
            ],
        },
        notes=[
            "Requires InputIterator for source(s), OutputIterator for destination",
            "Can use same range as source and destination for in-place transformation",
            "unary_op/binary_op must be callable with appropriate arguments",
            "constexpr in C++20",
        ]
    ),

    "generate": CppFeatureDetail(
        name="std::generate",
        version="C++98",
        description="Assigns values generated by a function to elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("generate(first, last, gen)", "Assigns result of gen() to each element in [first, last)", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Generator must be a callable with no arguments",
            "Generator return type must be assignable to iterator's value_type",
            "constexpr in C++20",
        ]
    ),

    "generate_n": CppFeatureDetail(
        name="std::generate_n",
        version="C++98",
        description="Assigns values generated by a function to the first n elements of a range",
        member_functions={
            "Signature": [
                MemberFunction("generate_n(first, count, gen)", "Assigns gen() to first count elements starting at first", "O(count)"),
            ],
        },
        notes=[
            "Requires OutputIterator",
            "Returns iterator to element past the last assigned one",
            "If count <= 0, no assignment occurs",
            "constexpr in C++20",
        ]
    ),

    "remove": CppFeatureDetail(
        name="std::remove",
        version="C++98",
        description="Removes all elements equal to a given value from a range",
        member_functions={
            "Signature": [
                MemberFunction("remove(first, last, value)", "Logical removal: moves non-matching elements to front, returns new end", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Does not change container size - use erase-remove idiom",
            "Returns iterator to new logical end",
            "Relative order of remaining elements preserved",
        ]
    ),

    "remove_if": CppFeatureDetail(
        name="std::remove_if",
        version="C++98",
        description="Removes all elements satisfying a predicate from a range",
        member_functions={
            "Signature": [
                MemberFunction("remove_if(first, last, pred)", "Logical removal: moves elements where pred is false to front", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Use erase-remove idiom to actually remove elements",
            "Returns iterator to new logical end",
            "Predicate called exactly last - first times",
        ]
    ),

    "remove_copy": CppFeatureDetail(
        name="std::remove_copy",
        version="C++98",
        description="Copies elements from a range to another, excluding those equal to a value",
        member_functions={
            "Signature": [
                MemberFunction("remove_copy(first, last, d_first, value)", "Copies elements not equal to value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Returns iterator to end of copied range",
            "Does not modify source range",
        ]
    ),

    "remove_copy_if": CppFeatureDetail(
        name="std::remove_copy_if",
        version="C++98",
        description="Copies elements from a range, excluding those that satisfy a predicate",
        member_functions={
            "Signature": [
                MemberFunction("remove_copy_if(first, last, d_first, pred)", "Copies elements where pred is false", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Returns iterator to end of destination range",
            "Does not modify source",
        ]
    ),

    "replace": CppFeatureDetail(
        name="std::replace",
        version="C++98",
        description="Replaces all occurrences of a value in a range with another value",
        member_functions={
            "Signature": [
                MemberFunction("replace(first, last, old_value, new_value)", "Replaces all elements equal to old_value with new_value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Uses operator== for comparison",
            "Modifies range in-place",
            "constexpr in C++20",
        ]
    ),

    "replace_if": CppFeatureDetail(
        name="std::replace_if",
        version="C++98",
        description="Replaces elements satisfying a predicate with a given value",
        member_functions={
            "Signature": [
                MemberFunction("replace_if(first, last, pred, new_value)", "Replaces elements where pred is true with new_value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Predicate must be callable with element type",
            "Modifies range in-place",
            "constexpr in C++20",
        ]
    ),

    "replace_copy": CppFeatureDetail(
        name="std::replace_copy",
        version="C++98",
        description="Copies a range, replacing all occurrences of a value with another",
        member_functions={
            "Signature": [
                MemberFunction("replace_copy(first, last, d_first, old_value, new_value)", "Copies range, replacing old_value with new_value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Does not modify source range",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "replace_copy_if": CppFeatureDetail(
        name="std::replace_copy_if",
        version="C++98",
        description="Copies a range, replacing elements satisfying a predicate",
        member_functions={
            "Signature": [
                MemberFunction("replace_copy_if(first, last, d_first, pred, new_value)", "Copies range, replacing where pred is true with new_value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Does not modify source",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "swap": CppFeatureDetail(
        name="std::swap",
        version="C++98",
        description="Exchanges the values of two objects",
        member_functions={
            "Signature": [
                MemberFunction("swap(a, b)", "Swaps values of a and b", "O(1) for most types"),
            ],
        },
        notes=[
            "Works with most types that are MoveConstructible and MoveAssignable",
            "Specialized for many standard library types for O(1) complexity",
            "constexpr in C++20",
            "noexcept when move construction and assignment are noexcept",
        ]
    ),

    "swap_ranges": CppFeatureDetail(
        name="std::swap_ranges",
        version="C++98",
        description="Exchanges elements between two ranges",
        member_functions={
            "Signature": [
                MemberFunction("swap_ranges(first1, last1, first2)", "Swaps elements in [first1, last1) with those starting at first2", "O(last1 - first1)"),
            ],
        },
        notes=[
            "Requires ForwardIterator for both ranges",
            "Both ranges must have same length",
            "Returns iterator to element past last swapped in second range",
            "constexpr in C++20",
        ]
    ),

    "iter_swap": CppFeatureDetail(
        name="std::iter_swap",
        version="C++98",
        description="Swaps the values pointed to by two iterators",
        member_functions={
            "Signature": [
                MemberFunction("iter_swap(a, b)", "Swaps *a and *b", "O(1)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Effectively performs swap(*a, *b)",
            "constexpr in C++20",
        ]
    ),

    "reverse": CppFeatureDetail(
        name="std::reverse",
        version="C++98",
        description="Reverses the order of elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("reverse(first, last)", "Reverses elements in [first, last)", "O((last - first) / 2)"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator",
            "Modifies range in-place",
            "constexpr in C++20",
        ]
    ),

    "reverse_copy": CppFeatureDetail(
        name="std::reverse_copy",
        version="C++98",
        description="Copies a range in reverse order to another location",
        member_functions={
            "Signature": [
                MemberFunction("reverse_copy(first, last, d_first)", "Copies [first, last) reversed to d_first", "O(last - first)"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator for source, OutputIterator for destination",
            "Does not modify source",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "rotate": CppFeatureDetail(
        name="std::rotate",
        version="C++98",
        description="Rotates the elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("rotate(first, middle, last)", "Rotates so that middle becomes the first element", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Element at middle becomes new first element",
            "Returns iterator to element originally at first",
            "constexpr in C++20",
        ]
    ),

    "rotate_copy": CppFeatureDetail(
        name="std::rotate_copy",
        version="C++98",
        description="Copies a rotated range to another location",
        member_functions={
            "Signature": [
                MemberFunction("rotate_copy(first, middle, last, d_first)", "Copies rotated [first, last) to d_first", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator for source, OutputIterator for destination",
            "Does not modify source",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "shuffle": CppFeatureDetail(
        name="std::shuffle",
        version="C++11",
        description="Randomly reorders elements in a range using a random number generator",
        member_functions={
            "Signature": [
                MemberFunction("shuffle(first, last, g)", "Randomly permutes elements using URNG g", "O(last - first)"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "g must satisfy UniformRandomBitGenerator requirements",
            "All permutations equally likely",
            "Replaces std::random_shuffle (deprecated in C++14, removed in C++17)",
        ]
    ),

    "sample": CppFeatureDetail(
        name="std::sample",
        version="C++17",
        description="Selects n random elements from a range",
        member_functions={
            "Signature": [
                MemberFunction("sample(first, last, out, n, g)", "Selects n elements and writes to out using URNG g", "O(n) for forward iterators, O(last-first) for input iterators"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination, UniformRandomBitGenerator for g",
            "If n >= distance(first, last), copies all elements",
            "Returns iterator to one past last written element",
        ]
    ),

    "unique": CppFeatureDetail(
        name="std::unique",
        version="C++98",
        description="Removes consecutive duplicate elements from a range",
        member_functions={
            "Signature": [
                MemberFunction("unique(first, last)", "Remove consecutive duplicates using operator==", "O(last - first)"),
                MemberFunction("unique(first, last, pred)", "Remove consecutive duplicates using binary predicate", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Does not change container size - use erase-unique idiom",
            "Returns iterator to new logical end",
            "To remove all duplicates, sort first",
        ]
    ),

    "unique_copy": CppFeatureDetail(
        name="std::unique_copy",
        version="C++98",
        description="Copies a range, removing consecutive duplicates",
        member_functions={
            "Signature": [
                MemberFunction("unique_copy(first, last, d_first)", "Copies range excluding consecutive duplicates", "O(last - first)"),
                MemberFunction("unique_copy(first, last, d_first, pred)", "Same with binary predicate", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "Does not modify source",
            "Returns iterator to end of destination",
        ]
    ),

    "partition": CppFeatureDetail(
        name="std::partition",
        version="C++98",
        description="Reorders elements so that those satisfying a predicate come first",
        member_functions={
            "Signature": [
                MemberFunction("partition(first, last, pred)", "Partition based on pred", "O(last - first)"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator (ForwardIterator if non-stable)",
            "Returns iterator to first element of second partition",
            "Not stable - use stable_partition for stability",
            "Exactly last - first applications of pred",
        ]
    ),

    "stable_partition": CppFeatureDetail(
        name="std::stable_partition",
        version="C++98",
        description="Partitions a range while preserving relative order",
        member_functions={
            "Signature": [
                MemberFunction("stable_partition(first, last, pred)", "Stable partition based on pred", "O(n log n) if insufficient memory, O(n) with extra memory"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator",
            "Preserves relative order within each partition",
            "Returns iterator to first element of second partition",
        ]
    ),

    "partition_copy": CppFeatureDetail(
        name="std::partition_copy",
        version="C++11",
        description="Copies a range partitioned into two separate outputs",
        member_functions={
            "Signature": [
                MemberFunction("partition_copy(first, last, d_first_true, d_first_false, pred)", "Copies elements to two destinations based on pred", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for both destinations",
            "Returns std::pair of iterators to ends of both output ranges",
            "Does not modify source",
        ]
    ),

    "is_partitioned": CppFeatureDetail(
        name="std::is_partitioned",
        version="C++11",
        description="Checks if a range is partitioned by a predicate",
        member_functions={
            "Signature": [
                MemberFunction("is_partitioned(first, last, pred)", "Returns true if all elements satisfying pred appear before those that don't", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Returns true for empty ranges",
            "At most last - first applications of pred",
        ]
    ),

    "partition_point": CppFeatureDetail(
        name="std::partition_point",
        version="C++11",
        description="Finds the partition point in a partitioned range",
        member_functions={
            "Signature": [
                MemberFunction("partition_point(first, last, pred)", "Returns iterator to first element of second partition", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Range must already be partitioned by pred",
            "Uses binary search",
            "Undefined behavior if range not partitioned",
        ]
    ),

    "sort": CppFeatureDetail(
        name="std::sort",
        version="C++98",
        description="Sorts elements in a range in ascending order",
        member_functions={
            "Signature": [
                MemberFunction("sort(first, last)", "Sorts using operator<", "O(n log n)"),
                MemberFunction("sort(first, last, comp)", "Sorts using custom comparator", "O(n log n)"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Not stable - use stable_sort for stability",
            "Typically uses introsort (quicksort + heapsort + insertion sort)",
            "constexpr in C++20",
        ]
    ),

    "stable_sort": CppFeatureDetail(
        name="std::stable_sort",
        version="C++98",
        description="Sorts elements in a range while preserving relative order of equal elements",
        member_functions={
            "Signature": [
                MemberFunction("stable_sort(first, last)", "Stable sort using operator<", "O(n log^2 n) worst case, O(n log n) if extra memory available"),
                MemberFunction("stable_sort(first, last, comp)", "Stable sort with custom comparator", "O(n log^2 n) worst case, O(n log n) if extra memory available"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Preserves relative order of equivalent elements",
            "Typically uses merge sort",
        ]
    ),

    "partial_sort": CppFeatureDetail(
        name="std::partial_sort",
        version="C++98",
        description="Sorts the first N elements of a range",
        member_functions={
            "Signature": [
                MemberFunction("partial_sort(first, middle, last)", "Sorts [first, middle), rest unspecified order", "O((last-first) log(middle-first))"),
                MemberFunction("partial_sort(first, middle, last, comp)", "Same with custom comparator", "O((last-first) log(middle-first))"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Elements in [middle, last) are in unspecified order",
            "Typically uses heapsort",
        ]
    ),

    "partial_sort_copy": CppFeatureDetail(
        name="std::partial_sort_copy",
        version="C++98",
        description="Copies the smallest N elements from a range, sorted",
        member_functions={
            "Signature": [
                MemberFunction("partial_sort_copy(first, last, d_first, d_last)", "Copies sorted smallest elements", "O((last-first) log(min(last-first, d_last-d_first)))"),
                MemberFunction("partial_sort_copy(first, last, d_first, d_last, comp)", "Same with custom comparator", "O((last-first) log(min(last-first, d_last-d_first)))"),
            ],
        },
        notes=[
            "Requires InputIterator for source, RandomAccessIterator for destination",
            "Number of elements copied is min(last-first, d_last-d_first)",
            "Does not modify source",
        ]
    ),

    "is_sorted": CppFeatureDetail(
        name="std::is_sorted",
        version="C++11",
        description="Checks if a range is sorted in non-descending order",
        member_functions={
            "Signature": [
                MemberFunction("is_sorted(first, last)", "Checks if sorted using operator<", "O(last - first)"),
                MemberFunction("is_sorted(first, last, comp)", "Checks if sorted using custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns true for ranges with < 2 elements",
            "constexpr in C++20",
        ]
    ),

    "is_sorted_until": CppFeatureDetail(
        name="std::is_sorted_until",
        version="C++11",
        description="Finds the largest sorted subrange at the beginning of a range",
        member_functions={
            "Signature": [
                MemberFunction("is_sorted_until(first, last)", "Returns iterator to first unsorted element", "O(last - first)"),
                MemberFunction("is_sorted_until(first, last, comp)", "Same with custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns last if entire range is sorted",
            "constexpr in C++20",
        ]
    ),

    "nth_element": CppFeatureDetail(
        name="std::nth_element",
        version="C++98",
        description="Partially sorts a range so that the nth element is in its sorted position",
        member_functions={
            "Signature": [
                MemberFunction("nth_element(first, nth, last)", "Partitions around nth element", "O(last - first) average"),
                MemberFunction("nth_element(first, nth, last, comp)", "Same with custom comparator", "O(last - first) average"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Element at nth is the element that would be there if range were sorted",
            "All elements before nth are <= *nth, all after are >= *nth",
            "Typically uses introselect (quickselect + heapselect)",
        ]
    ),

    "binary_search": CppFeatureDetail(
        name="std::binary_search",
        version="C++98",
        description="Checks if a value exists in a sorted range",
        member_functions={
            "Signature": [
                MemberFunction("binary_search(first, last, value)", "Returns true if value found", "O(log(last - first))"),
                MemberFunction("binary_search(first, last, value, comp)", "Same with custom comparator", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Range must be sorted (or partitioned w.r.t. value)",
            "Does not return position - use lower_bound/upper_bound for that",
            "constexpr in C++20",
        ]
    ),

    "lower_bound": CppFeatureDetail(
        name="std::lower_bound",
        version="C++98",
        description="Finds the first element not less than a given value in a sorted range",
        member_functions={
            "Signature": [
                MemberFunction("lower_bound(first, last, value)", "Returns iterator to first element >= value", "O(log(last - first))"),
                MemberFunction("lower_bound(first, last, value, comp)", "Same with custom comparator", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Range must be sorted",
            "Returns last if all elements < value",
            "constexpr in C++20",
        ]
    ),

    "upper_bound": CppFeatureDetail(
        name="std::upper_bound",
        version="C++98",
        description="Finds the first element greater than a given value in a sorted range",
        member_functions={
            "Signature": [
                MemberFunction("upper_bound(first, last, value)", "Returns iterator to first element > value", "O(log(last - first))"),
                MemberFunction("upper_bound(first, last, value, comp)", "Same with custom comparator", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Range must be sorted",
            "Returns last if all elements <= value",
            "constexpr in C++20",
        ]
    ),

    "equal_range": CppFeatureDetail(
        name="std::equal_range",
        version="C++98",
        description="Finds the range of elements equal to a given value in a sorted range",
        member_functions={
            "Signature": [
                MemberFunction("equal_range(first, last, value)", "Returns pair of iterators [lower_bound, upper_bound)", "O(log(last - first))"),
                MemberFunction("equal_range(first, last, value, comp)", "Same with custom comparator", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Range must be sorted",
            "Returns std::pair<ForwardIt, ForwardIt>",
            "If value not found, both iterators point to first element > value",
            "constexpr in C++20",
        ]
    ),

    "merge": CppFeatureDetail(
        name="std::merge",
        version="C++98",
        description="Merges two sorted ranges into one sorted range",
        member_functions={
            "Signature": [
                MemberFunction("merge(first1, last1, first2, last2, d_first)", "Merge using operator<", "O((last1-first1) + (last2-first2))"),
                MemberFunction("merge(first1, last1, first2, last2, d_first, comp)", "Merge with custom comparator", "O((last1-first1) + (last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for sources, OutputIterator for destination",
            "Both input ranges must be sorted",
            "Stable merge",
            "constexpr in C++20",
        ]
    ),

    "inplace_merge": CppFeatureDetail(
        name="std::inplace_merge",
        version="C++98",
        description="Merges two consecutive sorted ranges in-place",
        member_functions={
            "Signature": [
                MemberFunction("inplace_merge(first, middle, last)", "Merges [first, middle) and [middle, last) in-place", "O(n log n) if insufficient memory, O(n) with extra memory"),
                MemberFunction("inplace_merge(first, middle, last, comp)", "Same with custom comparator", "O(n log n) if insufficient memory, O(n) with extra memory"),
            ],
        },
        notes=[
            "Requires BidirectionalIterator",
            "Both [first, middle) and [middle, last) must be sorted",
            "Stable merge",
        ]
    ),

    "includes": CppFeatureDetail(
        name="std::includes",
        version="C++98",
        description="Checks if one sorted range includes all elements of another",
        member_functions={
            "Signature": [
                MemberFunction("includes(first1, last1, first2, last2)", "Returns true if [first2, last2) ⊆ [first1, last1)", "O(2*(last1-first1 + last2-first2))"),
                MemberFunction("includes(first1, last1, first2, last2, comp)", "Same with custom comparator", "O(2*(last1-first1 + last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Both ranges must be sorted",
            "Returns true if second range is subset of first (with multiplicity)",
            "constexpr in C++20",
        ]
    ),

    "set_difference": CppFeatureDetail(
        name="std::set_difference",
        version="C++98",
        description="Computes the difference of two sorted ranges",
        member_functions={
            "Signature": [
                MemberFunction("set_difference(first1, last1, first2, last2, d_first)", "A \\ B: elements in first but not in second", "O(2*(last1-first1 + last2-first2))"),
                MemberFunction("set_difference(first1, last1, first2, last2, d_first, comp)", "Same with custom comparator", "O(2*(last1-first1 + last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for sources, OutputIterator for destination",
            "Both input ranges must be sorted",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "set_intersection": CppFeatureDetail(
        name="std::set_intersection",
        version="C++98",
        description="Computes the intersection of two sorted ranges",
        member_functions={
            "Signature": [
                MemberFunction("set_intersection(first1, last1, first2, last2, d_first)", "A ∩ B: elements in both ranges", "O(2*(last1-first1 + last2-first2))"),
                MemberFunction("set_intersection(first1, last1, first2, last2, d_first, comp)", "Same with custom comparator", "O(2*(last1-first1 + last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for sources, OutputIterator for destination",
            "Both input ranges must be sorted",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "set_symmetric_difference": CppFeatureDetail(
        name="std::set_symmetric_difference",
        version="C++98",
        description="Computes the symmetric difference of two sorted ranges",
        member_functions={
            "Signature": [
                MemberFunction("set_symmetric_difference(first1, last1, first2, last2, d_first)", "A △ B: elements in either but not both", "O(2*(last1-first1 + last2-first2))"),
                MemberFunction("set_symmetric_difference(first1, last1, first2, last2, d_first, comp)", "Same with custom comparator", "O(2*(last1-first1 + last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for sources, OutputIterator for destination",
            "Both input ranges must be sorted",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "set_union": CppFeatureDetail(
        name="std::set_union",
        version="C++98",
        description="Computes the union of two sorted ranges",
        member_functions={
            "Signature": [
                MemberFunction("set_union(first1, last1, first2, last2, d_first)", "A ∪ B: all elements from both ranges", "O(2*(last1-first1 + last2-first2))"),
                MemberFunction("set_union(first1, last1, first2, last2, d_first, comp)", "Same with custom comparator", "O(2*(last1-first1 + last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator for sources, OutputIterator for destination",
            "Both input ranges must be sorted",
            "Returns iterator to end of destination",
            "constexpr in C++20",
        ]
    ),

    "make_heap": CppFeatureDetail(
        name="std::make_heap",
        version="C++98",
        description="Constructs a max heap from a range",
        member_functions={
            "Signature": [
                MemberFunction("make_heap(first, last)", "Builds max heap using operator<", "O(3*(last - first))"),
                MemberFunction("make_heap(first, last, comp)", "Builds heap with custom comparator", "O(3*(last - first))"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Creates max heap by default (largest element first)",
            "Use std::greater<> for min heap",
            "constexpr in C++20",
        ]
    ),

    "push_heap": CppFeatureDetail(
        name="std::push_heap",
        version="C++98",
        description="Inserts an element into a max heap",
        member_functions={
            "Signature": [
                MemberFunction("push_heap(first, last)", "Inserts element at last-1 into heap [first, last-1)", "O(log(last - first))"),
                MemberFunction("push_heap(first, last, comp)", "Same with custom comparator", "O(log(last - first))"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Range [first, last-1) must already be a heap",
            "New element should be at position last-1",
            "constexpr in C++20",
        ]
    ),

    "pop_heap": CppFeatureDetail(
        name="std::pop_heap",
        version="C++98",
        description="Removes the largest element from a max heap",
        member_functions={
            "Signature": [
                MemberFunction("pop_heap(first, last)", "Moves largest element to last-1, maintains heap [first, last-1)", "O(2*log(last - first))"),
                MemberFunction("pop_heap(first, last, comp)", "Same with custom comparator", "O(2*log(last - first))"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Range [first, last) must be a heap",
            "After call, largest element at last-1, heap is [first, last-1)",
            "constexpr in C++20",
        ]
    ),

    "sort_heap": CppFeatureDetail(
        name="std::sort_heap",
        version="C++98",
        description="Sorts elements in a max heap",
        member_functions={
            "Signature": [
                MemberFunction("sort_heap(first, last)", "Sorts heap in ascending order", "O(n log n) where n = last - first"),
                MemberFunction("sort_heap(first, last, comp)", "Same with custom comparator", "O(n log n)"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Range must be a heap",
            "After call, range is sorted and no longer a heap",
            "constexpr in C++20",
        ]
    ),

    "is_heap": CppFeatureDetail(
        name="std::is_heap",
        version="C++11",
        description="Checks if a range is a max heap",
        member_functions={
            "Signature": [
                MemberFunction("is_heap(first, last)", "Returns true if range is max heap", "O(last - first)"),
                MemberFunction("is_heap(first, last, comp)", "Same with custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Returns true for empty range or single element",
            "constexpr in C++20",
        ]
    ),

    "is_heap_until": CppFeatureDetail(
        name="std::is_heap_until",
        version="C++11",
        description="Finds the largest subrange that is a max heap",
        member_functions={
            "Signature": [
                MemberFunction("is_heap_until(first, last)", "Returns iterator to first element not in heap", "O(last - first)"),
                MemberFunction("is_heap_until(first, last, comp)", "Same with custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires RandomAccessIterator",
            "Returns last if entire range is a heap",
            "constexpr in C++20",
        ]
    ),

    "min": CppFeatureDetail(
        name="std::min",
        version="C++98",
        description="Returns the smaller of two values",
        member_functions={
            "Signature": [
                MemberFunction("min(a, b)", "Returns smaller value using operator<", "O(1)"),
                MemberFunction("min(a, b, comp)", "Returns smaller value using comparator", "O(1)"),
                MemberFunction("min(ilist)", "Returns smallest value in initializer_list (C++11)", "O(n)"),
            ],
        },
        notes=[
            "If values equivalent, returns first argument",
            "constexpr in C++14",
            "noexcept in appropriate cases",
        ]
    ),

    "max": CppFeatureDetail(
        name="std::max",
        version="C++98",
        description="Returns the larger of two values",
        member_functions={
            "Signature": [
                MemberFunction("max(a, b)", "Returns larger value using operator<", "O(1)"),
                MemberFunction("max(a, b, comp)", "Returns larger value using comparator", "O(1)"),
                MemberFunction("max(ilist)", "Returns largest value in initializer_list (C++11)", "O(n)"),
            ],
        },
        notes=[
            "If values equivalent, returns first argument",
            "constexpr in C++14",
            "noexcept in appropriate cases",
        ]
    ),

    "minmax": CppFeatureDetail(
        name="std::minmax",
        version="C++11",
        description="Returns both the smallest and largest of two or more values",
        member_functions={
            "Signature": [
                MemberFunction("minmax(a, b)", "Returns pair {min, max} using operator<", "O(1)"),
                MemberFunction("minmax(a, b, comp)", "Same with custom comparator", "O(1)"),
                MemberFunction("minmax(ilist)", "Returns pair from initializer_list", "O(n)"),
            ],
        },
        notes=[
            "Returns std::pair<T, T>",
            "constexpr in C++14",
            "More efficient than separate min and max calls",
        ]
    ),

    "min_element": CppFeatureDetail(
        name="std::min_element",
        version="C++98",
        description="Finds the smallest element in a range",
        member_functions={
            "Signature": [
                MemberFunction("min_element(first, last)", "Returns iterator to smallest element", "O(last - first)"),
                MemberFunction("min_element(first, last, comp)", "Same with custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns first if multiple minimums exist",
            "Returns last for empty range",
            "constexpr in C++17",
        ]
    ),

    "max_element": CppFeatureDetail(
        name="std::max_element",
        version="C++98",
        description="Finds the largest element in a range",
        member_functions={
            "Signature": [
                MemberFunction("max_element(first, last)", "Returns iterator to largest element", "O(last - first)"),
                MemberFunction("max_element(first, last, comp)", "Same with custom comparator", "O(last - first)"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns first if multiple maximums exist",
            "Returns last for empty range",
            "constexpr in C++17",
        ]
    ),

    "minmax_element": CppFeatureDetail(
        name="std::minmax_element",
        version="C++11",
        description="Finds both the smallest and largest elements in a range",
        member_functions={
            "Signature": [
                MemberFunction("minmax_element(first, last)", "Returns pair of iterators {min, max}", "O(3/2 * (last - first))"),
                MemberFunction("minmax_element(first, last, comp)", "Same with custom comparator", "O(3/2 * (last - first))"),
            ],
        },
        notes=[
            "Requires ForwardIterator",
            "Returns std::pair<ForwardIt, ForwardIt>",
            "More efficient than separate min_element and max_element",
            "constexpr in C++17",
        ]
    ),

    "clamp": CppFeatureDetail(
        name="std::clamp",
        version="C++17",
        description="Clamps a value between a minimum and maximum",
        member_functions={
            "Signature": [
                MemberFunction("clamp(v, lo, hi)", "Returns value clamped to [lo, hi]", "O(1)"),
                MemberFunction("clamp(v, lo, hi, comp)", "Same with custom comparator", "O(1)"),
            ],
        },
        notes=[
            "Returns lo if v < lo, hi if v > hi, otherwise v",
            "Undefined behavior if lo > hi",
            "constexpr and noexcept",
        ]
    ),

    "equal": CppFeatureDetail(
        name="std::equal",
        version="C++98",
        description="Checks if two ranges contain equal elements",
        member_functions={
            "Signature": [
                MemberFunction("equal(first1, last1, first2)", "Compares using operator==", "O(last1 - first1)"),
                MemberFunction("equal(first1, last1, first2, last2)", "C++14: checks both ranges same length", "O(min(last1-first1, last2-first2))"),
                MemberFunction("equal(first1, last1, first2, pred)", "Uses binary predicate", "O(last1 - first1)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Short-circuits on first mismatch",
            "constexpr in C++20",
        ]
    ),

    "lexicographical_compare": CppFeatureDetail(
        name="std::lexicographical_compare",
        version="C++98",
        description="Checks if one range is lexicographically less than another",
        member_functions={
            "Signature": [
                MemberFunction("lexicographical_compare(first1, last1, first2, last2)", "Compare using operator<", "O(min(last1-first1, last2-first2))"),
                MemberFunction("lexicographical_compare(first1, last1, first2, last2, comp)", "Compare with custom comparator", "O(min(last1-first1, last2-first2))"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "Implements dictionary ordering",
            "Shorter range is less if all elements equal",
            "constexpr in C++20",
        ]
    ),

    "accumulate": CppFeatureDetail(
        name="std::accumulate",
        version="C++98",
        description="Computes the sum (or fold) of a range of elements",
        member_functions={
            "Signature": [
                MemberFunction("accumulate(first, last, init)", "Sum using operator+", "O(last - first)"),
                MemberFunction("accumulate(first, last, init, binary_op)", "Fold using custom binary operation", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "In <numeric> header",
            "Performs left fold: (...((init + *first) + *(first+1)) + ...)",
        ]
    ),

    "reduce": CppFeatureDetail(
        name="std::reduce",
        version="C++17",
        description="Computes the sum (or fold) of a range, potentially in parallel",
        member_functions={
            "Signature": [
                MemberFunction("reduce(first, last)", "Sum with init=0, using operator+", "O(last - first)"),
                MemberFunction("reduce(first, last, init)", "Sum with custom init", "O(last - first)"),
                MemberFunction("reduce(first, last, init, binary_op)", "Fold with custom operation", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "In <numeric> header",
            "Order of operations unspecified - operation must be associative and commutative",
            "Can be parallelized with execution policies",
        ]
    ),

    "transform_reduce": CppFeatureDetail(
        name="std::transform_reduce",
        version="C++17",
        description="Applies a transformation then reduces the result",
        member_functions={
            "Signature": [
                MemberFunction("transform_reduce(first1, last1, first2, init)", "Inner product: init + sum of (*i1) * (*i2)", "O(last1 - first1)"),
                MemberFunction("transform_reduce(first1, last1, first2, init, reduce_op, transform_op)", "Custom reduce and transform", "O(last1 - first1)"),
                MemberFunction("transform_reduce(first, last, init, reduce_op, unary_transform_op)", "Transform then reduce", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator",
            "In <numeric> header",
            "Can be parallelized",
            "Operations must be associative and commutative",
        ]
    ),

    "exclusive_scan": CppFeatureDetail(
        name="std::exclusive_scan",
        version="C++17",
        description="Computes an exclusive prefix sum",
        member_functions={
            "Signature": [
                MemberFunction("exclusive_scan(first, last, d_first, init)", "Exclusive scan with init and operator+", "O(last - first)"),
                MemberFunction("exclusive_scan(first, last, d_first, init, binary_op)", "Exclusive scan with custom operation", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "In <numeric> header",
            "Element i of output is sum of init and elements [0, i) of input",
            "First output element equals init",
        ]
    ),

    "inclusive_scan": CppFeatureDetail(
        name="std::inclusive_scan",
        version="C++17",
        description="Computes an inclusive prefix sum",
        member_functions={
            "Signature": [
                MemberFunction("inclusive_scan(first, last, d_first)", "Inclusive scan with operator+", "O(last - first)"),
                MemberFunction("inclusive_scan(first, last, d_first, binary_op)", "Inclusive scan with custom operation", "O(last - first)"),
                MemberFunction("inclusive_scan(first, last, d_first, binary_op, init)", "Inclusive scan with init", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "In <numeric> header",
            "Element i of output is sum of elements [0, i] of input",
        ]
    ),

    "transform_exclusive_scan": CppFeatureDetail(
        name="std::transform_exclusive_scan",
        version="C++17",
        description="Transforms elements then computes exclusive prefix sum",
        member_functions={
            "Signature": [
                MemberFunction("transform_exclusive_scan(first, last, d_first, init, binary_op, unary_op)", "Transform then exclusive scan", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "In <numeric> header",
            "Applies unary_op to each element before scanning",
        ]
    ),

    "transform_inclusive_scan": CppFeatureDetail(
        name="std::transform_inclusive_scan",
        version="C++17",
        description="Transforms elements then computes inclusive prefix sum",
        member_functions={
            "Signature": [
                MemberFunction("transform_inclusive_scan(first, last, d_first, binary_op, unary_op)", "Transform then inclusive scan", "O(last - first)"),
                MemberFunction("transform_inclusive_scan(first, last, d_first, binary_op, unary_op, init)", "Same with init value", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "In <numeric> header",
            "Applies unary_op to each element before scanning",
        ]
    ),

    "adjacent_difference": CppFeatureDetail(
        name="std::adjacent_difference",
        version="C++98",
        description="Computes differences between adjacent elements",
        member_functions={
            "Signature": [
                MemberFunction("adjacent_difference(first, last, d_first)", "Compute differences using operator-", "O(last - first)"),
                MemberFunction("adjacent_difference(first, last, d_first, binary_op)", "Compute with custom operation", "O(last - first)"),
            ],
        },
        notes=[
            "Requires InputIterator for source, OutputIterator for destination",
            "In <numeric> header",
            "First element copied unchanged, subsequent are differences",
            "Can be used in-place",
        ]
    ),

    "inner_product": CppFeatureDetail(
        name="std::inner_product",
        version="C++98",
        description="Computes the inner product of two ranges",
        member_functions={
            "Signature": [
                MemberFunction("inner_product(first1, last1, first2, init)", "Uses operator* for multiplication and operator+ for accumulation", "O(last1 - first1)"),
                MemberFunction("inner_product(first1, last1, first2, init, binary_op)", "Uses operator* for multiplication and custom binary_op for accumulation", "O(last1 - first1)"),
            ],
        },
        notes=[
            "Requires InputIterator for [first1, last1) and first2",
            "The value type must support the required arithmetic operations",
            "Advances first2 by the same distance as [first1, last1)",
        ]
    ),

    "gcd": CppFeatureDetail(
        name="std::gcd",
        version="C++17",
        description="Computes the greatest common divisor of two integers",
        member_functions={
            "Signature": [
                MemberFunction("gcd(m, n)", "Computes GCD using Euclidean algorithm", "O(log min(|m|, |n|))"),
            ],
        },
        notes=[
            "Requires M and N to be integer types (std::integral)",
            "Returns abs(m) if n == 0, abs(n) if m == 0, 0 if both 0",
            "Noexcept and constexpr",
        ]
    ),

    "lcm": CppFeatureDetail(
        name="std::lcm",
        version="C++17",
        description="Computes the least common multiple of two integer values",
        member_functions={
            "Signature": [
                MemberFunction("lcm(m, n)", "Computes LCM of m and n, where m and n are integers", "O(1)"),
            ],
        },
        notes=[
            "Requires integral types M and N",
            "Returns 0 if either m or n is 0",
            "Undefined behavior if the result cannot be represented in the return type (common_type_t<M,N>)",
            "No iterator requirements",
        ]
    ),

    # SMART POINTERS
    "unique_ptr": CppFeatureDetail(
        name="std::unique_ptr",
        version="C++11",
        description="Exclusive ownership smart pointer",
        member_functions={
            "Core Operations": [
                MemberFunction("get()", "Get raw pointer", "O(1)"),
                MemberFunction("release()", "Release ownership", "O(1)"),
                MemberFunction("reset(ptr)", "Replace managed object", "O(1)"),
                MemberFunction("operator*", "Dereference", "O(1)"),
                MemberFunction("operator->", "Member access", "O(1)"),
            ],
        },
        notes=[
            "Move-only (no copying)",
            "Automatic cleanup via RAII",
            "Zero overhead vs raw pointer",
        ]
    ),

    "shared_ptr": CppFeatureDetail(
        name="std::shared_ptr",
        version="C++11",
        description="Shared ownership smart pointer with reference counting",
        member_functions={
            "Core Operations": [
                MemberFunction("get()", "Get raw pointer", "O(1)"),
                MemberFunction("reset()", "Release reference", "O(1)"),
                MemberFunction("use_count()", "Get reference count", "O(1)"),
                MemberFunction("operator*", "Dereference", "O(1)"),
                MemberFunction("operator->", "Member access", "O(1)"),
            ],
        },
        notes=[
            "Thread-safe reference counting",
            "Use make_shared for efficiency",
            "Slightly more overhead than unique_ptr",
        ]
    ),

    "weak_ptr": CppFeatureDetail(
        name="std::weak_ptr",
        version="C++11",
        description="Non-owning 'weak' reference to an object managed by a std::shared_ptr",
        member_functions={
            "Observers": [
                MemberFunction("expired()", "Checks if the managed object has been deleted", "O(1)"),
                MemberFunction("use_count()", "Returns the number of shared_ptrs sharing ownership", "O(1)"),
                MemberFunction("lock()", "Creates a shared_ptr that manages the referenced object", "O(1)"),
            ],
            "Modifiers": [
                MemberFunction("reset()", "Releases the reference", "O(1)"),
                MemberFunction("swap(other)", "Swaps with another weak_ptr", "O(1)"),
            ],
        },
        notes=[
            "Prevents circular references between shared_ptr instances.",
            "Must be converted to shared_ptr via lock() to access the object.",
            "Does not affect the reference count of the managed object.",
        ]
    ),

    "make_unique": CppFeatureDetail(
        name="std::make_unique",
        version="C++14",
        description="Helper function to create a std::unique_ptr in a safe and efficient way.",
        member_functions={
            "Signature": [
                MemberFunction("make_unique<T>(args...)", "Constructs an object of type T and wraps it in a unique_ptr."),
            ],
        },
        notes=[
            "Provides exception safety by avoiding memory leaks in complex expressions.",
            "More concise than creating a unique_ptr with `new`.",
            "Added in C++14. For C++11, a custom implementation is often used.",
        ]
    ),

    "make_shared": CppFeatureDetail(
        name="std::make_shared",
        version="C++11",
        description="Helper function to create a std::shared_ptr in a safe and efficient way.",
        member_functions={
            "Signature": [
                MemberFunction("make_shared<T>(args...)", "Constructs an object of type T and wraps it in a shared_ptr."),
            ],
        },
        notes=[
            "More efficient than creating a shared_ptr with `new` because it can allocate the object and its control block in a single allocation.",
            "Provides exception safety.",
        ]
    ),

    # ITERATORS
    "iterator": CppFeatureDetail(
        name="iterator",
        version="C++98",
        description="Mutable iterator type",
        member_functions={
            "Operations": [
                MemberFunction("operator++", "Advance", "Varies by container"),
                MemberFunction("operator*", "Dereference", "O(1)"),
                MemberFunction("operator->", "Member access", "O(1)"),
            ],
        },
        notes=[
            "Category depends on container",
            "Allows modification of elements",
        ]
    ),

    "const_iterator": CppFeatureDetail(
        name="const_iterator",
        version="C++98",
        description="Constant iterator - read-only access",
        member_functions={
            "Operations": [
                MemberFunction("operator++", "Advance", "Varies by container"),
                MemberFunction("operator*", "Dereference (const)", "O(1)"),
            ],
        },
        notes=[
            "Cannot modify elements",
            "Use cbegin()/cend() to obtain",
        ]
    ),

    "reverse_iterator": CppFeatureDetail(
        name="std::reverse_iterator",
        version="C++98",
        description="Iterator adaptor for reverse traversal",
        member_functions={
            "Constructors": [
                MemberFunction("reverse_iterator()", "Default constructor", "O(1)"),
                MemberFunction("reverse_iterator(iter)", "Construct from base iterator", "O(1)"),
                MemberFunction("reverse_iterator(Iter current)", "Construct from current iterator position", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Dereference to element", "O(1)"),
                MemberFunction("operator++", "Pre-increment: move to previous element", "O(1)"),
                MemberFunction("operator++(int)", "Post-increment: move to previous element", "O(1)"),
                MemberFunction("operator--", "Pre-decrement: move to next element", "O(1)"),
                MemberFunction("operator--(int)", "Post-decrement: move to next element", "O(1)"),
                MemberFunction("operator->", "Member access through dereference", "O(1)"),
                MemberFunction("operator==", "Compare for equality with another reverse_iterator", "O(1)"),
                MemberFunction("operator!=", "Compare for inequality", "O(1)"),
            ],
            "Member Functions": [
                MemberFunction("base()", "Return underlying iterator (one past the current position)", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: Same as base iterator (requires BidirectionalIterator or better)",
            "Header: <iterator>",
            "Reverses traversal direction: ++ on reverse_iterator moves backward in the base sequence",
            "Supports bidirectional operations on the base iterator",
        ]
    ),

    "const_reverse_iterator": CppFeatureDetail(
        name="std::const_reverse_iterator",
        version="C++98",
        description="Const iterator adaptor for reverse traversal of containers",
        member_functions={
            "Constructors": [
                MemberFunction("const_reverse_iterator()", "Default constructor", "O(1)"),
                MemberFunction("const_reverse_iterator(const_iterator)", "Construct from base const iterator", "O(1)"),
                MemberFunction("const_reverse_iterator(reverse_iterator)", "Construct from non-const reverse iterator", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Dereference to const element", "O(1)"),
                MemberFunction("operator++", "Move to previous element (pre-increment)", "O(1)"),
                MemberFunction("operator++(int)", "Move to previous element (post-increment)", "O(1)"),
                MemberFunction("operator--", "Move to next element (pre-decrement)", "O(1)"),
                MemberFunction("operator--(int)", "Move to next element (post-decrement)", "O(1)"),
                MemberFunction("operator->", "Access member through const pointer", "O(1)"),
                MemberFunction("operator==", "Compare for equality", "O(1)"),
                MemberFunction("operator!=", "Compare for inequality", "O(1)"),
            ],
            "Member Functions": [
                MemberFunction("base()", "Get underlying const iterator", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: Matches base const iterator category (BidirectionalIterator or better)",
            "Header: <iterator>",
            "Provides const access during reverse traversal",
            "Typically used with const containers or to enforce const correctness",
            "Equivalent to std::reverse_iterator<ConstIterator>",
        ]
    ),

    "back_inserter": CppFeatureDetail(
        name="std::back_inserter",
        version="C++98",
        description="Function creating an output iterator that appends elements to the end of a container",
        member_functions={
            "Constructors": [
                MemberFunction("back_inserter(cont)", "Creates back_insert_iterator from container reference", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Returns reference to *this", "O(1)"),
                MemberFunction("operator++", "No-op, returns *this", "O(1)"),
                MemberFunction("operator--", "Not supported"),
                MemberFunction("operator=(const T& x)", "Appends x via container.push_back(x), returns *this", "Amortized O(1)"),
                MemberFunction("operator=(T&& x)", "Appends std::move(x) via container.push_back, returns *this", "Amortized O(1)"),
            ],
        },
        notes=[
            "Iterator category: OutputIterator",
            "Header: <iterator>",
            "Requires container with push_back member (e.g., vector, deque, list)",
            "Used with algorithms like std::copy for appending elements",
            "Does not support dereferencing for reading or random access",
        ]
    ),

    "front_inserter": CppFeatureDetail(
        name="std::front_inserter",
        version="C++98",
        description="Function creating an output iterator that inserts at the front of a container",
        member_functions={
            "Constructors": [
                MemberFunction("front_inserter(Container& x)", "Returns insert_iterator<Container> inserting at x.begin()", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Returns reference to the iterator itself", "O(1)"),
                MemberFunction("operator++", "Advances iterator (maintains insertion at begin())", "O(1)"),
                MemberFunction("operator++(int)", "Post-increment (maintains insertion at begin())", "O(1)"),
                MemberFunction("operator=(const T& val)", "Inserts val at container front via push_front", "Amortized O(1)"),
                MemberFunction("operator=(T&& val)", "Moves and inserts val at container front", "Amortized O(1)"),
            ],
        },
        notes=[
            "Iterator category: OutputIterator",
            "Header: <iterator>",
            "Requires Container with push_front member",
            "Used with algorithms like std::copy for front insertion into deque or list",
            "Insertion position always at begin(); ++ has no effect on position",
        ]
    ),

    "inserter": CppFeatureDetail(
        name="std::inserter",
        version="C++98",
        description="Function creating an insert_iterator adaptor for container insertion",
        member_functions={
            "Functions": [
                MemberFunction("inserter(Container& cont, Iterator it)", "Returns insert_iterator that inserts before 'it' in 'cont'", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator=(const T& val)", "Inserts 'val' into container at current position", "Amortized O(1)"),
                MemberFunction("operator*()", "Returns *this for assignment compatibility", "O(1)"),
                MemberFunction("operator++()", "Advances insertion iterator (no-op for insert_iterator)", "O(1)"),
                MemberFunction("operator++(int)", "Post-increment (no-op for insert_iterator)", "O(1)"),
            ],
        },
        notes=[
            "Returns: std::insert_iterator<Container>",
            "Iterator category: OutputIterator",
            "Header: <iterator>",
            "Used with algorithms like std::copy for inserting into containers like std::list or std::map",
            "Insertion point advances after each assignment",
        ]
    ),

    "move_iterator": CppFeatureDetail(
        name="std::move_iterator",
        version="C++11",
        description="Iterator adaptor that converts lvalue references to rvalue references for move semantics",
        member_functions={
            "Constructors": [
                MemberFunction("move_iterator() noexcept", "Default constructor", "O(1)"),
                MemberFunction("move_iterator(Iter i) noexcept", "Construct from base iterator", "O(1)"),
                MemberFunction("move_iterator(const move_iterator& other) noexcept", "Copy constructor", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*() const", "Dereference to rvalue reference", "O(1)"),
                MemberFunction("operator->() const", "Arrow operator to underlying element", "O(1)"),
                MemberFunction("operator++()", "Pre-increment underlying iterator", "O(1)"),
                MemberFunction("operator++(int)", "Post-increment underlying iterator", "O(1)"),
                MemberFunction("operator--()", "Pre-decrement (if bidirectional)", "O(1)"),
                MemberFunction("operator--(int)", "Post-decrement (if bidirectional)", "O(1)"),
                MemberFunction("operator==(const move_iterator& other) const", "Equality comparison via base", "O(1)"),
                MemberFunction("operator!=(const move_iterator& other) const", "Inequality comparison via base", "O(1)"),
            ],
            "Member Functions": [
                MemberFunction("base() const noexcept", "Return underlying base iterator", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: Same as base iterator (InputIterator/ForwardIterator/BidirectionalIterator/RandomAccessIterator)",
            "Header: <iterator>",
            "Dereference yields rvalue reference: decltype(*base()) &&",
            "Used with std::make_move_iterator for efficient moves in algorithms",
        ]
    ),

    "istream_iterator": CppFeatureDetail(
        name="std::istream_iterator",
        version="C++98",
        description="Input iterator adaptor for reading objects from an istream",
        member_functions={
            "Constructors": [
                MemberFunction("istream_iterator()", "Default constructor (past-the-end iterator)", "O(1)"),
                MemberFunction("istream_iterator(istream_type& s, const char_type* delim = 0)", "Construct and bind to input stream with optional delimiter", "O(1)"),
                MemberFunction("istream_iterator(const istream_iterator& other)", "Copy constructor", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Dereference to read and return next value using >>", "O(1) amortized"),
                MemberFunction("operator++", "Pre-increment: advance to next value", "O(1) amortized"),
                MemberFunction("operator++(int)", "Post-increment: advance to next value", "O(1) amortized"),
                MemberFunction("operator==", "Equality comparison", "O(1)"),
                MemberFunction("operator!=", "Inequality comparison", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: InputIterator",
            "Header: <iterator>",
            "Reads whitespace-separated values by default; fails when extraction returns false",
            "Past-the-end when default-constructed or stream reaches EOF/failure",
            "Template parameter T must support istream& >> T",
        ]
    ),

    "ostream_iterator": CppFeatureDetail(
        name="std::ostream_iterator",
        version="C++98",
        description="Output iterator that writes elements to an output stream",
        member_functions={
            "Constructors": [
                MemberFunction("ostream_iterator(basic_ostream<charT, traits>& s)", "Construct with output stream", "O(1)"),
                MemberFunction("ostream_iterator(basic_ostream<charT, traits>& s, const charT* delimiter)", "Construct with stream and optional delimiter", "O(1)"),
                MemberFunction("ostream_iterator(const ostream_iterator& x)", "Copy constructor", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator=(const T& x)", "Extract and write value to stream, append delimiter if set", "O(1)"),
                MemberFunction("operator*()", "Return reference to self (required for output iterator)", "O(1)"),
                MemberFunction("operator++()", "No-op, return reference to self", "O(1)"),
                MemberFunction("operator++(int)", "No-op, return copy of self", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: OutputIterator",
            "Header: <iterator>",
            "Template parameters: class T (value type), class charT = char, class traits = char_traits<charT>",
            "No comparison operators; stream reference must outlive iterator",
            "Commonly used with std::copy for streaming ranges",
        ]
    ),

    "istreambuf_iterator": CppFeatureDetail(
        name="std::istreambuf_iterator",
        version="C++98",
        description="Input iterator for reading characters from a stream buffer",
        member_functions={
            "Constructors": [
                MemberFunction("istreambuf_iterator()", "Default constructor (singular iterator)", "O(1)"),
                MemberFunction("istreambuf_iterator(basic_streambuf<charT, Traits>* s)", "Construct from stream buffer pointer", "O(1)"),
                MemberFunction("istreambuf_iterator(const basic_istream<charT, Traits>& is)", "Construct from input stream", "O(1)"),
            ],
            "Operations": [
                MemberFunction("operator*", "Dereference to read next character", "O(1)"),
                MemberFunction("operator++", "Pre-increment to next character", "O(1)"),
                MemberFunction("operator++(int)", "Post-increment to next character", "O(1)"),
                MemberFunction("operator==", "Compare for equality", "O(1)"),
                MemberFunction("operator!=", "Compare for inequality", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: InputIterator",
            "Header: <iterator>",
            "Templated on charT and Traits (defaults to char_traits<charT>)",
            "Singular iterator (default-constructed) compares equal to end-of-stream",
            "operator* fails (returns Traits::eof()) if stream is in failure state",
        ]
    ),

    "ostreambuf_iterator": CppFeatureDetail(
        name="std::ostreambuf_iterator",
        version="C++98",
        description="Output iterator that inserts characters into a stream buffer",
        member_functions={
            "Constructors": [
                MemberFunction("ostreambuf_iterator() noexcept", "Default constructor (singular iterator)", "O(1)"),
                MemberFunction("ostreambuf_iterator(ostreambuf_iterator const& other) noexcept", "Copy constructor", "O(1)"),
                MemberFunction("ostreambuf_iterator(basic_streambuf<charT, traits>* s) noexcept", "Construct from stream buffer pointer", "O(1)"),
            ],
            "Operations": [
                MemberFunction("charT& operator*() noexcept", "Returns reference for assignment (proxy)", "O(1)"),
                MemberFunction("ostreambuf_iterator& operator++() noexcept", "Advances iterator (no-op, returns *this)", "O(1)"),
                MemberFunction("ostreambuf_iterator operator++(int) noexcept", "Post-increment (no-op, returns *this)", "O(1)"),
                MemberFunction("ostreambuf_iterator& operator=(charT c)", "Assigns character to stream buffer", "O(1)"),
            ],
            "Member Functions": [
                MemberFunction("bool failed() const noexcept", "Returns true if output failed", "O(1)"),
                MemberFunction("explicit operator bool() const noexcept", "Returns true if valid and not failed", "O(1)"),
            ],
        },
        notes=[
            "Iterator category: OutputIterator",
            "Header: <iterator>",
            "Template: ostreambuf_iterator<charT, traits>",
            "Used for outputting sequences to ostreams via streambuf",
            "Singular iterator if constructed with null streambuf",
        ]
    ),
}


# ============================================================================
# BROWSER CLASS
# ============================================================================

class CppReferenceBrowser:
    """Simple C++ Standard Library reference browser."""

    def run(self):
        """Main loop."""
        console.print("[bold cyan]C++ Standard Library Reference[/bold cyan]\n")

        while True:
            choice = self._main_menu()

            if choice == 'exit':
                break
            elif choice == 'containers':
                self._browse_category("Containers", CONTAINERS)
            elif choice == 'algorithms':
                self._browse_category("Algorithms", ALGORITHMS)
            elif choice == 'iterators':
                self._browse_category("Iterators", ITERATORS)
            elif choice == 'pointers':
                self._browse_category("Smart Pointers", SMART_POINTERS)

    def _main_menu(self):
        """Show main menu."""
        choices = [
            Choice(title=[("class:bright_blue", "📦 Containers")], value='containers'),
            Choice(title=[("class:bright_green", "⚡ Algorithms")], value='algorithms'),
            Choice(title=[("class:bright_yellow", "🔄 Iterators")], value='iterators'),
            Choice(title=[("class:bright_cyan", "🧠 Smart Pointers")], value='pointers'),
            questionary.Separator(),
            Choice(title=[("class:white", "❌ Exit")], value='exit'),
        ]

        answer = questionary.select(
            "Select category:",
            choices=choices,
            style=QUESTIONARY_STYLE
        ).ask()

        return answer if answer else 'exit'

    def _browse_category(self, title: str, data: Dict[str, List[CppFeature]]):
        """Browse a category."""
        while True:
            # Build menu from subcategories
            choices = []

            for subcategory, features in data.items():
                count = len(features)
                choices.append(Choice(
                    title=[
                        ("class:bright_cyan", f"{subcategory}"),
                        ("class:grey70", f" ({count} items)")
                    ],
                    value=subcategory
                ))

            choices.append(questionary.Separator())
            choices.append(Choice(title=[("class:yellow", "← Back")], value="__back__"))

            answer = questionary.select(
                f"{title}:",
                choices=choices,
                style=QUESTIONARY_STYLE
            ).ask()

            if not answer or answer == "__back__":
                break

            # Show features in subcategory
            self._show_features(answer, data[answer])

    def _show_features(self, title: str, features: List[CppFeature]):
        """Display features as selectable menu."""
        while True:
            choices = []

            for feature in features:
                choices.append(Choice(
                    title=[
                        ("class:bright_yellow", f"{feature.name}"),
                        ("class:bright_blue", f" ({feature.version})"),
                        ("class:grey70", f" - {feature.description}")
                    ],
                    value=feature
                ))

            choices.append(questionary.Separator())
            choices.append(Choice(title=[("class:yellow", "← Back")], value="__back__"))

            answer = questionary.select(
                f"{title} (select for details):",
                choices=choices,
                style=QUESTIONARY_STYLE
            ).ask()

            if not answer or answer == "__back__":
                break

            # Show detail if available
            if answer.name in DETAIL_DATA:
                self._show_detail(DETAIL_DATA[answer.name])
            else:
                console.print(f"\n[yellow]Detailed reference for {answer.name} coming soon![/yellow]\n")
                try:
                    if sys.stdin.isatty():
                        questionary.press_any_key_to_continue("Press any key to continue...").ask()
                except Exception:
                    pass

    def _show_detail(self, detail: CppFeatureDetail):
        """Display detailed reference information."""
        console.print("\n")

        # Header
        header = f"[bold cyan]{detail.name}[/bold cyan] [dim]({detail.version})[/dim]\n"
        header += f"{detail.description}"
        console.print(Panel(header, border_style="cyan"))

        # Member Types
        if detail.member_types:
            console.print("\n[bold]Member Types:[/bold]")
            types_table = Table(show_header=False, box=None, padding=(0, 2))
            types_table.add_column("Type", style="bright_yellow")
            types_table.add_column("Description", style="white")

            for name, desc in detail.member_types:
                types_table.add_row(name, desc)

            console.print(types_table)

        # Member Functions
        if detail.member_functions:
            for category, functions in detail.member_functions.items():
                console.print(f"\n[bold]{category}:[/bold]")
                func_table = Table(show_header=True, box=None, padding=(0, 2))
                func_table.add_column("Function", style="bright_green", no_wrap=True)
                func_table.add_column("Description", style="white")
                func_table.add_column("Complexity", style="bright_blue")

                for func in functions:
                    func_table.add_row(func.name, func.description, func.complexity)

                console.print(func_table)

        # Notes
        if detail.notes:
            console.print("\n[bold]Notes:[/bold]")
            for note in detail.notes:
                console.print(f"  • {note}")

        console.print("\n")

        try:
            if sys.stdin.isatty():
                questionary.press_any_key_to_continue("Press any key to continue...").ask()
        except Exception:
            pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    try:
        browser = CppReferenceBrowser()
        browser.run()
        console.print("\n[dim]Goodbye![/dim]\n")
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
