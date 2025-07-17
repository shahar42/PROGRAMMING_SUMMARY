#!/usr/bin/env python3
"""
UNIX Environment MCP Server
Focused on system calls, APIs, UNIX programming patterns, file operations
"""

import json
import sys
from pathlib import Path

sys.path.append('.')
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unix-environment")

# Load UNIX concepts only
concepts = []
book_name = "unix_env"
book_title = "Advanced Programming in the UNIX Environment (Stevens)"

def load_concepts():
    """Load UNIX Environment concepts from outputs directory"""
    global concepts
    concepts_dir = Path("outputs") / book_name
    
    if not concepts_dir.exists():
        return
        
    for concept_file in concepts_dir.glob("concept_*.json"):
        try:
            with open(concept_file, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)
                
                concept = {
                    'id': f"{book_name}_{concept_file.stem}",
                    'title': concept_data.get('topic', 'Unknown'),
                    'description': concept_data.get('explanation', ''),
                    'content': concept_data.get('example_explanation', ''),
                    'syntax': concept_data.get('syntax', ''),
                    'code_example': concept_data.get('code_example', []),
                    'raw_data': concept_data
                }
                concepts.append(concept)
        except Exception:
            continue

@mcp.tool()
def search_concepts(query: str, limit: int = 10) -> str:
    """Search UNIX Environment programming concepts"""
    if not query.strip():
        return "Please provide a search query"
        
    query_lower = query.lower()
    matches = []
    
    for concept in concepts:
        if (query_lower in concept['title'].lower() or 
            query_lower in concept['description'].lower() or
            query_lower in concept['content'].lower()):
            matches.append(concept)
            if len(matches) >= limit:
                break
    
    if not matches:
        return f"No UNIX Environment concepts found for: '{query}'"
    
    result = f"Found {len(matches)} UNIX Environment concepts:\n\n"
    for i, concept in enumerate(matches, 1):
        result += f"{i}. **{concept['title']}**\n"
        if concept['description']:
            desc = concept['description'][:100] + "..." if len(concept['description']) > 100 else concept['description']
            result += f"   {desc}\n"
        result += f"   ID: `{concept['id']}`\n\n"
    
    return result

@mcp.tool()
def get_concept_details(concept_id: str) -> str:
    """Get detailed information about a UNIX Environment concept"""
    concept = next((c for c in concepts if c['id'] == concept_id), None)
    
    if not concept:
        return f"UNIX Environment concept not found: {concept_id}"
    
    result = f"# {concept['title']}\n\n**Source:** {book_title}\n\n"
    
    if concept['description']:
        result += f"## Description\n{concept['description']}\n\n"
    
    if concept['content']:
        result += f"## Details\n{concept['content']}\n\n"
    
    if concept['syntax']:
        result += f"## Syntax\n```c\n{concept['syntax']}\n```\n\n"
    
    if concept['code_example']:
        code = '\n'.join(concept['code_example']) if isinstance(concept['code_example'], list) else concept['code_example']
        result += f"## Code Example\n```c\n{code}\n```\n\n"
    
    return result

@mcp.tool()
def list_all_concepts() -> str:
    """List all available UNIX Environment concepts"""
    if not concepts:
        return "No UNIX Environment concepts loaded"
    
    result = f"**{book_title}** - {len(concepts)} concepts:\n\n"
    for i, concept in enumerate(concepts, 1):
        result += f"{i}. {concept['title']}\n"
    
    return result

# Load concepts on startup
load_concepts()

if __name__ == "__main__":
    print(f"🚀 Starting UNIX Environment server with {len(concepts)} concepts")
    mcp.run()
