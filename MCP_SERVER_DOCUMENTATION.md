# MCP Server: Features and Architecture

## 1. Introduction

This document outlines the architecture and key features of the Programming Concepts MCP Server. The server is a `FastMCP` application designed to provide intelligent, tool-based access to a comprehensive knowledge base derived from classic programming books. Its primary purpose is to act as a reliable backend for an AI agent, enabling it to learn, search, and synthesize information about complex programming topics.

---

## 2. Architecture

The server's architecture is designed for performance, flexibility, and maintainability.

### 2.1. Server Core

The server is built using the **`FastMCP`** framework, which exposes Python functions as discrete, callable tools for an AI client. This allows for a clean separation between the server's logic and the AI's interaction with it.

### 2.2. Startup and Indexing

On startup, the server builds a comprehensive, in-memory database of all programming concepts. This process is handled by the `build_concept_index` function and includes several key steps:

*   **Directory Scanning:** The server scans all subdirectories within the `outputs/` folder. Each subdirectory is treated as a separate book.
*   **Caching:** To ensure fast startups, the server uses a cache file (`outputs/concept_cache.json`). If no concept files have been modified since the cache was last created, the server loads directly from the cache, bypassing the expensive indexing process.
*   **Concept Loading:** The server reads all `.json` files within each book directory.
*   **Backup File Handling:** The indexing logic was updated to explicitly ignore any filename containing `.backup`, preventing duplicate concepts from being loaded.
*   **Specialized Loaders:** The server has a dedicated function, `load_posix_concepts`, to handle the unique format of the POSIX man page files, demonstrating the system's extensibility.

### 2.3. Data Model and Normalization

As concepts are loaded, they are normalized into a standard internal format by the `add_concept` function.

*   **Unique IDs:** A clean, predictable ID is generated for each concept (e.g., `csapp_2016_mem_virtual-memory_...`).
*   **Filename Conventions:** The server is designed to understand two conventions for filenames:
    1.  **New Convention (Preferred):** `{book_code}_{category}_{topic}_{hash}.json`. This format is powerful as it allows the server to automatically extract a `category` tag from the filename.
    2.  **Old Convention:** Any filename containing `concept_` and a number (e.g., `concept_123.json`). This format is supported for legacy files but does not provide a category.

---

## 3. Core Features (Tools)

The server's functionality is exposed through a rich set of tools.

### 3.1. Search and Discovery

These tools allow for flexible and intelligent querying of the knowledge base.

*   `search_concepts(query)`: The primary search tool. It has several layers of intelligence:
    *   **Keyword Expansion:** It uses the `_expand_search_terms` function, which contains a large, internal dictionary of synonyms and acronyms. A search for `RAII` is automatically expanded to also search for `Resource Acquisition Is Initialization`.
    *   **Relevance Scoring:** It uses a weighted scoring system to rank results. Matches in a concept's `title` (+3 points) are weighted more heavily than matches in its `description` (+2) or `content` (+1). An exact match for the title grants a significant bonus (+2).
*   `search_by_book(book_name, query)`: Narrows the search to a specific book.
*   `search_by_category(category)`: Filters concepts by the category extracted from the filename (e.g., `mem`, `op`, `func`).
*   `find_advanced_concepts(topic)`: Uses heuristics to find concepts on a topic that are likely to be advanced.
*   `find_code_examples(pattern)`: Finds all concepts that contain code snippets, with an option to search within the code.
*   `discover_hidden_gems(topic, minimum_score, limit)`: 🔍 AI-powered discovery of fascinating, lesser-known programming concepts. Uses LLM evaluation to identify concepts with deep implementation details, counter-intuitive behaviors, or surprising insights that reveal "wow, I had no idea!" moments.

### 3.2. Learning and Synthesis

These tools are designed to help a user learn about broad topics in a structured way.

*   `generate_study_path(goal)`: Creates a structured learning plan. 
    *   It uses an internal `study_paths` dictionary that contains curated keyword lists for a wide variety of C, C++, STL, and Systems Programming topics.
    *   It sorts the resulting concepts not just by relevance but also by a predefined "book authority" score to present foundational concepts first.
*   `generate_custom_tutorial(topic, skill_level)`: Creates a complete, tailored lesson on a topic.
*   `generate_reference_sheet(topic, format)`: Generates a formatted reference sheet for a specific topic. Supports markdown, text, and HTML formats.
*   `synthesize_concepts(topic)`: Uses a generative AI model to combine information from multiple books into a single, comprehensive explanation.
*   `create_best_practices_guide(topic)`: Analyzes patterns across all sources to generate comprehensive best practices guides for topics like error handling, memory management, etc.
*   `compare_concepts(concept1, concept2)`: Provides a side-by-side comparison of two concepts.

### 3.3. Direct Concept Access

*   `get_concept_details(concept_id)`: Retrieves the full, formatted content for a single concept by its unique ID.
*   `read_concept_resource(book_name, concept_id)`: Resource-like tool to read a specific concept from a specific book using clean identifiers.
*   `list_concept_uris()`: Lists all available concepts in a URI-like format (`concept://book/topic`).
*   `debug_concept_ids(search_term)`: Debug tool to see concept IDs and help with tool integration. Useful for finding exact concept IDs.

### 3.4. Code Analysis

*   `explain_my_code(code_snippet)`: Analyzes a user-provided code snippet and finds relevant concepts from the knowledge base to explain it.

### 3.5. Knowledge Base Maintenance

*   `analyze_concept_duplicates(book_name)`: A read-only tool to find and report on likely duplicate concepts within a book.
*   `cleanup_duplicate_concepts(book_name)`: A tool to automatically remove identified duplicates, with a `--dry-run` mode for safety.

---

## 4. Supported Books

The server currently supports programming concepts from the following authoritative sources:

### Core Programming Languages
*   **kernighan_ritchie**: "The C Programming Language" (Kernighan & Ritchie) - Authoritative C language reference
*   **cpp_standard**: "The C++ Standard Library" (ISO/IEC 14882) - Official C++ standard reference
*   **cpp_primer**: "C++ Primer (5th Edition)" - Comprehensive C++ tutorial
*   **expert_c_programming**: "Expert C Programming Deep C Secrets" (van der Linden) - Advanced C concepts

### Systems Programming
*   **csapp_2016**: "Computer Systems: A Programmer's Perspective (3rd Edition)" - Systems programming and computer architecture
*   **unix_env**: "Advanced Programming in the UNIX Environment" (Stevens) - UNIX/Linux systems programming
*   **os_three_pieces**: "Operating Systems: Three Easy Pieces" (Arpaci-Dusseau) - Operating systems concepts
*   **posix_manpages**: "POSIX Manual Pages" - System call and library function references

### Specialized Topics
*   **linkers_loaders**: "Linkers and Loaders" (Levine) - Program linking and loading
*   **Inside_the_C++_Object_Model**: "Inside the C++ Object Model" (Stanley Lippman) - C++ implementation internals
*   **cpp_stl_containers**: "C++ STL Containers" - Extracted STL container concepts

Each book has an associated authority weight used for relevance scoring, with foundational texts like Kernighan & Ritchie and the C++ Standard receiving the highest weights.

---

## 5. Enhanced Features

### 5.1. AI-Powered Discovery
*   **Hidden Gems Detection**: The `discover_hidden_gems` tool uses OpenAI's LLM to evaluate concepts for "wow factor" - identifying genuinely surprising implementation details, counter-intuitive behaviors, and deep system insights.
*   **Intelligent Concept Synthesis**: Multi-source synthesis uses AI to combine information from different books into coherent explanations.

### 5.2. Context-Aware Search Intelligence
*   **Smart Keyword Expansion**: Search terms are automatically expanded using synonyms and acronyms (e.g., "RAII" → "Resource Acquisition Is Initialization").
*   **Book Authority Weighting**: Results are weighted by source authority - foundational texts like K&R carry more weight than tutorial materials.
*   **Context Hints**: Query terms trigger intelligent book recommendations (e.g., "STL" queries boost cpp_stl_containers results).

### 5.3. Flexible Resource Access
*   **URI-Style Addressing**: Concepts can be accessed using clean URIs like `concept://book_name/topic_identifier`.
*   **Multiple ID Formats**: Support for both new convention filenames (`{book}_{category}_{topic}_{hash}.json`) and legacy formats.
*   **Category-Based Filtering**: Automatic category extraction from filenames enables filtering by concept type (mem, func, io, etc.).

### 5.4. Educational Tools
*   **Study Path Generation**: Curated learning sequences for major programming topics with prerequisite ordering.
*   **Custom Tutorial Generation**: AI-generated tutorials tailored to specific skill levels (beginner, intermediate, advanced).
*   **Reference Sheet Creation**: Formatted reference materials in multiple output formats (markdown, text, HTML).
*   **Best Practices Synthesis**: Cross-source analysis to identify and document programming best practices.

### 5.5. Maintenance and Quality
*   **Intelligent Duplicate Detection**: Similarity-based duplicate identification with configurable thresholds.
*   **Safe Cleanup Operations**: Dry-run mode for all destructive operations.
*   **Debug and Introspection**: Tools for debugging concept IDs and understanding the knowledge base structure.
