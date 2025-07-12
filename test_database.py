# test_database.py
from mcp_server import ConceptDatabase

# Test your database
db = ConceptDatabase()
print(f"✅ Indexed {len(db.concepts_index)} concepts")

# Test search
results = db.search_concepts("file operations", limit=3)
for r in results:
    print(f"- {r['topic']} ({r['book_title']})")

# Test book listing  
books = db.list_books()
for book in books:
    print(f"📚 {book['title']}: {book['concept_count']} concepts")
