#!/usr/bin/env python3
"""
FIXED: Memory Optimization Server for MCP Architecture

Fixed the 'FunctionTool' object is not callable error by extracting shared logic
into helper functions that both MCP tools can use.

A specialized server focused on memory locality, Translation Lookaside Buffer (TLB) 
optimization, and cache performance analysis. Integrates with the existing MCP 
multi-server architecture for intelligent routing of memory optimization queries.

Port: 8106
Framework: FastMCP
"""

import json
import os
import re
import ast
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Memory Optimization Server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory-optimization-mcp")

# Global concepts storage
concepts = []
books_metadata = {
    "memory_optimization": "Memory Optimization and Cache Performance"
}

@dataclass
class MemoryAnalysis:
    """Data structure for memory analysis results"""
    cache_misses_estimated: float
    tlb_pressure: str
    spatial_locality: str
    temporal_locality: str
    optimization_priority: List[str]
    performance_impact: str
    specific_issues: List[str]
    recommended_optimizations: List[str]

@dataclass
class CacheConfig:
    """Cache configuration for different architectures"""
    l1_size: int
    l1_line_size: int
    l2_size: int
    l3_size: int
    page_size: int
    tlb_entries: int

# Architecture-specific cache configurations
CACHE_CONFIGS = {
    "x86_64": CacheConfig(32768, 64, 262144, 8388608, 4096, 64),
    "arm": CacheConfig(32768, 64, 262144, 2097152, 4096, 32),
    "risc_v": CacheConfig(16384, 64, 131072, 1048576, 4096, 32)
}

# Memory optimization patterns and anti-patterns
MEMORY_PATTERNS = {
    "cache_friendly": [
        r"for\s*\([^)]*\)\s*\{\s*[^}]*\[\s*i\s*\]\s*\[\s*j\s*\]",  # Row-major access
        r"for\s*\([^)]*\)\s*\{\s*[^}]*\+\+\s*\w+",  # Sequential access
        r"memcpy|memmove",  # Bulk operations
    ],
    "cache_unfriendly": [
        r"for\s*\([^)]*\)\s*\{\s*[^}]*\[\s*j\s*\]\s*\[\s*i\s*\]",  # Column-major access
        r"\[\s*\w+\s*\*\s*\d+\s*\+\s*\w+\s*\]",  # Large stride access
        r"random|rand\(\)",  # Random access patterns
    ],
    "tlb_problematic": [
        r"mmap.*MAP_ANONYMOUS",  # Large memory allocations
        r"malloc\s*\(\s*\d{7,}\s*\)",  # Very large allocations
        r"for\s*\([^)]*\)\s*\{\s*[^}]*\w+\s*\[\s*\w+\s*\*\s*\d{4,}\s*\]",  # Large stride
    ],
    "alignment_issues": [
        r"struct\s+\w+\s*\{[^}]*char[^}]*int[^}]*\}",  # Poorly aligned structs
        r"malloc\s*\(\s*[^)]*\s*\+\s*1\s*\)",  # Unaligned allocations
    ]
}

def load_concepts():
    """Load memory optimization concepts from existing book outputs and samples"""
    global concepts
    concepts = []
    
    # Load from existing book outputs first (prioritized)
    outputs_dir = Path("outputs")
    memory_related_books = ["os_three_pieces", "expert_c_programming", "kernighan_ritchie"]
    
    loaded_from_books = 0
    
    if outputs_dir.exists():
        for book_name in memory_related_books:
            book_dir = outputs_dir / book_name
            if book_dir.exists():
                for concept_file in book_dir.glob("*concept_*.json"):
                    try:
                        with open(concept_file, 'r', encoding='utf-8') as f:
                            concept_data = json.load(f)
                            
                        # Filter for memory-related concepts
                        topic_lower = concept_data.get('topic', '').lower()
                        explanation_lower = concept_data.get('explanation', '').lower()
                        
                        memory_keywords = [
                            'cache', 'memory', 'tlb', 'virtual', 'page', 'locality', 
                            'optimization', 'performance', 'malloc', 'free', 'alignment',
                            'prefetch', 'bandwidth', 'latency', 'hierarchy', 'stride'
                        ]
                        
                        is_memory_related = any(keyword in topic_lower or keyword in explanation_lower 
                                              for keyword in memory_keywords)
                        
                        if is_memory_related:
                            concept_id = f"{book_name}_{concept_file.stem}_{loaded_from_books}"
                            
                            # Map to memory optimization server format with safe dictionary access
                            concept = {
                                'id': concept_id,
                                'title': concept_data.get('topic', 'Unknown Concept'),
                                'description': concept_data.get('explanation', ''),
                                'content': concept_data.get('explanation', ''),
                                'category': f"book_{book_name}",
                                'difficulty_level': concept_data.get('difficulty_level', 'intermediate'),
                                'syntax': concept_data.get('syntax', ''),
                                'book': book_name,
                                'book_title': books_metadata.get(book_name, book_name),
                                'source_file': concept_file.name,
                                'memory_impact': concept_data.get('memory_impact', {}),
                                'optimization_techniques': concept_data.get('optimization_techniques', []),
                                'performance_metrics': concept_data.get('performance_metrics', {}),
                                'related_concepts': concept_data.get('related_concepts', []),
                                'detection_patterns': concept_data.get('detection_patterns', []),
                                'raw_data': concept_data
                            }
                            
                            # Add code examples if available
                            if concept_data.get('code_example'):
                                if isinstance(concept_data['code_example'], list):
                                    concept['syntax'] = '\n'.join(concept_data['code_example'])
                                else:
                                    concept['syntax'] = str(concept_data['code_example'])
                            
                            concepts.append(concept)
                            loaded_from_books += 1
                            
                    except Exception as e:
                        logger.warning(f"Could not load {concept_file}: {e}")
    
    logger.info(f"Loaded {loaded_from_books} memory-related concepts from existing books")
    
    # Add sample concepts if no concepts were loaded from books
    sample_concepts = [
        {
            "topic": "Cache Line Optimization",
            "explanation": "Cache line optimization involves structuring memory accesses to maximize the utilization of cache lines. Modern processors load 64-byte cache lines, so accessing data sequentially within these boundaries minimizes cache misses.",
            "code_example": [
                "// Bad: Poor cache locality - column-major access",
                "for (int i = 0; i < ROWS; i++)",
                "    for (int j = 0; j < COLS; j++)",
                "        sum += matrix[j][i];",
                "",
                "// Good: Cache-friendly - row-major access", 
                "for (int i = 0; i < ROWS; i++)",
                "    for (int j = 0; j < COLS; j++)",
                "        sum += matrix[i][j];"
            ],
            "category": "cache_fundamentals",
            "difficulty_level": "intermediate",
            "memory_impact": {
                "cache_misses": "Reduces L1 cache misses by 60-80%",
                "tlb_impact": "Minimal TLB impact",
                "memory_bandwidth": "Improves bandwidth utilization by 2-5x"
            },
            "optimization_techniques": [
                "Use row-major access patterns for C arrays",
                "Minimize stride length in array traversals",
                "Align data structures to cache line boundaries",
                "Group related data together in memory"
            ],
            "performance_metrics": {
                "typical_improvement": "2-5x speedup",
                "cache_miss_reduction": "70-90%",
                "applicable_scenarios": ["Matrix operations", "Array processing", "Image processing"]
            },
            "related_concepts": ["spatial_locality", "cache_hierarchy", "prefetching"],
            "detection_patterns": [
                "nested loops with large strides",
                "non-sequential memory access", 
                "column-major array access in C"
            ]
        }
    ]
    
    # Load sample concepts to supplement book data with safe dictionary access
    for i, concept_data in enumerate(sample_concepts):
        concept_id = f"sample_memory_concept_{i}"
        
        concept = {
            'id': concept_id,
            'title': concept_data['topic'],
            'description': concept_data['explanation'],
            'content': concept_data['explanation'],
            'category': concept_data.get('category', 'general'),
            'difficulty_level': concept_data.get('difficulty_level', 'intermediate'),
            'memory_impact': concept_data.get('memory_impact', {}),
            'syntax': '\n'.join(concept_data['code_example']) if 'code_example' in concept_data else '',
            'optimization_techniques': concept_data.get('optimization_techniques', []),
            'performance_metrics': concept_data.get('performance_metrics', {}),
            'related_concepts': concept_data.get('related_concepts', []),
            'detection_patterns': concept_data.get('detection_patterns', []),
            'book': 'memory_optimization',
            'book_title': books_metadata['memory_optimization'],
            'raw_data': concept_data
        }
        concepts.append(concept)
    
    logger.info(f"Total memory optimization concepts loaded: {len(concepts)} ({loaded_from_books} from books, {len(sample_concepts)} samples)")

def analyze_code_patterns(code: str) -> Dict[str, List[str]]:
    """Analyze code for memory access patterns"""
    patterns_found = {
        "cache_friendly": [],
        "cache_unfriendly": [], 
        "tlb_problematic": [],
        "alignment_issues": []
    }
    
    for pattern_type, patterns in MEMORY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
            if matches:
                patterns_found[pattern_type].extend(matches)
    
    return patterns_found

def estimate_cache_behavior(code: str, arch: str = "x86_64") -> Dict[str, Any]:
    """Estimate cache behavior based on code patterns"""
    config = CACHE_CONFIGS[arch]
    patterns = analyze_code_patterns(code)
    
    # Simple heuristic-based estimation
    cache_miss_score = 0
    
    # Add penalty for cache-unfriendly patterns
    cache_miss_score += len(patterns["cache_unfriendly"]) * 0.3
    cache_miss_score += len(patterns["tlb_problematic"]) * 0.2
    cache_miss_score += len(patterns["alignment_issues"]) * 0.1
    
    # Subtract for cache-friendly patterns
    cache_miss_score -= len(patterns["cache_friendly"]) * 0.2
    
    # Normalize to percentage
    estimated_miss_rate = min(max(cache_miss_score * 10, 1), 95)
    
    return {
        "estimated_miss_rate": estimated_miss_rate,
        "l1_efficiency": max(100 - estimated_miss_rate, 5),
        "memory_bandwidth_efficiency": max(80 - estimated_miss_rate, 20),
        "optimization_potential": "High" if estimated_miss_rate > 30 else "Medium" if estimated_miss_rate > 15 else "Low"
    }

def generate_optimization_suggestions(analysis: MemoryAnalysis, code: str) -> List[Dict[str, Any]]:
    """Generate specific optimization suggestions based on analysis"""
    suggestions = []
    
    if "cache_unfriendly" in analysis.specific_issues:
        suggestions.append({
            "type": "Cache Optimization",
            "priority": "High", 
            "description": "Convert column-major to row-major array access",
            "expected_improvement": "2-5x speedup",
            "implementation": "Change loop order to access arrays sequentially"
        })
    
    if "tlb_problematic" in analysis.specific_issues:
        suggestions.append({
            "type": "TLB Optimization",
            "priority": "High",
            "description": "Reduce TLB pressure with sequential access",
            "expected_improvement": "1.5-3x speedup",
            "implementation": "Use huge pages or reduce stride length"
        })
        
    if "alignment_issues" in analysis.specific_issues:
        suggestions.append({
            "type": "Memory Alignment",
            "priority": "Medium",
            "description": "Align data structures to cache boundaries",
            "expected_improvement": "10-30% improvement",
            "implementation": "Reorder struct members and add padding"
        })
    
    return suggestions

# HELPER FUNCTIONS - Extracted from MCP tools to avoid circular dependencies
def _get_concept_explanation(concept_name: str) -> str:
    """Helper function to generate concept explanation (extracted from explain_memory_concept)"""
    # Search for matching concept
    matching_concept = None
    for concept in concepts:
        if (concept_name.lower() in concept['title'].lower() or 
            concept_name.lower() in concept.get('category', '').lower() or
            concept_name == concept['id']):
            matching_concept = concept
            break
    
    if not matching_concept:
        # Return available concepts
        available = [c['title'] for c in concepts]
        return f"Concept '{concept_name}' not found.\n\nAvailable concepts:\n" + "\n".join(f"- {c}" for c in available)
    
    concept = matching_concept
    result = f"# {concept['title']}\n\n"
    
    # Basic information
    result += f"**Category:** {concept.get('category', 'General')}\n"
    result += f"**Difficulty:** {concept.get('difficulty_level', 'Unknown')}\n\n"
    
    # Main explanation
    result += f"## Overview\n{concept['description']}\n\n"
    
    # Memory impact
    if concept.get('memory_impact'):
        impact = concept['memory_impact']
        result += f"## Memory Performance Impact\n"
        for key, value in impact.items():
            result += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        result += "\n"
    
    # Code examples
    if concept.get('syntax'):
        result += f"## Code Examples\n```c\n{concept['syntax']}\n```\n\n"
    
    # Optimization techniques
    if concept.get('optimization_techniques'):
        result += f"## Optimization Techniques\n"
        for technique in concept['optimization_techniques']:
            result += f"- {technique}\n"
        result += "\n"
    
    # Performance metrics
    if concept.get('performance_metrics'):
        metrics = concept['performance_metrics']
        result += f"## Performance Metrics\n"
        for key, value in metrics.items():
            if key == 'applicable_scenarios':
                result += f"- **{key.replace('_', ' ').title()}:** {', '.join(value)}\n"
            else:
                result += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        result += "\n"
    
    # Related concepts
    if concept.get('related_concepts'):
        result += f"## Related Concepts\n"
        for related in concept['related_concepts']:
            result += f"- {related.replace('_', ' ').title()}\n"
        result += "\n"
    
    # Detection patterns
    if concept.get('detection_patterns'):
        result += f"## How to Identify This Pattern\n"
        for pattern in concept['detection_patterns']:
            result += f"- {pattern}\n"
    
    return result

# Load concepts on startup
load_concepts()

# MCP TOOLS - Fixed to avoid circular dependencies
@mcp.tool()
async def search_concepts(query: str, limit: int = 10) -> str:
    """Search memory optimization concepts by keyword, topic, or description.
    
    Args:
        query: Search query (use '*' to list all concepts)
        limit: Maximum number of results to return (default: 10)
    """
    query_lower = query.lower()
    
    if query == "*":
        matching_concepts = concepts[:limit]
    else:
        matching_concepts = []
        for concept in concepts:
            if (query_lower in concept['title'].lower() or
                query_lower in concept['description'].lower() or
                query_lower in concept['content'].lower() or
                query_lower in concept.get('category', '').lower()):
                matching_concepts.append(concept)
                if len(matching_concepts) >= limit:
                    break
    
    if not matching_concepts:
        return f"No memory optimization concepts found for query: '{query}'"
    
    result_text = f"Found {len(matching_concepts)} memory optimization concepts:\n\n"
    for i, concept in enumerate(matching_concepts, 1):
        result_text += f"{i}. **{concept['title']}** ({concept.get('category', 'general')})\n"
        result_text += f"   {concept['description'][:150]}...\n"
        if concept.get('performance_metrics', {}).get('typical_improvement'):
            perf = concept['performance_metrics']
            result_text += f"   Expected improvement: {perf['typical_improvement']}\n"
        result_text += f"   ID: {concept['id']}\n\n"
    
    return result_text

@mcp.tool()
async def get_concept_details(concept_id: str) -> str:
    """Get detailed information about a specific memory optimization concept.
    
    Args:
        concept_id: Unique identifier of the concept
    """
    # Find concept by ID
    concept = None
    for c in concepts:
        if c['id'] == concept_id:
            concept = c
            break
    
    if not concept:
        return f"Concept with ID '{concept_id}' not found"
    
    # FIXED: Use helper function instead of calling MCP tool directly
    return _get_concept_explanation(concept['title'])

@mcp.tool()
async def explain_memory_concept(concept_name: str) -> str:
    """Detailed explanation of memory optimization concepts.
    
    Args:
        concept_name: Name or ID of the concept to explain
    """
    # FIXED: Use helper function for actual implementation
    return _get_concept_explanation(concept_name)

@mcp.tool()
async def analyze_memory_patterns(code_snippet: str, language: str = "c") -> str:
    """Analyze code for memory access patterns and cache behavior.
    
    Args:
        code_snippet: Source code to analyze
        language: Programming language (default: c)
    """
    if not code_snippet.strip():
        return "Error: Empty code snippet provided"
    
    try:
        # Analyze patterns
        patterns = analyze_code_patterns(code_snippet)
        cache_behavior = estimate_cache_behavior(code_snippet)
        
        # Determine issues and locality assessment  
        issues = []
        if patterns["cache_unfriendly"]:
            issues.append("cache_unfriendly")
        if patterns["tlb_problematic"]:
            issues.append("tlb_problematic") 
        if patterns["alignment_issues"]:
            issues.append("alignment_issues")
        
        spatial_locality = "Poor" if patterns["cache_unfriendly"] else "Good" if patterns["cache_friendly"] else "Average"
        temporal_locality = "Average"  # Would need more sophisticated analysis
        
        # Create analysis object
        analysis = MemoryAnalysis(
            cache_misses_estimated=cache_behavior["estimated_miss_rate"],
            tlb_pressure="High" if patterns["tlb_problematic"] else "Low",
            spatial_locality=spatial_locality,
            temporal_locality=temporal_locality,
            optimization_priority=["Cache optimization", "TLB optimization"] if issues else ["Minor optimizations"],
            performance_impact=cache_behavior["optimization_potential"],
            specific_issues=issues,
            recommended_optimizations=[]
        )
        
        # Generate suggestions
        suggestions = generate_optimization_suggestions(analysis, code_snippet)
        
        # Format results
        result = f"**Memory Pattern Analysis Results**\n\n"
        result += f"**Cache Behavior:**\n"
        result += f"- Estimated miss rate: {analysis.cache_misses_estimated:.1f}%\n"
        result += f"- L1 cache efficiency: {cache_behavior['l1_efficiency']:.1f}%\n"
        result += f"- Memory bandwidth efficiency: {cache_behavior['memory_bandwidth_efficiency']:.1f}%\n\n"
        
        result += f"**Memory Locality:**\n"
        result += f"- Spatial locality: {analysis.spatial_locality}\n"
        result += f"- Temporal locality: {analysis.temporal_locality}\n"
        result += f"- TLB pressure: {analysis.tlb_pressure}\n\n"
        
        result += f"**Optimization Potential:** {analysis.performance_impact}\n\n"
        
        if patterns["cache_unfriendly"]:
            result += f"**⚠️ Cache-Unfriendly Patterns Detected:**\n"
            for pattern in patterns["cache_unfriendly"][:3]:
                result += f"- {pattern}\n"
            result += "\n"
        
        if patterns["cache_friendly"]:
            result += f"**✅ Cache-Friendly Patterns Found:**\n"
            for pattern in patterns["cache_friendly"][:3]:
                result += f"- {pattern}\n"
            result += "\n"
        
        if suggestions:
            result += f"**Optimization Suggestions:**\n"
            for i, suggestion in enumerate(suggestions, 1):
                result += f"{i}. **{suggestion['type']}** (Priority: {suggestion['priority']})\n"
                result += f"   {suggestion['description']}\n"
                result += f"   Expected improvement: {suggestion['expected_improvement']}\n"
                result += f"   Implementation: {suggestion['implementation']}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error analyzing memory patterns: {str(e)}"

@mcp.tool()
async def list_all_concepts() -> str:
    """List all available memory optimization concepts."""
    if not concepts:
        return "No memory optimization concepts available"
    
    result = f"**Available Memory Optimization Concepts ({len(concepts)} total)**\n\n"
    
    # Group by category
    categories = {}
    for concept in concepts:
        cat = concept.get('category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(concept)
    
    for category, concept_list in categories.items():
        result += f"## {category.replace('_', ' ').title()}\n\n"
        for concept in concept_list:
            result += f"- **{concept['title']}** (ID: {concept['id']})\n"
            result += f"  {concept['description'][:100]}...\n"
            if concept.get('difficulty_level'):
                result += f"  Difficulty: {concept['difficulty_level']}\n"
            result += "\n"
    
    result += "Use `get_concept_details(concept_id)` or `explain_memory_concept(concept_name)` for detailed information.\n"
    
    return result

if __name__ == "__main__":
    mcp.run()
