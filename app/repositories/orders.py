"""Order queries (create, per-session lookups, status/delete helpers)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Order


def add(db: Session, order: Order) -> Order:
    db.add(order)
    db.flush()
    return order


def get(db: Session, store_id: str, order_id: int) -> Order | None:
    return db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.store_id == store_id, Order.id == order_id)
    ).scalar_one_or_none()


def list_by_session(db: Session, session_id: int) -> list[Order]:
    return list(
        db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.session_id == session_id)
            .order_by(Order.created_at, Order.id)
        ).scalars()
    )


def delete(db: Session, order: Order) -> None:
    db.delete(order)
    db.flush()


def session_total(db: Session, session_id: int) -> int:
    return sum(o.total_amount for o in list_by_session(db, session_id))
