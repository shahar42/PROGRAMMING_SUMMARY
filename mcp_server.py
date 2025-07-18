#!/usr/bin/env python3
"""
Programming Concepts MCP Server using FastMCP
Provides access to programming concepts from technical books.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict
import re
from typing import List, Tuple, Dict

# Add current directory to Python path
sys.path.append('.')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("programming-concepts-mcp")

# Initialize FastMCP server
mcp = FastMCP("programming-concepts")

# Global variables for concepts database
concepts = []
books_metadata = {
    "kernighan_ritchie": "The C Programming Language (Kernighan & Ritchie)",
    "unix_env": "Advanced Programming in the UNIX Environment (Stevens)",
    "linkers_loaders": "Linkers and Loaders (Levine)",
    "os_three_pieces": "Operating Systems: Three Easy Pieces (Arpaci-Dusseau)",
    "expert_c_programming": "Expert C Programming Deep C Secrets (van der Linden)"
}


def build_concept_index():
    """Build the concept index from outputs directory."""
    global concepts

    logger.info("Building concept index from outputs")

    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    outputs_dir = PROJECT_ROOT / "outputs"
    if not outputs_dir.exists():
        logger.error("outputs directory not found")
        return

    total_concepts = 0

    for book_dir in outputs_dir.iterdir():
        if not book_dir.is_dir():
            continue

        book_name = book_dir.name
        if book_name not in books_metadata:
            continue

        logger.info(f"Indexing book: {book_name}")

        # Look for JSON files containing concepts
        concept_files = list(book_dir.glob("*.json"))
        book_concepts = 0

        for concept_file in concept_files:
            if concept_file.name in ["progress.json", "metadata.json"]:
                continue

            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept_data = json.load(f)

                # Handle both single concept and list of concepts
                if isinstance(concept_data, list):
                    for concept in concept_data:
                        add_concept(concept, book_name, concept_file.name)
                        book_concepts += 1
                elif isinstance(concept_data, dict):
                    add_concept(concept_data, book_name, concept_file.name)
                    book_concepts += 1

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {concept_file}: {e}")
                continue

        if book_concepts > 0:
            logger.info(f"Found {book_concepts} concepts in {book_name}")
            total_concepts += book_concepts

    logger.info(
        f"Successfully indexed {total_concepts} concepts across {len([k for k in books_metadata.keys() if any(Path('outputs').glob(f'{k}/*.json'))])} books")


def add_concept(concept_data: Dict[str, Any], book_name: str, filename: str):
    """Add a concept to the index with proper field mapping."""
    global concepts

    # Generate a unique ID for the concept
    concept_id = f"{book_name}_{filename.replace('.json', '')}_{len(concepts)}"

    # SURGICAL FIX: Map the standardized extractor format to MCP server expectations

    # Map 'topic' -> 'title' (all extractors use 'topic')
    title = concept_data.get('topic', concept_data.get('title', concept_data.get('concept', 'Unknown Concept')))

    # Map 'explanation' -> 'description' (all extractors use 'explanation' for main description)
    description = concept_data.get('explanation', concept_data.get('description', concept_data.get('summary', '')))

    # Combine 'explanation' and 'example_explanation' for full content
    content_parts = []
    if concept_data.get('explanation'):
        content_parts.append(concept_data['explanation'])
    if concept_data.get('example_explanation'):
        content_parts.append(concept_data['example_explanation'])
    content = '\n\n'.join(content_parts) if content_parts else concept_data.get('content', '')

    # Handle code examples: prefer existing 'syntax', fallback to formatted 'code_example'
    syntax = concept_data.get('syntax', '')
    if not syntax and concept_data.get('code_example'):
        # Format code_example array into a proper code block
        code_lines = concept_data['code_example']
        if isinstance(code_lines, list):
            syntax = '\n'.join(code_lines)
        else:
            syntax = str(code_lines)

    concept = {
        'id': concept_id,
        'title': title,
        'description': description,
        'content': content,
        'syntax': syntax,
        'book': book_name,
        'book_title': books_metadata[book_name],
        'source_file': filename,
        'raw_data': concept_data
    }

    concepts.append(concept)

@mcp.tool()
async def search_concepts(query: str, limit: int = 10) -> str:
    """Search programming concepts by keyword, topic, or description.

    Args:
        query: Search query (use '*' to list all concepts)
        limit: Maximum number of results to return (default: 10)
    """
    query_lower = query.lower()

    if query == "*":
        # Return all concepts
        matching_concepts = concepts[:limit]
    else:
        # Search concepts
        matching_concepts = []
        for concept in concepts:
            if (query_lower in concept['title'].lower() or
                    query_lower in concept['description'].lower() or
                    query_lower in concept['content'].lower() or
                    query_lower in concept['book_title'].lower()):
                matching_concepts.append(concept)
                if len(matching_concepts) >= limit:
                    break

    if not matching_concepts:
        return f"No concepts found for query: '{query}'"

    # Format results
    result_text = f"Found {len(matching_concepts)} programming concepts:\n\n"
    for i, concept in enumerate(matching_concepts, 1):
        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
        if concept['description']:
            result_text += f"   {concept['description'][:100]}{'...' if len(concept['description']) > 100 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n\n"

    return result_text


@mcp.tool()
async def search_by_book(book_name: str, query: str = "") -> str:
    """Search concepts within a specific book.

    Args:
        book_name: Name of the book to search in (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming)
        query: Search query within the book (optional, empty means show all concepts from book)
    """
    # Validate book name
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Invalid book name. Available books: {', '.join(available_books)}"

    # Filter concepts by book
    book_concepts = [c for c in concepts if c['book'] == book_name]

    if not book_concepts:
        return f"No concepts found for book: {books_metadata[book_name]}"

    # If query is provided, filter further
    if query:
        query_lower = query.lower()
        matching_concepts = []
        for concept in book_concepts:
            if (query_lower in concept['title'].lower() or
                    query_lower in concept['description'].lower() or
                    query_lower in concept['content'].lower()):
                matching_concepts.append(concept)
    else:
        matching_concepts = book_concepts

    if not matching_concepts:
        return f"No concepts found for query '{query}' in {books_metadata[book_name]}"

    # Format results
    result_text = f"Found {len(matching_concepts)} concepts in **{books_metadata[book_name]}**"
    if query:
        result_text += f" matching '{query}'"
    result_text += ":\n\n"

    for i, concept in enumerate(matching_concepts, 1):
        result_text += f"{i}. **{concept['title']}**\n"
        if concept['description']:
            result_text += f"   {concept['description'][:150]}{'...' if len(concept['description']) > 150 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n\n"

    return result_text


@mcp.tool()
async def find_advanced_concepts(topic: str, threshold: int = 2) -> str:
    """Finds advanced concepts related to a specific topic.

    "Advanced" is determined by a scoring system based on keywords and the source book.

    Args:
        topic: The general programming topic to search for (e.g., 'memory', 'linking').
        threshold: A score (default: 2) a concept must meet to be considered "advanced".
                   Higher values return more specialized concepts.
    """
    # 1. Define our heuristics for what makes a concept "advanced"
    ADVANCED_KEYWORDS = [
        'advanced', 'internals', 'optimization', 'low-level', 'kernel', 'complex',
        'performance', 'architecture', 'concurrent', 'asynchronous', 'memory layout',
        'virtual memory', 'system call', 'linking', 'loading', 'multithreading',
        'synchronization', 'parallelism', 'cache coherence', 'memory alignment',
        'interrupts', 'scheduling', 'file systems', 'network stack', 'garbage collection',
        'instruction pipelining', 'branch prediction', 'memory paging', 'context switching',
        'atomic operations', 'lock-free programming', 'syscalls',
        'dynamic linking', 'static analysis',
        'memory fences', 'thread affinity', 'heap management', 'GOT', 'TLB',
        'page table', 'segment'
    ]
    BOOK_WEIGHTS = {
        "linkers_loaders": 3,
        "expert_c_programming": 3,  # Expert C Programming is advanced
        "unix_env": 2,
        "os_three_pieces": 2,
        "kernighan_ritchie": 0  # K&R is foundational, so less inherently "advanced"
    }

    # 2. Search for concepts matching the topic and calculate their "advanced score"
    advanced_matches = []
    topic_lower = topic.lower()

    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()

        # First, ensure the concept is relevant to the topic at all
        if topic_lower not in concept_text:
            continue

        # Calculate the advanced score
        advanced_score = 0
        # Add points for being from an advanced book
        advanced_score += BOOK_WEIGHTS.get(concept['book'], 0)
        # Add points for each advanced keyword found
        for keyword in ADVANCED_KEYWORDS:
            if keyword in concept_text:
                advanced_score += 1

        # Only include concepts that meet our threshold
        if advanced_score >= threshold:
            advanced_matches.append({'concept': concept, 'score': advanced_score})

    # 3. Format and return the results
    if not advanced_matches:
        return f"No advanced concepts found for topic '{topic}' with threshold {threshold}. Try a lower threshold or broader topic."

    # Sort results to show the "most advanced" first
    advanced_matches.sort(key=lambda x: x['score'], reverse=True)

    result_text = f"Found {len(advanced_matches)} advanced concepts for '{topic}' (Threshold: {threshold}):\n\n"
    for i, match in enumerate(advanced_matches, 1):
        concept = match['concept']
        result_text += f"{i}. **{concept['title']}** (From: {concept['book_title']})\n"
        result_text += f"   *Advanced Score: {match['score']}*\n"
        result_text += f"   {concept['description'][:100]}{'...' if len(concept['description']) > 100 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n\n"

    return result_text


@mcp.tool()
async def find_code_examples(pattern: str = "") -> str:
    """Find all concepts that contain actual code examples.

    Args:
        pattern: Optional pattern to search within code examples (e.g. 'malloc', 'file', 'fork')
    """
    code_concepts = []
    pattern_lower = pattern.lower() if pattern else ""

    for concept in concepts:
        # Check if concept has code/syntax
        has_code = (concept['syntax'] and concept['syntax'].strip()) or \
                   (concept['raw_data'].get('code') and concept['raw_data']['code'].strip()) or \
                   (concept['raw_data'].get('example') and concept['raw_data']['example'].strip())

        if has_code:
            # If pattern specified, check if it matches
            if pattern:
                code_text = (concept['syntax'] + " " +
                             str(concept['raw_data'].get('code', '')) + " " +
                             str(concept['raw_data'].get('example', ''))).lower()
                if pattern_lower in code_text:
                    code_concepts.append(concept)
            else:
                code_concepts.append(concept)

    if not code_concepts:
        if pattern:
            return f"No code examples found matching pattern: '{pattern}'"
        else:
            return "No code examples found in the knowledge base"

    # Format results
    result_text = f"Found {len(code_concepts)} concepts with code examples"
    if pattern:
        result_text += f" matching '{pattern}'"
    result_text += ":\n\n"

    for i, concept in enumerate(code_concepts, 1):
        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"

        # Show code preview
        code_sample = concept['syntax'] or concept['raw_data'].get('code', '') or concept['raw_data'].get('example', '')
        if code_sample:
            # Show first few lines of code
            code_lines = code_sample.strip().split('\n')[:3]
            preview = '\n'.join(code_lines)
            if len(code_sample.split('\n')) > 3:
                preview += "\n   ..."
            result_text += f"   ```c\n   {preview}\n   ```\n"

        result_text += f"   ID: `{concept['id']}`\n\n"

    return result_text


@mcp.tool()
async def compare_concepts(concept1_id: str, concept2_id: str) -> str:
    """Compare two concepts side-by-side.

    Args:
        concept1_id: ID of the first concept to compare
        concept2_id: ID of the second concept to compare
    """
    # Find both concepts
    concept1 = None
    concept2 = None

    for c in concepts:
        if c['id'] == concept1_id:
            concept1 = c
        elif c['id'] == concept2_id:
            concept2 = c

    if not concept1:
        return f"First concept not found: {concept1_id}"
    if not concept2:
        return f"Second concept not found: {concept2_id}"

    # Format comparison
    result_text = f"# Concept Comparison\n\n"

    # Basic info comparison
    result_text += f"## Overview\n"
    result_text += f"| Aspect | **{concept1['title']}** | **{concept2['title']}** |\n"
    result_text += f"|--------|-------------------------|-------------------------|\n"
    result_text += f"| Source | {concept1['book_title']} | {concept2['book_title']} |\n"
    result_text += f"| ID | `{concept1['id']}` | `{concept2['id']}` |\n\n"

    # Description comparison
    if concept1['description'] or concept2['description']:
        result_text += f"## Description Comparison\n\n"
        result_text += f"### {concept1['title']}\n"
        result_text += f"{concept1['description'] or 'No description available'}\n\n"
        result_text += f"### {concept2['title']}\n"
        result_text += f"{concept2['description'] or 'No description available'}\n\n"

    # Content comparison
    if concept1['content'] or concept2['content']:
        result_text += f"## Detailed Content Comparison\n\n"
        result_text += f"### {concept1['title']} Details\n"
        result_text += f"{concept1['content'][:500] if concept1['content'] else 'No detailed content available'}\n"
        if concept1['content'] and len(concept1['content']) > 500:
            result_text += "...\n"
        result_text += f"\n### {concept2['title']} Details\n"
        result_text += f"{concept2['content'][:500] if concept2['content'] else 'No detailed content available'}\n"
        if concept2['content'] and len(concept2['content']) > 500:
            result_text += "...\n"
        result_text += "\n"

    # Code comparison
    if concept1['syntax'] or concept2['syntax']:
        result_text += f"## Code Comparison\n\n"
        result_text += f"### {concept1['title']} Code\n"
        if concept1['syntax']:
            result_text += f"```c\n{concept1['syntax']}\n```\n\n"
        else:
            result_text += "No code example available\n\n"

        result_text += f"### {concept2['title']} Code\n"
        if concept2['syntax']:
            result_text += f"```c\n{concept2['syntax']}\n```\n\n"
        else:
            result_text += "No code example available\n\n"

    # Key differences
    result_text += f"## Key Observations\n"
    if concept1['book'] != concept2['book']:
        result_text += f"- **Different Sources**: {concept1['book_title']} vs {concept2['book_title']}\n"
    else:
        result_text += f"- **Same Source**: Both from {concept1['book_title']}\n"

    if concept1['syntax'] and concept2['syntax']:
        result_text += f"- **Both have code examples** - useful for practical comparison\n"
    elif concept1['syntax'] or concept2['syntax']:
        result_text += f"- **Only one has code example** - theoretical vs practical perspective\n"

    return result_text


@mcp.tool()
async def generate_study_path(goal: str) -> str:
    """Create ordered learning sequence for a programming goal.

    Args:
        goal: Learning goal (e.g. 'system programming', 'memory management', 'file I/O', 'C basics')
    """
    goal_lower = goal.lower()

    # Define study paths based on common goals
    study_paths = {
        'c basics': ['basic', 'variable', 'function', 'array', 'pointer', 'string'],
        'memory management': ['pointer', 'malloc', 'free', 'memory', 'heap', 'stack'],
        'file io': ['file', 'open', 'read', 'write', 'close', 'stream'],
        'system programming': ['process', 'fork', 'exec', 'signal', 'pipe', 'thread'],
        'unix programming': ['unix', 'system call', 'process', 'signal', 'file descriptor'],
        'debugging': ['debug', 'error', 'gdb', 'valgrind', 'trace'],
        'compilation': ['compile', 'link', 'library', 'object', 'makefile'],
        'data structures': ['struct', 'array', 'list', 'tree', 'hash']
    }

    # Find matching keywords for the goal
    relevant_keywords = []
    for path_name, keywords in study_paths.items():
        if any(keyword in goal_lower for keyword in path_name.split()):
            relevant_keywords.extend(keywords)
            break

    # If no specific path found, extract keywords from goal
    if not relevant_keywords:
        relevant_keywords = goal_lower.split()

    # Find concepts matching the keywords
    relevant_concepts = []
    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()
        relevance_score = sum(1 for keyword in relevant_keywords if keyword in concept_text)

        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))

    if not relevant_concepts:
        return f"No concepts found for learning goal: '{goal}'"

    # Sort by relevance and book authority
    book_priority = {'kernighan_ritchie': 4, 'unix_env': 3, 'os_three_pieces': 2, 'linkers_loaders': 1}
    relevant_concepts.sort(key=lambda x: (x[1], book_priority.get(x[0]['book'], 0)), reverse=True)

    # Create study path
    result_text = f"# Study Path: {goal.title()}\n\n"
    result_text += f"Found {len(relevant_concepts)} relevant concepts organized by learning progression:\n\n"

    # Group by complexity/book
    basic_concepts = []
    intermediate_concepts = []
    advanced_concepts = []

    for concept, score in relevant_concepts:
        concept_text = concept['title'].lower() + ' ' + concept['description'].lower()

        # Simple heuristic for complexity
        if any(word in concept_text for word in ['basic', 'introduction', 'overview', 'simple']):
            basic_concepts.append(concept)
        elif any(word in concept_text for word in ['advanced', 'complex', 'optimization', 'internals']):
            advanced_concepts.append(concept)
        else:
            intermediate_concepts.append(concept)

    # If no clear categorization, distribute evenly
    if not basic_concepts and not advanced_concepts:
        third = len(relevant_concepts) // 3
        basic_concepts = [c[0] for c in relevant_concepts[:third]]
        intermediate_concepts = [c[0] for c in relevant_concepts[third:2 * third]]
        advanced_concepts = [c[0] for c in relevant_concepts[2 * third:]]

    # Format study path
    if basic_concepts:
        result_text += f"## 📚 Foundation Level\n"
        for i, concept in enumerate(basic_concepts[:5], 1):
            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Core concept'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n\n"

    if intermediate_concepts:
        result_text += f"## 🔧 Practical Level\n"
        for i, concept in enumerate(intermediate_concepts[:5], 1):
            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Practical application'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n\n"

    if advanced_concepts:
        result_text += f"## 🚀 Advanced Level\n"
        for i, concept in enumerate(advanced_concepts[:5], 1):
            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Advanced topic'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n\n"

    result_text += f"## 💡 Study Tips\n"
    result_text += f"- Start with Foundation Level concepts\n"
    result_text += f"- Use `get_concept_details(id)` for full explanations\n"
    result_text += f"- Use `find_code_examples('{goal}')` for practical examples\n"
    result_text += f"- Compare concepts between different books for deeper understanding\n"

    return result_text


@mcp.tool()
async def explain_my_code(code_snippet: str, language: str = "C") -> str:
    """Analyze code using concepts from your knowledge base.

    Args:
        code_snippet: The code to analyze
        language: Programming language (default: C)
    """
    code_lower = code_snippet.lower()

    # Extract keywords/patterns from code
    code_keywords = []

    # Common C patterns to look for
    c_patterns = {
        'malloc': ['malloc', 'memory allocation', 'heap'],
        'free': ['free', 'memory deallocation'],
        'pointer': ['*', 'pointer', 'address'],
        'array': ['[', ']', 'array', 'index'],
        'function': ['(', ')', 'function', 'call'],
        'struct': ['struct', 'structure'],
        'file': ['fopen', 'fclose', 'fread', 'fwrite', 'file'],
        'process': ['fork', 'exec', 'wait', 'process'],
        'signal': ['signal', 'kill', 'sigaction'],
        'thread': ['pthread', 'thread', 'mutex'],
        'string': ['strcpy', 'strlen', 'strcmp', 'string'],
        'stdio': ['printf', 'scanf', 'fprintf', 'input', 'output']
    }

    # Identify relevant concepts based on code content
    for keyword, patterns in c_patterns.items():
        if any(pattern in code_lower for pattern in patterns):
            code_keywords.append(keyword)

    # Find concepts that match the identified keywords
    relevant_concepts = []
    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()
        relevance_score = sum(1 for keyword in code_keywords if keyword in concept_text)

        # Also check if concept has similar code patterns
        if concept['syntax']:
            syntax_lower = concept['syntax'].lower()
            code_similarity = sum(1 for line in code_snippet.split('\n')
                                  if any(word in syntax_lower for word in line.split() if len(word) > 2))
            relevance_score += code_similarity * 0.5

        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))

    if not relevant_concepts:
        return f"No relevant concepts found for this {language} code. The code might use patterns not covered in the knowledge base."

    # Sort by relevance
    relevant_concepts.sort(key=lambda x: x[1], reverse=True)

    # Format analysis
    result_text = f"# Code Analysis: {language}\n\n"
    result_text += f"## Your Code\n```{language.lower()}\n{code_snippet}\n```\n\n"

    result_text += f"## Analysis Using Knowledge Base\n\n"
    result_text += f"Identified {len(code_keywords)} key patterns: {', '.join(code_keywords)}\n\n"

    # Show most relevant concepts
    top_concepts = relevant_concepts[:5]
    result_text += f"### 🔍 Relevant Concepts ({len(top_concepts)} found)\n\n"

    for i, (concept, score) in enumerate(top_concepts, 1):
        result_text += f"**{i}. {concept['title']}** ({concept['book_title']})\n"
        result_text += f"   {concept['description'][:150] if concept['description'] else 'No description'}{'...' if len(concept.get('description', '')) > 150 else ''}\n"

        # Show relevant code if available
        if concept['syntax'] and any(keyword in concept['syntax'].lower() for keyword in code_keywords):
            code_preview = concept['syntax'].strip().split('\n')[:2]
            result_text += f"   ```c\n   {chr(10).join(code_preview)}\n   ```\n"

        result_text += f"   ID: `{concept['id']}` | Relevance: {score:.1f}\n\n"

    # Provide expert insights
    result_text += f"### 📚 Expert Insights\n"

    # Group insights by book
    book_insights = {}
    for concept, score in top_concepts:
        book = concept['book_title']
        if book not in book_insights:
            book_insights[book] = []
        book_insights[book].append(concept['title'])

    for book, concept_titles in book_insights.items():
        result_text += f"- **{book}**: Covers {', '.join(concept_titles[:3])}\n"

    result_text += f"\n### 🚀 Next Steps\n"
    result_text += f"- Use `get_concept_details()` for detailed explanations of relevant concepts\n"
    result_text += f"- Use `find_code_examples('{code_keywords[0] if code_keywords else 'pattern'}')` for similar examples\n"
    result_text += f"- Compare implementations across different books for best practices\n"

    return result_text


@mcp.tool()
async def get_concept_details(concept_id: str) -> str:
    """Get detailed information about a specific concept.

    Args:
        concept_id: The ID of the concept to retrieve
    """
    # Find the concept
    concept = None
    for c in concepts:
        if c['id'] == concept_id:
            concept = c
            break

    if not concept:
        return f"Concept not found: {concept_id}"

    # Format detailed response
    result_text = f"# {concept['title']}\n\n"
    result_text += f"**Source:** {concept['book_title']}\n\n"

    if concept['description']:
        result_text += f"## Description\n{concept['description']}\n\n"

    if concept['content']:
        result_text += f"## Details\n{concept['content']}\n\n"

    if concept['syntax']:
        result_text += f"## Code Example\n```c\n{concept['syntax']}\n```\n\n"

    # Add any additional information from raw data
    raw_data = concept['raw_data']
    for key, value in raw_data.items():
        if key not in ['title', 'description', 'content', 'syntax', 'concept', 'summary', 'explanation',
                       'code'] and value:
            result_text += f"**{key.title()}:** {value}\n"

    return result_text


@mcp.tool()
async def generate_reference_sheet(topic: str, format: str = "markdown") -> str:
    """Generate a formatted reference sheet for a specific topic.

    Args:
        topic: The programming topic to create a reference for
        format: Output format - 'markdown', 'text', or 'html'
    """
    global concepts

    if not concepts:
        return "No concepts available"

    # Search for relevant concepts
    topic_lower = topic.lower()
    relevant_concepts = []

    for concept in concepts:
        if (topic_lower in concept['title'].lower() or
                topic_lower in concept['description'].lower() or
                topic_lower in concept['content'].lower()):
            relevant_concepts.append(concept)

    if not relevant_concepts:
        return f"No concepts found for topic: {topic}"

    # Group concepts by book
    by_book = {}
    for concept in relevant_concepts:
        book = concept['book_title']
        if book not in by_book:
            by_book[book] = []
        by_book[book].append(concept)

    # Generate reference sheet based on format
    if format.lower() == "markdown":
        return _generate_markdown_reference(topic, by_book)
    elif format.lower() == "html":
        return _generate_html_reference(topic, by_book)
    else:  # text format
        return _generate_text_reference(topic, by_book)

@mcp.tool()
async def synthesize_concepts(topic: str, max_sources: int = 5) -> str:
    """AI-powered synthesis: Combine concepts from multiple books into comprehensive explanation.
    
    Args:
        topic: The topic to synthesize (e.g., 'memory management', 'pointers', 'processes')
        max_sources: Maximum number of source books to include (default: 5)
    """
    topic_lower = topic.lower()
    
    # Find all related concepts across books
    related_concepts = []
    concept_scores = []
    
    for concept in concepts:
        # Calculate relevance score using multiple factors
        title_score = 2.0 if topic_lower in concept['title'].lower() else 0.0
        desc_score = 1.5 if topic_lower in concept['description'].lower() else 0.0
        content_score = 1.0 if topic_lower in concept['content'].lower() else 0.0
        
        # Boost score for certain books based on topic
        book_boost = {
            'memory': {'kernighan_ritchie': 1.5, 'os_three_pieces': 2.0, 'expert_c_programming': 1.8},
            'process': {'unix_env': 2.0, 'os_three_pieces': 1.8},
            'link': {'linkers_loaders': 2.5},
            'pointer': {'kernighan_ritchie': 2.0, 'expert_c_programming': 2.2}
        }
        
        boost = 1.0
        for keyword, boosts in book_boost.items():
            if keyword in topic_lower:
                boost = boosts.get(concept['book'], 1.0)
                break
                
        total_score = (title_score + desc_score + content_score) * boost
        
        if total_score > 0:
            related_concepts.append(concept)
            concept_scores.append(total_score)
    
    if not related_concepts:
        return f"No concepts found for synthesis on topic: '{topic}'"
    
    # Sort by score and group by book
    sorted_pairs = sorted(zip(related_concepts, concept_scores), key=lambda x: x[1], reverse=True)
    concepts_by_book = {}
    
    for concept, score in sorted_pairs[:15]:  # Top 15 concepts
        book = concept['book']
        if book not in concepts_by_book:
            concepts_by_book[book] = []
        concepts_by_book[book].append((concept, score))
    
    # Limit books to max_sources
    if len(concepts_by_book) > max_sources:
        # Keep books with highest total scores
        book_scores = {book: sum(score for _, score in concepts) 
                      for book, concepts in concepts_by_book.items()}
        top_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)[:max_sources]
        concepts_by_book = {book: concepts_by_book[book] for book, _ in top_books}
    
    # Generate synthesized content
    result = f"# 🧬 Synthesized Knowledge: {topic.title()}\n\n"
    result += f"*AI-powered synthesis combining insights from {len(concepts_by_book)} authoritative sources*\n\n"
    
    # Executive Summary
    result += "## 📋 Executive Summary\n\n"
    result += f"This synthesis combines {sum(len(c) for c in concepts_by_book.values())} concepts from:\n"
    for book in concepts_by_book:
        result += f"- **{books_metadata[book]}**\n"
    result += "\n"
    
    # Core Concepts Section
    result += f"## 🎯 Core Understanding of {topic.title()}\n\n"
    
    # Synthesize main explanation
    all_descriptions = []
    for book_concepts in concepts_by_book.values():
        for concept, _ in book_concepts[:3]:  # Top 3 from each book
            if concept['description']:
                all_descriptions.append(concept['description'])
    
    if all_descriptions:
        # Create unified explanation
        result += "### Unified Explanation\n\n"
        # Combine unique insights
        seen_points = set()
        for desc in all_descriptions:
            sentences = desc.split('. ')
            for sentence in sentences:
                normalized = sentence.lower().strip()
                if normalized and normalized not in seen_points and len(normalized) > 20:
                    seen_points.add(normalized)
                    result += f"- {sentence.strip()}.\n"
        result += "\n"
    
    # Technical Details by Perspective
    result += "## 🔍 Multi-Perspective Analysis\n\n"
    
    for book, book_concepts in concepts_by_book.items():
        book_name = books_metadata[book].split('(')[0].strip()
        result += f"### {book_name} Perspective\n\n"
        
        # Combine insights from this book
        for concept, score in book_concepts[:2]:  # Top 2 concepts
            if concept['content']:
                result += f"**{concept['title']}**: {concept['content'][:200]}...\n\n"
    
    # Code Examples Section
    result += "## 💻 Unified Code Examples\n\n"
    
    code_examples = []
    for book, book_concepts in concepts_by_book.items():
        for concept, _ in book_concepts:
            if concept['syntax']:
                code_examples.append({
                    'code': concept['syntax'],
                    'source': books_metadata[book],
                    'title': concept['title']
                })
    
    if code_examples:
        result += "### Comprehensive Example\n\n```c\n"
        result += "/* Synthesized from multiple sources */\n\n"
        
        # Intelligently combine code examples
        seen_patterns = set()
        for example in code_examples[:3]:  # Top 3 examples
            code_lines = example['code'].split('\n')
            result += f"/* From {example['source'].split('(')[0].strip()} */\n"
            for line in code_lines:
                normalized = line.strip().lower()
                if normalized and normalized not in seen_patterns:
                    seen_patterns.add(normalized)
                    result += f"{line}\n"
            result += "\n"
        result += "```\n\n"
    
    # Key Insights Section
    result += "## 💡 Synthesized Insights\n\n"
    
    # Generate insights based on patterns
    insights = []
    
    # Pattern: If multiple books cover it, it's fundamental
    if len(concepts_by_book) >= 3:
        insights.append(f"**Fundamental Concept**: {topic.title()} is covered across {len(concepts_by_book)} sources, indicating its critical importance in systems programming.")
    
    # Pattern: Book-specific insights
    if 'kernighan_ritchie' in concepts_by_book and 'expert_c_programming' in concepts_by_book:
        insights.append(f"**Evolution**: Compare basic {topic} concepts from K&R with advanced techniques from Expert C Programming to see the evolution of best practices.")
    
    if 'unix_env' in concepts_by_book and 'os_three_pieces' in concepts_by_book:
        insights.append(f"**System-Level View**: Both UNIX and OS perspectives provide complementary views on {topic} at the system level.")
    
    for insight in insights:
        result += f"{insight}\n\n"
    
    # Cross-References
    result += "## 🔗 Related Concepts for Deeper Understanding\n\n"
    
    # Find related topics mentioned across concepts
    related_topics = set()
    for book_concepts in concepts_by_book.values():
        for concept, _ in book_concepts:
            # Extract potential related topics from content
            content_words = (concept['content'] + ' ' + concept['description']).lower().split()
            for word in ['memory', 'pointer', 'process', 'thread', 'file', 'system', 'kernel', 'linking']:
                if word in content_words and word != topic_lower:
                    related_topics.add(word)
    
    if related_topics:
        result += "Consider exploring these related topics:\n"
        for related in sorted(related_topics)[:5]:
            result += f"- `synthesize_concepts('{related}')`\n"
    
    result += f"\n---\n*Synthesis generated from {len(concepts_by_book)} books with {sum(len(c) for c in concepts_by_book.values())} relevant concepts*"
    
    return result


@mcp.tool()
async def generate_custom_tutorial(topic: str, skill_level: str = "intermediate") -> str:
    """Generate a custom tutorial by merging related concepts across books.
    
    Args:
        topic: The topic for the tutorial (e.g., 'pointers', 'file operations')
        skill_level: Target skill level - 'beginner', 'intermediate', or 'advanced'
    """
    topic_lower = topic.lower()
    skill_level_lower = skill_level.lower()
    
    if skill_level_lower not in ['beginner', 'intermediate', 'advanced']:
        return "Invalid skill level. Please choose 'beginner', 'intermediate', or 'advanced'."
    
    # Find and categorize concepts by complexity
    beginner_concepts = []
    intermediate_concepts = []
    advanced_concepts = []
    
    for concept in concepts:
        if topic_lower in concept['title'].lower() or topic_lower in concept['description'].lower():
            # Categorize based on book and content
            if concept['book'] == 'kernighan_ritchie' or 'basic' in concept['title'].lower():
                beginner_concepts.append(concept)
            elif concept['book'] == 'expert_c_programming' or 'advanced' in concept['title'].lower():
                advanced_concepts.append(concept)
            else:
                intermediate_concepts.append(concept)
    
    # Select concepts based on skill level
    if skill_level_lower == 'beginner':
        selected_concepts = beginner_concepts + intermediate_concepts[:2]
    elif skill_level_lower == 'intermediate':
        selected_concepts = beginner_concepts[-2:] + intermediate_concepts + advanced_concepts[:2]
    else:  # advanced
        selected_concepts = intermediate_concepts[-2:] + advanced_concepts
    
    if not selected_concepts:
        return f"No concepts found to create a tutorial on '{topic}'"
    
    # Generate tutorial structure
    result = f"# 📚 Custom Tutorial: {topic.title()}\n\n"
    result += f"**Skill Level**: {skill_level.title()}\n"
    result += f"**Duration**: Approximately {len(selected_concepts) * 10} minutes\n"
    result += f"**Sources**: {len(set(c['book'] for c in selected_concepts))} books\n\n"
    
    # Learning Objectives
    result += "## 🎯 Learning Objectives\n\n"
    result += "By the end of this tutorial, you will:\n"
    
    if skill_level_lower == 'beginner':
        result += f"- Understand the fundamental concepts of {topic}\n"
        result += f"- Write basic code using {topic}\n"
        result += f"- Recognize common patterns and use cases\n"
    elif skill_level_lower == 'intermediate':
        result += f"- Master practical applications of {topic}\n"
        result += f"- Understand system-level implications\n"
        result += f"- Implement efficient solutions using {topic}\n"
    else:
        result += f"- Master advanced techniques in {topic}\n"
        result += f"- Understand optimization strategies\n"
        result += f"- Recognize and avoid common pitfalls\n"
    
    result += "\n## 📖 Tutorial Content\n\n"
    
    # Progressive lessons
    for i, concept in enumerate(selected_concepts, 1):
        result += f"### Lesson {i}: {concept['title']}\n\n"
        
        # Concept explanation
        if concept['description']:
            result += f"**Concept**: {concept['description']}\n\n"
        
        # Detailed explanation
        if concept['content']:
            result += f"**Explanation**: {concept['content'][:300]}...\n\n"
        
        # Code example
        if concept['syntax']:
            result += "**Example**:\n```c\n"
            result += concept['syntax']
            result += "\n```\n\n"
        
        # Practice exercise
        result += f"**Practice**: Try modifying the above code to "
        if skill_level_lower == 'beginner':
            result += "experiment with different values.\n\n"
        elif skill_level_lower == 'intermediate':
            result += "handle edge cases and error conditions.\n\n"
        else:
            result += "optimize for performance and memory usage.\n\n"
        
        result += "---\n\n"
    
    # Summary and Next Steps
    result += "## 🎉 Tutorial Summary\n\n"
    result += f"Congratulations! You've completed the {skill_level} tutorial on {topic}.\n\n"
    
    result += "### Key Takeaways\n"
    for concept in selected_concepts[:3]:
        result += f"- {concept['title']}\n"
    
    result += f"\n### Next Steps\n"
    if skill_level_lower == 'beginner':
        result += f"- Try `generate_custom_tutorial('{topic}', 'intermediate')` to continue learning\n"
    elif skill_level_lower == 'intermediate':
        result += f"- Explore `generate_custom_tutorial('{topic}', 'advanced')` for expert techniques\n"
    else:
        result += f"- Review `create_best_practices_guide('{topic}')` for production-ready patterns\n"
    
    result += f"- Practice with `find_code_examples('{topic}')` for more examples\n"
    
    return result


@mcp.tool()
async def create_best_practices_guide(topic: str) -> str:
    """Analyze patterns across all sources to generate best practices guide.
    
    Args:
        topic: The topic to analyze for best practices (e.g., 'error handling', 'memory management')
    """
    topic_lower = topic.lower()
    
    # Collect all relevant concepts
    relevant_concepts = []
    for concept in concepts:
        relevance_score = 0
        if topic_lower in concept['title'].lower():
            relevance_score += 3
        if topic_lower in concept['description'].lower():
            relevance_score += 2
        if topic_lower in concept['content'].lower():
            relevance_score += 1
            
        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))
    
    if not relevant_concepts:
        return f"No concepts found to generate best practices for '{topic}'"
    
    # Sort by relevance
    relevant_concepts.sort(key=lambda x: x[1], reverse=True)
    
    # Analyze patterns across books
    patterns_by_book = {}
    code_patterns = []
    common_recommendations = []
    pitfalls = []
    
    for concept, _ in relevant_concepts[:20]:  # Top 20 concepts
        book = concept['book']
        if book not in patterns_by_book:
            patterns_by_book[book] = []
        patterns_by_book[book].append(concept)
        
        # Extract patterns from content
        content = (concept['content'] + ' ' + concept['description']).lower()
        
        # Look for recommendations
        if any(word in content for word in ['should', 'must', 'always', 'recommend']):
            common_recommendations.append(concept)
        
        # Look for pitfalls
        if any(word in content for word in ['avoid', 'never', 'pitfall', 'error', 'mistake', 'wrong']):
            pitfalls.append(concept)
        
        # Collect code patterns
        if concept['syntax']:
            code_patterns.append({
                'code': concept['syntax'],
                'source': concept['book_title'],
                'context': concept['title']
            })
    
    # Generate best practices guide
    result = f"# 🏆 Best Practices Guide: {topic.title()}\n\n"
    result += f"*Analyzing {len(relevant_concepts)} concepts from {len(patterns_by_book)} authoritative sources*\n\n"
    
    # Overview
    result += "## 📊 Analysis Overview\n\n"
    result += f"This guide synthesizes best practices for {topic} based on:\n"
    for book, concepts in patterns_by_book.items():
        result += f"- **{books_metadata[book]}**: {len(concepts)} relevant concepts\n"
    result += "\n"
    
    # Core Best Practices
    result += "## ✅ Core Best Practices\n\n"
    
    # Synthesize recommendations from different sources
    practice_num = 1
    seen_practices = set()
    
    for rec_concept in common_recommendations[:8]:
        # Extract actionable practices
        sentences = rec_concept['description'].split('. ')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['should', 'must', 'always']):
                practice = sentence.strip()
                if practice.lower() not in seen_practices:
                    seen_practices.add(practice.lower())
                    result += f"### {practice_num}. {practice}\n"
                    result += f"*Source: {rec_concept['book_title']}*\n\n"
                    
                    # Add supporting code if available
                    if rec_concept['syntax']:
                        result += "**Example**:\n```c\n"
                        result += rec_concept['syntax'][:200]
                        if len(rec_concept['syntax']) > 200:
                            result += "\n// ..."
                        result += "\n```\n\n"
                    
                    practice_num += 1
    
    # Common Patterns
    result += "## 🔄 Common Implementation Patterns\n\n"
    
    if code_patterns:
        # Group similar patterns
        pattern_groups = {}
        for pattern in code_patterns[:10]:
            # Simple grouping by first significant line
            lines = pattern['code'].strip().split('\n')
            for line in lines:
                if line.strip() and not line.strip().startswith('//'):
                    key = line.strip()[:30]
                    if key not in pattern_groups:
                        pattern_groups[key] = []
                    pattern_groups[key].append(pattern)
                    break
        
        pattern_num = 1
        for key, patterns in list(pattern_groups.items())[:5]:
            result += f"### Pattern {pattern_num}: {patterns[0]['context']}\n\n"
            
            # Show variations from different sources
            for i, pattern in enumerate(patterns[:2]):
                result += f"**Approach {i+1}** ({pattern['source'].split('(')[0].strip()}):\n"
                result += "```c\n"
                result += pattern['code'][:150]
                if len(pattern['code']) > 150:
                    result += "\n// ..."
                result += "\n```\n\n"
            
            pattern_num += 1
    
    # Pitfalls to Avoid
    result += "## ⚠️ Common Pitfalls and How to Avoid Them\n\n"
    
    pitfall_num = 1
    seen_pitfalls = set()
    
    for pitfall_concept in pitfalls[:6]:
        content = pitfall_concept['description'] + ' ' + pitfall_concept['content']
        sentences = content.split('. ')
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['avoid', 'never', 'don\'t']):
                pitfall = sentence.strip()
                if pitfall.lower() not in seen_pitfalls and len(pitfall) > 20:
                    seen_pitfalls.add(pitfall.lower())
                    result += f"### Pitfall {pitfall_num}: {pitfall}\n"
                    result += f"*Identified in: {pitfall_concept['book_title']}*\n\n"
                    
                    # Add corrective action if available
                    if pitfall_concept['syntax']:
                        result += "**How to avoid**:\n```c\n"
                        result += pitfall_concept['syntax'][:150]
                        if len(pitfall_concept['syntax']) > 150:
                            result += "\n// ..."
                        result += "\n```\n\n"
                    
                    pitfall_num += 1
                    if pitfall_num > 5:
                        break
    
    # Expert Insights
    result += "## 🎓 Expert Insights\n\n"
    
    # Prioritize insights from expert books
    expert_books = ['expert_c_programming', 'unix_env']
    for book in expert_books:
        if book in patterns_by_book:
            book_concepts = patterns_by_book[book][:2]
            for concept in book_concepts:
                if concept['content']:
                    result += f"### {concept['title']}\n"
                    result += f"{concept['content'][:250]}...\n"
                    result += f"*— {books_metadata[book]}*\n\n"
    
    # Quick Reference Card
    result += "## 📋 Quick Reference Card\n\n"
    result += f"### {topic.title()} Best Practices Checklist\n\n"
    
    checklist_items = [
        f"Review relevant concepts with `search_concepts('{topic}')`",
        f"deep Study implementations across books with `synthesize_concepts('{topic}')`",
        f"Practice with examples using `find_code_examples('{topic}')`",
        "Test edge cases and error conditions",
        "Consider performance implications",
        "Document concisely your implementation decisions"
    ]
    
    for item in checklist_items:
        result += f"- [ ] {item}\n"
    
    result += f"\n---\n*Best practices guide generated from {len(relevant_concepts)} concepts across {len(patterns_by_book)} authoritative sources*"
    
    return result

def _generate_markdown_reference(topic: str, by_book: dict) -> str:
    """Generate markdown formatted reference sheet."""
    output = f"# {topic.title()} Reference Sheet\n\n"
    output += f"*Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books*\n\n"

    for book, concepts in by_book.items():
        output += f"## {book}\n\n"

        for concept in concepts:
            output += f"### {concept['title']}\n\n"

            if concept['description']:
                output += f"{concept['description']}\n\n"

            if concept['syntax']:
                output += f"```c\n{concept['syntax']}\n```\n\n"

            if concept['content']:
                output += f"**Details:** {concept['content'][:200]}{'...' if len(concept['content']) > 200 else ''}\n\n"

            output += f"*Source: {book}*\n\n---\n\n"

    return output


def _generate_html_reference(topic: str, by_book: dict) -> str:
    """Generate HTML formatted reference sheet."""
    output = f"""<!DOCTYPE html>
<html>
<head>
    <title>{topic.title()} Reference Sheet</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; }}
        h2 {{ color: #007acc; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
        .source {{ font-style: italic; color: #666; }}
    </style>
</head>
<body>
    <h1>{topic.title()} Reference Sheet</h1>
    <p><em>Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books</em></p>
"""

    for book, concepts in by_book.items():
        output += f"    <h2>{book}</h2>\n"

        for concept in concepts:
            output += f"    <h3>{concept['title']}</h3>\n"

            if concept['description']:
                output += f"    <p>{concept['description']}</p>\n"

            if concept['syntax']:
                output += f"    <pre><code>{concept['syntax']}</code></pre>\n"

            if concept['content']:
                content = concept['content'][:200] + ('...' if len(concept['content']) > 200 else '')
                output += f"    <p><strong>Details:</strong> {content}</p>\n"

            output += f"    <p class='source'>Source: {book}</p>\n    <hr>\n"

    output += "</body></html>"
    return output


def _generate_text_reference(topic: str, by_book: dict) -> str:
    """Generate plain text formatted reference sheet."""
    output = f"{topic.upper()} REFERENCE SHEET\n"
    output += "=" * len(f"{topic.upper()} REFERENCE SHEET") + "\n\n"
    output += f"Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books\n\n"

    for book, concepts in by_book.items():
        output += f"{book.upper()}\n"
        output += "-" * len(book) + "\n\n"

        for concept in concepts:
            output += f"{concept['title']}\n"

            if concept['description']:
                output += f"Description: {concept['description']}\n"

            if concept['syntax']:
                output += f"Code:\n{concept['syntax']}\n"

            if concept['content']:
                content = concept['content'][:200] + ('...' if len(concept['content']) > 200 else '')
                output += f"Details: {content}\n"

            output += f"Source: {book}\n\n"

    return output


# Initialize the concepts database when the module loads
build_concept_index()
logger.info("Programming Concepts MCP Server initialized")

if __name__ == "__main__":
    # Run the FastMCP server
    logger.info("Starting Programming Concepts MCP Server for Claude Code...")
    logger.info("MCP Server ready for Claude Code")
    mcp.run(transport='stdio')
