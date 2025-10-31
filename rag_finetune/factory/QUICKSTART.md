# Factory Quick Start Guide

Get a new book into your search system in 5 minutes.

## Prerequisites

```bash
# Ensure Gemini API key is set
export GEMINI_API_KEY="your-api-key"

# Install dependencies if needed
pip install google-generativeai PyPDF2 tqdm
```

## Step-by-Step

### 1. Add Your Book

```bash
# Copy your book to the factory
cp ~/Downloads/my_book.pdf rag_finetune/factory/books/
```

### 2. Create Book Config (Optional but Recommended)

```bash
cd rag_finetune/factory/books
cp example_book_config.json my_book.json
```

Edit `my_book.json`:
```json
{
  "title": "My Book Title",
  "full_title": "My Book Title (2024 Edition)",
  "author": "Author Name",
  "category_prefix": "mybook",
  "chunk_size": 2000,
  "rate_limit_delay": 1.0
}
```

### 3. Extract Concepts

```bash
cd ../../..  # Back to project root
python3 rag_finetune/factory/scripts/book_processor.py \
    rag_finetune/factory/books/my_book.pdf
```

This will:
- Parse your book
- Send chunks to Gemini
- Extract concepts with LLM
- Save to `factory/output/my_book/`

**Time estimate**: 5-30 minutes depending on book size and rate limits.

### 4. Review Output

```bash
# Check what was generated
ls rag_finetune/factory/output/my_book/

# Look at a sample concept
cat rag_finetune/factory/output/my_book/mybook_mem_*.json | head -50

# Check metadata
cat rag_finetune/factory/output/my_book/metadata.json
```

### 5. Integrate into Database

```bash
python3 rag_finetune/factory/scripts/batch_integrate.py \
    rag_finetune/factory/output/my_book/
```

This will:
- Copy concepts to main database
- Add book to `book_config.json`
- Rebuild search index
- Make everything searchable

### 6. Test

```bash
cppfind "some topic from your new book"
```

You should see results from your book with the assigned color!

## Common Issues

### "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your-key-here"
```

### "Rate limit exceeded"
Increase `rate_limit_delay` in your book config:
```json
{
  "rate_limit_delay": 2.0
}
```

### "Poor quality concepts"
Try smaller chunks for more focused extraction:
```json
{
  "chunk_size": 1000
}
```

### "Duplicate concepts detected"
The integrator skips duplicates automatically. Check logs for details.

## Advanced Usage

### Process Specific Chapters

Edit your book file to only include desired chapters, then process normally.

### Resume Interrupted Processing

If processing stops midway:
```bash
# Concepts are saved as they're generated
# Just re-run batch_integrate with existing output
python3 rag_finetune/factory/scripts/batch_integrate.py \
    rag_finetune/factory/output/my_book/
```

### Batch Process Multiple Books

```bash
# Process all books in factory/books/
for book in rag_finetune/factory/books/*.pdf; do
    python3 rag_finetune/factory/scripts/book_processor.py "$book"
done

# Then integrate all
for output_dir in rag_finetune/factory/output/*/; do
    python3 rag_finetune/factory/scripts/batch_integrate.py "$output_dir"
done
```

### Customize Extraction Prompt

Edit `factory/templates/extraction.txt` to change:
- Concept granularity
- Code example style
- Explanation structure
- Category choices

## Performance Tips

1. **Start small**: Test with a single chapter first
2. **Optimize chunk size**: Smaller = more concepts, larger = better context
3. **Use rate limiting**: Prevent API throttling
4. **Monitor output**: Check first few concepts before full run
5. **Iterate prompts**: Refine extraction template based on results

## File Organization

```
factory/
├── books/                    # Your input books
│   ├── my_book.pdf
│   └── my_book.json         # Config
├── output/                   # Generated concepts
│   └── my_book/
│       ├── concept_001.json
│       ├── concept_002.json
│       └── metadata.json
├── templates/                # LLM prompts
│   └── extraction.txt
└── scripts/                  # Processing tools
    ├── book_processor.py
    └── batch_integrate.py
```

## Next Steps

After integration:
- Run `detect_books.py` to verify registration
- Check book display colors with `cppfind`
- Adjust book config if needed
- Process more books!

## Getting Help

- Check `factory/README.md` for detailed docs
- Review `factory/logs/` for error details
- Test with small samples first
- Examine existing concepts for format reference
