Project Overview
Transform the existing single-book Gemini extraction system into a multi-book, multi-AI daily extraction pipeline. Each book uses a different AI model but maintains the same atomic concept JSON format.
Current System Status ✅ PHASE 1 COMPLETE
The refactoring has been successfully completed:

✅ Core modules extracted: progress_tracker.py, pdf_extractor.py, concept_detector.py
✅ Gemini processor moved to: processors/gemini_processor.py
✅ Main script refactored: books/extract_c_concepts.py (using modular imports)
✅ QualityValidator removed (not necessary for functionality)
✅ System tested and working from page 60

Revised Target Book-AI Mapping (Based on Free Tiers)

K&R C Programming → Gemini (existing, working) ✅
Advanced UNIX Programming → Claude/Anthropic (has free tier)
Linkers & Loaders → Gemini (second instance, proven to work)
Operating Systems → Grok/X.AI (has free tier, uses Llama models)

Note: Llama direct access has no free tier. Grok effectively uses Llama models but provides free access.
Remaining Implementation Tasks
1. ✅ COMPLETED: Core Refactoring

✅ Extracted shared classes into core/ modules
✅ Created processors/gemini_processor.py
✅ Updated main script with modular imports
✅ Removed QualityValidator (unnecessary complexity)

2. Create New Processor Classes
File: processors/claude_processor.py (Recommended for UNIX book)

Copy GeminiAtomicProcessor structure
Replace with Anthropic Claude API integration
Maintain identical JSON output format
Has generous free tier

File: processors/grok_processor.py (For OS book)

Copy GeminiAtomicProcessor structure
Replace with X.AI Grok API integration
Maintain identical JSON output format
Has free tier, uses Llama models internally

3. Create Book-Specific Extractors
File: books/extract_unix_env.py

Copy books/extract_c_concepts.py structure
Update PDF path to "Advanced Programming in the UNIX Environment 3rd Edition.pdf"
Update output directory to "outputs/unix_env"
Import and use processors.claude_processor.ClaudeAtomicProcessor
Customize prompts for UNIX system programming concepts

File: books/extract_linkers_loaders.py

Copy books/extract_c_concepts.py structure
Update PDF path to "LinkersAndLoaders (1).pdf"
Update output directory to "outputs/linkers_loaders"
Import and use processors.gemini_processor.GeminiAtomicProcessor (second instance)
Customize prompts for binary formats and linking concepts

File: books/extract_os_three_pieces.py

Copy books/extract_c_concepts.py structure
Update PDF path to "Operating Systems - Three Easy Pieces.pdf"
Update output directory to "outputs/os_three_pieces"
Import and use processors.grok_processor.GrokAtomicProcessor
Customize prompts for OS algorithms and data structures

4. Configuration Management
File: config/books_config.json
json{
  "kernighan_ritchie": {
    "pdf_path": "The C Programming Language (Kernighan Ritchie).pdf",
    "output_dir": "outputs/kernighan_ritchie",
    "processor": "gemini",
    "concept_focus": "C language syntax, operators, control structures",
    "max_concepts_per_day": 4,
    "status": "active"
  },
  "unix_env": {
    "pdf_path": "Advanced Programming in the UNIX Environment 3rd Edition.pdf", 
    "output_dir": "outputs/unix_env",
    "processor": "claude",
    "concept_focus": "System calls, APIs, UNIX programming patterns",
    "max_concepts_per_day": 4,
    "status": "pending"
  },
  "linkers_loaders": {
    "pdf_path": "LinkersAndLoaders (1).pdf",
    "output_dir": "outputs/linkers_loaders", 
    "processor": "gemini", 
    "concept_focus": "Binary formats, linking mechanics, loader concepts",
    "max_concepts_per_day": 4,
    "status": "pending"
  },
  "os_three_pieces": {
    "pdf_path": "Operating Systems - Three Easy Pieces.pdf",
    "output_dir": "outputs/os_three_pieces",
    "processor": "grok",
    "concept_focus": "OS algorithms, data structures, system concepts",
    "max_concepts_per_day": 4,
    "status": "pending"
  }
}
Update config/config.env:
GEMINI_API_KEY=AIzaSyCbDRTwx9KzSOdDdsuOy3ZPvFDlox0Z_S4
CLAUDE_API_KEY=your_anthropic_claude_key_here
GROK_API_KEY=your_xai_grok_key_here
5. Master Daily Runner
File: scripts/run_all_daily.sh

Sequential execution of all 4 book extractors
Consolidated logging with per-book separation
Error handling that allows other books to continue if one fails
Unified daily summary generation

6. Progress Tracking Updates

Each book maintains independent progress.json in its output directory
Modify core/progress_tracker.py to accept custom progress file paths
Ensure no cross-book progress interference

Critical Implementation Notes
API Free Tier Reality Check

Gemini: ✅ Has generous free tier (currently working)
Claude/Anthropic: ✅ Has free tier with reasonable limits
Grok/X.AI: ✅ Has free tier, uses Llama models internally
Llama Direct: ❌ No free tier available

Rate Limiting Strategy

Implement 2-3 second delays between API calls
Add retry logic with exponential backoff
Monitor daily API usage to stay within free limits
Process 1 concept per API call to minimize token usage

JSON Format Consistency (MANDATORY)
All processors MUST output identical JSON structure:
json{
  "topic": "Concept Name",
  "explanation": "Clear definition...",
  "syntax": "generalized pattern", 
  "code_example": ["line1", "line2", "..."],
  "example_explanation": "How this demonstrates the concept...",
  "extraction_metadata": {
    "source": "Book Title",
    "page_range": "X-Y", 
    "extraction_date": "ISO timestamp",
    "has_code": boolean,
    "has_explanation": boolean
  }
}
Error Handling Strategy

Each book extraction should be independent
Log failures but continue with other books
Implement graceful degradation if APIs are unavailable
Maintain progress state even on partial failures

Updated Directory Structure
project/
├── core/                           ✅ COMPLETED
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── concept_detector.py  
│   └── progress_tracker.py
├── processors/                     ✅ PARTIALLY COMPLETED
│   ├── __init__.py
│   ├── gemini_processor.py         ✅ COMPLETED
│   ├── claude_processor.py         🔄 TO CREATE
│   └── grok_processor.py           🔄 TO CREATE
├── books/
│   ├── extract_c_concepts.py       ✅ COMPLETED (refactored)
│   ├── extract_unix_env.py         🔄 TO CREATE
│   ├── extract_linkers_loaders.py  🔄 TO CREATE
│   └── extract_os_three_pieces.py  🔄 TO CREATE
├── outputs/
│   ├── kernighan_ritchie/          ✅ ACTIVE (8 concepts)
│   ├── unix_env/                   🔄 TO CREATE
│   ├── linkers_loaders/            🔄 TO CREATE
│   └── os_three_pieces/            🔄 TO CREATE
├── config/
│   ├── config.env                  ✅ EXISTS (needs new API keys)
│   └── books_config.json           🔄 TO CREATE
└── scripts/
    ├── run_all_daily.sh            🔄 TO CREATE
    ├── run_daily_extraction.sh     ✅ EXISTS (for K&R only)
    └── set_up_daly.sh              ✅ EXISTS (for K&R only)
Updated Execution Priority

✅ COMPLETED: Refactor existing code to shared core modules
🔄 NEXT: Create Claude processor (for UNIX book)
🔄 THEN: Create Grok processor (for OS book)
🔄 THEN: Create book-specific extractors
🔄 THEN: Create master daily runner
🔄 FINALLY: End-to-end testing

Success Criteria

All 4 books extract 4 concepts daily
Identical JSON format across all processors
Independent progress tracking per book
Consolidated daily logging and summaries
Stays within free API tier limits
Graceful handling of API failures without stopping other books

Current Status: Phase 1 Complete, Ready for Phase 2 (Processor Creation)
