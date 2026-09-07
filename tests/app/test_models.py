"""Smoke tests: schema creation, cascade delete, and datetime serialization."""

import app.models as models
from app.schemas import OrderCreateResponse


def test_seeded_store_roundtrip(db, seeded_store):
    store = db.get(models.Store, "store001")
    assert store is not None and store.name == "데모 식당"
    menus = db.query(models.Menu).all()
    assert {m.name for m in menus} == {"불고기 정식", "콜라"}


def test_order_items_cascade_on_order_delete(db, seeded_store):
    session = models.TableSession(
        store_id="store001", table_id=seeded_store["table_id"]
    )
    db.add(session)
    db.flush()
    order = models.Order(
        order_number="20260907-1526-0001",
        store_id="store001",
        table_id=seeded_store["table_id"],
        session_id=session.id,
        total_amount=12000,
    )
    order.items.append(
        models.OrderItem(
            menu_id=seeded_store["menu_ids"][0],
            menu_name="불고기 정식",
            unit_price=12000,
            quantity=1,
            line_total=12000,
        )
    )
    db.add(order)
    db.commit()

    db.delete(order)
    db.commit()
    assert db.query(models.OrderItem).count() == 0


def test_datetime_serialized_as_utc_z():
    from datetime import datetime, timezone

    payload = OrderCreateResponse(
        order_number="20260907-1526-0001",
        order_id=1,
        session_id=1,
        status="pending",
        total_amount=0,
        created_at=datetime(2026, 9, 7, 6, 26, 0, tzinfo=timezone.utc),
        items=[],
    )
    dumped = payload.model_dump()
    assert dumped["created_at"] == "2026-09-07T06:26:00Z"
