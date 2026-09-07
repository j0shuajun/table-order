"""Admin dashboard, session completion, and table management."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, ValidationError
from app.core.events import broker
from app.core.security import hash_password
from app.models import Table
from app.repositories import orders as order_repo
from app.repositories import sessions as session_repo
from app.repositories import tables as table_repo
from app.schemas import (
    AdminTablesResponse,
    HistorySessionOut,
    TableOrdersResponse,
    TableSummary,
)
from app.services import serializers

_LATEST_PREVIEW = 3


def tables_summary(db: Session, store_id: str) -> AdminTablesResponse:
    summaries: list[TableSummary] = []
    for table in table_repo.list_tables(db, store_id):
        session = session_repo.get_active(db, store_id, table.id)
        orders = order_repo.list_by_session(db, session.id) if session else []
        current_total = sum(o.total_amount for o in orders)
        latest = sorted(orders, key=lambda o: o.created_at, reverse=True)[
            :_LATEST_PREVIEW
        ]
        summaries.append(
            TableSummary(
                table_id=table.id,
                table_number=table.table_number,
                session_id=session.id if session else None,
                session_status=session.status if session else None,
                current_total=current_total,
                order_count=len(orders),
                latest_orders=[serializers.latest_preview(o) for o in latest],
            )
        )
    return AdminTablesResponse(tables=summaries)


def table_orders(db: Session, store_id: str, table_id: int) -> TableOrdersResponse:
    session = session_repo.get_active(db, store_id, table_id)
    orders = order_repo.list_by_session(db, session.id) if session else []
    return TableOrdersResponse(
        table_id=table_id,
        session_id=session.id if session else None,
        session_total=sum(o.total_amount for o in orders),
        orders=[serializers.admin_order_out(o) for o in orders],
    )


def table_history(
    db: Session,
    store_id: str,
    table_id: int,
    start: date | None = None,
    end: date | None = None,
) -> list[HistorySessionOut]:
    sessions = session_repo.list_closed(db, store_id, table_id)
    result: list[HistorySessionOut] = []
    for session in sessions:
        started: datetime = session.started_at
        if start and started.date() < start:
            continue
        if end and started.date() > end:
            continue
        orders = order_repo.list_by_session(db, session.id)
        result.append(
            HistorySessionOut(
                session_id=session.id,
                started_at=session.started_at,
                closed_at=session.closed_at,
                session_total=sum(o.total_amount for o in orders),
                orders=[serializers.admin_order_out(o) for o in orders],
            )
        )
    return result


def complete_session(db: Session, store_id: str, table_id: int) -> int:
    """Close the active session (R-SES-3). Returns the closed session id."""
    session = session_repo.get_active(db, store_id, table_id)
    if session is None:
        raise ConflictError("진행 중인 세션이 없습니다.")
    session_id = session.id
    session_repo.close(db, session)
    db.commit()
    broker.publish(
        "session_closed",
        {"table_id": table_id, "session_id": session_id, "current_total": 0},
    )
    return session_id


def list_table_config(db: Session, store_id: str) -> list[Table]:
    return table_repo.list_tables(db, store_id)


def create_table(db: Session, store_id: str, table_number: str, password: str) -> Table:
    if not table_number.strip():
        raise ValidationError("테이블 번호가 비어 있습니다.")
    if table_repo.get_by_number(db, store_id, table_number) is not None:
        raise ConflictError("이미 존재하는 테이블 번호입니다.")
    table = table_repo.add(
        db,
        Table(
            store_id=store_id,
            table_number=table_number,
            password_hash=hash_password(password),
        ),
    )
    db.commit()
    db.refresh(table)
    return table
