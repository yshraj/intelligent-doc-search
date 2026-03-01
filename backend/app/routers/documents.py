"""Document list, upload, get, delete. All require JWT; scoped by user_id."""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from postgrest import APIError as PostgrestAPIError
from supabase import create_client

from app.auth import AuthenticatedUser, get_current_user, get_current_user_id
from app.config import settings
from app.ingestion import compute_file_hash, process_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

DOCUMENTS_TABLE = "documents"
STORAGE_BUCKET = "documents"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME = {"application/pdf", "text/plain"}


class DocumentOut(BaseModel):
    id: str
    filename: str
    title: str | None
    mime_type: str
    file_size: int
    status: str
    created_at: str


def _supabase_admin():
    """Client with service role for Storage (backend uploads)."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required for document upload",
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _supabase_user(token: str):
    """Client with user token for documents table (RLS)."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured",
        )
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(token)
    return client


def _row_to_doc(row: dict[str, Any]) -> DocumentOut:
    return DocumentOut(
        id=str(row["id"]),
        filename=row["filename"],
        title=row.get("title"),
        mime_type=row["mime_type"],
        file_size=row.get("file_size", 0),
        status=row["status"],
        created_at=str(row["created_at"]),
    )


@router.get("", response_model=list[DocumentOut])
async def list_documents(user: AuthenticatedUser = Depends(get_current_user)):
    """List current user's documents."""
    client = _supabase_user(user.token)
    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .select("id, filename, title, mime_type, file_size, status, created_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        logger.exception("List documents failed: %s", exc)
        _raise_doc_error("list", exc)
    return [_row_to_doc(r) for r in result.data]


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Upload a single PDF or text file with deduplication."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: PDF, plain text",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    # Compute hash for deduplication
    file_hash = compute_file_hash(content)
    
    # Check if file already exists for this user (only if file_hash column exists)
    client = _supabase_user(user.token)
    try:
        existing = (
            client.table(DOCUMENTS_TABLE)
            .select("id, filename, title, mime_type, file_size, status, created_at")
            .eq("user_id", user.id)
            .eq("file_hash", file_hash)
            .limit(1)
            .execute()
        )
        
        if existing.data:
            # File already exists - return existing document
            logger.info(
                "Duplicate file detected for user %s: hash=%s, existing_id=%s",
                user.id, file_hash, existing.data[0]["id"]
            )
            return _row_to_doc(existing.data[0])
    
    except Exception as exc:
        # If file_hash column doesn't exist yet, just log and continue
        logger.warning("Deduplication check failed (file_hash column may not exist yet), continuing with upload: %s", exc)

    doc_id = str(uuid.uuid4())
    storage_path = f"{user.id}/{doc_id}/{file.filename}"

    admin = _supabase_admin()
    try:
        admin.storage.from_(STORAGE_BUCKET).upload(
            storage_path,
            content,
            {"content-type": content_type},
        )
    except Exception as exc:
        logger.exception("Storage upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file. Ensure Storage bucket 'documents' exists and storage.sql RLS is applied.",
        ) from exc

    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .insert({
                "id": doc_id,
                "user_id": user.id,
                "filename": file.filename,
                "title": file.filename,
                "storage_path": storage_path,
                "mime_type": content_type,
                "file_size": len(content),
                "file_hash": file_hash,  # Will be ignored if column doesn't exist
                "status": "processing",
            })
            .execute()
        )
    except Exception as exc:
        logger.exception("Document insert failed: %s", exc)
        
        # If file_hash column doesn't exist, try without it
        if "file_hash" in str(exc).lower():
            logger.warning("Retrying insert without file_hash column...")
            try:
                result = (
                    client.table(DOCUMENTS_TABLE)
                    .insert({
                        "id": doc_id,
                        "user_id": user.id,
                        "filename": file.filename,
                        "title": file.filename,
                        "storage_path": storage_path,
                        "mime_type": content_type,
                        "file_size": len(content),
                        "status": "processing",
                    })
                    .execute()
                )
                logger.info("Insert succeeded without file_hash. Please run migration: supabase/add_file_hash.sql")
            except Exception as retry_exc:
                try:
                    admin.storage.from_(STORAGE_BUCKET).remove([storage_path])
                except Exception:
                    pass
                _raise_doc_error("create", retry_exc)
        else:
            try:
                admin.storage.from_(STORAGE_BUCKET).remove([storage_path])
            except Exception:
                pass
            _raise_doc_error("create", exc)

    row = result.data[0]
    
    # Process document in background
    background_tasks.add_task(
        _process_document_background,
        doc_id,
        user.id,
        file.filename,
        content_type,
        content,
    )
    
    return _row_to_doc(row)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get document metadata. Enforces ownership via RLS."""
    client = _supabase_user(user.token)
    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .select("id, filename, title, mime_type, file_size, status, created_at")
            .eq("id", document_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.exception("Get document failed: %s", exc)
        _raise_doc_error("get", exc)

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _row_to_doc(result.data[0])


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Download document file. Enforces ownership via RLS."""
    from fastapi.responses import Response
    
    client = _supabase_user(user.token)
    
    # Get document metadata to verify ownership and get storage path
    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .select("id, filename, storage_path, mime_type")
            .eq("id", document_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.exception("Get document for download failed: %s", exc)
        _raise_doc_error("get", exc)

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    doc = result.data[0]
    storage_path = doc["storage_path"]
    filename = doc["filename"]
    mime_type = doc["mime_type"]
    
    # Download file from storage
    admin = _supabase_admin()
    try:
        file_data = admin.storage.from_(STORAGE_BUCKET).download(storage_path)
        
        # Return file as response with proper headers
        return Response(
            content=file_data,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mime_type,
            }
        )
    except Exception as exc:
        logger.exception("Storage download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(exc)[:200]}",
        ) from exc


@router.delete("/clear-all")
async def clear_all_documents(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete ALL documents for the current user from Storage, DB, and Qdrant."""
    client = _supabase_user(user.token)
    
    # Get all user documents
    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .select("id, storage_path")
            .eq("user_id", user.id)
            .execute()
        )
    except Exception as exc:
        logger.exception("Get documents for clear all failed: %s", exc)
        _raise_doc_error("list", exc)

    if not result.data:
        return {"deleted_count": 0, "message": "No documents to delete"}

    document_ids = [doc["id"] for doc in result.data]
    storage_paths = [doc["storage_path"] for doc in result.data]
    
    # Delete from Qdrant
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from app.ingestion import get_qdrant_client
        
        qdrant = get_qdrant_client()
        
        # Check if collection exists first
        try:
            qdrant.get_collection(settings.qdrant_collection)
            # Collection exists, proceed with delete
            qdrant.delete(
                collection_name=settings.qdrant_collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user.id)),
                    ]
                ),
            )
            logger.info("Deleted all vectors for user %s from Qdrant", user.id)
        except Exception as collection_exc:
            logger.info("Qdrant collection not found or delete failed: %s", str(collection_exc)[:100])
    except Exception as exc:
        logger.warning("Qdrant delete setup failed (continuing with storage/DB delete): %s", exc)
    
    # Delete from Storage
    admin = _supabase_admin()
    deleted_storage_count = 0
    for storage_path in storage_paths:
        try:
            admin.storage.from_(STORAGE_BUCKET).remove([storage_path])
            deleted_storage_count += 1
        except Exception as exc:
            logger.warning("Storage delete failed for %s: %s", storage_path, exc)

    # Delete from DB
    try:
        client.table(DOCUMENTS_TABLE).delete().eq("user_id", user.id).execute()
    except Exception as exc:
        logger.exception("Document clear all failed: %s", exc)
        _raise_doc_error("delete", exc)

    return {
        "deleted_count": len(document_ids),
        "message": f"Successfully deleted {len(document_ids)} document(s)"
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete document from Storage, DB, and Qdrant."""
    client = _supabase_user(user.token)
    try:
        result = (
            client.table(DOCUMENTS_TABLE)
            .select("storage_path")
            .eq("id", document_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.exception("Get document for delete failed: %s", exc)
        _raise_doc_error("get", exc)

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    storage_path = result.data[0]["storage_path"]
    
    # Delete from Qdrant
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from app.ingestion import get_qdrant_client
        
        qdrant = get_qdrant_client()
        
        # Check if collection exists first
        try:
            qdrant.get_collection(settings.qdrant_collection)
            # Collection exists, proceed with delete
            qdrant.delete(
                collection_name=settings.qdrant_collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                        FieldCondition(key="user_id", match=MatchValue(value=user.id)),
                    ]
                ),
            )
            logger.info("Deleted vectors for document %s from Qdrant", document_id)
        except Exception as collection_exc:
            # Collection doesn't exist or other error - log but continue
            logger.info("Qdrant collection not found or delete failed (document may not have been processed): %s", 
                       str(collection_exc)[:100])
    except Exception as exc:
        logger.warning("Qdrant delete setup failed (continuing with storage/DB delete): %s", exc)
    
    # Delete from Storage
    admin = _supabase_admin()
    try:
        admin.storage.from_(STORAGE_BUCKET).remove([storage_path])
    except Exception as exc:
        logger.warning("Storage delete failed (continuing with DB delete): %s", exc)

    # Delete from DB
    try:
        client.table(DOCUMENTS_TABLE).delete().eq("id", document_id).eq("user_id", user.id).execute()
    except Exception as exc:
        logger.exception("Document delete failed: %s", exc)
        _raise_doc_error("delete", exc)

    return {"deleted": document_id}


def _raise_doc_error(action: str, exc: Exception) -> None:
    raw = str(exc)
    if isinstance(exc, PostgrestAPIError) and exc.message:
        raw = exc.message
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to {action} document: {raw[:200]}",
    ) from exc


def _process_document_background(
    document_id: str,
    user_id: str,
    filename: str,
    mime_type: str,
    content: bytes,
):
    """Background task to process document: extract, chunk, embed, store, and tag."""
    logger.info("Starting background processing for document %s", document_id)
    
    try:
        result = process_document(document_id, user_id, filename, mime_type, content)
        
        # Update document status in DB
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.error("Cannot update document status: Supabase not configured")
            return
        
        admin = create_client(settings.supabase_url, settings.supabase_service_role_key)
        admin.table(DOCUMENTS_TABLE).update({
            "status": result["status"],
        }).eq("id", document_id).execute()
        
        # If processing succeeded, save tags and create groups
        if result["status"] == "ready" and result.get("tags"):
            try:
                # Save tags
                tags_to_insert = [
                    {
                        "document_id": document_id,
                        "tag_name": tag["name"],
                        "tag_category": tag["category"],
                        "confidence_score": tag["confidence"],
                        "auto_generated": True,
                    }
                    for tag in result["tags"]
                ]
                
                if tags_to_insert:
                    admin.table("document_tags").insert(tags_to_insert).execute()
                    logger.info("Saved %d tags for document %s", len(tags_to_insert), document_id)
                
                # Create groups if they don't exist and assign document
                if result.get("suggested_groups"):
                    # Only use the FIRST (most confident) group to avoid duplicates
                    # The document_grouper returns groups in order of confidence
                    primary_group = result["suggested_groups"][0] if result["suggested_groups"] else None
                    
                    if primary_group:
                        try:
                            # Check if group exists
                            existing_group = (
                                admin.table("document_groups")
                                .select("id")
                                .eq("user_id", user_id)
                                .eq("group_name", primary_group)
                                .limit(1)
                                .execute()
                            )
                            
                            if existing_group.data:
                                group_id = existing_group.data[0]["id"]
                            else:
                                # Create group
                                new_group = (
                                    admin.table("document_groups")
                                    .insert({
                                        "user_id": user_id,
                                        "group_name": primary_group,
                                        "group_type": "type_based",
                                    })
                                    .execute()
                                )
                                group_id = new_group.data[0]["id"]
                            
                            # Add document to group (only once)
                            try:
                                admin.table("document_group_membership").insert({
                                    "document_id": document_id,
                                    "group_id": group_id,
                                }).execute()
                            except Exception as membership_exc:
                                # Ignore duplicate membership errors
                                if "duplicate" not in str(membership_exc).lower():
                                    raise
                            
                            logger.info("Assigned document %s to primary group: %s", document_id, primary_group)
                            
                        except Exception as group_exc:
                            logger.warning("Failed to create/assign group %s: %s", primary_group, group_exc)
                    
                    logger.info("Assigned document %s to groups", document_id)
            
            except Exception as tag_exc:
                logger.warning("Failed to save tags/groups for document %s: %s", document_id, tag_exc)
        
        logger.info("Document %s processing complete: %s", document_id, result["status"])
    
    except Exception as exc:
        logger.exception("Background processing failed for document %s: %s", document_id, exc)
        # Try to mark as failed
        try:
            if settings.supabase_url and settings.supabase_service_role_key:
                admin = create_client(settings.supabase_url, settings.supabase_service_role_key)
                admin.table(DOCUMENTS_TABLE).update({
                    "status": "failed",
                }).eq("id", document_id).execute()
        except Exception:
            pass
