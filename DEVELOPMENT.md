# LiveDocAI - Development Documentation

## Document Grouper Implementation

### Overview
The Document Grouper automatically classifies, tags, and organizes documents. It analyzes content during upload and assigns relevant tags and group memberships.

### Components

**Backend:**
- `supabase/document_groups.sql` - Database schema (3 tables)
- `backend/app/document_grouper.py` - Classification engine
- `backend/app/routers/groups.py` - API endpoints
- Integration in ingestion pipeline

**Frontend:**
- `frontend/src/components/DocumentOrganization.jsx` - Main UI
- `frontend/src/components/TagManager.jsx` - Tag management
- `frontend/src/components/SensitivityBadge.jsx` - Sensitivity indicators

### How It Works

1. Document uploaded → Text extracted and chunked
2. Document Grouper analyzes content (pattern matching + optional LLM)
3. Tags generated (type, topic, sensitivity, time_period)
4. Groups created automatically (if needed)
5. Document assigned to groups
6. Status set to "ready"

### Tag Categories
- **type** - contract, report, memo, policy, invoice
- **topic** - legal, finance, technical, hr, marketing
- **sensitivity** - public, internal, confidential, anonymous
- **time_period** - FY2024, Q1_2024, etc.
- **custom** - User-defined

### API Endpoints
- `GET /groups/documents/{doc_id}/tags` - Get tags
- `POST /groups/documents/{doc_id}/tags` - Add tag
- `DELETE /groups/documents/{doc_id}/tags/{tag_id}` - Remove tag
- `GET /groups/tags/search?tag_names=...` - Search by tags
- `GET /groups` - List groups
- `POST /groups` - Create group
- `GET /groups/{group_id}/documents` - Get group documents
- `PUT /groups/documents/{doc_id}/groups` - Update membership

### Setup
See `SETUP.md` for detailed setup instructions.

### Features
See `FEATURES.md` for usage examples and patterns.

---

## Original Architecture Documentation



### 1. Why FastAPI?

**Chosen:** FastAPI (Python)

**Reasons:**
- **Native async/await** - Concurrent operations for embedding generation and API calls
- **Automatic OpenAPI docs** - Built-in API documentation at `/docs`
- **Strong typing** - Pydantic models for request/response validation
- **Performance** - Comparable to Node.js, faster than Django
- **AI/ML ecosystem** - Rich Python libraries (pdfplumber, tiktoken, LangChain)
- **Easy integration** - Seamless with Python-based AI tools

**Alternatives Considered:**
- Express.js - Less mature AI/ML ecosystem, would need TypeScript for typing
- Django - Heavier framework, overkill for API-only backend
- Flask - Less modern, no built-in async support

**AI Tool Assistance:**
- Cursor helped scaffold FastAPI project structure
- GitHub Copilot suggested Pydantic models for request validation
- ChatGPT provided async/await patterns for concurrent operations


### 2. Why Supabase?

**Chosen:** Supabase (PostgreSQL + Auth + Storage)

**Reasons:**
- **All-in-one solution** - Database, authentication, and file storage in one platform
- **Built-in Google OAuth** - No need to implement OAuth flow manually
- **Row-Level Security (RLS)** - Database-level data isolation between users
- **Real-time capabilities** - Future feature potential (live chat updates)
- **Generous free tier** - 500MB database, 1GB storage, 50K monthly active users
- **PostgreSQL reliability** - Battle-tested database with ACID compliance

**Alternatives Considered:**
- Firebase - Vendor lock-in, less SQL flexibility, NoSQL limitations
- Auth0 + AWS S3 + RDS - More complex setup, higher cost, multiple services to manage
- Self-hosted PostgreSQL - More maintenance overhead, need separate auth solution

**AI Tool Assistance:**
- Claude helped design RLS policies for user isolation
- Cursor suggested optimal indexes for query performance
- ChatGPT provided SQL migration patterns

**Override Decision:**
- AI suggested using Firebase initially, but I chose Supabase for better SQL support and RLS

### 3. Why Qdrant?

**Chosen:** Qdrant Cloud (Vector Database)

**Reasons:**
- **Purpose-built for vectors** - Optimized for similarity search
- **Excellent filtering** - Payload indexes for efficient user_id and document_id filtering
- **Cloud-hosted** - No infrastructure management, 1GB free tier
- **Better performance** - Faster than pgvector for large-scale vector search
- **Simple REST API** - Easy integration with Python client
- **Payload indexing** - Critical for multi-tenant security

**Alternatives Considered:**
- Pinecone - More expensive ($70/month after free tier), less flexible filtering
- Weaviate - More complex setup, heavier resource requirements
- pgvector (Supabase extension) - Slower for large datasets, limited filtering capabilities
- Chroma - Good for local dev, but less mature cloud offering

**AI Tool Assistance:**
- Kiro helped implement Qdrant client with proper error handling
- Copilot suggested batch upsert patterns for performance
- Gemini provided vector search optimization strategies

**Override Decision:**
- AI suggested Pinecone initially, but I chose Qdrant for cost and filtering capabilities


### 4. Why Google Gemini?

**Chosen:** Google Gemini API (gemini-embedding-001 + gemini-2.5-flash)

**Reasons:**
- **High-quality embeddings** - 768 dimensions, optimized for retrieval
- **Fast text generation** - gemini-2.5-flash optimized for speed
- **Generous free tier** - 1500 requests/day (vs OpenAI's 3 requests/min)
- **Single API** - Both embeddings and generation from one provider
- **Good multilingual support** - Works well with non-English documents
- **Competitive pricing** - $0.075/1M tokens (vs OpenAI $0.50/1M)
- **Long context window** - 1M tokens for complex documents

**Alternatives Considered:**
- OpenAI (GPT-4 + text-embedding-3) - More expensive, stricter rate limits, better quality
- Anthropic Claude - No native embedding model, would need separate service
- Cohere - Less mature ecosystem, fewer integrations
- Open-source models (Llama, Mistral) - Requires hosting, more complex setup

**AI Tool Assistance:**
- ChatGPT helped implement retry logic with exponential backoff
- Cursor suggested using two Gemini packages (google-genai for embeddings, google-generativeai for generation)
- Codium AI helped suppress deprecation warnings

**Override Decision:**
- AI suggested OpenAI initially for better quality, but I chose Gemini for cost and rate limits

### 5. Why React + Vite?

**Chosen:** React 18 + Vite

**Reasons:**
- **Fast development** - Hot Module Replacement (HMR) for instant updates
- **Modern build tooling** - Vite is 10-100x faster than Webpack
- **Large ecosystem** - Extensive component libraries and community support
- **Easy Supabase integration** - Official Supabase JS client
- **Component-based** - Reusable UI components
- **Familiar** - Most developers know React

**Alternatives Considered:**
- Next.js - Overkill for SPA, adds SSR complexity we don't need
- Vue.js - Smaller ecosystem, less familiar to most developers
- Svelte - Less mature, smaller community, fewer libraries
- Vanilla JS - Too much boilerplate, slower development

**AI Tool Assistance:**
- Cursor scaffolded React components with proper hooks
- GitHub Copilot suggested state management patterns
- ChatGPT provided CSS animations and responsive design


### 6. Why LangChain?

**Chosen:** LangChain for LLM orchestration

**Reasons:**
- **Abstraction layer** - Unified interface for different LLMs
- **Prompt templates** - Structured prompt management
- **Output parsing** - Consistent response handling
- **Chain composition** - Easy to build complex workflows
- **Future extensibility** - Can add agents, tools, memory easily

**Alternatives Considered:**
- Direct API calls - More control but more boilerplate
- LlamaIndex - Better for indexing, but overkill for our use case
- Custom abstraction - Reinventing the wheel

**AI Tool Assistance:**
- Claude helped design LangChain prompt templates
- Cursor suggested chain composition patterns
- ChatGPT provided error handling for LLM calls

---

## AI Tools Used

### Primary Tools

**1. Cursor (Primary IDE)**
- **Usage:** 60% of development time
- **Strengths:**
  - Excellent code completion with context awareness
  - Multi-file editing suggestions
  - Fast inline code generation
  - Good at scaffolding project structure
- **Examples:**
  - Generated FastAPI router boilerplate
  - Suggested Pydantic models for request validation
  - Auto-completed SQL queries with proper syntax
- **Limitations:**
  - Sometimes suggested outdated package versions
  - Occasionally missed edge cases in error handling

**2. Kiro (AI Assistant)**
- **Usage:** 25% of development time
- **Strengths:**
  - Great for debugging complex issues
  - Helped with Qdrant client implementation
  - Suggested performance optimizations
- **Examples:**
  - Fixed Qdrant index creation issues
  - Optimized batch embedding generation
  - Debugged JWT validation logic
- **Limitations:**
  - Sometimes verbose explanations when quick fix needed

**3. ChatGPT (Problem Solving)**
- **Usage:** 10% of development time
- **Strengths:**
  - Excellent for architectural discussions
  - Good at explaining complex concepts
  - Helpful for SQL query optimization
- **Examples:**
  - Designed RLS policies for Supabase
  - Explained vector similarity search algorithms
  - Suggested chunking strategies for RAG
- **Limitations:**
  - Sometimes suggested overly complex solutions

**4. Claude (Code Review & Architecture)**
- **Usage:** 5% of development time
- **Strengths:**
  - Excellent at code review and refactoring
  - Good at identifying security issues
  - Thoughtful architectural advice
- **Examples:**
  - Reviewed authentication flow for security
  - Suggested improvements to error handling
  - Helped design intent detection system
- **Limitations:**
  - Slower response times than other tools


**5. GitHub Copilot (Code Completion)**
- **Usage:** Throughout development (background)
- **Strengths:**
  - Fast inline suggestions
  - Good at repetitive code patterns
  - Helpful for boilerplate
- **Examples:**
  - Auto-completed import statements
  - Suggested test cases
  - Generated docstrings
- **Limitations:**
  - Sometimes suggested incorrect patterns
  - Needed manual review for complex logic

**6. Gemini (Research & Documentation)**
- **Usage:** 3% of development time
- **Strengths:**
  - Good for researching best practices
  - Helpful for documentation writing
- **Examples:**
  - Researched RAG implementation patterns
  - Helped write README documentation
- **Limitations:**
  - Less accurate for code generation

**7. Codium AI (Testing & Code Quality)**
- **Usage:** 2% of development time
- **Strengths:**
  - Good at suggesting test cases
  - Helpful for code quality checks
- **Examples:**
  - Suggested edge cases for error handling
  - Helped suppress deprecation warnings
- **Limitations:**
  - Limited integration with our stack

### Effective AI Assistance Examples

**Example 1: Qdrant Index Creation**
- **Problem:** Qdrant queries failing with "Index required but not found"
- **AI Tool:** Kiro
- **Solution:** Suggested creating payload indexes for user_id and document_id
- **Code Generated:**
```python
qdrant_client.create_payload_index(
    collection_name="document_chunks",
    field_name="user_id",
    field_schema="keyword"
)
```
- **Outcome:** Fixed filtering issues, improved query performance

**Example 2: Hybrid Chunking Strategy**
- **Problem:** Need to balance semantic coherence with token limits
- **AI Tool:** ChatGPT
- **Solution:** Suggested paragraph-based chunking with token-based splitting
- **Code Generated:**
```python
def chunk_by_paragraphs_and_tokens(pages, max_tokens=700, overlap=100):
    # Split by paragraphs first
    paragraphs = split_by_paragraphs(pages)
    # Merge small paragraphs
    merged = merge_small_chunks(paragraphs, min_tokens=50)
    # Split large paragraphs
    final_chunks = split_large_chunks(merged, max_tokens, overlap)
    return final_chunks
```
- **Outcome:** Better retrieval quality, preserved semantic boundaries

**Example 3: Intent Detection System**
- **Problem:** Need to optimize prompts for different query types
- **AI Tool:** Claude
- **Solution:** Suggested rule-based intent detection with 8 categories
- **Code Generated:**
```python
def detect_intent(query: str) -> IntentType:
    q_lower = query.lower()
    if any(kw in q_lower for kw in ['what is', 'who is', 'when']):
        return IntentType.FACTUAL
    elif any(kw in q_lower for kw in ['compare', 'difference']):
        return IntentType.COMPARISON
    # ... more patterns
```
- **Outcome:** Better answer quality, more relevant responses


### Where I Overrode AI Suggestions

**1. Vector Database Choice**
- **AI Suggested:** Pinecone (more popular, better docs)
- **I Chose:** Qdrant
- **Reason:** Better filtering capabilities, lower cost, payload indexing
- **Outcome:** Saved $70/month, better multi-tenant security

**2. Embedding Model**
- **AI Suggested:** OpenAI text-embedding-3-large (1536 dimensions)
- **I Chose:** Gemini gemini-embedding-001 (768 dimensions)
- **Reason:** Free tier limits, cost efficiency, good enough quality
- **Outcome:** 1500 free requests/day vs 3 requests/min

**3. Chunking Strategy**
- **AI Suggested:** Fixed 512-token chunks with 50-token overlap
- **I Chose:** Hybrid paragraph + token-based (700 tokens, 100 overlap)
- **Reason:** Preserve semantic boundaries, better context
- **Outcome:** Improved retrieval quality, fewer broken sentences

**4. Authentication**
- **AI Suggested:** Custom JWT implementation with refresh tokens
- **I Chose:** Supabase Auth with Google OAuth
- **Reason:** Less code to maintain, built-in security, faster development
- **Outcome:** Saved 2-3 days of development time

**5. Frontend State Management**
- **AI Suggested:** Redux Toolkit for global state
- **I Chose:** React useState and useEffect
- **Reason:** Simple app, no need for complex state management
- **Outcome:** Less boilerplate, faster development

**6. Error Handling**
- **AI Suggested:** Try-catch on every function
- **I Chose:** Centralized error handling with FastAPI exception handlers
- **Reason:** DRY principle, consistent error responses
- **Outcome:** Cleaner code, easier debugging

---

## Database Schema & Rationale

### Core Tables

**1. user_profiles**
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT NOT NULL,
  full_name TEXT,
  company TEXT,
  role TEXT,
  onboarding_completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Rationale:**
- Separate from auth.users for custom fields
- Onboarding flag for UX flow
- Company/role for future analytics

**2. documents**
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  file_size BIGINT DEFAULT 0,
  status TEXT CHECK (status IN ('processing', 'ready', 'failed')),
  file_hash TEXT,  -- For deduplication
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Rationale:**
- Metadata only (files in Storage, vectors in Qdrant)
- Status tracking for async processing
- file_hash for duplicate detection
- Indexes on user_id and status for fast queries


**3. chat_sessions (Optional)**
```sql
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  title TEXT,
  document_id UUID REFERENCES documents(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Rationale:**
- Groups related Q&A pairs
- Auto-generates title from first question
- Links to specific document (optional)

**4. chat_messages (Optional)**
```sql
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  document_scope TEXT DEFAULT 'all',
  sources JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Rationale:**
- Stores Q&A pairs with sources
- JSONB for flexible source metadata
- document_scope for filtering context

### Row-Level Security (RLS)

**Why RLS?**
- Database-level security (defense in depth)
- Automatic filtering by user_id
- No risk of application-level bugs exposing data
- Works with Supabase client automatically

**Example Policy:**
```sql
CREATE POLICY "Users can read own documents"
  ON documents FOR SELECT
  USING (auth.uid() = user_id);
```

**Benefits:**
- Users can only see their own data
- Enforced at database level
- No need for WHERE clauses in application code

### Indexes

**Performance Indexes:**
```sql
CREATE INDEX documents_user_id_idx ON documents(user_id);
CREATE INDEX documents_status_idx ON documents(status);
CREATE INDEX documents_file_hash_idx ON documents(file_hash);
CREATE INDEX documents_user_hash_idx ON documents(user_id, file_hash);
```

**Rationale:**
- user_id: Fast user document lookups
- status: Filter by processing state
- file_hash: Duplicate detection
- Composite index: User-scoped duplicate checks

---

## Authentication & Session Management

### Google OAuth Flow

**1. User clicks "Sign in with Google"**
```javascript
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: window.location.origin
  }
});
```

**2. Supabase handles OAuth**
- Redirects to Google
- User grants permissions
- Google returns authorization code
- Supabase exchanges code for tokens

**3. Supabase returns JWT**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

**4. Frontend stores token**
```javascript
// Stored in localStorage automatically by Supabase client
localStorage.setItem('supabase.auth.token', JSON.stringify(session));
```

**5. All API requests include token**
```javascript
fetch('/api/documents', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
});
```


### JWT Validation (Backend)

**1. Extract token from Authorization header**
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
```

**2. Validate JWT signature**
```python
from jwt import PyJWKClient
import jwt

# Get Supabase public key
jwks_url = f"{SUPABASE_URL}/auth/v1/jwks"
jwks_client = PyJWKClient(jwks_url)
signing_key = jwks_client.get_signing_key_from_jwt(token)

# Verify signature
decoded = jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    audience="authenticated"
)
```

**3. Extract user_id**
```python
user_id = decoded["sub"]
email = decoded.get("email")
```

**4. Use in all queries**
```python
# Database query
documents = supabase.table("documents").select("*").eq("user_id", user_id).execute()

# Vector search
results = qdrant_client.query_points(
    collection_name="document_chunks",
    query=embedding,
    query_filter=Filter(must=[
        FieldCondition(key="user_id", match=MatchValue(value=user_id))
    ])
)
```

### Session Management

**Token Refresh:**
- Supabase client handles refresh automatically
- Refresh token stored in localStorage
- Access token refreshed before expiry

**Logout:**
```javascript
await supabase.auth.signOut();
// Clears localStorage and redirects to login
```

**Security Features:**
- JWT signed with RS256 (asymmetric)
- Short-lived access tokens (1 hour)
- Refresh tokens for seamless renewal
- No password storage (delegated to Google)

---

## API Design Choices

### RESTful Design

**Endpoints follow REST conventions:**
- `GET /documents` - List resources
- `POST /documents/upload` - Create resource
- `GET /documents/{id}` - Get specific resource
- `DELETE /documents/{id}` - Delete resource

**Why REST?**
- Simple and well-understood
- Easy to test with curl/Postman
- Good for CRUD operations
- No need for GraphQL complexity

### Request/Response Models

**Pydantic for validation:**
```python
class ChatRequest(BaseModel):
    question: str
    document_id: str | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    intent: str
```

**Benefits:**
- Automatic validation
- Type safety
- Auto-generated OpenAPI docs
- Clear API contracts

### Error Handling

**Centralized exception handlers:**
```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

**Consistent error format:**
```json
{
  "detail": "Document not found",
  "error_code": "DOCUMENT_NOT_FOUND"
}
```


### CORS Configuration

**Allow frontend origin:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:** Update to production frontend URL

---

## AI Integration Approach

### Retrieval-Augmented Generation (RAG)

**Why RAG?**
- Grounds answers in actual document content
- Reduces hallucination
- Provides source citations
- Works with private documents

**RAG Pipeline:**

**1. Document Ingestion**
```python
# Extract text
pages = extract_text_from_pdf(file_content)

# Chunk text
chunks = chunk_by_paragraphs_and_tokens(pages, max_tokens=700, overlap=100)

# Generate embeddings
embeddings = generate_embeddings([chunk['content'] for chunk in chunks])

# Store in Qdrant
qdrant_client.upsert(
    collection_name="document_chunks",
    points=[{
        "id": str(uuid.uuid4()),
        "vector": embedding,
        "payload": {
            "user_id": user_id,
            "document_id": document_id,
            "content": chunk['content'],
            "page_start": chunk['page_start'],
            "page_end": chunk['page_end']
        }
    } for chunk, embedding in zip(chunks, embeddings)]
)
```

**2. Query Processing**
```python
# Detect intent
intent = detect_intent(question, document_scope)

# Generate query embedding
query_embedding = generate_embeddings([question])[0]

# Search Qdrant
results = qdrant_client.query_points(
    collection_name="document_chunks",
    query=query_embedding,
    query_filter=Filter(must=[
        FieldCondition(key="user_id", match=MatchValue(value=user_id))
    ]),
    limit=8,
    score_threshold=0.2
)

# Format context based on intent
context = format_context_by_intent(results, intent)

# Generate answer
prompt = get_prompt_template(intent, question, context)
answer = llm.invoke(prompt)
```

### Intent Detection

**8 Intent Types:**
1. **FACTUAL** - "What is X?" → Direct fact retrieval
2. **COMPARISON** - "Compare X and Y" → Side-by-side analysis
3. **SUMMARY** - "Summarize..." → Condensed overview
4. **EXPLANATION** - "Explain how..." → Detailed explanation
5. **PROCEDURAL** - "How to..." → Step-by-step instructions
6. **ANALYTICAL** - "Analyze..." → Deep insights
7. **DEFINITION** - "Define X" → Term definition
8. **GENERAL** - Fallback for other queries

**Implementation:**
```python
def detect_intent(query: str, document_scope: str) -> IntentType:
    q_lower = query.lower()
    
    # Keyword matching
    if any(kw in q_lower for kw in ['what is', 'who is', 'when', 'where']):
        return IntentType.FACTUAL
    elif any(kw in q_lower for kw in ['compare', 'difference', 'versus']):
        return IntentType.COMPARISON
    elif any(kw in q_lower for kw in ['summarize', 'summary', 'overview']):
        return IntentType.SUMMARY
    # ... more patterns
    
    return IntentType.GENERAL
```

**Why rule-based?**
- Fast and deterministic
- No additional API calls
- Easy to debug and extend
- Sufficient accuracy for 8 categories


### Prompt Engineering

**Intent-Specific Prompts:**

**FACTUAL Intent:**
```python
prompt = f"""You are a helpful assistant answering questions based on provided documents.

Question: {question}

Context from documents:
{context}

Instructions:
- Provide a direct, factual answer
- Cite specific sources with [Source: filename, Page X]
- If information is not in the context, say so
- Be concise and accurate

Answer:"""
```

**ANALYTICAL Intent:**
```python
prompt = f"""You are an analytical assistant helping users understand documents deeply.

Question: {question}

Context from documents:
{context}

Instructions:
- Provide a thorough analysis
- Identify patterns, trends, and implications
- Support claims with evidence from sources
- Cite sources with [Source: filename, Page X]
- Structure your analysis clearly

Analysis:"""
```

**Benefits:**
- Better answer quality for each intent type
- Consistent citation format
- Reduced hallucination
- Clearer instructions for the model

### Chunking Strategy

**Hybrid Approach:**
1. Split by paragraphs (preserve semantic boundaries)
2. Merge small paragraphs (< 100 tokens)
3. Split large paragraphs (> 700 tokens with 100 overlap)

**Code:**
```python
def chunk_by_paragraphs_and_tokens(pages, max_tokens=700, overlap=100):
    # Split by double newline
    paragraphs = []
    for page in pages:
        paras = page['text'].split('\n\n')
        paragraphs.extend([{
            'text': p.strip(),
            'page': page['page']
        } for p in paras if p.strip()])
    
    # Merge small paragraphs
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        tokens = count_tokens(para['text'])
        
        if tokens > max_tokens:
            # Split large paragraph
            chunks.extend(split_large_paragraph(para, max_tokens, overlap))
        else:
            if current_tokens + tokens > max_tokens:
                chunks.append(merge_paragraphs(current_chunk))
                current_chunk = [para]
                current_tokens = tokens
            else:
                current_chunk.append(para)
                current_tokens += tokens
    
    return chunks
```

**Why this approach?**
- Preserves semantic boundaries (paragraphs)
- Handles both short and long paragraphs
- Overlap ensures context continuity
- 700 tokens fits well in embedding model (2048 max)

### Embedding Generation

**Batch Processing:**
```python
async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = await client.models.embed_content_async(
            model='gemini-embedding-001',
            contents=batch
        )
        all_embeddings.extend([e.values for e in response.embeddings])
    
    return all_embeddings
```

**Benefits:**
- Faster processing (100 texts per request)
- Fewer API calls
- Better rate limit utilization


### Vector Search

**Qdrant Query:**
```python
results = qdrant_client.query_points(
    collection_name="document_chunks",
    query=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
    ),
    limit=8,
    score_threshold=0.2
)
```

**Key Parameters:**
- `limit=8` - Balance between context and token limits
- `score_threshold=0.2` - Filter out irrelevant chunks
- `user_id` filter - Mandatory for security

**Why these values?**
- 8 chunks × 700 tokens = 5600 tokens (fits in context window)
- 0.2 threshold filters noise while keeping relevant results
- User filter ensures data isolation

---

## Trade-offs & Time Constraints

### What I Prioritized

**1. Core RAG Functionality**
- ✅ Document upload and processing
- ✅ Semantic search with Qdrant
- ✅ AI-powered Q&A with citations
- ✅ User authentication and isolation

**Reason:** These are the essential features that demonstrate the system works

**2. User Experience**
- ✅ Clean, modern UI
- ✅ Loading states and error messages
- ✅ Responsive design
- ✅ Smooth animations

**Reason:** Good UX shows attention to detail and polish

**3. Security**
- ✅ JWT authentication
- ✅ Row-Level Security (RLS)
- ✅ User data isolation
- ✅ Secure file storage

**Reason:** Security is non-negotiable for production systems

### What I Deprioritized

**1. Advanced Features**
- ❌ Multi-document comparison
- ❌ Document versioning
- ❌ Collaborative features
- ❌ Advanced analytics

**Reason:** Nice-to-have features that don't demonstrate core competency

**2. Performance Optimization**
- ⚠️ Basic caching only
- ⚠️ No CDN for static assets
- ⚠️ No database query optimization beyond indexes

**Reason:** Premature optimization; can be added later

**3. Testing**
- ⚠️ Manual testing only
- ❌ No unit tests
- ❌ No integration tests
- ❌ No E2E tests

**Reason:** Time constraint; would add in production

**4. Monitoring & Observability**
- ❌ No application monitoring
- ❌ No error tracking (Sentry)
- ❌ No performance metrics
- ❌ Basic logging only

**Reason:** Important for production but not for demo

### What Would I Improve With More Time?

**1. Testing (1-2 weeks)**
- Unit tests for core functions
- Integration tests for API endpoints
- E2E tests for critical user flows
- Test coverage > 80%

**2. Performance (1 week)**
- Redis caching for query embeddings
- Database query optimization
- CDN for static assets
- Lazy loading for large documents

**3. Advanced RAG (1-2 weeks)**
- Hybrid search (semantic + keyword)
- Query expansion with synonyms
- Re-ranking with cross-encoder
- Multi-query retrieval

**4. User Features (1 week)**
- Document folders/organization
- Sharing documents with team
- Export chat history
- Advanced search filters

**5. Monitoring (3-4 days)**
- Sentry for error tracking
- Datadog/New Relic for APM
- Custom metrics dashboard
- Alert system for failures

**6. Documentation (2-3 days)**
- API documentation with examples
- Architecture diagrams
- Deployment guide
- Troubleshooting guide


---

## Production Considerations

### Addressed

**1. Security**
- ✅ JWT authentication with Supabase
- ✅ Row-Level Security (RLS) for data isolation
- ✅ HTTPS for all API calls (Supabase/Qdrant)
- ✅ Environment variables for secrets
- ✅ No hardcoded credentials

**2. Scalability**
- ✅ Cloud-hosted services (Supabase, Qdrant)
- ✅ Async processing for embeddings
- ✅ Batch operations for efficiency
- ✅ Stateless API (horizontal scaling ready)

**3. Error Handling**
- ✅ Try-catch blocks for external API calls
- ✅ Retry logic with exponential backoff
- ✅ User-friendly error messages
- ✅ Logging for debugging

**4. Data Privacy**
- ✅ User data isolation (RLS + Qdrant filters)
- ✅ Secure file storage (Supabase Storage)
- ✅ No data sharing between users
- ✅ GDPR-friendly (can delete all user data)

**5. Cost Optimization**
- ✅ Free tiers for all services
- ✅ Batch processing to reduce API calls
- ✅ Efficient chunking to minimize storage
- ✅ Gemini API (cheaper than OpenAI)

### Skipped (Would Add for Production)

**1. Rate Limiting**
- ❌ No rate limiting on API endpoints
- ❌ No protection against abuse
- **Impact:** Could be exploited for DoS
- **Solution:** Add rate limiting middleware (e.g., slowapi)

**2. Monitoring & Alerting**
- ❌ No application monitoring
- ❌ No error tracking
- ❌ No performance metrics
- **Impact:** Hard to debug production issues
- **Solution:** Add Sentry, Datadog, or similar

**3. Backup & Recovery**
- ❌ No automated backups
- ❌ No disaster recovery plan
- **Impact:** Data loss risk
- **Solution:** Supabase has automated backups (paid tier)

**4. Load Testing**
- ❌ No load testing performed
- ❌ Unknown system limits
- **Impact:** May fail under high load
- **Solution:** Use Locust or k6 for load testing

**5. CI/CD Pipeline**
- ❌ No automated deployment
- ❌ No automated testing
- **Impact:** Manual deployment errors
- **Solution:** GitHub Actions for CI/CD

**6. Database Migrations**
- ❌ No migration system
- ❌ Schema changes require manual SQL
- **Impact:** Hard to track schema changes
- **Solution:** Use Alembic or Supabase migrations

**7. API Versioning**
- ❌ No API versioning
- **Impact:** Breaking changes affect all clients
- **Solution:** Add /v1/ prefix to all endpoints

**8. Caching**
- ❌ No caching layer
- **Impact:** Repeated queries hit API every time
- **Solution:** Redis for query embedding cache

**9. Content Moderation**
- ❌ No content filtering
- ❌ No abuse detection
- **Impact:** Users could upload inappropriate content
- **Solution:** Add content moderation API

**10. Compliance**
- ❌ No audit logs
- ❌ No data retention policies
- **Impact:** May not meet regulatory requirements
- **Solution:** Add audit logging, implement retention policies


### Deployment Checklist

**Before Production:**

**1. Environment Variables**
- [ ] Update SUPABASE_URL to production
- [ ] Update QDRANT_URL to production cluster
- [ ] Rotate all API keys
- [ ] Set CORS to production frontend URL
- [ ] Enable HTTPS only

**2. Database**
- [ ] Run all SQL migrations
- [ ] Verify RLS policies
- [ ] Create database backups
- [ ] Set up monitoring

**3. Security**
- [ ] Enable rate limiting
- [ ] Add API key rotation
- [ ] Set up WAF (Web Application Firewall)
- [ ] Enable DDoS protection
- [ ] Add security headers

**4. Monitoring**
- [ ] Set up error tracking (Sentry)
- [ ] Add performance monitoring
- [ ] Create alerting rules
- [ ] Set up log aggregation

**5. Performance**
- [ ] Add Redis caching
- [ ] Enable CDN for static assets
- [ ] Optimize database queries
- [ ] Add connection pooling

**6. Testing**
- [ ] Run load tests
- [ ] Test failure scenarios
- [ ] Verify backup/restore
- [ ] Test scaling

**7. Documentation**
- [ ] Update README with production URLs
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document API endpoints

---

## Lessons Learned

### What Worked Well

**1. AI-Assisted Development**
- Cursor dramatically sped up boilerplate code
- ChatGPT excellent for architectural discussions
- Claude great for code review and security

**2. Cloud Services**
- Supabase saved weeks of auth implementation
- Qdrant Cloud eliminated vector DB hosting complexity
- Gemini API provided good quality at low cost

**3. Modern Stack**
- FastAPI's async support handled concurrent operations well
- React + Vite provided fast development experience
- LangChain simplified LLM integration

### What I'd Do Differently

**1. Start with Tests**
- Should have written tests from the beginning
- Would have caught bugs earlier
- Would have made refactoring easier

**2. Better Error Handling**
- Should have planned error handling strategy upfront
- Would have saved debugging time
- Would have improved user experience

**3. More Planning**
- Should have spent more time on architecture design
- Would have avoided some refactoring
- Would have made better technology choices

**4. Documentation as I Go**
- Should have documented decisions immediately
- Would have saved time writing this document
- Would have captured reasoning better

### Key Takeaways

**1. AI Tools Are Powerful But Not Perfect**
- Great for boilerplate and common patterns
- Need human oversight for architecture decisions
- Best used as assistants, not replacements

**2. Cloud Services Save Time**
- Don't reinvent the wheel
- Use managed services when possible
- Focus on core business logic

**3. Security First**
- Implement security from the start
- Don't treat it as an afterthought
- Use proven solutions (Supabase Auth, RLS)

**4. Simple Is Better**
- Start with simple solutions
- Add complexity only when needed
- Avoid premature optimization

**5. User Experience Matters**
- Good UX shows attention to detail
- Loading states and error messages are important
- Polish makes a difference

---

## Conclusion

DocuChat demonstrates a production-ready RAG system built with modern tools and best practices. The architecture prioritizes:

1. **User privacy** - Complete data isolation with RLS and Qdrant filters
2. **Answer quality** - Intent-aware prompting and hybrid chunking
3. **Developer experience** - Clear code structure and comprehensive docs
4. **Cost efficiency** - Free tiers for all services
5. **Scalability** - Cloud-hosted services ready for growth

The project showcases effective use of AI tools (Cursor, Kiro, ChatGPT, Claude, Copilot, Gemini, Codium) while maintaining human oversight for critical decisions. Trade-offs were made consciously to deliver core functionality within time constraints, with clear paths for future improvements.

For questions or contributions, see the main [README.md](README.md).

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Author:** Yash Darji  
**Role:** Backend Engineer – AI & Agent Systems  
**LinkedIn:** https://www.linkedin.com/in/yash-darji/  
**GitHub:** https://github.com/yshraj  
**Portfolio:** https://yashdarjiportfolio.netlify.app/
