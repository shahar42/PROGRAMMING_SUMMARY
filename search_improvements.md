# Search Improvements for MCP Programming Concepts Server

## Problem
The fuzzy search is incorrectly expanding "mmap" to include "map" and returning C++ container results (std::map, std::multimap) instead of the mmap system call. This happens because the fuzzy matching treats "mmap" as a variant of "map".

## Root Cause
- Fuzzy matching is too aggressive: "mmap" → "map" → "std::map, std::multimap..."
- No domain knowledge to distinguish system calls from C++ containers
- No source prioritization for syscall-related queries

## Smart Solutions

### 1. Exact Match Priority
If search term exactly matches a known syscall name, prioritize those results:

```python
SYSCALL_NAMES = {
    "mmap", "munmap", "open", "close", "read", "write", "fork", "exec",
    "pipe", "dup", "dup2", "fcntl", "ioctl", "select", "poll", "epoll",
    "socket", "bind", "listen", "accept", "connect", "send", "recv",
    "malloc", "free", "brk", "sbrk", "mprotect", "msync"
}

def search_concepts(query, limit=10):
    # Exact match priority
    if query.lower() in SYSCALL_NAMES:
        exact_results = find_exact_matches(query)
        if exact_results:
            return prioritize_posix_sources(exact_results)
```

### 2. Source Priority Weighting
Weight results by source when fuzzy matching occurs:

```python
SOURCE_WEIGHTS = {
    "posix_manpages": 10,    # Highest for syscalls
    "csapp_2016": 8,         # Systems programming book
    "unix_env": 8,           # UNIX programming
    "os_three_pieces": 6,    # OS concepts
    "cpp_standard": 2,       # Lower for C++ when searching syscalls
    "cpp_primer": 2          # Lower for C++ when searching syscalls
}

def score_result(result, query):
    base_score = similarity_score(result, query)
    source_weight = SOURCE_WEIGHTS.get(result.source, 5)
    return base_score * source_weight
```

### 3. Fuzzy Expansion Blacklist
Prevent problematic fuzzy expansions:

```python
FUZZY_BLACKLIST = {
    "mmap": ["map"],         # Don't expand mmap to map
    "munmap": ["map"],       # Don't expand munmap to map
    "fork": ["work"],        # Don't expand fork to work
    "exec": ["execute"],     # Don't expand exec to execute
    "pipe": ["pipeline"],    # Don't expand pipe to pipeline
}

def expand_search_terms(query):
    if query in FUZZY_BLACKLIST:
        # Return only the original term, no expansion
        return [query]
    else:
        # Normal fuzzy expansion
        return fuzzy_expand(query)
```

### 4. Two-Stage Search
Try exact match first, then fuzzy search:

```python
def search_concepts(query, limit=10):
    # Stage 1: Exact match
    exact_results = find_exact_matches(query)
    if len(exact_results) >= limit // 2:  # If we have good exact matches
        return exact_results[:limit]

    # Stage 2: Fuzzy search to fill remaining slots
    fuzzy_results = fuzzy_search(query)
    combined = exact_results + fuzzy_results
    return deduplicate(combined)[:limit]
```

## Recommended Implementation

Combine approaches #1 and #3 for maximum impact with minimal complexity:

```python
# Easy fixes that solve 90% of syscall search issues

SYSCALL_NAMES = {"mmap", "munmap", "open", "close", "fork", "exec", "pipe", ...}
FUZZY_BLACKLIST = {"mmap": ["map"], "fork": ["work"], "exec": ["execute"]}

def search_concepts(query, limit=10):
    # Exact syscall match gets priority
    if query.lower() in SYSCALL_NAMES:
        results = find_exact_matches(query)
        posix_results = [r for r in results if "posix" in r.source.lower()]
        other_results = [r for r in results if "posix" not in r.source.lower()]
        return (posix_results + other_results)[:limit]

    # Prevent problematic fuzzy expansion
    if query in FUZZY_BLACKLIST:
        search_terms = [query]
    else:
        search_terms = fuzzy_expand(query)

    # Continue with normal search logic...
```

## Files to Modify
- `search.py` or `concept_search.py` in the MCP server
- Where `mcp__programming-concepts__search_concepts` is implemented
- Add the syscall names list and blacklist as constants
- Modify the search and ranking logic

## Expected Improvement
- "mmap" queries will return POSIX mmap documentation first
- No more C++ container pollution in syscall searches
- Maintains fuzzy search benefits for legitimate use cases
- Simple implementation requiring minimal code changes