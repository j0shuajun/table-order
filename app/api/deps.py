"""Request dependencies: DB session and JWT-based auth guards.

REST endpoints authenticate via the ``Authorization: Bearer`` header; the SSE
endpoint takes the token as a query parameter because EventSource cannot set
headers (see api-contract R-AUTH-4).
"""

from fastapi import Header

from app.core.db import get_db
from app.core.errors import AuthError, ForbiddenError
from app.core.security import decode_token

__all__ = ["get_db", "require_admin", "require_table", "claims_from_token"]


def claims_from_token(token: str, expected_role: str) -> dict:
    claims = decode_token(token)
    if claims is None:
        raise AuthError("인증이 필요합니다.")
    if claims.get("role") != expected_role:
        raise ForbiddenError("권한이 없습니다.")
    return claims


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("인증이 필요합니다.")
    return authorization[len("Bearer ") :]


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    return claims_from_token(_bearer(authorization), "admin")


def require_table(authorization: str | None = Header(default=None)) -> dict:
    return claims_from_token(_bearer(authorization), "table")
