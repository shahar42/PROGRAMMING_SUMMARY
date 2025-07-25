#!/usr/bin/env python3
"""
Topic Detection MCP Server
Part 1: Intelligent question analysis and server recommendation engine
UPDATED: Now includes CSAPP (Computer Systems) topic detection and routing
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add current directory to Python path
sys.path.append('.')
sys.path.append('scripts')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic-detection-mcp")

# Initialize FastMCP server
mcp = FastMCP("topic-detection")

# Book configurations with enhanced CSAPP support
BOOK_CONFIGS = {
    "kernighan_ritchie": {
        "name": "K&R C Programming",
        "focus": "C language syntax, operators, control structures, functions",
        "keywords": [
            "variable", "function", "pointer", "array", "struct", "union", 
            "malloc", "free", "string", "stdio", "printf", "scanf",
            "if", "while", "for", "switch", "break", "continue",
            "char", "int", "float", "double", "void", "const", "static"
        ],
        "weight": 1.0
    },
    "unix_env": {
        "name": "UNIX Environment",
        "focus": "System calls, APIs, UNIX programming patterns, file operations",
        "keywords": [
            "fork", "exec", "wait", "signal", "pipe", "socket", "bind", "listen",
            "open", "read", "write", "close", "chmod", "chown", "stat",
            "process", "daemon", "ipc", "fifo", "mmap", "select", "poll",
            "posix", "unix", "linux", "file descriptor", "system call"
        ],
        "weight": 1.2
    },
    "linkers_loaders": {
        "name": "Linkers & Loaders",
        "focus": "Binary formats, linking mechanics, loader concepts, object files",
        "keywords": [
            "linker", "loader", "object file", "symbol table", "relocation",
            "dynamic linking", "static linking", "shared library", "dll",
            "elf", "executable", "binary", "symbol resolution", "undefined symbol",
            "library", "archive", "link time", "load time", "runtime"
        ],
        "weight": 1.1
    },
    "os_three_pieces": {
        "name": "Operating Systems",
        "focus": "OS algorithms, data structures, system concepts, concurrency",
        "keywords": [
            "scheduler", "scheduling", "virtual memory", "page", "page table",
            "file system", "inode", "directory", "block", "disk",
            "thread", "mutex", "semaphore", "lock", "synchronization",
            "deadlock", "race condition", "kernel", "user space", "system call"
        ],
        "weight": 1.3
    },
    "expert_c_programming": {
        "name": "Expert C Programming",
        "focus": "Advanced C techniques, pitfalls, expert-level programming, deep language insights",
        "keywords": [
            "undefined behavior", "sequence point", "volatile", "restrict",
            "alignment", "padding", "endianness", "stack overflow",
            "buffer overflow", "memory leak", "dangling pointer",
            "optimization", "compiler", "preprocessor", "macro", "inline"
        ],
        "weight": 1.4
    },
    "csapp_2016": {
        "name": "Computer Systems (CSAPP)",
        "focus": "Computer architecture, memory hierarchy, virtual memory, concurrency, system calls, network programming, performance optimization",
        "keywords": [
            # Machine-level programming
            "assembly", "x86", "x86-64", "register", "instruction", "opcode",
            "stack frame", "calling convention", "parameter passing",
            
            # Processor architecture
            "processor", "cpu", "pipeline", "pipelining", "hazard", "stall",
            "branch prediction", "out of order", "superscalar", "instruction set",
            
            # Memory hierarchy
            "cache", "cache miss", "cache hit", "locality", "spatial locality",
            "temporal locality", "memory hierarchy", "memory mountain",
            "cache line", "cache block", "associativity", "replacement policy",
            
            # Virtual memory
            "virtual memory", "virtual address", "physical address", "page table",
            "page fault", "tlb", "translation", "address translation", "mmu",
            "page", "page size", "memory protection", "segmentation",
            
            # Concurrency and parallelism
            "thread", "threading", "synchronization", "mutex", "semaphore",
            "race condition", "deadlock", "atomic", "critical section",
            "parallel", "parallelism", "multicore", "shared memory",
            
            # System software
            "system call", "exception", "interrupt", "context switch",
            "process", "fork", "exec", "signal", "exceptional control flow",
            
            # Network programming
            "socket", "tcp", "udp", "client", "server", "protocol",
            "network", "internet", "ip address", "port", "connection",
            
            # Performance optimization
            "performance", "optimization", "bottleneck", "profiling",
            "throughput", "latency", "bandwidth", "scalability"
        ],
        "weight": 1.5  # Higher weight for systems concepts
    },
    "posix_manpages": {
    "name": "POSIX System Calls Reference",
    "focus": "Comprehensive reference for POSIX system calls, including parameters, return values, and error codes",
    "keywords": [
        "syscall", "system call", "parameters", "errno", "return value",
        "epoll", "fork", "exec", "socket", "bind", "listen", "accept",
        "read", "write", "open", "close", "poll", "select",
        "pipe", "dup", "dup2", "wait", "waitpid", "signal", "sigaction",
        "mmap", "munmap", "fstat", "lseek", "connect", "send", "recv"
    ],
    "weight": 1.7
    }
}

# Global cache for extracted concepts
CONCEPT_CACHE = {}
CACHE_LOADED = False

def load_concept_cache():
    """Load all concepts from all books for better topic detection"""
    global CONCEPT_CACHE, CACHE_LOADED
    
    if CACHE_LOADED:
        return CONCEPT_CACHE
    
    project_root = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    outputs_dir = project_root / "outputs"
    
    for book_name in BOOK_CONFIGS.keys():
        book_dir = outputs_dir / book_name
        if book_dir.exists():
            concept_files = list(book_dir.glob("*concept_*.json"))
            CONCEPT_CACHE[book_name] = []
            
            for concept_file in concept_files:
                try:
                    with open(concept_file, 'r', encoding='utf-8') as f:
                        concept = json.load(f)
                        CONCEPT_CACHE[book_name].append({
                            "topic": concept.get('topic', ''),
                            "explanation": concept.get('explanation', ''),
                            "keywords": extract_keywords_from_concept(concept)
                        })
                except Exception as e:
                    logger.warning(f"Error loading {concept_file}: {e}")
    
    CACHE_LOADED = True
    logger.info(f"📚 Loaded concept cache for {len(CONCEPT_CACHE)} books")
    return CONCEPT_CACHE

def extract_keywords_from_concept(concept):
    """Extract keywords from a concept for better matching"""
    text = f"{concept.get('topic', '')} {concept.get('explanation', '')}"
    # Simple keyword extraction - could be enhanced
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return list(set(words))

def calculate_topic_scores(user_question: str) -> Dict[str, float]:
    """
    Calculate relevance scores for each book based on the user's question
    Enhanced with concept cache and CSAPP systems keywords
    """
    question_lower = user_question.lower()
    question_words = set(re.findall(r'\b[a-zA-Z]{2,}\b', question_lower))
    
    scores = {}
    
    # Load concept cache for enhanced detection
    concept_cache = load_concept_cache()
    
    for book_name, config in BOOK_CONFIGS.items():
        score = 0.0
        
        # Score based on configured keywords
        keyword_matches = 0
        for keyword in config["keywords"]:
            if keyword.lower() in question_lower:
                keyword_matches += 1
                # Give higher scores for exact phrase matches
                if len(keyword.split()) > 1:
                    score += 3.0  # Multi-word phrases get higher score
                else:
                    score += 1.0
        
        # Bonus for multiple keyword matches (indicates strong relevance)
        if keyword_matches > 2:
            score += keyword_matches * 0.5
        
        # Score based on extracted concepts (if cache is loaded)
        if book_name in concept_cache:
            concept_matches = 0
            for concept in concept_cache[book_name][:50]:  # Limit to avoid slowdown
                concept_keywords = concept.get("keywords", [])
                matches = len(question_words.intersection(set(concept_keywords)))
                if matches > 0:
                    concept_matches += matches
                    score += matches * 0.3
        
        # Apply book weight
        score *= config["weight"]
        
        # Special boosting for CSAPP systems questions
        if book_name == "csapp_2016":
            systems_indicators = ["system", "architecture", "processor", "memory", "cache", "assembly", "performance"]
            systems_matches = sum(1 for indicator in systems_indicators if indicator in question_lower)
            if systems_matches > 0:
                score += systems_matches * 2.0  # Strong boost for systems questions
        
        scores[book_name] = round(score, 2)
    
    return scores

def get_recommendations(topic_scores: Dict[str, float], min_score: float = 0.5) -> List[Dict]:
    """
    Get book recommendations based on topic scores
    Enhanced with better reasoning for CSAPP
    """
    recommendations = []
    
    # Sort books by score
    sorted_books = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
    
    for book_name, score in sorted_books:
        if score >= min_score:
            config = BOOK_CONFIGS[book_name]
            
            # Determine confidence level
            if score >= 5.0:
                confidence = "very_high"
            elif score >= 3.0:
                confidence = "high"
            elif score >= 1.5:
                confidence = "medium"
            else:
                confidence = "low"
            
            # Generate reasoning
            reasoning = f"Score: {score} - "
            if book_name == "csapp_2016":
                reasoning += "Systems programming and computer architecture concepts detected"
            elif book_name == "kernighan_ritchie":
                reasoning += "C language syntax and basic programming concepts"
            elif book_name == "unix_env":
                reasoning += "UNIX system calls and environment programming"
            elif book_name == "linkers_loaders":
                reasoning += "Binary linking and loading concepts"
            elif book_name == "os_three_pieces":
                reasoning += "Operating systems algorithms and concepts"
            elif book_name == "expert_c_programming":
                reasoning += "Advanced C programming techniques and pitfalls"
            
            recommendations.append({
                "book": book_name,
                "name": config["name"],
                "score": score,
                "confidence": confidence,
                "focus": config["focus"],
                "reasoning": reasoning
            })
    
    return recommendations

def classify_query_intent(user_question):
    """Determine if user wants API reference or learning material"""
    reference_patterns = [
        r"\w+\(\)",  # function() syntax
        r"parameters? (?:for|of) \w+",  # "parameters for fork"
        r"return value",  # "return value"
        r"error codes?",  # "error codes"
        r"how do I (?:use|call) \w+"  # "how do I use epoll"
    ]
    
    question_lower = user_question.lower()
    for pattern in reference_patterns:
        if re.search(pattern, question_lower):
            return "reference"
    
    return "learning"

@mcp.tool()
def detect_relevant_server(user_question: str) -> Dict:
    """
    Main tool: Analyze user question and recommend appropriate book servers
    Enhanced with CSAPP systems programming detection
    
    Args:
        user_question: The programming or systems question to analyze
        
    Returns:
        Dictionary with analysis results and server recommendations
    """
    logger.info(f"🔍 Analyzing question: {user_question[:100]}...")
    
    # Calculate topic relevance scores
    topic_scores = calculate_topic_scores(user_question)
    
    # Get recommendations
    recommendations = get_recommendations(topic_scores)
    
    # Determine primary recommendation
    primary_rec = recommendations[0] if recommendations else None
    
    result = {
        "question": user_question,
        "analysis": {
            "topic_scores": topic_scores,
            "total_books_analyzed": len(BOOK_CONFIGS),
            "books_with_relevance": len([s for s in topic_scores.values() if s > 0])
        },
        "recommendations": recommendations,
        "primary_recommendation": primary_rec,
        "routing_decision": {
            "recommended_server": primary_rec["book"] if primary_rec else "main_server",
            "confidence": primary_rec["confidence"] if primary_rec else "none",
            "reasoning": primary_rec["reasoning"] if primary_rec else "No specific book match found"
        }
    }
    
    logger.info(f"🎯 Primary recommendation: {primary_rec['book'] if primary_rec else 'main_server'}")
    
    return result

@mcp.tool()
def analyze_topic_coverage(user_question: str) -> Dict:
    """
    Detailed analysis of how well each book covers the topic
    
    Args:
        user_question: Question to analyze
        
    Returns:
        Detailed coverage analysis including CSAPP systems coverage
    """
    topic_scores = calculate_topic_scores(user_question)
    question_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', user_question.lower()))
    
    coverage_analysis = {}
    
    for book_name, score in topic_scores.items():
        config = BOOK_CONFIGS[book_name]
        
        # Find matching keywords
        matching_keywords = []
        for keyword in config["keywords"]:
            if keyword.lower() in user_question.lower():
                matching_keywords.append(keyword)
        
        # Calculate coverage percentage (rough estimate)
        total_relevant_words = len(question_words)
        coverage_words = len(set(matching_keywords))
        coverage_percentage = min(100, (coverage_words / max(1, total_relevant_words)) * 100)
        
        coverage_analysis[book_name] = {
            "name": config["name"],
            "relevance_score": score,
            "matching_keywords": matching_keywords,
            "coverage_percentage": round(coverage_percentage, 1),
            "focus_area": config["focus"],
            "recommendation": "primary" if score == max(topic_scores.values()) else "secondary" if score > 1.0 else "minimal"
        }
    
    return {
        "question": user_question,
        "coverage_analysis": coverage_analysis,
        "summary": {
            "best_match": max(topic_scores, key=topic_scores.get),
            "total_matches": len([s for s in topic_scores.values() if s > 0]),
            "avg_coverage": round(sum(coverage_percentage for coverage_percentage in [a["coverage_percentage"] for a in coverage_analysis.values()]) / len(coverage_analysis), 1)
        }
    }

@mcp.tool()
def list_available_servers() -> Dict:
    """
    List all available book servers and their focus areas
    Updated to include CSAPP
    
    Returns:
        Dictionary with server information
    """
    servers = {}
    
    for book_name, config in BOOK_CONFIGS.items():
        servers[book_name] = {
            "name": config["name"],
            "focus": config["focus"],
            "keyword_count": len(config["keywords"]),
            "weight": config["weight"],
            "sample_keywords": config["keywords"][:10]  # First 10 keywords as sample
        }
    
    return {
        "available_servers": servers,
        "total_servers": len(servers),
        "newest_addition": "csapp_2016",
        "server_priorities": {
            "systems_programming": "csapp_2016",
            "c_language": "kernighan_ritchie", 
            "unix_programming": "unix_env",
            "linking_loading": "linkers_loaders",
            "operating_systems": "os_three_pieces",
            "advanced_c": "expert_c_programming"
        }
    }

@mcp.tool()
def refresh_concept_cache() -> Dict:
    """
    Refresh the concept cache by reloading from all book directories
    
    Returns:
        Cache refresh status
    """
    global CONCEPT_CACHE, CACHE_LOADED
    
    CONCEPT_CACHE.clear()
    CACHE_LOADED = False
    
    # Reload cache
    cache = load_concept_cache()
    
    cache_stats = {}
    for book_name, concepts in cache.items():
        cache_stats[book_name] = len(concepts)
    
    return {
        "cache_refreshed": True,
        "books_loaded": len(cache),
        "concept_counts": cache_stats,
        "total_concepts": sum(cache_stats.values()),
        "cache_status": "ready"
    }

@mcp.tool()
def get_cache_status() -> Dict:
    """
    Get current status of the concept cache
    
    Returns:
        Cache status information
    """
    cache = load_concept_cache()
    
    cache_info = {}
    total_concepts = 0
    
    for book_name, concepts in cache.items():
        concept_count = len(concepts)
        cache_info[book_name] = {
            "concept_count": concept_count,
            "book_title": BOOK_CONFIGS[book_name]["name"],
            "sample_topics": [c.get("topic", "Unknown")[:50] for c in concepts[:3]]
        }
        total_concepts += concept_count
    
    return {
        "cache_loaded": CACHE_LOADED,
        "books_in_cache": len(cache),
        "total_concepts": total_concepts,
        "cache_details": cache_info,
        "newest_book": "csapp_2016" if "csapp_2016" in cache else "none"
    }

if __name__ == "__main__":
    logger.info("🎯 Starting Topic Detection Server")
    logger.info(f"📚 Configured for {len(BOOK_CONFIGS)} book servers")
    logger.info("🆕 New: CSAPP (Computer Systems) support added")
    
    # Load initial cache
    load_concept_cache()
    
    mcp.run()
