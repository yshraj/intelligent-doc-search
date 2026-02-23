# Quick Start Guide - RAG Implementation

This guide will help you set up and test the complete RAG pipeline.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account (free tier)
- Qdrant Cloud account (free tier)
- Google AI Studio account (free tier)

## Step 1: Set Up Qdrant Cloud

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Sign up for free account
3. Create a new cluster (1GB free tier)
4. Copy your cluster URL and API key

## Step 2: Set Up Gemini API

1. Go to [ai.google.dev](https://ai.google.dev)
2. Get API key from Google AI Studio
3. Copy your API key

## Step 3: Configure Environment

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in all values:
```bash
# Supabase (from your Supabase project settings)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Qdrant Cloud
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=your-qdrant-key

# Gemini API
GEMINI_API_KEY=your-gemini-key
```

3. Configure frontend:
```bash
cd frontend
cp .env.example .env
```

Edit `frontend/.env`:
```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_URL=http://localhost:8000
```

## Step 4: Install Dependencies

Backend:
```bash
cd backend
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

## Step 5: Set Up Supabase

1. Run schema in Supabase SQL Editor:
```bash
# Copy contents of supabase/schema.sql
# Paste and run in Supabase SQL Editor
```

2. Create Storage bucket:
   - Go to Storage in Supabase dashboard
   - Create new bucket named "documents"
   - Make it Private
   - Optional: Set 10MB file size limit

3. Run storage RLS policies:
```bash
# Copy contents of supabase/storage.sql
# Paste and run in Supabase SQL Editor
```

4. Enable Google OAuth:
   - Go to Authentication → Providers
   - Enable Google provider
   - Add your Google OAuth credentials
   - Add redirect URL: `http://localhost:5173`

## Step 6: Start Services

Terminal 1 - Backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

## Step 7: Test the Application

1. Open browser to `http://localhost:5173`

2. Sign in with Google

3. Complete onboarding form

4. Upload a test document:
   - Click "Choose File"
   - Select a PDF or TXT file (< 10MB)
   - Click "Upload"
   - Wait for status to change from "processing" to "ready"

5. Ask a question:
   - Go to "Chat" tab
   - Select your document (or "All ready documents")
   - Type a question about the document
   - Click "Ask"
   - View answer and source citations with page numbers

## Verification Checklist

### Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Qdrant Connection
After uploading a document, check Qdrant dashboard:
- Collection `document_chunks` should exist
- Points should be visible with your document's vectors

### Document Processing
Watch backend logs for:
```
INFO: Starting background processing for document <uuid>
INFO: Generated X chunks for document <uuid>
INFO: Upserted X chunks to Qdrant for document <uuid>
INFO: Document <uuid> processing complete: ready
```

### RAG Query
After asking a question, check backend logs for:
```
INFO: Retrieved X chunks for user <uuid>
INFO: Generated answer for question: <question>
```

## Troubleshooting

### "Missing user_profiles table"
- Run `supabase/schema.sql` in Supabase SQL Editor

### "Failed to upload file"
- Ensure Storage bucket "documents" exists and is Private
- Run `supabase/storage.sql` for RLS policies

### "QDRANT_URL and QDRANT_API_KEY must be configured"
- Check `.env` file has correct Qdrant credentials
- Verify Qdrant cluster is running

### "GEMINI_API_KEY must be configured"
- Check `.env` file has valid Gemini API key
- Verify key has not expired

### Document stuck in "processing"
- Check backend logs for errors
- Verify Gemini API key is valid
- Check Qdrant connection
- Document may have failed (check status)

### "No ready documents found"
- Wait for document processing to complete
- Check document status in Documents tab
- Refresh document list

### Empty or irrelevant answers
- Ensure document has extractable text (not scanned image)
- Try more specific questions
- Check if document is actually relevant to question

## Testing with Sample Documents

Create a test file `test.txt`:
```
LiveDocAI is a smart document Q&A system.
It uses RAG (Retrieval-Augmented Generation) to answer questions.
The system supports PDF and plain text files.
Documents are chunked and embedded using Gemini.
Vectors are stored in Qdrant Cloud.
```

Upload and ask:
- "What is LiveDocAI?"
- "What file types are supported?"
- "Where are vectors stored?"

Expected: Accurate answers with source citations.

## Next Steps

- Read `docs/RAG_IMPLEMENTATION.md` for technical details
- Check `TODO.md` for testing checklist
- Review `phase-1-plan.md` for feature completeness
- Explore API docs at `http://localhost:8000/docs`

## Support

If you encounter issues:
1. Check backend logs for errors
2. Verify all environment variables are set
3. Ensure Supabase schema and storage are configured
4. Test Qdrant and Gemini API connections independently
5. Review error messages in browser console
