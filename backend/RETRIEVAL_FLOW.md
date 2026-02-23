# RAG Retrieval Flow Documentation

Complete documentation of the Retrieval-Augmented Generation (RAG) pipeline in DocuChat.

---

## Overview

The RAG system consists of two main phases:
1. **Ingestion** - Process documents and store embeddings
2. **Retrieval** - Query documents and generate answers

---

## Phase 1: Document Ingestion

### Step 1: Document Upload
**File:** `backend/app/routers/documents.py`

```
User uploads PDF/TXT → FastAPI endpoint → Validation
```

**Validation:**
- File type: PDF or TXT only
- File size: Max 10MB per file
- User authentication: Valid JWT required

### Step 2: Text Extraction
**File:** `backend/app/ingestion.py`

**For PDF:**
```python
pdfplumber.open() → Extract text per page → Normalize text
```

**For TXT:**
```python
Decode UTF-8 → Normalize text → Single page
```

**Normalization:**
- Remove null characters
- Collapse multiple whitespace
- Collapse multiple newlines (max 2)
- Trim whitespace

**Output:** List of `{page: int, text: str}`

### Step 3: Hybrid Chunking
**File:** `backend/app/ingestion.py` → `chunk_text_hybrid()`

**Strategy:** Paragraph-aware + Token-based

**Parameters:**
- `max_tokens`: 700 tokens per chunk
- `overlap_tokens`: 100 tokens overlap between chunks

**Algorithm:**
1. Split text into paragraphs (by `\n\n`)
2. Accumulate paragraphs until reaching max_tokens
3. If single paragraph > max_tokens:
   - Split by sentences
   - Create chunks with overlap
4. Add overlap from previous chunk (last 100 tokens)

**Output:** List of chunks with metadata:
```python
{
    "chunk_index": int,
    "content": str,
    "page_start": int,
    "page_end": int,
    "token_count": int
}
```

### Step 4: Generate Embeddings
**File:** `backend/app/ingestion.py` → `generate_embeddings()`

**API:** `google-genai` (new package)

**Model:** `models/gemini-embedding-001`

**Process:**
```python
texts → Batch (100 texts) → Gemini API → Embeddings (3072 dims)
```

**Batch Processing:**
- Process 100 texts at a time
- Respects rate limits
- Returns list of embedding vectors

**Output:** List of `list[float]` (3072 dimensions each)

### Step 5: Store in Qdrant
**File:** `backend/app/ingestion.py` → `upsert_chunks_to_qdrant()`

**Collection:** `document_chunks`

**Vector Config:**
- Size: 3072 dimensions
- Distance: Cosine similarity

**Payload Indexes:**
- `user_id` (KEYWORD) - For user isolation
- `document_id` (KEYWORD) - For document filtering

**Point Structure:**
```python
{
    "id": uuid,
    "vector": [3072 floats],
    "payload": {
        "user_id": str,
        "document_id": str,
        "chunk_index": int,
        "page_start": int,
        "page_end": int,
        "filename": str,
        "content": str,
        "token_count": int
    }
}
```

**Status Update:** Document status → `ready`

---

## Phase 2: Query & Retrieval

### Step 1: User Query
**File:** `backend/app/routers/chat.py`

```
User asks question → POST /chat → JWT validation → Extract user_id
```

**Input:**
```json
{
    "question": "What is this document about?",
    "document_id": "uuid" | "all"
}
```

### Step 2: Generate Query Embedding
**File:** `backend/app/retrieval.py` → `retrieve_relevant_chunks()`

**Process:**
```python
question → generate_embeddings([question]) → query_embedding (3072 dims)
```

**Same model as ingestion:** `gemini-embedding-001`

### Step 3: Build Qdrant Filter
**File:** `backend/app/retrieval.py`

**Mandatory Filter:**
```python
Filter(must=[
    FieldCondition(key="user_id", match=user_id)  # ALWAYS required
])
```

**Optional Filter:**
```python
# If specific document selected
Filter(must=[
    FieldCondition(key="user_id", match=user_id),
    FieldCondition(key="document_id", match=document_id)
])
```

**Security:** User can ONLY query their own documents

### Step 4: Semantic Search
**File:** `backend/app/retrieval.py`

**API:** `client.query_points()`

**Parameters:**
```python
{
    "collection_name": "document_chunks",
    "query": query_embedding,  # 3072 dims
    "query_filter": filter,    # user_id + optional document_id
    "limit": 8                 # top_k chunks
}
```

**Similarity:** Cosine similarity between query and chunk embeddings

**Output:** List of points sorted by similarity score (0-1)

### Step 5: Post-Processing
**File:** `backend/app/retrieval.py`

**Filtering:**
1. **Score threshold:** Remove chunks with score < 0.2
2. **Deduplication:** Remove chunks with identical content
3. **Metadata extraction:** Extract filename, page numbers, content

**Output:**
```python
[
    {
        "content": str,
        "document_id": str,
        "filename": str,
        "page_start": int,
        "page_end": int,
        "chunk_index": int,
        "score": float  # 0-1
    },
    ...
]
```

### Step 6: Build Context
**File:** `backend/app/retrieval.py` → `generate_answer()`

**Format:**
```
[Source 1 | page 5 | document.pdf | relevance: 0.85]
<chunk content>

[Source 2 | page 7 | document.pdf | relevance: 0.78]
<chunk content>
...
```

**Purpose:** Provide structured context with metadata for citations

### Step 7: Generate Answer
**File:** `backend/app/retrieval.py`

**API:** `google-generativeai` (old package)

**Models (tried in order):**
1. `models/gemini-2.5-flash` (primary - fastest)
2. `models/gemini-2.0-flash` (fallback)
3. `models/gemini-flash-latest` (fallback)

**Prompt Structure:**
```
You are a helpful assistant that answers questions based ONLY on provided document excerpts.

Context from documents:
[structured context with sources]

Question: {user_question}

Instructions:
- Answer using ONLY the context
- Cite sources (filename, page)
- Be concise and accurate
- Say if information is insufficient
```

**Output:** Generated answer with citations

### Step 8: Format Sources
**File:** `backend/app/retrieval.py` → `rag_query()`

**Deduplication:** Keep highest-scoring chunk per document

**Snippet Creation:**
- First 150 characters of chunk content
- Add "..." if truncated

**Sorting:** By filename, then page number

**Output:**
```python
{
    "answer": str,
    "sources": [
        {
            "document_id": str,
            "filename": str,
            "page_start": int,
            "page_end": int,
            "chunk_index": int,
            "snippet": str  # 150 chars
        },
        ...
    ]
}
```

### Step 9: Return to User
**File:** `backend/app/routers/chat.py`

**Response:**
```json
{
    "answer": "According to document.pdf, page 5...",
    "sources": [
        {
            "document_id": "uuid",
            "filename": "document.pdf",
            "page_start": 5,
            "page_end": 5,
            "snippet": "The document discusses..."
        }
    ]
}
```

---

## Configuration Parameters

### Chunking
```python
max_chunk_tokens = 700      # Maximum tokens per chunk
chunk_overlap_tokens = 100  # Overlap between chunks
```

### Retrieval
```python
retrieval_top_k = 8         # Number of chunks to retrieve
retrieval_min_score = 0.2   # Minimum similarity threshold
```

### Models
```python
# Embeddings
embedding_model = "models/gemini-embedding-001"
embedding_dimensions = 3072

# Text Generation
generation_models = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-flash-latest"
]
```

---

## Performance Characteristics

### Chunking
- **Preserves context:** Paragraph-aware splitting
- **Overlap:** Prevents information loss at boundaries
- **Token-based:** Respects model context limits

### Retrieval
- **Fast:** Qdrant vector search with indexes
- **Accurate:** Cosine similarity for semantic matching
- **Secure:** Mandatory user_id filtering

### Generation
- **Fast:** gemini-2.5-flash (optimized for speed)
- **Accurate:** Strict prompt instructions for citations
- **Reliable:** Fallback models if primary fails

---

## Security Features

### User Isolation
- **Mandatory filtering:** Every query filters by user_id
- **Payload indexes:** Efficient filtering without data leakage
- **JWT validation:** All endpoints require authentication

### Data Privacy
- **No cross-user access:** Users can only query their documents
- **Secure storage:** User-scoped paths in Supabase Storage
- **RLS policies:** Row-level security in database

---

## Error Handling

### Ingestion Errors
- **PDF extraction fails:** Mark document as `failed`
- **Embedding fails:** Retry with exponential backoff
- **Qdrant fails:** Log error, mark document as `failed`

### Retrieval Errors
- **No chunks found:** Return friendly message
- **Embedding fails:** Return error to user
- **Generation fails:** Try fallback models, then return error

---

## Monitoring & Logging

### Key Metrics
- Chunks retrieved per query
- Average similarity scores
- Generation model used
- Query latency

### Logs
```python
logger.info("Retrieved %d chunks for user %s", len(chunks), user_id)
logger.info("Generated answer using %s", model_name)
logger.warning("Model %s failed, trying next...", model_name)
```

---

## Future Improvements

### Potential Enhancements
- [ ] Reranking with cross-encoder
- [ ] Hybrid BM25 + vector search
- [ ] Query expansion
- [ ] Multi-query retrieval
- [ ] Streaming responses
- [ ] Confidence scoring per chunk
- [ ] Semantic chunking (LlamaIndex)

---

## Summary

**Ingestion Flow:**
```
Upload → Extract → Chunk → Embed → Store (Qdrant)
```

**Retrieval Flow:**
```
Query → Embed → Search (Qdrant) → Filter → Generate → Cite → Return
```

**Key Features:**
- ✅ Hybrid chunking (paragraph + token)
- ✅ Semantic search (cosine similarity)
- ✅ User isolation (mandatory filtering)
- ✅ Source citations (page numbers + snippets)
- ✅ Fast generation (gemini-2.5-flash)
- ✅ Error handling (fallback models)
