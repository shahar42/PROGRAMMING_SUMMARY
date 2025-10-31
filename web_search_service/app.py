#!/usr/bin/env python3
"""
C/C++ Concept Search - Web Service
Self-contained Flask application for semantic search with AI chat
"""

import json
import pickle
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from dotenv import load_dotenv

# ==================== Configuration ====================

# Service paths (relative to this directory)
SERVICE_DIR = Path(__file__).parent
DATA_DIR = SERVICE_DIR / "data"
CONFIG_DIR = SERVICE_DIR / "config"
TEMPLATES_DIR = SERVICE_DIR / "templates"
STATIC_DIR = SERVICE_DIR / "static"

INDEX_FILE = DATA_DIR / "concept_index.pkl"
BOOK_CONFIG_FILE = CONFIG_DIR / "book_config.json"
CONCEPTS_DIR = DATA_DIR / "concepts"

# Load environment variables
ENV_FILE = SERVICE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Settings
TOP_K = 50
DEFAULT_DISPLAY = 10

# ==================== Flask App Setup ====================

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static"
)
CORS(app)

# Global state
searcher = None
book_config = {}


# ==================== Utilities ====================

def load_book_config() -> Dict:
    """Load book configuration from JSON file"""
    try:
        with open(BOOK_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('books', {})
    except FileNotFoundError:
        print(f"Warning: Book config not found at {BOOK_CONFIG_FILE}")
        return {}
    except Exception as e:
        print(f"Error loading book config: {e}")
        return {}


def show_error(message: str):
    """Print error message"""
    print(f"❌ Error: {message}")


def show_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


# ==================== ConceptSearch Class ====================

class ConceptSearch:
    """Semantic search engine for C/C++ concepts"""

    def __init__(self, index_path: Path):
        """Initialize search engine with pre-built index"""
        show_info(f"Loading concept index from {index_path}...")

        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")

        with open(index_path, 'rb') as f:
            data = pickle.load(f)

        self.concepts = data["concepts"]
        self.embeddings = data["embeddings"]
        self.model_name = data["model_name"]

        show_info(f"Loading model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)

        show_info(f"Ready • {len(self.concepts)} concepts indexed")

    def search(self, query: str, top_k: int = TOP_K) -> List[Tuple[Dict, float]]:
        """Search concepts by semantic similarity with keyword boost"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        query_words = set(query.lower().split())

        for idx in top_indices:
            concept = self.concepts[idx]
            semantic_score = float(similarities[idx])

            # Load concept JSON to check keywords field
            file_path = Path(concept["file_path"])
            if not file_path.is_absolute():
                file_path = CONCEPTS_DIR / Path(concept["file_path"]).name

            try:
                with open(file_path, 'r') as f:
                    full_data = json.load(f)

                keywords = full_data.get("keywords", "")

                # Handle keywords as list or string
                if isinstance(keywords, list):
                    keywords = ", ".join(keywords)

                # Count keyword matches for boosting
                keyword_boost = 0
                if keywords:
                    keyword_words = set(keywords.lower().replace(",", " ").split())
                    matches = query_words & keyword_words
                    keyword_boost = len(matches) * 0.08

                # Combine scores
                final_score = min(semantic_score + keyword_boost, 1.0)
                results.append((concept, final_score))
            except Exception as e:
                # If we can't read the file, use semantic score only
                results.append((concept, semantic_score))

        # Re-sort by final scores
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_book_config(self, book_name: str) -> Dict:
        """Get book configuration with sensible defaults"""
        return book_config.get(book_name, {
            "color": "white",
            "short": book_name[:15],
            "display": book_name
        })

    def get_concept_full(self, concept_id: str) -> Optional[Dict]:
        """Load full concept data from file by concept ID"""
        try:
            for concept in self.concepts:
                if concept['id'] == concept_id:
                    # Try to load from concepts directory
                    concept_file = CONCEPTS_DIR / f"{concept_id}.json"
                    if concept_file.exists():
                        with open(concept_file, 'r') as f:
                            return json.load(f)

                    # Fallback: try the file_path from index
                    file_path = Path(concept["file_path"])
                    if not file_path.is_absolute():
                        file_path = CONCEPTS_DIR / file_path.name

                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading concept {concept_id}: {e}")
            return None


# ==================== API Routes ====================

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def api_search():
    """
    Search for concepts

    Request: {"query": "what is RAII?"}
    Response: {"query": "...", "results": [...], "total": N, "summary": [...]}
    """
    try:
        data = request.json or {}
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Empty query'}), 400

        if not searcher:
            return jsonify({'error': 'Search engine not initialized'}), 500

        results = searcher.search(query, top_k=TOP_K)

        if not results:
            return jsonify({'query': query, 'results': [], 'total': 0, 'summary': []})

        # Format results for display (limit initial display)
        formatted_results = []
        for concept, score in results[:DEFAULT_DISPLAY]:
            book_config_data = searcher.get_book_config(concept.get('book', ''))
            formatted_results.append({
                'id': concept['id'],
                'topic': concept['topic'],
                'book': concept.get('book', 'Unknown'),
                'book_display': book_config_data['display'],
                'book_color': book_config_data['color'],
                'score': round(score * 100),
                'file_path': concept['file_path']
            })

        # Create summary by book
        by_book = {}
        for concept, score in results:
            book = concept.get('book', 'Unknown')
            if book not in by_book:
                by_book[book] = {'count': 0, 'top_score': 0}
            by_book[book]['count'] += 1
            by_book[book]['top_score'] = max(by_book[book]['top_score'], int(score * 100))

        summary = []
        for book in sorted(by_book.keys()):
            config = searcher.get_book_config(book)
            summary.append({
                'book': book,
                'display': config['display'],
                'color': config['color'],
                'count': by_book[book]['count'],
                'top_score': by_book[book]['top_score']
            })

        return jsonify({
            'query': query,
            'results': formatted_results,
            'total': len(results),
            'summary': summary
        })

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/concept/<concept_id>', methods=['GET'])
def api_concept(concept_id):
    """
    Get full concept details

    Response: {topic, explanation, code_example, book, etc.}
    """
    try:
        if not searcher:
            return jsonify({'error': 'Search engine not initialized'}), 500

        # Load full concept data
        full_data = searcher.get_concept_full(concept_id)
        if not full_data:
            return jsonify({'error': 'Concept not found'}), 404

        # Find concept in index for metadata
        matching_concept = None
        for c in searcher.concepts:
            if c['id'] == concept_id:
                matching_concept = c
                break

        if not matching_concept:
            return jsonify({'error': 'Concept metadata not found'}), 404

        book_config_data = searcher.get_book_config(matching_concept.get('book', ''))

        return jsonify({
            'id': concept_id,
            'topic': full_data.get('topic', ''),
            'explanation': full_data.get('explanation', ''),
            'code_example': full_data.get('code_example'),
            'syntax': full_data.get('syntax'),
            'example_explanation': full_data.get('example_explanation'),
            'book': matching_concept.get('book', ''),
            'book_display': book_config_data['display'],
            'book_color': book_config_data['color'],
            'has_code': bool(full_data.get('code_example') or full_data.get('practical_example')),
            'extraction_metadata': full_data.get('extraction_metadata', {})
        })

    except Exception as e:
        print(f"Concept fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Chat with AI tutor about a concept

    Request: {
        "concept_id": "...",
        "message": "Can you explain...?"
    }
    Response: {"response": "...", "concept_id": "..."}
    """
    try:
        data = request.json or {}
        concept_id = data.get('concept_id', '').strip()
        message = data.get('message', '').strip()

        if not concept_id or not message:
            return jsonify({'error': 'Missing concept_id or message'}), 400

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({'error': 'GEMINI_API_KEY not configured'}), 500

        if not searcher:
            return jsonify({'error': 'Search engine not initialized'}), 500

        # Load concept data
        full_data = searcher.get_concept_full(concept_id)
        if not full_data:
            return jsonify({'error': 'Concept not found'}), 404

        # Build system context (hidden from user)
        topic = full_data.get('topic', 'Unknown Topic')
        explanation = full_data.get('explanation', '')
        code_example = full_data.get('code_example', '')
        syntax = full_data.get('syntax', '')
        example_explanation = full_data.get('example_explanation', '')
        book = full_data.get('book', 'Unknown Source')

        system_context = f"""You are an expert programming tutor specializing in C/C++ concepts.

You are currently helping a student understand the following concept:

**Topic**: {topic}
**Source**: {book}

**Concept Explanation**:
{explanation}

"""

        if syntax:
            system_context += f"""**Syntax/Reference**:
{syntax}

"""

        if code_example:
            system_context += f"""**Code Example**:
```
{code_example}
```

"""

        if example_explanation:
            system_context += f"""**Example Explanation**:
{example_explanation}

"""

        system_context += """**Your Role**:
- You are a guru of programming and computer architecture
- Your answers are concise yet dense with information
- Answer questions about this specific concept
- Provide clear, technical explanations without fluff
- Give practical examples when helpful
- Reference the concept material above when relevant
- If asked about something outside this concept, politely redirect to the topic

The student doesn't know you have this context loaded - answer naturally as an expert tutor."""

        # Initialize Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=system_context
        )

        # Send message and get response
        response = model.generate_content(message)

        return jsonify({
            'response': response.text,
            'concept_id': concept_id
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get search index statistics"""
    try:
        if not searcher:
            return jsonify({'error': 'Search engine not initialized'}), 500

        # Count concepts by book
        by_book = {}
        for concept in searcher.concepts:
            book = concept.get('book', 'Unknown')
            if book not in by_book:
                by_book[book] = 0
            by_book[book] += 1

        return jsonify({
            'total_concepts': len(searcher.concepts),
            'embedding_dimensions': int(searcher.embeddings.shape[1]),
            'model': searcher.model_name,
            'books': {
                book: {
                    'count': count,
                    'display': searcher.get_book_config(book)['display']
                }
                for book, count in sorted(by_book.items(), key=lambda x: -x[1])
            }
        })

    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== Initialization ====================

def initialize():
    """Initialize the search engine on startup"""
    global searcher, book_config

    print("\n" + "="*60)
    print("C/C++ Concept Search Web Service")
    print("="*60 + "\n")

    try:
        # Load book config
        book_config = load_book_config()
        if book_config:
            show_info(f"Loaded {len(book_config)} book configurations")
        else:
            show_info("No book config found - using defaults")

        # Initialize search
        searcher = ConceptSearch(INDEX_FILE)
        print("\n✅ Service initialized successfully\n")

    except Exception as e:
        show_error(f"Failed to initialize: {e}")
        exit(1)


# ==================== Main ====================

if __name__ == '__main__':
    initialize()

    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"Debug mode: {debug}\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False  # Disable reloader to prevent double initialization
    )
