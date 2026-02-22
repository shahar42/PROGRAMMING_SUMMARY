from pathlib import Path
import PyPDF2

pdf_path = Path("rag_finetune/The C++ Standard Library.pdf")
with open(pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    pages = reader.pages[378:408]  # Pages 379-408
    text = '\n\n'.join([p.extract_text() for p in pages])

# Chunk the text
chunk_size = 2000
overlap = 200
chunks = []
start = 0
while start < len(text):
    end = start + chunk_size
    chunks.append(text[start:end])
    start = end - overlap

# Print chunks 13 and 14
print("=== CHUNK 13 ===")
print(chunks[12])
print("\n=== CHUNK 14 ===")
print(chunks[13])
