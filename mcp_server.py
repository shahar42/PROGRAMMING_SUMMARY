#!/usr/bin/env python3
"""
Programming Concepts MCP Server
Serves archaeological extraction database to Claude via MCP protocol
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# MCP server imports
try:
    from mcp.server.fastmcp import FastMCP
    from typing import Annotated
except ImportError:
    print("MCP package not found. Install with: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("programming-concepts-mcp")

class ConceptDatabase:
    """Manages the archaeological extraction database"""
    
    def __init__(self, concepts_root: str = "outputs"):
        self.concepts_root = Path(concepts_root)
        self.concepts_index: Dict[str, Dict] = {}
        self.book_metadata = {
            "kernighan_ritchie": {
                "title": "The C Programming Language",
                "authors": "Kernighan & Ritchie",
                "focus": "C language fundamentals"
            },
            "unix_env": {
                "title": "Advanced Programming in the UNIX Environment", 
                "authors": "W. Richard Stevens",
                "focus": "UNIX system programming"
            },
            "linkers_loaders": {
                "title": "Linkers and Loaders",
                "authors": "John R. Levine", 
                "focus": "Binary formats and linking"
            },
            "os_three_pieces": {
                "title": "Operating Systems: Three Easy Pieces",
                "authors": "Remzi H. Arpaci-Dusseau",
                "focus": "Operating system concepts"
            }
        }
        self._build_index()
    
    def _build_index(self):
        """Build searchable index of all extracted concepts"""
        logger.info(f"Building concept index from {self.concepts_root}")
        
        concept_count = 0
        for book_dir in self.concepts_root.iterdir():
            if not book_dir.is_dir():
                continue
                
            book_name = book_dir.name
            logger.info(f"Indexing book: {book_name}")
            
            # Find all concept JSON files
            concept_files = list(book_dir.glob("*concept_*.json"))
            logger.info(f"Found {len(concept_files)} concepts in {book_name}")
            
            for concept_file in concept_files:
                try:
                    with open(concept_file, 'r', encoding='utf-8') as f:
                        concept_data = json.load(f)
                    
                    # Create unique concept ID
                    concept_id = f"{book_name}_{concept_file.stem}"
                    
                    # Enhance concept with metadata
                    enhanced_concept = {
                        **concept_data,
                        "concept_id": concept_id,
                        "book": book_name,
                        "book_title": self.book_metadata.get(book_name, {}).get("title", book_name),
                        "file_path": str(concept_file),
                        "search_text": f"{concept_data.get('topic', '')} {concept_data.get('explanation', '')}"
                    }
                    
                    self.concepts_index[concept_id] = enhanced_concept
                    concept_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to index {concept_file}: {e}")
        
        logger.info(f"Successfully indexed {concept_count} concepts across {len(self.book_metadata)} books")
    
    def search_concepts(self, query: str, book: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search concepts by query with optional book filter"""
        results = []
        query_lower = query.lower()
        
        for concept_id, concept in self.concepts_index.items():
            # Apply book filter if specified
            if book and concept['book'] != book:
                continue
            
            # Search in topic, explanation, and syntax
            searchable_text = concept['search_text'].lower()
            if query_lower in searchable_text:
                results.append({
                    'concept_id': concept_id,
                    'topic': concept['topic'],
                    'book': concept['book'],
                    'book_title': concept['book_title'],
                    'explanation': concept['explanation'][:200] + "..." if len(concept['explanation']) > 200 else concept['explanation'],
                    'syntax': concept.get('syntax', 'N/A')
                })
        
        # Sort by relevance (simple: topic matches first)
        results.sort(key=lambda x: query_lower in x['topic'].lower(), reverse=True)
        return results[:limit]
    
    def get_concept_by_id(self, concept_id: str) -> Optional[Dict]:
        """Get full concept details by ID"""
        return self.concepts_index.get(concept_id)
    
    def list_books(self) -> List[Dict]:
        """List all available books with concept counts"""
        book_stats = {}
        
        # Count concepts per book
        for concept in self.concepts_index.values():
            book = concept['book']
            if book not in book_stats:
                book_stats[book] = 0
            book_stats[book] += 1
        
        # Build book list with metadata
        books = []
        for book_name, metadata in self.book_metadata.items():
            books.append({
                'book_id': book_name,
                'title': metadata['title'],
                'authors': metadata['authors'], 
                'focus': metadata['focus'],
                'concept_count': book_stats.get(book_name, 0)
            })
        
        return books
    
    def get_concepts_by_topic(self, topic: str, limit: int = 5) -> List[Dict]:
        """Find concepts related to a specific topic"""
        return self.search_concepts(topic, limit=limit)

# Initialize FastMCP server
mcp = FastMCP("programming-concepts-mcp")
database = ConceptDatabase()
logger.info("Programming Concepts MCP Server initialized")

@mcp.tool()
def search_concepts(query: str, book: str = None, limit: int = 10) -> str:
    """Search programming concepts by topic, keyword, or concept name"""
    results = database.search_concepts(query=query, book=book, limit=limit)
    
    if not results:
        return f"No concepts found for query: '{query}'"
    
    response = f"Found {len(results)} programming concepts:\n\n"
    for i, result in enumerate(results, 1):
        response += f"{i}. **{result['topic']}** ({result['book_title']})\n"
        response += f"   ID: `{result['concept_id']}`\n"
        response += f"   Syntax: `{result['syntax']}`\n"
        response += f"   {result['explanation']}\n\n"
    
    return response

@mcp.tool()
def get_concept_details(concept_id: str) -> str:
    """Get complete details of a specific programming concept including code examples"""
    concept = database.get_concept_by_id(concept_id)
    
    if not concept:
        return f"Concept not found: {concept_id}"
    
    response = f"# {concept['topic']}\n\n"
    response += f"**Source:** {concept['book_title']}\n"
    response += f"**Pages:** {concept.get('extraction_metadata', {}).get('page_range', 'N/A')}\n\n"
    response += f"## Explanation\n{concept['explanation']}\n\n"
    response += f"## Syntax\n```\n{concept.get('syntax', 'N/A')}\n```\n\n"
    
    if concept.get('code_example'):
        response += "## Code Example\n```c\n"
        response += "\n".join(concept['code_example'])
        response += "\n```\n\n"
    
    if concept.get('example_explanation'):
        response += f"## Example Explanation\n{concept['example_explanation']}\n"
    
    return response

@mcp.tool()
def list_books() -> str:
    """List all available programming books in the database with statistics"""
    books = database.list_books()
    response = "# Available Programming Books\n\n"
    for book in books:
        response += f"## {book['title']}\n"
        response += f"- **Authors:** {book['authors']}\n"
        response += f"- **Focus:** {book['focus']}\n"
        response += f"- **Concepts:** {book['concept_count']} extracted\n"
        response += f"- **Book ID:** `{book['book_id']}`\n\n"
    
    return response

@mcp.tool()
def get_concepts_by_topic(topic: str, limit: int = 5) -> str:
    """Find programming concepts related to a specific topic across all books"""
    results = database.get_concepts_by_topic(topic=topic, limit=limit)
    
    if not results:
        return f"No concepts found for topic: '{topic}'"
    
    response = f"# Programming Concepts: {topic}\n\n"
    for result in results:
        response += f"## {result['topic']} ({result['book_title']})\n"
        response += f"**ID:** `{result['concept_id']}`\n"
        response += f"**Syntax:** `{result['syntax']}`\n"
        response += f"{result['explanation']}\n\n"
    
    return response

def main():
    """Main MCP server entry point"""
    logger.info("Starting Programming Concepts MCP Server for Claude Code...")
    logger.info("MCP Server ready for Claude Code")
    
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
