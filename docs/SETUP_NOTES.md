# Setup Notes

## Current Implementation Status

The backend uses `google-generativeai` package (v0.8.6) which is deprecated but stable and working. The deprecation warnings are suppressed in the code.

### Why Not Using New Package

The new `google-genai` package has API compatibility issues with model names. The stable `google-generativeai` works perfectly for Phase 1 and will continue to work for the foreseeable future.

## Installation

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `google-generativeai>=0.3.0` (stable, working package)
- `pdfplumber>=0.11.0` (PDF extraction)
- `tiktoken>=0.5.0` (token counting)
- `qdrant-client>=1.7.0` (vector store)

## API Configuration

**Embedding Model**: `models/gemini-embedding-001` (3072 dimensions)
- Stable and reliable
- Free tier: 1500 requests/day
- Batch support for efficiency
- High-quality embeddings

**Generation Model**: `models/gemini-pro` (with fallback)
- Fast and accurate
- Large context window
- Free tier available

## Environment Variables

Required in `.env`:
```bash
GEMINI_API_KEY=your-key-here
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
```

## First Run

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start backend:
```bash
uvicorn app.main:app --reload --port 8000
```

3. The Qdrant collection will be created automatically on first document upload

## Troubleshooting

**"Failed to generate embeddings"**
- Check GEMINI_API_KEY is valid
- Verify API key has not expired
- Check rate limits (free tier: 1500 requests/day)

**"QDRANT_URL and QDRANT_API_KEY must be configured"**
- Verify Qdrant Cloud cluster is running
- Check API key is correct
- Ensure cluster URL includes https://

**Deprecation Warnings**
- These are suppressed in the code
- The package works perfectly despite being deprecated
- Migration to new package can be done in Phase 2

**Python Version Warning**
- Python 3.10 is supported but will reach EOL in 2026
- Consider upgrading to Python 3.11+ for long-term support
- Current implementation works fine with 3.10

**Document Stuck in "Processing"**
- Check backend logs for errors
- Verify Gemini API key is valid
- Check Qdrant connection
- Document may have failed (status will show "failed")

**Delete Button Stuck on "Deleting..."**
- This happens when document failed to process (no vectors in Qdrant)
- The delete still completes successfully
- Refresh the page to see updated list

## Vector Store

The embedding model uses 3072-dimensional vectors (gemini-embedding-001).

If you have existing data with different embeddings:
1. Delete the old collection in Qdrant dashboard
2. Re-upload documents to generate new embeddings
3. The collection will be recreated automatically with correct dimensions

## Performance

**Embedding Generation**:
- Batch size: 100 texts per request
- Rate limit friendly
- Automatic retry on transient failures

**Answer Generation**:
- Model: gemini-1.5-flash
- Context window: Large (handles 8 chunks easily)
- Response time: ~1-3 seconds typical

## Testing

Upload a test document and check:
1. Status changes from "processing" to "ready"
2. Backend logs show successful processing
3. Qdrant dashboard shows vectors in collection
4. Chat queries return relevant answers with citations

## Known Issues

1. Deprecation warnings (suppressed, not affecting functionality)
2. Delete button may appear stuck for failed documents (still works)
3. No progress indicator during upload (instant for small files)

All issues are cosmetic and don't affect core functionality.
