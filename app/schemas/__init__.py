"""Pydantic request/response schemas mirroring api-contract.md.

Datetimes are serialized as ISO 8601 UTC with a trailing ``Z`` to match the
contract. SQLite returns naive datetimes on read-back, so we assume UTC when
tzinfo is missing.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, Field, PlainSerializer


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcDateTime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]


# --- Auth ---------------------------------------------------------------
class AdminLoginRequest(BaseModel):
    store_id: str
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    store_id: str
    username: str
    expires_in: int


class TableAuthRequest(BaseModel):
    store_id: str
    table_number: str
    password: str


class TableAuthResponse(BaseModel):
    token: str
    store_id: str
    table_id: int
    table_number: str
    expires_in: int


# --- Menu (customer) ----------------------------------------------------
class MenuOut(BaseModel):
    id: int
    name: str
    price: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int


class CategoryOut(BaseModel):
    id: int
    name: str
    display_order: int
    menus: list[MenuOut]


class MenuListResponse(BaseModel):
    categories: list[CategoryOut]


# --- Orders (customer) --------------------------------------------------
class OrderItemRequest(BaseModel):
    menu_id: int
    quantity: int = Field(ge=1)


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest]


class OrderItemOut(BaseModel):
    menu_id: Optional[int] = None
    menu_name: str
    unit_price: int
    quantity: int
    line_total: int


class OrderCreateResponse(BaseModel):
    order_number: str
    order_id: int
    session_id: int
    status: str
    total_amount: int
    created_at: UtcDateTime
    items: list[OrderItemOut]


class CurrentOrderOut(BaseModel):
    order_number: str
    status: str
    total_amount: int
    created_at: UtcDateTime
    items: list[OrderItemOut]


class CurrentOrdersResponse(BaseModel):
    session_id: Optional[int] = None
    orders: list[CurrentOrderOut]
    session_total: int


# --- Admin dashboard ----------------------------------------------------
class LatestOrderPreview(BaseModel):
    order_number: str
    status: str
    total_amount: int
    created_at: UtcDateTime


class TableSummary(BaseModel):
    table_id: int
    table_number: str
    session_id: Optional[int] = None
    session_status: Optional[str] = None
    current_total: int
    order_count: int
    latest_orders: list[LatestOrderPreview]


class AdminTablesResponse(BaseModel):
    tables: list[TableSummary]


class AdminOrderOut(BaseModel):
    order_id: int
    order_number: str
    status: str
    total_amount: int
    created_at: UtcDateTime
    items: list[OrderItemOut]


class TableOrdersResponse(BaseModel):
    table_id: int
    session_id: Optional[int] = None
    session_total: int
    orders: list[AdminOrderOut]


class HistorySessionOut(BaseModel):
    session_id: int
    started_at: UtcDateTime
    closed_at: Optional[UtcDateTime] = None
    session_total: int
    orders: list[AdminOrderOut]


class TableHistoryResponse(BaseModel):
    table_id: int
    sessions: list[HistorySessionOut]


class StatusUpdateRequest(BaseModel):
    status: str


class StatusUpdateResponse(BaseModel):
    order_id: int
    status: str
    updated_at: UtcDateTime


class DeleteOrderResponse(BaseModel):
    deleted_order_id: int
    table_id: int
    current_total: int


class CompleteSessionResponse(BaseModel):
    table_id: int
    closed_session_id: int
    current_total: int


# --- Table management ---------------------------------------------------
class TableConfigOut(BaseModel):
    table_id: int
    table_number: str
    created_at: UtcDateTime


class TableConfigResponse(BaseModel):
    tables: list[TableConfigOut]


class TableCreateRequest(BaseModel):
    table_number: str
    password: str


class TableCreateResponse(BaseModel):
    table_id: int
    table_number: str


# --- Menu management (admin) --------------------------------------------
class CategoryCreateRequest(BaseModel):
    name: str
    display_order: int = 0


class CategoryCreateResponse(BaseModel):
    id: int
    name: str
    display_order: int


class MenuCreateRequest(BaseModel):
    name: str
    price: int
    category_id: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0


class MenuUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None


class MenuMutationResponse(BaseModel):
    id: int
    name: str
    price: int
    category_id: int
    display_order: int


class DeleteMenuResponse(BaseModel):
    deleted_menu_id: int
