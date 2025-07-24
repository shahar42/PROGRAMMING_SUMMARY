#!/usr/bin/env python3
"""
CSAPP (Computer Systems: A Programmer's Perspective) MCP Server
Specialized server for computer systems and architecture concepts

Provides focused access to systems programming concepts, computer architecture,
memory hierarchy, performance optimization, and hardware-software interaction.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re

# Add project root to path
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
sys.path.append(PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("csapp-server")

# Initialize FastMCP server
mcp = FastMCP("csapp-concepts")

# Global storage for CSAPP concepts
CSAPP_CONCEPTS = {}
CONCEPTS_LOADED = False

def load_csapp_concepts():
    """Load all CSAPP concepts from JSON files"""
    global CSAPP_CONCEPTS, CONCEPTS_LOADED
    
    if CONCEPTS_LOADED:
        return CSAPP_CONCEPTS
    
    concepts_dir = Path(PROJECT_ROOT) / "outputs" / "csapp_2016"
    
    if not concepts_dir.exists():
        logger.warning(f"CSAPP concepts directory not found: {concepts_dir}")
        return {}
    
    concept_files = list(concepts_dir.glob("*concept_*.json"))
    logger.info(f"Found {len(concept_files)} CSAPP concept files")
    
    for concept_file in concept_files:
        try:
            with open(concept_file, 'r', encoding='utf-8') as f:
                concept = json.load(f)
                
            # Create searchable ID
            concept_id = concept_file.stem  # e.g., concept_001
            
            # Add metadata
            concept['concept_id'] = concept_id
            concept['source_book'] = 'csapp_2016'
            concept['book_title'] = 'Computer Systems: A Programmer\'s Perspective'
            
            CSAPP_CONCEPTS[concept_id] = concept
            
        except Exception as e:
            logger.error(f"Error loading concept {concept_file}: {e}")
    
    CONCEPTS_LOADED = True
    logger.info(f"✅ Loaded {len(CSAPP_CONCEPTS)} CSAPP concepts")
    return CSAPP_CONCEPTS

@mcp.tool()
def search_concepts(query: str, limit: int = 10) -> Dict:
    """
    Search CSAPP concepts for systems programming and architecture topics
    
    Args:
        query: Search terms (e.g., "cache memory", "virtual address", "assembly")
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with search results and metadata
    """
    concepts = load_csapp_concepts()
    
    if not concepts:
        return {
            "results": [],
            "total_found": 0,
            "query": query,
            "message": "No CSAPP concepts loaded yet. Run concept extraction first."
        }
    
    # Normalize query
    query_lower = query.lower()
    query_terms = re.findall(r'\w+', query_lower)
    
    # Score concepts by relevance
    scored_results = []
    
    for concept_id, concept in concepts.items():
        score = 0
        text_to_search = f"{concept.get('topic', '')} {concept.get('explanation', '')} {concept.get('syntax', '')} {' '.join(concept.get('code_example', []))}"
        text_lower = text_to_search.lower()
        
        # Calculate relevance score
        for term in query_terms:
            if term in text_lower:
                # Higher score for matches in topic
                if term in concept.get('topic', '').lower():
                    score += 10
                # Medium score for matches in explanation
                elif term in concept.get('explanation', '').lower():
                    score += 5
                # Lower score for matches in code
                else:
                    score += 2
        
        if score > 0:
            scored_results.append((score, concept))
    
    # Sort by relevance and limit results
    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_results[:limit]
    
    # Format results
    formatted_results = []
    for score, concept in top_results:
        formatted_results.append({
            "concept_id": concept['concept_id'],
            "topic": concept.get('topic', 'Unknown Topic'),
            "explanation": concept.get('explanation', '')[:200] + "..." if len(concept.get('explanation', '')) > 200 else concept.get('explanation', ''),
            "relevance_score": score,
            "page_range": concept.get('extraction_metadata', {}).get('page_range', 'Unknown'),
            "has_code": bool(concept.get('code_example'))
        })
    
    return {
        "results": formatted_results,
        "total_found": len(scored_results),
        "query": query,
        "search_focus": "Computer Systems & Architecture",
        "book_source": "CSAPP - Computer Systems: A Programmer's Perspective"
    }

@mcp.tool()
def get_concept_details(concept_id: str) -> Dict:
    """
    Get detailed information about a specific CSAPP concept
    
    Args:
        concept_id: The concept ID (e.g., "concept_001")
    
    Returns:
        Complete concept details including code examples
    """
    concepts = load_csapp_concepts()
    
    if concept_id not in concepts:
        return {
            "error": f"Concept '{concept_id}' not found",
            "available_concepts": list(concepts.keys())[:10],
            "total_concepts": len(concepts)
        }
    
    concept = concepts[concept_id]
    
    # Format code example for display
    code_display = ""
    if concept.get('code_example'):
        code_display = "\n".join(concept['code_example'])
    
    return {
        "concept_id": concept_id,
        "topic": concept.get('topic', 'Unknown Topic'),
        "explanation": concept.get('explanation', ''),
        "syntax": concept.get('syntax', ''),
        "code_example": code_display,
        "example_explanation": concept.get('example_explanation', ''),
        "extraction_metadata": concept.get('extraction_metadata', {}),
        "systems_focus": "Computer Architecture & Systems Programming",
        "book_source": "Computer Systems: A Programmer's Perspective (CSAPP)"
    }

@mcp.tool()
def list_all_concepts() -> Dict:
    """
    List all available CSAPP concepts with basic information
    
    Returns:
        List of all concepts with topics and metadata
    """
    concepts = load_csapp_concepts()
    
    concept_list = []
    for concept_id, concept in concepts.items():
        concept_list.append({
            "concept_id": concept_id,
            "topic": concept.get('topic', 'Unknown Topic'),
            "page_range": concept.get('extraction_metadata', {}).get('page_range', 'Unknown'),
            "has_code": bool(concept.get('code_example')),
            "extraction_date": concept.get('extraction_metadata', {}).get('extraction_date', 'Unknown')
        })
    
    # Sort by concept_id for consistent ordering
    concept_list.sort(key=lambda x: x['concept_id'])
    
    return {
        "concepts": concept_list,
        "total_count": len(concept_list),
        "book_focus": "Computer Systems & Architecture",
        "source": "Computer Systems: A Programmer's Perspective (CSAPP)",
        "content_areas": [
            "Machine-level programming",
            "Processor architecture", 
            "Memory hierarchy",
            "Virtual memory systems",
            "Concurrency & synchronization",
            "System software",
            "Network programming",
            "Performance optimization"
        ]
    }

@mcp.tool()
def search_by_topic_area(area: str) -> Dict:
    """
    Search concepts by specific CSAPP topic areas
    
    Args:
        area: Topic area (machine, memory, concurrency, network, performance, etc.)
    
    Returns:
        Concepts filtered by topic area
    """
    concepts = load_csapp_concepts()
    area_lower = area.lower()
    
    # Define topic area keywords
    area_keywords = {
        "machine": ["assembly", "instruction", "register", "stack", "calling convention"],
        "memory": ["cache", "virtual memory", "page", "tlb", "memory hierarchy"],
        "concurrency": ["thread", "synchronization", "mutex", "semaphore", "race condition"],
        "network": ["socket", "tcp", "client", "server", "protocol"],
        "performance": ["optimization", "pipeline", "branch prediction", "profiling"],
        "architecture": ["processor", "cpu", "pipeline", "hazard", "branch"]
    }
    
    # Find matching keywords
    keywords = []
    for topic, topic_keywords in area_keywords.items():
        if area_lower in topic or topic in area_lower:
            keywords.extend(topic_keywords)
    
    if not keywords:
        keywords = [area_lower]  # Use the area term itself
    
    # Search using keywords
    results = []
    for concept_id, concept in concepts.items():
        text_to_search = f"{concept.get('topic', '')} {concept.get('explanation', '')}"
        text_lower = text_to_search.lower()
        
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
        
        if score > 0:
            results.append({
                "concept_id": concept_id,
                "topic": concept.get('topic', 'Unknown Topic'),
                "explanation": concept.get('explanation', '')[:150] + "...",
                "relevance": score,
                "page_range": concept.get('extraction_metadata', {}).get('page_range', 'Unknown')
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return {
        "area_searched": area,
        "keywords_used": keywords,
        "results": results,
        "total_found": len(results),
        "book_source": "CSAPP - Computer Systems: A Programmer's Perspective"
    }

if __name__ == "__main__":
    # Test concept loading
    logger.info("🚀 Starting CSAPP Concepts Server")
    concepts = load_csapp_concepts()
    logger.info(f"📚 Ready with {len(concepts)} CSAPP concepts")
    
    # Run the server
    mcp.run()
