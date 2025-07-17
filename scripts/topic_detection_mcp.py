#!/usr/bin/env python3
"""
Programming Topic Detection MCP Server
Part 1: Intelligent routing for programming questions to appropriate book servers
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add current directory to Python path
sys.path.append('.')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic-detection-mcp")

# Initialize FastMCP server
mcp = FastMCP("topic-detection")

# Book configurations from your existing setup
BOOK_CONFIGS = {
    "kernighan_ritchie": {
        "name": "K&R C Programming",
        "focus": "C language syntax, operators, control structures, functions",
        "keywords": ["malloc", "free", "pointer", "struct", "array", "function", "printf", "scanf", 
                    "for", "while", "if", "else", "int", "char", "string", "variable", "const",
                    "extern", "static", "typedef", "sizeof", "bitwise", "assignment", "operators"]
    },
    "unix_env": {
        "name": "UNIX Environment", 
        "focus": "System calls, APIs, UNIX programming patterns, file operations",
        "keywords": ["fork", "exec", "signal", "pipe", "file", "descriptor", "process", "thread",
                    "read", "write", "open", "close", "ioctl", "mmap", "socket", "unix", "system",
                    "environment", "api", "syscall", "stat", "chmod"]
    },
    "linkers_loaders": {
        "name": "Linkers & Loaders",
        "focus": "Binary formats, linking mechanics, loader concepts, object files", 
        "keywords": ["linking", "loader", "symbol", "undefined", "reference", "shared", "library",
                    "object", "binary", "elf", "dynamic", "static", "relocation", "section",
                    "segment", "compilation", "build", "makefile", "ld"]
    },
    "os_three_pieces": {
        "name": "Operating Systems",
        "focus": "OS algorithms, data structures, system concepts, concurrency",
        "keywords": ["scheduler", "memory", "virtual", "page", "tlb", "cache", "interrupt", 
                    "context", "switch", "mutex", "semaphore", "deadlock", "race", "condition",
                    "filesystem", "inode", "kernel", "cpu", "algorithm", "concurrency"]
    },
    "expert_c_programming": {
        "name": "Expert C Programming", 
        "focus": "Advanced C techniques, pitfalls, expert-level programming",
        "keywords": ["optimization", "pitfall", "undefined", "behavior", "volatile", "register",
                    "inline", "pragma", "casting", "alignment", "endian", "performance", "debug",
                    "profiling", "expert", "advanced", "tricks", "secrets"]
    }
}

def load_extracted_concepts():
    """Load actual extracted concept topics as additional keywords"""
    concepts_by_book = {}
    
    # Try to load from your outputs directory structure
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        for book_dir in outputs_dir.iterdir():
            if book_dir.is_dir() and book_dir.name in BOOK_CONFIGS:
                book_concepts = []
                for concept_file in book_dir.glob("concept_*.json"):
                    try:
                        with open(concept_file, 'r', encoding='utf-8') as f:
                            concept = json.load(f)
                            # Extract key terms from topic
                            topic_words = re.findall(r'\b\w+\b', concept['topic'].lower())
                            book_concepts.extend(topic_words)
                    except Exception as e:
                        logger.warning(f"Could not load {concept_file}: {e}")
                
                concepts_by_book[book_dir.name] = list(set(book_concepts))
                logger.info(f"Loaded {len(book_concepts)} concept keywords from {book_dir.name}")
    
    return concepts_by_book

def calculate_topic_scores(user_input: str) -> Dict[str, Dict]:
    """Calculate relevance scores for each book based on keyword matching"""
    user_words = re.findall(r'\b\w+\b', user_input.lower())
    
    # Load extracted concepts to enhance keyword matching
    extracted_concepts = load_extracted_concepts()
    
    book_scores = {}
    
    for book_id, config in BOOK_CONFIGS.items():
        # Combine predefined keywords with extracted concept terms
        all_keywords = config["keywords"].copy()
        if book_id in extracted_concepts:
            all_keywords.extend(extracted_concepts[book_id])
        
        # Calculate score based on keyword matches
        matches = [word for word in user_words if word in all_keywords]
        score = len(matches) / len(user_words) if user_words else 0
        
        # Boost score for exact phrase matches in focus area
        focus_words = config["focus"].lower().split()
        for phrase in [" ".join(focus_words[i:i+2]) for i in range(len(focus_words)-1)]:
            if phrase in user_input.lower():
                score += 0.3
        
        book_scores[book_id] = {
            "name": config["name"],
            "score": round(score, 3),
            "matches": matches,
            "focus": config["focus"]
        }
    
    return book_scores

def get_recommendations(book_scores: Dict[str, Dict]) -> Dict:
    """Generate server recommendations based on scores"""
    # Sort books by score
    sorted_books = sorted(book_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    # Determine primary and secondary recommendations
    primary = []
    secondary = []
    
    for book_id, data in sorted_books:
        if data["score"] >= 0.15:  # Strong relevance threshold
            primary.append(f"{data['name']}-server")
        elif data["score"] >= 0.05:  # Moderate relevance threshold
            secondary.append(f"{data['name']}-server")
    
    # Ensure at least one recommendation
    if not primary and sorted_books:
        primary.append(f"{sorted_books[0][1]['name']}-server")
    
    return {
        "primary": primary[:2],  # Max 2 primary recommendations
        "secondary": secondary[:2],  # Max 2 secondary recommendations
        "top_match": sorted_books[0] if sorted_books else None
    }

@mcp.tool()
def detect_programming_topics(user_question: str) -> str:
    """
    Analyze a programming question and recommend which book servers to consult.
    
    Args:
        user_question: The programming question or topic to analyze
        
    Returns:
        Natural language recommendation with confidence and reasoning
    """
    if not user_question.strip():
        return "Please provide a programming question to analyze."
    
    # Calculate topic relevance scores
    book_scores = calculate_topic_scores(user_question)
    recommendations = get_recommendations(book_scores)
    
    # Generate natural, concise response
    if not recommendations["primary"]:
        return "Unable to determine the best server for this question. Try rephrasing with more specific programming terms."
    
    # Get details of top match
    top_book_id, top_data = recommendations["top_match"]
    confidence = "high" if top_data["score"] >= 0.3 else "moderate" if top_data["score"] >= 0.15 else "low"
    
    # Build response
    response_parts = []
    
    # Primary recommendation
    response_parts.append(f"**Recommended:** {', '.join(recommendations['primary'])}")
    
    # Confidence and reasoning
    if top_data["matches"]:
        key_terms = ", ".join(top_data["matches"][:3])
        response_parts.append(f"**Confidence:** {confidence} (detected: {key_terms})")
    
    # Focus area context
    response_parts.append(f"**Why:** {top_data['focus']}")
    
    # Secondary suggestions if available
    if recommendations["secondary"]:
        response_parts.append(f"**Also consider:** {', '.join(recommendations['secondary'])}")
    
    return "\n".join(response_parts)

@mcp.tool()
def list_available_servers() -> str:
    """List all available book servers and their focus areas"""
    
    server_list = []
    for book_id, config in BOOK_CONFIGS.items():
        server_name = f"{config['name']}-server"
        server_list.append(f"• **{server_name}:** {config['focus']}")
    
    return "**Available Programming Book Servers:**\n" + "\n".join(server_list)

@mcp.tool()
def analyze_topic_coverage(user_question: str) -> str:
    """
    Detailed analysis of how each book server relates to the question.
    
    Args:
        user_question: Programming question to analyze
        
    Returns:
        Detailed breakdown of relevance scores and reasoning
    """
    if not user_question.strip():
        return "Please provide a programming question to analyze."
    
    book_scores = calculate_topic_scores(user_question)
    
    analysis_parts = [f"**Topic Analysis for:** \"{user_question}\"\n"]
    
    # Sort by relevance
    sorted_scores = sorted(book_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    for book_id, data in sorted_scores:
        score_bar = "█" * int(data["score"] * 20) + "░" * (5 - int(data["score"] * 20))
        relevance = "High" if data["score"] >= 0.3 else "Medium" if data["score"] >= 0.15 else "Low"
        
        analysis_parts.append(
            f"**{data['name']}:** {score_bar} {data['score']:.3f} ({relevance})\n"
            f"  Keywords: {', '.join(data['matches'][:5]) if data['matches'] else 'none'}\n"
            f"  Focus: {data['focus']}\n"
        )
    
    return "\n".join(analysis_parts)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
