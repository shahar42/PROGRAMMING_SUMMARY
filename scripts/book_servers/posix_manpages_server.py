#!/usr/bin/env python3
"""
POSIX Man Pages MCP Server
Specialized server for POSIX system call reference and API documentation

Optimized for reference queries rather than learning - provides quick parameter
lookups, error code meanings, and related syscall cross-references.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

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

def load_posix_syscalls():
    """Load all POSIX system calls from JSON files"""
    global syscalls, syscalls_loaded
    
    if syscalls_loaded:
        return syscalls
    
    syscalls_dir = Path(PROJECT_ROOT) / "outputs" / "posix_manpages"
    
    if not syscalls_dir.exists():
        logger.warning(f"POSIX syscalls directory not found: {syscalls_dir}")
        return {}
    
    json_files = list(syscalls_dir.glob("unix_*.json"))
    logger.info(f"Found {len(json_files)} POSIX system call files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                syscall_data = json.load(f)
            
            # Use syscall name as key for fast lookups
            syscall_name = syscall_data.get('name', json_file.stem.replace('unix_', ''))
            
            # Add file metadata for reference
            syscall_data['source_file'] = json_file.name
            syscall_data['syscall_id'] = syscall_name
            
            syscalls[syscall_name] = syscall_data
            
        except Exception as e:
            logger.error(f"Error loading syscall {json_file}: {e}")
    
    syscalls_loaded = True
    logger.info(f"✅ Loaded {len(syscalls)} POSIX system calls")
    return syscalls

@mcp.tool()
def search_syscalls(query: str, limit: int = 10) -> str:
    """
    Search POSIX system calls by name, functionality, or description
    Optimized for API reference queries
    
    Args:
        query: Search terms (e.g., "epoll", "file", "network", "process")
        limit: Maximum results to return
    """
    syscalls_data = load_posix_syscalls()
    
    if not syscalls_data:
        return "No POSIX system calls loaded. Run the extractor first."
    
    query_lower = query.lower()
    matches = []
    
    # Score syscalls by relevance
    for syscall_name, syscall_data in syscalls_data.items():
        score = 0
        
        # High score for exact name match
        if query_lower == syscall_name.lower():
            score += 100
        elif query_lower in syscall_name.lower():
            score += 50
        
        # Medium score for description match
        description = syscall_data.get('description', '').lower()
        if query_lower in description:
            score += 20
        
        # Lower score for synopsis match
        synopsis = ' '.join(syscall_data.get('synopsis', [])).lower()
        if query_lower in synopsis:
            score += 10
        
        # Score for parameter names (useful for "socket" finding bind, listen, etc.)
        parameters = syscall_data.get('parameters', [])
        for param in parameters:
            if query_lower in param.get('name', '').lower():
                score += 15
            if query_lower in param.get('description', '').lower():
                score += 8
        
        # Score for related calls
        related_calls = syscall_data.get('related_calls', [])
        for related in related_calls:
            if query_lower in related.lower():
                score += 25
        
        if score > 0:
            matches.append((score, syscall_name, syscall_data))
    
    if not matches:
        return f"No POSIX system calls found for: '{query}'"
    
    # Sort by relevance and limit results
    matches.sort(key=lambda x: x[0], reverse=True)
    top_matches = matches[:limit]
    
    result = f"Found {len(matches)} POSIX system calls for '{query}':\n\n"
    
    for i, (score, syscall_name, syscall_data) in enumerate(top_matches, 1):
        result += f"{i}. **{syscall_name}()**\n"
        
        # Show synopsis (function signature)
        synopsis = syscall_data.get('synopsis', [])
        if synopsis and len(synopsis) > 1:  # Skip just the #include
            func_sig = next((s for s in synopsis if '(' in s), synopsis[-1])
            result += f"   `{func_sig}`\n"
        
        # Show concise description
        description = syscall_data.get('description', '')
        if description:
            desc_short = description[:120] + "..." if len(description) > 120 else description
            result += f"   {desc_short}\n"
        
        # Show parameter count and error count for quick reference
        param_count = len(syscall_data.get('parameters', []))
        error_count = len(syscall_data.get('errors', []))
        result += f"   Parameters: {param_count} | Documented errors: {error_count}\n"
        
        result += "\n"
    
    result += f"Use `get_syscall_details(syscall_name)` for complete reference information."
    
    return result

@mcp.tool()
def get_syscall_details(syscall_name: str) -> str:
    """
    Get complete reference information for a specific system call
    
    Args:
        syscall_name: Name of the system call (e.g., "epoll_create1", "fork")
    """
    syscalls_data = load_posix_syscalls()
    
    # Handle variations in syscall name format
    syscall_key = None
    for key in syscalls_data.keys():
        if key.lower() == syscall_name.lower():
            syscall_key = key
            break
    
    if not syscall_key:
        available = list(syscalls_data.keys())[:10]
        return f"System call '{syscall_name}' not found.\n\nAvailable syscalls: {', '.join(available)}...\n\nUse `search_syscalls('{syscall_name}')` to find similar calls."
    
    syscall = syscalls_data[syscall_key]
    
    # Format complete reference
    result = f"# {syscall['name']}() - POSIX System Call Reference\n\n"
    
    # Synopsis section
    synopsis = syscall.get('synopsis', [])
    if synopsis:
        result += "## Synopsis\n```c\n"
        for line in synopsis:
            result += f"{line}\n"
        result += "```\n\n"
    
    # Description
    description = syscall.get('description', '')
    if description:
        result += f"## Description\n{description}\n\n"
    
    # Parameters
    parameters = syscall.get('parameters', [])
    if parameters:
        result += "## Parameters\n\n"
        for param in parameters:
            param_name = param.get('name', 'unknown')
            param_type = param.get('type', 'unknown')
            param_desc = param.get('description', 'No description')
            result += f"- **{param_name}** (`{param_type}`): {param_desc}\n"
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
    
    result = f"# Related System Calls for {base_syscall['name']}()\n\n"
    
    # Direct relationships from related_calls field
    direct_related = base_syscall.get('related_calls', [])
    if direct_related:
        result += "## Directly Related\n\n"
        for related_name in direct_related:
            if related_name in syscalls_data:
                related_syscall = syscalls_data[related_name]
                desc = related_syscall.get('description', 'No description available')
                desc_short = desc[:100] + "..." if len(desc) > 100 else desc
                result += f"- **{related_name}()**: {desc_short}\n"
            else:
                result += f"- **{related_name}()**: (not in current dataset)\n"
        result += "\n"
    
    # Find syscalls that mention this one in their related_calls
    reverse_related = []
    for name, data in syscalls_data.items():
        if name != base_syscall['name']:
            related_calls = data.get('related_calls', [])
            if base_syscall['name'] in related_calls:
                reverse_related.append((name, data))
    
    if reverse_related:
        result += "## Also Related To\n\n"
        for name, data in reverse_related:
            desc = data.get('description', 'No description available')
            desc_short = desc[:100] + "..." if len(desc) > 100 else desc
            result += f"- **{name}()**: {desc_short}\n"
        result += "\n"
    
    # Find functionally similar syscalls (same keywords in description)
    base_desc = base_syscall.get('description', '').lower()
    base_keywords = set(word for word in base_desc.split() if len(word) > 4)
    
    functionally_similar = []
    for name, data in syscalls_data.items():
        if name == base_syscall['name']:
            continue
        
        other_desc = data.get('description', '').lower()
        other_keywords = set(word for word in other_desc.split() if len(word) > 4)
        
        # Calculate keyword overlap
        overlap = len(base_keywords.intersection(other_keywords))
        if overlap >= 2:  # At least 2 shared keywords
            functionally_similar.append((overlap, name, data))
    
    if functionally_similar:
        functionally_similar.sort(key=lambda x: x[0], reverse=True)
        result += "## Functionally Similar\n\n"
        for overlap, name, data in functionally_similar[:5]:  # Top 5
            desc = data.get('description', 'No description available')
            desc_short = desc[:100] + "..." if len(desc) > 100 else desc
            result += f"- **{name}()**: {desc_short}\n"
        result += "\n"
    
    if not direct_related and not reverse_related and not functionally_similar:
        result += "No related system calls found in the current dataset.\n"
    else:
        result += "Use `get_syscall_details(syscall_name)` for complete information on any related call."
    
    return result

@mcp.tool()
def list_syscalls_by_category() -> str:
    """
    List all available POSIX system calls organized by functional category
    """
    syscalls_data = load_posix_syscalls()
    
    if not syscalls_data:
        return "No POSIX system calls loaded."
    
    # Categorize syscalls based on common patterns
    categories = {
        "File Operations": [],
        "Process Management": [], 
        "Network/Socket": [],
        "I/O Multiplexing": [],
        "Signal Handling": [],
        "Memory Management": [],
        "Time/Timer": [],
        "System Information": [],
        "Other": []
    }
    
    # Simple categorization based on syscall names and descriptions
    for name, data in syscalls_data.items():
        name_lower = name.lower()
        desc_lower = data.get('description', '').lower()
        
        if any(word in name_lower for word in ['open', 'read', 'write', 'close', 'file', 'dir', 'stat', 'access']):
            categories["File Operations"].append((name, data))
        elif any(word in name_lower for word in ['fork', 'exec', 'wait', 'exit', 'process', 'pid']):
            categories["Process Management"].append((name, data))
        elif any(word in name_lower for word in ['socket', 'bind', 'listen', 'accept', 'connect', 'send', 'recv']):
            categories["Network/Socket"].append((name, data))
        elif any(word in name_lower for word in ['epoll', 'poll', 'select', 'event']):
            categories["I/O Multiplexing"].append((name, data))
        elif any(word in name_lower for word in ['signal', 'sig', 'kill']):
            categories["Signal Handling"].append((name, data))
        elif any(word in name_lower for word in ['mmap', 'munmap', 'malloc', 'brk', 'sbrk']):
            categories["Memory Management"].append((name, data))
        elif any(word in name_lower for word in ['time', 'timer', 'sleep', 'alarm']):
            categories["Time/Timer"].append((name, data))
        elif any(word in name_lower for word in ['uname', 'getpid', 'getuid', 'sysinfo']):
            categories["System Information"].append((name, data))
        else:
            categories["Other"].append((name, data))
    
    result = f"# POSIX System Calls by Category ({len(syscalls_data)} total)\n\n"
    
    for category, syscalls_list in categories.items():
        if not syscalls_list:
            continue
            
        result += f"## {category} ({len(syscalls_list)})\n\n"
        
        for name, data in sorted(syscalls_list):
            desc = data.get('description', 'No description')
            desc_short = desc[:80] + "..." if len(desc) > 80 else desc
            result += f"- **{name}()**: {desc_short}\n"
        
        result += "\n"
    
    result += "Use `search_syscalls(category_name)` to find syscalls by functionality.\n"
    result += "Use `get_syscall_details(syscall_name)` for complete reference information."
    
    return result

@mcp.tool()
def lookup_error_code(error_code: str) -> str:
    """
    Look up what system calls can return a specific error code
    
    Args:
        error_code: Error code to look up (e.g., "EINVAL", "ENOENT")
    """
    syscalls_data = load_posix_syscalls()
    error_code_upper = error_code.upper()
    
    matching_syscalls = []
    
    for name, data in syscalls_data.items():
        errors = data.get('errors', [])
        for error in errors:
            if error.get('code', '').upper() == error_code_upper:
                matching_syscalls.append({
                    'name': name,
                    'description': error.get('description', 'No description'),
                    'syscall_desc': data.get('description', 'No description')
                })
                break
    
    if not matching_syscalls:
        return f"Error code '{error_code}' not found in current POSIX system calls dataset."
    
    result = f"# System Calls That Can Return {error_code_upper}\n\n"
    result += f"Found {len(matching_syscalls)} system calls that document this error:\n\n"
    
    for syscall_info in matching_syscalls:
        result += f"## {syscall_info['name']}()\n"
        result += f"**System call**: {syscall_info['syscall_desc']}\n"
        result += f"**{error_code_upper} meaning**: {syscall_info['description']}\n\n"
    
    result += f"Use `get_syscall_details(syscall_name)` for complete error information."
    
    return result

# Load syscalls on startup
load_posix_syscalls()

if __name__ == "__main__":
    print(f"🚀 Starting POSIX Man Pages server with {len(syscalls)} system calls")
    print("📋 Optimized for API reference queries")
    print("🔧 Tools: search_syscalls, get_syscall_details, find_related_syscalls, list_syscalls_by_category, lookup_error_code")
    mcp.run()
