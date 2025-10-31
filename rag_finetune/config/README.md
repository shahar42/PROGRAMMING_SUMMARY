# Book Configuration Guide

This directory contains the configuration for book display in the C/C++ concept search tool.

## Adding a New Book

To add a new book to the search system:

1. **Edit `book_config.json`**
2. **Add a new entry** under the `"books"` section

### Entry Format

```json
"Full Book Title As Stored In Database": {
  "color": "color_name",
  "short": "Short Name",
  "display": "Display Name"
}
```

### Fields Explained

- **Key** (e.g., `"C++ Primer (5th Edition)"`): Must match **exactly** how the book title appears in your concept JSON files
- **color**: Visual color for the book in the UI (see available colors below)
- **short**: Abbreviated name (max 15 characters recommended) for compact displays
- **display**: Clean display name without edition numbers or authors

### Example

```json
"Effective Modern C++ by Scott Meyers (2014)": {
  "color": "bright_yellow",
  "short": "Eff Modern C++",
  "display": "Effective Modern C++"
}
```

## Available Colors

Choose from these color names:

**Bright Colors:**
- `bright_blue`
- `bright_red`
- `bright_green`
- `bright_yellow`
- `bright_magenta`
- `bright_cyan`

**Standard Colors:**
- `blue`
- `red`
- `green`
- `yellow`
- `magenta`
- `cyan`

**Other:**
- `grey70`
- `white`

## Finding Book Titles in Your Database

To find the exact book title as stored:

```bash
# Search for a concept from the book
cppfind "some topic from that book"

# Or check concept JSON files directly
grep -r '"book":' rag_finetune/data/concepts/ | head -20
```

The value in the `"book"` field is what you need to use as the key in `book_config.json`.

## Testing Your Changes

After adding a book:

1. Save `book_config.json`
2. Run the search tool: `cppfind "topic from new book"`
3. Check that:
   - Book appears with correct color in the legend
   - Display name shows without edition/author
   - Menu entries show the display name

## Automatic Fallback

If a book is encountered that's not in `book_config.json`, it will:
- Use white color
- Show first 15 characters as short name
- Show full title as display name

This ensures the tool never breaks, even with unlisted books.

## Tips

- **Use distinct colors** for books you search frequently
- **Keep short names concise** - they appear in narrow displays
- **Test with actual searches** after adding a book
- **Backup this file** before making major changes
