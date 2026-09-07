"""Dashboard summary, session completion, and menu management."""

from datetime import datetime, timezone

import pytest

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.schemas import MenuCreateRequest, MenuUpdateRequest, OrderItemRequest
from app.services import admin_service, auth_service, menu_service, order_service

FIXED_NOW = datetime(2026, 9, 7, 6, 26, 0, tzinfo=timezone.utc)


def test_tables_summary_reflects_active_orders(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    order_service.create_order(
        db,
        "store001",
        seeded_store["table_id"],
        [OrderItemRequest(menu_id=bulgogi, quantity=2)],
        now=FIXED_NOW,
    )
    resp = admin_service.tables_summary(db, "store001")
    active = [t for t in resp.tables if t.table_id == seeded_store["table_id"]][0]
    assert active.current_total == 24000
    assert active.order_count == 1
    assert active.session_status == "active"
    assert len(active.latest_orders) == 1


def test_complete_session_closes_and_resets(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    order_service.create_order(
        db,
        "store001",
        seeded_store["table_id"],
        [OrderItemRequest(menu_id=bulgogi, quantity=1)],
        now=FIXED_NOW,
    )
    admin_service.complete_session(db, "store001", seeded_store["table_id"])
    resp = admin_service.table_orders(db, "store001", seeded_store["table_id"])
    assert resp.session_id is None and resp.session_total == 0
    # closed session appears in history
    history = admin_service.table_history(db, "store001", seeded_store["table_id"])
    assert len(history) == 1


def test_complete_session_without_active_conflicts(db, seeded_store):
    with pytest.raises(ConflictError):
        admin_service.complete_session(db, "store001", seeded_store["table_id"])


def test_new_order_after_complete_starts_new_session(db, seeded_store):
    bulgogi = seeded_store["menu_ids"][0]
    o1 = order_service.create_order(
        db,
        "store001",
        seeded_store["table_id"],
        [OrderItemRequest(menu_id=bulgogi, quantity=1)],
        now=FIXED_NOW,
    )
    admin_service.complete_session(db, "store001", seeded_store["table_id"])
    o2 = order_service.create_order(
        db,
        "store001",
        seeded_store["table_id"],
        [OrderItemRequest(menu_id=bulgogi, quantity=1)],
        now=FIXED_NOW,
    )
    assert o1.session_id != o2.session_id


def test_create_menu_validation(db, seeded_store):
    with pytest.raises(ValidationError):
        menu_service.create_menu(
            db,
            "store001",
            MenuCreateRequest(name="", price=1000, category_id=1),
        )
    with pytest.raises(ValidationError):
        menu_service.create_menu(
            db,
            "store001",
            MenuCreateRequest(name="테스트", price=1000, category_id=999999),
        )


def test_menu_crud_roundtrip(db, seeded_store):
    categories = menu_service.list_menu(db, "store001")
    category_id = categories[0].id
    created = menu_service.create_menu(
        db,
        "store001",
        MenuCreateRequest(name="된장찌개", price=9000, category_id=category_id),
    )
    updated = menu_service.update_menu(
        db, "store001", created.id, MenuUpdateRequest(price=9500)
    )
    assert updated.price == 9500 and updated.name == "된장찌개"
    deleted_id = menu_service.delete_menu(db, "store001", created.id)
    assert deleted_id == created.id
    with pytest.raises(NotFoundError):
        menu_service.update_menu(db, "store001", created.id, MenuUpdateRequest(price=1))


def test_create_table_duplicate_conflicts(db, seeded_store):
    admin_service.create_table(db, "store001", "T9", "0000")
    with pytest.raises(ConflictError):
        admin_service.create_table(db, "store001", "T9", "0000")


def test_reset_table_password_allows_new_auth(db, seeded_store):
    table_id = seeded_store["table_id"]
    admin_service.reset_table_password(db, "store001", table_id, "9999")
    # New password authenticates; old one no longer works.
    assert auth_service.table_auth(db, "store001", "T1", "9999").id == table_id
    with pytest.raises(Exception):
        auth_service.table_auth(db, "store001", "T1", "0000")


def test_reset_table_password_rejects_empty(db, seeded_store):
    with pytest.raises(ValidationError):
        admin_service.reset_table_password(
            db, "store001", seeded_store["table_id"], "  "
        )


def test_reset_table_password_missing_table(db, seeded_store):
    with pytest.raises(NotFoundError):
        admin_service.reset_table_password(db, "store001", 999999, "9999")
