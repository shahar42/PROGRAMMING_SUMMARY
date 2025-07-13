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
    "os_three_pieces": "Operating Systems: Three Easy Pieces (Arpaci-Dusseau)"
}

def build_concept_index():
    """Build the concept index from outputs directory."""
    global concepts
    
    logger.info("Building concept index from outputs")
    
    outputs_dir = Path("outputs")
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
    
    logger.info(f"Successfully indexed {total_concepts} concepts across {len([k for k in books_metadata.keys() if any(Path('outputs').glob(f'{k}/*.json'))])} books")

def add_concept(concept_data: Dict[str, Any], book_name: str, filename: str):
    """Add a concept to the index."""
    global concepts
    
    # Generate a unique ID for the concept
    concept_id = f"{book_name}_{filename.replace('.json', '')}_{len(concepts)}"
    
    # Extract key information
    title = concept_data.get('title', concept_data.get('concept', 'Unknown Concept'))
    description = concept_data.get('description', concept_data.get('summary', ''))
    content = concept_data.get('content', concept_data.get('explanation', ''))
    syntax = concept_data.get('syntax', concept_data.get('code', ''))
    
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
        if key not in ['title', 'description', 'content', 'syntax', 'concept', 'summary', 'explanation', 'code'] and value:
            result_text += f"**{key.title()}:** {value}\n"
    
    return result_text

# Initialize the concepts database when the module loads
build_concept_index()
logger.info("Programming Concepts MCP Server initialized")

if __name__ == "__main__":
    # Run the FastMCP server
    logger.info("Starting Programming Concepts MCP Server for Claude Code...")
    logger.info("MCP Server ready for Claude Code")
    mcp.run(transport='stdio')
