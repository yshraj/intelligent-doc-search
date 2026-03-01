"""Document groups and tags API endpoints."""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import create_client

from app.auth import AuthenticatedUser, get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["groups"])


class TagOut(BaseModel):
    id: str
    document_id: str
    tag_name: str
    tag_category: str
    confidence_score: float
    auto_generated: bool
    created_at: str


class TagCreate(BaseModel):
    tag_name: str
    tag_category: str
    confidence_score: float = 1.0
    auto_generated: bool = False


class GroupOut(BaseModel):
    id: str
    group_name: str
    group_type: str
    parent_group_id: str | None
    description: str | None
    document_count: int
    created_at: str


class GroupCreate(BaseModel):
    group_name: str
    group_type: str = "custom"
    parent_group_id: str | None = None
    description: str | None = None


class GroupMembershipOut(BaseModel):
    id: str
    document_id: str
    group_id: str
    added_at: str


class DocumentWithTags(BaseModel):
    id: str
    filename: str
    tags: list[TagOut]


def _supabase_user(token: str):
    """Client with user token for RLS."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured",
        )
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(token)
    return client


# ============================================================================
# Tag Endpoints
# ============================================================================

@router.get("/documents/{document_id}/tags", response_model=list[TagOut])
async def get_document_tags(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all tags for a document."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table("document_tags")
            .select("*")
            .eq("document_id", document_id)
            .order("confidence_score", desc=True)
            .execute()
        )
    except Exception as exc:
        logger.exception("Get document tags failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tags: {str(exc)[:200]}",
        )
    
    return [
        TagOut(
            id=str(row["id"]),
            document_id=str(row["document_id"]),
            tag_name=row["tag_name"],
            tag_category=row["tag_category"],
            confidence_score=row["confidence_score"],
            auto_generated=row["auto_generated"],
            created_at=str(row["created_at"]),
        )
        for row in result.data
    ]


@router.post("/documents/{document_id}/tags", response_model=TagOut)
async def add_document_tag(
    document_id: str,
    tag: TagCreate,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a tag to a document."""
    client = _supabase_user(user.token)
    
    # Verify document ownership
    try:
        doc_result = (
            client.table("documents")
            .select("id")
            .eq("id", document_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Document verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify document",
        )
    
    # Add tag
    try:
        result = (
            client.table("document_tags")
            .insert({
                "document_id": document_id,
                "tag_name": tag.tag_name,
                "tag_category": tag.tag_category,
                "confidence_score": tag.confidence_score,
                "auto_generated": tag.auto_generated,
            })
            .execute()
        )
    except Exception as exc:
        logger.exception("Add tag failed: %s", exc)
        # Check for duplicate
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag already exists for this document",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tag: {str(exc)[:200]}",
        )
    
    row = result.data[0]
    return TagOut(
        id=str(row["id"]),
        document_id=str(row["document_id"]),
        tag_name=row["tag_name"],
        tag_category=row["tag_category"],
        confidence_score=row["confidence_score"],
        auto_generated=row["auto_generated"],
        created_at=str(row["created_at"]),
    )


@router.delete("/documents/{document_id}/tags/{tag_id}")
async def delete_document_tag(
    document_id: str,
    tag_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a tag from a document."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table("document_tags")
            .delete()
            .eq("id", tag_id)
            .eq("document_id", document_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Delete tag failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tag: {str(exc)[:200]}",
        )
    
    return {"deleted": tag_id}


@router.get("/tags/search", response_model=list[DocumentWithTags])
async def search_by_tags(
    tag_names: str,  # Comma-separated tag names
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Search documents by tags."""
    client = _supabase_user(user.token)
    
    tag_list = [t.strip() for t in tag_names.split(",") if t.strip()]
    
    if not tag_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one tag name required",
        )
    
    try:
        # Get documents with matching tags
        result = (
            client.table("document_tags")
            .select("document_id, documents(id, filename)")
            .in_("tag_name", tag_list)
            .execute()
        )
        
        # Group by document
        doc_map = {}
        for row in result.data:
            doc_id = str(row["document_id"])
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "id": doc_id,
                    "filename": row["documents"]["filename"],
                    "tags": [],
                }
        
        # Get all tags for these documents
        if doc_map:
            tags_result = (
                client.table("document_tags")
                .select("*")
                .in_("document_id", list(doc_map.keys()))
                .execute()
            )
            
            for tag_row in tags_result.data:
                doc_id = str(tag_row["document_id"])
                if doc_id in doc_map:
                    doc_map[doc_id]["tags"].append(
                        TagOut(
                            id=str(tag_row["id"]),
                            document_id=doc_id,
                            tag_name=tag_row["tag_name"],
                            tag_category=tag_row["tag_category"],
                            confidence_score=tag_row["confidence_score"],
                            auto_generated=tag_row["auto_generated"],
                            created_at=str(tag_row["created_at"]),
                        )
                    )
        
        return [
            DocumentWithTags(**doc_data)
            for doc_data in doc_map.values()
        ]
    
    except Exception as exc:
        logger.exception("Search by tags failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search: {str(exc)[:200]}",
        )


# ============================================================================
# Group Endpoints
# ============================================================================

@router.get("", response_model=list[GroupOut])
async def list_groups(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all groups for the current user."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table("document_groups")
            .select("*")
            .eq("user_id", user.id)
            .order("group_name")
            .execute()
        )
        
        groups = []
        for row in result.data:
            # Get document count
            count_result = (
                client.table("document_group_membership")
                .select("id", count="exact")
                .eq("group_id", row["id"])
                .execute()
            )
            
            groups.append(
                GroupOut(
                    id=str(row["id"]),
                    group_name=row["group_name"],
                    group_type=row["group_type"],
                    parent_group_id=str(row["parent_group_id"]) if row.get("parent_group_id") else None,
                    description=row.get("description"),
                    document_count=count_result.count or 0,
                    created_at=str(row["created_at"]),
                )
            )
        
        return groups
    
    except Exception as exc:
        logger.exception("List groups failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list groups: {str(exc)[:200]}",
        )


@router.post("", response_model=GroupOut)
async def create_group(
    group: GroupCreate,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a new document group."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table("document_groups")
            .insert({
                "user_id": user.id,
                "group_name": group.group_name,
                "group_type": group.group_type,
                "parent_group_id": group.parent_group_id,
                "description": group.description,
            })
            .execute()
        )
        
        row = result.data[0]
        return GroupOut(
            id=str(row["id"]),
            group_name=row["group_name"],
            group_type=row["group_type"],
            parent_group_id=str(row["parent_group_id"]) if row.get("parent_group_id") else None,
            description=row.get("description"),
            document_count=0,
            created_at=str(row["created_at"]),
        )
    
    except Exception as exc:
        logger.exception("Create group failed: %s", exc)
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Group with this name already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(exc)[:200]}",
        )


@router.get("/{group_id}/documents")
async def get_group_documents(
    group_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all documents in a group."""
    client = _supabase_user(user.token)
    
    try:
        # Verify group ownership
        group_result = (
            client.table("document_groups")
            .select("id")
            .eq("id", group_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        
        if not group_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        
        # Get documents
        result = (
            client.table("document_group_membership")
            .select("document_id, documents(id, filename, title, mime_type, status, created_at)")
            .eq("group_id", group_id)
            .execute()
        )
        
        return [
            {
                "id": str(row["documents"]["id"]),
                "filename": row["documents"]["filename"],
                "title": row["documents"].get("title"),
                "mime_type": row["documents"]["mime_type"],
                "status": row["documents"]["status"],
                "created_at": str(row["documents"]["created_at"]),
            }
            for row in result.data
        ]
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Get group documents failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(exc)[:200]}",
        )


@router.put("/documents/{document_id}/groups")
async def update_document_groups(
    document_id: str,
    group_ids: list[str],
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update group membership for a document (replaces existing)."""
    client = _supabase_user(user.token)
    
    try:
        # Verify document ownership
        doc_result = (
            client.table("documents")
            .select("id")
            .eq("id", document_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        # Delete existing memberships
        client.table("document_group_membership").delete().eq("document_id", document_id).execute()
        
        # Add new memberships
        if group_ids:
            memberships = [
                {
                    "document_id": document_id,
                    "group_id": group_id,
                }
                for group_id in group_ids
            ]
            
            client.table("document_group_membership").insert(memberships).execute()
        
        return {"document_id": document_id, "group_ids": group_ids}
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Update document groups failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update groups: {str(exc)[:200]}",
        )


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a group (memberships are cascade deleted)."""
    client = _supabase_user(user.token)
    
    try:
        result = (
            client.table("document_groups")
            .delete()
            .eq("id", group_id)
            .eq("user_id", user.id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        
        return {"deleted": group_id}
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Delete group failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(exc)[:200]}",
        )
