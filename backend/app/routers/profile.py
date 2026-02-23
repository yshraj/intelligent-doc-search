"""One-call user profile init endpoint."""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from postgrest import APIError as PostgrestAPIError
from supabase import create_client

from app.auth import AuthenticatedUser, get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

PROFILE_TABLE = "user_profiles"


class ProfileData(BaseModel):
    id: str
    email: str
    full_name: str | None
    company: str | None
    role: str | None
    onboarding_completed: bool


class ProfileInitResponse(BaseModel):
    status: Literal["new", "existing"]
    profile: ProfileData
    is_new_user: bool


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    company: str | None = None
    role: str | None = None


class ProfileUpdateResponse(BaseModel):
    profile: ProfileData


def _supabase_client_for_user(token: str):
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be configured for profile init",
        )
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(token)
    return client


def _raise_profile_error(action: str, exc: Exception) -> None:
    raw = str(exc)
    lowered = raw.lower()

    # Extract structured message from PostgREST APIError when available
    if isinstance(exc, PostgrestAPIError) and exc.message:
        raw = exc.message
        if exc.details:
            raw = f"{raw} ({exc.details})"

    if (
        'relation "user_profiles" does not exist' in lowered
        or "pgrst205" in lowered
        or "could not find the table 'public.user_profiles' in the schema cache" in lowered
    ):
        detail = (
            "Missing user_profiles table (or stale Supabase schema cache). "
            "Run supabase/schema.sql in the same Supabase project as SUPABASE_URL, then retry."
        )
    elif "row-level security" in lowered or "rls" in lowered:
        detail = "RLS policy blocked the operation. Ensure policies allow auth.uid() = id for select, insert, and update."
    elif "jwt" in lowered and ("invalid" in lowered or "expired" in lowered):
        detail = "Supabase rejected JWT. Sign out and sign in again."
    else:
        detail = f"Failed to {action} profile: {raw[:200]}"

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc


@router.post("/init", response_model=ProfileInitResponse)
async def init_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """Create missing profile row, or return existing status with profile data."""
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing email claim",
        )

    supabase = _supabase_client_for_user(user.token)
    user_id = user.id

    try:
        existing = (
            supabase.table(PROFILE_TABLE)
            .select("id, email, full_name, company, role, onboarding_completed")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        _raise_profile_error("query", exc)

    if existing.data:
        profile_row = existing.data[0]
        profile = ProfileData(
            id=profile_row["id"],
            email=profile_row["email"],
            full_name=profile_row.get("full_name"),
            company=profile_row.get("company"),
            role=profile_row.get("role"),
            onboarding_completed=profile_row.get("onboarding_completed", False),
        )
        return ProfileInitResponse(status="existing", profile=profile, is_new_user=False)

    try:
        # Note: supabase-py insert() does not support .select() chaining; it returns
        # the full row by default via Prefer: return=representation.
        result = (
            supabase.table(PROFILE_TABLE)
            .insert({"id": user_id, "email": user.email})
            .execute()
        )
        profile_row = result.data[0]
        profile = ProfileData(
            id=profile_row["id"],
            email=profile_row["email"],
            full_name=profile_row.get("full_name"),
            company=profile_row.get("company"),
            role=profile_row.get("role"),
            onboarding_completed=profile_row.get("onboarding_completed", False),
        )
    except Exception as exc:
        # Safe race handling: another init call may create the same row first.
        if "duplicate key value violates unique constraint" in str(exc).lower():
            try:
                existing = (
                    supabase.table(PROFILE_TABLE)
                    .select("id, email, full_name, company, role, onboarding_completed")
                    .eq("id", user_id)
                    .limit(1)
                    .execute()
                )
                profile_row = existing.data[0]
                profile = ProfileData(
                    id=profile_row["id"],
                    email=profile_row["email"],
                    full_name=profile_row.get("full_name"),
                    company=profile_row.get("company"),
                    onboarding_completed=profile_row.get("onboarding_completed", False),
                )
                return ProfileInitResponse(status="existing", profile=profile, is_new_user=False)
            except Exception as query_exc:
                _raise_profile_error("query", query_exc)
        _raise_profile_error("create", exc)

    return ProfileInitResponse(status="new", profile=profile, is_new_user=True)


@router.post("/update", response_model=ProfileUpdateResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update user profile with onboarding information."""
    supabase = _supabase_client_for_user(user.token)
    user_id = user.id

    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.company is not None:
        update_data["company"] = request.company
    if request.role is not None:
        update_data["role"] = request.role
    update_data["onboarding_completed"] = True

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    try:
        # update() returns FilterRequestBuilder (no select); representation returned by default
        result = (
            supabase.table(PROFILE_TABLE)
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        profile_row = result.data[0]
        profile = ProfileData(
            id=profile_row["id"],
            email=profile_row["email"],
            full_name=profile_row.get("full_name"),
            company=profile_row.get("company"),
            role=profile_row.get("role"),
            onboarding_completed=profile_row.get("onboarding_completed", False),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Profile update failed: %s", exc)
        _raise_profile_error("update", exc)

    return ProfileUpdateResponse(profile=profile)


@router.get("/me")
async def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    """Return authenticated user identity from verified token."""
    return {
        "id": user.id,
        "email": user.email,
    }
