from hmac import compare_digest
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import API_ADMIN_KEY, API_VIEWER_KEY

ApiRole = Literal["admin", "viewer"]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_role(api_key: str | None = Depends(api_key_header)) -> ApiRole:
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if compare_digest(api_key, API_ADMIN_KEY):
        return "admin"
    if compare_digest(api_key, API_VIEWER_KEY):
        return "viewer"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def require_admin(role: ApiRole = Depends(get_api_role)) -> ApiRole:
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return role
