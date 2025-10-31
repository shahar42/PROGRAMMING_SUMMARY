# Concept Factory

Automated system for converting books into structured JSON concepts using LLMs.

## Directory Structure

```
factory/
├── books/              # Input: Place your book files here
│   ├── book_name.pdf
│   ├── book_name.txt
│   └── book_name.md
├── output/             # Output: Generated concepts per book
│   ├── book_name/
│   │   ├── concept_001.json
│   │   ├── concept_002.json
│   │   └── metadata.json
├── templates/          # Prompt templates for LLM
│   ├── extraction.txt
│   └── concept_schema.json
├── logs/              # Processing logs
└── scripts/           # Factory scripts
    ├── book_processor.py
    ├── concept_extractor.py
    └── batch_integrate.py
```

## Workflow

### 1. Add a Book

Place your book file in `factory/books/`:
```bash
cp ~/Downloads/my_book.pdf factory/books/
```

Supported formats:
- PDF (.pdf)
- Plain text (.txt)
- Markdown (.md)
- EPUB (.epub)

### 2. Configure Book Metadata

Create a config file `factory/books/my_book.json`:
```json
{
  "title": "My Programming Book",
  "full_title": "My Programming Book (1st Edition)",
  "author": "Author Name",
  "year": 2024,
  "category_prefix": "mybook",
  "language": "C++",
  "chunk_size": 2000,
  "llm_provider": "gemini"
}
```

### 3. Extract Concepts

Run the extraction:
```bash
python3 factory/scripts/book_processor.py factory/books/my_book.pdf
```

This will:
- Parse the book into chunks
- Send to LLM for concept extraction
- Generate JSON concepts in `factory/output/my_book/`
- Create metadata file with stats

### 4. Review & Edit

Review generated concepts:
```bash
ls factory/output/my_book/
cat factory/output/my_book/concept_001.json
```

Edit any concepts that need refinement.

### 5. Integrate into Main Database

Batch integrate all concepts:
```bash
python3 factory/scripts/batch_integrate.py factory/output/my_book/
```

This will:
- Copy concepts to `rag_finetune/data/concepts/`
- Update book configuration
- Rebuild search index
- Generate statistics

## Concept Schema

Each generated concept follows this structure:

```json
{
  "id": "mybook_mem_pointer_basics_abc123",
  "topic": "Pointer Basics in C",
  "book": "My Programming Book",
  "category": "mem",
  "explanation": "Detailed explanation...",
  "code_example": "int* ptr = &value;",
  "practical_example": "Real-world usage...",
  "related_concepts": ["mybook_mem_memory_allocation_def456"],
  "keywords": ["pointer", "memory", "address"],
  "difficulty": "beginner",
  "page_reference": "42-45"
}
```

## LLM Providers Supported

- **Gemini** (default): Google's Gemini API
- **OpenAI**: GPT-4 / GPT-3.5
- **Claude**: Anthropic Claude API
- **Local**: llama.cpp or Ollama

Configure in book metadata or environment variables.

## Advanced Usage

### Custom Extraction Prompts

Edit `factory/templates/extraction.txt` to customize:
- Concept granularity
- Focus areas
- Code example style
- Explanation depth

### Batch Processing

Process multiple books:
```bash
python3 factory/scripts/batch_process.py factory/books/*.pdf
```

### Resume Interrupted Processing

```bash
python3 factory/scripts/book_processor.py --resume factory/output/my_book/
```

## Quality Control

### Validation

Check concept quality:
```bash
python3 factory/scripts/validate_concepts.py factory/output/my_book/
```

This checks:
- Required fields present
- ID format correct
- No duplicates
- Code examples parse
- Reasonable explanation length

### Statistics

View extraction stats:
```bash
python3 factory/scripts/stats.py factory/output/my_book/metadata.json
```

Shows:
- Total concepts extracted
- Concepts per category
- Average explanation length
- Code example coverage
- Processing time

## Troubleshooting

**Issue: LLM rate limiting**
- Solution: Adjust `rate_limit_delay` in book config
- Use checkpointing for resume

**Issue: Poor quality concepts**
- Solution: Adjust chunk_size (smaller = more focused)
- Refine extraction prompt
- Try different LLM provider

**Issue: Missing code examples**
- Solution: Add explicit instruction in prompt
- Post-process with `generate_code_examples.py`

**Issue: Duplicate concepts**
- Solution: Run deduplication script
- Check concept ID generation logic

## Best Practices

1. **Start small**: Test with one chapter first
2. **Review samples**: Check first 10 concepts before full run
3. **Backup**: Keep original books and generated concepts
4. **Iterate prompts**: Refine extraction prompts based on output
5. **Version control**: Track book configs and templates
6. **Document sources**: Keep book metadata accurate

## Integration Checklist

Before integrating concepts:

- [ ] All concepts have unique IDs
- [ ] Book title matches exactly across concepts
- [ ] Category prefixes are consistent
- [ ] Code examples are syntactically valid
- [ ] No placeholder text ("TODO", "TBD", etc.)
- [ ] Page references are accurate
- [ ] Related concepts IDs exist
- [ ] Book added to `config/book_config.json`
- [ ] Extraction logged in `factory/logs/`

## Next Steps

After integration:
1. Test search: `cppfind "topic from new book"`
2. Verify book appears with correct color
3. Check concept display and formatting
4. Run `detect_books.py` to confirm registration
5. Update documentation with new book info
