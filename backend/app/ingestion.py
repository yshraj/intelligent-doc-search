"""Document ingestion pipeline: extract, chunk, embed, store in Qdrant."""
import hashlib
import io
import logging
import re
import uuid
from typing import Any

import pdfplumber
import tiktoken
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize tokenizer for chunking
try:
    TOKENIZER = tiktoken.get_encoding("cl100k_base")
except Exception:
    TOKENIZER = None
    logger.warning("tiktoken encoding not available, using character-based fallback")


def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content for deduplication."""
    return hashlib.sha256(content).hexdigest()


def normalize_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    # Remove null characters
    text = text.replace("\x00", "")
    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple newlines (keep max 2)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim
    return text.strip()


def extract_text_from_pdf(content: bytes) -> list[dict[str, Any]]:
    """Extract text from PDF, return list of {page, text}."""
    pages = []
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                normalized = normalize_text(text)
                pages.append({"page": i, "text": normalized})
    except Exception as exc:
        logger.exception("PDF extraction failed: %s", exc)
        raise ValueError(f"Failed to extract PDF text: {str(exc)[:100]}")
    return pages


def extract_text_from_txt(content: bytes) -> list[dict[str, Any]]:
    """Extract text from plain text file, return single page."""
    try:
        text = content.decode("utf-8", errors="replace")
        normalized = normalize_text(text)
        return [{"page": 1, "text": normalized}]
    except Exception as exc:
        logger.exception("TXT extraction failed: %s", exc)
        raise ValueError(f"Failed to extract text: {str(exc)[:100]}")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken or character fallback."""
    if TOKENIZER:
        try:
            return len(TOKENIZER.encode(text, disallowed_special=()))
        except Exception:
            pass
    # Fallback: rough estimate (1 token ≈ 4 chars)
    return len(text) // 4


def chunk_text_hybrid(
    pages: list[dict[str, Any]],
    max_tokens: int = 700,
    overlap_tokens: int = 100,
) -> list[dict[str, Any]]:
    """
    Hybrid paragraph + token-based chunking.
    
    Returns list of chunks with metadata:
    {
        "chunk_index": int,
        "content": str,
        "page_start": int,
        "page_end": int,
        "token_count": int
    }
    """
    chunks = []
    chunk_index = 0
    buffer = []
    buffer_tokens = 0
    current_page_start = None
    current_page_end = None
    
    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]
        
        if not text.strip():
            continue
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        for para in paragraphs:
            para_tokens = count_tokens(para)
            
            # If single paragraph exceeds max, split it
            if para_tokens > max_tokens:
                # Flush current buffer first
                if buffer:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "content": "\n\n".join(buffer),
                        "page_start": current_page_start,
                        "page_end": current_page_end,
                        "token_count": buffer_tokens,
                    })
                    chunk_index += 1
                    buffer = []
                    buffer_tokens = 0
                    current_page_start = None
                    current_page_end = None
                
                # Split large paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                temp_buffer = []
                temp_tokens = 0
                
                for sent in sentences:
                    sent_tokens = count_tokens(sent)
                    if temp_tokens + sent_tokens > max_tokens and temp_buffer:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "content": " ".join(temp_buffer),
                            "page_start": page_num,
                            "page_end": page_num,
                            "token_count": temp_tokens,
                        })
                        chunk_index += 1
                        # Keep overlap
                        overlap_text = " ".join(temp_buffer[-2:]) if len(temp_buffer) >= 2 else ""
                        temp_buffer = [overlap_text, sent] if overlap_text else [sent]
                        temp_tokens = count_tokens(" ".join(temp_buffer))
                    else:
                        temp_buffer.append(sent)
                        temp_tokens += sent_tokens
                
                if temp_buffer:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "content": " ".join(temp_buffer),
                        "page_start": page_num,
                        "page_end": page_num,
                        "token_count": temp_tokens,
                    })
                    chunk_index += 1
                continue
            
            # Normal paragraph accumulation
            if buffer_tokens + para_tokens > max_tokens and buffer:
                # Save current chunk
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": "\n\n".join(buffer),
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                    "token_count": buffer_tokens,
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = buffer[-1] if buffer else ""
                overlap_tok = count_tokens(overlap_text)
                if overlap_tok <= overlap_tokens:
                    buffer = [overlap_text, para]
                    buffer_tokens = overlap_tok + para_tokens
                    current_page_start = current_page_end
                else:
                    buffer = [para]
                    buffer_tokens = para_tokens
                    current_page_start = page_num
                current_page_end = page_num
            else:
                # Add to buffer
                buffer.append(para)
                buffer_tokens += para_tokens
                if current_page_start is None:
                    current_page_start = page_num
                current_page_end = page_num
    
    # Flush remaining buffer
    if buffer:
        chunks.append({
            "chunk_index": chunk_index,
            "content": "\n\n".join(buffer),
            "page_start": current_page_start,
            "page_end": current_page_end,
            "token_count": buffer_tokens,
        })
    
    return chunks


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    if not settings.qdrant_url or not settings.qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be configured")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_qdrant_collection(client: QdrantClient, collection_name: str, vector_size: int = 3072):
    """Create Qdrant collection if it doesn't exist. gemini-embedding-001 uses 3072 dimensions."""
    from qdrant_client.models import PayloadSchemaType
    
    try:
        collection = client.get_collection(collection_name)
        logger.info("Collection %s already exists", collection_name)
        
        # Ensure payload indexes exist for filtering
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="user_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info("Created payload index for user_id")
        except Exception as e:
            # Index might already exist
            logger.debug("Payload index for user_id: %s", str(e))
        
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info("Created payload index for document_id")
        except Exception as e:
            # Index might already exist
            logger.debug("Payload index for document_id: %s", str(e))
            
    except Exception:
        logger.info("Creating collection %s with vector size %d", collection_name, vector_size)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        
        # Create payload indexes for efficient filtering
        logger.info("Creating payload indexes for filtering")
        client.create_payload_index(
            collection_name=collection_name,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Gemini API with new google-genai package."""
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY must be configured")
    
    client = genai.Client(api_key=settings.gemini_api_key)
    
    embeddings = []
    # Batch process to respect rate limits
    batch_size = 100  # Gemini supports batch embedding
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            # New API uses embed_content method on client
            result = client.models.embed_content(
                model="models/gemini-embedding-001",  # Only available embedding model
                contents=batch,
            )
            # Extract embeddings from response
            for embedding_obj in result.embeddings:
                embeddings.append(embedding_obj.values)
        except Exception as exc:
            logger.exception("Embedding generation failed for batch %d: %s", i, exc)
            raise ValueError(f"Failed to generate embeddings: {str(exc)[:100]}")
    
    return embeddings


def upsert_chunks_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    document_id: str,
    user_id: str,
    filename: str,
):
    """Upsert chunk embeddings to Qdrant with metadata."""
    points = []
    
    for chunk, embedding in zip(chunks, embeddings):
        point_id = str(uuid.uuid4())
        payload = {
            "user_id": user_id,
            "document_id": document_id,
            "chunk_index": chunk["chunk_index"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "filename": filename,
            "content": chunk["content"],
            "token_count": chunk["token_count"],
        }
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
    
    try:
        client.upsert(collection_name=collection_name, points=points)
        logger.info("Upserted %d chunks to Qdrant for document %s", len(points), document_id)
    except Exception as exc:
        logger.exception("Qdrant upsert failed: %s", exc)
        raise ValueError(f"Failed to store embeddings: {str(exc)[:100]}")


def process_document(
    document_id: str,
    user_id: str,
    filename: str,
    mime_type: str,
    content: bytes,
) -> dict[str, Any]:
    """
    Complete ingestion pipeline for a document.
    
    Returns:
    {
        "status": "ready" | "failed",
        "total_chunks": int,
        "error_message": str | None
    }
    """
    try:
        # Step 1: Extract text
        if mime_type == "application/pdf":
            pages = extract_text_from_pdf(content)
        elif mime_type == "text/plain":
            pages = extract_text_from_txt(content)
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")
        
        if not pages or not any(p["text"] for p in pages):
            raise ValueError("No text content extracted from document")
        
        # Step 2: Chunk text
        chunks = chunk_text_hybrid(
            pages,
            max_tokens=settings.max_chunk_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        
        if not chunks:
            raise ValueError("No chunks generated from document")
        
        logger.info("Generated %d chunks for document %s", len(chunks), document_id)
        
        # Step 3: Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = generate_embeddings(chunk_texts)
        
        # Step 4: Store in Qdrant
        client = get_qdrant_client()
        ensure_qdrant_collection(client, settings.qdrant_collection)
        upsert_chunks_to_qdrant(
            client,
            settings.qdrant_collection,
            chunks,
            embeddings,
            document_id,
            user_id,
            filename,
        )
        
        return {
            "status": "ready",
            "total_chunks": len(chunks),
            "error_message": None,
        }
    
    except Exception as exc:
        logger.exception("Document processing failed for %s: %s", document_id, exc)
        return {
            "status": "failed",
            "total_chunks": 0,
            "error_message": str(exc)[:500],
        }
