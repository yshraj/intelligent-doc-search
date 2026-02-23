"""Supabase auth helpers for protected routes."""
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.config import settings

security = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthenticatedUser:
    """Normalized authenticated user extracted from a verified JWT."""

    id: str
    email: str | None
    token: str


def _project_ref_from_url(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.split(".")[0]
    except Exception:
        return ""


def _issuer_from_url(url: str) -> str:
    return f"{url.rstrip('/')}/auth/v1"


def _jwks_url_from_url(url: str) -> str:
    return f"{_issuer_from_url(url)}/.well-known/jwks.json"


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _verify_supabase_jwt(token: str) -> dict:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured",
        )

    issuer = _issuer_from_url(settings.supabase_url)
    audience = settings.supabase_jwt_audience or "authenticated"
    jwks_url = _jwks_url_from_url(settings.supabase_url)

    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token).key
    except PyJWKClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch Supabase public key from JWKS: {str(exc)[:180]}",
        ) from exc

    try:
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            issuer=issuer,
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(exc)[:180]}",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser:
    """Require Bearer token, verify it against Supabase JWKS, and return user identity."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization must use Bearer token",
        )

    token = credentials.credentials
    payload = _verify_supabase_jwt(token)

    project_ref = _project_ref_from_url(settings.supabase_url)
    issuer = str(payload.get("iss", ""))
    if project_ref and issuer and project_ref not in issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token issuer project does not match backend SUPABASE_URL",
        )

    user_id = str(payload.get("sub", "")).strip()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user id (sub claim)",
        )

    email = payload.get("email")
    email_value = str(email).strip() if email else None
    return AuthenticatedUser(id=user_id, email=email_value, token=token)


async def get_current_user_id(user: AuthenticatedUser = Depends(get_current_user)) -> str:
    """Return authenticated user id from validated token."""
    return user.id
