"""Per-store, per-day order sequence with atomic increment."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OrderSequence


def next_seq(db: Session, store_id: str, seq_date: str) -> int:
    """Increment and return the next sequence for (store_id, seq_date).

    Runs inside the caller's transaction; SQLite serializes writes so the
    read-modify-write cannot interleave with another order creation.
    """
    row = db.execute(
        select(OrderSequence)
        .where(OrderSequence.store_id == store_id, OrderSequence.seq_date == seq_date)
        .with_for_update()
    ).scalar_one_or_none()
    if row is None:
        row = OrderSequence(store_id=store_id, seq_date=seq_date, last_seq=0)
        db.add(row)
        db.flush()
    row.last_seq += 1
    db.flush()
    return row.last_seq
