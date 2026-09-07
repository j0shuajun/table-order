"""Table and admin-user queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminUser, Table


def get_by_number(db: Session, store_id: str, table_number: str) -> Table | None:
    return db.execute(
        select(Table).where(
            Table.store_id == store_id, Table.table_number == table_number
        )
    ).scalar_one_or_none()


def get(db: Session, store_id: str, table_id: int) -> Table | None:
    return db.execute(
        select(Table).where(Table.store_id == store_id, Table.id == table_id)
    ).scalar_one_or_none()


def list_tables(db: Session, store_id: str) -> list[Table]:
    return list(
        db.execute(
            select(Table)
            .where(Table.store_id == store_id)
            .order_by(Table.table_number, Table.id)
        ).scalars()
    )


def add(db: Session, table: Table) -> Table:
    db.add(table)
    db.flush()
    return table


def get_admin(db: Session, store_id: str, username: str) -> AdminUser | None:
    return db.execute(
        select(AdminUser).where(
            AdminUser.store_id == store_id, AdminUser.username == username
        )
    ).scalar_one_or_none()
