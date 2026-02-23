# Intent-Based RAG System

Intelligent query understanding with dynamic prompting for better multi-document responses.

## Overview

The system now automatically detects user intent and adjusts its response strategy accordingly. This solves the problem of comprehensive queries not covering all documents equally.

## Supported Intents

### 1. Question-Answering (QA)
**Keywords**: "what", "who", "when", "where", "why", "how", "explain", "tell me"

**Single Document** (`qa_single`):
- Direct answer from that document only
- Concise and specific (2-3 sentences)
- Cites page numbers

**Multiple Documents** (`qa_multi`):
- Aggregates information from all relevant documents
- Each point cites source document
- Format: [Point] (Source: **Document Name**, page X)

### 2. Summarization
**Keywords**: "summarize", "summary", "overview", "brief", "key points", "main ideas"

**Single Document** (`summarize_single`):
- Concise summary under 200 words
- Main topic, key points (3-5 bullets), conclusions
- Structured and clear

**Multiple Documents** (`summarize_multi`):
- **Balanced summary with equal coverage per document**
- Separate section for EACH document (2-4 sentences each)
- Overall synthesis showing relationships
- **Solves the comprehensive summary problem!**

### 3. Comprehensive Analysis
**Keywords**: "comprehensive", "detailed", "complete", "thorough", "in-depth"

**Multiple Documents Only** (`comprehensive`):
- Most detailed response type
- Mandatory structure:
  - Document Summaries (3-4 sentences per doc)
  - Cross-Document Analysis (themes, unique insights, contradictions)
  - Key Takeaways (3-5 main points)
- **Every document MUST be covered equally**
- Up to 800 tokens for thorough analysis

### 4. Comparison
**Keywords**: "compare", "comparison", "difference", "contrast", "versus", "vs", "similar"

**Multiple Documents Required** (`compare`):
- Structured comparison format
- Similarities section (bullet points)
- Differences table (side-by-side)
- Key insights from comparison

### 5. Extraction
**Keywords**: "extract", "list", "find all", "get all", "pull out", "identify all"

**Any Scope** (`extract`):
- Exhaustive extraction of requested information
- Grouped by document if multiple
- Bullet point format
- "None found" if nothing matches

### 6. Analysis
**Keywords**: "analyze", "analysis", "insights", "trends", "patterns", "themes"

**Any Scope** (`analysis`):
- Deep analysis covering:
  - Key themes and patterns
  - Important insights
  - Implications and significance
  - Connections between concepts
- Cross-document patterns for multi-doc queries

## How It Works

### 1. Intent Detection
```python
query = "Create a comprehensive summary"
document_scope = "multi"  # 3 documents

detected_intent = detect_intent(query, document_scope)
# Returns: "comprehensive"
```

### 2. Context Formatting
For multi-doc intents (summarize_multi, comprehensive, compare):
```
=== DOCUMENT: Employee HR Policy Guide.pdf ===
[Chunk 1 | Page 3 | Relevance: 0.85]
Content here...

=== DOCUMENT: Financial Services Guide.pdf ===
[Chunk 1 | Page 2 | Relevance: 0.82]
Content here...

=== DOCUMENT: Robert Williams.pdf ===
[Chunk 1 | Page 1 | Relevance: 0.91]
Content here...
```

This visual separation helps the AI treat each document equally.

### 3. Dynamic Prompting
Each intent gets a specialized prompt template with:
- Intent-specific instructions
- Required output format
- Emphasis on balanced coverage (for multi-doc)
- Appropriate response length

### 4. Generation Config
Response length adjusted by intent:
- **Comprehensive/Compare/Analysis**: 800 tokens, temp 0.5
- **Summarize**: 500 tokens, temp 0.4
- **QA**: 400 tokens, temp 0.4

## Example Queries

### Comprehensive Summary (Multi-Doc)
**Query**: "Create a comprehensive summary of all documents"

**Intent Detected**: `comprehensive`

**Response Format**:
```markdown
# Document Summaries

## Employee HR Policy Guide.pdf
[3-4 sentences covering main content]

## Financial Services Guide.pdf
[3-4 sentences covering main content]

## Robert Williams.pdf
[3-4 sentences covering main content]

# Cross-Document Analysis
- Common themes: [List]
- Unique insights: [What each contributes]
- Contradictions: [Any conflicts]

# Key Takeaways
[3-5 synthesized points]
```

### Comparison
**Query**: "Compare the policies across these documents"

**Intent Detected**: `compare`

**Response Format**:
```markdown
## Similarities
- Common point 1
- Common point 2

## Differences
| Aspect | Doc 1 | Doc 2 | Doc 3 |
|--------|-------|-------|-------|
| Policy | Info  | Info  | Info  |

## Key Insights
[What comparison reveals]
```

### Simple QA (Single Doc)
**Query**: "What is the vacation policy?"

**Intent Detected**: `qa_single`

**Response**: "According to the **Employee HR Policy Guide** (page 5), employees receive 15 days of paid vacation annually, increasing to 20 days after 5 years of service."

## UI Features

### Intent Badge
Each AI response shows a small badge indicating detected intent:
```
[ℹ️ comprehensive]
```

This helps users understand how their query was interpreted.

### Visual Styling
- Badge appears above AI response
- Blue gradient background
- Capitalized, readable format
- Icon for visual clarity

## Benefits

### 1. Solves Multi-Doc Coverage Problem
Before: "Comprehensive summary" would focus on one document
After: Structured format ensures ALL documents covered equally

### 2. Better Response Quality
Each intent gets optimized prompting for that specific task

### 3. Automatic Detection
No manual selection needed - system understands user intent

### 4. Scalable
Easy to add new intents as needed

### 5. Transparent
Users see detected intent, can rephrase if wrong

## Configuration

### Adding New Intents

1. Add to `IntentType` in `backend/app/intent_detection.py`
2. Add detection logic in `detect_intent()`
3. Add prompt template in `get_prompt_template()`
4. Optionally adjust generation config in `retrieval.py`

### Adjusting Keywords

Edit keyword lists in `detect_intent()`:
```python
comprehensive_keywords = [
    "comprehensive", "detailed", "complete", 
    "thorough", "in-depth", "full"
]
```

### Customizing Prompts

Edit templates in `get_prompt_template()`:
```python
templates = {
    "comprehensive": f"""Your custom prompt here...""",
    # ...
}
```

## Testing

### Test Comprehensive Summary
1. Upload 3+ documents
2. Select "All ready documents"
3. Ask: "Create a comprehensive summary"
4. Verify: Each document gets its own section
5. Check: Intent badge shows "comprehensive"

### Test Comparison
1. Upload 2+ documents
2. Ask: "Compare these documents"
3. Verify: Similarities and differences shown
4. Check: Intent badge shows "compare"

### Test Single Doc QA
1. Select one document
2. Ask: "What is the main topic?"
3. Verify: Concise answer from that document only
4. Check: Intent badge shows "qa single"

## Troubleshooting

### Intent Not Detected Correctly
- Check if query contains intent keywords
- Try more explicit phrasing
- System defaults to QA if unclear

### Not All Documents Covered
- Verify intent is "comprehensive" or "summarize_multi"
- Check if all documents have relevant chunks retrieved
- Increase `top_k` retrieval parameter if needed

### Response Too Short/Long
- Adjust `max_output_tokens` in generation config
- Modify prompt template instructions
- Different intents have different length limits

## Future Enhancements

### Planned Features
1. **User Override**: Let users manually select intent
2. **Intent Confidence**: Show confidence score
3. **Query Refinement**: Suggest better phrasing
4. **More Intents**: Translation, classification, ranking
5. **Multi-Intent**: Handle queries with multiple intents

### Advanced Options
- Per-document minimum chunk count
- Reranking for diversity
- MMR (Maximal Marginal Relevance)
- Hybrid BM25 + vector search

## API Response

### Chat Response Format
```json
{
  "answer": "Generated answer text...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "doc.pdf",
      "page_start": 3,
      "page_end": 3,
      "snippet": "Content preview..."
    }
  ],
  "session_id": "uuid",
  "intent": "comprehensive"
}
```

The `intent` field shows what was detected and used.

## Summary

The intent-based RAG system provides:
- ✅ Automatic query understanding
- ✅ Balanced multi-document coverage
- ✅ Intent-specific response strategies
- ✅ Better comprehensive summaries
- ✅ Transparent intent detection
- ✅ Scalable architecture

Your "comprehensive summary" problem is now solved with structured, balanced responses across all documents!
