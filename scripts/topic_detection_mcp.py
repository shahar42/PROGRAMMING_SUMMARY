#!/usr/bin/env python3
"""
Programming Topic Detection MCP Server
Part 1: Intelligent routing for programming questions to appropriate book servers
Enhanced with caching and phrase-aware keyword extraction
"""

import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Add current directory to Python path
sys.path.append('.')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic-detection-mcp")

# Initialize FastMCP server
mcp = FastMCP("topic-detection")

# Global cache for extracted concepts
EXTRACTED_CONCEPTS_CACHE = {}
CACHE_LAST_UPDATED = {}
CACHE_FILE_TIMESTAMPS = {}

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

MEMORY_OPTIMIZATION_KEYWORDS = {
    # High relevance (0.8-1.0) - Core memory optimization terms
    'cache': 0.9,
    'memory locality': 0.95,
    'tlb': 0.9,
    'cache miss': 0.95,
    'cache line': 0.9,
    'memory optimization': 0.95,
    'cache optimization': 0.95,
    'spatial locality': 0.9,
    'temporal locality': 0.9,
    'cache blocking': 0.85,
    'memory alignment': 0.85,
    
    # Medium-high relevance (0.6-0.8) - Related performance terms
    'prefetch': 0.8,
    'memory bandwidth': 0.8,
    'cache hierarchy': 0.8,
    'virtual memory': 0.7,
    'page fault': 0.75,
    'numa': 0.8,
    'memory performance': 0.85,
    'access pattern': 0.75,
    'data locality': 0.8,
    'cache friendly': 0.8,
    
    # Medium relevance (0.4-0.6) - Broader terms
    'memory': 0.5,
    'performance': 0.4,
    'optimization': 0.4,
    'array access': 0.6,
    'matrix': 0.5,
    'loop optimization': 0.6,
    'data structure': 0.5,
    'bottleneck': 0.5,
    
    # Specific technical terms (0.7-0.9)
    'huge pages': 0.8,
    'tlb miss': 0.9,
    'cache hit': 0.85,
    'memory hierarchy': 0.8,
    'false sharing': 0.85,
    'cache coherence': 0.8,
    'memory pool': 0.7,
    'memory allocator': 0.7,
    'struct packing': 0.8,
    'memory fragmentation': 0.75,
    'prefetching': 0.8,
    'memory bound': 0.8,
    'memory intensive': 0.75,
    'cache efficiency': 0.85,
    'memory subsystem': 0.8,
    'stride': 0.7,
    'page size': 0.7,
    'memory mapping': 0.7,
    'cache size': 0.75,
    'working set': 0.7
}

def extract_keywords_from_topic(topic: str) -> Tuple[List[str], List[str]]:
    """
    Extract both phrases and individual keywords from a concept topic.
    
    Args:
        topic: The concept topic string (e.g., "External Variables in C")
        
    Returns:
        Tuple of (phrases, individual_words)
    """
    # Keep the full topic as a primary phrase (cleaned)
    primary_phrase = topic.lower().strip()
    phrases = [primary_phrase]
    
    # Extract meaningful sub-phrases (2-3 words)
    words = re.findall(r'\b\w+\b', topic.lower())
    sub_phrases = []
    
    # Create 2-word phrases
    for i in range(len(words) - 1):
        if words[i] not in ['in', 'of', 'the', 'and', 'or', 'with', 'for', 'to']:
            sub_phrases.append(f"{words[i]} {words[i+1]}")
    
    # Create 3-word phrases for longer topics
    if len(words) >= 3:
        for i in range(len(words) - 2):
            if not any(stop in [words[i], words[i+1], words[i+2]] 
                      for stop in ['in', 'of', 'the', 'and', 'or', 'with', 'for', 'to']):
                sub_phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
    
    phrases.extend(sub_phrases)
    
    # Extract important individual words (filter out common words)
    stop_words = {'in', 'of', 'the', 'and', 'or', 'with', 'for', 'to', 'a', 'an', 'is', 'are', 'using'}
    individual_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return phrases, individual_words

def get_file_modification_times(outputs_dir: Path) -> Dict[str, float]:
    """Get modification times for all concept files"""
    file_times = {}
    
    if not outputs_dir.exists():
        return file_times
        
    for book_dir in outputs_dir.iterdir():
        if book_dir.is_dir() and book_dir.name in BOOK_CONFIGS:
            for concept_file in book_dir.glob("concept_*.json"):
                try:
                    file_times[str(concept_file)] = concept_file.stat().st_mtime
                except OSError:
                    pass  # Skip files we can't read
                    
    return file_times

def cache_needs_refresh() -> bool:
    """Check if cache needs to be refreshed based on file modification times"""
    if not EXTRACTED_CONCEPTS_CACHE:
        return True  # Cache is empty
        
    outputs_dir = Path("outputs")
    current_times = get_file_modification_times(outputs_dir)
    
    # Check if any files are newer than our cache
    for file_path, mod_time in current_times.items():
        if file_path not in CACHE_FILE_TIMESTAMPS:
            return True  # New file found
        if mod_time > CACHE_FILE_TIMESTAMPS[file_path]:
            return True  # File was modified
            
    return False

def load_extracted_concepts() -> Dict[str, Dict[str, List[str]]]:
    """
    Load actual extracted concept topics with caching and auto-refresh.
    
    Returns:
        Dict with structure: {book_id: {"phrases": [...], "words": [...]}}
    """
    global EXTRACTED_CONCEPTS_CACHE, CACHE_LAST_UPDATED, CACHE_FILE_TIMESTAMPS
    
    # Check if we need to refresh cache
    if not cache_needs_refresh():
        logger.debug("Using cached extracted concepts")
        return EXTRACTED_CONCEPTS_CACHE
    
    logger.info("Refreshing extracted concepts cache...")
    
    concepts_by_book = {}
    outputs_dir = Path("outputs")
    
    if not outputs_dir.exists():
        logger.warning(f"Outputs directory not found: {outputs_dir}")
        return {}
    
    # Update file timestamps
    CACHE_FILE_TIMESTAMPS = get_file_modification_times(outputs_dir)
    
    for book_dir in outputs_dir.iterdir():
        if book_dir.is_dir() and book_dir.name in BOOK_CONFIGS:
            book_phrases = []
            book_words = []
            concept_count = 0
            
            for concept_file in book_dir.glob("concept_*.json"):
                try:
                    with open(concept_file, 'r', encoding='utf-8') as f:
                        concept = json.load(f)
                        
                        # Extract keywords from the topic
                        if 'topic' in concept:
                            phrases, words = extract_keywords_from_topic(concept['topic'])
                            book_phrases.extend(phrases)
                            book_words.extend(words)
                            concept_count += 1
                            
                except Exception as e:
                    logger.warning(f"Could not load {concept_file}: {e}")
            
            if concept_count > 0:
                # Remove duplicates while preserving order
                concepts_by_book[book_dir.name] = {
                    "phrases": list(dict.fromkeys(book_phrases)),  # Remove duplicates, preserve order
                    "words": list(dict.fromkeys(book_words))
                }
                logger.info(f"Loaded {concept_count} concepts from {book_dir.name}: "
                           f"{len(concepts_by_book[book_dir.name]['phrases'])} phrases, "
                           f"{len(concepts_by_book[book_dir.name]['words'])} words")
    
    # Update cache
    EXTRACTED_CONCEPTS_CACHE = concepts_by_book
    CACHE_LAST_UPDATED[time.time()] = True
    
    return concepts_by_book

def calculate_topic_scores(user_input: str) -> Dict[str, Dict]:
    """Calculate relevance scores for each book based on enhanced keyword matching"""
    user_input_lower = user_input.lower()
    user_words = re.findall(r'\b\w+\b', user_input_lower)
    
    # Load extracted concepts (cached)
    extracted_concepts = load_extracted_concepts()
    
    book_scores = {}
    
    for book_id, config in BOOK_CONFIGS.items():
        score = 0.0
        matches = []
        
        # 1. Check predefined keywords (baseline matching)
        predefined_matches = [word for word in user_words if word in config["keywords"]]
        score += len(predefined_matches) * 0.1  # Lower weight for predefined
        matches.extend(predefined_matches)
        
        # 2. Check extracted concept phrases (high weight)
        if book_id in extracted_concepts:
            concept_data = extracted_concepts[book_id]
            
            # Phrase matching (highest priority)
            for phrase in concept_data.get("phrases", []):
                if phrase in user_input_lower:
                    score += 0.5  # High weight for exact phrase matches
                    matches.append(phrase)
            
            # Individual word matching (medium priority)
            word_matches = [word for word in user_words if word in concept_data.get("words", [])]
            score += len(word_matches) * 0.2  # Medium weight for extracted words
            matches.extend(word_matches)
        
        # 3. Focus area phrase matching (medium weight)
        focus_words = config["focus"].lower().split()
        for i in range(len(focus_words) - 1):
            phrase = f"{focus_words[i]} {focus_words[i+1]}"
            if phrase in user_input_lower:
                score += 0.3
                matches.append(phrase)
        
        # 4. Normalize score by input length (avoid bias toward long inputs)
        if user_words:
            normalized_score = min(score, 1.0)  # Cap at 1.0
        else:
            normalized_score = 0.0
        
        # Remove duplicate matches
        unique_matches = list(dict.fromkeys(matches))
        
        book_scores[book_id] = {
            "name": config["name"],
            "score": round(normalized_score, 3),
            "matches": unique_matches[:5],  # Limit to top 5 matches for readability
            "focus": config["focus"]
        }
        
    book_scores = enhanced_memory_relevance_calculation(user_input_lower, book_scores)    

    return book_scores

def enhanced_memory_relevance_calculation(question_lower, existing_scores):
    """Enhanced relevance calculation for memory optimization"""
    
    # Calculate memory optimization score
    memory_score = 0
    word_count = 0
    
    for word, weight in MEMORY_OPTIMIZATION_KEYWORDS.items():
        if word in question_lower:
            memory_score += weight
            word_count += 1
    
    # Boost score for multiple memory-related terms
    if word_count >= 2:
        memory_score *= 1.2
    
    # Boost for specific patterns indicating memory issues
    performance_patterns = [
        'slow performance', 'cache misses', 'memory bottleneck',
        'optimize memory', 'improve cache', 'reduce latency',
        'memory access pattern', 'cache performance'
    ]
    
    for pattern in performance_patterns:
        if pattern in question_lower:
            memory_score += 0.3
    
    # Add to existing scores
    existing_scores['memory_optimization'] = min(memory_score, 1.0)
    
    return existing_scores

def get_recommendations(book_scores: Dict[str, Dict]) -> Dict:
    """Generate server recommendations based on scores"""
    # Sort books by score
    sorted_books = sorted(book_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    # Determine primary and secondary recommendations
    primary = []
    secondary = []
    
    for book_id, data in sorted_books:
        if data["score"] >= 0.25:  # High relevance threshold (increased due to better scoring)
            primary.append(f"{data['name']}-server")
        elif data["score"] >= 0.1:  # Moderate relevance threshold
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
    confidence = "high" if top_data["score"] >= 0.4 else "moderate" if top_data["score"] >= 0.2 else "low"
    
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
def refresh_concept_cache() -> str:
    """Manually refresh the extracted concepts cache"""
    global EXTRACTED_CONCEPTS_CACHE, CACHE_FILE_TIMESTAMPS
    
    # Clear cache to force refresh
    EXTRACTED_CONCEPTS_CACHE.clear()
    CACHE_FILE_TIMESTAMPS.clear()
    
    # Reload concepts
    concepts = load_extracted_concepts()
    
    total_concepts = sum(len(book_data.get("phrases", [])) for book_data in concepts.values())
    
    return f"✅ Cache refreshed successfully!\n\nLoaded concepts from {len(concepts)} books with {total_concepts} total phrases."

@mcp.tool()
def get_cache_status() -> str:
    """Get current cache status and statistics"""
    if not EXTRACTED_CONCEPTS_CACHE:
        return "❌ Cache is empty. Run refresh_concept_cache() to initialize."
    
    status_parts = ["📊 **Extracted Concepts Cache Status**\n"]
    
    total_phrases = 0
    total_words = 0
    
    for book_id, concepts in EXTRACTED_CONCEPTS_CACHE.items():
        book_name = BOOK_CONFIGS[book_id]["name"]
        phrases = len(concepts.get("phrases", []))
        words = len(concepts.get("words", []))
        
        total_phrases += phrases
        total_words += words
        
        status_parts.append(f"• **{book_name}:** {phrases} phrases, {words} words")
    
    status_parts.extend([
        "",
        f"**Total:** {total_phrases} phrases, {total_words} words across {len(EXTRACTED_CONCEPTS_CACHE)} books",
        f"**Cache Files:** {len(CACHE_FILE_TIMESTAMPS)} concept files tracked"
    ])
    
    if CACHE_LAST_UPDATED:
        last_update = max(CACHE_LAST_UPDATED.keys())
        status_parts.append(f"**Last Updated:** {time.ctime(last_update)}")
    
    return "\n".join(status_parts)

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
        score_bar = "█" * int(data["score"] * 10) + "░" * (10 - int(data["score"] * 10))
        relevance = "High" if data["score"] >= 0.4 else "Medium" if data["score"] >= 0.2 else "Low"
        
        analysis_parts.append(
            f"**{data['name']}:** {score_bar} {data['score']:.3f} ({relevance})\n"
            f"  Keywords: {', '.join(data['matches'][:5]) if data['matches'] else 'none'}\n"
            f"  Focus: {data['focus']}\n"
        )
    
    return "\n".join(analysis_parts)

# Initialize cache on server startup
def initialize_cache():
    """Initialize the concepts cache on server startup"""
    try:
        concepts = load_extracted_concepts()
        if concepts:
            logger.info(f"✅ Initialized concept cache with {len(concepts)} books")
        else:
            logger.warning("⚠️ No extracted concepts found - using predefined keywords only")
    except Exception as e:
        logger.error(f"❌ Failed to initialize concept cache: {e}")

# Initialize cache when module loads
initialize_cache()

if __name__ == "__main__":
    # Run the MCP server
    logger.info("🚀 Starting Enhanced Topic Detection MCP Server...")
    mcp.run()
