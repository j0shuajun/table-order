"""Order creation, retrieval, status change, and deletion.

Prices are authoritative from the DB (client prices are ignored). Order
creation ties into the table's active session (creating one on first order),
assigns a per-store/day order number, and publishes an SSE event after commit.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core import config
from app.core.errors import NotFoundError, ValidationError
from app.core.events import broker
from app.models import Order, OrderItem
from app.repositories import menus as menu_repo
from app.repositories import orders as order_repo
from app.repositories import sequences as seq_repo
from app.repositories import sessions as session_repo
from app.schemas import OrderItemRequest
from app.services import serializers

_KST = ZoneInfo(config.ORDER_NUMBER_TZ)

_ALLOWED_STATUSES = {"pending", "preparing", "completed"}


def create_order(
    db: Session,
    store_id: str,
    table_id: int,
    items: list[OrderItemRequest],
    now: datetime | None = None,
) -> Order:
    """Create an order in the table's active session (R-SES-1, R-ORD, R-TOT-1)."""
    if not items:
        raise ValidationError("주문 항목이 비어 있습니다.")

    now = now or datetime.now(timezone.utc)
    menu_map = menu_repo.get_menus_by_ids(
        db, store_id, [item.menu_id for item in items]
    )
    missing = [item.menu_id for item in items if item.menu_id not in menu_map]
    if missing:
        raise NotFoundError("존재하지 않는 메뉴가 포함되어 있습니다.")

    session = session_repo.get_active(db, store_id, table_id) or session_repo.create(
        db, store_id, table_id
    )

    kst = now.astimezone(_KST)
    seq = seq_repo.next_seq(db, store_id, kst.strftime("%Y%m%d"))
    order_number = f"{kst.strftime('%Y%m%d')}-{kst.strftime('%H%M')}-{seq:04d}"

    order = Order(
        order_number=order_number,
        store_id=store_id,
        table_id=table_id,
        session_id=session.id,
        status="pending",
        total_amount=0,
        created_at=now,
        updated_at=now,
    )
    total = 0
    for item in items:
        menu = menu_map[item.menu_id]
        line_total = menu.price * item.quantity
        total += line_total
        order.items.append(
            OrderItem(
                menu_id=menu.id,
                menu_name=menu.name,
                unit_price=menu.price,
                quantity=item.quantity,
                line_total=line_total,
            )
        )
    order.total_amount = total
    order_repo.add(db, order)
    db.commit()
    db.refresh(order)

    current_total = order_repo.session_total(db, session.id)
    broker.publish(
        "order_created",
        {
            "table_id": table_id,
            "order": serializers.admin_order_out(order).model_dump(),
            "current_total": current_total,
        },
    )
    return order


def get_current(db: Session, store_id: str, table_id: int):
    """Active-session orders (time order) with the running session total."""
    session = session_repo.get_active(db, store_id, table_id)
    if session is None:
        return None, [], 0
    orders = order_repo.list_by_session(db, session.id)
    total = sum(o.total_amount for o in orders)
    return session, orders, total


def update_status(db: Session, store_id: str, order_id: int, status: str) -> Order:
    if status not in _ALLOWED_STATUSES:
        raise ValidationError("허용되지 않은 상태값입니다.")
    order = order_repo.get(db, store_id, order_id)
    if order is None:
        raise NotFoundError("주문을 찾을 수 없습니다.")
    order.status = status
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    broker.publish(
        "order_updated",
        {
            "table_id": order.table_id,
            "order_id": order.id,
            "status": order.status,
            "updated_at": _iso(order.updated_at),
        },
    )
    return order


def delete_order(db: Session, store_id: str, order_id: int) -> tuple[int, int]:
    """Delete an order (items cascade). Returns (table_id, current_total)."""
    order = order_repo.get(db, store_id, order_id)
    if order is None:
        raise NotFoundError("주문을 찾을 수 없습니다.")
    table_id = order.table_id
    session_id = order.session_id
    order_repo.delete(db, order)
    db.commit()
    current_total = order_repo.session_total(db, session_id)
    broker.publish(
        "order_deleted",
        {"table_id": table_id, "order_id": order_id, "current_total": current_total},
    )
    return table_id, current_total


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
