"""Menu browsing (customer) and menu/category management (admin)."""

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models import Category, Menu
from app.repositories import menus as menu_repo
from app.schemas import (
    CategoryOut,
    MenuCreateRequest,
    MenuOut,
    MenuUpdateRequest,
)


def list_menu(db: Session, store_id: str) -> list[CategoryOut]:
    """Category-grouped menu for the customer screen (display order)."""
    categories = menu_repo.list_categories(db, store_id)
    menus = menu_repo.list_menus(db, store_id)
    by_category: dict[int, list[MenuOut]] = {}
    for m in menus:
        by_category.setdefault(m.category_id, []).append(
            MenuOut(
                id=m.id,
                name=m.name,
                price=m.price,
                description=m.description,
                image_url=m.image_url,
                display_order=m.display_order,
            )
        )
    return [
        CategoryOut(
            id=c.id,
            name=c.name,
            display_order=c.display_order,
            menus=by_category.get(c.id, []),
        )
        for c in categories
    ]


def create_category(
    db: Session, store_id: str, name: str, display_order: int
) -> Category:
    if not name.strip():
        raise ValidationError("카테고리 이름이 비어 있습니다.")
    category = menu_repo.add_category(
        db, Category(store_id=store_id, name=name, display_order=display_order)
    )
    db.commit()
    db.refresh(category)
    return category


def create_menu(db: Session, store_id: str, req: MenuCreateRequest) -> Menu:
    _validate_menu_fields(db, store_id, req.name, req.price, req.category_id)
    menu = menu_repo.add_menu(
        db,
        Menu(
            store_id=store_id,
            category_id=req.category_id,
            name=req.name,
            price=req.price,
            description=req.description,
            image_url=req.image_url,
            display_order=req.display_order,
        ),
    )
    db.commit()
    db.refresh(menu)
    return menu


def update_menu(
    db: Session, store_id: str, menu_id: int, req: MenuUpdateRequest
) -> Menu:
    menu = menu_repo.get_menu(db, store_id, menu_id)
    if menu is None:
        raise NotFoundError("메뉴를 찾을 수 없습니다.")
    name = req.name if req.name is not None else menu.name
    price = req.price if req.price is not None else menu.price
    category_id = req.category_id if req.category_id is not None else menu.category_id
    _validate_menu_fields(db, store_id, name, price, category_id)
    menu.name = name
    menu.price = price
    menu.category_id = category_id
    if req.description is not None:
        menu.description = req.description
    if req.image_url is not None:
        menu.image_url = req.image_url
    if req.display_order is not None:
        menu.display_order = req.display_order
    db.commit()
    db.refresh(menu)
    return menu


def delete_menu(db: Session, store_id: str, menu_id: int) -> int:
    menu = menu_repo.get_menu(db, store_id, menu_id)
    if menu is None:
        raise NotFoundError("메뉴를 찾을 수 없습니다.")
    menu_repo.delete_menu(db, menu)
    db.commit()
    return menu_id


def _validate_menu_fields(
    db: Session, store_id: str, name: str, price: int, category_id: int
) -> None:
    if not name or not name.strip():
        raise ValidationError("메뉴 이름이 비어 있습니다.")
    if price < 0:
        raise ValidationError("가격은 0 이상의 정수여야 합니다.")
    if menu_repo.get_category(db, store_id, category_id) is None:
        raise ValidationError("존재하지 않는 카테고리입니다.")
