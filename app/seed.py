"""Idempotent demo seed: store, admin, tables, categories, and menus.

Runs once at startup. If the demo store already exists, seeding is skipped so
restarts never duplicate data (R-SEED-1).
"""

from sqlalchemy.orm import Session

from app.core import config
from app.core.security import hash_password
from app.models import AdminUser, Category, Menu, Store, Table

# Menus served their own photo under /static/img. The old demo used this
# placeholder; backfill replaces only rows still pointing at it (below).
_LEGACY_IMG = "https://placehold.co/300x200?text=Menu"


def _img(filename: str) -> str:
    return f"/static/img/{filename}"


# category name -> list of (name, price, description, image filename)
_MENUS = {
    "메인": [
        ("불고기 정식", 12000, "간장 양념 불고기와 공깃밥", "bulgogi.jpg"),
        ("비빔밥", 9000, "제철 나물과 고추장", "bibimbap.jpg"),
        ("김치찌개", 8000, "묵은지와 돼지고기", "kimchi-jjigae.jpg"),
        ("된장찌개", 8000, "두부와 애호박", "doenjang-jjigae.jpg"),
        ("제육볶음", 10000, "매콤한 돼지고기 볶음", "jeyuk-bokkeum.jpg"),
    ],
    "사이드": [
        ("계란말이", 5000, "부드러운 계란말이", "gyeran-mari.jpg"),
        ("감자튀김", 4000, "바삭한 감자튀김", "gamja-twigim.jpg"),
        ("김치전", 6000, "바삭한 김치전", "kimchi-jeon.jpg"),
    ],
    "음료": [
        ("콜라", 3000, "시원한 콜라", "cola.jpg"),
        ("사이다", 3000, "시원한 사이다", "cider.jpg"),
    ],
}

# menu name -> image URL, used both for seeding and placeholder backfill.
_MENU_IMAGES = {
    name: _img(filename)
    for items in _MENUS.values()
    for (name, _price, _desc, filename) in items
}


def seed_if_empty(db: Session) -> bool:
    """Seed the demo store if absent. Returns True when seeding occurred."""
    store_id = config.DEFAULT_STORE_ID
    if db.get(Store, store_id) is not None:
        return False

    db.add(Store(store_id=store_id, name="데모 식당"))
    db.flush()

    db.add(
        AdminUser(
            store_id=store_id,
            username="admin",
            password_hash=hash_password("admin1234"),
        )
    )
    for i in range(1, 7):
        db.add(
            Table(
                store_id=store_id,
                table_number=f"T{i}",
                password_hash=hash_password("0000"),
            )
        )

    for order, (category_name, menus) in enumerate(_MENUS.items()):
        category = Category(store_id=store_id, name=category_name, display_order=order)
        db.add(category)
        db.flush()
        for display_order, (name, price, description, filename) in enumerate(menus):
            db.add(
                Menu(
                    store_id=store_id,
                    category_id=category.id,
                    name=name,
                    price=price,
                    description=description,
                    image_url=_img(filename),
                    display_order=display_order,
                )
            )

    db.commit()
    return True


def backfill_menu_images(db: Session) -> int:
    """Point existing demo menus at their photo, replacing the old placeholder.

    Only rows still holding the legacy placeholder (or an empty image) are
    touched, so any image a store admin set by hand is preserved. Returns the
    number of menus updated.
    """
    updated = 0
    menus = (
        db.query(Menu)
        .filter((Menu.image_url == _LEGACY_IMG) | (Menu.image_url.is_(None)))
        .all()
    )
    for menu in menus:
        image_url = _MENU_IMAGES.get(menu.name)
        if image_url is not None:
            menu.image_url = image_url
            updated += 1
    if updated:
        db.commit()
    return updated
