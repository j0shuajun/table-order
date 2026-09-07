"""Shared pytest fixtures: an isolated in-memory SQLite session per test."""

import bcrypt
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models as models  # noqa: F401  (register models on Base.metadata)
from app.core.db import Base


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def seeded_store(db: Session):
    """A minimal store + one table + one category/menu for service tests."""
    store = models.Store(store_id="store001", name="데모 식당")
    db.add(store)
    db.flush()
    table = models.Table(
        store_id="store001",
        table_number="T1",
        password_hash=bcrypt.hashpw(b"0000", bcrypt.gensalt()).decode(),
    )
    category = models.Category(store_id="store001", name="메인", display_order=0)
    db.add_all([table, category])
    db.flush()
    menu = models.Menu(
        store_id="store001",
        category_id=category.id,
        name="불고기 정식",
        price=12000,
        display_order=0,
    )
    menu2 = models.Menu(
        store_id="store001",
        category_id=category.id,
        name="콜라",
        price=3000,
        display_order=1,
    )
    db.add_all([menu, menu2])
    db.commit()
    return {
        "store_id": "store001",
        "table_id": table.id,
        "menu_ids": [menu.id, menu2.id],
    }
