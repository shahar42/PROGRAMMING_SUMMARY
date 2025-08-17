#!/usr/bin/env python3
"""
C++ Standard MCP Server
FastMCP server providing intelligent access to C++ programming concepts
Extracted from ISO/IEC 14882:2014 C++ Programming Language Standard

Features:
- Clear separation from C concepts
- Chapter-based concept organization
- Multi-model extraction metadata
- Modern C++ focus (classes, templates, STL, C++11/14 features)
"""

import json
import re
import sys
from pathlib import Path
from fastmcp import FastMCP

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Initialize MCP server
mcp = FastMCP("C++ Standard Concepts Server")

# Global storage for C++ concepts
cpp_concepts = []

def load_cpp_concepts():
    """Load all C++ concepts from the cpp_standard output directory"""
    global cpp_concepts
    
    # Updated path for C++ concepts
    outputs_dir = Path(__file__).parent.parent / "outputs" / "cpp_standard"
    
    if not outputs_dir.exists():
        print(f"Warning: C++ concepts directory not found: {outputs_dir}")
        return
    
    cpp_concepts.clear()
    
    # Load all C++ concept JSON files
    concept_files = list(outputs_dir.glob("cpp_*.json"))
    
    for concept_file in concept_files:
        try:
            with open(concept_file, 'r') as f:
                concept_data = json.load(f)
            
            # Extract clean concept ID from filename
            filename = concept_file.name
            concept_id_match = re.search(r'cpp_([a-z]+)_(\d+)', filename)
            
            if concept_id_match:
                chapter = concept_id_match.group(1)
                number = concept_id_match.group(2)
                concept_id = f"cpp_{chapter}_{number}"
            else:
                # Fallback ID
                concept_id = f"cpp_concept_{len(cpp_concepts):03d}"
            
            # Standardize concept structure for MCP server
            title = concept_data.get('topic', concept_data.get('title', 'Unknown C++ Concept'))
            description = concept_data.get('explanation', concept_data.get('description', ''))
            
            # Combine explanation and example_explanation for full content
            content_parts = []
            if concept_data.get('explanation'):
                content_parts.append(concept_data['explanation'])
            if concept_data.get('example_explanation'):
                content_parts.append(concept_data['example_explanation'])
            content = '\n\n'.join(content_parts) if content_parts else ''
            
            # Handle C++ code examples
            syntax = concept_data.get('syntax', '')
            if not syntax and concept_data.get('code_example'):
                code_lines = concept_data['code_example']
                if isinstance(code_lines, list):
                    syntax = '\n'.join(code_lines)
                else:
                    syntax = str(code_lines)
            
            # Extract metadata
            metadata = concept_data.get('extraction_metadata', {})
            chapter = metadata.get('chapter', 'basic')
            processor = metadata.get('processor', 'unknown')
            
            concept = {
                'id': concept_id,
                'title': title,
                'description': description,
                'content': content,
                'syntax': syntax,
                'chapter': chapter,
                'processor': processor,
                'book': 'cpp_standard',
                'book_title': 'ISO/IEC 14882:2014 C++ Programming Language Standard',
                'source_file': filename,
                'raw_data': concept_data
            }
            
            cpp_concepts.append(concept)
            
        except Exception as e:
            print(f"Error loading C++ concept {concept_file}: {e}")
    
    print(f"Loaded {len(cpp_concepts)} C++ concepts from {len(concept_files)} files")

# Load concepts on startup
load_cpp_concepts()

@mcp.tool()
def search_cpp_concepts(query: str, limit: int = 10) -> str:
    """Search for C++ programming concepts by keyword or topic.
    
    Args:
        query: Search terms for C++ concepts (e.g., 'templates', 'classes', 'STL')
        limit: Maximum number of results to return
    """
    if not cpp_concepts:
        return "No C++ concepts available. Please run the C++ extraction script first."
    
    query_lower = query.lower()
    results = []
    
    for concept in cpp_concepts:
        # Search in title, description, and content
        searchable_text = (
            concept['title'].lower() + ' ' +
            concept['description'].lower() + ' ' + 
            concept['content'].lower()
        )
        
        if query_lower in searchable_text:
            score = searchable_text.count(query_lower)
            results.append((concept, score))
    
    # Sort by relevance score
    results.sort(key=lambda x: x[1], reverse=True)
    results = results[:limit]
    
    if not results:
        return f"No C++ concepts found for query: '{query}'"
    
    result_text = f"# C++ Concepts Search Results for '{query}'\n\n"
    result_text += f"Found {len(results)} relevant C++ concepts:\n\n"
    
    for concept, score in results:
        result_text += f"## {concept['title']}\n"
        result_text += f"**ID:** `{concept['id']}`\n"
        result_text += f"**Chapter:** {concept['chapter'].title()}\n"
        result_text += f"**Processor:** {concept['processor'].upper()}\n"
        result_text += f"**Description:** {concept['description'][:200]}{'...' if len(concept['description']) > 200 else ''}\n\n"
    
    return result_text

@mcp.tool()
def get_cpp_concept_details(concept_id: str) -> str:
    """Get detailed information about a specific C++ concept.
    
    Args:
        concept_id: The ID of the C++ concept (e.g., 'cpp_classes_042')
    """
    concept = find_cpp_concept_by_id(concept_id)
    
    if not concept:
        return f"C++ concept not found: {concept_id}"
    
    result = f"# {concept['title']}\n\n"
    result += f"**Concept ID:** `{concept['id']}`\n"
    result += f"**Chapter:** {concept['chapter'].title()}\n"
    result += f"**Source:** {concept['book_title']}\n"
    result += f"**Extracted by:** {concept['processor'].upper()}\n\n"
    
    result += f"## Description\n{concept['description']}\n\n"
    
    if concept['content']:
        result += f"## Detailed Explanation\n{concept['content']}\n\n"
    
    if concept['syntax']:
        result += f"## C++ Code Example\n```cpp\n{concept['syntax']}\n```\n\n"
    
    return result

@mcp.tool()
def list_cpp_concepts_by_chapter() -> str:
    """List all C++ concepts organized by C++ standard chapters.
    
    Returns organized view of concepts by chapter (classes, templates, library, etc.)
    """
    if not cpp_concepts:
        return "No C++ concepts available."
    
    # Group by chapter
    by_chapter = {}
    for concept in cpp_concepts:
        chapter = concept['chapter']
        if chapter not in by_chapter:
            by_chapter[chapter] = []
        by_chapter[chapter].append(concept)
    
    result_text = "# C++ Concepts by Standard Chapter\n\n"
    result_text += f"Total C++ concepts: {len(cpp_concepts)}\n\n"
    
    for chapter in sorted(by_chapter.keys()):
        concepts = by_chapter[chapter]
        result_text += f"## {chapter.title()} Chapter ({len(concepts)} concepts)\n\n"
        
        for concept in concepts:
            result_text += f"- **{concept['title']}** (`{concept['id']}`)\n"
            result_text += f"  {concept['description'][:100]}{'...' if len(concept['description']) > 100 else ''}\n\n"
    
    return result_text

@mcp.tool()
def search_cpp_by_feature(feature: str) -> str:
    """Search for C++ concepts by specific language feature.
    
    Args:
        feature: C++ feature type ('classes', 'templates', 'stl', 'modern', 'exceptions')
    """
    feature_keywords = {
        'classes': ['class', 'constructor', 'destructor', 'inheritance', 'virtual', 'polymorphism'],
        'templates': ['template', 'generic', 'specialization', 'metaprogramming', 'SFINAE'],
        'stl': ['std::', 'vector', 'map', 'algorithm', 'iterator', 'container'],
        'modern': ['auto', 'lambda', 'move', 'smart pointer', 'range-based', 'constexpr'],
        'exceptions': ['try', 'catch', 'throw', 'exception', 'RAII'],
        'memory': ['new', 'delete', 'unique_ptr', 'shared_ptr', 'memory management'],
        'operators': ['operator', 'overload', 'overloading']
    }
    
    if feature.lower() not in feature_keywords:
        available_features = ', '.join(feature_keywords.keys())
        return f"Unknown feature '{feature}'. Available features: {available_features}"
    
    keywords = feature_keywords[feature.lower()]
    matching_concepts = []
    
    for concept in cpp_concepts:
        searchable_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()
        
        score = sum(searchable_text.count(keyword) for keyword in keywords)
        if score > 0:
            matching_concepts.append((concept, score))
    
    # Sort by relevance
    matching_concepts.sort(key=lambda x: x[1], reverse=True)
    
    if not matching_concepts:
        return f"No C++ concepts found for feature: {feature}"
    
    result_text = f"# C++ {feature.title()} Concepts\n\n"
    result_text += f"Found {len(matching_concepts)} concepts related to {feature}:\n\n"
    
    for concept, score in matching_concepts[:15]:  # Limit to top 15
        result_text += f"## {concept['title']}\n"
        result_text += f"**ID:** `{concept['id']}` | **Chapter:** {concept['chapter']} | **Score:** {score}\n"
        result_text += f"{concept['description'][:150]}{'...' if len(concept['description']) > 150 else ''}\n\n"
    
    return result_text

@mcp.tool() 
def compare_cpp_concepts(concept1_id: str, concept2_id: str) -> str:
    """Compare two C++ concepts side by side.
    
    Args:
        concept1_id: First C++ concept ID
        concept2_id: Second C++ concept ID
    """
    concept1 = find_cpp_concept_by_id(concept1_id)
    concept2 = find_cpp_concept_by_id(concept2_id)
    
    if not concept1:
        return f"First C++ concept not found: {concept1_id}"
    if not concept2:
        return f"Second C++ concept not found: {concept2_id}"
    
    result = f"# C++ Concept Comparison\n\n"
    result += f"## {concept1['title']} vs {concept2['title']}\n\n"
    
    result += f"| Aspect | {concept1['title']} | {concept2['title']} |\n"
    result += f"|--------|---------|----------|\n"
    result += f"| **ID** | `{concept1['id']}` | `{concept2['id']}` |\n"
    result += f"| **Chapter** | {concept1['chapter']} | {concept2['chapter']} |\n"
    result += f"| **Processor** | {concept1['processor'].upper()} | {concept2['processor'].upper()} |\n"
    result += f"| **Description** | {concept1['description'][:100]}... | {concept2['description'][:100]}... |\n\n"
    
    result += f"### {concept1['title']} Details\n{concept1['content'][:300]}...\n\n"
    result += f"### {concept2['title']} Details\n{concept2['content'][:300]}...\n\n"
    
    return result

@mcp.tool()
def get_cpp_extraction_stats() -> str:
    """Get statistics about C++ concept extraction and multi-model processing."""
    if not cpp_concepts:
        return "No C++ concepts available."
    
    # Count by processor
    processor_stats = {}
    chapter_stats = {}
    
    for concept in cpp_concepts:
        processor = concept.get('processor', 'unknown')
        chapter = concept.get('chapter', 'unknown')
        
        processor_stats[processor] = processor_stats.get(processor, 0) + 1
        chapter_stats[chapter] = chapter_stats.get(chapter, 0) + 1
    
    result = f"# C++ Concept Extraction Statistics\n\n"
    result += f"**Total C++ Concepts:** {len(cpp_concepts)}\n\n"
    
    result += f"## Multi-Model Processing Distribution\n"
    for processor, count in sorted(processor_stats.items()):
        percentage = (count / len(cpp_concepts)) * 100
        result += f"- **{processor.upper()}:** {count} concepts ({percentage:.1f}%)\n"
    
    result += f"\n## Chapter Distribution\n"
    for chapter, count in sorted(chapter_stats.items()):
        result += f"- **{chapter.title()}:** {count} concepts\n"
    
    result += f"\n## Source Information\n"
    result += f"- **Book:** ISO/IEC 14882:2014 C++ Programming Language Standard\n"
    result += f"- **Extraction Method:** Round-robin multi-model (Grok → GPT → Gemini)\n"
    result += f"- **Focus:** Modern C++ features, OOP, templates, STL\n"
    
    return result

def find_cpp_concept_by_id(concept_id: str):
    """Find C++ concept by ID with flexible matching"""
    # Try exact match first
    for concept in cpp_concepts:
        if concept['id'] == concept_id:
            return concept
    
    # Try partial matches
    concept_id_lower = concept_id.lower()
    for concept in cpp_concepts:
        if concept_id_lower in concept['id'].lower():
            return concept
    
    return None

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
