"""Customer endpoints (role=table): menu, order creation, current orders."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_table
from app.schemas import (
    CurrentOrdersResponse,
    MenuListResponse,
    OrderCreateRequest,
    OrderCreateResponse,
)
from app.services import menu_service, order_service, serializers

router = APIRouter(prefix="/api", tags=["customer"])


@router.get("/menu", response_model=MenuListResponse)
def get_menu(claims: dict = Depends(require_table), db: Session = Depends(get_db)):
    return MenuListResponse(categories=menu_service.list_menu(db, claims["store_id"]))


@router.post("/orders", response_model=OrderCreateResponse, status_code=201)
def create_order(
    req: OrderCreateRequest,
    claims: dict = Depends(require_table),
    db: Session = Depends(get_db),
):
    order = order_service.create_order(
        db, claims["store_id"], claims["table_id"], req.items
    )
    return OrderCreateResponse(
        order_number=order.order_number,
        order_id=order.id,
        session_id=order.session_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[serializers.item_out(i) for i in order.items],
    )


@router.get("/orders/current", response_model=CurrentOrdersResponse)
def current_orders(
    claims: dict = Depends(require_table), db: Session = Depends(get_db)
):
    session, orders, total = order_service.get_current(
        db, claims["store_id"], claims["table_id"]
    )
    return CurrentOrdersResponse(
        session_id=session.id if session else None,
        orders=[serializers.current_order_out(o) for o in orders],
        session_total=total,
    )
