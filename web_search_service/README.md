# C/C++ Concept Search - Web Service

A self-contained, production-ready web service for semantic search over C/C++ programming concepts with AI-powered tutoring.

## Features

- **Semantic Search**: Find concepts using natural language queries
- **AI Chat Tutor**: Ask follow-up questions about concepts with context-aware responses
- **Book Filtering**: Filter results by source book
- **Concept Details**: View full explanations, code examples, and syntax references
- **Responsive Design**: Terminal-inspired UI that works on desktop and mobile

## Directory Structure

```
web_search_service/
├── app.py                 # Flask application with API endpoints
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
├── .env.example          # Environment variables template
├── README.md             # This file
│
├── data/
│   ├── concept_index.pkl # Pre-computed search index (semantic embeddings)
│   ├── book_config.json  # Book metadata and display settings
│   └── concepts/         # Individual concept JSON files (~12MB)
│
├── config/
│   └── book_config.json  # (symlink to data/book_config.json)
│
├── templates/
│   └── index.html        # Single-page HTML interface
│
└── static/
    ├── style.css         # Terminal-inspired styling
    └── app.js            # Frontend logic and interactions
```

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Run the server**:
   ```bash
   python app.py
   ```

4. **Access the web interface**:
   ```
   http://localhost:5000
   ```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (for chat) | Google Generative AI API key for chat feature |
| `FLASK_ENV` | No | Set to `production` for deployment (default: `development`) |
| `PORT` | No | Server port (default: 5000) |

## Deployment to Render

### Prerequisites

- A Render account (render.com)
- Git repository with this code
- A Google Generative AI API key

### Steps

1. **Push code to Git repository**:
   ```bash
   git add .
   git commit -m "Add web search service"
   git push
   ```

2. **Create a new Web Service on Render**:
   - Go to render.com and sign in
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the deployment:
     - **Name**: `cpp-concept-search` (or your choice)
     - **Environment**: Python 3
     - **Build Command**: `pip install -r web_search_service/requirements.txt`
     - **Start Command**: `cd web_search_service && gunicorn app:app`
     - **Instance Type**: Free tier is sufficient

3. **Add Environment Variables**:
   - In Render dashboard, go to your service
   - Click "Environment"
   - Add `GEMINI_API_KEY` with your API key
   - Set `FLASK_ENV` to `production`

4. **Deploy**:
   - Render will automatically deploy when you push to main branch
   - Wait for the build to complete (~5-10 minutes)
   - Access your service at: `https://cpp-concept-search.onrender.com`

## API Endpoints

### POST `/api/search`
Search for concepts by query

**Request**:
```json
{
  "query": "what is RAII?"
}
```

**Response**:
```json
{
  "query": "what is RAII?",
  "results": [
    {
      "id": "concept_id",
      "topic": "RAII: Resource Acquisition Is Initialization",
      "book": "C++ Primer (5th Edition)",
      "book_display": "C++ Primer",
      "book_color": "cyan",
      "score": 95,
      "file_path": "data/concepts/..."
    }
  ],
  "total": 25,
  "summary": [
    {
      "book": "C++ Primer (5th Edition)",
      "display": "C++ Primer",
      "color": "cyan",
      "count": 15,
      "top_score": 95
    }
  ]
}
```

### GET `/api/concept/<concept_id>`
Get full concept details

**Response**:
```json
{
  "id": "concept_id",
  "topic": "RAII: Resource Acquisition Is Initialization",
  "explanation": "Detailed explanation...",
  "code_example": "int main() { ... }",
  "syntax": "RAII pattern syntax...",
  "example_explanation": "Explanation of code example...",
  "book": "C++ Primer (5th Edition)",
  "book_display": "C++ Primer",
  "book_color": "cyan",
  "has_code": true,
  "extraction_metadata": { ... }
}
```

### POST `/api/chat`
Chat with AI tutor about a concept

**Request**:
```json
{
  "concept_id": "concept_id",
  "message": "Can you explain this with a simpler example?",
  "history": []
}
```

**Response**:
```json
{
  "response": "AI response text here...",
  "concept_id": "concept_id"
}
```

### GET `/api/stats`
Get search index statistics

**Response**:
```json
{
  "total_concepts": 2850,
  "embedding_dimensions": 384,
  "model": "all-MiniLM-L6-v2",
  "books": {
    "C++ Primer (5th Edition)": {
      "count": 500,
      "display": "C++ Primer"
    }
  }
}
```

## How It Works

### Search Engine

1. **Embedding Model**: Uses `sentence-transformers` (all-MiniLM-L6-v2)
2. **Index**: Pre-computed embeddings stored in `concept_index.pkl`
3. **Matching**: Cosine similarity between query and concept embeddings
4. **Boosting**: Keyword matching adds 0.08 points per keyword match
5. **Results**: Top 50 results returned, UI shows 10 by default

### AI Chat

1. **Context Loading**: Full concept data loaded invisibly into system prompt
2. **Model**: Google Gemini 2.0 Flash for fast responses
3. **Role**: Acts as expert C/C++ tutor with concept context
4. **Streaming**: Responses streamed token-by-token for better UX

## Maintenance

### Update Concepts

If you update the concept files in `data/concepts/`:

1. Rebuild the search index locally:
   ```bash
   cd /path/to/rag_finetune
   python scripts/build_concept_index.py
   ```

2. Copy updated index to web service:
   ```bash
   cp rag_finetune/data/concept_index.pkl web_search_service/data/
   ```

3. Push to Git and redeploy:
   ```bash
   git add web_search_service/data/concept_index.pkl
   git commit -m "Update search index"
   git push
   ```

### Monitor Performance

- **Render Dashboard**: Monitor build/deployment status and logs
- **Browser Console**: Check for JavaScript errors
- **API Logs**: View request/response in browser DevTools

## Troubleshooting

### Search returns 0 results

1. Check if concept files exist in `data/concepts/`
2. Verify `concept_index.pkl` is present
3. Check file paths in Python code

### Chat feature not working

1. Verify `GEMINI_API_KEY` is set in environment variables
2. Check API key is valid in Google Cloud console
3. Look for error messages in Render logs

### Slow search responses

- First search loads the embedding model (normal, ~10s)
- Subsequent searches are cached (normal, <1s)
- If consistently slow, check Render instance resources

### "Index not found" error on startup

1. Ensure all files were copied to `data/` directory
2. Verify directory structure matches expectations
3. Check file permissions

## Data Sources

This web service uses a pre-built search index containing ~2,850 concepts extracted from:

- C++ Primer (5th Edition)
- Effective Modern C++
- Inside the C++ Object Model
- Expert C Programming: Deep C Secrets
- And more...

Concepts include:
- Detailed explanations of C/C++ features
- Code examples demonstrating usage
- Syntax references and patterns
- Cross-references between related concepts

## License

This web service is part of the C/C++ Holy Grail project.

## Support

For issues or questions:
1. Check the [API Endpoints](#api-endpoints) documentation
2. Review logs on Render dashboard
3. Verify environment variables are set correctly
4. Check browser console for client-side errors

---

**Status**: Production-ready | **Last Updated**: 2025-10-31
