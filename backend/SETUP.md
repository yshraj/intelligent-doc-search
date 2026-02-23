# Backend Setup & Configuration

Complete guide for setting up and troubleshooting the DocuChat backend.

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Supabase (Auth, Database, Storage)
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Qdrant Cloud (Vector Store)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_key

# Gemini API (Embeddings + Text Generation)
GEMINI_API_KEY=your_gemini_key
GEMINI_API_KEY_2=  # Optional fallback key
```

### 3. Setup Database

Run the SQL scripts in Supabase SQL Editor:
- `supabase/schema.sql` - Creates tables and RLS policies
- `supabase/storage.sql` - Sets up storage bucket

### 4. Fix Qdrant Indexes (If Needed)

If you have an existing Qdrant collection without indexes:

```bash
python3 fix_qdrant_indexes.py
```

This creates required payload indexes for `user_id` and `document_id` filtering.

### 5. Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## API Configuration

### Gemini API Keys

The system uses **two packages** for Gemini API:

| Package | Purpose | Model | Warnings |
|---------|---------|-------|----------|
| `google-genai` | Embeddings | `gemini-embedding-001` | None ✅ |
| `google-generativeai` | Text Generation | `gemini-2.5-flash` | Suppressed ✅ |

**Why two packages?**
- New `google-genai` doesn't support text generation yet
- Old `google-generativeai` is deprecated but still works
- Warnings are suppressed in code

**Key Configuration:**
- `GEMINI_API_KEY` - Primary key (works for both)
- `GEMINI_API_KEY_2` - Optional fallback key

### Qdrant Configuration

**Required Payload Indexes:**
- `user_id` (KEYWORD) - For user isolation
- `document_id` (KEYWORD) - For document filtering

These are automatically created when:
- Creating a new collection
- Running `fix_qdrant_indexes.py`

**Collection Settings:**
- Name: `document_chunks`
- Vector Size: 3072 dimensions
- Distance: Cosine similarity

---

## RAG Pipeline

### Document Ingestion

1. **Upload** - PDF/TXT files (max 10MB)
2. **Extract** - Text extraction with pdfplumber
3. **Chunk** - Hybrid paragraph + token chunking (700 tokens, 100 overlap)
4. **Embed** - Generate embeddings with `gemini-embedding-001`
5. **Store** - Upsert to Qdrant with metadata

### Query & Retrieval

1. **Embed Query** - Generate query embedding
2. **Search** - Qdrant semantic search with filters
   - Filter by `user_id` (mandatory)
   - Optional filter by `document_id`
   - Top-k: 8 chunks
   - Min score: 0.2
3. **Generate** - Create answer with `gemini-2.5-flash`
4. **Cite** - Return answer with source citations

---

## Troubleshooting

### Error: "Index required but not found for user_id"

**Solution:**
```bash
python3 fix_qdrant_indexes.py
```

This creates the required payload indexes for filtering.

### Error: "API key expired"

**Check:**
1. Verify `GEMINI_API_KEY` is set correctly in `.env`
2. Test the key: `python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY')[:20])"`
3. If using `GEMINI_API_KEY_2`, ensure it's not expired

### Error: "QdrantClient has no attribute 'search'"

**Already Fixed** - The code now uses `query_points()` API.

If you see this error:
1. Ensure you have the latest code
2. Check qdrant-client version: `pip show qdrant-client`
3. Should be >= 1.7.0

### Deprecation Warnings

**Already Suppressed** - Warnings are filtered in code.

If you still see warnings:
1. They're harmless and can be ignored
2. Warnings are suppressed before imports in `retrieval.py`

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── auth.py              # JWT validation
│   ├── ingestion.py         # Document processing & embeddings
│   ├── retrieval.py         # RAG query & generation
│   └── routers/
│       ├── documents.py     # Document endpoints
│       └── chat.py          # Chat endpoints
├── requirements.txt         # Python dependencies
├── fix_qdrant_indexes.py   # Utility to fix indexes
├── SETUP.md                # This file (setup & troubleshooting)
└── RETRIEVAL_FLOW.md       # Complete RAG pipeline documentation
```

---

## Key Dependencies

```
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0

# Database & Auth
supabase>=2.0.0
PyJWT[crypto]>=2.8.0

# Document Processing
pdfplumber>=0.11.0
tiktoken>=0.5.0

# Vector Store
qdrant-client>=1.7.0

# AI/ML
google-genai>=0.3.0          # New API (embeddings)
google-generativeai>=0.3.0   # Old API (text generation)
```

---

## Security Features

- ✅ **User Isolation** - Mandatory `user_id` filtering on all queries
- ✅ **JWT Validation** - All endpoints require valid Supabase JWT
- ✅ **RLS Policies** - Row-level security in Supabase
- ✅ **Private Storage** - User-scoped file paths
- ✅ **Payload Indexes** - Efficient filtering without data leakage

---

## Performance Tuning

### Chunking Settings

```python
max_chunk_tokens = 700      # Chunk size
chunk_overlap_tokens = 100  # Overlap between chunks
```

### Retrieval Settings

```python
retrieval_top_k = 8         # Number of chunks to retrieve
retrieval_min_score = 0.2   # Minimum similarity threshold
```

Adjust in `backend/app/config.py` or via environment variables.

---

## Monitoring

### Check Collection Status

```python
from app.ingestion import get_qdrant_client
from app.config import settings

client = get_qdrant_client()
collection = client.get_collection(settings.qdrant_collection)
print(f"Points: {collection.points_count}")
print(f"Indexes: {collection.payload_schema}")
```

### Test Embeddings

```python
from app.ingestion import generate_embeddings

embeddings = generate_embeddings(["Test document"])
print(f"Dimensions: {len(embeddings[0])}")  # Should be 3072
```

### Test Text Generation

```python
from app.retrieval import generate_answer

chunks = [{
    'content': 'Test content',
    'filename': 'test.pdf',
    'page_start': 1,
    'page_end': 1,
    'score': 0.9
}]
answer = generate_answer("Test question?", chunks)
print(answer)
```

---

## Support

For issues or questions:
1. Check this SETUP.md file
2. Review **RETRIEVAL_FLOW.md** for RAG pipeline details
3. Review error messages in console
4. Check Supabase and Qdrant dashboards
5. Verify environment variables are set correctly

---

## Status

✅ All systems operational
- Qdrant API: Updated to `query_points()`
- Gemini API: Hybrid package approach (no warnings)
- Payload Indexes: Auto-created for filtering
- User Isolation: Enforced at all levels
