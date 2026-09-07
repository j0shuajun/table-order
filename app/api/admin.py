"""Admin endpoints (role=admin): dashboard, orders, tables, menu management."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas import (
    AdminTablesResponse,
    CategoryCreateRequest,
    CategoryCreateResponse,
    CompleteSessionResponse,
    DeleteMenuResponse,
    DeleteOrderResponse,
    MenuCreateRequest,
    MenuListResponse,
    MenuMutationResponse,
    MenuUpdateRequest,
    StatusUpdateRequest,
    StatusUpdateResponse,
    TableConfigOut,
    TableConfigResponse,
    TableCreateRequest,
    TableCreateResponse,
    TableHistoryResponse,
    TableOrdersResponse,
    TablePasswordResetRequest,
    TablePasswordResetResponse,
)
from app.services import admin_service, menu_service, order_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/tables", response_model=AdminTablesResponse)
def tables(claims: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return admin_service.tables_summary(db, claims["store_id"])


@router.get("/tables/config", response_model=TableConfigResponse)
def tables_config(claims: dict = Depends(require_admin), db: Session = Depends(get_db)):
    tables = admin_service.list_table_config(db, claims["store_id"])
    return TableConfigResponse(
        tables=[
            TableConfigOut(
                table_id=t.id, table_number=t.table_number, created_at=t.created_at
            )
            for t in tables
        ]
    )


@router.post("/tables", response_model=TableCreateResponse, status_code=201)
def create_table(
    req: TableCreateRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    table = admin_service.create_table(
        db, claims["store_id"], req.table_number, req.password
    )
    return TableCreateResponse(table_id=table.id, table_number=table.table_number)


@router.put("/tables/{table_id}/password", response_model=TablePasswordResetResponse)
def reset_table_password(
    table_id: int,
    req: TablePasswordResetRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    table = admin_service.reset_table_password(
        db, claims["store_id"], table_id, req.password
    )
    return TablePasswordResetResponse(table_id=table.id)


@router.get("/tables/{table_id}/orders", response_model=TableOrdersResponse)
def table_orders(
    table_id: int,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.table_orders(db, claims["store_id"], table_id)


@router.get("/tables/{table_id}/history", response_model=TableHistoryResponse)
def table_history(
    table_id: int,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    sessions = admin_service.table_history(db, claims["store_id"], table_id, start, end)
    return TableHistoryResponse(table_id=table_id, sessions=sessions)


@router.post("/tables/{table_id}/complete", response_model=CompleteSessionResponse)
def complete_session(
    table_id: int,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    closed_id = admin_service.complete_session(db, claims["store_id"], table_id)
    return CompleteSessionResponse(
        table_id=table_id, closed_session_id=closed_id, current_total=0
    )


@router.post("/orders/{order_id}/status", response_model=StatusUpdateResponse)
def update_status(
    order_id: int,
    req: StatusUpdateRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = order_service.update_status(db, claims["store_id"], order_id, req.status)
    return StatusUpdateResponse(
        order_id=order.id, status=order.status, updated_at=order.updated_at
    )


@router.delete("/orders/{order_id}", response_model=DeleteOrderResponse)
def delete_order(
    order_id: int,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    table_id, current_total = order_service.delete_order(
        db, claims["store_id"], order_id
    )
    return DeleteOrderResponse(
        deleted_order_id=order_id, table_id=table_id, current_total=current_total
    )


# --- Menu management ----------------------------------------------------
@router.get("/menus", response_model=MenuListResponse)
def list_menus(claims: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return MenuListResponse(categories=menu_service.list_menu(db, claims["store_id"]))


@router.post("/categories", response_model=CategoryCreateResponse, status_code=201)
def create_category(
    req: CategoryCreateRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = menu_service.create_category(
        db, claims["store_id"], req.name, req.display_order
    )
    return CategoryCreateResponse(
        id=category.id, name=category.name, display_order=category.display_order
    )


@router.post("/menus", response_model=MenuMutationResponse, status_code=201)
def create_menu(
    req: MenuCreateRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _menu_mutation(menu_service.create_menu(db, claims["store_id"], req))


@router.put("/menus/{menu_id}", response_model=MenuMutationResponse)
def update_menu(
    menu_id: int,
    req: MenuUpdateRequest,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _menu_mutation(
        menu_service.update_menu(db, claims["store_id"], menu_id, req)
    )


@router.delete("/menus/{menu_id}", response_model=DeleteMenuResponse)
def delete_menu(
    menu_id: int,
    claims: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    deleted_id = menu_service.delete_menu(db, claims["store_id"], menu_id)
    return DeleteMenuResponse(deleted_menu_id=deleted_id)


def _menu_mutation(menu) -> MenuMutationResponse:
    return MenuMutationResponse(
        id=menu.id,
        name=menu.name,
        price=menu.price,
        category_id=menu.category_id,
        display_order=menu.display_order,
    )
