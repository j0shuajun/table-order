"""Convert ORM entities into the Pydantic response schemas from api-contract.

Shared by services (for SSE payloads) and routers (for HTTP responses) so a
single mapping defines the wire shape.
"""

from app.models import Order, OrderItem
from app.schemas import (
    AdminOrderOut,
    CurrentOrderOut,
    LatestOrderPreview,
    OrderItemOut,
)


def item_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        menu_id=item.menu_id,
        menu_name=item.menu_name,
        unit_price=item.unit_price,
        quantity=item.quantity,
        line_total=item.line_total,
    )


def admin_order_out(order: Order) -> AdminOrderOut:
    return AdminOrderOut(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[item_out(i) for i in order.items],
    )


def current_order_out(order: Order) -> CurrentOrderOut:
    return CurrentOrderOut(
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[item_out(i) for i in order.items],
    )


def latest_preview(order: Order) -> LatestOrderPreview:
    return LatestOrderPreview(
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
    )
