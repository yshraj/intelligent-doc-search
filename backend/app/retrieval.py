"""RAG retrieval and generation using Qdrant + LangChain."""
import logging
from typing import Any
import warnings

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from google import genai  # New API for embeddings

# Suppress all FutureWarnings from google packages
warnings.filterwarnings('ignore', category=FutureWarning)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.ingestion import generate_embeddings, get_qdrant_client

logger = logging.getLogger(__name__)

# Cache for LLM instance
_llm_instance = None


def get_llm():
    """Get or create cached LLM instance."""
    global _llm_instance
    
    if _llm_instance is not None:
        return _llm_instance
    
    api_key = settings.gemini_api_key or settings.gemini_api_key_2
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GEMINI_API_KEY_2 must be configured")
    
    # Try different model names that work with LangChain
    # Note: LangChain adds "models/" prefix automatically, so use short names
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-pro-latest",
    ]
    
    for model_name in models_to_try:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.4,
                max_output_tokens=settings.max_output_tokens,  # Set during initialization
            )
            # Test it works with a simple call
            test_prompt = ChatPromptTemplate.from_messages([("user", "Say ok")])
            test_chain = test_prompt | llm | StrOutputParser()
            result = test_chain.invoke({})
            
            if result:
                logger.info("Using LangChain model: %s with max_output_tokens=%d", 
                           model_name, settings.max_output_tokens)
                _llm_instance = llm
                return _llm_instance
        except Exception as e:
            logger.debug("Model %s failed: %s", model_name, str(e)[:100])
            continue
    
    raise ValueError("No working Gemini model found. Please check your API key.")


def retrieve_relevant_chunks(
    user_id: str,
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve top-k relevant chunks from Qdrant with hybrid semantic search.
    
    Args:
        user_id: User ID for filtering (MANDATORY for security)
        question: User's question
        document_id: Optional document ID to filter by (None = search all user docs)
        top_k: Number of chunks to retrieve (default: from settings)
        min_score: Minimum similarity score threshold (default: from settings)
    
    Returns:
        List of chunks with metadata and scores, sorted by relevance
    """
    if top_k is None:
        top_k = settings.retrieval_top_k
    if min_score is None:
        min_score = settings.retrieval_min_score
    try:
        # Generate query embedding
        query_embedding = generate_embeddings([question])[0]
        
        # Build filter - ALWAYS filter by user_id for security
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        if document_id:
            filter_conditions.append(
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            )
        
        query_filter = Filter(must=filter_conditions)
        
        # Search Qdrant with cosine similarity
        client = get_qdrant_client()
        try:
            # Try new API (qdrant-client >= 1.8.0)
            response = client.query_points(
                collection_name=settings.qdrant_collection,
                query=query_embedding,
                query_filter=query_filter,
                limit=top_k,
            )
            results = response.points
        except AttributeError:
            # Fallback to old API (qdrant-client < 1.8.0)
            results = client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k,
            )
        
        # Format results and filter by minimum score
        chunks = []
        seen_content = set()  # Deduplicate identical chunks
        
        for hit in results:
            # Skip low-relevance chunks
            if hit.score < min_score:
                continue
            
            content = hit.payload.get("content", "")
            
            # Skip duplicate content
            if content in seen_content:
                continue
            seen_content.add(content)
            
            chunks.append({
                "content": content,
                "document_id": hit.payload.get("document_id", ""),
                "filename": hit.payload.get("filename", ""),
                "page_start": hit.payload.get("page_start"),
                "page_end": hit.payload.get("page_end"),
                "chunk_index": hit.payload.get("chunk_index"),
                "score": hit.score,
            })
        
        logger.info("Retrieved %d chunks for user %s (filtered from %d results)", 
                   len(chunks), user_id, len(results))
        return chunks
    
    except Exception as exc:
        logger.exception("Retrieval failed: %s", exc)
        raise ValueError(f"Failed to retrieve relevant chunks: {str(exc)[:200]}")


def generate_answer(
    question: str, 
    context_chunks: list[dict[str, Any]], 
    document_id: str | None = None
) -> str:
    """
    Generate answer using LangChain with a simple, flexible prompt.
    Let the LLM handle everything naturally without hardcoded logic.
    
    Args:
        question: User's question
        context_chunks: Retrieved chunks with content and metadata
        document_id: Document ID filter (None = all documents)
    
    Returns:
        Generated answer
    """
    if not context_chunks:
        return "I couldn't find any relevant information in your documents to answer this question."
    
    # Group chunks by document for better context
    docs_map = {}
    for chunk in context_chunks:
        doc_name = chunk.get('filename', 'Unknown')
        if doc_name not in docs_map:
            docs_map[doc_name] = []
        docs_map[doc_name].append(chunk)
    
    # Format context with document grouping
    context_parts = []
    for doc_name, doc_chunks in docs_map.items():
        context_parts.append(f"=== {doc_name} ===")
        for chunk in doc_chunks:
            page = chunk.get('page_start', '?')
            content = chunk.get('content', '')
            context_parts.append(f"[Page {page}]\n{content}")
        context_parts.append("")  # Empty line between documents
    
    context = "\n\n".join(context_parts)
    doc_count = len(docs_map)
    doc_list = ", ".join(docs_map.keys())
    
    # Estimate token count (rough: 1 token ≈ 4 chars)
    # With 8 chunks × 700 tokens = 5600 tokens max context
    # We need to leave room for: prompt template (~400 tokens) + answer (2048 tokens)
    # So context should be < 4000 tokens to be safe (leaves buffer for answer)
    estimated_context_tokens = len(context) // 4
    max_context_tokens = 4000
    
    if estimated_context_tokens > max_context_tokens:
        # Truncate context to fit, but keep it balanced across documents
        logger.warning("Context too large (%d tokens estimated), truncating to %d tokens", 
                      estimated_context_tokens, max_context_tokens)
        
        # Calculate how much to keep per document
        target_chars = max_context_tokens * 4
        chars_per_doc = target_chars // doc_count
        
        truncated_parts = []
        for doc_name, doc_chunks in docs_map.items():
            truncated_parts.append(f"=== {doc_name} ===")
            doc_content = []
            current_chars = 0
            
            for chunk in doc_chunks:
                page = chunk.get('page_start', '?')
                content = chunk.get('content', '')
                chunk_text = f"[Page {page}]\n{content}"
                
                if current_chars + len(chunk_text) <= chars_per_doc:
                    doc_content.append(chunk_text)
                    current_chars += len(chunk_text)
                else:
                    # Add partial chunk if there's room
                    remaining = chars_per_doc - current_chars
                    if remaining > 100:  # Only add if meaningful
                        doc_content.append(chunk_text[:remaining] + "...")
                    break
            
            truncated_parts.extend(doc_content)
            truncated_parts.append("")
        
        context = "\n\n".join(truncated_parts)
    
    # Single flexible prompt - optimized for 2048 token limit
    prompt_text = f"""You are a helpful AI assistant that answers questions about documents.

Available documents ({doc_count}): {doc_list}

Context from documents:
{context}

User question: {question}

Instructions:
- Answer the user's question naturally and completely
- Use information from ALL relevant documents (don't focus on just one)
- Cite sources by mentioning document names and page numbers
- Use markdown formatting for better readability
- If comparing or summarizing multiple documents, organize by document
- CRITICAL: You have a 2048 token limit. Be concise but ALWAYS finish your sentences and provide a proper conclusion
- Prioritize key information over exhaustive detail
- End with a complete thought - never stop mid-sentence
- If information isn't available, say so clearly

Answer:"""
    
    try:
        # Get LLM instance (already configured with max_output_tokens)
        llm = get_llm()
        
        # Create simple prompt and chain
        prompt = ChatPromptTemplate.from_messages([
            ("user", "{prompt_text}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        # Generate answer
        answer = chain.invoke({"prompt_text": prompt_text})
        
        logger.info("Generated answer for question: %s (used %d chunks from %d documents)", 
                   question[:50], len(context_chunks), doc_count)
        
        return answer.strip()
    
    except Exception as exc:
        logger.exception("Answer generation failed: %s", exc)
        raise ValueError(f"Failed to generate answer: {str(exc)[:200]}")


def rag_query(
    user_id: str,
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    """
    Complete RAG pipeline: retrieve + generate with hybrid semantic search.
    
    Security: Always filters by user_id to prevent cross-user data leakage.
    
    Args:
        user_id: Current user ID (MANDATORY)
        question: User's question
        document_id: Optional single document filter (None = all user docs)
        top_k: Number of chunks to retrieve (default: from settings)
    
    Returns:
    {
        "answer": str,
        "sources": [{"document_id", "filename", "page_start", "page_end", "chunk_index", "snippet"}]
    }
    """
    if top_k is None:
        top_k = settings.retrieval_top_k
    try:
        # Retrieve relevant chunks with mandatory user_id filter
        chunks = retrieve_relevant_chunks(user_id, question, document_id, top_k)
        
        if not chunks:
            return {
                "answer": "I couldn't find any relevant information in your documents to answer this question. Try uploading more documents or rephrasing your question.",
                "sources": [],
            }
        
        # Generate answer with context
        answer = generate_answer(question, chunks, document_id)
        
        # Format sources with snippets for UI display
        sources = []
        seen_docs = {}  # Track best chunk per document
        
        for chunk in chunks:
            doc_id = chunk["document_id"]
            
            # Keep highest-scoring chunk per document for sources
            if doc_id not in seen_docs or chunk["score"] > seen_docs[doc_id]["score"]:
                seen_docs[doc_id] = chunk
        
        # Build source list from best chunks
        for doc_id, chunk in seen_docs.items():
            # Create snippet (first 150 chars of content)
            content = chunk["content"]
            snippet = content[:150] + "..." if len(content) > 150 else content
            
            sources.append({
                "document_id": doc_id,
                "filename": chunk["filename"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "chunk_index": chunk["chunk_index"],
                "snippet": snippet,
            })
        
        # Sort sources by page number for better UX
        sources.sort(key=lambda s: (s["filename"], s["page_start"] or 0))
        
        return {
            "answer": answer,
            "sources": sources,
        }
    
    except Exception as exc:
        logger.exception("RAG query failed: %s", exc)
        raise
