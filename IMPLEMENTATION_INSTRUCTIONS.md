# Multi-Book Multi-AI Extraction System Implementation Guide

## Project Overview
Transform the existing single-book Gemini extraction system into a 4-book, 4-AI daily extraction pipeline. Each book uses a different AI model but maintains the same atomic concept JSON format.

## Current System Analysis
The existing `books/extract_c_concepts.py` contains 6 main classes:
1. **ProgressTracker**: Manages extraction progress per book
2. **PDFStructureExtractor**: Extracts and classifies PDF content 
3. **ConceptBoundaryDetector**: Identifies atomic concept boundaries
4. **GeminiAtomicProcessor**: Processes concepts using Gemini AI
5. **QualityValidator**: Validates extracted concepts
6. **ExtractionEngine**: Main orchestrator

## Target Book-AI Mapping
- **K&R C Programming** → Gemini (existing, move to new structure)
- **Advanced UNIX Programming** → Grok (X.AI)
- **Linkers & Loaders** → Llama (specify provider in config)
- **Operating Systems** → Gemini (new instance)

## Implementation Tasks

### 1. Refactor Existing Code (CRITICAL)
- Extract classes 1-3, 5-6 from `books/extract_c_concepts.py` into `core/` modules
- Move `GeminiAtomicProcessor` to `processors/gemini_processor.py`
- Update import paths in refactored `books/extract_c_concepts.py`

### 2. Create New Processor Classes
**File: `processors/grok_processor.py`**
- Copy `GeminiAtomicProcessor` structure
- Replace Gemini API calls with X.AI Grok API integration
- Maintain identical JSON output format

**File: `processors/llama_processor.py`**
- Copy `GeminiAtomicProcessor` structure  
- Integrate chosen Llama provider (Groq/Together AI/local)
- Maintain identical JSON output format

### 3. Create Book-Specific Extractors
**File: `books/extract_unix_env.py`**
- Copy `books/extract_c_concepts.py` structure
- Update PDF path to "Advanced Programming in the UNIX Environment 3rd Edition.pdf"
- Update output directory to "outputs/unix_env"
- Import and use `processors.grok_processor.GrokAtomicProcessor`
- Customize prompts for UNIX system programming concepts

**File: `books/extract_linkers_loaders.py`**
- Copy `books/extract_c_concepts.py` structure
- Update PDF path to "LinkersAndLoaders (1).pdf"
- Update output directory to "outputs/linkers_loaders" 
- Import and use `processors.llama_processor.LlamaAtomicProcessor`
- Customize prompts for binary formats and linking concepts

**File: `books/extract_os_three_pieces.py`**
- Copy `books/extract_c_concepts.py` structure
- Update PDF path to "Operating Systems - Three Easy Pieces.pdf"
- Update output directory to "outputs/os_three_pieces"
- Import and use `processors.gemini_processor.GeminiAtomicProcessor` 
- Customize prompts for OS algorithms and data structures

### 4. Configuration Management
**File: `config/books_config.json`**
```json
{
  "kernighan_ritchie": {
    "pdf_path": "The C Programming Language (Kernighan Ritchie).pdf",
    "output_dir": "outputs/kernighan_ritchie",
    "processor": "gemini",
    "concept_focus": "C language syntax, operators, control structures",
    "max_concepts_per_day": 4
  },
  "unix_env": {
    "pdf_path": "Advanced Programming in the UNIX Environment 3rd Edition.pdf", 
    "output_dir": "outputs/unix_env",
    "processor": "grok",
    "concept_focus": "System calls, APIs, UNIX programming patterns",
    "max_concepts_per_day": 4
  },
  "linkers_loaders": {
    "pdf_path": "LinkersAndLoaders (1).pdf",
    "output_dir": "outputs/linkers_loaders", 
    "processor": "llama",
    "concept_focus": "Binary formats, linking mechanics, loader concepts",
    "max_concepts_per_day": 4
  },
  "os_three_pieces": {
    "pdf_path": "Operating Systems - Three Easy Pieces.pdf",
    "output_dir": "outputs/os_three_pieces",
    "processor": "gemini", 
    "concept_focus": "OS algorithms, data structures, system concepts",
    "max_concepts_per_day": 4
  }
}
```

**Update `config/config.env`:**
```
GEMINI_API_KEY=AIzaSyCbDRTwx9KzSOdDdsuOy3ZPvFDlox0Z_S4
GROK_API_KEY=your_xai_grok_key_here
LLAMA_API_KEY=your_llama_provider_key_here
LLAMA_PROVIDER=groq  # or together_ai, ollama_local, etc.
```

### 5. Master Daily Runner
**File: `scripts/run_all_daily.sh`**
- Sequential execution of all 4 book extractors
- Consolidated logging with per-book separation
- Error handling that allows other books to continue if one fails
- Unified daily summary generation

### 6. Progress Tracking Updates
- Each book maintains independent `progress.json` in its output directory
- Modify `core/progress_tracker.py` to accept custom progress file paths
- Ensure no cross-book progress interference

### 7. Quality Validation Consistency
- Maintain identical JSON structure validation across all processors
- Update validation rules to handle different concept types while preserving format

## Critical Implementation Notes

### API Rate Limits & Free Tiers
- Implement delays between API calls (2-3 seconds minimum)
- Add retry logic with exponential backoff
- Monitor daily API usage to stay within free limits
- Consider processing 1 concept per API call to minimize token usage

### JSON Format Consistency (MANDATORY)
All processors MUST output identical JSON structure:
```json
{
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
```

### Error Handling Strategy
- Each book extraction should be independent
- Log failures but continue with other books
- Implement graceful degradation if APIs are unavailable
- Maintain progress state even on partial failures

### Testing Strategy
- Test each processor with small content samples first
- Verify JSON output format consistency
- Test API key validation and error handling
- Run end-to-end test with 1 concept per book

## Directory Structure After Implementation
```
project/
├── core/
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── concept_detector.py  
│   ├── progress_tracker.py
│   └── quality_validator.py
├── processors/
│   ├── __init__.py
│   ├── gemini_processor.py
│   ├── grok_processor.py
│   └── llama_processor.py
├── books/
│   ├── extract_c_concepts.py (refactored)
│   ├── extract_unix_env.py
│   ├── extract_linkers_loaders.py  
│   └── extract_os_three_pieces.py
├── outputs/
│   ├── kernighan_ritchie/ (existing summaries)
│   ├── unix_env/
│   ├── linkers_loaders/
│   └── os_three_pieces/
├── logs/
│   ├── kernighan_ritchie/
│   ├── unix_env/ 
│   ├── linkers_loaders/
│   └── os_three_pieces/
├── config/
│   ├── config.env
│   └── books_config.json
├── scripts/
│   ├── run_all_daily.sh
│   ├── run_daily_extraction.sh (existing)
│   └── set_up_daly.sh (existing)
└── [PDF files and other existing files]
```

## Execution Priority
1. Refactor existing code to shared core modules
2. Create Grok processor (simpler than Llama integration)
3. Test with one new book extraction 
4. Create Llama processor
5. Implement remaining book extractors
6. Create master daily runner
7. End-to-end testing

## Success Criteria
- All 4 books extract 4 concepts daily
- Identical JSON format across all processors
- Independent progress tracking per book
- Consolidated daily logging and summaries
- Stays within free API tier limits
- Handles failures gracefully without stopping other books