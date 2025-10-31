Perfect! Now I see the structure. Here's my suggestion:

  Strategy: Content-Based Deduplication

  Create a script that:

  1. Loads all "Memory Hierarchy and Caching Strategies" JSON files
  2. Analyzes each concept's code_example and explanation fields
  3. Categorizes them:
    - CONCRETE = Has specific algorithm/technique name (LRU, write-back, blocking, prefetching) OR demonstrates specific optimization in code
    - ABSTRACT = Generic talk about "memory hierarchy exists" with no actionable strategy
  4. Uses LLM (Gemini Flash) to classify each concept as CONCRETE vs ABSTRACT
  5. Keeps only 1-2 best CONCRETE examples, deletes the rest

  Script approach:
  # For each concept JSON:
  # - Extract explanation + code
  # - Ask Gemini: "Does this explain a SPECIFIC caching strategy/technique or just abstract theory?"
  # - If abstract → mark for deletion
  # - If concrete → keep only the best ones (highest quality explanation + code)

  Should I create this script? It will:
  - Read from rag_finetune/data/concepts/csap_*.json
  - Classify using Gemini API (needs GEMINI_API_KEY)
  - Show you what will be deleted before actually deleting
  - Preserve metadata per your instructions

  Confirm and I'll build it.

