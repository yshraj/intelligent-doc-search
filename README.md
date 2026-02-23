# DocuChat

AI-powered document chat system – upload PDFs/text files, ask questions, and get answers with source citations.

**Tech Stack:** FastAPI, React, Supabase (Auth + DB + Storage), Qdrant Cloud (vectors), Gemini API (embeddings + generation).

## Quick Start

### 1. Environment Setup

```bash
# Root .env
cp .env.example .env
# Edit with your Supabase, Qdrant, and Gemini credentials

# Frontend .env
cp frontend/.env.example frontend/.env
# Set VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
```

### 2. Database Setup

Run these SQL scripts in Supabase SQL Editor:
- `supabase/schema.sql` - Creates tables and RLS policies
- `supabase/storage.sql` - Sets up storage bucket
- `supabase/chat_history.sql` - Chat history tables (optional)
- `supabase/add_file_hash.sql` - File deduplication (optional)

### 3. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Fix Qdrant indexes (if needed for existing collections)
python3 fix_qdrant_indexes.py

# Start server
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

**See `backend/SETUP.md` for detailed configuration and troubleshooting.**

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

## Features

✅ **Authentication** - Google OAuth via Supabase  
✅ **Document Management** - Upload, process, and delete PDF/TXT files  
✅ **RAG Pipeline** - Hybrid chunking, semantic search, AI-powered answers  
✅ **Intent Detection** - Automatic query understanding with 8 intent types  
✅ **Source Citations** - Answers include page numbers and snippets  
✅ **Chat History** - Save, search, and resume conversations  
✅ **File Deduplication** - Prevents duplicate uploads  
✅ **User Isolation** - Each user only sees their own documents  
✅ **Modern UI** - Apple/Google-inspired design with animations

## Project Structure

```
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── SETUP.md      # Backend setup & troubleshooting
│   └── fix_qdrant_indexes.py  # Utility script
├── frontend/         # React frontend
├── supabase/         # Database schemas
├── docs/             # Documentation
└── phase-1-plan.md   # Implementation plan
```

## Documentation

- **Backend Setup**: `backend/SETUP.md` - Complete backend configuration guide
- **Intent-Based RAG**: `INTENT_BASED_RAG.md` - Query understanding and dynamic prompting
- **Environment Setup**: `docs/ENV_SETUP.md` - Where to get credentials
- **RAG Implementation**: `docs/RAG_IMPLEMENTATION.md` - Technical details
- **Quick Start**: `docs/QUICKSTART.md` - Step-by-step guide

## Configuration

### Supabase

In Supabase Dashboard → Authentication → URL Configuration:
- **Site URL**: `http://localhost:5173` (or your frontend URL)
- **Redirect URLs**: Add your frontend origin

### Qdrant

Ensure payload indexes exist for `user_id` and `document_id`:
```bash
cd backend
python3 fix_qdrant_indexes.py
```

## Status

✅ Phase 1 Complete - All core features implemented and working
