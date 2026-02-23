# RAG Implementation Guide

This document describes the complete RAG (Retrieval-Augmented Generation) pipeline implementation for LiveDocAI Phase 1.

## Overview

The RAG pipeline processes uploaded documents through the following stages:

1. **Upload & Validate** - File validation and storage
2. **Text Extraction** - Extract text from PDF/TXT files
3. **Chunking** - Split text into semantic chunks with overlap
4. **Embedding** - Generate vector embeddings using Gemini
5. **Storage** - Store vectors in Qdrant Cloud
6. **Retrieval** - Search relevant chunks for user queries
7. **Generation** - Generate answers using Gemini with context

## Architecture

```
User Upload → FastAPI → Supabase Storage
                ↓
         Background Task
                ↓
    Extract Text (pdfplumber)
                ↓
    Chunk Text (hybrid paragraph + token)
                ↓
    Generate Embeddings (Gemini)
                ↓
    Store Vectors (Qdrant Cloud)
                ↓
    Update Status → "ready"

User Query → Retrieve Chunks (Qdrant)
                ↓
    Generate Answer (Gemini + Context)
                ↓
    Return Answer + Sources
```

## Implementation Details

### 1. Text Extraction

**PDF Processing** (`pdfplumber`):
- Extracts text page by page
- Preserves page numbers for citations
- Handles multi-page documents

**Text Processing**:
- UTF-8 decoding with error handling
- Treated as single-page document

**Normalization**:
- Remove null characters
- Collapse multiple whitespace
- Trim leading/trailing spaces

### 2. Chunking Strategy

**Hybrid Paragraph + Token-based Chunking**:

Parameters:
- `MAX_TOKENS`: 700 tokens per chunk
- `OVERLAP`: 100 tokens between chunks

Algorithm:
1. Split each page into paragraphs (`\n\n`)
2. Accumulate paragraphs until token limit
3. When limit reached, save chunk and start new one with overlap
4. For oversized paragraphs, split by sentences
5. Preserve page numbers and chunk indices

Chunk Metadata:
```python
{
    "chunk_index": 0,
    "content": "chunk text...",
    "page_start": 1,
    "page_end": 1,
    "token_count": 523
}
```

### 3. Embeddings

**Model**: Gemini `embedding-001`

**Process**:
- Batch processing (10 texts per request)
- Task type: `retrieval_document`
- Rate limit handling with retries
- Vector size: 768 dimensions

### 4. Vector Storage (Qdrant Cloud)

**Collection**: `document_chunks`

**Configuration**:
- Distance metric: Cosine similarity
- Vector size: 768

**Point Structure**:
```python
{
    "id": "uuid",
    "vector": [0.1, 0.2, ...],  # 768-dim embedding
    "payload": {
        "user_id": "uuid",
        "document_id": "uuid",
        "chunk_index": 0,
        "page_start": 1,
        "page_end": 1,
        "filename": "document.pdf",
        "content": "chunk text...",
        "token_count": 523
    }
}
```

**Filtering**:
- All queries filtered by `user_id` (user isolation)
- Optional filter by `document_id` (single document queries)

### 5. Retrieval

**Query Process**:
1. Generate embedding for user question
2. Build filter (user_id + optional document_id)
3. Search Qdrant with cosine similarity
4. Return top-k chunks (default: 5)

**Result Format**:
```python
{
    "content": "chunk text",
    "document_id": "uuid",
    "filename": "document.pdf",
    "page_start": 1,
    "page_end": 1,
    "chunk_index": 0,
    "score": 0.85
}
```

### 6. Answer Generation

**Model**: Gemini `gemini-1.5-flash`

**Prompt Structure**:
```
You are a helpful assistant that answers questions based on provided document excerpts.

Context from documents:
[Source 1: filename.pdf, page 1]
<chunk content>

[Source 2: filename.pdf, page 3]
<chunk content>

Question: <user question>

Instructions:
- Answer using ONLY the information from the context
- If context doesn't contain enough information, say so
- Be concise and accurate
- Reference sources when relevant

Answer:
```

**Response**:
- Generated answer text
- List of source documents with page numbers
- Deduplicated by document_id

## API Endpoints

### POST /documents/upload

Upload and process document:
- Validates file type and size
- Stores in Supabase Storage
- Creates DB record with status "processing"
- Triggers background processing task
- Returns immediately with document metadata

### POST /chat

Query documents with RAG:
```json
{
  "question": "What are the key points?",
  "document_id": "uuid" // or "all"
}
```

Response:
```json
{
  "answer": "Based on the documents...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "document.pdf",
      "page_start": 1,
      "page_end": 2
    }
  ]
}
```

### DELETE /documents/{id}

Delete document:
- Removes from Supabase Storage
- Deletes DB record
- Removes all vectors from Qdrant

## Configuration

Required environment variables:

```bash
# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key

# Gemini API
GEMINI_API_KEY=your-gemini-key

# Optional: Chunking parameters
MAX_CHUNK_TOKENS=700
CHUNK_OVERLAP_TOKENS=100
QDRANT_COLLECTION=document_chunks
```

## Error Handling

**Processing Failures**:
- Document status set to "failed"
- Error logged for debugging
- User sees "failed" status in UI

**Query Failures**:
- Graceful degradation
- Clear error messages
- No partial results

**Rate Limiting**:
- Batch processing for embeddings
- Retry logic for transient failures
- Respects API rate limits

## Performance Considerations

**Upload**:
- Background processing (non-blocking)
- Status polling in UI (8-second intervals)

**Chunking**:
- Efficient token counting with tiktoken
- Character-based fallback if unavailable

**Embeddings**:
- Batch processing (10 per request)
- Parallel processing possible for large documents

**Retrieval**:
- Fast vector search with Qdrant
- Filtered by user_id (security + performance)
- Top-k limiting (default: 5 chunks)

## Security

**User Isolation**:
- All Qdrant queries filtered by user_id
- RLS policies in Supabase
- JWT validation on all endpoints

**Data Privacy**:
- User data never mixed in vector store
- Deletion removes all traces (storage + DB + vectors)

## Future Enhancements

Not in Phase 1, but possible:

- Semantic chunking (LlamaIndex/LangChain)
- Table extraction from PDFs
- OCR for scanned documents
- DOCX/HTML support
- Chunk storage in Supabase for debugging
- Confidence scoring
- Multi-query retrieval
- Reranking with cross-encoders
- Streaming responses
