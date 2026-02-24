# DocuChat - AI-Powered Document Q&A System

An intelligent document chat application that lets users upload PDFs and text files, then ask questions and receive AI-generated answers with precise source citations. Built with modern RAG (Retrieval-Augmented Generation) architecture.

## 🎯 Overview

DocuChat combines semantic search with large language models to provide accurate, context-aware answers from your documents. The system features intent detection, hybrid chunking strategies, and comprehensive source attribution.

## ✨ Key Features

- **Smart Document Processing** - Upload PDF/TXT files with automatic text extraction and intelligent chunking
- **Intent-Aware RAG** - 8 intent types for optimized query understanding and response generation
- **Semantic Search** - Vector-based retrieval using Qdrant for finding relevant content
- **Source Citations** - Every answer includes page numbers and text snippets from source documents
- **Google OAuth** - Secure authentication via Supabase
- **Chat History** - Save, search, and resume conversations
- **File Deduplication** - Automatic detection of duplicate uploads
- **User Isolation** - Complete data privacy with user-scoped access
- **Modern UI** - Clean, responsive interface with smooth animations
- **Backend Health Check** - Automatic detection of cold starts with user-friendly notifications

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Supabase (PostgreSQL database, authentication, file storage)
- Qdrant Cloud (vector database for embeddings)
- Google Gemini API (embeddings + text generation)
- LangChain (LLM orchestration)
- pdfplumber (PDF text extraction)

**Frontend:**
- React 18 + Vite
- Supabase JS Client
- Modern CSS with animations

**AI/ML:**
- `gemini-embedding-001` (768-dimensional embeddings)
- `gemini-2.5-flash` (text generation via LangChain)
- Intent detection with 8 query types
- Hybrid chunking (paragraph + token-based)

### System Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │─────▶│   FastAPI    │─────▶│  Supabase   │
│  Frontend   │      │   Backend    │      │  (Auth/DB)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├─────▶ Qdrant Cloud (Vectors)
                            │
                            └─────▶ Gemini API (AI)
```

### RAG Pipeline

**Document Ingestion:**
1. Upload PDF/TXT → Extract text with pdfplumber
2. Hybrid chunking (paragraph + token-based, 700 tokens, 100 overlap)
3. Generate embeddings with `gemini-embedding-001`
4. Store in Qdrant with metadata (user_id, document_id, page numbers)

**Query & Retrieval:**
1. Detect query intent (8 types: factual, comparison, summary, etc.)
2. Generate query embedding
3. Semantic search in Qdrant (filtered by user_id, top-8 chunks, min score 0.2)
4. Format context based on intent
5. Generate answer with `gemini-2.5-flash` via LangChain
6. Parse and return answer with source citations

For detailed architecture decisions and AI tool usage, see [DEVELOPMENT.md](DEVELOPMENT.md).

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Free accounts on:
  - [Supabase](https://supabase.com) (database, auth, storage)
  - [Qdrant Cloud](https://cloud.qdrant.io) (vector database)
  - [Google AI Studio](https://ai.google.dev) (Gemini API)

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/yshraj/intelligent-doc-search.git
cd intelligent-doc-search

# Backend setup
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment Variables

```bash
# Root directory - backend configuration
cp .env.example .env
# Edit .env with your credentials (see below)

# Frontend directory
cd frontend
cp .env.example .env
# Edit with your Supabase URL and anon key
```

**Root `.env` (Backend):**
```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Qdrant Cloud
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
```

**Frontend `.env`:**
```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_URL=http://localhost:8000
```

### 3. Setup Supabase Database

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run these scripts **in order**:

**a) Core Schema (`supabase/schema.sql`):**
- Creates `user_profiles` and `documents` tables
- Sets up Row-Level Security (RLS) policies
- Creates indexes for performance

**b) Storage Setup (`supabase/storage.sql`):**
- First, create bucket via Dashboard: Storage → New bucket → name: "documents", Private
- Then run the SQL to set up RLS policies for file access
- Path format: `{user_id}/{document_id}/{filename}`

**c) Chat History (`supabase/chat_history.sql`) - Optional:**
- Creates `chat_sessions` and `chat_messages` tables
- Auto-generates session titles from first question
- Enables conversation history feature

**d) File Deduplication (`supabase/add_file_hash.sql`) - Optional:**
- Adds `file_hash` column to documents table
- Creates indexes for fast duplicate detection
- Prevents re-uploading same file

3. Enable Google OAuth:
   - Go to Authentication → Providers → Google
   - Add your Google OAuth credentials
   - Set Site URL: `http://localhost:5173`
   - Add Redirect URL: `http://localhost:5173`

### 4. Setup Qdrant Cloud

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a cluster (1GB free tier)
3. Copy your cluster URL and API key
4. The collection will be created automatically on first document upload

**To manually create indexes (optional):**
```bash
cd backend
source .venv/bin/activate
python3 fix_qdrant_indexes.py
```

This creates payload indexes for:
- `user_id` (KEYWORD) - For user isolation
- `document_id` (KEYWORD) - For document filtering

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the app:** http://localhost:5173

## 🧪 Test Credentials

**No special credentials needed!** Any Google account works for authentication.

**Quick summary:**
- Sign in with any Gmail or Google Workspace account
- Upload any PDF or TXT file (< 10MB)
- Ask questions and get AI-powered answers
- Each user's data is completely isolated

**Sample test documents:**
- Research papers (arXiv, academic papers)
- Technical documentation (API docs, user manuals)
- Meeting notes or reports
- Any text-based PDF

## 📁 Project Structure

```
docuchat/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── auth.py              # JWT authentication
│   │   ├── ingestion.py         # Document processing & embeddings
│   │   ├── retrieval.py         # RAG query & answer generation
│   │   ├── intent_detection.py  # Query intent classification
│   │   └── routers/
│   │       ├── documents.py     # Document management endpoints
│   │       └── chat.py          # Chat/query endpoints
│   ├── requirements.txt         # Python dependencies
│   └── fix_qdrant_indexes.py   # Utility for Qdrant setup
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── lib/supabase.js     # Supabase client
│   │   └── assets/             # Static assets
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
├── supabase/
│   ├── schema.sql              # Database schema (REQUIRED)
│   ├── storage.sql             # Storage bucket setup (REQUIRED)
│   ├── chat_history.sql        # Chat history tables (optional)
│   └── add_file_hash.sql       # File deduplication (optional)
├── DEVELOPMENT.md              # Architecture & AI tools documentation
└── README.md                   # This file
```

## 🔧 Configuration

### RAG Pipeline Settings

Adjust in `backend/app/config.py` or via environment variables:

```python
# Chunking
max_chunk_tokens = 700          # Chunk size
chunk_overlap_tokens = 100      # Overlap between chunks

# Retrieval
retrieval_top_k = 8             # Number of chunks to retrieve
retrieval_min_score = 0.2       # Minimum similarity threshold

# Generation
max_output_tokens = 2048        # Max response length
```

### Intent Types

The system detects 8 query intent types for optimized prompting:
- **FACTUAL** - Direct fact retrieval ("What is X?")
- **COMPARISON** - Comparing concepts ("Compare X and Y")
- **SUMMARY** - Document summarization ("Summarize...")
- **EXPLANATION** - Detailed explanations ("Explain how...")
- **PROCEDURAL** - Step-by-step instructions ("How to...")
- **ANALYTICAL** - Analysis and insights ("Analyze...")
- **DEFINITION** - Term definitions ("Define X")
- **GENERAL** - Open-ended questions (fallback)

### Database Schema

**Core Tables:**
- `user_profiles` - User information and onboarding status
- `documents` - Document metadata (files in Storage, vectors in Qdrant)
- `chat_sessions` - Chat conversation sessions (optional)
- `chat_messages` - Individual Q&A pairs (optional)

**Security:**
- Row-Level Security (RLS) on all tables
- Users can only access their own data
- Storage paths scoped by user_id

**Indexes:**
- `documents_user_id_idx` - Fast user document lookups
- `documents_status_idx` - Filter by processing status
- `documents_file_hash_idx` - Duplicate detection (optional)

### Qdrant Collection

**Collection:** `document_chunks`

**Vector Configuration:**
- Dimensions: 768 (gemini-embedding-001)
- Distance: Cosine similarity

**Payload Schema:**
```json
{
  "user_id": "uuid",
  "document_id": "uuid",
  "filename": "string",
  "page_start": "integer",
  "page_end": "integer",
  "content": "string"
}
```

**Indexes:**
- `user_id` (KEYWORD) - Mandatory for all queries
- `document_id` (KEYWORD) - Optional document filtering

## 🐛 Troubleshooting

**Backend won't start:**
- Verify all environment variables in `.env`
- Check Python virtual environment is activated
- Ensure dependencies installed: `pip install -r requirements.txt`

**Upload fails:**
- Verify Supabase storage bucket "documents" exists (create via Dashboard)
- Run `supabase/storage.sql` for RLS policies
- Check file size < 10MB
- Ensure backend can connect to Supabase

**No search results:**
- Verify Qdrant connection (check URL and API key in `.env`)
- Run `python3 fix_qdrant_indexes.py` to create required indexes
- Check document status is "ready" in database (not "processing")
- Verify embeddings were generated (check Qdrant dashboard)

**Authentication issues:**
- Verify Google OAuth is enabled in Supabase (Authentication → Providers)
- Check redirect URLs match your frontend URL
- Ensure Site URL is set correctly in Supabase
- Clear browser cookies and try again

**Chat history not working:**
- Run `supabase/chat_history.sql` in Supabase SQL Editor
- Restart backend server
- Check browser console for errors

## 📚 API Endpoints

**Authentication:**
- All endpoints require `Authorization: Bearer <jwt_token>` header

**Documents:**
- `GET /documents` - List user's documents
- `POST /documents/upload` - Upload new document
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document
- `POST /documents/clear-all` - Delete all user documents

**Chat:**
- `POST /chat/query` - Ask question and get answer
- `POST /chat/suggestions` - Get suggested questions

**Chat History (if enabled):**
- `GET /chat/history` - List chat sessions
- `GET /chat/history/{session_id}` - Get session messages
- `DELETE /chat/history/{session_id}` - Delete session

## 🚀 Deployment

### Backend Cold Start Handling

If deploying the backend on Render's free tier or similar platforms with cold starts:

The frontend includes automatic backend health monitoring that:
- Sends a preflight request to `/health` endpoint on page load
- Shows a friendly notification if the backend takes >5 seconds to respond
- Informs users that the first request may take 30-60 seconds while the instance spins up
- Auto-dismisses after 8 seconds or can be manually closed

This provides a smooth user experience even when the backend is waking from sleep.

### Environment Variables for Production

Update these in your deployment platform:

```bash
# Backend
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key
GEMINI_API_KEY=your-gemini-key

# Frontend
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://your-backend-url.com
```

### Supabase Configuration

In Supabase Dashboard → Authentication → URL Configuration:
- **Site URL**: Your production frontend URL
- **Redirect URLs**: Add your production frontend URL

### Build Commands

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
# Serve the dist/ folder with your web server
```

## 📖 Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Architecture decisions, AI tools used, trade-offs, and development process

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

MIT License - Feel free to use this project for learning and portfolio purposes.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Supabase](https://supabase.com/)
- [Qdrant](https://qdrant.tech/)
- [Google Gemini](https://ai.google.dev/)
- [LangChain](https://www.langchain.com/)

---

**Questions?** Check [DEVELOPMENT.md](DEVELOPMENT.md) or open an issue.
