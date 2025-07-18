#!/usr/bin/env python3
"""
Memory Optimization Server for MCP Architecture

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
                for concept_file in book_dir.glob("concept_*.json"):
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
                            
                            # Map to memory optimization server format
                            concept = {
                                'id': concept_id,
                                'title': concept_data.get('topic', 'Unknown Concept'),
                                'description': concept_data.get('explanation', ''),
                                'content': concept_data.get('explanation', ''),
                                'category': f"book_{book_name}",
                                'difficulty_level': 'intermediate',  # Default
                                'syntax': concept_data.get('syntax', ''),
                                'book': book_name,
                                'book_title': books_metadata.get(book_name, book_name),
                                'source_file': concept_file.name,
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
    if loaded_from_books == 0:
        logger.info("No book concepts found, using built-in samples")
        sample_concepts = [
        {
            "topic": "Cache Line Optimization",
            "category": "cache_fundamentals",
            "difficulty_level": "intermediate",
            "explanation": "Cache line optimization involves structuring memory accesses to maximize the utilization of cache lines. Modern processors load 64-byte cache lines, so accessing data sequentially within these boundaries minimizes cache misses.",
            "memory_impact": {
                "cache_misses": "Reduces L1 cache misses by 60-80%",
                "tlb_impact": "Minimal TLB impact",
                "memory_bandwidth": "Improves bandwidth utilization by 2-5x"
            },
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
        },
        {
            "topic": "TLB Optimization",
            "category": "tlb_optimization", 
            "difficulty_level": "advanced",
            "explanation": "Translation Lookaside Buffer (TLB) optimization focuses on reducing TLB misses by improving virtual memory access patterns. TLB caches virtual-to-physical address translations, and misses are expensive (100+ cycles).",
            "memory_impact": {
                "cache_misses": "Indirect positive impact",
                "tlb_impact": "Reduces TLB misses by 80-95%",
                "memory_bandwidth": "Reduces memory stalls significantly"
            },
            "code_example": [
                "// Bad: TLB thrashing with large strides",
                "for (i = 0; i < size; i += 4096)",
                "    process(huge_array[i]);",
                "",
                "// Good: TLB-friendly sequential access",
                "for (i = 0; i < size; i++)",
                "    process(huge_array[i]);"
            ],
            "optimization_techniques": [
                "Use huge pages for large allocations",
                "Minimize page boundary crossings",
                "Group related data on same pages",
                "Avoid large stride memory access patterns"
            ],
            "performance_metrics": {
                "typical_improvement": "1.5-3x speedup for memory-bound code",
                "tlb_miss_reduction": "80-95%",
                "applicable_scenarios": ["Large dataset processing", "Scientific computing", "Database operations"]
            },
            "related_concepts": ["virtual_memory", "page_management", "numa_optimization"],
            "detection_patterns": [
                "large stride array access",
                "random memory access patterns",
                "frequent page boundary crossings"
            ]
        },
        {
            "topic": "Spatial Locality Optimization",
            "category": "memory_locality",
            "difficulty_level": "beginner",
            "explanation": "Spatial locality refers to accessing memory locations that are close to recently accessed locations. Good spatial locality ensures that when data is loaded into cache, nearby data (which is likely to be accessed soon) comes with it.",
            "memory_impact": {
                "cache_misses": "Reduces cache misses by 50-80%",
                "tlb_impact": "Moderate positive impact",
                "memory_bandwidth": "Improves bandwidth efficiency"
            },
            "code_example": [
                "// Bad: Poor spatial locality",
                "struct Point { double x, y, z; };",
                "struct Data { Point* points; int* values; };",
                "// Points and values stored separately",
                "",
                "// Good: Improved spatial locality",
                "struct DataPoint { double x, y, z; int value; };",
                "// Related data stored together"
            ],
            "optimization_techniques": [
                "Store related data in contiguous memory",
                "Use structure-of-arrays vs array-of-structures appropriately",
                "Minimize pointer chasing",
                "Pack hot data together"
            ],
            "performance_metrics": {
                "typical_improvement": "1.5-3x speedup",
                "cache_miss_reduction": "50-80%",
                "applicable_scenarios": ["Data structure design", "Algorithm optimization", "Memory layout"]
            },
            "related_concepts": ["temporal_locality", "cache_line_optimization", "data_structure_layout"],
            "detection_patterns": [
                "scattered memory allocations",
                "pointer chasing patterns",
                "separated related data"
            ]
        },
        {
            "topic": "Memory Alignment",
            "category": "advanced_techniques",
            "difficulty_level": "intermediate",
            "explanation": "Memory alignment ensures that data structures are placed at memory addresses that are multiples of their size or cache line size. Proper alignment prevents unnecessary cache line splits and improves performance.",
            "memory_impact": {
                "cache_misses": "Prevents cache line splits",
                "tlb_impact": "Minimal impact",
                "memory_bandwidth": "Improves access efficiency by 10-30%"
            },
            "code_example": [
                "// Bad: Misaligned structure",
                "struct BadAlign {",
                "    char a;     // 1 byte",
                "    int b;      // 4 bytes, misaligned",
                "    char c;     // 1 byte",
                "    double d;   // 8 bytes, misaligned",
                "};",
                "",
                "// Good: Properly aligned structure",
                "struct GoodAlign {",
                "    double d;   // 8 bytes, aligned",
                "    int b;      // 4 bytes, aligned", 
                "    char a;     // 1 byte",
                "    char c;     // 1 byte",
                "    char pad[2]; // Explicit padding",
                "};"
            ],
            "optimization_techniques": [
                "Order struct members by size (largest first)",
                "Use explicit padding for cache line alignment",
                "Use compiler alignment attributes",
                "Align arrays to cache line boundaries"
            ],
            "performance_metrics": {
                "typical_improvement": "10-30% improvement",
                "cache_miss_reduction": "Prevents cache line splits",
                "applicable_scenarios": ["High-performance computing", "Real-time systems", "Embedded systems"]
            },
            "related_concepts": ["cache_line_optimization", "struct_packing", "hardware_architecture"],
            "detection_patterns": [
                "mixed-size struct members",
                "unaligned memory allocations",
                "cache line boundary violations"
            ]
        }
    ]

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
                for concept_file in book_dir.glob("concept_*.json"):
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
    if loaded_from_books == 0:
        logger.info("No book concepts found, using built-in samples")
        sample_concepts = [
        {
            "topic": "Cache Line Optimization",
            "category": "cache_fundamentals",
            "difficulty_level": "intermediate",
            "explanation": "Cache line optimization involves structuring memory accesses to maximize the utilization of cache lines. Modern processors load 64-byte cache lines, so accessing data sequentially within these boundaries minimizes cache misses.",
            "memory_impact": {
                "cache_misses": "Reduces L1 cache misses by 60-80%",
                "tlb_impact": "Minimal TLB impact",
                "memory_bandwidth": "Improves bandwidth utilization by 2-5x"
            },
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
        },
        {
            "topic": "TLB Optimization",
            "category": "tlb_optimization", 
            "difficulty_level": "advanced",
            "explanation": "Translation Lookaside Buffer (TLB) optimization focuses on reducing TLB misses by improving virtual memory access patterns. TLB caches virtual-to-physical address translations, and misses are expensive (100+ cycles).",
            "memory_impact": {
                "cache_misses": "Indirect positive impact",
                "tlb_impact": "Reduces TLB misses by 80-95%",
                "memory_bandwidth": "Reduces memory stalls significantly"
            },
            "code_example": [
                "// Bad: TLB thrashing with large strides",
                "for (i = 0; i < size; i += 4096)",
                "    process(huge_array[i]);",
                "",
                "// Good: TLB-friendly sequential access",
                "for (i = 0; i < size; i++)",
                "    process(huge_array[i]);"
            ],
            "optimization_techniques": [
                "Use huge pages for large allocations",
                "Minimize page boundary crossings",
                "Group related data on same pages",
                "Avoid large stride memory access patterns"
            ],
            "performance_metrics": {
                "typical_improvement": "1.5-3x speedup for memory-bound code",
                "tlb_miss_reduction": "80-95%",
                "applicable_scenarios": ["Large dataset processing", "Scientific computing", "Database operations"]
            },
            "related_concepts": ["virtual_memory", "page_management", "numa_optimization"],
            "detection_patterns": [
                "large stride array access",
                "random memory access patterns",
                "frequent page boundary crossings"
            ]
        },
        {
            "topic": "Spatial Locality Optimization",
            "category": "memory_locality",
            "difficulty_level": "beginner",
            "explanation": "Spatial locality refers to accessing memory locations that are close to recently accessed locations. Good spatial locality ensures that when data is loaded into cache, nearby data (which is likely to be accessed soon) comes with it.",
            "memory_impact": {
                "cache_misses": "Reduces cache misses by 50-80%",
                "tlb_impact": "Moderate positive impact",
                "memory_bandwidth": "Improves bandwidth efficiency"
            },
            "code_example": [
                "// Bad: Poor spatial locality",
                "struct Point { double x, y, z; };",
                "struct Data { Point* points; int* values; };",
                "// Points and values stored separately",
                "",
                "// Good: Improved spatial locality",
                "struct DataPoint { double x, y, z; int value; };",
                "// Related data stored together"
            ],
            "optimization_techniques": [
                "Store related data in contiguous memory",
                "Use structure-of-arrays vs array-of-structures appropriately",
                "Minimize pointer chasing",
                "Pack hot data together"
            ],
            "performance_metrics": {
                "typical_improvement": "1.5-3x speedup",
                "cache_miss_reduction": "50-80%",
                "applicable_scenarios": ["Data structure design", "Algorithm optimization", "Memory layout"]
            },
            "related_concepts": ["temporal_locality", "cache_line_optimization", "data_structure_layout"],
            "detection_patterns": [
                "scattered memory allocations",
                "pointer chasing patterns",
                "separated related data"
            ]
        },
        {
            "topic": "Memory Alignment",
            "category": "advanced_techniques",
            "difficulty_level": "intermediate",
            "explanation": "Memory alignment ensures that data structures are placed at memory addresses that are multiples of their size or cache line size. Proper alignment prevents unnecessary cache line splits and improves performance.",
            "memory_impact": {
                "cache_misses": "Prevents cache line splits",
                "tlb_impact": "Minimal impact",
                "memory_bandwidth": "Improves access efficiency by 10-30%"
            },
            "code_example": [
                "// Bad: Misaligned structure",
                "struct BadAlign {",
                "    char a;     // 1 byte",
                "    int b;      // 4 bytes, misaligned",
                "    char c;     // 1 byte",
                "    double d;   // 8 bytes, misaligned",
                "};",
                "",
                "// Good: Properly aligned structure",
                "struct GoodAlign {",
                "    double d;   // 8 bytes, aligned",
                "    int b;      // 4 bytes, aligned", 
                "    char a;     // 1 byte",
                "    char c;     // 1 byte",
                "    char pad[2]; // Explicit padding",
                "};"
            ],
            "optimization_techniques": [
                "Order struct members by size (largest first)",
                "Use explicit padding for cache line alignment",
                "Use compiler alignment attributes",
                "Align arrays to cache line boundaries"
            ],
            "performance_metrics": {
                "typical_improvement": "10-30% improvement",
                "cache_miss_reduction": "Prevents cache line splits",
                "applicable_scenarios": ["High-performance computing", "Real-time systems", "Embedded systems"]
            },
            "related_concepts": ["cache_line_optimization", "struct_packing", "hardware_architecture"],
            "detection_patterns": [
                "mixed-size struct members",
                "unaligned memory allocations",
                "cache line boundary violations"
            ]
        }
    ]
    else:
        # Add a few key sample concepts to supplement book data
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

# Load concepts on startup
load_concepts()

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
async def suggest_cache_optimizations(code_snippet: str, target_architecture: str = "x86_64") -> str:
    """Provide specific cache optimization recommendations.
    
    Args:
        code_snippet: Source code to optimize
        target_architecture: Target architecture (x86_64, arm, risc_v)
    """
    if target_architecture not in CACHE_CONFIGS:
        return f"Error: Unsupported architecture '{target_architecture}'. Supported: {list(CACHE_CONFIGS.keys())}"
    
    try:
        config = CACHE_CONFIGS[target_architecture]
        patterns = analyze_code_patterns(code_snippet)
        cache_behavior = estimate_cache_behavior(code_snippet, target_architecture)
        
        result = f"**Cache Optimization Recommendations for {target_architecture.upper()}**\n\n"
        result += f"**Target Architecture Specs:**\n"
        result += f"- L1 Cache: {config.l1_size//1024}KB, {config.l1_line_size}B line size\n"
        result += f"- L2 Cache: {config.l2_size//1024}KB\n"
        result += f"- L3 Cache: {config.l3_size//1024//1024}MB\n"
        result += f"- Page Size: {config.page_size}B\n\n"
        
        # Priority-ranked optimizations
        optimizations = []
        
        if patterns["cache_unfriendly"]:
            optimizations.append({
                "priority": 1,
                "title": "Fix Memory Access Patterns",
                "description": "Convert column-major to row-major array access",
                "implementation": "Change nested loop order: for(i) for(j) arr[i][j] instead of arr[j][i]",
                "expected_gain": "2-5x speedup",
                "difficulty": "Easy"
            })
        
        if re.search(r'for.*for.*\[.*\*.*\]', code_snippet):
            optimizations.append({
                "priority": 2, 
                "title": "Cache Blocking (Tiling)",
                "description": "Break large loops into cache-sized blocks",
                "implementation": f"Use {config.l1_size//8} element blocks for optimal L1 usage",
                "expected_gain": "1.5-3x speedup",
                "difficulty": "Medium"
            })
        
        if re.search(r'struct.*\{', code_snippet):
            optimizations.append({
                "priority": 3,
                "title": "Data Structure Layout",
                "description": "Optimize struct layout for cache lines",
                "implementation": f"Align hot data to {config.l1_line_size}B boundaries, group related fields",
                "expected_gain": "10-30% improvement",
                "difficulty": "Medium"
            })
        
        # Add prefetching suggestion for sequential access
        if re.search(r'for.*\[.*\+\+.*\]', code_snippet):
            optimizations.append({
                "priority": 4,
                "title": "Software Prefetching",
                "description": "Add prefetch hints for predictable access patterns",
                "implementation": "__builtin_prefetch(&arr[i+8], 0, 1) for read-ahead",
                "expected_gain": "5-15% improvement",
                "difficulty": "Advanced"
            })
        
        # Sort by priority and format
        optimizations.sort(key=lambda x: x["priority"])
        
        for opt in optimizations:
            result += f"**{opt['priority']}. {opt['title']}** (Difficulty: {opt['difficulty']})\n"
            result += f"   Description: {opt['description']}\n"
            result += f"   Implementation: {opt['implementation']}\n"
            result += f"   Expected gain: {opt['expected_gain']}\n\n"
        
        if not optimizations:
            result += "**✅ No major cache optimizations needed!**\n"
            result += "Your code appears to have good cache behavior already.\n\n"
            result += "**Minor suggestions:**\n"
            result += f"- Ensure data alignment to {config.l1_line_size}B boundaries\n"
            result += "- Consider prefetching for very large datasets\n"
            result += "- Profile with hardware counters to verify performance\n"
        
        return result
        
    except Exception as e:
        return f"Error generating cache optimizations: {str(e)}"

@mcp.tool() 
async def detect_tlb_issues(code_snippet: str, page_size: str = "4kb") -> str:
    """Identify potential TLB thrashing and page table inefficiencies.
    
    Args:
        code_snippet: Source code to analyze
        page_size: Target page size (4kb, 2mb, 1gb)
    """
    page_sizes = {"4kb": 4096, "2mb": 2097152, "1gb": 1073741824}
    
    if page_size not in page_sizes:
        return f"Error: Unsupported page size '{page_size}'. Supported: {list(page_sizes.keys())}"
    
    try:
        page_size_bytes = page_sizes[page_size]
        patterns = analyze_code_patterns(code_snippet)
        
        result = f"**TLB Analysis Results (Page Size: {page_size})**\n\n"
        
        # Detect TLB issues
        tlb_issues = []
        
        # Large stride detection
        large_stride_matches = re.findall(r'\[.*\*\s*(\d+).*\]', code_snippet)
        for stride in large_stride_matches:
            stride_val = int(stride)
            if stride_val * 4 > page_size_bytes:  # Assuming 4-byte elements
                tlb_issues.append(f"Large stride access: {stride_val} elements ({stride_val*4} bytes)")
        
        # Random access detection
        if re.search(r'random|rand\(\)', code_snippet, re.IGNORECASE):
            tlb_issues.append("Random memory access pattern detected")
        
        # Large allocation detection
        malloc_matches = re.findall(r'malloc\s*\(\s*(\d+)', code_snippet)
        for size in malloc_matches:
            size_val = int(size)
            if size_val > page_size_bytes * 10:  # > 10 pages
                pages_needed = size_val // page_size_bytes
                tlb_issues.append(f"Large allocation: {size_val} bytes ({pages_needed} pages)")
        
        # Report findings
        if tlb_issues:
            result += f"**⚠️ TLB Issues Detected:**\n"
            for issue in tlb_issues:
                result += f"- {issue}\n"
            result += "\n"
            
            result += f"**TLB Pressure:** High\n"
            result += f"**Expected TLB miss rate:** 15-40%\n\n"
            
            result += f"**Optimization Recommendations:**\n"
            result += f"1. **Use Huge Pages**\n"
            result += f"   - Switch to {page_sizes['2mb']//1024//1024}MB pages for large allocations\n"
            result += f"   - Reduces TLB entries needed by 512x\n"
            result += f"   - Implementation: madvise(ptr, size, MADV_HUGEPAGE)\n\n"
            
            result += f"2. **Reduce Memory Stride**\n"
            result += f"   - Access memory sequentially when possible\n"
            result += f"   - Use cache blocking to improve locality\n"
            result += f"   - Expected improvement: 2-4x speedup\n\n"
            
            result += f"3. **Memory Layout Optimization**\n"
            result += f"   - Group related data on same pages\n"
            result += f"   - Minimize working set size\n"
            result += f"   - Consider memory pools for small objects\n\n"
        else:
            result += f"**✅ No significant TLB issues detected!**\n"
            result += f"**TLB Pressure:** Low\n"
            result += f"**Expected TLB miss rate:** <5%\n\n"
            
            result += f"**Minor optimizations:**\n"
            result += f"- Consider huge pages for very large datasets (>100MB)\n"
            result += f"- Ensure sequential access patterns are maintained\n"
            result += f"- Monitor TLB performance with hardware counters\n"
        
        # Page size recommendations
        result += f"**Page Size Analysis:**\n"
        result += f"- Current: {page_size} ({page_size_bytes:,} bytes)\n"
        if tlb_issues and page_size == "4kb":
            result += f"- Recommendation: Consider 2MB huge pages\n"
            result += f"- Benefit: 512x fewer TLB entries needed\n"
        elif page_size == "2mb":
            result += f"- Current setting is optimal for most workloads\n"
        
        return result
        
    except Exception as e:
        return f"Error detecting TLB issues: {str(e)}"

@mcp.tool()
async def explain_memory_concept(concept_name: str) -> str:
    """Detailed explanation of memory optimization concepts.
    
    Args:
        concept_name: Name or ID of the concept to explain
    """
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

@mcp.tool()
async def generate_optimization_checklist(optimization_type: str) -> str:
    """Create step-by-step optimization guides.
    
    Args:
        optimization_type: Type of optimization (cache_optimization, tlb_optimization, memory_locality)
    """
    checklists = {
        "cache_optimization": {
            "title": "Cache Optimization Checklist",
            "steps": [
                {
                    "step": "Analyze Memory Access Patterns",
                    "actions": [
                        "Identify nested loops and array accesses",
                        "Check for row-major vs column-major access",
                        "Look for large stride memory access",
                        "Profile cache miss rates with tools like perf"
                    ]
                },
                {
                    "step": "Fix Access Patterns", 
                    "actions": [
                        "Convert column-major to row-major array access",
                        "Minimize stride length in array traversals", 
                        "Use sequential access when possible",
                        "Verify changes with cache profiling"
                    ]
                },
                {
                    "step": "Implement Cache Blocking",
                    "actions": [
                        "Break large loops into cache-sized blocks",
                        "Use L1 cache size (typically 32KB) for block sizing",
                        "Implement tiled matrix multiplication if applicable",
                        "Benchmark performance improvements"
                    ]
                },
                {
                    "step": "Optimize Data Layout",
                    "actions": [
                        "Align data structures to cache line boundaries (64B)",
                        "Group hot data together in structs",
                        "Consider struct of arrays vs array of structs",
                        "Use padding to avoid false sharing"
                    ]
                },
                {
                    "step": "Add Prefetching",
                    "actions": [
                        "Identify predictable access patterns",
                        "Add software prefetch hints (__builtin_prefetch)",
                        "Tune prefetch distance (typically 8-16 cache lines ahead)",
                        "Measure impact with hardware counters"
                    ]
                }
            ]
        },
        "tlb_optimization": {
            "title": "TLB Optimization Checklist",
            "steps": [
                {
                    "step": "Analyze Memory Access Patterns",
                    "actions": [
                        "Identify large memory allocations (>10MB)",
                        "Look for large stride array access patterns",
                        "Check for random memory access",
                        "Profile TLB miss rates"
                    ]
                },
                {
                    "step": "Enable Huge Pages",
                    "actions": [
                        "Use 2MB pages for large allocations",
                        "Configure system: echo always > /sys/kernel/mm/transparent_hugepage/enabled",
                        "Use madvise(MADV_HUGEPAGE) for specific allocations",
                        "Monitor huge page usage: cat /proc/meminfo | grep Huge"
                    ]
                },
                {
                    "step": "Reduce Memory Footprint",
                    "actions": [
                        "Minimize working set size",
                        "Use memory pools for small objects",
                        "Group related data on same pages",
                        "Avoid unnecessary memory allocations"
                    ]
                },
                {
                    "step": "Optimize Access Patterns",
                    "actions": [
                        "Use sequential access when possible",
                        "Minimize page boundary crossings",
                        "Implement cache blocking to improve locality",
                        "Consider memory mapping for large files"
                    ]
                },
                {
                    "step": "Measure and Validate",
                    "actions": [
                        "Profile with perf: perf stat -e dTLB-load-misses",
                        "Monitor page fault rates",
                        "Measure overall application performance",
                        "Document performance improvements"
                    ]
                }
            ]
        },
        "memory_locality": {
            "title": "Memory Locality Optimization Checklist", 
            "steps": [
                {
                    "step": "Assess Current Locality",
                    "actions": [
                        "Profile cache miss rates by level (L1, L2, L3)",
                        "Identify hot code paths and data structures",
                        "Analyze data access patterns",
                        "Measure memory bandwidth utilization"
                    ]
                },
                {
                    "step": "Improve Spatial Locality",
                    "actions": [
                        "Store related data contiguously in memory",
                        "Use structure packing to minimize gaps",
                        "Choose appropriate data layout (AoS vs SoA)",
                        "Align frequently accessed data to cache boundaries"
                    ]
                },
                {
                    "step": "Enhance Temporal Locality",
                    "actions": [
                        "Reuse data while it's still in cache",
                        "Process data in blocks rather than streams",
                        "Minimize the working set size",
                        "Use loop fusion to improve reuse"
                    ]
                },
                {
                    "step": "Optimize Data Structures",
                    "actions": [
                        "Choose cache-friendly data structures",
                        "Minimize pointer chasing",
                        "Use arrays instead of linked lists when possible",
                        "Consider data structure size vs cache size"
                    ]
                },
                {
                    "step": "Validate Improvements",
                    "actions": [
                        "Re-profile cache behavior after changes",
                        "Measure end-to-end performance",
                        "Check for performance regressions",
                        "Document optimization decisions"
                    ]
                }
            ]
        }
    }
    
    if optimization_type not in checklists:
        available = list(checklists.keys())
        return f"Unknown optimization type '{optimization_type}'.\n\nAvailable checklists:\n" + "\n".join(f"- {t}" for t in available)
    
    checklist = checklists[optimization_type]
    result = f"# {checklist['title']}\n\n"
    
    for i, step in enumerate(checklist['steps'], 1):
        result += f"## {i}. {step['step']}\n\n"
        for action in step['actions']:
            result += f"- [ ] {action}\n"
        result += "\n"
    
    result += "---\n\n"
    result += "**Pro Tips:**\n"
    result += "- Always profile before and after optimizations\n"
    result += "- Focus on the most impactful optimizations first\n"
    result += "- Test on target hardware architecture\n"
    result += "- Document performance improvements for future reference\n"
    
    return result

@mcp.tool()
async def compare_memory_techniques(technique1: str, technique2: str) -> str:
    """Side-by-side comparison of optimization approaches.
    
    Args:
        technique1: First optimization technique
        technique2: Second optimization technique
    """
    # Find matching concepts
    concept1 = None
    concept2 = None
    
    for concept in concepts:
        if technique1.lower() in concept['title'].lower():
            concept1 = concept
        if technique2.lower() in concept['title'].lower():
            concept2 = concept
    
    if not concept1:
        return f"Technique '{technique1}' not found in knowledge base"
    if not concept2:
        return f"Technique '{technique2}' not found in knowledge base"
    
    result = f"# Comparison: {concept1['title']} vs {concept2['title']}\n\n"
    
    # Overview comparison
    result += "## Overview\n\n"
    result += f"**{concept1['title']}:**\n{concept1['description'][:200]}...\n\n"
    result += f"**{concept2['title']}:**\n{concept2['description'][:200]}...\n\n"
    
    # Performance comparison
    if 'performance_metrics' in concept1 and 'performance_metrics' in concept2:
        result += "## Performance Impact\n\n"
        
        metrics1 = concept1['performance_metrics']
        metrics2 = concept2['performance_metrics']
        
        result += "| Metric | {} | {} |\n".format(concept1['title'], concept2['title'])
        result += "|--------|" + "-" * len(concept1['title']) + "|" + "-" * len(concept2['title']) + "|\n"
        
        common_metrics = set(metrics1.keys()) & set(metrics2.keys())
        for metric in common_metrics:
            result += f"| {metric.replace('_', ' ').title()} | {metrics1[metric]} | {metrics2[metric]} |\n"
        result += "\n"
    
    # Difficulty and implementation
    result += "## Implementation\n\n"
    result += f"**{concept1['title']} Difficulty:** {concept1.get('difficulty_level', 'Unknown')}\n"
    result += f"**{concept2['title']} Difficulty:** {concept2.get('difficulty_level', 'Unknown')}\n\n"
    
    # When to use each
    result += "## When to Use\n\n"
    
    if concept1.get('performance_metrics', {}).get('applicable_scenarios'):
        scenarios1 = concept1['performance_metrics']['applicable_scenarios']
        result += f"**Use {concept1['title']} for:**\n"
        for scenario in scenarios1:
            result += f"- {scenario}\n"
        result += "\n"
    
    if concept2.get('performance_metrics', {}).get('applicable_scenarios'):
        scenarios2 = concept2['performance_metrics']['applicable_scenarios']
        result += f"**Use {concept2['title']} for:**\n"
        for scenario in scenarios2:
            result += f"- {scenario}\n"
        result += "\n"
    
    # Recommendation
    result += "## Recommendation\n\n"
    
    # Simple heuristic based on difficulty and impact
    diff1 = concept1.get('difficulty_level', 'medium').lower()
    diff2 = concept2.get('difficulty_level', 'medium').lower()
    
    if diff1 == 'beginner' and diff2 != 'beginner':
        result += f"**Start with {concept1['title']}** - easier to implement and good foundation\n"
    elif diff2 == 'beginner' and diff1 != 'beginner':
        result += f"**Start with {concept2['title']}** - easier to implement and good foundation\n"
    else:
        result += "**Both techniques are valuable** - consider your specific use case and constraints\n"
    
    result += "\n**Best Practice:** Implement both techniques if they address different aspects of your performance bottleneck.\n"
    
    return result

@mcp.tool()
async def create_optimization_plan(code_snippet: str, performance_target: str) -> str:
    """Generate comprehensive optimization strategy.
    
    Args:
        code_snippet: Source code to optimize
        performance_target: Target improvement (e.g., "2x speedup", "reduce cache misses by 50%")
    """
    try:
        # Analyze current code
        patterns = analyze_code_patterns(code_snippet)
        cache_behavior = estimate_cache_behavior(code_snippet)
        
        result = f"# Memory Optimization Plan\n\n"
        result += f"**Performance Target:** {performance_target}\n\n"
        
        # Current state assessment
        result += f"## Current State Assessment\n\n"
        result += f"- **Estimated cache miss rate:** {cache_behavior.get('estimated_miss_rate', 'N/A'):.1f}%\n"
        result += f"- **Memory bandwidth efficiency:** {cache_behavior.get('memory_bandwidth_efficiency', 'N/A'):.1f}%\n"
        result += f"- **Optimization potential:** {cache_behavior.get('optimization_potential', 'Unknown')}\n\n"
        
        # Identify issues
        issues = []
        if patterns["cache_unfriendly"]:
            issues.append(("Cache Access Patterns", "High", "Fix memory access order"))
        if patterns["tlb_problematic"]:
            issues.append(("TLB Pressure", "High", "Reduce page misses"))
        if patterns["alignment_issues"]:
            issues.append(("Memory Alignment", "Medium", "Align data structures"))
        
        if issues:
            result += f"## Identified Issues\n\n"
            for issue, priority, fix in issues:
                result += f"- **{issue}** (Priority: {priority}): {fix}\n"
            result += "\n"
        
        # Optimization phases
        result += f"## Optimization Plan (Prioritized)\n\n"
        
        phase = 1
        
        # Phase 1: Quick wins (cache access patterns)
        if patterns["cache_unfriendly"]:
            result += f"### Phase {phase}: Fix Memory Access Patterns\n"
            result += f"**Expected improvement:** 2-5x speedup\n"
            result += f"**Implementation time:** 1-2 hours\n"
            result += f"**Actions:**\n"
            result += f"- Convert column-major to row-major array access\n"
            result += f"- Ensure loop order matches memory layout\n"
            result += f"- Verify with cache profiling (perf stat -e cache-misses)\n\n"
            phase += 1
        
        # Phase 2: Cache blocking
        if re.search(r'for.*for.*\[', code_snippet):
            result += f"### Phase {phase}: Implement Cache Blocking\n"
            result += f"**Expected improvement:** 1.5-3x additional speedup\n"
            result += f"**Implementation time:** 2-4 hours\n"
            result += f"**Actions:**\n"
            result += f"- Break large loops into 32KB blocks (L1 cache size)\n"
            result += f"- Implement tiled algorithms for matrix operations\n"
            result += f"- Benchmark block sizes for optimal performance\n\n"
            phase += 1
        
        # Phase 3: TLB optimization
        if patterns["tlb_problematic"]:
            result += f"### Phase {phase}: TLB Optimization\n"
            result += f"**Expected improvement:** 1.5-2x additional speedup\n"
            result += f"**Implementation time:** 1-3 hours\n"
            result += f"**Actions:**\n"
            result += f"- Enable huge pages for large allocations\n"
            result += f"- Reduce memory stride where possible\n"
            result += f"- Group related data on same pages\n\n"
            phase += 1
        
        # Phase 4: Advanced optimizations
        result += f"### Phase {phase}: Advanced Optimizations\n"
        result += f"**Expected improvement:** 10-30% additional improvement\n"
        result += f"**Implementation time:** 4-8 hours\n"
        result += f"**Actions:**\n"
        result += f"- Add software prefetching for predictable patterns\n"
        result += f"- Optimize data structure alignment\n"
        result += f"- Consider SIMD vectorization\n"
        result += f"- Profile with hardware performance counters\n\n"
        
        # Success metrics
        result += f"## Success Metrics\n\n"
        target_miss_rate = max(cache_behavior['estimated_miss_rate'] * 0.3, 5)  # 70% reduction
        result += f"- **Estimated cache miss rate:** <{target_miss_rate:.1f}% (current: {cache_behavior.get('estimated_miss_rate', 'N/A'):.1f}%)\n"
        result += f"- **Target memory bandwidth efficiency:** >80% (current: {cache_behavior.get('memory_bandwidth_efficiency', 'N/A'):.1f}%)\n"
        result += f"- **Overall performance target:** {performance_target}\n\n"
        
        # Tools and validation
        result += f"## Validation Tools\n\n"
        result += f"```bash\n"
        result += f"# Cache performance\n"
        result += f"perf stat -e cache-references,cache-misses,L1-dcache-load-misses ./your_program\n\n"
        result += f"# TLB performance\n"
        result += f"perf stat -e dTLB-load-misses,iTLB-load-misses ./your_program\n\n"
        result += f"# Memory bandwidth\n"
        result += f"perf stat -e cpu/mem-loads/,cpu/mem-stores/ ./your_program\n"
        result += f"```\n\n"
        
        # Risk assessment
        result += f"## Risk Assessment\n\n"
        result += f"- **Low risk:** Memory access pattern fixes (Phase 1)\n"
        result += f"- **Medium risk:** Cache blocking may increase code complexity\n"
        result += f"- **High risk:** Advanced optimizations may have limited portability\n\n"
        
        result += f"**Recommendation:** Implement phases sequentially and validate each step.\n"
        
        return result
        
    except Exception as e:
        return f"Error creating optimization plan: {str(e)}"

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
    
    # Return detailed information using explain_memory_concept
    return await explain_memory_concept(concept['title'])

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
