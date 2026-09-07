"""Password hashing (bcrypt) and stateless JWT issuing/verification.

Tokens are never stored server-side: a token is trusted purely by recomputing
its HS256 signature and checking expiry. Two roles exist — ``admin`` and
``table`` — distinguished by the ``role`` claim.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import JWT_ALGORITHM, JWT_SECRET, JWT_TTL_SECONDS


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Malformed stored hash — treat as non-match rather than crashing.
        return False


def create_token(claims: dict) -> str:
    """Issue an HS256 JWT with the given claims plus a 16h expiry."""
    payload = dict(claims)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=JWT_TTL_SECONDS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Return claims if the token is valid and unexpired, else None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
