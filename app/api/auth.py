"""Authentication endpoints (no auth required)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    TableAuthRequest,
    TableAuthResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = auth_service.admin_login(db, req.store_id, req.username, req.password)
    return AdminLoginResponse(
        token=auth_service.admin_token(admin),
        store_id=admin.store_id,
        username=admin.username,
        expires_in=auth_service.TOKEN_TTL_SECONDS,
    )


@router.post("/table/auth", response_model=TableAuthResponse)
def table_auth(req: TableAuthRequest, db: Session = Depends(get_db)):
    table = auth_service.table_auth(db, req.store_id, req.table_number, req.password)
    return TableAuthResponse(
        token=auth_service.table_token(table),
        store_id=table.store_id,
        table_id=table.id,
        table_number=table.table_number,
        expires_in=auth_service.TOKEN_TTL_SECONDS,
    )
