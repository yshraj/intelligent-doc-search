# DocuChat Setup Guide

Complete setup instructions for getting DocuChat running locally.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account (free tier)
- Qdrant Cloud account (free tier)
- Google AI Studio account (free tier)

## Quick Start

### 1. Clone and Install

```bash
# Install backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
# Root directory
cp .env.example .env

# Frontend directory
cd frontend
cp .env.example .env
```

Edit `.env` files with your credentials (see Environment Setup section below).

### 3. Setup Supabase

1. Create a new Supabase project at https://supabase.com
2. Run SQL scripts in Supabase SQL Editor (in order):
   - `supabase/schema.sql` - Core tables and RLS policies
   - `supabase/storage.sql` - Storage bucket setup
   - `supabase/chat_history.sql` - Chat history (optional)
   - `supabase/add_file_hash.sql` - File deduplication (optional)

3. Enable Google OAuth:
   - Go to Authentication → Providers
   - Enable Google provider
   - Add your Google OAuth credentials
   - Add redirect URL: `http://localhost:5173`

### 4. Setup Qdrant Cloud

1. Sign up at https://cloud.qdrant.io
2. Create a new cluster (1GB free tier)
3. Copy your cluster URL and API key

### 5. Get Gemini API Key

1. Go to https://ai.google.dev
2. Get API key from Google AI Studio
3. Copy your API key

### 6. Run the Application

Terminal 1 - Backend:
```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Environment Setup

### Root `.env`

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Qdrant Cloud
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=your-qdrant-key

# Gemini API
GEMINI_API_KEY=your-gemini-key
```

### Frontend `.env`

```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_URL=http://localhost:8000
```

## Features

### Core Features
- Google OAuth authentication
- PDF/TXT document upload and processing
- AI-powered Q&A with RAG
- Source citations with page numbers
- Document management (list, view, delete)

### Optional Features
- Chat history (requires `chat_history.sql`)
- File deduplication (requires `add_file_hash.sql`)
- Clear all documents
- Export chat history

## Commands

### Backend
```bash
# Start development server
cd backend
uvicorn app.main:app --reload --port 8000

# Fix Qdrant indexes (if needed)
python3 fix_qdrant_indexes.py
```

### Frontend
```bash
# Start development server
cd frontend
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Troubleshooting

### Backend won't start
- Check all environment variables are set in `.env`
- Verify Python virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Check `frontend/.env` has correct values
- Verify Node modules are installed: `npm install`
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### Upload fails
- Verify Supabase Storage bucket "documents" exists
- Check `storage.sql` was run for RLS policies
- Ensure backend can connect to Supabase

### No answers from chat
- Verify Qdrant connection (check URL and API key)
- Ensure Gemini API key is valid
- Check document status is "ready" (not "processing")

### Chat history not working
- Run `supabase/chat_history.sql` in Supabase SQL Editor
- Restart backend server
- Check browser console for errors

## Documentation

- `README.md` - Project overview
- `SETUP.md` - This file (setup instructions)
- `TODO.md` - Implementation status and testing checklist
- `backend/SETUP.md` - Backend-specific setup and troubleshooting
- `backend/RETRIEVAL_FLOW.md` - RAG pipeline documentation
- `docs/QUICKSTART.md` - Quick start guide
- `docs/RAG_IMPLEMENTATION.md` - Technical RAG details
- `docs/ENV_SETUP.md` - Where to get credentials

## Next Steps

After setup:
1. Sign in with Google
2. Complete onboarding form
3. Upload a test document
4. Wait for processing to complete
5. Ask questions in Chat tab
6. View conversation in History tab

## Support

For issues:
1. Check this SETUP.md file
2. Review backend logs for errors
3. Check browser console for frontend errors
4. Verify all SQL scripts were run
5. Ensure all environment variables are set
