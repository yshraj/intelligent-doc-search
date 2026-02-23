"""Intent detection and prompt templates for RAG queries."""
import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Intent types
IntentType = Literal[
    "qa_single",
    "qa_multi", 
    "summarize_single",
    "summarize_multi",
    "comprehensive",
    "compare",
    "extract",
    "analysis",
    "out_of_scope"  # Small talk, greetings, off-topic
]


def detect_intent(query: str, document_scope: str) -> IntentType:
    """
    Detect user intent from query text and document scope.
    
    Args:
        query: User's question/query
        document_scope: "single" or "multi"
    
    Returns:
        Intent type string
    """
    query_lower = query.lower().strip()
    
    # Out-of-scope detection (greetings, small talk, off-topic)
    out_of_scope_keywords = [
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
        "how are you", "what's up", "sup", "yo",
        "joke", "weather", "news", "tell me about yourself",
        "who are you", "what can you do",
    ]
    
    # Check for very short queries that are likely greetings
    if len(query_lower) <= 3 and query_lower in ["hi", "hey", "yo"]:
        logger.info("Detected intent: out_of_scope (greeting)")
        return "out_of_scope"
    
    # Check for out-of-scope keywords
    if any(keyword in query_lower for keyword in out_of_scope_keywords):
        logger.info("Detected intent: out_of_scope")
        return "out_of_scope"
    
    # Comprehensive/Detailed (highest priority for multi-doc)
    comprehensive_keywords = ["comprehensive", "detailed", "complete", "thorough", "in-depth", "full"]
    if any(word in query_lower for word in comprehensive_keywords):
        if document_scope == "multi":
            logger.info("Detected intent: comprehensive (multi-doc)")
            return "comprehensive"
        else:
            logger.info("Detected intent: summarize_single (comprehensive on single doc)")
            return "summarize_single"
    
    # Comparison (requires multi-doc)
    compare_keywords = ["compare", "comparison", "difference", "differences", "contrast", "versus", "vs", "similar", "similarities"]
    if any(word in query_lower for word in compare_keywords):
        logger.info("Detected intent: compare")
        return "compare"
    
    # Summarization
    summarize_keywords = ["summarize", "summary", "overview", "brief", "key points", "main ideas", "gist"]
    if any(word in query_lower for word in summarize_keywords):
        intent = "summarize_multi" if document_scope == "multi" else "summarize_single"
        logger.info("Detected intent: %s", intent)
        return intent
    
    # Extraction
    extract_keywords = ["extract", "list", "find all", "get all", "pull out", "identify all", "show me all"]
    if any(word in query_lower for word in extract_keywords):
        logger.info("Detected intent: extract")
        return "extract"
    
    # Analysis
    analysis_keywords = ["analyze", "analysis", "insights", "trends", "patterns", "themes", "evaluate"]
    if any(word in query_lower for word in analysis_keywords):
        logger.info("Detected intent: analysis")
        return "analysis"
    
    # Default to QA
    intent = "qa_multi" if document_scope == "multi" else "qa_single"
    logger.info("Detected intent: %s (default)", intent)
    return intent


def get_document_scope(document_id: str | None, chunks: list[dict[str, Any]]) -> str:
    """
    Determine if query is single-doc or multi-doc.
    
    Args:
        document_id: Document ID from request (None or "all" = multi)
        chunks: Retrieved chunks
    
    Returns:
        "single" or "multi"
    """
    if document_id and document_id != "all":
        return "single"
    
    # Check unique documents in chunks
    unique_docs = len(set(chunk.get('document_id', '') for chunk in chunks))
    return "multi" if unique_docs > 1 else "single"


def format_context_by_document(chunks: list[dict[str, Any]]) -> str:
    """
    Format chunks grouped by document for better multi-doc understanding.
    
    Args:
        chunks: Retrieved chunks with metadata
    
    Returns:
        Formatted context string with document grouping
    """
    # Group chunks by document
    grouped = {}
    for chunk in chunks:
        doc_name = chunk.get('filename', 'Unknown')
        if doc_name not in grouped:
            grouped[doc_name] = []
        grouped[doc_name].append(chunk)
    
    # Format with clear document separation
    formatted_parts = []
    for doc_name, doc_chunks in grouped.items():
        formatted_parts.append(f"=== DOCUMENT: {doc_name} ===")
        for i, chunk in enumerate(doc_chunks, 1):
            page = chunk.get('page_start', '?')
            content = chunk.get('content', '')
            score = chunk.get('score', 0)
            formatted_parts.append(
                f"[Chunk {i} | Page {page} | Relevance: {score:.2f}]\n{content}"
            )
        formatted_parts.append("")  # Empty line between documents
    
    return "\n\n".join(formatted_parts)


def format_context_standard(chunks: list[dict[str, Any]]) -> str:
    """
    Standard context formatting (mixed chunks).
    
    Args:
        chunks: Retrieved chunks with metadata
    
    Returns:
        Formatted context string
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        filename = chunk.get("filename", "Unknown")
        page = chunk.get("page_start", "?")
        content = chunk.get("content", "")
        score = chunk.get("score", 0)
        
        context_parts.append(
            f"[Source {i} | page {page} | {filename} | relevance: {score:.2f}]\n{content}"
        )
    
    return "\n\n".join(context_parts)


def get_prompt_template(intent: IntentType, question: str, context: str, chunks: list[dict[str, Any]]) -> str:
    """
    Get intent-specific prompt template.
    
    Args:
        intent: Detected intent type
        question: User's question
        context: Formatted context
        chunks: Retrieved chunks (for metadata)
    
    Returns:
        Complete prompt string
    """
    # Get unique document names for multi-doc prompts
    doc_names = sorted(set(chunk.get('filename', 'Unknown') for chunk in chunks))
    doc_count = len(doc_names)
    
    templates = {
        "qa_single": f"""You are a helpful assistant that answers questions based ONLY on the provided document.

Context from document:
{context}

Question: {question}

INSTRUCTIONS:
- Answer directly using ONLY information from this document
- Provide a complete, thorough answer with all relevant details
- Use markdown formatting (bold, italic, lists when appropriate)
- Cite page numbers naturally in your answer
- Include examples, explanations, and context where helpful
- If information is not in the document, say "I don't have enough information"
- Do NOT cut off your response mid-sentence - complete all thoughts fully

Answer:""",

        "qa_multi": f"""You are a helpful assistant that answers questions by aggregating information from multiple documents.

Context from {doc_count} documents:
{context}

Question: {question}

CRITICAL INSTRUCTIONS:
- You MUST review and use information from ALL {doc_count} documents: {', '.join(doc_names)}
- Answer by combining information from ALL relevant documents
- For each point, cite which document it came from
- Use markdown formatting (bold, italic, lists when appropriate)
- Format: [Point] (Source: **Document Name**, page X)
- Provide comprehensive coverage with all relevant details
- Include examples and explanations where helpful
- If a document doesn't contain relevant information, mention that explicitly
- Do NOT focus on just one document - synthesize across ALL documents
- Do NOT cut off your response mid-sentence - complete all thoughts fully

Answer:""",

        "summarize_single": f"""You are a helpful assistant that creates comprehensive summaries.

Document content:
{context}

Task: Summarize this document

INSTRUCTIONS:
- Provide a thorough summary covering:
  • Main topic/purpose
  • Key points (as many as needed to capture the content)
  • Important conclusions or recommendations
  • Supporting details and context
- Use markdown formatting for readability
- Be clear, structured, and complete
- Do NOT cut off your response mid-sentence - complete all sections fully

Summary:""",

        "summarize_multi": f"""You are a helpful assistant that creates balanced summaries across multiple documents.

Context from documents:
{context}

Task: Create a summary covering ALL {doc_count} documents

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. Create a separate section for EACH document
2. Each section should be thorough and complete (as many sentences as needed)
3. Use this EXACT format:

## {doc_names[0] if doc_names else 'Document 1'}
[Complete summary covering main points, key details, and important information]

{"## " + doc_names[1] if len(doc_names) > 1 else ""}
{"[Complete summary covering main points, key details, and important information]" if len(doc_names) > 1 else ""}

{"## " + doc_names[2] if len(doc_names) > 2 else ""}
{"[Complete summary covering main points, key details, and important information]" if len(doc_names) > 2 else ""}

## Overall Synthesis
[How documents relate, common themes, key takeaways - provide comprehensive analysis]

YOU MUST discuss every document listed above. Missing any document is a failure.
Do NOT cut off your response mid-sentence - complete all sections fully.

Summary:""",

        "comprehensive": f"""You are a helpful assistant that provides detailed, comprehensive analysis across multiple documents.

Context from documents:
{context}

Task: Provide a COMPREHENSIVE analysis covering ALL {doc_count} documents

MANDATORY STRUCTURE - YOU MUST USE THIS FORMAT:

# Document Summaries

## {doc_names[0] if doc_names else 'Document 1'}
[Thorough coverage of main content, key points, important details, and supporting information]

{"## " + doc_names[1] if len(doc_names) > 1 else ""}
{"[Thorough coverage of main content, key points, important details, and supporting information]" if len(doc_names) > 1 else ""}

{"## " + doc_names[2] if len(doc_names) > 2 else ""}
{"[Thorough coverage of main content, key points, important details, and supporting information]" if len(doc_names) > 2 else ""}

# Cross-Document Analysis
- **Common themes**: [List all themes that appear across documents with detailed explanation]
- **Unique insights**: [What each document uniquely contributes - be thorough]
- **Contradictions or differences**: [Any conflicting information or different perspectives - explain fully]
- **Connections and relationships**: [How documents relate to each other]

# Key Takeaways
[Comprehensive synthesis of main points from all documents - include all important information]

CRITICAL: 
- EVERY document in the context MUST appear in your response with equal coverage
- Do NOT cut off your response mid-sentence - complete all sections fully
- Provide thorough, detailed analysis throughout

Analysis:""",

        "compare": f"""You are a helpful assistant that compares documents systematically.

Documents to compare:
{context}

Task: Compare these {doc_count} documents

INSTRUCTIONS:
Format your response as:

## Similarities
- [List all common points with detailed explanations]
- [Include as many similarities as you find]
- [Provide context and examples]

## Differences
| Aspect | {doc_names[0] if doc_names else 'Doc 1'} | {doc_names[1] if len(doc_names) > 1 else 'Doc 2'} | {doc_names[2] if len(doc_names) > 2 else 'Doc 3'} |
|--------|----------|----------|----------|
| [Aspect 1] | [Detailed info] | [Detailed info] | [Detailed info] |
| [Aspect 2] | [Detailed info] | [Detailed info] | [Detailed info] |
| [Add as many rows as needed] | | | |

## Key Insights
[Comprehensive analysis of what the comparison reveals - provide thorough explanation]

CRITICAL: Do NOT cut off your response mid-sentence - complete all sections fully.

Comparison:""",

        "extract": f"""You are a helpful assistant that extracts specific information from documents.

Context from documents:
{context}

Question: {question}

CRITICAL INSTRUCTIONS:
- You MUST extract information from ALL {doc_count} documents listed below
- Group by document and clearly label each section
- Format your response EXACTLY as shown:

{chr(10).join(f"**{doc_name}:**{chr(10)}- [List all relevant items found in this document]{chr(10)}" for doc_name in doc_names)}

RULES:
- Be exhaustive - include ALL instances found in EACH document
- If nothing found in a specific document, write "**[Document Name]:** None found"
- Do NOT skip any document
- Do NOT combine documents - keep them separate
- Do NOT cut off your response mid-sentence - complete all sections fully

Extracted information:""",

        "analysis": f"""You are a helpful assistant that provides deep analysis of documents.

Context from documents:
{context}

Question: {question}

INSTRUCTIONS:
Provide comprehensive deep analysis covering:
- **Key themes and patterns**: What are the main ideas? Explain thoroughly with examples
- **Important insights**: What stands out or is significant? Provide detailed explanation
- **Implications**: What does this mean or suggest? Explore fully
- **Connections**: How do concepts relate? Explain relationships in detail
- **Supporting evidence**: Reference specific information from the documents

For multiple documents, identify cross-document patterns and relationships.

Use markdown formatting and be thorough and complete.
Do NOT cut off your response mid-sentence - complete all sections fully.

Analysis:""",
    }
    
    return templates.get(intent, templates["qa_single"])
