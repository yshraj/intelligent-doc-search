"""Chat history management - sessions and messages."""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from supabase import create_client

from app.auth import AuthenticatedUser, get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])

SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    question: str
    answer: str
    document_scope: str
    sources: list[dict[str, Any]]
    created_at: str


class ChatSessionOut(BaseModel):
    id: str
    title: str | None
    document_id: str | None
    created_at: str
    updated_at: str
    message_count: int = 0
    last_message: str | None = None


class ChatSessionDetail(BaseModel):
    id: str
    title: str | None
    document_id: str | None
    created_at: str
    updated_at: str
    messages: list[ChatMessageOut]


class UpdateSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


def _supabase_user(token: str):
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured",
        )
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(token)
    return client


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
):
    """List user's chat sessions with message counts."""
    client = _supabase_user(user.token)
    
    try:
        # Get sessions
        query = (
            client.table(SESSIONS_TABLE)
            .select("id, title, document_id, created_at, updated_at")
            .eq("user_id", user.id)
            .order("updated_at", desc=True)
            .limit(limit)
        )
        
        if search:
            query = query.ilike("title", f"%{search}%")
        
        sessions_result = query.execute()
        
        # Get message counts and last messages for each session
        sessions = []
        for session in sessions_result.data:
            # Get message count
            count_result = (
                client.table(MESSAGES_TABLE)
                .select("id", count="exact")
                .eq("session_id", session["id"])
                .execute()
            )
            
            # Get last message
            last_msg_result = (
                client.table(MESSAGES_TABLE)
                .select("question")
                .eq("session_id", session["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            sessions.append(ChatSessionOut(
                id=session["id"],
                title=session.get("title"),
                document_id=session.get("document_id"),
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                message_count=count_result.count or 0,
                last_message=last_msg_result.data[0]["question"] if last_msg_result.data else None,
            ))
        
        return sessions
    
    except Exception as exc:
        logger.exception("List sessions failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(exc)[:200]}",
        ) from exc


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get session with all messages."""
    client = _supabase_user(user.token)
    
    try:
        # Get session
        session_result = (
            client.table(SESSIONS_TABLE)
            .select("id, title, document_id, created_at, updated_at")
            .eq("id", session_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        session = session_result.data[0]
        
        # Get messages
        messages_result = (
            client.table(MESSAGES_TABLE)
            .select("id, session_id, question, answer, document_scope, sources, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        
        messages = [
            ChatMessageOut(
                id=msg["id"],
                session_id=msg["session_id"],
                question=msg["question"],
                answer=msg["answer"],
                document_scope=msg["document_scope"],
                sources=msg.get("sources", []),
                created_at=msg["created_at"],
            )
            for msg in messages_result.data
        ]
        
        return ChatSessionDetail(
            id=session["id"],
            title=session.get("title"),
            document_id=session.get("document_id"),
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            messages=messages,
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Get session failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(exc)[:200]}",
        ) from exc


@router.patch("/sessions/{session_id}", response_model=ChatSessionOut)
async def update_session(
    session_id: str,
    payload: UpdateSessionRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update session title."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table(SESSIONS_TABLE)
            .update({"title": payload.title})
            .eq("id", session_id)
            .eq("user_id", user.id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        session = result.data[0]
        return ChatSessionOut(
            id=session["id"],
            title=session.get("title"),
            document_id=session.get("document_id"),
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=0,
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Update session failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(exc)[:200]}",
        ) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete session and all its messages."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table(SESSIONS_TABLE)
            .delete()
            .eq("id", session_id)
            .eq("user_id", user.id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        return {"deleted": session_id}
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Delete session failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(exc)[:200]}",
        ) from exc


@router.delete("/clear-all")
async def clear_all_history(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete all chat history for the user."""
    client = _supabase_user(user.token)
    
    try:
        # Delete all sessions (messages will cascade delete)
        result = (
            client.table(SESSIONS_TABLE)
            .delete()
            .eq("user_id", user.id)
            .execute()
        )
        
        count = len(result.data) if result.data else 0
        
        return {
            "deleted_count": count,
            "message": f"Successfully deleted {count} session(s)",
        }
    
    except Exception as exc:
        logger.exception("Clear all history failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(exc)[:200]}",
        ) from exc


@router.get("/search", response_model=list[ChatMessageOut])
async def search_messages(
    user: AuthenticatedUser = Depends(get_current_user),
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
):
    """Search through chat messages."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table(MESSAGES_TABLE)
            .select("id, session_id, question, answer, document_scope, sources, created_at")
            .eq("user_id", user.id)
            .or_(f"question.ilike.%{q}%,answer.ilike.%{q}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [
            ChatMessageOut(
                id=msg["id"],
                session_id=msg["session_id"],
                question=msg["question"],
                answer=msg["answer"],
                document_scope=msg["document_scope"],
                sources=msg.get("sources", []),
                created_at=msg["created_at"],
            )
            for msg in result.data
        ]
    
    except Exception as exc:
        logger.exception("Search messages failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search messages: {str(exc)[:200]}",
        ) from exc


@router.get("/export")
async def export_history(
    user: AuthenticatedUser = Depends(get_current_user),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Export all chat history."""
    client = _supabase_user(user.token)
    
    try:
        # Get all sessions with messages
        sessions_result = (
            client.table(SESSIONS_TABLE)
            .select("id, title, document_id, created_at, updated_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        
        export_data = []
        
        for session in sessions_result.data:
            messages_result = (
                client.table(MESSAGES_TABLE)
                .select("question, answer, document_scope, sources, created_at")
                .eq("session_id", session["id"])
                .order("created_at", desc=False)
                .execute()
            )
            
            export_data.append({
                "session": {
                    "id": session["id"],
                    "title": session.get("title"),
                    "document_id": session.get("document_id"),
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                },
                "messages": messages_result.data,
            })
        
        if format == "json":
            return {
                "format": "json",
                "exported_at": "now",
                "user_id": user.id,
                "sessions": export_data,
            }
        else:
            # CSV format - flatten messages
            csv_rows = []
            for session_data in export_data:
                for msg in session_data["messages"]:
                    csv_rows.append({
                        "session_id": session_data["session"]["id"],
                        "session_title": session_data["session"]["title"],
                        "question": msg["question"],
                        "answer": msg["answer"],
                        "document_scope": msg["document_scope"],
                        "created_at": msg["created_at"],
                    })
            
            return {
                "format": "csv",
                "exported_at": "now",
                "user_id": user.id,
                "rows": csv_rows,
            }
    
    except Exception as exc:
        logger.exception("Export history failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export history: {str(exc)[:200]}",
        ) from exc
