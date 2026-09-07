"""Table session queries (active-session lookup, create, close)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TableSession


def get_active(db: Session, store_id: str, table_id: int) -> TableSession | None:
    return db.execute(
        select(TableSession).where(
            TableSession.store_id == store_id,
            TableSession.table_id == table_id,
            TableSession.status == "active",
        )
    ).scalar_one_or_none()


def create(db: Session, store_id: str, table_id: int) -> TableSession:
    session = TableSession(store_id=store_id, table_id=table_id, status="active")
    db.add(session)
    db.flush()
    return session


def close(db: Session, session: TableSession) -> None:
    session.status = "closed"
    session.closed_at = datetime.now(timezone.utc)
    db.flush()


def list_closed(db: Session, store_id: str, table_id: int) -> list[TableSession]:
    return list(
        db.execute(
            select(TableSession)
            .where(
                TableSession.store_id == store_id,
                TableSession.table_id == table_id,
                TableSession.status == "closed",
            )
            .order_by(TableSession.started_at.desc())
        ).scalars()
    )
