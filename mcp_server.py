#!/usr/bin/env python3
"""
Programming Concepts MCP Server using FastMCP
Provides access to programming concepts from technical books.
ENHANCED: Now includes direct concept access via tools with URI-style addressing
UPDATED: Efficient book-specific duplicate cleanup functionality
"""

import json
import logging
import sys
import string
import asyncio
import os
import requests
from pathlib import Path
from typing import Any, Dict, List, Tuple
from collections import defaultdict
import re
import openai
from datetime import datetime
from dotenv import load_dotenv

# Current directory is automatically in path for modern Python

from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv('config/config.env')

# Get project root from environment or use script's directory
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", SCRIPT_DIR))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("programming-concepts-mcp")

# Initialize FastMCP server
mcp = FastMCP("programming-concepts")

# Initialize OpenAI client for hidden gems evaluation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logger.info("✅ OpenAI API key loaded for hidden gems evaluation")
else:
    logger.warning("⚠️ OpenAI API key not found - using heuristic evaluation")

# Global variables for concepts database
concepts = []
books_metadata = {
    "kernighan_ritchie": "The C Programming Language (Kernighan & Ritchie)",
    "unix_env": "Advanced Programming in the UNIX Environment (Stevens)",
    "linkers_loaders": "Linkers and Loaders (Levine)",
    "os_three_pieces": "Operating Systems: Three Easy Pieces (Arpaci-Dusseau)",
    "expert_c_programming": "Expert C Programming Deep C Secrets (van der Linden)",
    "csapp_2016": "Computer Systems: A Programmer's Perspective (3rd Edition)",
    "cpp_standard": "The C++ Standard Library (ISO/IEC 14882)",
    "cpp_primer": "C++ Primer (5th Edition)",
    "Inside_the_C++_Object_Model": "Inside the C++ Object Model (Stanley Lippman)",
    "cpp_stl_containers": "C++ STL Containers (Extracted Concepts)",
    "posix_manpages": "POSIX Manual Pages"
}

# Book authority weights for relevance scoring
BOOK_AUTHORITY = {
    "kernighan_ritchie": 3.0,      # Authoritative for C
    "csapp_2016": 3.0,             # Authoritative for systems (boosted from 2.8)
    "cpp_standard": 3.0,           # Authoritative for C++
    "expert_c_programming": 2.5,   # Advanced C concepts
    "unix_env": 2.7,               # UNIX/systems
    "os_three_pieces": 2.4,        # OS concepts
    "cpp_primer": 2.0,             # Tutorial level
    "linkers_loaders": 2.6,        # Specialized topic
    "Inside_the_C++_Object_Model": 2.7,  # Advanced C++
    "cpp_stl_containers": 2.3,     # STL specific
    "posix_manpages": 2.5,         # Reference material (reasonable universal weight)
}

# Context hints for boosting relevant books based on query terms
CONTEXT_HINTS = {
    'cpp': ['cpp_standard', 'cpp_primer', 'Inside_the_C++_Object_Model', 'cpp_stl_containers'],
    'c++': ['cpp_standard', 'cpp_primer', 'Inside_the_C++_Object_Model', 'cpp_stl_containers'],
    'stl': ['cpp_stl_containers', 'cpp_standard', 'cpp_primer'],
    'std::': ['cpp_standard', 'cpp_stl_containers'],
    'system': ['csapp_2016', 'unix_env', 'os_three_pieces', 'posix_manpages'],
    'syscall': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'system call': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'unix': ['unix_env', 'csapp_2016', 'posix_manpages'],
    'linux': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'pipe': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'fork': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'read': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'write': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'open': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'close': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'file descriptor': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'process': ['posix_manpages', 'unix_env', 'csapp_2016', 'os_three_pieces'],
    'thread': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'signal': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'ipc': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'socket': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'network': ['posix_manpages', 'unix_env', 'csapp_2016'],
    'memory': ['csapp_2016', 'kernighan_ritchie', 'expert_c_programming'],
    'link': ['linkers_loaders', 'csapp_2016'],
    'vector': ['cpp_stl_containers', 'cpp_standard'],
    'sort': ['cpp_stl_containers', 'cpp_standard'],
    'algorithm': ['cpp_stl_containers', 'cpp_standard'],
    'template': ['cpp_standard', 'cpp_primer', 'Inside_the_C++_Object_Model'],
    'object': ['Inside_the_C++_Object_Model', 'cpp_standard', 'cpp_primer'],
    'posix': ['posix_manpages', 'unix_env'],
}


def build_concept_index():
    """Build the concept index from outputs directory, using a cache for performance."""
    global concepts
    
    # Use global PROJECT_ROOT instead of hardcoded path
    outputs_dir = PROJECT_ROOT / "outputs"
    cache_file = outputs_dir / "concept_cache.json"
    
    if not outputs_dir.exists():
        logger.error("outputs directory not found")
        return

    # Check if cache is valid
    if cache_file.exists():
        logger.info("Cache file found. Checking for modifications...")
        cache_mod_time = cache_file.stat().st_mtime
        
        # Find the most recently modified concept file
        latest_concept_mod_time = 0
        for book_dir in outputs_dir.iterdir():
            if book_dir.is_dir():
                for concept_file in book_dir.glob("*.json"):
                    if concept_file.name not in ["progress.json", "metadata.json", "summary.json", "concept_cache.json"]:
                        latest_concept_mod_time = max(latest_concept_mod_time, concept_file.stat().st_mtime)

        if cache_mod_time >= latest_concept_mod_time:
            logger.info("Cache is up-to-date. Loading from cache.")
            with open(cache_file, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
            logger.info(f"Successfully loaded {len(concepts)} concepts from cache.")
            return

    logger.info("Cache is outdated or not found. Rebuilding concept index.")
    concepts = []
    total_concepts = 0

    for book_dir in outputs_dir.iterdir():
        if not book_dir.is_dir():
            continue

        book_name = book_dir.name
        if book_name not in books_metadata:
            continue

        logger.info(f"Indexing book: {book_name}")

        concept_files = [f for f in book_dir.glob("*.json")
                         if f.name not in ["progress.json", "metadata.json", "summary.json", "concept_cache.json"]
                         and not f.name.endswith("_summary.md") and ".backup" not in f.name]
        
        book_concepts = 0
        for concept_file in concept_files:
            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept_data = json.load(f)

                if isinstance(concept_data, list):
                    for concept in concept_data:
                        add_concept(concept, book_name, concept_file.name)
                        book_concepts += 1
                elif isinstance(concept_data, dict):
                    add_concept(concept_data, book_name, concept_file.name)
                    book_concepts += 1
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {concept_file}: {e}")

        if book_concepts > 0:
            logger.info(f"Found {book_concepts} concepts in {book_name}")
            total_concepts += book_concepts

    logger.info(f"Successfully indexed {total_concepts} concepts.")
    
    # Save to cache
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(concepts, f)
        logger.info(f"Saved {len(concepts)} concepts to cache file: {cache_file}")
    except IOError as e:
        logger.error(f"Failed to write to cache file: {e}")


def add_concept(concept_data: Dict[str, Any], book_name: str, filename: str):
    """Add a concept to the index with proper field mapping and CLEAN ID generation."""
    global concepts

    # Extract category from new naming scheme if available
    category = extract_category_from_filename(filename)

    # Generate clean IDs using ONLY the new naming scheme
    # New naming scheme - use filename stem as ID
    concept_id = f"{book_name}_{Path(filename).stem}"

    # SURGICAL FIX: Map the standardized extractor format to MCP server expectations
    title = concept_data.get('topic', concept_data.get('title', concept_data.get('concept', 'Unknown Concept')))
    description = concept_data.get('explanation', concept_data.get('description', concept_data.get('summary', '')))

    # Combine 'explanation' and 'example_explanation' for full content
    content_parts = []
    if concept_data.get('explanation'):
        content_parts.append(concept_data['explanation'])
    if concept_data.get('example_explanation'):
        content_parts.append(concept_data['example_explanation'])
    content = '\n\n'.join(content_parts) if content_parts else concept_data.get('content', '')

    # Handle code examples: prefer existing 'syntax', fallback to formatted 'code_example'
    syntax = concept_data.get('syntax', '')
    if not syntax and concept_data.get('code_example'):
        code_lines = concept_data['code_example']
        if isinstance(code_lines, list):
            syntax = '\n'.join(code_lines)
        else:
            syntax = str(code_lines)

    concept = {
        'id': concept_id,  # CLEAN ID
        'title': title,
        'description': description,
        'content': content,
        'syntax': syntax,
        'book': book_name,
        'book_title': books_metadata.get(book_name, book_name),
        'source_file': filename,
        'category': category,  # New field for category-based filtering
        'raw_data': concept_data
    }

    concepts.append(concept)


def extract_category_from_filename(filename):
    """Extract category from new naming scheme filename"""
    # Pattern: {book_code}_{category}_{topic}_{hash}.json
    # Examples: cppx_func_*, cppx_mem_*, kr_ptr_*, etc.
    parts = filename.split('_')
    if len(parts) >= 2:
        # Second part after book code should be category
        return parts[1]
    return None


def find_concept_by_id_flexible(concept_id: str):
    """Find concept by ID with flexible matching"""
    # Try exact match first
    for concept in concepts:
        if concept['id'] == concept_id:
            return concept

    # Try case-insensitive partial match as fallback
    concept_id_lower = concept_id.lower()
    for concept in concepts:
        if concept_id_lower in concept['id'].lower():
            return concept

    return None




def load_posix_concepts():
    """Load POSIX syscalls as concepts from converted format"""
    # Load from converted concepts directory
    posix_concepts_dir = PROJECT_ROOT / "outputs/posix_manpages_concepts"

    if not posix_concepts_dir.exists():
        logger.warning(f"POSIX concepts directory not found: {posix_concepts_dir}")
        return

    logger.info(f"Loading POSIX concepts from {posix_concepts_dir}")
    loaded_count = 0

    for json_file in posix_concepts_dir.glob("posix_sys_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)

            # Add the concept directly (it's already in the right format)
            add_concept(concept_data, 'posix_manpages', json_file.name)
            loaded_count += 1

        except Exception as e:
            logger.warning(f"Error loading POSIX concept {json_file}: {e}")

    logger.info(f"✅ Loaded {loaded_count} POSIX system call concepts")


# ===============================
# ENHANCED CONCEPT ACCESS
# ===============================

def concept_to_clean_uri_id(concept):
    """Convert concept to clean URI-friendly ID"""
    # Use the original filename without extension as the base
    base_id = concept['source_file'].replace('.json', '')

    # Clean up the ID to be URI-friendly
    clean_id = re.sub(r'[^\w\-_]', '_', base_id)
    clean_id = re.sub(r'_+', '_', clean_id)  # Remove multiple underscores
    clean_id = clean_id.strip('_')  # Remove leading/trailing underscores

    return clean_id


def find_concept_by_uri_id(book_name: str, uri_id: str):
    """Find concept by book and URI ID"""
    for concept in concepts:
        if concept['book'] == book_name:
            concept_uri_id = concept_to_clean_uri_id(concept)
            if concept_uri_id == uri_id:
                return concept
    return None


# ===============================
# EFFICIENT DUPLICATE CLEANUP TOOLS
# ===============================

@mcp.tool()
async def analyze_concept_duplicates(book_name: str, similarity_threshold: float = 0.90) -> str:
    """Analyze duplicate concepts in a book directory without making any changes.

    Args:
        book_name: Book directory name (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming, csapp_2016)
        similarity_threshold: Similarity threshold for considering duplicates (0.0-1.0, default: 0.90)
    """
    from pathlib import Path
    import json
    from difflib import SequenceMatcher

    # Validate book name
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Invalid book name '{book_name}'. Available books: {', '.join(available_books)}"

    # Get book directory
    # Use global PROJECT_ROOT instead of hardcoded path
    book_dir = PROJECT_ROOT / "outputs" / book_name

    if not book_dir.exists():
        return f"Book directory not found: {book_dir}"

    # Find all JSON files except progress.json and backup files
    all_json_files = list(book_dir.glob("*.json"))
    concept_files = [f for f in all_json_files if not (
            f.name == 'progress.json' or
            'backup' in f.name.lower()
    )]

    if not concept_files:
        return f"No concept files found in {book_dir}"

    result_parts = [
        f"# 📊 Duplicate Analysis for {books_metadata[book_name]}\n\n",
        f"**Files Analyzed:** {len(concept_files)}\n",
        f"**Similarity Threshold:** {similarity_threshold:.0%}\n\n"
    ]

    # Load all concepts
    loaded_concepts = []
    for file_path in concept_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)
                loaded_concepts.append({
                    'data': concept_data,
                    'file_path': file_path,
                    'file_name': file_path.name
                })
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")

    # Calculate similarity matrix for top similar pairs
    similar_pairs = []

    for i, concept1 in enumerate(loaded_concepts):
        for j, concept2 in enumerate(loaded_concepts[i + 1:], i + 1):
            # Calculate similarity using same algorithm as cleanup tool
            topic1 = concept1['data'].get('topic', '')
            topic2 = concept2['data'].get('topic', '')
            topic_sim = SequenceMatcher(None, topic1.lower(), topic2.lower()).ratio()

            exp1 = concept1['data'].get('explanation', '')
            exp2 = concept2['data'].get('explanation', '')
            exp_sim = SequenceMatcher(None, exp1.lower(), exp2.lower()).ratio()

            combined_similarity = (topic_sim * 0.3 + exp_sim * 0.7)

            if combined_similarity >= 0.5:  # Include moderately similar pairs for analysis
                similar_pairs.append({
                    'similarity': combined_similarity,
                    'concept1': concept1,
                    'concept2': concept2,
                    'is_duplicate': combined_similarity >= similarity_threshold
                })

    # Sort by similarity (highest first)
    similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)

    # Count duplicates
    duplicates = [pair for pair in similar_pairs if pair['is_duplicate']]

    result_parts.extend([
        f"## Summary\n\n",
        f"- **Total similar pairs found:** {len(similar_pairs)}\n",
        f"- **Pairs above duplicate threshold:** {len(duplicates)}\n",
        f"- **Estimated files that could be removed:** {len(duplicates)}\n\n"
    ])

    if duplicates:
        result_parts.append(f"## 🚨 Potential Duplicates (≥{similarity_threshold:.0%} similar)\n\n")
        for i, pair in enumerate(duplicates[:10], 1):  # Show top 10
            result_parts.extend([
                f"### {i}. Similarity: {pair['similarity']:.1%}\n",
                f"**File 1:** `{pair['concept1']['file_name']}`\n",
                f"Topic: {pair['concept1']['data'].get('topic', 'Unknown')}\n\n",
                f"**File 2:** `{pair['concept2']['file_name']}`\n",
                f"Topic: {pair['concept2']['data'].get('topic', 'Unknown')}\n\n"
            ])

        if len(duplicates) > 10:
            result_parts.append(f"*...and {len(duplicates) - 10} more duplicate pairs*\n\n")

    if len(similar_pairs) > len(duplicates):
        result_parts.append(f"## 📋 Other Similar Pairs ({similarity_threshold - 0.1:.0%}-{similarity_threshold:.0%} similar)\n\n")
        similar_not_dup = [p for p in similar_pairs if not p['is_duplicate']][:5]

        for i, pair in enumerate(similar_not_dup, 1):
            result_parts.append(f"{i}. **{pair['similarity']:.1%}** - `{pair['concept1']['file_name']}` vs `{pair['concept2']['file_name']}`\n")

    result_parts.append(f"\n## 💡 Recommendations\n\n")

    if duplicates:
        result_parts.extend([
            f"- Run `cleanup_duplicate_concepts('{book_name}', {similarity_threshold}, True)` for a dry run\n",
            f"- Run `cleanup_duplicate_concepts('{book_name}', {similarity_threshold}, False)` to perform cleanup\n",
            f"- Consider adjusting threshold if too many/few duplicates detected\n"
        ])
    else:
        result_parts.extend([
            f"- ✅ No duplicates found at {similarity_threshold:.0%} threshold\n",
            f"- Consider lowering threshold (e.g., 0.80) if you want more aggressive deduplication\n"
        ])

    return ''.join(result_parts)


@mcp.tool()
async def cleanup_duplicate_concepts(book_name: str, similarity_threshold: float = 0.90, dry_run: bool = True) -> str:
    """Clean up duplicate concept files for a specific book.

    Args:
        book_name: Book directory name (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming, csapp_2016)
        similarity_threshold: Similarity threshold for considering duplicates (0.0-1.0, default: 0.90)
        dry_run: If True, only report what would be cleaned without actually deleting files
    """
    from pathlib import Path
    import shutil
    from datetime import datetime
    import json
    from difflib import SequenceMatcher

    # Validate book name
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Invalid book name '{book_name}'. Available books: {', '.join(available_books)}"

    # Get book directory
    # Use global PROJECT_ROOT instead of hardcoded path
    book_dir = PROJECT_ROOT / "outputs" / book_name

    if not book_dir.exists():
        return f"Book directory not found: {book_dir}"

    # Find all JSON files except progress.json and backup files
    all_json_files = list(book_dir.glob("*.json"))
    concept_files = [f for f in all_json_files if not (
            f.name == 'progress.json' or
            'backup' in f.name.lower()
    )]

    if not concept_files:
        return f"No concept files found in {book_dir}"

    result = f"# 🧹 Duplicate Cleanup Report for {books_metadata[book_name]}\n\n"
    result += f"**Similarity Threshold:** {similarity_threshold:.0%}\n"
    result += f"**Mode:** {'DRY RUN (no files will be deleted)' if dry_run else 'ACTIVE CLEANUP'}\n"
    result += f"**Files Scanned:** {len(concept_files)}\n\n"

    # Load all concepts for comparison
    loaded_concepts = []
    failed_loads = 0

    for file_path in concept_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)
                loaded_concepts.append({
                    'data': concept_data,
                    'file_path': file_path,
                    'file_name': file_path.name
                })
        except Exception as e:
            failed_loads += 1
            logger.warning(f"Failed to load {file_path}: {e}")

    if failed_loads > 0:
        result_parts.append(f"⚠️ **Warning:** {failed_loads} files could not be loaded\n\n")

    # Helper function to calculate similarity between concepts
    def calculate_concept_similarity(concept1_data, concept2_data):
        """Calculate similarity between two concepts using multiple factors"""

        # Topic similarity
        topic1 = concept1_data.get('topic', '')
        topic2 = concept2_data.get('topic', '')
        topic_sim = SequenceMatcher(None, topic1.lower(), topic2.lower()).ratio()

        # Explanation similarity
        exp1 = concept1_data.get('explanation', '')
        exp2 = concept2_data.get('explanation', '')
        exp_sim = SequenceMatcher(None, exp1.lower(), exp2.lower()).ratio()

        # Code similarity (if both have code)
        code_sim = 0.0
        code1 = concept1_data.get('code_example', [])
        code2 = concept2_data.get('code_example', [])

        if code1 and code2:
            code_text1 = '\n'.join(code1) if isinstance(code1, list) else str(code1)
            code_text2 = '\n'.join(code2) if isinstance(code2, list) else str(code2)
            code_sim = SequenceMatcher(None, code_text1.lower(), code_text2.lower()).ratio()

        # Content similarity
        content1 = concept1_data.get('content', concept1_data.get('example_explanation', ''))
        content2 = concept2_data.get('content', concept2_data.get('example_explanation', ''))
        content_sim = SequenceMatcher(None, content1.lower(), content2.lower()).ratio()

        # Weighted average
        weights = {'topic': 0.3, 'explanation': 0.4, 'code': 0.2, 'content': 0.1}
        combined_similarity = (
                topic_sim * weights['topic'] +
                exp_sim * weights['explanation'] +
                code_sim * weights['code'] +
                content_sim * weights['content']
        )

        return combined_similarity

    # Find duplicate groups
    duplicate_groups = []
    processed_indices = set()

    for i, concept1 in enumerate(loaded_concepts):
        if i in processed_indices:
            continue

        duplicate_group = [concept1]
        processed_indices.add(i)

        for j, concept2 in enumerate(loaded_concepts[i + 1:], i + 1):
            if j in processed_indices:
                continue

            similarity = calculate_concept_similarity(concept1['data'], concept2['data'])

            if similarity >= similarity_threshold:
                duplicate_group.append(concept2)
                processed_indices.add(j)

        if len(duplicate_group) > 1:
            duplicate_groups.append(duplicate_group)

    # Report findings
    if not duplicate_groups:
        result_parts.append("✅ **No duplicates found!** All concepts appear to be unique.\n")
        return ''.join(result_parts)

    result_parts.append(f"🔍 **Found {len(duplicate_groups)} duplicate groups:**\n\n")

    files_to_delete = []
    files_kept = []
    backup_dir = None

    if not dry_run:
        # Create backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = book_dir / f"cleanup_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

    for group_num, group in enumerate(duplicate_groups, 1):
        result_parts.append(f"### Group {group_num}: {len(group)} similar concepts\n\n")

        # Choose the best concept to keep (longest explanation or most recent)
        best_concept = max(group, key=lambda x: (
            len(x['data'].get('explanation', '')),
            len(x['data'].get('code_example', [])),
            x['file_path'].stat().st_mtime
        ))

        files_kept.append(best_concept['file_name'])

        for i, concept in enumerate(group):
            is_keeper = concept == best_concept

            # Calculate similarity with best concept
            if concept != best_concept:
                similarity = calculate_concept_similarity(best_concept['data'], concept['data'])
                similarity_text = f" (similarity: {similarity:.1%})"
            else:
                similarity_text = ""

            status = "**KEEP**" if is_keeper else ("WOULD DELETE" if dry_run else "DELETE")
            result_parts.extend([
                f"- {status}: `{concept['file_name']}`{similarity_text}\n",
                f"  Topic: {concept['data'].get('topic', 'Unknown')[:60]}...\n"
            ])

            if not is_keeper:
                if not dry_run:
                    # Create backup before deletion
                    backup_path = backup_dir / concept['file_name']
                    shutil.copy2(concept['file_path'], backup_path)

                    # Delete the duplicate
                    concept['file_path'].unlink()
                    files_to_delete.append(concept['file_name'])
                else:
                    files_to_delete.append(concept['file_name'])

        result_parts.append("\n")

    # Summary
    result_parts.extend([
        "## 📊 Cleanup Summary\n\n",
        f"- **Duplicate groups found:** {len(duplicate_groups)}\n",
        f"- **Files to delete:** {len(files_to_delete)}\n",
        f"- **Files kept:** {len(files_kept)}\n"
    ])

    if not dry_run:
        result_parts.extend([
            f"- **Backup location:** `{backup_dir}`\n",
            f"- **Files deleted:** {len(files_to_delete)}\n",
            "\n✅ **Cleanup completed successfully!**\n",
            "\n💡 **Note:** Deleted files are backed up and can be restored if needed.\n"
        ])
    else:
        result_parts.extend([
            "\n⚠️ **This was a dry run** - no files were actually deleted.\n",
            f"\nRun `cleanup_duplicate_concepts('{book_name}', {similarity_threshold}, False)` to perform actual cleanup."
        ])

    return ''.join(result_parts)


# ===============================
# SEARCH AND DISCOVERY TOOLS
# ===============================

def _validate_and_preprocess_query(query: str) -> tuple[str, str]:
    """Validate query and return (processed_query, query_type)"""
    if not query or query.isspace():
        return "", "EMPTY"
    if query == "*":
        return "*", "WILDCARD" 
    if query.isdigit():
        return query, "NUMERIC"
    if all(c in string.punctuation + string.whitespace for c in query):
        return "", "INVALID"
    return query.strip().lower(), "NORMAL"


def _calculate_enhanced_relevance(concept, search_terms, base_score):
    """Enhanced relevance calculation with context awareness"""
    enhanced_score = base_score
    
    # Book authority multiplier
    authority_weight = BOOK_AUTHORITY.get(concept['book'], 1.0)
    enhanced_score *= authority_weight
    
    # Context bonus - if query contains context hints, boost matching books
    for term in search_terms:
        for context, preferred_books in CONTEXT_HINTS.items():
            if context in term and concept['book'] in preferred_books:
                enhanced_score *= 1.8  # 80% bonus for context match (boosted from 1.5)
                break

    # Special syscall bonus - extra boost for POSIX manpages on syscall queries
    syscall_terms = ['syscall', 'system call', 'open', 'pipe', 'fork', 'exec', 'read', 'write', 'close', 'dup', 'wait']
    for term in search_terms:
        if any(syscall_term in term for syscall_term in syscall_terms) and concept['book'] == 'posix_manpages':
            enhanced_score *= 1.4  # Additional 40% bonus for POSIX syscalls
            break
    
    # Exact title match gets huge bonus
    for term in search_terms:
        if term in concept['title'].lower():
            enhanced_score *= 2.0
            
    return enhanced_score


def _fuzzy_match_book_name(user_input: str) -> str:
    """Fuzzy match user input to actual book names for natural UX"""
    if not user_input:
        return None
        
    user_lower = user_input.lower().replace(' ', '').replace('_', '').replace('-', '')
    
    # Direct mappings for common user inputs
    book_aliases = {
        'kr': 'kernighan_ritchie',
        'kernighan': 'kernighan_ritchie', 
        'ritchie': 'kernighan_ritchie',
        'cbook': 'kernighan_ritchie',
        'cprogramming': 'kernighan_ritchie',
        
        'cppprimer': 'cpp_primer',
        'primer': 'cpp_primer',
        'c++primer': 'cpp_primer',
        
        'cppstandard': 'cpp_standard',
        'standard': 'cpp_standard',
        'c++standard': 'cpp_standard',
        'iso': 'cpp_standard',
        
        'csapp': 'csapp_2016',
        'computersystems': 'csapp_2016',
        'systems': 'csapp_2016',
        
        'unix': 'unix_env',
        'unixenvironment': 'unix_env',
        'stevens': 'unix_env',
        
        'os': 'os_three_pieces',
        'operatingsystems': 'os_three_pieces',
        'threepieces': 'os_three_pieces',
        
        'expertc': 'expert_c_programming',
        'expert': 'expert_c_programming',
        'secrets': 'expert_c_programming',
        
        'linkers': 'linkers_loaders',
        'loaders': 'linkers_loaders',
        'levine': 'linkers_loaders',
        
        'objectmodel': 'Inside_the_C++_Object_Model',
        'lippman': 'Inside_the_C++_Object_Model',
        
        'stl': 'cpp_stl_containers',
        'containers': 'cpp_stl_containers',
        
        'posix': 'posix_manpages',
        'manpages': 'posix_manpages',
        'man': 'posix_manpages',
    }
    
    # Check aliases first
    if user_lower in book_aliases:
        return book_aliases[user_lower]
    
    # Fuzzy matching against actual book names and titles
    available_books = list(books_metadata.keys())
    
    # Try partial matching on book codes
    for book_code in available_books:
        if user_lower in book_code.lower().replace('_', ''):
            return book_code
    
    # Try partial matching on book titles
    for book_code, book_title in books_metadata.items():
        title_clean = book_title.lower().replace(' ', '').replace('(', '').replace(')', '').replace(':', '')
        if user_lower in title_clean or title_clean.startswith(user_lower):
            return book_code
    
    # No match found
    return None


async def _evaluate_concept_as_gem(concept: dict) -> tuple[int, str]:
    """Use OpenAI to evaluate if a concept is a 'hidden gem' (0-10 rating)"""
    
    # Prepare content for evaluation (truncate if too long)
    title = concept.get('title', 'Unknown Title')
    content = concept.get('content', '') + ' ' + concept.get('description', '')
    content = content[:800] + '...' if len(content) > 800 else content
    
    # Create evaluation prompt
    prompt = f"""Analyze this programming concept and rate it as a "hidden gem" (0-10):

Title: {title}
Content: {content}

A TRUE hidden gem must be:
- Something that would shock even expert C++/systems programmers
- Obscure implementation details that reveal secret compiler/OS behavior  
- Counter-intuitive gotchas that contradict common assumptions
- Internal mechanisms that are deliberately hidden from developers
- Bugs, quirks, or undocumented behaviors in compilers/systems
- Implementation details that even seasoned developers rarely encounter

BE EXTREMELY SELECTIVE. Most concepts should score 0-4.

Rate 0-10 where:
- 0-4: Known to experienced developers, documented behavior, or obvious
- 5-6: Advanced knowledge but still somewhat familiar to experts
- 7-8: TRULY surprising - even experts would say "I had no idea!"
- 9-10: Mind-blowing secrets that reveal hidden system internals

Only score 7+ if this would genuinely shock an expert who's been programming for 10+ years.

Format your response as: SCORE: X | REASON: brief explanation of why it's truly hidden"""

    try:
        # Use OpenAI API if available, otherwise fall back to heuristics
        if OPENAI_API_KEY:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",  # Using cost-effective model for evaluations
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a 20-year veteran systems programmer evaluating concepts for 'hidden gem' potential. Be RUTHLESSLY selective - most concepts should score 0-4. Only score 7+ for secrets that would shock even expert developers with decades of experience. Look for undocumented behaviors, implementation quirks, and truly obscure gotchas."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result['choices'][0]['message']['content'].strip()
                
                # Parse the response to extract score and reason
                try:
                    # Look for "SCORE: X" pattern
                    score_match = re.search(r'SCORE:\s*(\d+)', llm_response, re.IGNORECASE)
                    reason_match = re.search(r'REASON:\s*(.+)', llm_response, re.IGNORECASE)
                    
                    score = int(score_match.group(1)) if score_match else 0
                    reason = reason_match.group(1).strip() if reason_match else llm_response
                    
                    # Clamp score to valid range
                    score = max(0, min(10, score))
                    
                    return score, reason
                
                except (ValueError, AttributeError):
                    # Fallback: try to extract number from response
                    numbers = re.findall(r'\d+', llm_response)
                    score = int(numbers[0]) if numbers else 0
                    return max(0, min(10, score)), llm_response[:100]
            
            else:
                logger.warning(f"OpenAI API error {response.status_code}: {response.text}")
                # Fall through to heuristics
        
        # Fallback: Use heuristic-based scoring if OpenAI unavailable
        score = 0
        content_lower = (title + ' ' + content).lower()
        
        # Tier 1: Ultra-rare gems (3 points each)
        ultra_rare = ['vtable', 'thunk', 'abi', 'bootstrap', 'relocatable', 'elf', 
                     'instruction pipeline', 'branch prediction', 'context switch', 'sfinae']
        if any(word in content_lower for word in ultra_rare):
            score += 3
            
        # Tier 2: Deep system knowledge (2 points each)  
        deep_system = ['assembly', 'linker', 'kernel', 'system call', 'undefined behavior',
                      'race condition', 'dynamic dispatch', 'symbol resolution', 'lazy binding',
                      'virtual memory', 'paging', 'interrupt', 'privilege level']
        if any(word in content_lower for word in deep_system):
            score += 2
            
        # Tier 3: Implementation details (1 point each)
        implementation = ['implementation', 'internal', 'mechanism', 'optimization', 
                         'compiler', 'runtime', 'gotcha', 'subtle', 'profiling', 'debugging']
        if any(word in content_lower for word in implementation):
            score += 1
            
        # Bonus for code examples
        if content.count('```') > 0 or 'example' in content_lower:
            score += 1
            
        # Simple reason generation for heuristic fallback
        reasons = []
        if 'vtable' in content_lower:
            reasons.append("reveals virtual function table internals")
        elif 'assembly' in content_lower:
            reasons.append("shows low-level assembly details")
        elif 'undefined behavior' in content_lower:
            reasons.append("explains dangerous undefined behavior")
        elif 'optimization' in content_lower:
            reasons.append("reveals compiler optimization secrets")
        elif 'implementation' in content_lower:
            reasons.append("exposes internal implementation details")
        else:
            reasons.append("contains advanced system-level concepts")
            
        reason = f"[Heuristic] This concept {reasons[0]} that most developers rarely encounter"
        
        return min(score, 10), reason
        
    except Exception as e:
        logger.warning(f"Evaluation failed: {e}")
        return 0, "Evaluation failed"


def _expand_search_terms(query: str) -> list:
    """Expand search query with acronyms, synonyms, and related terms."""

    # Define acronym and synonym mappings
    search_expansions = {
        # System Programming Acronyms
        'got': ['global offset table', 'got'],
        'plt': ['procedure linkage table', 'plt'],
        'pic': ['position independent code', 'pic'],
        'elf': ['executable linkage format', 'elf'],
        'dll': ['dynamic link library', 'dll'],
        'so': ['shared object', 'shared library', 'so'],
        'api': ['application programming interface', 'api'],
        'abi': ['application binary interface', 'abi'],
        'tls': ['thread local storage', 'tls'],
        'rcu': ['read copy update', 'rcu'],
        'ipc': ['inter process communication', 'ipc'],
        'mmu': ['memory management unit', 'mmu'],
        'tlb': ['translation lookaside buffer', 'tlb'],
        'vm': ['virtual memory', 'vm'],
        'vma': ['virtual memory area', 'vma'],

        # Core C++ Acronyms & Concepts
        'raii': ['resource acquisition is initialization', 'raii'],
        'rtti': ['runtime type information', 'rtti'],
        'sfinae': ['substitution failure is not an error', 'sfinae'],
        'crtp': ['curiously recurring template pattern', 'crtp'],
        'pimpl': ['pointer to implementation', 'pimpl', 'opaque pointer'],
        'rvo': ['return value optimization', 'rvo'],
        'nrvo': ['named return value optimization', 'nrvo'],
        'oop': ['object oriented programming', 'oop'],
        'vtable': ['virtual table', 'vtable', 'virtual function table', 'vptr'],
        'vptr': ['virtual pointer', 'vptr', 'vtable pointer'],
        'adl': ['argument dependent lookup', 'adl', 'koenig lookup'],
        'ebo': ['empty base optimization', 'ebo'],
        'nttp': ['non type template parameter', 'nttp'],
        'ude': ['user defined explicit', 'ude'],
        'udl': ['user defined literal', 'udl'],
        'udt': ['user defined type', 'udt'],
        'pod': ['plain old data', 'pod'],
        'pmd': ['pointer to member data', 'pmd'],
        'pmf': ['pointer to member function', 'pmf'],
        'decay': ['type decay', 'decay'],

        # STL & Standard Library
        'stl': ['standard template library', 'stl'],
        'allocator': ['allocator', 'memory allocator', 'custom allocator'],
        'iterator': ['iterator', 'iterator pattern', 'iterator concept'],
        'functor': ['functor', 'function object', 'callable object'],
        'predicate': ['predicate', 'predicate function', 'boolean function'],
        'lambda': ['lambda', 'lambda expression', 'anonymous function'],
        'closure': ['closure', 'lambda closure', 'captured variables'],

        # Modern C++ (C++11/14/17/20/23)
        'auto': ['auto', 'auto keyword', 'type deduction'],
        'decltype': ['decltype', 'decltype keyword', 'type deduction'],
        'constexpr': ['constexpr', 'compile time constant', 'constant expression'],
        'consteval': ['consteval', 'immediate function', 'compile time evaluation'],
        'constinit': ['constinit', 'constant initialization'],
        'concept': ['concept', 'concepts', 'type constraint'],
        'requires': ['requires', 'requires clause', 'constraint'],
        'noexcept': ['noexcept', 'noexcept specifier', 'exception specification'],
        'override': ['override', 'override specifier'],
        'final': ['final', 'final specifier', 'final class'],
        'default': ['default', 'defaulted function', 'compiler generated'],
        'delete': ['delete', 'deleted function', 'explicitly deleted'],
        'explicit': ['explicit', 'explicit constructor', 'explicit conversion'],
        'move': ['move', 'move semantics', 'rvalue reference', 'std::move'],
        'forward': ['forward', 'perfect forwarding', 'std::forward'],
        'emplace': ['emplace', 'in place construction', 'emplace_back'],

        # C++ Core Language Features
        'template': ['template', 'generic programming', 'template programming'],
        'specialization': ['specialization', 'template specialization', 'explicit specialization'],
        'instantiation': ['instantiation', 'template instantiation'],
        'metaprogramming': ['metaprogramming', 'template metaprogramming', 'compile time programming'],
        'variadic': ['variadic', 'variadic template', 'parameter pack'],
        'fold': ['fold', 'fold expression', 'parameter pack expansion'],
        'inheritance': ['inheritance', 'class inheritance', 'base class', 'derived class'],
        'polymorphism': ['polymorphism', 'virtual function', 'dynamic dispatch'],
        'encapsulation': ['encapsulation', 'data hiding', 'access control'],
        'abstraction': ['abstraction', 'abstract class', 'interface'],
        'composition': ['composition', 'object composition', 'has-a relationship'],
        'aggregation': ['aggregation', 'object aggregation'],
        'association': ['association', 'object association'],

        # Memory Management
        'smart_pointer': ['smart pointer', 'smart_ptr', 'unique_ptr', 'shared_ptr', 'weak_ptr'],
        'unique_ptr': ['unique_ptr', 'unique pointer', 'exclusive ownership'],
        'shared_ptr': ['shared_ptr', 'shared pointer', 'reference counting'],
        'weak_ptr': ['weak_ptr', 'weak pointer', 'non owning pointer'],
        'make_unique': ['make_unique', 'make unique'],
        'make_shared': ['make_shared', 'make shared'],
        'allocator_traits': ['allocator_traits', 'allocator traits'],

        # Exception Handling
        'exception': ['exception', 'exception handling', 'try catch'],
        'throw': ['throw', 'throw statement', 'exception throwing'],
        'catch': ['catch', 'catch block', 'exception catching'],
        'rethrow': ['rethrow', 'rethrow exception'],
        'nested_exception': ['nested_exception', 'nested exception'],
        'exception_ptr': ['exception_ptr', 'exception pointer'],

        # Concurrency & Threading
        'thread': ['thread', 'threading', 'std::thread'],
        'mutex': ['mutex', 'mutual exclusion', 'std::mutex'],
        'lock': ['lock', 'locking', 'lock_guard', 'unique_lock'],
        'atomic': ['atomic', 'atomic operation', 'std::atomic'],
        'future': ['future', 'std::future', 'asynchronous'],
        'promise': ['promise', 'std::promise'],
        'async': ['async', 'std::async', 'asynchronous execution'],
        'condition_variable': ['condition_variable', 'condition variable', 'cv'],
        'semaphore': ['semaphore', 'counting semaphore'],
        'barrier': ['barrier', 'synchronization barrier'],
        'latch': ['latch', 'synchronization latch'],

        # Type Traits & SFINAE
        'enable_if': ['enable_if', 'std::enable_if', 'conditional compilation'],
        'void_t': ['void_t', 'std::void_t', 'detection idiom'],
        'declval': ['declval', 'std::declval', 'expression validity'],
        'is_same': ['is_same', 'std::is_same', 'type comparison'],
        'is_base_of': ['is_base_of', 'std::is_base_of', 'inheritance check'],
        'is_convertible': ['is_convertible', 'std::is_convertible', 'conversion check'],
        'remove_cv': ['remove_cv', 'std::remove_cv', 'type modification'],
        'add_const': ['add_const', 'std::add_const', 'type modification'],
        'decay': ['decay', 'std::decay', 'type decay'],

        # Containers
        'vector': ['vector', 'std::vector', 'dynamic array'],
        'array': ['array', 'std::array', 'fixed size array'],
        'list': ['list', 'std::list', 'doubly linked list'],
        'forward_list': ['forward_list', 'std::forward_list', 'singly linked list'],
        'deque': ['deque', 'std::deque', 'double ended queue', 'doubly ended queue', 'block vector'],
        'queue': ['queue', 'std::queue', 'fifo queue'],
        'stack': ['stack', 'std::stack', 'lifo stack'],
        'priority_queue': ['priority_queue', 'std::priority_queue', 'heap'],
        'set': ['set', 'std::set', 'ordered set'],
        'multiset': ['multiset', 'std::multiset', 'ordered multiset'],
        'unordered_set': ['unordered_set', 'std::unordered_set', 'hash set'],
        'map': ['map', 'std::map', 'ordered map', 'associative array'],
        'multimap': ['multimap', 'std::multimap', 'ordered multimap'],
        'unordered_map': ['unordered_map', 'std::unordered_map', 'hash map'],
        'unordered_multimap': ['unordered_multimap', 'std::unordered_multimap', 'hash multimap'],
        'bitset': ['bitset', 'std::bitset', 'bit array', 'bit vector'],

        # Algorithms
        'algorithm': [
            'algorithm', 'std algorithm', 'algorithms', 'sort', 'find', 'binary_search',
            'lower_bound', 'upper_bound', 'equal_range', 'transform', 'for_each',
            'accumulate', 'copy', 'move_algo', 'remove_if', 'count_if', 'copy_if',
            'any_of', 'all_of', 'none_of', 'fill', 'generate', 'replace', 'reverse'
        ],
        'sort': ['sort', 'std::sort', 'sorting'],
        'find': ['find', 'std::find', 'linear search'],
        'binary_search': ['binary_search', 'std::binary_search'],
        'lower_bound': ['lower_bound', 'std::lower_bound'],
        'upper_bound': ['upper_bound', 'std::upper_bound'],
        'equal_range': ['equal_range', 'std::equal_range'],
        'transform': ['transform', 'std::transform'],
        'for_each': ['for_each', 'std::for_each'],
        'accumulate': ['accumulate', 'std::accumulate', 'reduce'],
        'copy': ['copy', 'std::copy', 'copying'],
        'move_algo': ['move', 'std::move algorithm', 'move algorithm'],
        'remove_if': ['remove_if', 'std::remove_if', 'erase-remove idiom'],
        'remove_copy_if': ['remove_copy_if', 'std::remove_copy_if'],
        'count_if': ['count_if', 'std::count_if', 'counting elements'],
        'copy_if': ['copy_if', 'std::copy_if', 'conditional copy'],
        'any_of': ['any_of', 'std::any_of', 'any exist'],
        'all_of': ['all_of', 'std::all_of', 'all exist'],
        'none_of': ['none_of', 'std::none_of', 'none exist'],
        'fill': ['fill', 'std::fill', 'fill range'],
        'generate': ['generate', 'std::generate', 'generate range'],
        'replace': ['replace', 'std::replace', 'replace elements'],
        'reverse': ['reverse', 'std::reverse', 'reverse range'],

        # C++20 Features
        'span': ['span', 'std::span', 'view'],
        'string_view': ['string_view', 'std::string_view', 'non owning string'],
        'optional': ['optional', 'std::optional', 'maybe'],
        'variant': ['variant', 'std::variant', 'tagged union'],
        'any': ['any', 'std::any', 'type erasure'],
        'tuple': ['tuple', 'std::tuple', 'product type'],
        'pair': ['pair', 'std::pair', 'two element tuple'],
        'coroutine': ['coroutine', 'coroutines', 'co_await', 'co_yield', 'co_return'],
        'module': ['module', 'modules', 'import'],
        'ranges': ['ranges', 'std::ranges', 'range library'],
        'view': ['view', 'range view', 'std::views'],

        # C++ Library Features
        'iostream': ['iostream', 'input output stream', 'cin', 'cout', 'cerr'],
        'fstream': ['fstream', 'file stream', 'ifstream', 'ofstream'],
        'sstream': ['sstream', 'string stream', 'istringstream', 'ostringstream'],
        'regex': ['regex', 'regular expression', 'std::regex'],
        'chrono': ['chrono', 'time', 'duration', 'std::chrono'],
        'random': ['random', 'random number', 'std::random'],
        'filesystem': ['filesystem', 'file system', 'std::filesystem'],

        # C++ Compiler Features
        'inline': ['inline', 'inline function', 'inline expansion'],
        'static': ['static', 'static storage', 'static member'],
        'extern': ['extern', 'external linkage'],
        'mutable': ['mutable', 'mutable member'],
        'volatile': ['volatile', 'volatile qualifier'],
        'register': ['register', 'register storage'],
        'friend': ['friend', 'friend function', 'friend class'],
        'namespace': ['namespace', 'namespace scope'],
        'using': ['using', 'using declaration', 'using directive'],
        'typedef': ['typedef', 'type alias', 'type definition'],
        'const': ['const', 'const qualifier', 'constant'],
        'static_cast': ['static_cast', 'static casting'],
        'dynamic_cast': ['dynamic_cast', 'dynamic casting', 'runtime casting'],
        'const_cast': ['const_cast', 'const casting'],
        'reinterpret_cast': ['reinterpret_cast', 'reinterpret casting'],

        # Object-Oriented Programming
        'class': ['class', 'class definition', 'class declaration'],
        'struct': ['struct', 'structure', 'struct definition'],
        'union': ['union', 'union type', 'variant type'],
        'enum': ['enum', 'enumeration', 'enum class'],
        'public': ['public', 'public access', 'public member'],
        'private': ['private', 'private access', 'private member'],
        'protected': ['protected', 'protected access', 'protected member'],
        'virtual': ['virtual', 'virtual function', 'virtual inheritance'],
        'pure_virtual': ['pure virtual', 'abstract function', 'pure virtual function'],
        'constructor': ['constructor', 'ctor', 'object construction'],
        'destructor': ['destructor', 'dtor', 'object destruction'],
        'copy_constructor': ['copy constructor', 'copy ctor'],
        'move_constructor': ['move constructor', 'move ctor'],
        'copy_assignment': ['copy assignment', 'copy assignment operator'],
        'move_assignment': ['move assignment', 'move assignment operator'],

        # Templates Advanced
        'parameter_pack': ['parameter pack', 'variadic parameter', 'pack expansion'],
        'fold_expression': ['fold expression', 'fold', 'parameter pack fold'],
        'if_constexpr': ['if constexpr', 'constexpr if', 'conditional compilation'],
        'template_template': ['template template parameter', 'template template'],
        'dependent_name': ['dependent name', 'dependent type', 'template dependent'],
        'two_phase_lookup': ['two phase lookup', 'template lookup'],
        'tag_dispatching': ['tag dispatching', 'tag dispatch'],
        'expression_templates': ['expression templates', 'expression template'],
        'policy_based_design': ['policy based design', 'policy pattern'],

        # Low-level & System Programming
        'bit_manipulation': ['bit manipulation', 'bitwise operations', 'bit operations'],
        'bitfield': ['bitfield', 'bit field', 'packed structure'],
        'alignment': ['alignment', 'memory alignment', 'data alignment'],
        'padding': ['padding', 'structure padding', 'memory padding'],
        'endianness': ['endianness', 'byte order', 'little endian', 'big endian'],
        'cache_line': ['cache line', 'cache locality', 'cache coherence'],
        'branch_prediction': ['branch prediction', 'branch predictor'],
        'simd': ['simd', 'single instruction multiple data', 'vectorization'],
        'prefetch': ['prefetch', 'cache prefetch', 'memory prefetch'],

        # Error Handling & Debugging
        'assertion': ['assertion', 'assert', 'debug assertion'],
        'static_assert': ['static_assert', 'compile time assertion'],
        'debug': ['debug', 'debugging', 'debug mode'],
        'release': ['release', 'release mode', 'optimized build'],
        'sanitizer': ['sanitizer', 'address sanitizer', 'memory sanitizer'],
        'valgrind': ['valgrind', 'memory checker'],
        'gdb': ['gdb', 'gnu debugger', 'debugger'],
        'lldb': ['lldb', 'llvm debugger'],

        # Performance & Optimization
        'optimization': ['optimization', 'compiler optimization', 'performance'],
        'inlining': ['inlining', 'function inlining', 'inline optimization'],
        'loop_unrolling': ['loop unrolling', 'loop optimization'],
        'dead_code_elimination': ['dead code elimination', 'dce'],
        'constant_folding': ['constant folding', 'compile time evaluation'],
        'link_time_optimization': ['link time optimization', 'lto'],
        'profile_guided_optimization': ['profile guided optimization', 'pgo'],
        'cache_friendly': ['cache friendly', 'cache optimization'],
        'memory_locality': ['memory locality', 'spatial locality', 'temporal locality'],
        'branch_free': ['branch free', 'branchless programming'],

        # Build System & Tools
        'cmake': ['cmake', 'build system', 'makefile'],
        'makefile': ['makefile', 'make', 'build script'],
        'ninja': ['ninja', 'ninja build'],
        'compiler': ['compiler', 'gcc', 'clang', 'msvc'],
        'linker': ['linker', 'linking', 'link time'],
        'preprocessor': ['preprocessor', 'macro', 'preprocessing'],
        'macro': ['macro', 'preprocessor macro', 'define'],
        'header': ['header', 'header file', 'include'],
        'include_guard': ['include guard', 'header guard', 'pragma once'],
        'precompiled_header': ['precompiled header', 'pch'],

        # Testing & Quality
        'unit_test': ['unit test', 'testing', 'test framework'],
        'mock': ['mock', 'mocking', 'test double'],
        'fixture': ['fixture', 'test fixture'],
        'benchmark': ['benchmark', 'performance test', 'microbenchmark'],
        'coverage': ['coverage', 'code coverage', 'test coverage'],
        'static_analysis': ['static analysis', 'static checker'],
        'lint': ['lint', 'linter', 'code analysis'],
        'code_review': ['code review', 'peer review'],

        # Common synonyms and related terms
        'dynamic linking': ['dynamic linking', 'runtime linking', 'shared libraries'],
        'static linking': ['static linking', 'static libraries'],
        'memory management': ['memory management', 'allocation', 'deallocation', 'malloc', 'free', 'new', 'delete'],
        'pointers': ['pointers', 'pointer arithmetic', 'references', 'smart pointers'],
        'function pointers': ['function pointers', 'callbacks', 'function callbacks', 'functors'],
        'system calls': ['system calls', 'syscalls', 'kernel interface'],
        'process control': ['process control', 'fork', 'exec', 'process management'],
        'file operations': ['file operations', 'file io', 'file handling'],
        'error handling': ['error handling', 'exception handling', 'error management', 'exception'],
        'compilation': ['compilation', 'linking', 'build process', 'preprocessor'],
        'optimization': ['optimization', 'performance', 'efficiency', 'complexity'],
        'debugging': ['debugging', 'gdb', 'debugging tools'],
        'concurrency': ['concurrency', 'threading', 'parallel programming', 'multiple cores'],
        'synchronization': ['synchronization', 'mutex', 'semaphore', 'locks', 'conditional variable', 'system 5 semaphores', 'race conditions', 'deadlock', 'barrier', 'atomic'],
        'virtual memory': ['virtual memory', 'paging', 'memory mapping', 'page table', 'address translation', 'address space', 'mmap', 'TLB', 'MMU', 'page fault'],
        'cache': ['cache', 'caching', 'cpu cache'],
        'assembly': ['assembly', 'assembler', 'machine code'],
        'templates': ['templates', 'generic programming', 'metaprogramming'],
        'inheritance': ['inheritance', 'polymorphism', 'virtual functions'],
        'containers': [
            'containers', 'data structures', 'collection', 'STL',
            'vector', 'list', 'deque', 'array', 'forward_list',
            'map', 'set', 'multimap', 'multiset',
            'unordered_map', 'unordered_set', 'unordered_multimap', 'unordered_multiset', 'bitset',
            'stack', 'queue', 'priority_queue', 'iterator'
        ],
        'algorithms': ['algorithms', 'sorting', 'searching', 'complexity'],
        'networking': ['networking', 'sockets', 'tcp', 'udp'],
        'security': ['security', 'vulnerability'],
    }

    query_lower = query.lower().strip()
    search_terms = [query_lower]

    # Check for exact matches in expansions
    if query_lower in search_expansions:
        search_terms.extend(search_expansions[query_lower])

    # Check for partial matches (e.g., "global offset" should match "got")
    for key, expansions in search_expansions.items():
        if query_lower in key or key in query_lower:
            search_terms.extend(expansions)
        # Check if query matches any expansion
        for expansion in expansions:
            if query_lower in expansion or expansion in query_lower:
                search_terms.extend([key] + expansions)
                break

    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in search_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return unique_terms


@mcp.tool()
async def search_concepts(query: str, limit: int = 10) -> str:
    """Enhanced search for programming concepts with acronym and synonym support.

    Args:
        query: Search query (use '*' to list all concepts)
        limit: Maximum number of results to return (default: 10)
    """
    # Validate and preprocess the query
    processed_query, query_type = _validate_and_preprocess_query(query)
    search_terms = []  # Initialize for all code paths
    
    if query_type == "EMPTY":
        # Return most fundamental/popular concepts
        fundamental_concepts = [c for c in concepts if any(kw in c['title'].lower() 
                               for kw in ['pointer', 'function', 'variable', 'memory', 'array', 'malloc', 'free'])]
        matching_concepts = sorted(fundamental_concepts, key=lambda x: BOOK_AUTHORITY.get(x['book'], 1.0), reverse=True)[:limit]
    elif query_type == "INVALID":
        return "No concepts found - please use alphanumeric search terms"
    elif query_type == "NUMERIC":
        # Search for concepts that actually contain numbers in examples/code
        matching_concepts = [c for c in concepts if query in c.get('syntax', '') or query in c.get('content', '')][:limit]
    elif query_type == "WILDCARD":
        # Return all concepts
        matching_concepts = concepts[:limit]
    else:
        # Normal search with enhanced relevance
        search_terms = _expand_search_terms(processed_query)

        # Search concepts with enhanced term matching
        matching_concepts = []
        concept_scores = {}  # Track relevance scores

        for concept in concepts:
            base_score = 0
            concept_text_fields = [
                concept['title'].lower(),
                concept['description'].lower(),
                concept['content'].lower(),
                concept['book_title'].lower()
            ]

            # Add category match for new naming scheme
            if concept.get('category'):
                concept_text_fields.append(concept['category'].lower())

            # Calculate base relevance score based on term matches
            for term in search_terms:
                for i, field in enumerate(concept_text_fields):
                    if term in field:
                        # Weight: title=3, description=2.5, content=2, book=1.5, category=2
                        weights = [3, 2.5, 2, 1.5, 2]
                        weight = weights[i] if i < len(weights) else 1
                        base_score += weight

                        # Bonus for exact title match
                        if i == 0 and field == term:
                            base_score += 2

            # Apply enhanced relevance calculation
            if base_score > 0:
                enhanced_score = _calculate_enhanced_relevance(concept, search_terms, base_score)
                concept_scores[concept['id']] = enhanced_score
                matching_concepts.append(concept)

        # Sort by enhanced relevance score (highest first)
        matching_concepts.sort(key=lambda c: concept_scores.get(c['id'], 0), reverse=True)
        matching_concepts = matching_concepts[:limit]

    if not matching_concepts:
        # Show expanded search terms for debugging
        if len(search_terms) > 1:
            return f"No concepts found for query: '{query}'\nExpanded search terms: {', '.join(search_terms[:5])}{'...' if len(search_terms) > 5 else ''}"
        return f"No concepts found for query: '{query}'"

    # Format results with concept path information and search term info
    result_text = f"Found {len(matching_concepts)} programming concepts"
    if len(search_terms) > 1:
        result_text += f" (expanded from: {', '.join(search_terms[:3])}{'...' if len(search_terms) > 3 else ''})"
    result_text += ":\n\n"
    for i, concept in enumerate(matching_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        concept_path = f"{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
        if concept['description']:
            result_text += f"   {concept['description'][:100]}{'...' if len(concept['description']) > 100 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   Path: `{concept_path}`\n\n"

    return result_text


@mcp.tool()
async def search_by_book(book_name: str, query: str = "") -> str:
    """Search concepts within a specific book.

    Args:
        book_name: Name of the book to search in
        query: Search query within the book (optional, empty means show all concepts from book)
    """
    # Validate book name
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Invalid book name. Available books: {', '.join(available_books)}"

    # Filter concepts by book
    book_concepts = [c for c in concepts if c['book'] == book_name]

    if not book_concepts:
        return f"No concepts found for book: {books_metadata[book_name]}"

    # If query is provided, filter further
    if query:
        query_lower = query.lower()
        matching_concepts = []
        for concept in book_concepts:
            if (query_lower in concept['title'].lower() or
                    query_lower in concept['description'].lower() or
                    query_lower in concept['content'].lower()):
                matching_concepts.append(concept)
    else:
        matching_concepts = book_concepts

    if not matching_concepts:
        return f"No concepts found for query '{query}' in {books_metadata[book_name]}"

    # Format results
    result_text = f"Found {len(matching_concepts)} concepts in **{books_metadata[book_name]}**"
    if query:
        result_text += f" matching '{query}'"
    result_text += ":\n\n"

    for i, concept in enumerate(matching_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        concept_path = f"{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}**\n"
        if concept['description']:
            result_text += f"   {concept['description'][:150]}{'...' if len(concept['description']) > 150 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   Path: `{concept_path}`\n\n"

    return result_text


@mcp.tool()
async def search_by_category(category: str, book_name: str = None, limit: int = 10) -> str:
    """Search concepts by category using the new naming scheme.

    Args:
        category: Category to search for (e.g., 'func', 'mem', 'ptr', 'op', 'io', 'ctrl')
        book_name: Optional book name to filter by (e.g., 'cpp_primer', 'csapp_2016')
        limit: Maximum number of results to return (default: 10)
    """
    # Filter concepts by category and optionally by book
    matching_concepts = []
    search_pool = concepts
    
    # If book_name is specified, try fuzzy matching first
    matched_book = None
    if book_name:
        matched_book = _fuzzy_match_book_name(book_name)
        if not matched_book:
            available_books = sorted(set(c['book'] for c in concepts))
            available_titles = [f"'{book}' ({books_metadata.get(book, book)})" for book in available_books]
            return f"Could not find book matching '{book_name}'. Try one of:\n" + "\n".join([f"  • {title}" for title in available_titles[:8]]) + f"\n{'  • ...' if len(available_titles) > 8 else ''}"
        
        search_pool = [c for c in concepts if c['book'] == matched_book]
        if not search_pool:
            return f"No concepts found in book '{books_metadata.get(matched_book, matched_book)}'"
    
    for concept in search_pool:
        if concept.get('category') and concept['category'].lower() == category.lower():
            matching_concepts.append(concept)
            if len(matching_concepts) >= limit:
                break

    if not matching_concepts:
        # Show available categories from the search pool
        available_categories = set()
        for concept in search_pool:
            if concept.get('category'):
                available_categories.add(concept['category'])

        actual_book = matched_book or book_name
        book_context = f" in book '{books_metadata.get(actual_book, actual_book)}'" if actual_book else ""
        if available_categories:
            return f"No concepts found for category '{category}'{book_context}. Available categories{book_context}: {', '.join(sorted(available_categories))}"
        else:
            return f"No concepts found for category '{category}'{book_context}. No categories are currently indexed{book_context}."

    # Format results  
    actual_book = matched_book or book_name
    book_context = f" from **{books_metadata.get(actual_book, actual_book)}**" if actual_book else ""
    result_text = f"Found {len(matching_concepts)} concepts in category **{category}**{book_context}:\n\n"

    for i, concept in enumerate(matching_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        concept_path = f"{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
        if concept['description']:
            result_text += f"   {concept['description'][:150]}{'...' if len(concept['description']) > 150 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   Path: `{concept_path}`\n\n"

    return result_text




# ===============================
# ANALYSIS AND COMPARISON TOOLS
# ===============================

@mcp.tool()
async def compare_concepts(concept1_id: str, concept2_id: str) -> str:
    """Compare two concepts side-by-side.

    Args:
        concept1_id: ID of the first concept to compare
        concept2_id: ID of the second concept to compare
    """
    # FIXED: Use flexible ID matching
    concept1 = find_concept_by_id_flexible(concept1_id)
    concept2 = find_concept_by_id_flexible(concept2_id)

    if not concept1:
        return f"First concept not found: {concept1_id}\nAvailable IDs: {[c['id'][:50] + '...' for c in concepts[:5]]}"
    if not concept2:
        return f"Second concept not found: {concept2_id}\nAvailable IDs: {[c['id'][:50] + '...' for c in concepts[:5]]}"

    # Format comparison
    result_text = f"# Concept Comparison\n\n"

    # Basic info comparison
    result_text += f"## Overview\n"
    result_text += f"| Aspect | **{concept1['title']}** | **{concept2['title']}** |\n"
    result_text += f"|--------|-------------------------|-------------------------|\n"
    result_text += f"| Source | {concept1['book_title']} | {concept2['book_title']} |\n"
    result_text += f"| ID | `{concept1['id']}` | `{concept2['id']}` |\n\n"

    # Description comparison
    if concept1['description'] or concept2['description']:
        result_text += f"## Description Comparison\n\n"
        result_text += f"### {concept1['title']}\n"
        result_text += f"{concept1['description'] or 'No description available'}\n\n"
        result_text += f"### {concept2['title']}\n"
        result_text += f"{concept2['description'] or 'No description available'}\n\n"

    # Content comparison
    if concept1['content'] or concept2['content']:
        result_text += f"## Detailed Content Comparison\n\n"
        result_text += f"### {concept1['title']} Details\n"
        result_text += f"{concept1['content'][:500] if concept1['content'] else 'No detailed content available'}\n"
        if concept1['content'] and len(concept1['content']) > 500:
            result_text += "...\n"
        result_text += f"\n### {concept2['title']} Details\n"
        result_text += f"{concept2['content'][:500] if concept2['content'] else 'No detailed content available'}\n"
        if concept2['content'] and len(concept2['content']) > 500:
            result_text += "...\n"
        result_text += "\n"

    # Code comparison
    if concept1['syntax'] or concept2['syntax']:
        result_text += f"## Code Comparison\n\n"
        result_text += f"### {concept1['title']} Code\n"
        if concept1['syntax']:
            result_text += f"```c\n{concept1['syntax']}\n```\n\n"
        else:
            result_text += "No code example available\n\n"

        result_text += f"### {concept2['title']} Code\n"
        if concept2['syntax']:
            result_text += f"```c\n{concept2['syntax']}\n```\n\n"
        else:
            result_text += "No code example available\n\n"

    # Key differences
    result_text += f"## Key Observations\n"
    if concept1['book'] != concept2['book']:
        result_text += f"- **Different Sources**: {concept1['book_title']} vs {concept2['book_title']}\n"
    else:
        result_text += f"- **Same Source**: Both from {concept1['book_title']}\n"

    if concept1['syntax'] and concept2['syntax']:
        result_text += f"- **Both have code examples** - useful for practical comparison\n"
    elif concept1['syntax'] or concept2['syntax']:
        result_text += f"- **Only one has code example** - theoretical vs practical perspective\n"

    return result_text


@mcp.tool()
async def get_concept_details(concept_id: str) -> str:
    """Get detailed information about a specific concept.

    Args:
        concept_id: The ID of the concept to retrieve
    """
    # FIXED: Use flexible ID matching
    concept = find_concept_by_id_flexible(concept_id)

    if not concept:
        available_ids = [c['id'] for c in concepts[:10]]
        return f"Concept not found: {concept_id}\n\nAvailable concept IDs:\n" + "\n".join(
            [f"- {id}" for id in available_ids])

    # Format detailed response
    concept_uri_id = concept_to_clean_uri_id(concept)
    uri = f"concept://{concept['book']}/{concept_uri_id}"

    result_text = f"# {concept['title']}\n\n"
    result_text += f"**Source:** {concept['book_title']}\n"
    result_text += f"**ID:** `{concept['id']}`\n"
    result_text += f"**URI:** `{uri}`\n\n"

    if concept['description']:
        result_text += f"## Description\n{concept['description']}\n\n"

    if concept['content']:
        result_text += f"## Details\n{concept['content']}\n\n"

    if concept['syntax']:
        result_text += f"## Code Example\n```c\n{concept['syntax']}\n```\n\n"

    # Add any additional information from raw data
    raw_data = concept['raw_data']
    for key, value in raw_data.items():
        if key not in ['title', 'description', 'content', 'syntax', 'concept', 'summary', 'explanation',
                       'code'] and value:
            result_text += f"**{key.title()}:** {value}\n"

    return result_text


@mcp.tool()
async def debug_concept_ids(search_term: str = "") -> str:
    """Debug tool to see concept IDs and help with tool integration.

    Args:
        search_term: Optional search term to filter concepts
    """
    if search_term:
        matching_concepts = [c for c in concepts if
                             search_term.lower() in c['title'].lower() or search_term.lower() in c['id'].lower()]
    else:
        matching_concepts = concepts[:20]  # Show first 20

    result = f"📋 **Concept ID Debug Information**\n\n"
    result += f"Total concepts loaded: {len(concepts)}\n"
    if search_term:
        result += f"Filtering by: '{search_term}'\n"
    result += f"Showing: {len(matching_concepts)} concepts\n\n"

    for i, concept in enumerate(matching_concepts, 1):
        result += f"{i}. **{concept['title']}**\n"
        result += f"   ID: `{concept['id']}`\n"
        result += f"   Book: {concept['book']}\n"
        result += f"   Source file: {concept['source_file']}\n\n"

    return result


# ===============================
# LEARNING AND STUDY TOOLS
# ===============================

@mcp.tool()
async def generate_custom_tutorial(topic: str, skill_level: str = "intermediate") -> str:
    """
    ENHANCED: Generate comprehensive custom tutorial addressing review feedback:
    - Complete explanations (no truncation)
    - Concrete examples with tool outputs
    - Specific, actionable practice tasks
    - Explicit source attribution
    - Appropriate depth for skill level

    Args:
        topic: The topic for the tutorial (e.g., 'pointers', 'file operations', 'linking')
        skill_level: Target skill level - 'beginner', 'intermediate', or 'advanced'
    """
    topic_lower = topic.lower()
    skill_level_lower = skill_level.lower()

    if skill_level_lower not in ['beginner', 'intermediate', 'advanced']:
        return "Invalid skill level. Please choose 'beginner', 'intermediate', or 'advanced'."

    # Find and categorize concepts by complexity with better scoring
    beginner_concepts = []
    intermediate_concepts = []
    advanced_concepts = []

    for concept in concepts:
        if topic_lower in concept['title'].lower() or topic_lower in concept['description'].lower():
            # Enhanced categorization based on content complexity
            complexity_score = _calculate_concept_complexity(concept)

            if complexity_score <= 3 or concept['book'] == 'kernighan_ritchie':
                beginner_concepts.append((concept, complexity_score))
            elif complexity_score <= 6 or concept['book'] in ['unix_env', 'linkers_loaders']:
                intermediate_concepts.append((concept, complexity_score))
            else:  # Advanced concepts
                advanced_concepts.append((concept, complexity_score))

    # Sort by complexity score within each category
    beginner_concepts.sort(key=lambda x: x[1])
    intermediate_concepts.sort(key=lambda x: x[1])
    advanced_concepts.sort(key=lambda x: x[1])

    # Select concepts based on skill level with progressive difficulty
    if skill_level_lower == 'beginner':
        selected_tuples = beginner_concepts[:3] + intermediate_concepts[:2]
        estimated_duration = 45  # More realistic for beginners
    elif skill_level_lower == 'intermediate':
        selected_tuples = beginner_concepts[-1:] + intermediate_concepts[:3] + advanced_concepts[:2]
        estimated_duration = 60  # Deeper content
    else:  # advanced
        selected_tuples = intermediate_concepts[-2:] + advanced_concepts[:4]
        estimated_duration = 90  # Much more comprehensive

    selected_concepts = [concept for concept, _ in selected_tuples]

    if not selected_concepts:
        return f"No concepts found to create a tutorial on '{topic}'"

    # ENHANCEMENT 1: Complete source attribution
    source_books = list(set(concept['book_title'] for concept in selected_concepts))
    source_mapping = {}
    for concept in selected_concepts:
        book = concept['book_title']
        if book not in source_mapping:
            source_mapping[book] = []
        source_mapping[book].append(concept['title'])

    # Generate enhanced tutorial structure
    result_parts = [
        f"# 📚 Enhanced Tutorial: {topic.title()}\n\n",
        f"**Skill Level**: {skill_level.title()}\n",
        f"**Estimated Duration**: {estimated_duration} minutes\n",
        f"**Concepts Covered**: {len(selected_concepts)} lessons\n\n",
        "## 📖 Sources\n\n"
    ]

    # ENHANCEMENT 2: Explicit source attribution
    for book, concepts_list in source_mapping.items():
        result_parts.append(f"- **{book}**: {', '.join(concepts_list[:3])}")
        if len(concepts_list) > 3:
            result_parts.append(f" (and {len(concepts_list) - 3} more)")
        result_parts.append("\n")
    result_parts.append("\n")

    # ENHANCEMENT 3: Clear, comprehensive learning objectives
    result_parts.extend([
        "## 🎯 Learning Objectives\n\n",
        "By the end of this tutorial, you will:\n"
    ])

    if skill_level_lower == 'beginner':
        result_parts.extend([
            f"- Understand the fundamental concepts of {topic}\n",
            f"- Recognize common patterns and basic syntax\n",
            f"- Write simple, working code examples\n",
            f"- Identify when to use {topic} in your programs\n"
        ])
    elif skill_level_lower == 'intermediate':
        result_parts.extend([
            f"- Master practical applications of {topic}\n",
            f"- Understand system-level implications and performance considerations\n",
            f"- Implement robust solutions with proper error handling\n",
            f"- Debug common issues and optimize implementations\n"
        ])
    else:  # advanced
        result_parts.extend([
            f"- Master advanced techniques and optimization strategies for {topic}\n",
            f"- Understand deep system-level behavior and edge cases\n",
            f"- Implement high-performance, production-ready solutions\n",
            f"- Recognize and avoid subtle pitfalls and anti-patterns\n"
        ])

    result_parts.append("\n## 📖 Tutorial Content\n\n")

    # ENHANCEMENT 4: Progressive lessons with complete explanations
    for i, concept in enumerate(selected_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        uri = f"concept://{concept['book']}/{concept_uri_id}"

        result_parts.extend([
            f"### Lesson {i}: {concept['title']}\n\n",
            f"*Source: {concept['book_title']}*\n\n"
        ])

        # ENHANCEMENT 5: Complete concept explanation (no truncation)
        if concept['description']:
            result_parts.append(f"**Concept**: {concept['description']}\n\n")

        # ENHANCEMENT 6: Full detailed explanation
        if concept['content']:
            result_parts.append(f"**Detailed Explanation**:\n\n{concept['content']}\n\n")
        else:
            result_parts.append(f"**Detailed Explanation**: [See full concept for complete details]({uri})\n\n")

        # ENHANCEMENT 7: Enhanced code examples with context
        if concept['syntax']:
            result_parts.extend([
                "**Code Example**:\n\n",
                _generate_enhanced_code_example(concept, topic, skill_level_lower),
                "\n"
            ])

        # ENHANCEMENT 8: Specific, actionable practice tasks
        result_parts.extend([
            "**Practice Exercise**:\n\n",
            _generate_specific_practice_task(concept, topic, skill_level_lower, i),
            "\n"
        ])

        # ENHANCEMENT 9: Concrete tool demonstrations for advanced topics
        if skill_level_lower == 'advanced' and _has_system_level_content(concept):
            result_parts.extend([
                "**System Analysis**:\n\n",
                _generate_tool_demonstration(concept, topic),
                "\n"
            ])

        result_parts.extend([
            f"**Full Reference**: [Complete concept details]({uri})\n\n",
            "---\n\n"
        ])

    # ENHANCEMENT 10: Advanced summary and next steps
    result_parts.extend([
        "## 🎓 Summary & Next Steps\n\n",
        f"You've now covered {len(selected_concepts)} key concepts in {topic}. "
    ])

    if skill_level_lower == 'beginner':
        result_parts.extend([
            "Practice these fundamentals before moving to intermediate topics.\n\n",
            "**Recommended Next Topics**: ",
            ", ".join(_get_next_topics_beginner(topic))
        ])
    elif skill_level_lower == 'intermediate':
        result_parts.extend([
            "You're ready to tackle real-world applications and performance optimization.\n\n",
            "**Recommended Advanced Topics**: ",
            ", ".join(_get_next_topics_intermediate(topic))
        ])
    else:
        result_parts.extend([
            "You now have expert-level understanding. Consider contributing to open-source projects.\n\n",
            "**Expert-Level Challenges**: ",
            ", ".join(_get_expert_challenges(topic))
        ])

    result_parts.extend([
        "\n\n## 🔗 Cross-References\n\n",
        "Related tutorials you might find useful:\n"
    ])

    for book in source_books[:3]:
        result_parts.append(f"- Search `{book.split('(')[0].strip()}` for advanced {topic} topics\n")

    result_parts.extend([
        f"\n---\n*Tutorial generated from {len(source_books)} authoritative sources, ",
        f"covering {len(selected_concepts)} progressive concepts*"
    ])

    return ''.join(result_parts)


def _calculate_concept_complexity(concept: Dict) -> int:
    """Calculate complexity score (1-10) based on content characteristics"""
    score = 1

    # Book-based scoring
    book_scores = {
        'kernighan_ritchie': 2,
        'unix_env': 3,
        'linkers_loaders': 4,
        'os_three_pieces': 4,
        'expert_c_programming': 7,
        'csapp_2016': 5
    }
    score += book_scores.get(concept['book'], 5)

    # Content complexity indicators
    content = (concept.get('content', '') + concept.get('description', '')).lower()

    advanced_keywords = [
        'optimization', 'performance', 'kernel', 'assembly', 'register',
        'memory mapping', 'virtual memory', 'cache', 'pipeline', 'linker',
        'loader', 'relocation', 'symbol table', 'debugging', 'profiling', 'GOT', 'PLT'
        ,'mmu', 'compiler', 'low level'
    ]

    score += sum(1 for keyword in advanced_keywords if keyword in content)

    # Code complexity
    if concept.get('syntax'):
        code = concept['syntax']
        if len(code.split('\n')) > 10:
            score += 2
        if any(advanced in code.lower() for advanced in ['asm', 'volatile', 'inline', 'optimize']):
            score += 2

    return min(score, 10)


def _generate_enhanced_code_example(concept: Dict, topic: str, skill_level: str) -> str:
    """Generate enhanced code examples with context and annotations"""
    code = concept['syntax']

    if not code:
        return "```c\n/* No code example available for this concept */\n```\n"

    result = "```c\n"

    # Add contextual header based on skill level
    if skill_level == 'beginner':
        result += f"/* Basic {topic} example - {concept['title']} */\n"
        result += f"/* Focus: Understanding the fundamental syntax */\n\n"
    elif skill_level == 'intermediate':
        result += f"/* {topic} implementation - {concept['title']} */\n"
        result += f"/* Focus: Practical usage with error handling */\n\n"
    else:
        result += f"/* Advanced {topic} technique - {concept['title']} */\n"
        result += f"/* Focus: Optimization and edge case handling */\n\n"

    # Add the actual code
    lines = code.split('\n')
    for line in lines:
        result += f"{line}\n"

    # Add skill-appropriate annotations
    if skill_level == 'advanced' and len(lines) > 5:
        result += "\n/* Performance Notes:\n"
        result += f" * This implementation demonstrates {topic} concepts\n"
        result += " * Consider memory alignment and cache effects\n"
        result += " * Profile in production for optimal performance\n"
        result += " */\n"

    result += "```\n"
    return result


def _generate_specific_practice_task(concept: Dict, topic: str, skill_level: str, lesson_num: int) -> str:
    """Generate specific, actionable practice tasks instead of generic ones"""

    concept_name = concept['title'].lower()

    # Topic-specific practice tasks
    if 'linking' in topic.lower() or 'linker' in concept_name:
        if skill_level == 'beginner':
            return f"{lesson_num}. Create a simple program with two source files and compile them together.\n" \
                   f"   Use `gcc -c file1.c file2.c` then `gcc file1.o file2.o -o program`.\n" \
                   f"   Observe how the linker combines the object files."
        elif skill_level == 'intermediate':
            return f"{lesson_num}. Write a program that uses `libm` and link it incorrectly, then correctly.\n" \
                   f"   Try: `gcc program.c -lm` (wrong) vs `gcc program.c -o program -lm` (right).\n" \
                   f"   Document the error messages and explain why order matters."
        else:
            return f"{lesson_num}. Use `objdump -r` on an object file to examine relocation entries.\n" \
                   f"   Create a program with global variables and function calls.\n" \
                   f"   Analyze which symbols need relocation and why."

    elif 'memory' in topic.lower() or 'malloc' in concept_name:
        if skill_level == 'beginner':
            return f"{lesson_num}. Write a program that allocates an array with `malloc()` and frees it.\n" \
                   f"   Add `printf()` statements to track allocation and deallocation.\n" \
                   f"   What happens if you forget `free()`?"
        elif skill_level == 'intermediate':
            return f"{lesson_num}. Implement a simple memory pool allocator.\n" \
                   f"   Pre-allocate a large block and manage sub-allocations manually.\n" \
                   f"   Compare performance with standard `malloc()`."
        else:
            return f"{lesson_num}. Use `valgrind --tool=massif` to profile memory usage.\n" \
                   f"   Create a program with different allocation patterns.\n" \
                   f"   Analyze heap growth and identify optimization opportunities."

    elif 'process' in topic.lower() or 'fork' in concept_name:
        if skill_level == 'beginner':
            return f"{lesson_num}. Write a program that creates one child process with `fork()`.\n" \
                   f"   Have parent and child print different messages.\n" \
                   f"   Use `wait()` to ensure proper cleanup."
        elif skill_level == 'intermediate':
            return f"{lesson_num}. Create a producer-consumer program using `fork()` and pipes.\n" \
                   f"   Parent writes data to pipe, child reads and processes it.\n" \
                   f"   Handle pipe closure and error conditions."
        else:
            return f"{lesson_num}. Implement a process pool with `fork()` and signal handling.\n" \
                   f"   Create N worker processes, distribute tasks via IPC.\n" \
                   f"   Use `strace -f` to analyze system call patterns."

    else:
        # Generic but still specific tasks
        if skill_level == 'beginner':
            return f"{lesson_num}. Modify the code example to use different input values.\n" \
                   f"   Add error checking and print meaningful messages.\n" \
                   f"   Test with both valid and invalid inputs."
        elif skill_level == 'intermediate':
            return f"{lesson_num}. Extend the example to handle edge cases and error conditions.\n" \
                   f"   Add proper cleanup and resource management.\n" \
                   f"   Write a test harness to verify correctness."
        else:
            return f"{lesson_num}. Optimize the implementation for performance and memory efficiency.\n" \
                   f"   Profile with appropriate tools and document improvements.\n" \
                   f"   Consider thread safety and scalability issues."


def _has_system_level_content(concept: Dict) -> bool:
    """Check if concept involves system-level topics that benefit from tool demonstrations"""
    content = (concept.get('content', '') + concept.get('description', '') + concept.get('syntax', '')).lower()

    system_indicators = [
        'linker', 'loader', 'object file', 'symbol', 'relocation',
        'assembly', 'system call', 'kernel', 'memory map', 'virtual memory',
        'process', 'thread', 'signal', 'pipe', 'socket', 'user space', 'kernel space'
    ]

    return any(indicator in content for indicator in system_indicators)


def _generate_tool_demonstration(concept: Dict, topic: str) -> str:
    """Generate concrete tool usage examples for system-level concepts"""

    concept_content = concept.get('content', '').lower()

    if 'linker' in concept_content or 'symbol' in concept_content:
        return """**Tool Demo**: Examining symbols with `nm`
```bash
# Compile object file
gcc -c program.c

# List all symbols
nm program.o

# Find specific symbols (undefined references)
nm program.o | grep -E "U|T"

# Check symbols in library
nm /lib/x86_64-linux-gnu/libc.so.6 | grep malloc
```
**Expected Output**: You'll see symbol types (T=text, U=undefined, D=data)"""

    elif 'memory' in concept_content or 'malloc' in concept_content:
        return """**Tool Demo**: Memory analysis with `pmap` and `valgrind`
```bash
# Compile with debug info
gcc -g -o program program.c

# Run and get PID
./program &
PROGRAM_PID=$!

# Examine memory mapping
pmap $PROGRAM_PID

# Check for memory leaks
valgrind --leak-check=full ./program
```
**Expected Output**: Memory layout showing heap, stack, and shared libraries"""

    elif 'process' in concept_content or 'fork' in concept_content:
        return """**Tool Demo**: Process tracing with `strace`
```bash
# Trace system calls
strace -f ./program

# Focus on specific calls
strace -e trace=fork,exec,wait ./program

# Trace with timestamps
strace -t -o trace.log ./program
```
**Expected Output**: Sequence of system calls showing process creation and management"""

    else:
        return """**Tool Demo**: General debugging approach
```bash
# Compile with all warnings and debug info
gcc -Wall -Wextra -g -o program program.c

# Use gdb for debugging
gdb ./program
(gdb) break main
(gdb) run
(gdb) info variables
```
**Expected Output**: Detailed debugging information and variable states"""


def _get_next_topics_beginner(topic: str) -> List[str]:
    """Suggest next topics for beginner level"""
    next_topics = {
        'pointers': ['arrays', 'strings', 'dynamic memory'],
        'functions': ['pointers', 'structures', 'file I/O'],
        'memory': ['pointers', 'data structures', 'debugging'],
        'linking': ['compilation process', 'libraries', 'makefiles'],
        'processes': ['signals', 'file I/O', 'inter-process communication']
    }

    for key in next_topics:
        if key in topic.lower():
            return next_topics[key]

    return ['advanced syntax', 'data structures', 'system programming']


def _get_next_topics_intermediate(topic: str) -> List[str]:
    """Suggest advanced topics for intermediate level"""
    next_topics = {
        'pointers': ['function pointers', 'complex data structures', 'memory optimization'],
        'memory': ['virtual memory', 'memory mapping', 'cache optimization'],
        'linking': ['dynamic loading', 'plugin architectures', 'binary analysis'],
        'processes': ['thread programming', 'synchronization', 'performance optimization']
    }

    for key in next_topics:
        if key in topic.lower():
            return next_topics[key]

    return ['system internals', 'performance optimization', 'concurrent programming']


def _get_expert_challenges(topic: str) -> List[str]:
    """Suggest expert-level challenges"""
    challenges = {
        'linking': ['Write a custom dynamic loader', 'Implement position-independent code',
                    'Binary patching techniques'],
        'memory': ['Custom memory allocators', 'Lock-free data structures', 'NUMA optimization'],
        'processes': ['High-performance servers', 'Real-time systems', 'Kernel modules']
    }

    for key in challenges:
        if key in topic.lower():
            return challenges[key]

    return ['Contribute to open-source projects', 'Write performance-critical libraries', 'Develop system tools']





# Initialize the concepts database when the module loads
build_concept_index()
load_posix_concepts()
logger.info("Programming Concepts MCP Server initialized with efficient duplicate cleanup")

if __name__ == "__main__":
    # Run the FastMCP server
    logger.info("Starting Programming Concepts MCP Server for Claude Code...")
    logger.info("MCP Server ready for Claude Code with efficient duplicate cleanup functionality")
    mcp.run(transport='stdio')
