# Component Methods — 메서드 시그니처·입출력

/ Written at (KST): 2026-09-07 12:45 /

> 시그니처는 Python 힌트 스타일(개념). 상세 규칙은 business-rules.md의 R-* 참조. 반환 형태는 api-contract.md와 일치.

## AuthService
| 메서드 | 입력 | 출력 | 규칙 |
|---|---|---|---|
| `admin_login(store_id, username, password)` | str×3 | `{token, store_id, username, expires_in}` | R-AUTH-1 |
| `table_auth(store_id, table_number, password)` | str×3 | `{token, store_id, table_id, table_number, expires_in}` | R-AUTH-2 |

## MenuService
| 메서드 | 입력 | 출력 |
|---|---|---|
| `get_menu(store_id)` | str | `{categories:[{...,menus:[...]}]}` |

## OrderService
| 메서드 | 입력 | 출력 | 규칙 |
|---|---|---|---|
| `create_order(store_id, table_id, items)` | items:`[{menu_id,quantity}]` | 주문 상세(order_number, total, items...) | R-CRE, R-ORD, R-TOT-1, R-SES-1 |
| `get_current_orders(store_id, table_id)` | | `{session_id, orders[], session_total}` | R-SES-5, R-TOT-2 |
| `change_status(store_id, order_id, status)` | | `{order_id, status, updated_at}` | R-ST-1/2 |
| `delete_order(store_id, order_id)` | | `{deleted_order_id, table_id, current_total}` | R-DEL, R-TOT-2 |

## SessionService
| 메서드 | 입력 | 출력 | 규칙 |
|---|---|---|---|
| `get_or_create_active(store_id, table_id)` | | session | R-SES-1/2 |
| `complete_session(store_id, table_id)` | | `{table_id, closed_session_id, current_total}` | R-SES-3, R-TOT-4 |

## DashboardService
| 메서드 | 입력 | 출력 |
|---|---|---|
| `list_tables(store_id)` | | `{tables:[{table_id,table_number,session_status,current_total,order_count,latest_orders[≤3]}]}` |
| `table_detail(store_id, table_id)` | | active 세션 주문 상세 |
| `table_history(store_id, table_id, start?, end?)` | | closed 세션 목록(시간 역순, 날짜필터) |

## MenuAdminService
| 메서드 | 입력 | 출력 | 규칙 |
|---|---|---|---|
| `list_menus(store_id)` | | 카테고리별 메뉴 | |
| `create_category(store_id, name, display_order)` | | category | |
| `create_menu(store_id, payload)` | name,price,description,category_id,image_url,display_order | menu | R-MENU-1 |
| `update_menu(store_id, menu_id, payload)` | | menu | R-MENU-1/3 |
| `delete_menu(store_id, menu_id)` | | `{deleted_menu_id}` | R-MENU-2 |
| `create_table(store_id, table_number, password)` | | `{table_id, table_number}` | |
| `list_table_configs(store_id)` | | 테이블 목록 |

## core.security (의존성/헬퍼)
| 메서드 | 입력 | 출력 |
|---|---|---|
| `hash_password(raw)` / `verify_password(raw, hash)` | | str / bool |
| `create_token(claims)` / `decode_token(token)` | | JWT str / claims |
| `get_current_admin(Authorization header)` | | admin claims (401/403) |
| `get_current_table(Authorization header)` | | table claims (401/403) |

## core.EventBroker
| 메서드 | 입력 | 출력 |
|---|---|---|
| `subscribe(store_id) -> Queue` | | 관리자 연결용 asyncio 큐 |
| `unsubscribe(store_id, queue)` | | |
| `publish(store_id, event_type, data)` | | (구독 큐들에 전파) |

## Repositories (대표 메서드)
| 컴포넌트 | 메서드 |
|---|---|
| SessionRepository | `find_active(table_id)`, `create(table_id)`, `close(session_id)`, `list_closed(table_id, start?, end?)` |
| OrderRepository | `create(order, items)`, `by_session(session_id)`, `by_id(order_id)`, `delete(order_id)`, `update_status(order_id, status)`, `session_total(session_id)` |
| SequenceRepository | `next_seq(store_id, seq_date) -> int` (원자적 +1) |
| MenuRepository | `by_ids(ids)`, `list(store_id)`, `create/update/delete` |
