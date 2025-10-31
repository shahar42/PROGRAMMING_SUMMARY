# Concept JSON Schema

## Official Schema Fields

Based on analysis of existing concepts in the source of truth database (`rag_finetune/data/concepts/`).

### Required Fields

```json
{
  "topic": "string - The concept title/name",
  "explanation": "string - Detailed explanation of the concept",
  "book": "string - Full book title (e.g., 'C++ Primer (5th Edition)')",
  "extraction_metadata": {
    "source": "string - Book short name or source identifier",
    "extraction_date": "ISO 8601 timestamp",
    "book_metadata_added": "ISO 8601 timestamp (optional)",
    "has_code": "boolean (optional)",
    "has_explanation": "boolean (optional)",
    "book_context": "string - book identifier (optional)",
    "page_range": "string - e.g., '42-45' (optional)",
    "chapter": "string (optional)",
    "extraction_type": "string (optional)"
  }
}
```

### Optional Fields

```json
{
  "keywords": "string - Comma-separated searchable keywords for improved search matching",
  "code_example": "string - Working code example (can be omitted per instructions)",
  "syntax": "string - Syntax patterns or reference material",
  "example_explanation": "string - Explanation of the code example"
}
```

## Field Usage Guidelines

### `topic`
- Short, descriptive title for display in UI
- Clean, human-readable format
- Example: "Operator Precedence and Associativity in C++"

### `keywords`
- Optional comma-separated list of searchable terms
- Includes common abbreviations, alternative names, related terms
- Used by search engine for better matching
- Not displayed directly to users
- Example: "operator precedence, associativity, evaluation order, C++ operators"

### `explanation`
- Comprehensive explanation of the concept
- Can include tables, lists, or formatted text
- Should be self-contained and understandable

### `book`
- Use the full, official book title
- Must match existing book metadata
- Examples:
  - "C++ Primer (5th Edition)"
  - "Expert C Programming: Deep C Secrets"
  - "Computer Systems: A Programmer's Perspective (3rd Edition)"
  - "The C Programming Language - Kernighan & Ritchie"

### `syntax`
- Optional field for syntax patterns, reference tables, or structured information
- Useful for operator tables, declaration syntax, etc.
- Can contain multi-line formatted text

### `code_example`
- Optional (omit if instructed "no code example needed")
- Should be compilable/runnable when present
- Include comments for clarity

### `example_explanation`
- Optional explanation of the code example
- Only needed when `code_example` is present

### `extraction_metadata`
- Required container for metadata
- `source`: Short identifier for the book
- `extraction_date`: When the concept was extracted
- `book_context`: Usually matches `source`
- Other fields optional but recommended for traceability

## Complete Example

```json
{
  "topic": "Pointer Arithmetic in C",
  "keywords": "pointer arithmetic, pointer math, array traversal, pointer increment",
  "explanation": "Pointer arithmetic allows adding or subtracting integer values from pointers. When you add an integer n to a pointer, the address moves forward by n * sizeof(type) bytes. This is fundamental for array traversal and memory manipulation in C.",
  "syntax": "ptr + n   // Moves pointer forward by n elements\nptr - n   // Moves pointer backward by n elements\nptr++     // Increment pointer to next element\nptr--     // Decrement pointer to previous element\nptr2 - ptr1  // Distance between two pointers (in elements)",
  "code_example": "int arr[] = {10, 20, 30, 40, 50};\nint *ptr = arr;\n\nprintf(\"%d\\n\", *ptr);      // 10\nptr += 2;\nprintf(\"%d\\n\", *ptr);      // 30\nprintf(\"%ld\\n\", ptr - arr); // 2",
  "example_explanation": "This demonstrates pointer arithmetic with an integer array. Starting at arr[0], adding 2 to the pointer moves it to arr[2]. Subtracting pointers gives the element distance.",
  "extraction_metadata": {
    "source": "kernighan_ritchie",
    "page_range": "93-95",
    "extraction_date": "2025-10-30T09:45:00",
    "has_code": true,
    "has_explanation": true,
    "book_context": "kernighan_ritchie"
  },
  "book": "The C Programming Language - Kernighan & Ritchie"
}
```

## Notes

- **NO custom fields**: Do not add fields like `id`, `category`, `difficulty`, `related_concepts`, etc.
- **Keywords field is official**: The `keywords` field is now part of the official schema (added 2025-10-30)
- **Filename is the ID**: The concept ID comes from the filename, not a field
- **Book metadata**: Must match entries in book configuration
- **Timestamps**: Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- **Code optional**: Can be omitted when not needed or requested
- **Manually created concepts**: Set `"manually_created": true` and `"created_by": "claude"` in extraction_metadata

## Recently Added Concepts

### New/Delete Operator Concepts (2025-10-30)
Three fundamental concepts added to clarify common C++ memory management confusion:

1. **cpp_mem_new_operator_vs_operator_new_distinction.json**
   - Explains: `new Widget` (expression) vs `operator new` (allocation function)
   - Shows two-step process: allocate raw memory + construct object
   - Includes compilable example with custom operator new

2. **cpp_mem_delete_operator_vs_operator_delete_distinction.json**
   - Explains: `delete ptr` (expression) vs `operator delete` (deallocation function)
   - Shows two-step process: call destructor + deallocate memory
   - Demonstrates why wrong order causes undefined behavior

3. **cpp_mem_array_new_and_delete_operators.json**
   - Explains: `new[]`/`delete[]` for arrays vs single-object versions
   - Shows hidden array size metadata mechanism
   - Highlights critical mismatch errors (new[] with delete, etc.)
