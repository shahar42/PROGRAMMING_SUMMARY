#!/usr/bin/env python3
"""
C Concepts MCP Server
FastMCP server providing intelligent access to C programming concepts
from a variety of authoritative books.
"""

import json
import re
import sys
from pathlib import Path
from fastmcp import FastMCP

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Initialize MCP server
mcp = FastMCP("C Concepts Server")

# Global storage for C concepts
c_concepts = []

# List of C book directories
C_BOOK_DIRS = [
    "kernighan_ritchie",
    "unix_env",
    "linkers_loaders",
    "os_three_pieces",
    "expert_c_programming",
    "csapp_2016",
    "posix_manpages"
]

def load_c_concepts():
    """Load all C concepts from the respective book directories."""
    global c_concepts
    
    c_concepts.clear()
    
    for book_name in C_BOOK_DIRS:
        concepts_dir = Path(__file__).parent / "outputs" / book_name
        if not concepts_dir.exists():
            print(f"Warning: C concepts directory not found: {concepts_dir}")
            continue
            
        concept_files = list(concepts_dir.glob("*.json"))
        concept_files = [f for f in concept_files 
                         if f.name not in ["progress.json", "metadata.json", "summary.json"]
                         and f.suffix == ".json"]
        
        for concept_file in concept_files:
            try:
                with open(concept_file, 'r') as f:
                    concept_data = json.load(f)
                
                # Generate a unique ID for the concept
                concept_id = f"{book_name}_{concept_file.stem}"
                
                # Standardize concept structure
                title = concept_data.get('topic', concept_data.get('title', 'Unknown C Concept'))
                description = concept_data.get('explanation', concept_data.get('description', ''))
                content = concept_data.get('example_explanation', '')
                syntax = concept_data.get('syntax', '')
                if not syntax and concept_data.get('code_example'):
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
                    'source_file': concept_file.name,
                    'raw_data': concept_data
                }
                
                c_concepts.append(concept)
                
            except Exception as e:
                print(f"Error loading C concept {concept_file}: {e}")
    
    print(f"Loaded {len(c_concepts)} C concepts from {len(C_BOOK_DIRS)} books")

# Load concepts on startup
load_c_concepts()

@mcp.tool()
def search_c_concepts(query: str, limit: int = 10) -> str:
    """Search for C programming concepts by keyword or topic. 
    
    Args:
        query: Search terms for C concepts (e.g., 'pointers', 'memory', 'fork')
        limit: Maximum number of results to return
    """
    if not c_concepts:
        return "No C concepts available. Please run the C extraction scripts first."
    
    query_lower = query.lower()
    results = []
    
    for concept in c_concepts:
        searchable_text = (
            concept['title'].lower() + ' ' +
            concept['description'].lower() + ' ' + 
            concept['content'].lower()
        )
        
        if query_lower in searchable_text:
            score = searchable_text.count(query_lower)
            results.append((concept, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    results = results[:limit]
    
    if not results:
        return f"No C concepts found for query: '{query}'"
    
    result_text = f"# C Concepts Search Results for '{query}'\n\n"
    result_text += f"Found {len(results)} relevant C concepts:\n\n"
    
    for concept, score in results:
        result_text += f"## {concept['title']}\n"
        result_text += f"**ID:** `{concept['id']}`\n"
        result_text += f"**Book:** {concept['book']}\n"
        result_text += f"**Description:** {concept['description'][:200]}{'...' if len(concept['description']) > 200 else ''}\n\n"
    
    return result_text

@mcp.tool()
def get_c_concept_details(concept_id: str) -> str:
    """Get detailed information about a specific C concept. 
    
    Args:
        concept_id: The ID of the C concept (e.g., 'kernighan_ritchie_concept_001')
    """
    concept = next((c for c in c_concepts if c['id'] == concept_id), None)
    
    if not concept:
        return f"C concept not found: {concept_id}"
    
    result = f"# {concept['title']}\n\n"
    result += f"**Concept ID:** `{concept['id']}`\n"
    result += f"**Book:** {concept['book']}\n\n"
    
    result += f"## Description\n{concept['description']}\n\n"
    
    if concept['content']:
        result += f"## Detailed Explanation\n{concept['content']}\n\n"
    
    if concept['syntax']:
        result += f"## C Code Example\n```c\n{concept['syntax']}\n```\n\n"
    
    return result

@mcp.tool()
def list_c_concepts_by_book() -> str:
    """List all C concepts organized by book."""
    if not c_concepts:
        return "No C concepts available."
    
    by_book = {}
    for concept in c_concepts:
        book = concept['book']
        if book not in by_book:
            by_book[book] = []
        by_book[book].append(concept)
    
    result_text = "# C Concepts by Book\n\n"
    result_text += f"Total C concepts: {len(c_concepts)}\n\n"
    
    for book in C_BOOK_DIRS:
        if book in by_book:
            concepts = by_book[book]
            result_text += f"## {book} ({len(concepts)} concepts)\n\n"
            
            for concept in concepts[:5]: # Show first 5 concepts
                result_text += f"- **{concept['title']}** (`{concept['id']}`)\n"
            if len(concepts) > 5:
                result_text += "- ... and more\n"
            result_text += "\n"

    return result_text

if __name__ == "__main__":
    mcp.run()
