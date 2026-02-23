"""RAG chat – question + document_id (or 'all'), answer + sources."""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from supabase import create_client

from app.auth import AuthenticatedUser, get_current_user
from app.config import settings
from app.retrieval import rag_query

router = APIRouter(prefix="/chat", tags=["chat"])

DOCUMENTS_TABLE = "documents"
SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_id: str = "all"
    session_id: str | None = None  # Optional: continue existing session


class ChatSource(BaseModel):
    document_id: str
    filename: str
    page_start: int | None
    page_end: int | None
    snippet: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    session_id: str  # Return session ID for tracking
    intent: str | None = None  # Detected intent type


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


# Better suggestion chips based on document scope
SINGLE_DOC_SUGGESTIONS = [
    "What are the main topics covered in this document?",
    "Summarize the key points",
    "What are the most important takeaways?",
    "Extract all dates and deadlines mentioned",
    "What recommendations or conclusions are provided?",
    "List all requirements or criteria",
    "What are the main sections or chapters?",
    "Explain the methodology or approach used",
    "What data or statistics are presented?",
    "What are the limitations or challenges mentioned?",
    "Who are the key people or organizations mentioned?",
    "What actions or next steps are suggested?",
    "What definitions or terms are explained?",
    "What examples or case studies are provided?",
    "What are the main arguments or findings?",
]

MULTI_DOC_SUGGESTIONS = [
    "Create a comprehensive summary of all documents",
    "Compare and contrast these documents",
    "What are the common themes across all documents?",
    "What are the key differences between these documents?",
    "Summarize each document briefly",
    "What unique insights does each document provide?",
    "Extract all important dates from all documents",
    "What recommendations appear across multiple documents?",
    "Analyze the main trends or patterns",
    "Which document is most relevant for [specific topic]?",
    "What contradictions or conflicts exist between documents?",
    "List all requirements mentioned across documents",
    "What are the most important points from all documents?",
    "How do these documents relate to each other?",
    "What conclusions can be drawn from all documents together?",
]


def _supabase_user(token: str):
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured",
        )
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(token)
    return client


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Chat endpoint with full RAG pipeline.
    
    Retrieves relevant chunks from Qdrant and generates answer using Gemini.
    Saves conversation to chat history.
    """
    client = _supabase_user(user.token)

    # Verify document exists and is ready if specific document requested
    if payload.document_id != "all":
        query = (
            client.table(DOCUMENTS_TABLE)
            .select("id, status")
            .eq("user_id", user.id)
            .eq("id", payload.document_id)
            .limit(1)
        )
        
        try:
            result = query.execute()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query document: {str(exc)[:200]}",
            ) from exc
        
        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        if result.data[0].get("status") != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected document is still processing. Wait until status is ready.",
            )
    
    # Check if user has any ready documents
    try:
        ready_check = (
            client.table(DOCUMENTS_TABLE)
            .select("id")
            .eq("user_id", user.id)
            .eq("status", "ready")
            .limit(1)
            .execute()
        )
        
        if not ready_check.data:
            return ChatResponse(
                answer=(
                    "No ready documents found for your account yet. Upload a PDF or TXT file in the "
                    "Documents section, then ask your question again when status is ready."
                ),
                sources=[],
                session_id="",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check documents: {str(exc)[:200]}",
        ) from exc
    
    # Perform RAG query with hybrid semantic retrieval
    try:
        doc_id = None if payload.document_id == "all" else payload.document_id
        result = rag_query(user.id, payload.question, doc_id)
        
        sources = [
            ChatSource(
                document_id=src["document_id"],
                filename=src["filename"],
                page_start=src.get("page_start"),
                page_end=src.get("page_end"),
                snippet=src.get("snippet"),
            )
            for src in result["sources"]
        ]
        
        # Save to chat history
        session_id = payload.session_id
        
        # Create or get session
        if not session_id:
            session_result = (
                client.table(SESSIONS_TABLE)
                .insert({
                    "user_id": user.id,
                    "document_id": payload.document_id if payload.document_id != "all" else None,
                })
                .execute()
            )
            session_id = session_result.data[0]["id"]
        
        # Save message
        client.table(MESSAGES_TABLE).insert({
            "session_id": session_id,
            "user_id": user.id,
            "question": payload.question,
            "answer": result["answer"],
            "document_scope": payload.document_id,
            "sources": [
                {
                    "document_id": src.document_id,
                    "filename": src.filename,
                    "page_start": src.page_start,
                    "page_end": src.page_end,
                    "snippet": src.snippet,
                }
                for src in sources
            ],
        }).execute()
        
        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            session_id=session_id,
            intent=result.get("intent"),  # Include detected intent
        )
    
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(exc)[:200]}",
        ) from exc


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    document_id: str = "all",
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get smart suggestion chips based on document scope.
    
    Returns 15 relevant suggestions for single doc or all docs.
    """
    if document_id == "all":
        return SuggestionsResponse(suggestions=MULTI_DOC_SUGGESTIONS)
    else:
        return SuggestionsResponse(suggestions=SINGLE_DOC_SUGGESTIONS)
