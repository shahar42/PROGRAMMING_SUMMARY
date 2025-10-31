  rag_finetune/factory/
  ├── books/                          # INPUT: Your books go here
  │   └── example_book_config.json   # Template config
  ├── output/                         # OUTPUT: Generated concepts
  ├── logs/                           # Processing logs
  ├── templates/                      # LLM prompts & schemas
  │   ├── concept_schema.json        # JSON schema for concepts
  │   └── extraction.txt             # LLM extraction prompt
  ├── scripts/                        # Processing tools
  │   ├── book_processor.py          # Main: Extract concepts from books
  │   ├── batch_integrate.py         # Integrate into main DB
  │   └── validate_concepts.py       # Quality validation
  ├── README.md                       # Full documentation
  ├── QUICKSTART.md                   # 5-minute guide
  └── .gitignore                      # Ignore books/output

  🎯 Key Features

  1. Automated Extraction (book_processor.py)

  - Reads PDF/TXT/MD/EPUB files
  - Chunks intelligently with overlap
  - Uses Gemini to extract concepts
  - Generates proper JSON with IDs
  - Saves incrementally (resumable)
  - Rate limiting & error handling

  2. Batch Integration (batch_integrate.py)

  - Copies concepts to main database
  - Auto-adds book to book_config.json
  - Picks unused color automatically
  - Rebuilds search index
  - Validates & deduplicates

  3. Quality Validation (validate_concepts.py)

  - Checks required fields
  - Validates ID format
  - Verifies explanation length
  - Checks code examples
  - Reports statistics
  - Exit codes for CI/CD

  4. Smart Configuration

  - Per-book config files
  - Customizable chunk sizes
  - Rate limiting control
  - Category prefixes
  - Extraction settings

  🚀 Usage Example

  # 1. Add your book
  cp ~/Downloads/modern_cpp.pdf rag_finetune/factory/books/

  # 2. Create config (optional)
  cat > rag_finetune/factory/books/modern_cpp.json << EOF
  {
    "title": "Modern C++",
    "full_title": "Modern C++ (2024 Edition)",
    "category_prefix": "moderncpp",
    "chunk_size": 2000
  }
  EOF

  # 3. Extract concepts
  python3 rag_finetune/factory/scripts/book_processor.py \
      rag_finetune/factory/books/modern_cpp.pdf

  # 4. Validate (optional)
  python3 rag_finetune/factory/scripts/validate_concepts.py \
      rag_finetune/factory/output/modern_cpp/

  # 5. Integrate into database
  python3 rag_finetune/factory/scripts/batch_integrate.py \
      rag_finetune/factory/output/modern_cpp/

  # 6. Test!
  cppfind "move semantics"

  💡 What Makes It Expandable

  1. JSON Configuration - No code changes needed
  2. Template System - Customize prompts easily
  3. Modular Scripts - Each step is independent
  4. Auto-detection - Books self-register
  5. Validation - Catch issues before integration
  6. Documentation - Quick start + full docs

  🔄 Complete Workflow

  Book File → Processor → Concepts JSON → Validator → Integrator → Searchable!
     ↓           ↓            ↓              ↓           ↓            ↓
    PDF       Gemini      output/        validate    concepts/   cppfind
             chunks       my_book/        quality      DB        results

  The system is production-ready for processing new books with minimal effort!

