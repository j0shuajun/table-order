"""Order creation/lifecycle behavior: number format, totals, session, errors."""

import re
from datetime import datetime, timezone

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.schemas import OrderItemRequest
from app.services import order_service

# 2026-09-07 06:26 UTC == 2026-09-07 15:26 KST
FIXED_NOW = datetime(2026, 9, 7, 6, 26, 0, tzinfo=timezone.utc)


def _items(menu_id, qty=1):
    return [OrderItemRequest(menu_id=menu_id, quantity=qty)]


def test_create_order_uses_server_prices_and_totals(db, seeded_store):
    bulgogi, cola = seeded_store["menu_ids"]
    order = order_service.create_order(
        db,
        "store001",
        seeded_store["table_id"],
        [
            OrderItemRequest(menu_id=bulgogi, quantity=2),
            OrderItemRequest(menu_id=cola, quantity=1),
        ],
        now=FIXED_NOW,
    )
    assert order.total_amount == 12000 * 2 + 3000
    assert {i.line_total for i in order.items} == {24000, 3000}
    # snapshot name/price
    assert order.items[0].menu_name in {"불고기 정식", "콜라"}


def test_order_number_format_kst_and_sequence(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    o1 = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    o2 = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    assert re.fullmatch(r"\d{8}-\d{4}-\d{4}", o1.order_number)
    assert o1.order_number == "20260907-1526-0001"
    assert o2.order_number == "20260907-1526-0002"


def test_first_order_creates_active_session_and_reuses_it(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    o1 = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    o2 = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    assert o1.session_id == o2.session_id


def test_empty_items_rejected(db, seeded_store):
    with pytest.raises(ValidationError):
        order_service.create_order(
            db, "store001", seeded_store["table_id"], [], now=FIXED_NOW
        )


def test_unknown_menu_rejected(db, seeded_store):
    with pytest.raises(NotFoundError):
        order_service.create_order(
            db, "store001", seeded_store["table_id"], _items(999999), now=FIXED_NOW
        )


def test_get_current_returns_session_orders_and_total(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi, 2), now=FIXED_NOW
    )
    session, orders, total = order_service.get_current(
        db, "store001", seeded_store["table_id"]
    )
    assert session is not None
    assert len(orders) == 1
    assert total == 24000


def test_get_current_no_session(db, seeded_store):
    session, orders, total = order_service.get_current(
        db, "store001", seeded_store["table_id"]
    )
    assert session is None and orders == [] and total == 0


def test_update_status_validates_and_changes(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    order = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    updated = order_service.update_status(db, "store001", order.id, "preparing")
    assert updated.status == "preparing"
    with pytest.raises(ValidationError):
        order_service.update_status(db, "store001", order.id, "bogus")


def test_delete_order_recomputes_total(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    order = order_service.create_order(
        db, "store001", seeded_store["table_id"], _items(bulgogi), now=FIXED_NOW
    )
    table_id, current_total = order_service.delete_order(db, "store001", order.id)
    assert table_id == seeded_store["table_id"]
    assert current_total == 0
