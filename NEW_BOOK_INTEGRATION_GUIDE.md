# MCP Server: New Book Integration Guide

## Overview

This guide covers all the nuanced tweaks and refactoring required when adding a new concept directory to the MCP server. It goes beyond the obvious changes like adding directory paths and covers the subtle integration points that affect search intelligence, relevance scoring, and domain-specific functionality.

---

## 1. Obvious Changes (Baseline Requirements)

### 1.1. Core Metadata
- **File**: `mcp_server.py` lines 49-61
- **Update**: `books_metadata` dictionary
```python
books_metadata = {
    # ... existing books
    "new_book_code": "New Book Full Title (Author)"
}
```

### 1.2. Authority Weighting
- **File**: `mcp_server.py` lines 64-76
- **Update**: `BOOK_AUTHORITY` dictionary with appropriate weight (1.0-3.0)
```python
BOOK_AUTHORITY = {
    # ... existing weights
    "new_book_code": 2.5,  # Adjust based on book's authority level
}
```

### 1.3. Physical Directory
- **Location**: `/outputs/new_book_code/`
- **Ensure**: Directory exists and contains valid JSON concept files

---

## 2. Search Intelligence & Context Awareness

### 2.1. Context Hints (Critical for Search Relevance)
- **File**: `mcp_server.py` lines 78-94
- **Action**: Add domain-specific keywords that should boost this book in search results

**Example for a Machine Learning book:**
```python
CONTEXT_HINTS = {
    # ... existing hints
    'neural': ['machine_learning_book', 'deep_learning_book'],
    'tensorflow': ['machine_learning_book'],
    'pytorch': ['machine_learning_book'],
    'gradient': ['machine_learning_book'],
    'backprop': ['machine_learning_book'],
    'cnn': ['machine_learning_book'],
    'rnn': ['machine_learning_book'],
    'lstm': ['machine_learning_book'],
}
```

### 2.2. Search Term Expansion (Domain-Specific Terminology)
- **File**: `mcp_server.py` lines 1035-1280+
- **Action**: Add acronyms, synonyms, and domain-specific terms

**Critical**: This is often overlooked but essential for search quality!

**Example additions for a networking book:**
```python
search_expansions = {
    # ... existing expansions

    # Networking Acronyms
    'tcp': ['transmission control protocol', 'tcp'],
    'udp': ['user datagram protocol', 'udp'],
    'ip': ['internet protocol', 'ip'],
    'http': ['hypertext transfer protocol', 'http'],
    'https': ['hypertext transfer protocol secure', 'https'],
    'ssl': ['secure sockets layer', 'ssl'],
    'tls': ['transport layer security', 'tls'],
    'dns': ['domain name system', 'dns'],
    'dhcp': ['dynamic host configuration protocol', 'dhcp'],
    'nat': ['network address translation', 'nat'],
    'vpn': ['virtual private network', 'vpn'],
    'lan': ['local area network', 'lan'],
    'wan': ['wide area network', 'wan'],
    'osi': ['open systems interconnection', 'osi model'],
    'routing': ['routing', 'route', 'router', 'routing table'],
    'switch': ['switch', 'switching', 'layer 2 switch'],
    'firewall': ['firewall', 'packet filtering', 'security gateway'],

    # Protocol Specifics
    'packet': ['packet', 'data packet', 'network packet'],
    'frame': ['frame', 'ethernet frame', 'data frame'],
    'socket': ['socket', 'network socket', 'berkeley socket'],
    'port': ['port', 'network port', 'service port'],
    'bandwidth': ['bandwidth', 'throughput', 'data rate'],
    'latency': ['latency', 'network delay', 'round trip time', 'rtt'],
}
```

---

## 3. Learning Path Integration

### 3.1. Study Paths Dictionary
- **File**: `mcp_server.py` lines 1986-2021
- **Action**: Add curated learning sequences for topics covered by the new book

**Example for a Database book:**
```python
study_paths = {
    # ... existing paths

    # Database Topics
    'database fundamentals': ['database', 'table', 'row', 'column', 'primary key', 'foreign key', 'index'],
    'sql basics': ['sql', 'select', 'insert', 'update', 'delete', 'join', 'where', 'group by'],
    'database design': ['normalization', 'schema', 'erd', 'relationship', '1nf', '2nf', '3nf'],
    'database transactions': ['transaction', 'acid', 'commit', 'rollback', 'isolation', 'consistency'],
    'database performance': ['index', 'query optimization', 'explain plan', 'performance tuning'],
    'nosql': ['nosql', 'mongodb', 'cassandra', 'document store', 'key value', 'graph database'],
}
```

### 3.2. Book Priority in Study Paths
- **File**: `mcp_server.py` lines 2047-2048
- **Action**: Add the new book to the hardcoded priority mapping

```python
book_priority = {
    # ... existing priorities
    'new_book_code': 3,  # Adjust based on foundational importance (1-5)
}
```

---

## 4. Category and Filename Convention Handling

### 4.1. Category Extraction Logic
- **File**: `mcp_server.py` lines 232-240 (`extract_category_from_filename`)
- **Review**: Ensure your new book's filename conventions work with existing logic
- **Convention**: `{book_code}_{category}_{topic}_{hash}.json`

**Categories commonly used:**
- `func` - Functions, methods
- `mem` - Memory management
- `ptr` - Pointers, references
- `op` - Operations, operators
- `io` - Input/output
- `ctrl` - Control structures
- `struct` - Data structures
- `inherit` - Inheritance
- `template` - Templates, generics

### 4.2. Special Loading Logic
- **Check**: Does your new book require special loading logic like POSIX manpages?
- **File**: `mcp_server.py` lines 306-328 (`load_posix_concepts`)
- **Action**: Add custom loader if needed (e.g., for non-standard JSON format)

---

## 5. Validation and Error Handling

### 5.1. Book Name Validation (Multiple Locations)
These functions validate book names - **all need updating**:

1. **`analyze_concept_duplicates`** (line 376-378)
2. **`cleanup_duplicate_concepts`** (line 498-500)
3. **`read_concept_resource`** (line 701-703)
4. **`search_by_book`** (line 1490-1492)

**Action**: The validation is automatic via `books_metadata.keys()`, but verify error messages are helpful.

### 5.2. Fuzzy Book Matching
- **File**: `mcp_server.py` lines 868-870
- **Note**: The fuzzy matching logic automatically includes new books, but test edge cases

---

## 6. AI-Powered Features Integration

### 6.1. Hidden Gems Discovery
- **File**: `mcp_server.py` lines 2942-2970
- **Action**: Review gem keywords to ensure your book's domain-specific terms are covered

**Example additions for a Graphics book:**
```python
gem_keywords = [
    # ... existing keywords

    # Graphics/Rendering specific
    'shader', 'vertex', 'fragment', 'pixel', 'texture', 'rasterization',
    'ray tracing', 'gpu', 'opengl', 'vulkan', 'directx', 'webgl',
    'mesh', 'polygon', 'triangle', 'vertex buffer', 'frame buffer',
    'depth buffer', 'alpha blending', 'z-buffer',
]
```

### 6.2. Concept Synthesis
- **File**: `mcp_server.py` lines 2374-2394
- **Note**: Source attribution automatically includes new books, but verify formatting

---

## 7. Testing and Verification Checklist

### 7.1. Search Functionality
- [ ] Basic search finds concepts from new book
- [ ] Context hints boost relevance correctly
- [ ] Search term expansion works for domain terms
- [ ] Category filtering works (if using new naming scheme)

### 7.2. Learning Tools
- [ ] Study paths include relevant concepts from new book
- [ ] Custom tutorial generation works for book's topics
- [ ] Reference sheet generation includes concepts
- [ ] Best practices guide synthesis works

### 7.3. Book-Specific Features
- [ ] `search_by_book` works correctly
- [ ] Book validation in all tools works
- [ ] Authority weighting affects search ranking
- [ ] URI generation works: `concept://new_book_code/topic`

### 7.4. Integration Testing
- [ ] Duplicate analysis works
- [ ] Hidden gems discovery includes book concepts
- [ ] Concept synthesis can combine with other books
- [ ] Debug tools show concepts correctly

---

## 8. Domain-Specific Considerations

### 8.1. Programming Language Books
**Additional Steps:**
- Add language-specific keywords to `CONTEXT_HINTS`
- Add syntax patterns to `search_expansions`
- Consider study path prerequisites

### 8.2. Systems/Hardware Books
**Additional Steps:**
- Add hardware acronyms to `search_expansions`
- Add architecture-specific terms
- Consider assembly/instruction patterns

### 8.3. Mathematics/Algorithm Books
**Additional Steps:**
- Add mathematical notation synonyms
- Add algorithm name variations
- Add complexity analysis terms

### 8.4. Domain-Specific Reference Books
**Additional Steps:**
- Consider special loading logic for structured data
- Add API/function name patterns
- Add parameter/return type patterns

---

## 9. Performance Considerations

### 9.1. Cache Invalidation
- **File**: Cache at `outputs/concept_cache.json`
- **Action**: Delete cache after adding new book to force rebuild

### 9.2. Index Size Impact
- Monitor concept count impact on search performance
- Consider pagination if book adds >1000 concepts

---

## 10. Documentation Updates

### 10.1. Update Integration Lists
- [ ] Update `MCP_SERVER_DOCUMENTATION.md` supported books section
- [ ] Update any example lists in documentation
- [ ] Update tool help text that mentions specific books

### 10.2. Update Examples
- [ ] Add new book to search examples
- [ ] Include in tutorial examples
- [ ] Reference in best practices if applicable

---

## Quick Reference: Files to Modify

**Always Required:**
1. `books_metadata` dictionary (line 49-61)
2. `BOOK_AUTHORITY` dictionary (line 64-76)
3. `CONTEXT_HINTS` dictionary (line 78-94)

**Usually Required:**
4. `search_expansions` dictionary (line 1035-1280+)
5. `study_paths` dictionary (line 1986-2021)
6. `book_priority` mapping (line 2047-2048)

**Sometimes Required:**
7. Special loading logic (if non-standard format)
8. `gem_keywords` list (if unique domain)
9. Custom category handling (if new filename patterns)

**Always Test:**
10. All validation functions automatically include new book
11. Search relevance and ranking
12. Learning tool integration

---

This guide ensures comprehensive integration that maintains the MCP server's intelligent search and learning capabilities when adding new concept sources.