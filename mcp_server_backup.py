#!/usr/bin/env python3
"""
Main Programming Concepts MCP Server
UPDATED: Now includes CSAPP (Computer Systems: A Programmer's Perspective) integration

Provides unified access to programming concepts from 6 classic computer science books:
- K&R C Programming Language
- Advanced Programming in the UNIX Environment  
- Linkers and Loaders
- Operating Systems: Three Easy Pieces
- Expert C Programming: Deep C Secrets
- Computer Systems: A Programmer's Perspective (CSAPP) - NEW

Features:
- Cross-book concept search and comparison
- AI-powered concept synthesis combining insights from multiple books
- Custom tutorial generation merging related concepts
- Best practices guides analyzing patterns across all sources
"""

import json
import logging
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher

# Add current directory to Python path
sys.path.append('.')

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("programming-concepts-mcp")

# Initialize FastMCP server
mcp = FastMCP("programming-concepts")

# Global storage for all concepts
ALL_CONCEPTS = {}
CONCEPTS_LOADED = False

# Book metadata with CSAPP addition
books_metadata = {
    "kernighan_ritchie": "The C Programming Language (K&R)",
    "unix_env": "Advanced Programming in the UNIX Environment", 
    "linkers_loaders": "Linkers and Loaders",
    "os_three_pieces": "Operating Systems: Three Easy Pieces",
    "expert_c_programming": "Expert C Programming: Deep C Secrets",
    "csapp_2016": "Computer Systems: A Programmer's Perspective (CSAPP)"
}

def load_all_concepts():
    """Load concepts from all 6 book directories"""
    global ALL_CONCEPTS, CONCEPTS_LOADED
    
    if CONCEPTS_LOADED:
        return ALL_CONCEPTS
    
    project_root = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    outputs_dir = project_root / "outputs"
    
    ALL_CONCEPTS = {}
    total_loaded = 0
    
    for book_name in books_metadata.keys():
        book_dir = outputs_dir / book_name
        if not book_dir.exists():
            logger.warning(f"Directory not found: {book_dir}")
            ALL_CONCEPTS[book_name] = {}
            continue
        
        concept_files = list(book_dir.glob("*concept_*.json"))
        book_concepts = {}
        
        for concept_file in concept_files:
            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept = json.load(f)
                
                # Create unique concept ID
                concept_id = f"{book_name}_{concept_file.stem}"
                
                # Add metadata
                concept['concept_id'] = concept_id
                concept['source_book'] = book_name
                concept['book_title'] = books_metadata[book_name]
                
                book_concepts[concept_id] = concept
                total_loaded += 1
                
            except Exception as e:
                logger.error(f"Error loading {concept_file}: {e}")
        
        ALL_CONCEPTS[book_name] = book_concepts
        logger.info(f"📚 Loaded {len(book_concepts)} concepts from {book_name}")
    
    CONCEPTS_LOADED = True
    logger.info(f"✅ Total concepts loaded: {total_loaded} from {len(books_metadata)} books")
    return ALL_CONCEPTS

@mcp.tool()
def search_concepts(query: str, limit: int = 20) -> Dict:
    """
    Search concepts across all 6 books
    Enhanced with CSAPP systems programming concepts
    
    Args:
        query: Search terms
        limit: Maximum results to return
        
    Returns:
        Dictionary with search results from all books
    """
    concepts = load_all_concepts()
    
    if not any(concepts.values()):
        return {
            "results": [],
            "total_found": 0,
            "query": query,
            "books_searched": list(books_metadata.keys()),
            "message": "No concepts loaded. Run concept extraction first."
        }
    
    # Normalize query
    query_lower = query.lower()
    query_terms = re.findall(r'\w+', query_lower)
    
    # Score concepts by relevance across all books
    scored_results = []
    
    for book_name, book_concepts in concepts.items():
        for concept_id, concept in book_concepts.items():
            score = 0
            
            # Create searchable text
            searchable_text = f"{concept.get('topic', '')} {concept.get('explanation', '')} {concept.get('syntax', '')} {' '.join(concept.get('code_example', []))}"
            text_lower = searchable_text.lower()
            
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
            
            # Bonus for systems concepts in CSAPP
            if book_name == "csapp_2016" and any(term in text_lower for term in ["system", "architecture", "memory", "cache", "assembly"]):
                score += 3
            
            if score > 0:
                scored_results.append((score, concept, book_name))
    
    # Sort by relevance and limit results
    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_results[:limit]
    
    # Format results
    formatted_results = []
    for score, concept, book_name in top_results:
        formatted_results.append({
            "concept_id": concept['concept_id'],
            "topic": concept.get('topic', 'Unknown Topic'),
            "explanation": concept.get('explanation', '')[:200] + "..." if len(concept.get('explanation', '')) > 200 else concept.get('explanation', ''),
            "source_book": book_name,
            "book_title": books_metadata[book_name],
            "relevance_score": score,
            "page_range": concept.get('extraction_metadata', {}).get('page_range', 'Unknown'),
            "has_code": bool(concept.get('code_example'))
        })
    
    return {
        "results": formatted_results,
        "total_found": len(scored_results),
        "query": query,
        "books_searched": list(books_metadata.keys()),
        "books_with_results": len(set(book_name for _, _, book_name in scored_results))
    }

@mcp.tool()
async def analyze_concept_duplicates(book_name: str, similarity_threshold: float = 0.90) -> str:
    """Analyze duplicate concepts in a book directory without making any changes.
    
    Args:
        book_name: Book directory name (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming)
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
    
    # Find all concept JSON files
    concept_files = list(book_dir.glob("*concept_*.json"))
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
        for j, concept2 in enumerate(loaded_concepts[i+1:], i+1):
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
        result += f"## 📋 Other Similar Pairs ({similarity_threshold-0.1:.0%}-{similarity_threshold:.0%} similar)\n\n"
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
async def cleanup_duplicate_concepts(book_name: str, similarity_threshold: float = 0.90, dry_run: bool = False) -> str:
    """Clean up duplicate concept files for a specific book.
    
    Args:
        book_name: Book directory name (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming)
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
    
    # Find all concept JSON files
    concept_files = list(book_dir.glob("*concept_*.json"))
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
        
        for j, concept2 in enumerate(loaded_concepts[i+1:], i+1):
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
        result += "\nRun `cleanup_duplicate_concepts('{}', {}, False)` to perform actual cleanup.".format(book_name, similarity_threshold)
    
    return result

@mcp.tool()

async def show_books_progress() -> str:
    """Display comprehensive progress status for all books in the extraction system.
    
    Shows:
    - Extraction progress and completion status
    - Concept counts and file statistics  
    - Recent activity and session history
    - Health metrics and recommendations
    - YOU WILL NEED TO UPDATE THE AMOUNT OFPAGES AND BOOK NAME YOURSELF!
    """
    from pathlib import Path
    import json
    from datetime import datetime
    import os
    
    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    outputs_dir = PROJECT_ROOT / "outputs"
    
    if not outputs_dir.exists():
        return "❌ Outputs directory not found. Run concept extraction first."
    
    result = "# 📚 Book Extraction Progress Dashboard\n\n"
    result += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Book status tracking
    books_status = {}
    total_concepts = 0
    completed_books = 0
    active_books = 0
    
    # Expected total pages for completion estimation (verified counts)
    book_page_estimates = {
        "kernighan_ritchie": 272,       # K&R C Programming (verified)
        "unix_env": 1024,               # UNIX Environment (estimate - not provided)
        "linkers_loaders": 256,         # Linkers and Loaders (verified)
        "os_three_pieces": 570,         # OS Three Easy Pieces (verified - was 736)
        "expert_c_programming": 375,    # Expert C Programming (verified ~350-400, using mid-point)
        "csapp_2016": 1120             # CSAPP 3rd ed (verified ~1120, was 1048)
    }
    
    for book_name in books_metadata.keys():
        book_dir = outputs_dir / book_name
        progress_file = book_dir / "progress.json"
        
        # Initialize book status
        book_status = {
            "name": books_metadata[book_name],
            "directory_exists": book_dir.exists(),
            "progress_file_exists": progress_file.exists(),
            "concepts_extracted": 0,
            "concept_files": 0,
            "last_processed_page": 0,
            "extraction_sessions": 0,
            "last_extraction_date": "Never",
            "estimated_progress": 0.0,
            "status": "Not Started",
            "health": "Unknown",
            "recommendations": []
        }
        
        if not book_dir.exists():
            book_status["status"] = "Directory Missing"
            book_status["health"] = "Error"
            book_status["recommendations"].append("Create outputs directory and run extraction")
        else:
            # Count concept files
            concept_files = list(book_dir.glob("*concept_*.json"))
            book_status["concept_files"] = len(concept_files)
            
            if progress_file.exists():
                try:
                    with open(progress_file, 'r') as f:
                        progress_data = json.load(f)
                    
                    # Extract progress information
                    book_status["concepts_extracted"] = progress_data.get("total_concepts_extracted", 0)
                    book_status["last_processed_page"] = progress_data.get("last_processed_page", 0)
                    book_status["extraction_sessions"] = len(progress_data.get("extraction_sessions", []))
                    
                    # Get last extraction date
                    sessions = progress_data.get("extraction_sessions", [])
                    if sessions:
                        last_session = sessions[-1]
                        book_status["last_extraction_date"] = last_session.get("date", "Unknown")
                    
                    # Calculate estimated progress
                    expected_pages = book_page_estimates.get(book_name, 500)
                    progress_percent = min((book_status["last_processed_page"] / expected_pages) * 100, 100)
                    book_status["estimated_progress"] = progress_percent
                    
                    # Determine status
                    if book_status["concepts_extracted"] == 0:
                        book_status["status"] = "Not Started"
                        book_status["health"] = "Waiting"
                    elif progress_percent >= 95:
                        book_status["status"] = "Complete"
                        book_status["health"] = "Excellent"
                        completed_books += 1
                    elif progress_percent >= 50:
                        book_status["status"] = "Active"
                        book_status["health"] = "Good"
                        active_books += 1
                        book_status["recommendations"].append("Continue regular extraction sessions")
                    else:
                        book_status["status"] = "Started"
                        book_status["health"] = "Fair"
                        active_books += 1
                        book_status["recommendations"].append("Increase extraction frequency")
                    
                    # Check for recent activity
                    if sessions:
                        try:
                            last_date = datetime.fromisoformat(sessions[-1]["date"].replace("Z", "+00:00"))
                            days_since = (datetime.now() - last_date).days
                            
                            if days_since > 7 and book_status["status"] != "Complete":
                                book_status["health"] = "Stale"
                                book_status["recommendations"].append(f"No activity for {days_since} days")
                        except:
                            pass
                    
                    # File count vs concepts mismatch check
                    if book_status["concept_files"] != book_status["concepts_extracted"]:
                        book_status["recommendations"].append("File count mismatch - check for corruption")
                
                except Exception as e:
                    book_status["status"] = "Progress Error"
                    book_status["health"] = "Error"
                    book_status["recommendations"].append(f"Progress file corrupt: {str(e)}")
            
            elif book_status["concept_files"] > 0:
                # Has concept files but no progress file
                book_status["status"] = "Legacy Data"
                book_status["health"] = "Warning"
                book_status["concepts_extracted"] = book_status["concept_files"]
                book_status["recommendations"].append("Missing progress file - manual extraction?")
        
        books_status[book_name] = book_status
        total_concepts += book_status["concepts_extracted"]
    
    # Generate dashboard
    result += "## 📊 Overview\n\n"
    result += f"- **Total Books:** {len(books_metadata)}\n"
    result += f"- **Completed Books:** {completed_books}\n" 
    result += f"- **Active Books:** {active_books}\n"
    result += f"- **Total Concepts Extracted:** {total_concepts}\n\n"
    
    # Progress bars and detailed status
    result += "## 📈 Book Status Details\n\n"
    
    # Sort by progress for better display
    sorted_books = sorted(books_status.items(), 
                         key=lambda x: (x[1]["estimated_progress"], x[1]["concepts_extracted"]), 
                         reverse=True)
    
    for book_id, status in sorted_books:
        # Status emoji
        status_emoji = {
            "Complete": "✅",
            "Active": "🔄", 
            "Started": "🟡",
            "Not Started": "⭐",
            "Directory Missing": "❌",
            "Progress Error": "🔴",
            "Legacy Data": "⚠️"
        }.get(status["status"], "❓")
        
        # Health emoji
        health_emoji = {
            "Excellent": "💚",
            "Good": "🟢",
            "Fair": "🟡",
            "Warning": "🟠", 
            "Stale": "🔴",
            "Error": "❌",
            "Unknown": "❓"
        }.get(status["health"], "❓")
        
        result += f"### {status_emoji} {status['name']}\n\n"
        
        # Progress bar
        progress = status["estimated_progress"]
        bar_length = 20
        filled = int((progress / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        result += f"**Progress:** {bar} {progress:.1f}%\n\n"
        
        # Key metrics
        result += f"- **Status:** {status['status']} {health_emoji}\n"
        result += f"- **Concepts Extracted:** {status['concepts_extracted']}\n"
        result += f"- **Pages Processed:** {status['last_processed_page']}\n"
        result += f"- **Extraction Sessions:** {status['extraction_sessions']}\n"
        result += f"- **Last Activity:** {status['last_extraction_date'][:10] if status['last_extraction_date'] != 'Never' else 'Never'}\n"
        
        # File health check
        if status["concept_files"] != status["concepts_extracted"] and status["concepts_extracted"] > 0:
            result += f"- **⚠️ File Count:** {status['concept_files']} files vs {status['concepts_extracted']} recorded\n"
        
        # Recommendations
        if status["recommendations"]:
            result += f"\n**Recommendations:**\n"
            for rec in status["recommendations"][:3]:  # Show top 3
                result += f"- {rec}\n"
        
        result += "\n"
    
    # System health summary
    result += "## 🏥 System Health\n\n"
    
    healthy_books = sum(1 for status in books_status.values() 
                       if status["health"] in ["Excellent", "Good"])
    warning_books = sum(1 for status in books_status.values() 
                       if status["health"] in ["Fair", "Warning", "Stale"])
    error_books = sum(1 for status in books_status.values() 
                     if status["health"] == "Error")
    
    result += f"- **💚 Healthy Books:** {healthy_books}\n"
    result += f"- **🟡 Books Needing Attention:** {warning_books}\n"
    result += f"- **❌ Books with Errors:** {error_books}\n\n"
    
    # Next actions
    result += "## 🎯 Recommended Actions\n\n"
    
    # Find books that need immediate attention
    priority_actions = []
    
    for book_id, status in books_status.items():
        if status["status"] == "Directory Missing":
            priority_actions.append(f"🔴 **{status['name']}**: Create directory and start extraction")
        elif status["status"] == "Progress Error":
            priority_actions.append(f"🔴 **{status['name']}**: Fix progress file corruption")
        elif status["health"] == "Stale" and status["status"] != "Complete":
            priority_actions.append(f"🟡 **{status['name']}**: Resume extraction (inactive)")
        elif status["status"] == "Not Started" and status["directory_exists"]:
            priority_actions.append(f"⭐ **{status['name']}**: Start extraction")
    
    if priority_actions:
        for action in priority_actions[:5]:  # Show top 5 priorities
            result += f"- {action}\n"
    else:
        result += "✅ **All books are in good status!**\n"
    
    # Usage commands
    result += "\n## 🔧 Quick Commands\n\n"
    result += "```bash\n"
    result += "# Run specific book extraction\n"
    for book_id, status in books_status.items():
        if status["status"] in ["Not Started", "Active", "Started"]:
            script_names = {
                "kernighan_ritchie": "extract_c_concepts.py",
                "unix_env": "extract_unix_env.py", 
                "linkers_loaders": "extract_linkers_loaders.py",
                "os_three_pieces": "extract_os_three_pieces.py",
                "expert_c_programming": "extract_Expert_C_Programming.py",
                "csapp_2016": "extract_csapp.py"  # Assuming this exists
            }
            script = script_names.get(book_id, f"extract_{book_id}.py")
            result += f"python books/{script}  # {status['name']}\n"
            break  # Show just one example
    
    result += "\n# Clean up duplicates for any book\n"
    result += "cleanup_duplicate_concepts('book_name', 0.90, True)  # Dry run first\n"
    result += "```\n"
    
    # Summary statistics
    avg_progress = sum(status["estimated_progress"] for status in books_status.values()) / len(books_status)
    result += f"\n---\n"
    result += f"**Overall Progress:** {avg_progress:.1f}% across all books\n"
    result += f"**System Status:** {'🟢 Healthy' if error_books == 0 and warning_books <= 1 else '🟡 Needs Attention' if error_books == 0 else '🔴 Issues Detected'}\n"
    
    return result


@mcp.tool()
async def show_book_detailed_progress(book_name: str) -> str:
    """Show detailed progress information for a specific book.
    
    Args:
        book_name: Book to analyze (kernighan_ritchie, unix_env, linkers_loaders, os_three_pieces, expert_c_programming, csapp_2016)
    """
    from pathlib import Path
    import json
    from datetime import datetime
    
    if book_name not in books_metadata:
        available_books = list(books_metadata.keys())
        return f"Invalid book name '{book_name}'. Available books: {', '.join(available_books)}"
    
    PROJECT_ROOT = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
    book_dir = PROJECT_ROOT / "outputs" / book_name
    progress_file = book_dir / "progress.json"
    
    result = f"# 📖 Detailed Progress: {books_metadata[book_name]}\n\n"
    result += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if not book_dir.exists():
        result += "❌ **Status:** Directory does not exist\n\n"
        result += "**Next Steps:**\n"
        result += f"1. Create the book directory\n"
        result += f"2. Run the extraction script for {book_name}\n"
        return result
    
    # Count concept files
    concept_files = list(book_dir.glob("*concept_*.json"))
    result += f"## 📊 File Statistics\n\n"
    result += f"- **Concept Files:** {len(concept_files)}\n"
    
    # Check for different file naming patterns
    expert_c_files = [f for f in concept_files if f.name.startswith('expert_c_concept_')]
    regular_files = [f for f in concept_files if f.name.startswith('concept_') and not f.name.startswith('expert_c_concept_')]
    other_files = [f for f in concept_files if not f.name.startswith('concept_')]
    
    if expert_c_files:
        result += f"- **Expert C Format Files:** {len(expert_c_files)}\n"
    if regular_files:
        result += f"- **Regular Format Files:** {len(regular_files)}\n"
    if other_files:
        result += f"- **Other Format Files:** {len(other_files)}\n"
    
    # Backup directories
    backup_dirs = [d for d in book_dir.iterdir() if d.is_dir() and d.name.startswith('cleanup_backup_')]
    if backup_dirs:
        result += f"- **Backup Directories:** {len(backup_dirs)}\n"
    
    result += "\n"
    
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            
            result += f"## 📈 Extraction Progress\n\n"
            result += f"- **Total Concepts:** {progress_data.get('total_concepts_extracted', 0)}\n"
            result += f"- **Last Processed Page:** {progress_data.get('last_processed_page', 0)}\n"
            result += f"- **Current Chapter:** {progress_data.get('current_chapter', 1)}\n"
            
            # Extraction sessions history
            sessions = progress_data.get('extraction_sessions', [])
            result += f"- **Extraction Sessions:** {len(sessions)}\n"
            
            if sessions:
                result += f"\n### 🕒 Recent Sessions\n\n"
                
                # Show last 5 sessions
                for session in sessions[-5:]:
                    date = session.get('date', 'Unknown')[:10]  # Just the date part
                    concepts = session.get('concepts_extracted', 0)
                    page_range = session.get('page_range', 'Unknown')
                    chapter = session.get('chapter', 'Unknown')
                    
                    result += f"- **{date}:** {concepts} concepts extracted (pages {page_range})\n"
                
                # Calculate extraction velocity
                if len(sessions) >= 2:
                    try:
                        last_session = sessions[-1]
                        first_session = sessions[0]
                        
                        last_date = datetime.fromisoformat(last_session['date'].replace('Z', '+00:00'))
                        first_date = datetime.fromisoformat(first_session['date'].replace('Z', '+00:00'))
                        
                        days_span = (last_date - first_date).days
                        total_concepts = progress_data.get('total_concepts_extracted', 0)
                        
                        if days_span > 0:
                            velocity = total_concepts / days_span
                            result += f"\n**Extraction Velocity:** {velocity:.2f} concepts/day\n"
                    except:
                        pass
            
            # Health assessment
            result += f"\n## 🏥 Health Assessment\n\n"
            
            file_concept_match = len(concept_files) == progress_data.get('total_concepts_extracted', 0)
            result += f"- **File/Progress Sync:** {'✅ Matched' if file_concept_match else '⚠️ Mismatch'}\n"
            
            if sessions:
                try:
                    last_date = datetime.fromisoformat(sessions[-1]['date'].replace('Z', '+00:00'))
                    days_since = (datetime.now() - last_date).days
                    
                    if days_since == 0:
                        activity_status = "✅ Active Today"
                    elif days_since <= 3:
                        activity_status = f"🟢 Active ({days_since} days ago)"
                    elif days_since <= 7:
                        activity_status = f"🟡 Recent ({days_since} days ago)"
                    else:
                        activity_status = f"🔴 Stale ({days_since} days ago)"
                    
                    result += f"- **Recent Activity:** {activity_status}\n"
                except:
                    result += f"- **Recent Activity:** ❓ Date parse error\n"
            
            # Completion estimate
            book_page_estimates = {
                "kernighan_ritchie": 272,       # K&R C Programming (verified)
                "unix_env": 1024,               # UNIX Environment (estimate)
                "linkers_loaders": 256,         # Linkers and Loaders (verified)
                "os_three_pieces": 570,         # OS Three Easy Pieces (verified)
                "expert_c_programming": 375,    # Expert C Programming (verified ~350-400)
                "csapp_2016": 1120             # CSAPP 3rd ed (verified ~1120)
            }
            
            expected_pages = book_page_estimates.get(book_name, 500)
            current_page = progress_data.get('last_processed_page', 0)
            progress_percent = min((current_page / expected_pages) * 100, 100)
            
            result += f"\n## 🎯 Completion Status\n\n"
            result += f"- **Estimated Progress:** {progress_percent:.1f}%\n"
            result += f"- **Pages Processed:** {current_page} / ~{expected_pages}\n"
            
            if progress_percent >= 95:
                result += f"- **Status:** ✅ **COMPLETE**\n"
            elif progress_percent >= 75:
                result += f"- **Status:** 🏃 Nearly Complete\n"
            elif progress_percent >= 50:
                result += f"- **Status:** 🔄 Active Extraction\n"
            elif progress_percent >= 25:
                result += f"- **Status:** 🚀 Good Progress\n"
            else:
                result += f"- **Status:** 🌱 Early Stage\n"
                
        except Exception as e:
            result += f"## ❌ Progress File Error\n\n"
            result += f"Error reading progress.json: {str(e)}\n\n"
    
    else:
        result += f"## ⚠️ No Progress File\n\n"
        if concept_files:
            result += f"Found {len(concept_files)} concept files but no progress tracking.\n"
            result += f"This suggests manual extraction or missing progress file.\n\n"
        else:
            result += f"No extraction has been started for this book.\n\n"
    
    # Recent file activity
    if concept_files:
        result += f"## 📁 Recent File Activity\n\n"
        
        # Sort by modification time
        files_with_time = [(f, f.stat().st_mtime) for f in concept_files]
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        # Show 5 most recent files
        result += f"**Most Recently Modified:**\n"
        for f, mtime in files_with_time[:5]:
            mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            result += f"- `{f.name}` ({mod_date})\n"
    
    # Recommendations
    result += f"\n## 💡 Recommendations\n\n"
    
    if not progress_file.exists():
        result += f"- 🔴 **Priority:** Create progress tracking for this book\n"
    elif progress_percent < 100:
        result += f"- 🟢 **Continue:** Run daily extraction sessions\n"
        if len(sessions) > 0 and days_since > 3:
            result += f"- 🟡 **Resume:** Book has been inactive for {days_since} days\n"
    
    if len(concept_files) > 50:
        result += f"- 🧹 **Cleanup:** Consider running duplicate cleanup\n"
    
    result += f"\n---\n*Detailed analysis for {books_metadata[book_name]}*"
    
    return result

@mcp.tool()
def synthesize_concepts(topic: str, max_sources: int = 4) -> str:
    """
    AI-powered synthesis combining insights from multiple books including CSAPP
    
    Args:
        topic: Topic to synthesize (e.g., "memory management", "concurrency")
        max_sources: Maximum number of book sources to include
        
    Returns:
        Comprehensive synthesis combining perspectives from multiple books
    """
    concepts = load_all_concepts()
    
    # Search for relevant concepts across all books
    search_results = search_concepts(topic, limit=50)
    
    if not search_results["results"]:
        return f"No concepts found for topic: {topic}"
    
    # Group concepts by book
    concepts_by_book = defaultdict(list)
    for result in search_results["results"]:
        book = result["source_book"]
        concept_id = result["concept_id"]
        
        # Get full concept details
        if book in concepts and concept_id in concepts[book]:
            full_concept = concepts[book][concept_id]
            concepts_by_book[book].append((full_concept, result["relevance_score"]))
    
    # Limit to max_sources books
    top_books = sorted(concepts_by_book.items(), 
                      key=lambda x: max(score for _, score in x[1]), 
                      reverse=True)[:max_sources]
    
    # Generate synthesis
    result = f"# 🔬 Multi-Source Analysis: {topic.title()}\n\n"
    
    # Executive Summary
    result += "## 📋 Executive Summary\n\n"
    
    total_concepts = sum(len(concepts) for _, concepts in top_books)
    book_names = [books_metadata[book] for book, _ in top_books]
    
    result += f"**Comprehensive analysis of '{topic}' across {len(top_books)} authoritative sources:**\n"
    for book_name in book_names:
        result += f"- {book_name}\n"
    result += f"\n**Total concepts analyzed:** {total_concepts}\n\n"
    
    # Key Insights Section
    result += "## 💡 Key Insights\n\n"
    
    # Extract unique insights from each book
    seen_points = set()
    for book, book_concepts in top_books:
        book_name = books_metadata[book]
        
        # Get top concepts from this book
        top_concepts = sorted(book_concepts, key=lambda x: x[1], reverse=True)[:2]
        
        for concept, score in top_concepts:
            explanation = concept.get('explanation', '')
            # Split into sentences and add unique ones
            sentences = re.split(r'[.!?]+', explanation)
            for sentence in sentences:
                normalized = sentence.lower().strip()
                if normalized and normalized not in seen_points and len(normalized) > 20:
                    seen_points.add(normalized)
                    result += f"- {sentence.strip()}.\n"
        result += "\n"
    
    # Technical Details by Perspective
    result += "## 🔍 Multi-Perspective Analysis\n\n"
    
    for book, book_concepts in top_books:
        book_name = books_metadata[book].split('(')[0].strip()
        result += f"### {book_name} Perspective\n\n"
        
        # Combine insights from this book
        for concept, score in book_concepts[:2]:  # Top 2 concepts
            if concept.get('explanation'):
                result += f"**{concept.get('topic', 'Concept')}**: {concept['explanation'][:200]}...\n\n"
    
    # Code Examples Section
    result += "## 💻 Unified Code Examples\n\n"
    
    code_examples = []
    for book, book_concepts in top_books:
        for concept, _ in book_concepts:
            if concept.get('syntax') or concept.get('code_example'):
                code_examples.append({
                    'code': concept.get('syntax', '') or '\n'.join(concept.get('code_example', [])),
                    'source': books_metadata[book],
                    'title': concept.get('topic', 'Unknown'),
                    'explanation': concept.get('example_explanation', '')
                })
    
    if code_examples:
        result += "### Comprehensive Examples\n\n"
        
        # Intelligently combine code examples
        seen_patterns = set()
        example_count = 0
        
        for example in code_examples[:4]:  # Top 4 examples
            if example_count >= 3:  # Limit to 3 examples
                break
                
            code_lines = example['code'].split('\n')
            unique_lines = []
            
            for line in code_lines:
                normalized = line.strip().lower()
                if normalized and normalized not in seen_patterns:
                    seen_patterns.add(normalized)
                    unique_lines.append(line)
            
            if unique_lines:
                result += f"#### Example {example_count + 1}: {example['title']}\n"
                result += f"*Source: {example['source'].split('(')[0].strip()}*\n\n"
                result += "```c\n"
                result += "\n".join(unique_lines)
                result += "\n```\n\n"
                
                if example['explanation']:
                    result += f"**Explanation**: {example['explanation'][:150]}...\n\n"
                
                example_count += 1
    
    # Synthesized Insights Section
    result += "## 🎯 Synthesized Insights\n\n"
    
    # Generate insights based on patterns
    insights = []
    
    # Pattern: If multiple books cover it, it's fundamental
    if len(top_books) >= 3:
        insights.append(f"**Fundamental Concept**: {topic.title()} is covered across {len(top_books)} authoritative sources, indicating its critical importance in systems programming.")
    
    # Pattern: CSAPP + others = systems focus
    if any(book == "csapp_2016" for book, _ in top_books):
        insights.append(f"**Systems Perspective**: CSAPP provides the computer systems and architecture viewpoint, emphasizing hardware-software interaction and performance implications.")
    
    # Pattern: Book-specific insights
    book_combinations = [book for book, _ in top_books]
    if 'kernighan_ritchie' in book_combinations and 'expert_c_programming' in book_combinations:
        insights.append(f"**C Language Evolution**: Compare basic {topic} concepts from K&R with advanced techniques from Expert C Programming to see the evolution of best practices.")
    
    if 'unix_env' in book_combinations and 'os_three_pieces' in book_combinations:
        insights.append(f"**System-Level View**: Both UNIX and OS perspectives provide complementary views on {topic} at the system level.")
    
    if 'csapp_2016' in book_combinations and 'os_three_pieces' in book_combinations:
        insights.append(f"**Architecture & OS Integration**: CSAPP's hardware perspective combined with OS concepts provides complete understanding of {topic} from silicon to software.")
    
    for insight in insights:
        result += f"{insight}\n\n"
    
    # Cross-References
    result += "## 🔗 Cross-References\n\n"
    result += "**For deeper study, explore these related concepts:**\n"
    
    # Find related concepts
    related_terms = []
    for book, book_concepts in top_books:
        for concept, _ in book_concepts[:1]:  # One concept per book
            topic_words = concept.get('topic', '').split()
            related_terms.extend([word for word in topic_words if len(word) > 4])
    
    unique_terms = list(set(related_terms))[:5]
    for term in unique_terms:
        result += f"- {term}\n"
    
    result += f"\n---\n*Analysis generated from {total_concepts} concepts across {len(top_books)} books*"
    
    return result

@mcp.tool()
def get_concept_details(concept_id: str) -> Dict:
    """
    Get detailed information about a specific concept
    
    Args:
        concept_id: The concept ID (format: book_name_concept_XXX)
        
    Returns:
        Complete concept details
    """
    concepts = load_all_concepts()
    
    # Extract book name from concept_id
    book_name = concept_id.split('_concept_')[0] if '_concept_' in concept_id else concept_id.split('_')[0]
    
    if book_name not in concepts:
        return {
            "error": f"Book '{book_name}' not found",
            "available_books": list(concepts.keys())
        }
    
    if concept_id not in concepts[book_name]:
        return {
            "error": f"Concept '{concept_id}' not found in {book_name}",
            "available_concepts": list(concepts[book_name].keys())[:10]
        }
    
    concept = concepts[book_name][concept_id]
    
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
        "source_book": book_name,
        "book_title": books_metadata[book_name],
        "extraction_metadata": concept.get('extraction_metadata', {})
    }

@mcp.tool()
def search_by_book(book_name: str, query: str, limit: int = 10) -> Dict:
    """
    Search concepts within a specific book
    
    Args:
        book_name: Book to search (e.g., 'csapp_2016', 'kernighan_ritchie')
        query: Search terms
        limit: Maximum results
        
    Returns:
        Search results from the specified book
    """
    concepts = load_all_concepts()
    
    if book_name not in concepts:
        return {
            "error": f"Book '{book_name}' not found",
            "available_books": list(concepts.keys())
        }
    
    book_concepts = concepts[book_name]
    
    if not book_concepts:
        return {
            "results": [],
            "book_name": book_name,
            "book_title": books_metadata[book_name],
            "message": f"No concepts found in {book_name}. Run extraction first."
        }
    
    # Search within this book
    query_lower = query.lower()
    query_terms = re.findall(r'\w+', query_lower)
    
    scored_results = []
    
    for concept_id, concept in book_concepts.items():
        score = 0
        searchable_text = f"{concept.get('topic', '')} {concept.get('explanation', '')} {concept.get('syntax', '')} {' '.join(concept.get('code_example', []))}"
        text_lower = searchable_text.lower()
        
        for term in query_terms:
            if term in text_lower:
                if term in concept.get('topic', '').lower():
                    score += 10
                elif term in concept.get('explanation', '').lower():
                    score += 5
                else:
                    score += 2
        
        if score > 0:
            scored_results.append((score, concept))
    
    # Sort and limit
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
        "book_name": book_name,
        "book_title": books_metadata[book_name]
    }

@mcp.tool()
def list_books_and_stats() -> Dict:
    """
    List all books with concept statistics
    
    Returns:
        Book information and statistics including CSAPP
    """
    concepts = load_all_concepts()
    
    book_stats = {}
    total_concepts = 0
    
    for book_name, book_concepts in concepts.items():
        concept_count = len(book_concepts)
        total_concepts += concept_count
        
        # Sample topics
        sample_topics = [concept.get('topic', 'Unknown') for concept in list(book_concepts.values())[:3]]
        
        book_stats[book_name] = {
            "title": books_metadata[book_name],
            "concept_count": concept_count,
            "sample_topics": sample_topics,
            "status": "loaded" if concept_count > 0 else "no_concepts"
        }
    
    return {
        "books": book_stats,
        "total_books": len(books_metadata),
        "total_concepts": total_concepts,
        "newest_addition": "csapp_2016",
        "book_focus_areas": {
            "kernighan_ritchie": "C language fundamentals",
            "unix_env": "UNIX system programming",
            "linkers_loaders": "Binary linking and loading",
            "os_three_pieces": "Operating systems concepts",
            "expert_c_programming": "Advanced C techniques",
            "csapp_2016": "Computer systems and architecture"
        }
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Main Programming Concepts Server")
    logger.info(f"📚 Supporting {len(books_metadata)} books including CSAPP")
    
    # Load all concepts
    concepts = load_all_concepts()
    total = sum(len(book_concepts) for book_concepts in concepts.values())
    logger.info(f"✅ Ready with {total} concepts from {len(concepts)} books")
    
    mcp.run()
