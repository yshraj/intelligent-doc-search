# LangChain Implementation Guide

## Overview

The RAG system uses LangChain for text generation with:
1. **Auto model discovery** - Tries multiple Gemini models until one works
2. **Out-of-scope handling** - Detects greetings, small talk, off-topic queries
3. **Smart suggestions** - 15 context-aware suggestions per document scope
4. **Intent-based routing** - 9 intents with optimized prompts

## Installation

```bash
cd backend
pip install -r requirements.txt
```

Dependencies:
- `langchain>=0.1.0`
- `langchain-core>=0.1.0`
- `langchain-google-genai>=0.0.6`
- `google-genai>=0.3.0` (for embeddings)

## Configuration

Add to `.env`:
```bash
GEMINI_API_KEY=your_gemini_key
```

The system will automatically try these models in order:
1. `gemini-1.5-flash`
2. `gemini-1.5-pro`
3. `gemini-pro`

It caches the first working model for performance.

## Features

### 1. LangChain Integration
- Uses `ChatGoogleGenerativeAI` for text generation
- Simple prompt templates with `ChatPromptTemplate`
- Output parsing with `StrOutputParser`
- Automatic model fallback

### 2. Intent Detection (9 intents)

| Intent | Example |
|--------|---------|
| qa_single | "What is the vacation policy?" |
| qa_multi | "What are the main policies?" |
| summarize_single | "Summarize this document" |
| summarize_multi | "Summarize all documents" |
| comprehensive | "Give me a detailed analysis" |
| compare | "Compare these documents" |
| extract | "List all requirements" |
| analysis | "Analyze the trends" |
| out_of_scope | "hi", "how are you?" |

### 3. Out-of-Scope Handling
Detects and handles:
- Greetings: "hi", "hello", "hey"
- Small talk: "how are you?", "what's up?"
- Off-topic: "tell me a joke", "what's the weather?"

Response: "I'm a document Q&A assistant..."

### 4. Smart Suggestions (15 per context)

**Single Document:**
- "What are the main topics covered in this document?"
- "Summarize the key points"
- "Extract all dates and deadlines mentioned"
- ... (12 more)

**Multiple Documents:**
- "Create a comprehensive summary of all documents"
- "Compare and contrast these documents"
- "What are the common themes across all documents?"
- ... (12 more)

API: `GET /api/chat/suggestions?document_id=all`

## Usage

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Test Out-of-Scope
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer TOKEN" \
  -d '{"question": "hi"}'
```

### Get Suggestions
```bash
curl http://localhost:8000/api/chat/suggestions?document_id=all
```

## Architecture

```
Query → Intent Detection (keyword) → LangChain Chain → Response
        (intent_detection.py)         (ChatGoogleGenerativeAI)
```

### Files
- `backend/app/retrieval.py` - LangChain integration, model discovery
- `backend/app/intent_detection.py` - Keyword-based intent detection
- `backend/app/routers/chat.py` - API endpoints with suggestions
- `backend/requirements.txt` - LangChain dependencies

## Troubleshooting

### "No working Gemini model found"
- Check your `GEMINI_API_KEY` is valid
- Ensure you have access to Gemini models
- Check the logs to see which models were tried

### Model errors on startup
The system tries multiple models automatically. Check logs for:
```
INFO: Using LangChain model: gemini-1.5-flash
```

### Import errors
```bash
pip install -r requirements.txt
```

## Summary

✅ LangChain for text generation  
✅ Auto-discovers working Gemini model  
✅ Out-of-scope query handling  
✅ 15 smart suggestions per context  
✅ 9 intents with keyword detection  
✅ Simple, maintainable architecture  

Your RAG system uses LangChain exclusively!
