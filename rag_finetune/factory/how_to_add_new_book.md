 Book Integration Process - Complete Guide

  Overview

  The system has 3 main stages:
  1. Factory Processing - Extract concepts from books using LLM
  2. Integration - Copy concepts into the main database
  3. Indexing - Make concepts searchable

  ---
  STAGE 1: Factory Processing

  Files Involved:

  - factory/books/ - Input books (PDF, TXT, MD)
  - factory/templates/ - LLM extraction prompts
  - factory/scripts/book_processor.py - Main extraction script
  - factory/output/ - Generated concepts

  Process:

  1. Add Your Book
  cp ~/Downloads/my_book.pdf rag_finetune/factory/books/

  2. Create Book Config (optional but recommended)
  cd rag_finetune/factory/books
  # Create my_book.json (same name as PDF)

  Config format:
  {
    "title": "Short Book Title",
    "full_title": "Complete Book Title (Edition)",
    "author": "Author Name",
    "category_prefix": "mybook",
    "chunk_size": 2000,
    "rate_limit_delay": 1.0,
    "extraction_template": "extraction.txt"
  }

  Key fields:
  - title: Short name for display
  - full_title: Exact title that will be stored in concept JSON (CRITICAL - must match)
  - category_prefix: Prefix for concept IDs (e.g., "mybook_mem_pointer_basics_abc123")
  - chunk_size: Text chunk size for LLM (smaller = more focused concepts)
  - extraction_template: Which prompt template to use

  3. Run Extraction
  # Set API key
  export GEMINI_API_KEY="your-key"

  # Process entire book
  python3 rag_finetune/factory/scripts/book_processor.py \
      rag_finetune/factory/books/my_book.pdf

  # Or specific pages
  python3 rag_finetune/factory/scripts/book_processor.py \
      rag_finetune/factory/books/my_book.pdf --pages 29-67

  # Or custom template
  python3 rag_finetune/factory/scripts/book_processor.py \
      rag_finetune/factory/books/my_book.pdf \
      --template effective_modern_cpp_type_deduction.txt

  What happens:
  1. book_processor.py reads the book
  2. Splits into chunks (configurable size with overlap)
  3. For each chunk:
    - Sends to Gemini LLM with extraction prompt
    - LLM returns JSON array of concepts
    - Generates unique IDs: {prefix}_{category}_{slug}_{hash}
    - Saves each concept to factory/output/{book_name}/{concept_id}.json
  4. Interactive checkpoints at 1, 3, 5 concepts to review quality
  5. Saves metadata.json with processing stats

  Output structure:
  factory/output/my_book/
  ├── mybook_mem_pointer_basics_abc123.json
  ├── mybook_func_function_overloading_def456.json
  ├── ...
  └── metadata.json

  ---
  STAGE 2: Integration

  Files Involved:

  - factory/scripts/batch_integrate.py - Integration script
  - rag_finetune/data/concepts/ - Main concept database
  - rag_finetune/config/book_config.json - Book display configuration

  Process:

  1. Run Integration
  python3 rag_finetune/factory/scripts/batch_integrate.py \
      rag_finetune/factory/output/my_book/

  What happens:
  1. Validate & Copy Concepts:
    - Loads all concept JSON files from factory output
    - Validates required fields: id, topic, book, explanation
    - Checks for duplicates (skips if concept ID already exists)
    - Copies to rag_finetune/data/concepts/
  2. Update Book Config (config/book_config.json):
    - Reads metadata.json to get full_title
    - Checks if book already configured
    - If new:
        - Generates short name (15 chars max)
      - Assigns unused color from available list
      - Adds entry to book_config.json
  3. Rebuild Search Index:
    - Calls scripts/build_concept_index.py
    - Creates embeddings for all concepts
    - Saves searchable index

  Book Config Entry Format:
  {
    "books": {
      "My Book Title (2024 Edition)": {
        "color": "bright_yellow",
        "short": "My Book",
        "display": "My Book Title"
      }
    }
  }

  Critical:
  - The key ("My Book Title (2024 Edition)") MUST match the "book" field in concept JSON files EXACTLY
  - This is set from full_title in book config during extraction

  ---
  STAGE 3: Indexing

  Files Involved:

  - scripts/build_concept_index.py - Index builder
  - rag_finetune/data/concept_index.pkl - Embeddings index
  - rag_finetune/data/concept_metadata.json - Index stats

  Process:

  Manual rebuild (if needed):
  python3 rag_finetune/scripts/build_concept_index.py

  What happens:
  1. Scans all data/concepts/*.json files
  2. For each concept:
    - Extracts topic, explanation, book
    - Creates searchable text: {topic}. {explanation[:500]}
  3. Loads sentence-transformer model (all-MiniLM-L6-v2)
  4. Generates embeddings for all concepts
  5. Saves:
    - concept_index.pkl - Full index with embeddings
    - concept_metadata.json - Quick stats

  Index structure:
  {
    "concepts": [
      {
        "id": "concept_id",
        "book": "Book Title",
        "topic": "Concept Topic",
        "explanation": "Full text...",
        "searchable_text": "Topic. Explanation snippet...",
        "file_path": "/path/to/concept.json"
      },
      ...
    ],
    "embeddings": numpy_array,  # Shape: (num_concepts, 384)
    "model_name": "all-MiniLM-L6-v2"
  }

  ---
  Supporting Scripts

  detect_books.py

  python3 rag_finetune/scripts/detect_books.py
  Purpose: Scans all concepts, finds books, suggests config entries for unconfigured books

  Use when: You want to see which books are in the database and which need config entries

  validate_concepts.py

  python3 rag_finetune/factory/scripts/validate_concepts.py \
      rag_finetune/factory/output/my_book/
  Purpose: Validates concept quality before integration
  - Checks required fields
  - Validates ID format
  - Checks for duplicates
  - Validates code examples parse
  - Checks explanation length

  ---
  Complete Workflow Example

  # 1. ADD BOOK
  cp ~/books/effective_modern_cpp.pdf rag_finetune/factory/books/

  # 2. CREATE CONFIG
  cat > rag_finetune/factory/books/effective_modern_cpp.json <<EOF
  {
    "title": "Effective Modern C++",
    "full_title": "Effective Modern C++ by Scott Meyers",
    "author": "Scott Meyers",
    "category_prefix": "emc",
    "chunk_size": 1500,
    "rate_limit_delay": 1.5,
    "extraction_template": "effective_modern_cpp_type_deduction.txt"
  }
  EOF

  # 3. EXTRACT CONCEPTS
  export GEMINI_API_KEY="your-key"
  python3 rag_finetune/factory/scripts/book_processor.py \
      rag_finetune/factory/books/effective_modern_cpp.pdf \
      --pages 15-80

  # 4. REVIEW OUTPUT
  ls rag_finetune/factory/output/effective_modern_cpp_pages_15_80/
  cat rag_finetune/factory/output/effective_modern_cpp_pages_15_80/emc_*.json | head -50

  # 5. VALIDATE (optional)
  python3 rag_finetune/factory/scripts/validate_concepts.py \
      rag_finetune/factory/output/effective_modern_cpp_pages_15_80/

  # 6. INTEGRATE
  python3 rag_finetune/factory/scripts/batch_integrate.py \
      rag_finetune/factory/output/effective_modern_cpp_pages_15_80/

  # 7. VERIFY
  python3 rag_finetune/scripts/detect_books.py

  # 8. TEST SEARCH
  python3 rag_finetune/scripts/cpp_search.py "auto type deduction"

  ---
  Key Data Flows

  Book → Concepts:
  book_processor.py:
    reads: factory/books/my_book.pdf
    uses: factory/templates/extraction.txt
    outputs: factory/output/my_book/{concept_id}.json
    metadata: factory/output/my_book/metadata.json

  Concepts → Database:
  batch_integrate.py:
    reads: factory/output/my_book/*.json
    copies to: data/concepts/{concept_id}.json
    updates: config/book_config.json
    triggers: build_concept_index.py

  Database → Index:
  build_concept_index.py:
    reads: data/concepts/*.json
    creates: data/concept_index.pkl
    metadata: data/concept_metadata.json

  ---
  Critical Metadata Preservation

  NEVER DISCARD (as per project instructions):
  - Book titles in concept "book" field
  - Page references
  - Author information
  - Edition details
  - Chapter information

  Book title matching:
  The "book" field in concept JSON MUST match exactly the key in book_config.json:
  // In concept JSON:
  {"book": "Effective Modern C++ by Scott Meyers"}

  // In book_config.json:
  {"Effective Modern C++ by Scott Meyers": {...}}


