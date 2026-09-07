"""Credential verification and token issuance."""

import bcrypt
import pytest

from app.core.errors import AuthError
from app.core.security import decode_token
from app.models import AdminUser
from app.services import auth_service


def _seed_admin(db):
    db.add(
        AdminUser(
            store_id="store001",
            username="admin",
            password_hash=bcrypt.hashpw(b"admin1234", bcrypt.gensalt()).decode(),
        )
    )
    db.commit()


def test_admin_login_success_and_token_claims(db, seeded_store):
    _seed_admin(db)
    admin = auth_service.admin_login(db, "store001", "admin", "admin1234")
    claims = decode_token(auth_service.admin_token(admin))
    assert claims["role"] == "admin"
    assert claims["store_id"] == "store001"
    assert claims["username"] == "admin"


def test_admin_login_wrong_password(db, seeded_store):
    _seed_admin(db)
    with pytest.raises(AuthError):
        auth_service.admin_login(db, "store001", "admin", "nope")


def test_table_auth_success_and_token_claims(db, seeded_store):
    table = auth_service.table_auth(db, "store001", "T1", "0000")
    claims = decode_token(auth_service.table_token(table))
    assert claims["role"] == "table"
    assert claims["table_id"] == seeded_store["table_id"]
    assert claims["table_number"] == "T1"


def test_table_auth_wrong_password(db, seeded_store):
    with pytest.raises(AuthError):
        auth_service.table_auth(db, "store001", "T1", "9999")
