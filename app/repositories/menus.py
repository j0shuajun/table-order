"""Category and menu queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Menu


def list_categories(db: Session, store_id: str) -> list[Category]:
    return list(
        db.execute(
            select(Category)
            .where(Category.store_id == store_id)
            .order_by(Category.display_order, Category.id)
        ).scalars()
    )


def list_menus(db: Session, store_id: str) -> list[Menu]:
    return list(
        db.execute(
            select(Menu)
            .where(Menu.store_id == store_id)
            .order_by(Menu.category_id, Menu.display_order, Menu.id)
        ).scalars()
    )


def get_menus_by_ids(
    db: Session, store_id: str, menu_ids: list[int]
) -> dict[int, Menu]:
    if not menu_ids:
        return {}
    rows = db.execute(
        select(Menu).where(Menu.store_id == store_id, Menu.id.in_(menu_ids))
    ).scalars()
    return {m.id: m for m in rows}


def get_menu(db: Session, store_id: str, menu_id: int) -> Menu | None:
    return db.execute(
        select(Menu).where(Menu.store_id == store_id, Menu.id == menu_id)
    ).scalar_one_or_none()


def get_category(db: Session, store_id: str, category_id: int) -> Category | None:
    return db.execute(
        select(Category).where(
            Category.store_id == store_id, Category.id == category_id
        )
    ).scalar_one_or_none()


def add_category(db: Session, category: Category) -> Category:
    db.add(category)
    db.flush()
    return category


def add_menu(db: Session, menu: Menu) -> Menu:
    db.add(menu)
    db.flush()
    return menu


def delete_menu(db: Session, menu: Menu) -> None:
    db.delete(menu)
    db.flush()
