# cppfind - C++ Concept Search System Documentation

## Overview

`cppfind` is a semantic search tool for C++ programming concepts extracted from technical books. It uses sentence transformers to find relevant concepts based on natural language queries.

## Architecture

### Core Components

1. **Search Interface**: `scripts/cpp_search.py`
   - CLI tool using `questionary` for interactive search
   - Rich terminal UI with syntax highlighting
   - Top-K retrieval with similarity scoring
   - **NEW**: Interactive AI chat about selected concepts

2. **Index Builder**: `scripts/build_concept_index.py`
   - Creates searchable embeddings from concept JSON files
   - Uses `sentence-transformers` model: `all-MiniLM-L6-v2`
   - Outputs pickle file with concepts + embeddings

3. **Concept Storage**: `data/concepts/*.json`
   - Each JSON file contains:
     - `id`: Unique identifier (from filename)
     - `topic`: Clean concept title for display
     - `keywords`: Optional comma-separated searchable terms (improves search matching)
     - `book`: Source book
     - `explanation`: Detailed explanation
     - `code_example`: Optional code snippet
     - `extraction_metadata`: Source tracking

4. **Search Index**: `data/concept_index.pkl`
   - Pickled dictionary containing:
     - `concepts`: List of concept metadata dicts
     - `embeddings`: NumPy array (N x 384 dimensions)
     - `model_name`: Embedding model used

5. **AI Chat Integration** (NEW)
   - Uses Google Gemini 2.5 Flash for concept tutoring
   - Pre-loads concept context invisibly into system prompt
   - Streaming responses with Rich UI
   - Auto-loads API key from `apikeys.env` via python-dotenv

### File Locations (Absolute Paths)

```
BASE_DIR = /home/shahar42/Suumerizing_C_holy_grale_book/

Concepts:     rag_finetune/data/concepts/*.json
Index:        rag_finetune/data/concept_index.pkl
Metadata:     rag_finetune/data/concept_metadata.json
Book Config:  rag_finetune/config/book_config.json
```

## Data Flow Pipeline

### 1. Book Processing → Concept Extraction
```
PDF → factory/scripts/book_processor.py → factory/output/<book_name>/*.json
```

### 2. Deduplication & Renaming
```
factory/output/<book>/*.json → scripts/deduplicate_and_rename_emcpp.py → Unique titles
```

### 3. Integration into Main Database
```
factory/output/<book>/*.json → factory/scripts/batch_integrate.py → data/concepts/*.json
```
**Critical**: `batch_integrate.py` SKIPS existing files (line 72-76)
- If concepts already exist in `data/concepts/`, they won't be updated
- Must delete old files OR modify integration script to force overwrite

### 4. Index Building
```
data/concepts/*.json → scripts/build_concept_index.py → data/concept_index.pkl
```
**Requirements**:
- Must run from BASE_DIR: `/home/shahar42/Suumerizing_C_holy_grale_book/`
- Uses relative path: `CONCEPTS_DIR = Path("rag_finetune/data/concepts")`
- Generates embeddings for all concept files (384-dim vectors)

### 5. Search & Interaction
```
User query → cpp_search.py → cosine_similarity(query_embedding, index_embeddings) → Top-K results
    ↓
Select concept → View details
    ↓
Choose action:
  - Chat about concept (AI tutor with pre-loaded context)
  - View code example
  - Open manpage (POSIX)
  - Back to results
```

## Interactive Chat Feature

### Overview
The chat feature provides an AI-powered tutor that has full knowledge of the selected concept without the user needing to provide context.

### Implementation Details

**File**: `scripts/cpp_search.py` - `chat_about_concept()` function

**Flow**:
1. User selects "Chat about this concept" from detail menu
2. System builds hidden context from concept JSON:
   - Topic, explanation, syntax, code examples
   - Book source and metadata
3. Initializes Gemini 2.5 Flash with system instruction containing full concept
4. Starts interactive chat loop with streaming responses
5. User can ask follow-up questions with full context awareness
6. Type 'exit' or 'quit' to return to concept detail view

**Key Features**:
- **Hidden Context**: Concept data pre-loaded into system prompt (user doesn't know)
- **Streaming UI**: Token-by-token responses using Rich Live display
- **Guru Mode**: AI responds with concise, dense technical answers
- **Auto API Key Loading**: Reads `GEMINI_API_KEY` from `apikeys.env` via python-dotenv

**Configuration**:
```bash
# Create API key file (one-time setup)
echo 'export GEMINI_API_KEY="your-key-here"' > rag_finetune/apikeys.env

# No need to source manually - script auto-loads via dotenv
python3 rag_finetune/scripts/cpp_search.py
```

### Example Chat Session
```
> Chat about this concept

Chat about: The 'new operator' vs 'operator new' Distinction
Type 'exit' or 'quit' to return to menu

> You: What's the key difference?
Assistant: The 'new operator' (the expression `new Widget`) does two things:
calls operator new to allocate memory, then constructs the object.
operator new is just the allocation function, like malloc...

Type 'q' or 'exit' to return to menu

> You: exit
Exiting chat...
```

## Common Issues & Solutions

### Issue 1: Old Titles Showing in Search Results

**Symptom**: Search shows duplicate or outdated concept titles

**Root Cause**: Stale pickle index caching old concept data

**Solution**:
```bash
# 1. Ensure renamed concepts are in data/concepts/
cp factory/output/<book_complete>/*.json data/concepts/

# 2. Delete stale index
rm rag_finetune/data/concept_index.pkl

# 3. Rebuild from BASE_DIR
cd /home/shahar42/Suumerizing_C_holy_grale_book/
python3 rag_finetune/scripts/build_concept_index.py
```

### Issue 2: Index Builder Shows 0 Concepts

**Symptom**: `✅ Loaded 0 concepts` when running build_concept_index.py

**Root Cause**: Running from wrong directory - relative paths fail

**Solution**: Always run from BASE_DIR:
```bash
cd /home/shahar42/Suumerizing_C_holy_grale_book/
python3 rag_finetune/scripts/build_concept_index.py
```

### Issue 3: batch_integrate.py Skips Updated Files

**Symptom**: Renamed concepts don't appear after running batch_integrate

**Root Cause**: Script skips files that already exist (line 72-76):
```python
if dest_file.exists():
    print(f"⚠️  Skipping duplicate: {concept_file.name}")
    continue
```

**Solution**: Delete old files first OR modify script to force overwrite
```bash
# Option 1: Delete specific book's concepts
cd data/concepts
rm emcpp_*.json  # For Effective Modern C++

# Option 2: Direct copy (if no naming conflicts)
cp factory/output/<book>/*.json data/concepts/
```

## Index Statistics

Current index (`concept_metadata.json`):
- **Total concepts**: 2849
- **Embedding dimensions**: 384
- **Index size**: ~9 MB
- **Books indexed**: 12 (including EMCPP, C++ Primer, Inside the C++ Object Model, etc.)

## Naming Conventions

### Concept File Names

**Effective Modern C++**:
```
emcpp_<category>_<descriptive_name>_<6-char-hash>.json

Examples:
- emcpp_async_async_future_behavior__blocking_43799f.json
- emcpp_auto_auto_type_deduction_proxy_types_8a9f2c.json
```

**Other Books**:
```
<book_prefix>_<category>_<descriptive_name>_<6-char-hash>.json

Examples:
- cppx_func_function_pointer_callbacks_for_custom_op_0b7c2e.json
- objmdl_object_memory_layout_in_c_inheritance_2a01d9.json
```

**Legacy Format** (deprecated):
```
concept_NNN_<short_description>.json
```

### Title Format After Deduplication

Pattern: `[Main Concept]: [Specific Context/Issue]`

Examples:
- "Decltype(auto) Return: Dangling Reference Hazard"
- "Decltype Auto: Perfect Return Type Forwarding"
- "Trailing Return Syntax: Decltype Parameter Access"

## Search Performance

- **Model**: `all-MiniLM-L6-v2` (80MB, fast inference)
- **Similarity**: Cosine similarity on 384-dim embeddings
- **Search fields**: Embeddings generated from `topic` + `keywords` + `explanation`
- **Display**: Shows clean `topic` field only (keywords hidden from UI)
- **Top-K**: Fetches 50 results, displays 10 by default
- **Rebuild time**: ~3 minutes for 2849 concepts

## Keywords Enhancement (Added 2025-10-30)

### Purpose
The `keywords` field improves search matching by including common terms, abbreviations, and alternative names that users might search for.

### Implementation
- **Generation**: Auto-generated using Gemini 2.5 Flash API analyzing topic + explanation
- **Format**: Comma-separated string of 2-4 searchable terms
- **Storage**: Separate `keywords` field in concept JSON (not part of display title)
- **Search**: Keywords are embedded along with topic and explanation for semantic matching
- **Display**: UI shows only clean `topic` field; keywords remain hidden

### Example
```json
{
  "topic": "Virtual Function Table (vtable) Mechanism",
  "keywords": "vtable, dynamic dispatch, virtual functions, vptr"
}
```

When users search "vtable" or "dynamic dispatch", this concept will match better due to the keywords field.

## Deduplication Strategy

Script: `scripts/deduplicate_and_rename_emcpp.py`

### Phase 1: Exact Duplicates
- Hash content (explanation + code)
- Delete files with 100% identical content
- Keep first occurrence only

### Phase 2: Title Duplicates
- Find concepts with same title but different content
- Use Gemini API to generate specific unique titles
- Pattern: Add context to distinguish concepts
- Rate limit: 0.5s between API calls

Usage:
```bash
# Dry run (preview changes)
python3 scripts/deduplicate_and_rename_emcpp.py --dry-run

# Execute changes
python3 scripts/deduplicate_and_rename_emcpp.py

# Skip phases
python3 scripts/deduplicate_and_rename_emcpp.py --skip-delete  # Only rename
python3 scripts/deduplicate_and_rename_emcpp.py --skip-rename  # Only delete
```

## Data Philosophy: Single Source of Truth

**Principle**: "When the same data exists at 2 different places it will soon become not the same data"

This system follows strict data integrity rules:

1. **Single Source Files**: Each concept exists in ONE file only
   - Factory output (`factory/output/<book>/`) is the authoritative source
   - `data/concepts/` is a deployment/integration copy
   - Never maintain same content in multiple places

2. **Single Source of Code Examples**: Code examples live in concept files, not separate databases
   - Each concept JSON has optional `code_example` field
   - No external code example database
   - Integration happens once: code → concept file → never separate again

3. **Generated Artifacts Are Disposable**:
   - Search index (`concept_index.pkl`) can always be regenerated
   - Cache files can be deleted and rebuilt
   - Only source JSON files in factory/output are precious

4. **Deduplication Is Mandatory**: Run after every book extraction
   - Exact title duplicates must be removed immediately
   - Use quality scoring to keep best version
   - Delete inferior copies without hesitation

## Best Practices

1. **Always run index builder from BASE_DIR**
   ```bash
   cd /home/shahar42/Suumerizing_C_holy_grale_book/
   python3 rag_finetune/scripts/build_concept_index.py
   ```

2. **After deduplication, use direct copy instead of batch_integrate**
   ```bash
   # Safer for updates - no skip logic
   cp factory/output/<book_complete>/*.json data/concepts/
   ```

3. **Run deduplication after integration**
   ```bash
   # Preview duplicates
   python3 rag_finetune/scripts/remove_100_percent_title_duplicates.py --dry-run

   # Execute removal (with auto-confirm)
   python3 rag_finetune/scripts/remove_100_percent_title_duplicates.py --yes
   ```

4. **Rebuild index after ANY changes to concept files**
   ```bash
   rm rag_finetune/data/concept_index.pkl
   python3 rag_finetune/scripts/build_concept_index.py
   ```

5. **Verify index contents before using search**
   ```python
   import pickle
   data = pickle.load(open('rag_finetune/data/concept_index.pkl', 'rb'))
   print(f"Total concepts: {len(data['concepts'])}")
   # Check specific book
   emcpp = [c for c in data['concepts'] if 'Effective Modern' in c['book']]
   print(f"EMCPP concepts: {len(emcpp)}")
   ```

6. **Keep factory/output as source of truth**
   - All manual edits/renames should happen in `factory/output/<book>/`
   - `data/concepts/` is deployment destination
   - Index is generated artifact (can be rebuilt)

## Troubleshooting Checklist

When search shows wrong results:

- [ ] Check which index file search is using (`INDEX_FILE` in cpp_search.py)
- [ ] Verify concept files exist in `data/concepts/`
- [ ] Check index was rebuilt from correct directory
- [ ] Inspect pickle contents to confirm concepts are updated
- [ ] Verify no duplicate files with old names
- [ ] Check index file timestamp matches rebuild time

## Complete Workflow: Adding a New Book

Follow this exact sequence to maintain data integrity:

```bash
# 1. Extract concepts from PDF
cd /home/shahar42/Suumerizing_C_holy_grale_book
python3 rag_finetune/factory/scripts/book_processor.py <pdf_file>

# 2. Run book-specific deduplication (if exists)
python3 rag_finetune/scripts/deduplicate_and_rename_emcpp.py --dry-run
python3 rag_finetune/scripts/deduplicate_and_rename_emcpp.py

# 3. Copy to main concepts database
cp factory/output/<book_complete>/*.json rag_finetune/data/concepts/

# 4. Remove 100% exact title duplicates
python3 rag_finetune/scripts/remove_100_percent_title_duplicates.py --dry-run
python3 rag_finetune/scripts/remove_100_percent_title_duplicates.py --yes

# 5. Rebuild search index
rm rag_finetune/data/concept_index.pkl
python3 rag_finetune/scripts/build_concept_index.py

# 6. Verify search works
cppfind "test query from new book"
```

**Critical**: Never skip step 4. Duplicates corrupt search results.

## Future Improvements

1. **Absolute paths in build_concept_index.py** - Avoid directory dependency
2. **Force-overwrite flag in batch_integrate.py** - Handle updates cleanly
3. **Index versioning** - Track which concept files were indexed
4. **Incremental indexing** - Update only changed concepts
5. **Search result caching** - Speed up repeated queries
6. **Multi-stage search** - Combine semantic + keyword matching
