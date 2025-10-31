# C/C++ Concept Search System

Interactive semantic search over your C/C++ concept database.

## Quick Start

### 1. Install Dependencies

```bash
cd /home/shahar42/Suumerizing_C_holy_grale_book
pip install -r rag_finetune/requirements_search.txt
```

### 2. Build Search Index (One-time setup)

```bash
python rag_finetune/scripts/build_concept_index.py
```

This will:
- Load all 4,483 concepts from `outputs/`
- Generate semantic embeddings (using all-MiniLM-L6-v2, ~80MB model)
- Save index to `rag_finetune/data/concept_index.pkl`
- Takes ~5-10 minutes

### 3. Search Concepts

```bash
# Interactive mode
python rag_finetune/scripts/cpp_search.py

# Direct query
python rag_finetune/scripts/cpp_search.py "what is RAII?"
```

## Usage Examples

```bash
$ python rag_finetune/scripts/cpp_search.py "malloc vs new"

Search Results:

[1] Memory allocation with malloc and new (cpp_primer) - 95% match
[2] Dynamic memory management (cpp_primer) - 87% match
[3] RAII and resource management (cpp_primer) - 72% match

Select a concept to view details, then choose:
- Chat about this concept (interactive AI tutor)
- View Code Example
- Open Manpage (for POSIX calls)
- Back to Results
```

## New Feature: Interactive Chat

After selecting a concept, you can now chat with an AI tutor about it:

```bash
> Chat about this concept

Chat about: The 'new operator' vs 'operator new' Distinction
Type 'exit' or 'quit' to return to menu

> You: Can you explain this with a simple example?
Assistant: [Streaming response with context-aware explanation...]

> You: What are common mistakes?
Assistant: [Context-aware answer about the concept...]
```

The chat feature:
- Pre-loads the concept (explanation, code examples) into AI context invisibly
- Provides concise, dense technical answers
- Uses Gemini 2.5 Flash for fast responses
- Automatically loads API key from `rag_finetune/apikeys.env`

## How It Works

1. **Indexing**: Concepts are embedded using sentence-transformers
   - Embeddings generated from `topic` + `keywords` + `explanation` fields
   - Keywords field contains searchable terms (abbreviations, alternative names)
2. **Search**: Your query is embedded and compared via cosine similarity
3. **Ranking**: Results sorted by semantic relevance
4. **Display**: Interactive selection showing clean concept titles (keywords hidden)

## Files

- `scripts/build_concept_index.py` - Build searchable index
- `scripts/cpp_search.py` - Interactive search CLI
- `data/concept_index.pkl` - Pre-computed embeddings (~50MB)
- `data/concept_metadata.json` - Index statistics

## Search Enhancement: Keywords Field

Most concepts now include a `keywords` field with searchable terms:
- **Purpose**: Improves matching for abbreviations (vtable, RAII) and alternative names
- **Auto-generated**: Uses Gemini 2.5 Flash to analyze concepts and extract 2-4 key terms
- **Invisible to users**: Keywords are used for search but not shown in UI

Example: Searching "vtable" will match concepts with "Virtual Function Table" in the title because the keywords field contains "vtable, dynamic dispatch, vptr".

## Next Steps (If Retrieval Quality Needs Further Improvement)

1. **Add reranker model** - Use small LLM to rerank top-20 results
2. **Fine-tune embeddings** - Train on your specific domain
3. **Expand keywords** - Add more alternative terms to existing concepts
