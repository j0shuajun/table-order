"""Unit tests for password hashing and JWT issue/verify (R-AUTH-*)."""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("admin1234")
    assert hashed != "admin1234"
    assert verify_password("admin1234", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_verify_password_with_malformed_hash_returns_false():
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_token_roundtrip_preserves_claims():
    token = create_token({"role": "admin", "store_id": "store001", "username": "admin"})
    claims = decode_token(token)
    assert claims is not None
    assert claims["role"] == "admin"
    assert claims["store_id"] == "store001"
    assert claims["username"] == "admin"
    assert "exp" in claims


def test_decode_rejects_bad_signature():
    forged = jwt.encode(
        {"role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "different-secret",
        algorithm=JWT_ALGORITHM,
    )
    assert decode_token(forged) is None


def test_decode_rejects_expired_token():
    expired = jwt.encode(
        {"role": "table", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    assert decode_token(expired) is None
