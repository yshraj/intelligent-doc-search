# Simplification Changes - LLM-First Approach

## Overview
Removed hardcoded logic and intent detection system. Now using a single, flexible prompt that lets the LLM naturally handle all query types without artificial constraints.

## Key Changes

### 1. Removed Intent Detection System
- **Before**: Complex intent detection with 9 different intent types (qa_single, qa_multi, summarize_single, summarize_multi, comprehensive, compare, extract, analysis, out_of_scope)
- **After**: Single flexible prompt that lets LLM decide how to respond naturally

### 2. Simplified Prompt Engineering
- **Before**: 9 different prompt templates with hardcoded instructions and length limits
- **After**: One universal prompt with simple guidelines:
  - Answer naturally and completely
  - Use information from ALL relevant documents
  - Cite sources
  - Use markdown formatting
  - Don't cut off mid-sentence

### 3. Removed Token Limits Based on Intent
- **Before**: Different max_output_tokens for different intents (400-800 tokens)
- **After**: Consistent max_output_tokens (2048) - let LLM decide natural length

### 4. Simplified Context Formatting
- **Before**: Different formatting based on intent (format_context_by_document vs format_context_standard)
- **After**: Always group by document for clarity

### 5. Increased Retrieval Coverage
- **Before**: retrieval_top_k = 8 (too few for multi-document queries)
- **After**: retrieval_top_k = 15 (better coverage across multiple documents)

### 6. Removed UI Complexity
- **Before**: Intent badges displayed in chat
- **After**: Clean, simple message display

## Benefits

1. **Less Code**: Removed ~300 lines of intent detection and prompt template logic
2. **More Flexible**: LLM can handle any query type naturally without being constrained
3. **Better Multi-Doc**: Explicit instructions to use ALL documents, not just one
4. **No Truncation**: Consistent high token limit prevents mid-sentence cutoffs
5. **Easier Maintenance**: One prompt to maintain instead of 9
6. **Better UX**: No artificial categorization - just natural responses

## Files Modified

- `backend/app/retrieval.py` - Simplified generate_answer() and rag_query()
- `backend/app/config.py` - Increased retrieval_top_k to 15
- `frontend/src/App.jsx` - Removed intent badge display
- `.env` and `.env.example` - Added RETRIEVAL_TOP_K configuration

## Configuration

Users can now easily adjust:
- `MAX_OUTPUT_TOKENS` - Maximum response length (default: 2048)
- `RETRIEVAL_TOP_K` - Number of chunks to retrieve (default: 15)

## Result

The system now relies on the LLM's natural intelligence to:
- Understand query intent
- Decide appropriate response length
- Format responses appropriately
- Use all relevant documents
- Provide complete, untruncated answers
