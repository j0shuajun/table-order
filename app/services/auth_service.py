"""Admin and table authentication: verify credentials, issue JWTs."""

from sqlalchemy.orm import Session

from app.core import config
from app.core.errors import AuthError, ValidationError
from app.core.security import create_token, hash_password, verify_password
from app.models import AdminUser, Table
from app.repositories import tables as table_repo


def admin_login(db: Session, store_id: str, username: str, password: str) -> AdminUser:
    admin = table_repo.get_admin(db, store_id, username)
    if admin is None or not verify_password(password, admin.password_hash):
        raise AuthError("매장ID/사용자명/비밀번호를 확인하세요.")
    return admin


def table_auth(db: Session, store_id: str, table_number: str, password: str) -> Table:
    table = table_repo.get_by_number(db, store_id, table_number)
    if table is None or not verify_password(password, table.password_hash):
        raise AuthError("테이블 정보 또는 비밀번호가 올바르지 않습니다.")
    return table


def change_admin_password(
    db: Session,
    store_id: str,
    username: str,
    current_password: str,
    new_password: str,
) -> AdminUser:
    """Change the authenticated admin's password after verifying the current one."""
    admin = table_repo.get_admin(db, store_id, username)
    if admin is None or not verify_password(current_password, admin.password_hash):
        raise AuthError("현재 비밀번호가 올바르지 않습니다.")
    if not new_password.strip():
        raise ValidationError("새 비밀번호가 비어 있습니다.")
    admin.password_hash = hash_password(new_password)
    db.commit()
    return admin


def admin_token(admin: AdminUser) -> str:
    return create_token(
        {"role": "admin", "store_id": admin.store_id, "username": admin.username}
    )


def table_token(table: Table) -> str:
    return create_token(
        {
            "role": "table",
            "store_id": table.store_id,
            "table_id": table.id,
            "table_number": table.table_number,
        }
    )


TOKEN_TTL_SECONDS = config.JWT_TTL_SECONDS
