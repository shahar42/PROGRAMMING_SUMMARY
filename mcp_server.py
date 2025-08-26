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
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict
import re
from typing import List, Tuple, Dict

# Add current directory to Python path
sys.path.append('.')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("programming-concepts-mcp")

# Initialize FastMCP server
mcp = FastMCP("programming-concepts")

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
    "cpp_knowledge": "C++ Knowledge Base (High Priority Concepts)",
    "Inside_the_C++_Object_Model": "Inside the C++ Object Model (Stanley Lippman)"
}


def build_concept_index():
    """Build the concept index from outputs directory."""
    global concepts

    logger.info("Building concept index from outputs")

    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    outputs_dir = PROJECT_ROOT / "outputs"
    if not outputs_dir.exists():
        logger.error("outputs directory not found")
        return

    total_concepts = 0

    for book_dir in outputs_dir.iterdir():
        if not book_dir.is_dir():
            continue

        book_name = book_dir.name
        if book_name not in books_metadata:
            continue

        logger.info(f"Indexing book: {book_name}")

        # Look for JSON files containing concepts - support both old and new naming
        concept_files = list(book_dir.glob("*.json"))
        # Filter to only concept files, exclude metadata files
        concept_files = [f for f in concept_files
                         if f.name not in ["progress.json", "metadata.json", "summary.json"]
                         and not f.name.endswith("_summary.md")
                         and f.suffix == ".json"]
        book_concepts = 0

        for concept_file in concept_files:

            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept_data = json.load(f)

                # Handle both single concept and list of concepts
                if isinstance(concept_data, list):
                    for concept in concept_data:
                        add_concept(concept, book_name, concept_file.name)
                        book_concepts += 1
                elif isinstance(concept_data, dict):
                    add_concept(concept_data, book_name, concept_file.name)
                    book_concepts += 1

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {concept_file}: {e}")
                continue

        if book_concepts > 0:
            logger.info(f"Found {book_concepts} concepts in {book_name}")
            total_concepts += book_concepts

    logger.info(
        f"Successfully indexed {total_concepts} concepts across {len([k for k in books_metadata.keys() if any(Path('outputs').glob(f'{k}/*.json'))])} books")


def add_concept(concept_data: Dict[str, Any], book_name: str, filename: str):
    """Add a concept to the index with proper field mapping and CLEAN ID generation."""
    global concepts

    # Extract category from new naming scheme if available
    category = extract_category_from_filename(filename)

    # Generate clean, predictable IDs for both old and new naming schemes
    concept_num_match = re.search(r'concept_(\d+)', filename)
    if concept_num_match:
        # Old naming scheme
        concept_num = concept_num_match.group(1).zfill(3)  # Pad to 3 digits
        concept_id = f"{book_name}_concept_{concept_num}"
    else:
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

    # Try partial matches for backward compatibility
    concept_id_lower = concept_id.lower()
    for concept in concepts:
        if concept_id_lower in concept['id'].lower():
            return concept
        # Also try matching without book prefix
        if concept_id_lower.replace(concept['book'] + '_', '') in concept['id'].lower():
            return concept

    return None


def normalize_concept_id(raw_id: str) -> str:
    """Normalize concept ID to clean format"""
    # Extract book name and concept number
    parts = raw_id.split('_')
    if len(parts) >= 3 and 'concept' in parts:
        book_name = parts[0]
        concept_idx = parts.index('concept')
        if concept_idx + 1 < len(parts):
            concept_num = parts[concept_idx + 1]
            if concept_num.isdigit():
                return f"{book_name}_concept_{concept_num.zfill(3)}"

    return raw_id


def format_parameters(parameters):
    """Format parameter list for display"""
    if not parameters:
        return ""

    formatted = []
    for param in parameters:
        name = param.get('name', 'unknown')
        param_type = param.get('type', 'unknown')
        desc = param.get('description', 'No description')
        formatted.append(f"- **{name}** ({param_type}): {desc}")

    return "\n".join(formatted)


def format_errors(errors):
    """Format error list for display"""
    if not errors:
        return ""

    formatted = []
    for error in errors:
        code = error.get('code', 'UNKNOWN')
        desc = error.get('description', 'No description')
        formatted.append(f"- **{code}**: {desc}")

    return "\n".join(formatted)


def load_posix_concepts():
    """Load POSIX syscalls as concepts"""
    posix_dir = Path("/home/shahar42/Suumerizing_C_holy_grale_book/outputs/posix_manpages")

    if not posix_dir.exists():
        return

    for json_file in posix_dir.glob("unix_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                syscall = json.load(f)

            # Format as concept
            concept_data = {
                'topic': f"{syscall['name']}() - POSIX System Call",
                'explanation': syscall['description'],
                'syntax': '\n'.join(syscall['synopsis']),
                'content': f"Parameters:\n{format_parameters(syscall.get('parameters', []))}\n\nErrors:\n{format_errors(syscall.get('errors', []))}"
            }

            add_concept(concept_data, 'posix_manpages', json_file.name)

        except Exception as e:
            logger.warning(f"Error loading POSIX concept {json_file}: {e}")


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
    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
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

    result = f"# 📊 Duplicate Analysis for {books_metadata[book_name]}\n\n"
    result += f"**Files Analyzed:** {len(concept_files)}\n"
    result += f"**Similarity Threshold:** {similarity_threshold:.0%}\n\n"

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

    result += f"## Summary\n\n"
    result += f"- **Total similar pairs found:** {len(similar_pairs)}\n"
    result += f"- **Pairs above duplicate threshold:** {len(duplicates)}\n"
    result += f"- **Estimated files that could be removed:** {len(duplicates)}\n\n"

    if duplicates:
        result += f"## 🚨 Potential Duplicates (≥{similarity_threshold:.0%} similar)\n\n"
        for i, pair in enumerate(duplicates[:10], 1):  # Show top 10
            result += f"### {i}. Similarity: {pair['similarity']:.1%}\n"
            result += f"**File 1:** `{pair['concept1']['file_name']}`\n"
            result += f"Topic: {pair['concept1']['data'].get('topic', 'Unknown')}\n\n"
            result += f"**File 2:** `{pair['concept2']['file_name']}`\n"
            result += f"Topic: {pair['concept2']['data'].get('topic', 'Unknown')}\n\n"

        if len(duplicates) > 10:
            result += f"*...and {len(duplicates) - 10} more duplicate pairs*\n\n"

    if len(similar_pairs) > len(duplicates):
        result += f"## 📋 Other Similar Pairs ({similarity_threshold - 0.1:.0%}-{similarity_threshold:.0%} similar)\n\n"
        similar_not_dup = [p for p in similar_pairs if not p['is_duplicate']][:5]

        for i, pair in enumerate(similar_not_dup, 1):
            result += f"{i}. **{pair['similarity']:.1%}** - `{pair['concept1']['file_name']}` vs `{pair['concept2']['file_name']}`\n"

    result += f"\n## 💡 Recommendations\n\n"

    if duplicates:
        result += f"- Run `cleanup_duplicate_concepts('{book_name}', {similarity_threshold}, True)` for a dry run\n"
        result += f"- Run `cleanup_duplicate_concepts('{book_name}', {similarity_threshold}, False)` to perform cleanup\n"
        result += f"- Consider adjusting threshold if too many/few duplicates detected\n"
    else:
        result += f"- ✅ No duplicates found at {similarity_threshold:.0%} threshold\n"
        result += f"- Consider lowering threshold (e.g., 0.80) if you want more aggressive deduplication\n"

    return result


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
    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
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
        result += f"⚠️ **Warning:** {failed_loads} files could not be loaded\n\n"

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
        result += "✅ **No duplicates found!** All concepts appear to be unique.\n"
        return result

    result += f"🔍 **Found {len(duplicate_groups)} duplicate groups:**\n\n"

    files_to_delete = []
    files_kept = []
    backup_dir = None

    if not dry_run:
        # Create backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = book_dir / f"cleanup_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

    for group_num, group in enumerate(duplicate_groups, 1):
        result += f"### Group {group_num}: {len(group)} similar concepts\n\n"

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
            result += f"- {status}: `{concept['file_name']}`{similarity_text}\n"
            result += f"  Topic: {concept['data'].get('topic', 'Unknown')[:60]}...\n"

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

        result += "\n"

    # Summary
    result += "## 📊 Cleanup Summary\n\n"
    result += f"- **Duplicate groups found:** {len(duplicate_groups)}\n"
    result += f"- **Files to delete:** {len(files_to_delete)}\n"
    result += f"- **Files kept:** {len(files_kept)}\n"

    if not dry_run:
        result += f"- **Backup location:** `{backup_dir}`\n"
        result += f"- **Files deleted:** {len(files_to_delete)}\n"
        result += "\n✅ **Cleanup completed successfully!**\n"
        result += "\n💡 **Note:** Deleted files are backed up and can be restored if needed.\n"
    else:
        result += "\n⚠️ **This was a dry run** - no files were actually deleted.\n"
        result += "\nRun `cleanup_duplicate_concepts('{}', {}, False)` to perform actual cleanup.".format(book_name,
                                                                                                          similarity_threshold)

    return result


# ===============================
# CONCEPT ACCESS TOOLS
# ===============================

@mcp.tool()
async def read_concept_resource(book_name: str, concept_id: str) -> str:
    """
    Read a specific concept as a resource-like tool

    Args:
        book_name: Name of the book (e.g., 'os_three_pieces')
        concept_id: Clean concept identifier

    Returns:
        Formatted concept content
    """
    # Validate book exists
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Error: Book '{book_name}' not found. Available books: {', '.join(available_books)}"

    # Find the concept
    concept = find_concept_by_uri_id(book_name, concept_id)

    if not concept:
        # List available concepts for debugging
        available_concepts = []
        for c in concepts:
            if c['book'] == book_name:
                available_concepts.append(concept_to_clean_uri_id(c))

        return f"Error: Concept '{concept_id}' not found in {book_name}. Available concepts: {', '.join(available_concepts[:5])}..."

    # Format the concept content
    result = f"# {concept['title']}\n\n"
    result += f"**Source:** {concept['book_title']}\n\n"

    if concept['description']:
        result += f"## Description\n{concept['description']}\n\n"

    if concept['content']:
        result += f"## Details\n{concept['content']}\n\n"

    if concept['syntax']:
        result += f"## Code Example\n```c\n{concept['syntax']}\n```\n\n"

    # Add any additional information from raw data
    raw_data = concept['raw_data']
    for key, value in raw_data.items():
        if key not in ['title', 'description', 'content', 'syntax', 'concept', 'summary', 'explanation',
                       'code'] and value:
            result += f"**{key.title()}:** {value}\n"

    return result


@mcp.tool()
async def list_concept_uris() -> str:
    """List all available concept URIs"""

    result = "## Available Concept URIs\n\n"

    by_book = {}
    for concept in concepts:
        book_name = concept['book']
        if book_name not in by_book:
            by_book[book_name] = []

        concept_id = concept_to_clean_uri_id(concept)
        uri = f"concept://{book_name}/{concept_id}"
        by_book[book_name].append((concept['title'], uri))

    for book_name, book_concepts in by_book.items():
        result += f"### {books_metadata[book_name]}\n\n"
        for title, uri in book_concepts[:10]:  # Show first 10 per book
            result += f"- **{title}**: `{uri}`\n"
        if len(book_concepts) > 10:
            result += f"- ... and {len(book_concepts) - 10} more concepts\n"
        result += "\n"

    result += f"\n**Total:** {len(concepts)} concepts across {len(by_book)} books\n"
    result += f"\n**Usage:** Use `read_concept_resource(book_name, concept_id)` to access specific concepts"

    return result


# ===============================
# SEARCH AND DISCOVERY TOOLS
# ===============================

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
        'deque': ['deque', 'std::deque', 'double ended queue'],
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

        # Algorithms
        'algorithm': ['algorithm', 'std algorithm', 'algorithms'],
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
        'memory management': ['memory management', 'allocation', 'deallocation', 'malloc', 'free'],
        'pointers': ['pointers', 'pointer arithmetic', 'references'],
        'function pointers': ['function pointers', 'callbacks', 'function callbacks'],
        'system calls': ['system calls', 'syscalls', 'kernel interface'],
        'process control': ['process control', 'fork', 'exec', 'process management'],
        'file operations': ['file operations', 'file io', 'file handling'],
        'error handling': ['error handling', 'exception handling', 'error management'],
        'compilation': ['compilation', 'linking', 'build process'],
        'optimization': ['optimization', 'performance', 'efficiency'],
        'debugging': ['debugging', 'gdb', 'debugging tools'],
        'concurrency': ['concurrency', 'threading', 'parallel programming'],
        'synchronization': ['synchronization', 'mutex', 'semaphore', 'locks'],
        'virtual memory': ['virtual memory', 'paging', 'memory mapping'],
        'cache': ['cache', 'caching', 'cpu cache'],
        'assembly': ['assembly', 'assembler', 'machine code'],
        'templates': ['templates', 'generic programming', 'metaprogramming'],
        'inheritance': ['inheritance', 'polymorphism', 'virtual functions'],
        'containers': ['containers', 'data structures', 'vector', 'list', 'map'],
        'algorithms': ['algorithms', 'sorting', 'searching', 'complexity'],
        'networking': ['networking', 'sockets', 'tcp', 'udp'],
        'security': ['security', 'buffer overflow', 'vulnerability'],
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
    query_lower = query.lower()

    if query == "*":
        # Return all concepts
        matching_concepts = concepts[:limit]
    else:
        # Expand search terms with acronyms and synonyms
        search_terms = _expand_search_terms(query)

        # Search concepts with enhanced term matching
        matching_concepts = []
        concept_scores = {}  # Track relevance scores

        for concept in concepts:
            relevance_score = 0
            concept_text_fields = [
                concept['title'].lower(),
                concept['description'].lower(),
                concept['content'].lower(),
                concept['book_title'].lower()
            ]

            # Add category match for new naming scheme
            if concept.get('category'):
                concept_text_fields.append(concept['category'].lower())

            # Calculate relevance score based on term matches
            for term in search_terms:
                for i, field in enumerate(concept_text_fields):
                    if term in field:
                        # Weight: title=3, description=2, content=1, book=0.5, category=2
                        weights = [3, 2, 1, 0.5, 2]
                        weight = weights[i] if i < len(weights) else 1
                        relevance_score += weight

                        # Bonus for exact title match
                        if i == 0 and field == term:
                            relevance_score += 2

            if relevance_score > 0:
                concept_scores[id(concept)] = relevance_score
                matching_concepts.append(concept)

        # Sort by relevance score (highest first)
        matching_concepts.sort(key=lambda c: concept_scores.get(id(c), 0), reverse=True)
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
async def search_by_category(category: str, limit: int = 10) -> str:
    """Search concepts by category using the new naming scheme.

    Args:
        category: Category to search for (e.g., 'func', 'mem', 'ptr', 'op', 'io', 'ctrl')
        limit: Maximum number of results to return (default: 10)
    """
    # Filter concepts by category
    matching_concepts = []
    for concept in concepts:
        if concept.get('category') and concept['category'].lower() == category.lower():
            matching_concepts.append(concept)
            if len(matching_concepts) >= limit:
                break

    if not matching_concepts:
        # Show available categories
        available_categories = set()
        for concept in concepts:
            if concept.get('category'):
                available_categories.add(concept['category'])

        if available_categories:
            return f"No concepts found for category '{category}'. Available categories: {', '.join(sorted(available_categories))}"
        else:
            return f"No concepts found for category '{category}'. No categories are currently indexed."

    # Format results
    result_text = f"Found {len(matching_concepts)} concepts in category **{category}**:\n\n"

    for i, concept in enumerate(matching_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        concept_path = f"{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
        if concept['description']:
            result_text += f"   {concept['description'][:150]}{'...' if len(concept['description']) > 150 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   Path: `{concept_path}`\n\n"

    return result_text


@mcp.tool()
async def find_advanced_concepts(topic: str, threshold: int = 2) -> str:
    """Finds advanced concepts related to a specific topic.

    Args:
        topic: The general programming topic to search for (e.g., 'memory', 'linking').
        threshold: A score (default: 2) a concept must meet to be considered "advanced".
    """
    # Define heuristics for what makes a concept "advanced"
    ADVANCED_KEYWORDS = [
        'advanced', 'internals', 'optimization', 'low-level', 'kernel', 'complex',
        'performance', 'architecture', 'concurrent', 'asynchronous', 'memory layout',
        'virtual memory', 'system call', 'linking', 'loading', 'multithreading',
        'synchronization', 'parallelism', 'cache coherence', 'memory alignment',
        'interrupts', 'scheduling', 'file systems', 'network stack', 'garbage collection',
        'instruction pipelining', 'branch prediction', 'memory paging', 'context switching',
        'atomic operations', 'lock-free programming', 'syscalls',
        'dynamic linking', 'static analysis',
        'memory fences', 'thread affinity', 'heap management', 'GOT', 'TLB',
        'page table', 'segment'
    ]
    BOOK_WEIGHTS = {
        "linkers_loaders": 3,
        "expert_c_programming": 3,
        "csapp_2016": 3,
        "unix_env": 2,
        "os_three_pieces": 2,
        "kernighan_ritchie": 0
    }

    # Search for concepts matching the topic and calculate their "advanced score"
    advanced_matches = []
    topic_lower = topic.lower()

    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()

        # First, ensure the concept is relevant to the topic at all
        if topic_lower not in concept_text:
            continue

        # Calculate the advanced score
        advanced_score = 0
        # Add points for being from an advanced book
        advanced_score += BOOK_WEIGHTS.get(concept['book'], 0)
        # Add points for each advanced keyword found
        for keyword in ADVANCED_KEYWORDS:
            if keyword in concept_text:
                advanced_score += 1

        # Only include concepts that meet our threshold
        if advanced_score >= threshold:
            advanced_matches.append({'concept': concept, 'score': advanced_score})

    if not advanced_matches:
        return f"No advanced concepts found for topic '{topic}' with threshold {threshold}. Try a lower threshold or broader topic."

    # Sort results to show the "most advanced" first
    advanced_matches.sort(key=lambda x: x['score'], reverse=True)

    result_text = f"Found {len(advanced_matches)} advanced concepts for '{topic}' (Threshold: {threshold}):\n\n"
    for i, match in enumerate(advanced_matches, 1):
        concept = match['concept']
        concept_uri_id = concept_to_clean_uri_id(concept)
        concept_path = f"{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}** (From: {concept['book_title']})\n"
        result_text += f"   *Advanced Score: {match['score']}*\n"
        result_text += f"   {concept['description'][:100]}{'...' if len(concept['description']) > 100 else ''}\n"
        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   Path: `{concept_path}`\n\n"

    return result_text


@mcp.tool()
async def find_code_examples(pattern: str = "") -> str:
    """Find all concepts that contain actual code examples.

    Args:
        pattern: Optional pattern to search within code examples (e.g. 'malloc', 'file', 'fork')
    """
    code_concepts = []
    pattern_lower = pattern.lower() if pattern else ""

    for concept in concepts:
        # Check if concept has code/syntax
        has_code = (concept['syntax'] and concept['syntax'].strip()) or \
                   (concept['raw_data'].get('code') and concept['raw_data']['code'].strip()) or \
                   (concept['raw_data'].get('example') and concept['raw_data']['example'].strip())

        if has_code:
            # If pattern specified, check if it matches
            if pattern:
                code_text = (concept['syntax'] + " " +
                             str(concept['raw_data'].get('code', '')) + " " +
                             str(concept['raw_data'].get('example', ''))).lower()
                if pattern_lower in code_text:
                    code_concepts.append(concept)
            else:
                code_concepts.append(concept)

    if not code_concepts:
        if pattern:
            return f"No code examples found matching pattern: '{pattern}'"
        else:
            return "No code examples found in the knowledge base"

    # Format results
    result_text = f"Found {len(code_concepts)} concepts with code examples"
    if pattern:
        result_text += f" matching '{pattern}'"
    result_text += ":\n\n"

    for i, concept in enumerate(code_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        uri = f"concept://{concept['book']}/{concept_uri_id}"

        result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"

        # Show code preview
        code_sample = concept['syntax'] or concept['raw_data'].get('code', '') or concept['raw_data'].get('example', '')
        if code_sample:
            # Show first few lines of code
            code_lines = code_sample.strip().split('\n')[:3]
            preview = '\n'.join(code_lines)
            if len(code_sample.split('\n')) > 3:
                preview += "\n   ..."
            result_text += f"   ```c\n   {preview}\n   ```\n"

        result_text += f"   ID: `{concept['id']}`\n"
        result_text += f"   URI: `{uri}`\n\n"

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
async def explain_my_code(code_snippet: str, language: str = "C") -> str:
    """Analyze code using concepts from your knowledge base.

    Args:
        code_snippet: The code to analyze
        language: Programming language (default: C)
    """
    code_lower = code_snippet.lower()

    # Extract keywords/patterns from code
    code_keywords = []

    # Common C patterns to look for
    c_patterns = {
        'malloc': ['malloc', 'memory allocation', 'heap'],
        'free': ['free', 'memory deallocation'],
        'pointer': ['*', 'pointer', 'address'],
        'array': ['[', ']', 'array', 'index'],
        'function': ['(', ')', 'function', 'call'],
        'struct': ['struct', 'structure'],
        'file': ['fopen', 'fclose', 'fread', 'fwrite', 'file'],
        'process': ['fork', 'exec', 'wait', 'process'],
        'signal': ['signal', 'kill', 'sigaction'],
        'thread': ['pthread', 'thread', 'mutex'],
        'string': ['strcpy', 'strlen', 'strcmp', 'string'],
        'stdio': ['printf', 'scanf', 'fprintf', 'input', 'output']
    }

    # Identify relevant concepts based on code content
    for keyword, patterns in c_patterns.items():
        if any(pattern in code_lower for pattern in patterns):
            code_keywords.append(keyword)

    # Find concepts that match the identified keywords
    relevant_concepts = []
    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()
        relevance_score = sum(1 for keyword in code_keywords if keyword in concept_text)

        # Also check if concept has similar code patterns
        if concept['syntax']:
            syntax_lower = concept['syntax'].lower()
            code_similarity = sum(1 for line in code_snippet.split('\n')
                                  if any(word in syntax_lower for word in line.split() if len(word) > 2))
            relevance_score += code_similarity * 0.5

        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))

    if not relevant_concepts:
        return f"No relevant concepts found for this {language} code. The code might use patterns not covered in the knowledge base."

    # Sort by relevance
    relevant_concepts.sort(key=lambda x: x[1], reverse=True)

    # Format analysis
    result_text = f"# Code Analysis: {language}\n\n"
    result_text += f"## Your Code\n```{language.lower()}\n{code_snippet}\n```\n\n"

    result_text += f"## Analysis Using Knowledge Base\n\n"
    result_text += f"Identified {len(code_keywords)} key patterns: {', '.join(code_keywords)}\n\n"

    # Show most relevant concepts
    top_concepts = relevant_concepts[:5]
    result_text += f"### 🔍 Relevant Concepts ({len(top_concepts)} found)\n\n"

    for i, (concept, score) in enumerate(top_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        uri = f"concept://{concept['book']}/{concept_uri_id}"

        result_text += f"**{i}. {concept['title']}** ({concept['book_title']})\n"
        result_text += f"   {concept['description'][:150] if concept['description'] else 'No description'}{'...' if len(concept.get('description', '')) > 150 else ''}\n"

        # Show relevant code if available
        if concept['syntax'] and any(keyword in concept['syntax'].lower() for keyword in code_keywords):
            code_preview = concept['syntax'].strip().split('\n')[:2]
            result_text += f"   ```c\n   {chr(10).join(code_preview)}\n   ```\n"

        result_text += f"   ID: `{concept['id']}` | Relevance: {score:.1f}\n"
        result_text += f"   URI: `{uri}`\n\n"

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
async def generate_study_path(goal: str) -> str:
    """Create ordered learning sequence for a programming goal.

    Args:
        goal: Learning goal (e.g. 'system programming', 'memory management', 'file I/O', 'C basics')
    """
    goal_lower = goal.lower()

    # Define study paths based on common goals
    study_paths = {
        'c basics': ['basic', 'variable', 'function', 'array', 'pointer', 'string'],
        'memory management': ['pointer', 'malloc', 'free', 'memory', 'heap', 'stack'],
        'file io': ['file', 'open', 'read', 'write', 'close', 'stream'],
        'system programming': ['process', 'fork', 'exec', 'signal', 'pipe', 'thread'],
        'unix programming': ['unix', 'system call', 'process', 'signal', 'file descriptor'],
        'debugging': ['debug', 'error', 'gdb', 'valgrind', 'trace'],
        'compilation': ['compile', 'link', 'library', 'object', 'makefile'],
        'data structures': ['struct', 'array', 'list', 'tree', 'hash']
    }

    # Find matching keywords for the goal
    relevant_keywords = []
    for path_name, keywords in study_paths.items():
        if any(keyword in goal_lower for keyword in path_name.split()):
            relevant_keywords.extend(keywords)
            break

    # If no specific path found, extract keywords from goal
    if not relevant_keywords:
        relevant_keywords = goal_lower.split()

    # Find concepts matching the keywords
    relevant_concepts = []
    for concept in concepts:
        concept_text = (concept['title'] + ' ' + concept['description'] + ' ' + concept['content']).lower()
        relevance_score = sum(1 for keyword in relevant_keywords if keyword in concept_text)

        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))

    if not relevant_concepts:
        return f"No concepts found for learning goal: '{goal}'"

    # Sort by relevance and book authority
    book_priority = {'kernighan_ritchie': 4, 'unix_env': 3, 'os_three_pieces': 2, 'linkers_loaders': 1, 'csapp_2016': 3,
                     'cpp_knowledge': 5}
    relevant_concepts.sort(key=lambda x: (x[1], book_priority.get(x[0]['book'], 0)), reverse=True)

    # Create study path
    result_text = f"# Study Path: {goal.title()}\n\n"
    result_text += f"Found {len(relevant_concepts)} relevant concepts organized by learning progression:\n\n"

    # Group by complexity/book
    basic_concepts = []
    intermediate_concepts = []
    advanced_concepts = []

    for concept, score in relevant_concepts:
        concept_text = concept['title'].lower() + ' ' + concept['description'].lower()

        # Simple heuristic for complexity
        if any(word in concept_text for word in ['basic', 'introduction', 'overview', 'simple']):
            basic_concepts.append(concept)
        elif any(word in concept_text for word in ['advanced', 'complex', 'optimization', 'internals']):
            advanced_concepts.append(concept)
        else:
            intermediate_concepts.append(concept)

    # If no clear categorization, distribute evenly
    if not basic_concepts and not advanced_concepts:
        third = len(relevant_concepts) // 3
        basic_concepts = [c[0] for c in relevant_concepts[:third]]
        intermediate_concepts = [c[0] for c in relevant_concepts[third:2 * third]]
        advanced_concepts = [c[0] for c in relevant_concepts[2 * third:]]

    # Format study path
    if basic_concepts:
        result_text += f"## 📚 Foundation Level\n"
        for i, concept in enumerate(basic_concepts[:5], 1):
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Core concept'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n"
            result_text += f"   URI: `{uri}`\n\n"

    if intermediate_concepts:
        result_text += f"## 🔧 Practical Level\n"
        for i, concept in enumerate(intermediate_concepts[:5], 1):
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Practical application'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n"
            result_text += f"   URI: `{uri}`\n\n"

    if advanced_concepts:
        result_text += f"## 🚀 Advanced Level\n"
        for i, concept in enumerate(advanced_concepts[:5], 1):
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            result_text += f"{i}. **{concept['title']}** ({concept['book_title']})\n"
            result_text += f"   {concept['description'][:100] if concept['description'] else 'Advanced topic'}{'...' if len(concept.get('description', '')) > 100 else ''}\n"
            result_text += f"   ID: `{concept['id']}`\n"
            result_text += f"   URI: `{uri}`\n\n"

    result_text += f"## 💡 Study Tips\n"
    result_text += f"- Start with Foundation Level concepts\n"
    result_text += f"- Use `get_concept_details(id)` for full explanations\n"
    result_text += f"- Use `find_code_examples('{goal}')` for practical examples\n"
    result_text += f"- Compare concepts between different books for deeper understanding\n"

    return result_text


@mcp.tool()
async def generate_reference_sheet(topic: str, format: str = "markdown") -> str:
    """Generate a formatted reference sheet for a specific topic.

    Args:
        topic: The programming topic to create a reference for
        format: Output format - 'markdown', 'text', or 'html'
    """
    global concepts

    if not concepts:
        return "No concepts available"

    # Search for relevant concepts
    topic_lower = topic.lower()
    relevant_concepts = []

    for concept in concepts:
        if (topic_lower in concept['title'].lower() or
                topic_lower in concept['description'].lower() or
                topic_lower in concept['content'].lower()):
            relevant_concepts.append(concept)

    if not relevant_concepts:
        return f"No concepts found for topic: {topic}"

    # Group concepts by book
    by_book = {}
    for concept in relevant_concepts:
        book = concept['book_title']
        if book not in by_book:
            by_book[book] = []
        by_book[book].append(concept)

    # Generate reference sheet based on format
    if format.lower() == "markdown":
        return _generate_markdown_reference(topic, by_book)
    elif format.lower() == "html":
        return _generate_html_reference(topic, by_book)
    else:  # text format
        return _generate_text_reference(topic, by_book)


@mcp.tool()
async def synthesize_concepts(topic: str, max_sources: int = 5) -> str:
    """AI-powered synthesis: Combine concepts from multiple books into comprehensive explanation.

    Args:
        topic: The topic to synthesize (e.g., 'memory management', 'pointers', 'processes')
        max_sources: Maximum number of source books to include (default: 5)
    """
    topic_lower = topic.lower()

    # Find all related concepts across books
    related_concepts = []
    concept_scores = []

    for concept in concepts:
        # Calculate relevance score using multiple factors
        title_score = 2.0 if topic_lower in concept['title'].lower() else 0.0
        desc_score = 1.5 if topic_lower in concept['description'].lower() else 0.0
        content_score = 1.0 if topic_lower in concept['content'].lower() else 0.0

        # Boost score for certain books based on topic
        book_boost = {
            'memory': {'kernighan_ritchie': 1.5, 'os_three_pieces': 2.0, 'expert_c_programming': 1.8,
                       'csapp_2016': 2.2},
            'process': {'unix_env': 2.0, 'os_three_pieces': 1.8, 'csapp_2016': 1.8},
            'link': {'linkers_loaders': 2.5, 'csapp_2016': 1.5},
            'pointer': {'kernighan_ritchie': 2.0, 'expert_c_programming': 2.2},
            'cache': {'csapp_2016': 2.5, 'os_three_pieces': 1.5},
            'assembly': {'csapp_2016': 2.5},
            'system': {'unix_env': 2.0, 'csapp_2016': 2.2, 'os_three_pieces': 1.8}
        }

        boost = 1.0
        for keyword, boosts in book_boost.items():
            if keyword in topic_lower:
                boost = boosts.get(concept['book'], 1.0)
                break

        total_score = (title_score + desc_score + content_score) * boost

        if total_score > 0:
            related_concepts.append(concept)
            concept_scores.append(total_score)

    if not related_concepts:
        return f"No concepts found for synthesis on topic: '{topic}'"

    # Sort by score and group by book
    sorted_pairs = sorted(zip(related_concepts, concept_scores), key=lambda x: x[1], reverse=True)
    concepts_by_book = {}

    for concept, score in sorted_pairs[:15]:  # Top 15 concepts
        book = concept['book']
        if book not in concepts_by_book:
            concepts_by_book[book] = []
        concepts_by_book[book].append((concept, score))

    # Limit books to max_sources
    if len(concepts_by_book) > max_sources:
        # Keep books with highest total scores
        book_scores = {book: sum(score for _, score in concepts)
                       for book, concepts in concepts_by_book.items()}
        top_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)[:max_sources]
        concepts_by_book = {book: concepts_by_book[book] for book, _ in top_books}

    # Generate synthesized content
    result = f"# 🧬 Synthesized Knowledge: {topic.title()}\n\n"
    result += f"*AI-powered synthesis combining insights from {len(concepts_by_book)} authoritative sources*\n\n"

    # Executive Summary
    result += "## 📋 Executive Summary\n\n"
    result += f"This synthesis combines {sum(len(c) for c in concepts_by_book.values())} concepts from:\n"
    for book in concepts_by_book:
        result += f"- **{books_metadata[book]}**\n"
    result += "\n"

    # Core Concepts Section
    result += f"## 🎯 Core Understanding of {topic.title()}\n\n"

    # Synthesize main explanation
    all_descriptions = []
    for book_concepts in concepts_by_book.values():
        for concept, _ in book_concepts[:3]:  # Top 3 from each book
            if concept['description']:
                all_descriptions.append(concept['description'])

    if all_descriptions:
        # Create unified explanation
        result += "### Unified Explanation\n\n"
        # Combine unique insights
        seen_points = set()
        for desc in all_descriptions:
            sentences = desc.split('. ')
            for sentence in sentences:
                normalized = sentence.lower().strip()
                if normalized and normalized not in seen_points and len(normalized) > 20:
                    seen_points.add(normalized)
                    result += f"- {sentence.strip()}.\n"
        result += "\n"

    # Technical Details by Perspective
    result += "## 🔍 Multi-Perspective Analysis\n\n"

    for book, book_concepts in concepts_by_book.items():
        book_name = books_metadata[book].split('(')[0].strip()
        result += f"### {book_name} Perspective\n\n"

        # Combine insights from this book
        for concept, score in book_concepts[:2]:  # Top 2 concepts
            if concept['content']:
                concept_uri_id = concept_to_clean_uri_id(concept)
                uri = f"concept://{concept['book']}/{concept_uri_id}"
                result += f"**{concept['title']}**: {concept['content'][:200]}...\n"
                result += f"[Read full concept]({uri})\n\n"

    # Code Examples Section
    result += "## 💻 Unified Code Examples\n\n"

    code_examples = []
    for book, book_concepts in concepts_by_book.items():
        for concept, _ in book_concepts:
            if concept['syntax']:
                code_examples.append({
                    'code': concept['syntax'],
                    'source': books_metadata[book],
                    'title': concept['title'],
                    'concept': concept
                })

    if code_examples:
        result += "### Comprehensive Example\n\n```c\n"
        result += "/* Synthesized from multiple sources */\n\n"

        # Intelligently combine code examples
        seen_patterns = set()
        for example in code_examples[:3]:  # Top 3 examples
            code_lines = example['code'].split('\n')
            result += f"/* From {example['source'].split('(')[0].strip()} */\n"
            for line in code_lines:
                normalized = line.strip().lower()
                if normalized and normalized not in seen_patterns:
                    seen_patterns.add(normalized)
                    result += f"{line}\n"
            result += "\n"
        result += "```\n\n"

    result += f"\n---\n*Synthesis generated from {len(concepts_by_book)} books with {sum(len(c) for c in concepts_by_book.values())} relevant concepts*"

    return result


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
    result = f"# 📚 Enhanced Tutorial: {topic.title()}\n\n"
    result += f"**Skill Level**: {skill_level.title()}\n"
    result += f"**Estimated Duration**: {estimated_duration} minutes\n"
    result += f"**Concepts Covered**: {len(selected_concepts)} lessons\n\n"

    # ENHANCEMENT 2: Explicit source attribution
    result += "## 📖 Sources\n\n"
    for book, concepts_list in source_mapping.items():
        result += f"- **{book}**: {', '.join(concepts_list[:3])}"
        if len(concepts_list) > 3:
            result += f" (and {len(concepts_list) - 3} more)"
        result += "\n"
    result += "\n"

    # ENHANCEMENT 3: Clear, comprehensive learning objectives
    result += "## 🎯 Learning Objectives\n\n"
    result += "By the end of this tutorial, you will:\n"

    if skill_level_lower == 'beginner':
        result += f"- Understand the fundamental concepts of {topic}\n"
        result += f"- Recognize common patterns and basic syntax\n"
        result += f"- Write simple, working code examples\n"
        result += f"- Identify when to use {topic} in your programs\n"
    elif skill_level_lower == 'intermediate':
        result += f"- Master practical applications of {topic}\n"
        result += f"- Understand system-level implications and performance considerations\n"
        result += f"- Implement robust solutions with proper error handling\n"
        result += f"- Debug common issues and optimize implementations\n"
    else:  # advanced
        result += f"- Master advanced techniques and optimization strategies for {topic}\n"
        result += f"- Understand deep system-level behavior and edge cases\n"
        result += f"- Implement high-performance, production-ready solutions\n"
        result += f"- Recognize and avoid subtle pitfalls and anti-patterns\n"

    result += "\n## 📖 Tutorial Content\n\n"

    # ENHANCEMENT 4: Progressive lessons with complete explanations
    for i, concept in enumerate(selected_concepts, 1):
        concept_uri_id = concept_to_clean_uri_id(concept)
        uri = f"concept://{concept['book']}/{concept_uri_id}"

        result += f"### Lesson {i}: {concept['title']}\n\n"
        result += f"*Source: {concept['book_title']}*\n\n"

        # ENHANCEMENT 5: Complete concept explanation (no truncation)
        if concept['description']:
            result += f"**Concept**: {concept['description']}\n\n"

        # ENHANCEMENT 6: Full detailed explanation
        if concept['content']:
            result += f"**Detailed Explanation**:\n\n{concept['content']}\n\n"
        else:
            result += f"**Detailed Explanation**: [See full concept for complete details]({uri})\n\n"

        # ENHANCEMENT 7: Enhanced code examples with context
        if concept['syntax']:
            result += "**Code Example**:\n\n"
            result += _generate_enhanced_code_example(concept, topic, skill_level_lower)
            result += "\n"

        # ENHANCEMENT 8: Specific, actionable practice tasks
        result += "**Practice Exercise**:\n\n"
        result += _generate_specific_practice_task(concept, topic, skill_level_lower, i)
        result += "\n"

        # ENHANCEMENT 9: Concrete tool demonstrations for advanced topics
        if skill_level_lower == 'advanced' and _has_system_level_content(concept):
            result += "**System Analysis**:\n\n"
            result += _generate_tool_demonstration(concept, topic)
            result += "\n"

        result += f"**Full Reference**: [Complete concept details]({uri})\n\n"
        result += "---\n\n"

    # ENHANCEMENT 10: Advanced summary and next steps
    result += "## 🎓 Summary & Next Steps\n\n"
    result += f"You've now covered {len(selected_concepts)} key concepts in {topic}. "

    if skill_level_lower == 'beginner':
        result += "Practice these fundamentals before moving to intermediate topics.\n\n"
        result += "**Recommended Next Topics**: "
        result += ", ".join(_get_next_topics_beginner(topic))
    elif skill_level_lower == 'intermediate':
        result += "You're ready to tackle real-world applications and performance optimization.\n\n"
        result += "**Recommended Advanced Topics**: "
        result += ", ".join(_get_next_topics_intermediate(topic))
    else:
        result += "You now have expert-level understanding. Consider contributing to open-source projects.\n\n"
        result += "**Expert-Level Challenges**: "
        result += ", ".join(_get_expert_challenges(topic))

    result += "\n\n## 🔗 Cross-References\n\n"
    result += "Related tutorials you might find useful:\n"
    for book in source_books[:3]:
        result += f"- Search `{book.split('(')[0].strip()}` for advanced {topic} topics\n"

    result += f"\n---\n*Tutorial generated from {len(source_books)} authoritative sources, "
    result += f"covering {len(selected_concepts)} progressive concepts*"

    return result


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


@mcp.tool()
async def create_best_practices_guide(topic: str) -> str:
    """Analyze patterns across all sources to generate best practices guide.

    Args:
        topic: The topic to analyze for best practices (e.g., 'error handling', 'memory management')
    """
    topic_lower = topic.lower()

    # Collect all relevant concepts
    relevant_concepts = []
    for concept in concepts:
        relevance_score = 0
        if topic_lower in concept['title'].lower():
            relevance_score += 3
        if topic_lower in concept['description'].lower():
            relevance_score += 2
        if topic_lower in concept['content'].lower():
            relevance_score += 1

        if relevance_score > 0:
            relevant_concepts.append((concept, relevance_score))

    if not relevant_concepts:
        return f"No concepts found to generate best practices for '{topic}'"

    # Sort by relevance
    relevant_concepts.sort(key=lambda x: x[1], reverse=True)

    # Analyze patterns across books
    patterns_by_book = {}
    code_patterns = []
    common_recommendations = []
    pitfalls = []

    for concept, _ in relevant_concepts[:20]:  # Top 20 concepts
        book = concept['book']
        if book not in patterns_by_book:
            patterns_by_book[book] = []
        patterns_by_book[book].append(concept)

        # Extract patterns from content
        content = (concept['content'] + ' ' + concept['description']).lower()

        # Look for recommendations
        if any(word in content for word in ['should', 'must', 'always', 'recommend']):
            common_recommendations.append(concept)

        # Look for pitfalls
        if any(word in content for word in ['avoid', 'never', 'pitfall', 'error', 'mistake', 'wrong']):
            pitfalls.append(concept)

        # Collect code patterns
        if concept['syntax']:
            code_patterns.append({
                'code': concept['syntax'],
                'source': concept['book_title'],
                'context': concept['title'],
                'concept': concept
            })

    # Generate best practices guide
    result = f"# 🏆 Best Practices Guide: {topic.title()}\n\n"
    result += f"*Analyzing {len(relevant_concepts)} concepts from {len(patterns_by_book)} authoritative sources*\n\n"

    return result


# Helper functions for reference sheet generation
def _generate_markdown_reference(topic: str, by_book: dict) -> str:
    """Generate markdown formatted reference sheet."""
    output = f"# {topic.title()} Reference Sheet\n\n"
    output += f"*Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books*\n\n"

    for book, concepts in by_book.items():
        output += f"## {book}\n\n"

        for concept in concepts:
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            output += f"### {concept['title']}\n\n"

            if concept['description']:
                output += f"{concept['description']}\n\n"

            if concept['syntax']:
                output += f"```c\n{concept['syntax']}\n```\n\n"

            if concept['content']:
                output += f"**Details:** {concept['content'][:200]}{'...' if len(concept['content']) > 200 else ''}\n\n"

            output += f"*Source: {book}* | [Full Details]({uri})\n\n---\n\n"

    return output


def _generate_html_reference(topic: str, by_book: dict) -> str:
    """Generate HTML formatted reference sheet."""
    output = f"""<!DOCTYPE html>
<html>
<head>
    <title>{topic.title()} Reference Sheet</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; }}
        h2 {{ color: #007acc; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
        .source {{ font-style: italic; color: #666; }}
    </style>
</head>
<body>
    <h1>{topic.title()} Reference Sheet</h1>
    <p><em>Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books</em></p>
"""

    for book, concepts in by_book.items():
        output += f"    <h2>{book}</h2>\n"

        for concept in concepts:
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            output += f"    <h3>{concept['title']}</h3>\n"

            if concept['description']:
                output += f"    <p>{concept['description']}</p>\n"

            if concept['syntax']:
                output += f"    <pre><code>{concept['syntax']}</code></pre>\n"

            if concept['content']:
                content = concept['content'][:200] + ('...' if len(concept['content']) > 200 else '')
                output += f"    <p><strong>Details:</strong> {content}</p>\n"

            output += f"    <p class='source'>Source: {book} | <a href='{uri}'>Full Details</a></p>\n    <hr>\n"

    output += "</body></html>"
    return output


def _generate_text_reference(topic: str, by_book: dict) -> str:
    """Generate plain text formatted reference sheet."""
    output = f"{topic.upper()} REFERENCE SHEET\n"
    output += "=" * len(f"{topic.upper()} REFERENCE SHEET") + "\n\n"
    output += f"Generated from {sum(len(concepts) for concepts in by_book.values())} concepts across {len(by_book)} books\n\n"

    for book, concepts in by_book.items():
        output += f"{book.upper()}\n"
        output += "-" * len(book) + "\n\n"

        for concept in concepts:
            concept_uri_id = concept_to_clean_uri_id(concept)
            uri = f"concept://{concept['book']}/{concept_uri_id}"

            output += f"{concept['title']}\n"

            if concept['description']:
                output += f"Description: {concept['description']}\n"

            if concept['syntax']:
                output += f"Code:\n{concept['syntax']}\n"

            if concept['content']:
                content = concept['content'][:200] + ('...' if len(concept['content']) > 200 else '')
                output += f"Details: {content}\n"

            output += f"Source: {book}\nURI: {uri}\n\n"

    return output


# Initialize the concepts database when the module loads
build_concept_index()
logger.info("Programming Concepts MCP Server initialized with efficient duplicate cleanup")

if __name__ == "__main__":
    # Run the FastMCP server
    logger.info("Starting Programming Concepts MCP Server for Claude Code...")
    logger.info("MCP Server ready for Claude Code with efficient duplicate cleanup functionality")
    mcp.run(transport='stdio')
