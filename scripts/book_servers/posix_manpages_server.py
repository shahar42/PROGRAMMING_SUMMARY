#!/usr/bin/env python3
"""
POSIX Man Pages MCP Server - FIXED VERSION
Specialized server for POSIX system call reference and API documentation

SURGICAL FIXES IMPLEMENTED:
1. Complete search implementation with relevance scoring
2. JSON validation to prevent malformed data issues  
3. Functional categorization system for syscall browsing

Optimized for reference queries rather than learning - provides quick parameter
lookups, error code meanings, and related syscall cross-references.
"""

import json
import logging
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
sys.path.append(PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("posix-manpages-server")

# Initialize FastMCP server
mcp = FastMCP("posix-manpages")

# Global storage for POSIX system calls
syscalls = {}
syscalls_loaded = False
syscall_categories = {}

def validate_syscall_structure(syscall_data: Dict) -> bool:
    """
    SURGICAL FIX #2: JSON validation to prevent malformed data issues
    
    Validates that syscall JSON has required fields and proper structure
    """
    required_fields = ['name', 'description', 'synopsis']
    
    try:
        # Check required fields exist
        for field in required_fields:
            if field not in syscall_data:
                logger.warning(f"Missing required field: {field}")
                return False
                
        # Validate field types
        if not isinstance(syscall_data['name'], str):
            logger.warning(f"Invalid name type: {type(syscall_data['name'])}")
            return False
            
        if not isinstance(syscall_data['description'], str):
            logger.warning(f"Invalid description type: {type(syscall_data['description'])}")
            return False
            
        if not isinstance(syscall_data['synopsis'], list):
            logger.warning(f"Invalid synopsis type: {type(syscall_data['synopsis'])}")
            return False
            
        # Validate optional fields if present
        if 'parameters' in syscall_data and not isinstance(syscall_data['parameters'], list):
            logger.warning(f"Invalid parameters type: {type(syscall_data['parameters'])}")
            return False
            
        if 'errors' in syscall_data and not isinstance(syscall_data['errors'], list):
            logger.warning(f"Invalid errors type: {type(syscall_data['errors'])}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False

def categorize_syscall(syscall_data: Dict) -> Set[str]:
    """
    SURGICAL FIX #3: Dynamic categorization based on syscall functionality
    
    Analyzes syscall name and description to determine functional categories
    """
    categories = set()
    name = syscall_data.get('name', '').lower()
    description = syscall_data.get('description', '').lower()
    synopsis = ' '.join(syscall_data.get('synopsis', [])).lower()
    
    # All text for analysis
    full_text = f"{name} {description} {synopsis}"
    
    # File Operations
    file_keywords = ['file', 'open', 'close', 'read', 'write', 'seek', 'stat', 'access', 
                    'chmod', 'chown', 'link', 'unlink', 'rename', 'truncate', 'sync',
                    'fcntl', 'ioctl', 'select', 'poll', 'epoll']
    if any(keyword in full_text for keyword in file_keywords):
        categories.add('File Operations')
    
    # Process Control
    process_keywords = ['process', 'fork', 'exec', 'exit', 'wait', 'kill', 'signal',
                       'pid', 'thread', 'clone', 'vfork', 'getpid', 'setpid']
    if any(keyword in full_text for keyword in process_keywords):
        categories.add('Process Control')
    
    # Memory Management  
    memory_keywords = ['memory', 'mmap', 'munmap', 'mlock', 'brk', 'sbrk', 'malloc',
                      'mprotect', 'msync', 'madvise', 'memfd']
    if any(keyword in full_text for keyword in memory_keywords):
        categories.add('Memory Management')
    
    # Networking
    network_keywords = ['socket', 'bind', 'listen', 'accept', 'connect', 'send', 'recv',
                       'network', 'tcp', 'udp', 'ip', 'address']
    if any(keyword in full_text for keyword in network_keywords):
        categories.add('Networking')
    
    # Time and Scheduling
    time_keywords = ['time', 'clock', 'timer', 'sleep', 'alarm', 'schedule', 'priority',
                    'nice', 'nanosleep', 'gettimeofday']
    if any(keyword in full_text for keyword in time_keywords):
        categories.add('Time & Scheduling')
    
    # System Information
    sysinfo_keywords = ['system', 'uname', 'sysinfo', 'getrlimit', 'setrlimit', 'ulimit',
                       'getrusage', 'times', 'sysconf']
    if any(keyword in full_text for keyword in sysinfo_keywords):
        categories.add('System Information')
    
    # Inter-Process Communication
    ipc_keywords = ['pipe', 'fifo', 'shm', 'sem', 'msg', 'ipc', 'shared', 'message',
                   'semaphore', 'mutex']
    if any(keyword in full_text for keyword in ipc_keywords):
        categories.add('Inter-Process Communication')
    
    # Architecture Specific
    arch_keywords = ['arch', 'x86', 'cpuid', 'prctl', 'ptrace', 'personality']
    if any(keyword in full_text for keyword in arch_keywords):
        categories.add('Architecture Specific')
    
    # Unimplemented/Obsolete
    if 'unimplemented' in full_text or 'obsolete' in full_text or 'enosys' in full_text:
        categories.add('Unimplemented/Obsolete')
    
    # Default category if none found
    if not categories:
        categories.add('Miscellaneous')
    
    return categories

def calculate_search_relevance(syscall_data: Dict, query_terms: List[str]) -> float:
    """
    SURGICAL FIX #1: Calculate relevance score for search ranking
    
    Scores syscalls based on how well they match the query terms
    """
    score = 0.0
    name = syscall_data.get('name', '').lower()
    description = syscall_data.get('description', '').lower()
    synopsis = ' '.join(syscall_data.get('synopsis', [])).lower()
    
    for term in query_terms:
        term = term.lower().strip()
        if not term:
            continue
            
        # Exact name match gets highest score
        if term == name:
            score += 10.0
            
        # Name contains term gets high score  
        elif term in name:
            score += 7.0
            
        # Synopsis contains term gets medium score
        elif term in synopsis:
            score += 5.0
            
        # Description contains term gets lower score
        elif term in description:
            score += 3.0
            
        # Parameters contain term
        params_text = ' '.join([
            f"{p.get('name', '')} {p.get('type', '')} {p.get('description', '')}"
            for p in syscall_data.get('parameters', [])
        ]).lower()
        if term in params_text:
            score += 2.0
            
        # Related calls contain term
        related_text = ' '.join(syscall_data.get('related_calls', [])).lower()
        if term in related_text:
            score += 1.0
    
    # Boost score for partial matches in name
    for term in query_terms:
        if term and any(term.lower() in part for part in name.split('_')):
            score += 2.0
    
    return score

def load_posix_syscalls():
    """
    Load all POSIX system calls from JSON files with validation
    INCLUDES ALL THREE SURGICAL FIXES
    """
    global syscalls, syscalls_loaded, syscall_categories
    
    if syscalls_loaded:
        return syscalls
    
    syscalls_dir = Path(PROJECT_ROOT) / "outputs" / "posix_manpages"
    
    if not syscalls_dir.exists():
        logger.warning(f"POSIX syscalls directory not found: {syscalls_dir}")
        return {}
    
    json_files = list(syscalls_dir.glob("unix_*.json"))
    logger.info(f"Found {len(json_files)} POSIX system call files")
    
    valid_syscalls = 0
    invalid_syscalls = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                syscall_data = json.load(f)
            
            # SURGICAL FIX #2: Validate JSON structure
            if not validate_syscall_structure(syscall_data):
                logger.warning(f"Invalid syscall structure in {json_file}, skipping")
                invalid_syscalls += 1
                continue
            
            # Use syscall name as key for fast lookups
            syscall_name = syscall_data.get('name', json_file.stem.replace('unix_', ''))
            
            # Add file metadata for reference
            syscall_data['source_file'] = json_file.name
            syscall_data['syscall_id'] = syscall_name
            
            # SURGICAL FIX #3: Categorize syscall
            categories = categorize_syscall(syscall_data)
            syscall_data['categories'] = list(categories)
            
            # Add to category index
            for category in categories:
                if category not in syscall_categories:
                    syscall_categories[category] = []
                syscall_categories[category].append(syscall_name)
            
            syscalls[syscall_name] = syscall_data
            valid_syscalls += 1
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            invalid_syscalls += 1
            continue
        except Exception as e:
            logger.error(f"Error loading syscall {json_file}: {e}")
            invalid_syscalls += 1
            continue
    
    syscalls_loaded = True
    logger.info(f"✅ Loaded {valid_syscalls} valid POSIX system calls")
    if invalid_syscalls > 0:
        logger.warning(f"⚠️ Skipped {invalid_syscalls} invalid syscall files")
    
    return syscalls

@mcp.tool()
def search_syscalls(query: str, limit: int = 10) -> str:
    """
    SURGICAL FIX #1: Complete search implementation with relevance scoring
    
    Search POSIX system calls by name, functionality, or description
    Optimized for API reference queries
    
    Args:
        query: Search terms (e.g., "epoll", "file", "network", "process")
        limit: Maximum results to return
    """
    syscalls_data = load_posix_syscalls()
    
    if not syscalls_data:
        return "No POSIX system calls loaded. Run the extractor first."
    
    if not query.strip():
        return "Please provide a search query. Examples: 'epoll', 'file operations', 'memory'"
    
    # Parse query into terms
    query_terms = [term.strip() for term in query.split()]
    
    # Calculate relevance scores for all syscalls
    scored_results = []
    for syscall_name, syscall_data in syscalls_data.items():
        score = calculate_search_relevance(syscall_data, query_terms)
        if score > 0:  # Only include results with some relevance
            scored_results.append((score, syscall_name, syscall_data))
    
    # Sort by relevance score (highest first)
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # Format results
    if not scored_results:
        return f"No system calls found matching '{query}'. Try broader terms like 'file', 'process', or 'network'."
    
    result = f"# POSIX System Call Search Results for '{query}'\n\n"
    result += f"Found {len(scored_results)} matching system calls (showing top {min(limit, len(scored_results))}):\n\n"
    
    for i, (score, syscall_name, syscall_data) in enumerate(scored_results[:limit], 1):
        description = syscall_data.get('description', 'No description available')
        categories = ', '.join(syscall_data.get('categories', ['Uncategorized']))
        
        # Truncate long descriptions
        if len(description) > 150:
            description = description[:150] + "..."
        
        result += f"## {i}. `{syscall_name}()` (Relevance: {score:.1f})\n"
        result += f"**Categories**: {categories}\n\n"
        result += f"{description}\n\n"
        
        # Show synopsis if it's a high-relevance match
        if score >= 5.0:
            synopsis = syscall_data.get('synopsis', [])
            if synopsis:
                result += f"**Synopsis**: `{synopsis[0]}`\n\n"
        
        result += f"*Use `get_syscall_details('{syscall_name}')` for complete documentation*\n\n"
        result += "---\n\n"
    
    # Add category suggestions for broader searches
    if len(scored_results) > limit:
        result += f"💡 **Tip**: {len(scored_results) - limit} more results available. "
        result += "Try `list_syscall_categories()` to browse by functional area.\n"
    
    return result

@mcp.tool()
def get_syscall_details(syscall_name: str) -> str:
    """
    Get complete documentation for a specific POSIX system call
    
    Args:
        syscall_name: Name of the system call (e.g., "open", "fork", "mmap")
    """
    syscalls_data = load_posix_syscalls()
    
    # Case-insensitive lookup
    syscall = None
    for key, data in syscalls_data.items():
        if key.lower() == syscall_name.lower():
            syscall = data
            break
    
    if not syscall:
        available = list(syscalls_data.keys())[:10]
        return f"System call '{syscall_name}' not found.\n\nAvailable syscalls (first 10): {', '.join(available)}\n\nUse `search_syscalls('{syscall_name}')` to find similar calls."
    
    # Format complete documentation
    result = f"# {syscall['name']}() - POSIX System Call\n\n"
    
    # Categories
    categories = syscall.get('categories', ['Uncategorized'])
    result += f"**Categories**: {', '.join(categories)}\n\n"
    
    # Synopsis
    synopsis = syscall.get('synopsis', [])
    if synopsis:
        result += "## Synopsis\n```c\n"
        for line in synopsis:
            result += f"{line}\n"
        result += "```\n\n"
    
    # Description
    description = syscall.get('description', 'No description available')
    result += f"## Description\n{description}\n\n"
    
    # Parameters
    parameters = syscall.get('parameters', [])
    if parameters:
        result += "## Parameters\n\n"
        for param in parameters:
            name = param.get('name', 'unknown')
            param_type = param.get('type', 'unknown')
            desc = param.get('description', 'No description')
            result += f"- **{name}** (`{param_type}`): {desc}\n"
        result += "\n"
    
    # Return Value
    return_value = syscall.get('return_value', {})
    if return_value:
        result += "## Return Value\n\n"
        success = return_value.get('success', 'Not documented')
        failure = return_value.get('failure', 'Not documented')
        result += f"**Success**: {success}\n\n"
        result += f"**Failure**: {failure}\n\n"
    
    # Errors
    errors = syscall.get('errors', [])
    if errors:
        result += "## Errors\n\n"
        for error in errors:
            error_code = error.get('code', 'UNKNOWN')
            error_desc = error.get('description', 'No description')
            result += f"- **{error_code}**: {error_desc}\n"
        result += "\n"
    
    # Examples
    examples = syscall.get('examples', [])
    if examples:
        result += "## Examples\n```c\n"
        for example in examples:
            result += f"{example}\n"
        result += "```\n\n"
    
    # Additional information
    bugs = syscall.get('bugs')
    if bugs:
        result += f"## Bugs\n{bugs}\n\n"
    
    versions = syscall.get('versions')
    if versions:
        result += f"## Versions\n{versions}\n\n"
    
    posix_compliance = syscall.get('posix_compliance')
    if posix_compliance:
        result += f"## POSIX Compliance\n{posix_compliance}\n\n"
    
    # Related system calls
    related_calls = syscall.get('related_calls', [])
    if related_calls:
        result += "## Related System Calls\n"
        result += ", ".join(f"`{call}()`" for call in related_calls)
        result += "\n\n"
    
    # Metadata
    extraction_meta = syscall.get('extraction_metadata', {})
    if extraction_meta:
        result += "---\n"
        result += f"*Source: {extraction_meta.get('source', 'POSIX Manual')}*\n"
        result += f"*Extracted: {extraction_meta.get('extraction_date', 'Unknown')}*"
    
    return result

@mcp.tool()
def find_related_syscalls(syscall_name: str) -> str:
    """
    Find system calls related to a given syscall based on functionality
    
    Args:
        syscall_name: Name of the system call to find relations for
    """
    syscalls_data = load_posix_syscalls()
    
    # Find the base syscall
    base_syscall = None
    for key, data in syscalls_data.items():
        if key.lower() == syscall_name.lower():
            base_syscall = data
            break
    
    if not base_syscall:
        return f"System call '{syscall_name}' not found. Use `search_syscalls('{syscall_name}')` to find it."
    
    result = f"# Related System Calls for `{base_syscall['name']}()`\n\n"
    
    # Direct relations from related_calls field
    related_calls = base_syscall.get('related_calls', [])
    if related_calls:
        result += "## Directly Related\n"
        for call in related_calls:
            if call in syscalls_data:
                desc = syscalls_data[call].get('description', 'No description')[:100]
                result += f"- **`{call}()`**: {desc}{'...' if len(desc) >= 100 else ''}\n"
            else:
                result += f"- **`{call}()`**: (Documentation not available)\n"
        result += "\n"
    
    # Category-based relations
    base_categories = set(base_syscall.get('categories', []))
    category_related = []
    
    for syscall_name_check, syscall_data in syscalls_data.items():
        if syscall_name_check == base_syscall['name']:
            continue
            
        syscall_categories = set(syscall_data.get('categories', []))
        if base_categories & syscall_categories:  # Intersection
            category_related.append((syscall_name_check, syscall_data, 
                                   len(base_categories & syscall_categories)))
    
    # Sort by category overlap
    category_related.sort(key=lambda x: x[2], reverse=True)
    
    if category_related:
        result += "## Same Category\n"
        for call_name, call_data, overlap_count in category_related[:8]:
            desc = call_data.get('description', 'No description')[:80]
            shared_cats = ', '.join(base_categories & set(call_data.get('categories', [])))
            result += f"- **`{call_name}()`** ({shared_cats}): {desc}{'...' if len(desc) >= 80 else ''}\n"
        result += "\n"
    
    if not related_calls and not category_related:
        result += "No related system calls found.\n"
    
    return result

@mcp.tool()
def list_syscall_categories() -> str:
    """
    SURGICAL FIX #3: Functional categorization implementation
    
    List all available syscall categories with counts and examples
    """
    syscalls_data = load_posix_syscalls()
    
    if not syscalls_data:
        return "No POSIX system calls loaded. Run the extractor first."
    
    result = "# POSIX System Call Categories\n\n"
    
    # Sort categories by syscall count
    sorted_categories = sorted(syscall_categories.items(), 
                             key=lambda x: len(x[1]), reverse=True)
    
    for category, syscall_list in sorted_categories:
        count = len(syscall_list)
        result += f"## {category} ({count} syscalls)\n\n"
        
        # Show first few examples
        examples = syscall_list[:5]
        for syscall_name in examples:
            if syscall_name in syscalls_data:
                desc = syscalls_data[syscall_name].get('description', 'No description')
                # Truncate description
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                result += f"- **`{syscall_name}()`**: {desc}\n"
        
        if count > 5:
            result += f"- ... and {count - 5} more\n"
        
        result += f"\n*Use `search_syscalls('{category.lower()}')` to see all {category.lower()} calls*\n\n"
        result += "---\n\n"
    
    result += f"## Summary\n"
    result += f"- **Total Categories**: {len(sorted_categories)}\n"
    result += f"- **Total System Calls**: {len(syscalls_data)}\n\n"
    result += "💡 **Tip**: Use category names as search terms, e.g., `search_syscalls('file operations')`\n"
    
    return result

@mcp.tool()
def get_error_details(error_code: str) -> str:
    """
    Get detailed information about a specific error code
    
    Args:
        error_code: Error code (e.g., "ENOENT", "EINVAL", "EACCES")
    """
    syscalls_data = load_posix_syscalls()
    
    error_code = error_code.upper().strip()
    
    # Find all syscalls that can return this error
    matching_syscalls = []
    error_descriptions = set()
    
    for syscall_name, syscall_data in syscalls_data.items():
        errors = syscall_data.get('errors', [])
        for error in errors:
            if error.get('code', '').upper() == error_code:
                matching_syscalls.append({
                    'syscall': syscall_name,
                    'description': error.get('description', 'No description')
                })
                error_descriptions.add(error.get('description', 'No description'))
    
    if not matching_syscalls:
        return f"Error code '{error_code}' not found in any system calls. Check spelling or use `search_syscalls('error')` to browse."
    
    result = f"# Error Code: {error_code}\n\n"
    
    # Show unique descriptions
    if error_descriptions:
        result += "## Description\n"
        for desc in error_descriptions:
            result += f"- {desc}\n"
        result += "\n"
    
    # List affected syscalls
    result += f"## System Calls That Can Return {error_code}\n\n"
    
    # Group by description to avoid repetition
    desc_groups = defaultdict(list)
    for match in matching_syscalls:
        desc_groups[match['description']].append(match['syscall'])
    
    for desc, syscall_names in desc_groups.items():
        if len(syscall_names) <= 3:
            syscalls_str = ', '.join(f"`{name}()`" for name in syscall_names)
        else:
            syscalls_str = ', '.join(f"`{name}()`" for name in syscall_names[:3])
            syscalls_str += f" and {len(syscall_names) - 3} more"
        
        result += f"**{syscalls_str}**: {desc}\n\n"
    
    result += f"## Total Occurrences\n"
    result += f"Found in {len(matching_syscalls)} system call contexts.\n\n"
    result += "💡 **Tip**: Use `get_syscall_details('syscall_name')` for complete error information.\n"
    
    return result

if __name__ == "__main__":
    # Load syscalls on startup for testing
    logger.info("🚀 Starting POSIX Man Pages MCP Server")
    load_posix_syscalls()
    logger.info("✅ POSIX server ready with surgical fixes applied")
    
    # Run the MCP server
    mcp.run()
