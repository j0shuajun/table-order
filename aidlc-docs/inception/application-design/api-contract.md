# API Contract — REST + SSE (BE/FE 공통 준수)

/ Written at (KST): 2026-09-07 12:20 /

> 이 계약이 **단일 진실 원천**입니다. 백엔드 응답과 프런트 호출은 반드시 이 규격을 따릅니다.
> - 서빙: **단일 FastAPI 서버**. 정적 프런트는 `/`(고객), `/admin`(관리자)로 서빙. API는 `/api/*`.
> - 인증(Q2=A): REST는 `Authorization: Bearer <JWT>` 헤더. **SSE만** `?token=<JWT>` 쿼리파라미터(EventSource가 헤더 불가).
> - 토큰: HS256 JWT. 클레임 `role`(`admin`|`table`), `store_id`, (admin) `username`, (table) `table_id`,`table_number`, `exp`(발급 16h). 프런트는 localStorage 저장, 자동 로그인.
> - 금액: 정수(원). 시간: 응답은 ISO 8601 UTC 문자열.
> - 에러(Q6=A): `{ "detail": "메시지" }` + HTTP status. 관례: 400 검증실패 / 401 미인증·만료 / 403 권한불일치 / 404 없음 / 409 상태충돌.

---

## 1. 인증 (Auth)

### POST /api/admin/login
관리자 로그인. **인증 불필요**.
```json
// req
{ "store_id": "store001", "username": "admin", "password": "admin1234" }
// 200
{ "token": "<JWT>", "store_id": "store001", "username": "admin", "expires_in": 57600 }
// 401 { "detail": "매장ID/사용자명/비밀번호를 확인하세요." }
```

### POST /api/table/auth
테이블 태블릿 인증(관리자 초기 설정 시 1회 입력 → 이후 태블릿이 저장된 정보로 자동 재호출). **인증 불필요**.
```json
// req
{ "store_id": "store001", "table_number": "T1", "password": "0000" }
// 200
{ "token": "<JWT>", "store_id": "store001", "table_id": 1, "table_number": "T1", "expires_in": 57600 }
// 401 { "detail": "테이블 정보 또는 비밀번호가 올바르지 않습니다." }
```

---

## 2. 고객용 (role=`table` 필요)

### GET /api/menu
카테고리별 메뉴 조회(고객 메뉴 화면 기본 데이터).
```json
// 200
{
  "categories": [
    { "id": 1, "name": "메인", "display_order": 0,
      "menus": [
        { "id": 10, "name": "불고기 정식", "price": 12000,
          "description": "...", "image_url": "https://.../a.jpg", "display_order": 0 }
      ] }
  ]
}
```

### POST /api/orders
주문 생성. **가격은 서버가 DB에서 재계산**(클라이언트 가격 신뢰하지 않음). 세션 자동 시작/연결.
```json
// req  (수량 ≥ 1)
{ "items": [ { "menu_id": 10, "quantity": 2 }, { "menu_id": 21, "quantity": 1 } ] }
// 201
{
  "order_number": "20260907-1526-0001",
  "order_id": 100,
  "session_id": 5,
  "status": "pending",
  "total_amount": 27000,
  "created_at": "2026-09-07T06:26:00Z",
  "items": [
    { "menu_id": 10, "menu_name": "불고기 정식", "unit_price": 12000, "quantity": 2, "line_total": 24000 },
    { "menu_id": 21, "menu_name": "콜라", "unit_price": 3000, "quantity": 1, "line_total": 3000 }
  ]
}
// 400 { "detail": "주문 항목이 비어 있습니다." } | 404 { "detail": "존재하지 않는 메뉴가 포함되어 있습니다." }
```

### GET /api/orders/current
**현재(active) 세션**의 주문만 시간순 반환(과거 세션 제외).
```json
// 200
{
  "session_id": 5,
  "orders": [
    { "order_number": "20260907-1526-0001", "status": "pending", "total_amount": 27000,
      "created_at": "2026-09-07T06:26:00Z",
      "items": [ { "menu_name": "불고기 정식", "unit_price": 12000, "quantity": 2, "line_total": 24000 } ] }
  ],
  "session_total": 27000
}
// active 세션 없으면: { "session_id": null, "orders": [], "session_total": 0 }
```

---

## 3. 관리자용 (role=`admin` 필요)

### GET /api/admin/tables
대시보드용 테이블별 요약(active 세션 기준). 최신 주문 **3개** 미리보기.
```json
// 200
{
  "tables": [
    { "table_id": 1, "table_number": "T1", "session_id": 5, "session_status": "active",
      "current_total": 27000, "order_count": 1,
      "latest_orders": [
        { "order_number": "20260907-1526-0001", "status": "pending", "total_amount": 27000,
          "created_at": "2026-09-07T06:26:00Z" }
      ] },
    { "table_id": 2, "table_number": "T2", "session_id": null, "session_status": null,
      "current_total": 0, "order_count": 0, "latest_orders": [] }
  ]
}
```

### GET /api/admin/tables/{table_id}/orders
해당 테이블 **active 세션** 주문 상세 전체(카드 클릭 시).
```json
// 200
{ "table_id": 1, "session_id": 5, "session_total": 27000,
  "orders": [ { "order_id": 100, "order_number": "...", "status": "pending",
    "total_amount": 27000, "created_at": "...",
    "items": [ { "menu_name": "불고기 정식", "unit_price": 12000, "quantity": 2, "line_total": 24000 } ] } ] }
```

### GET /api/admin/tables/{table_id}/history?start=YYYY-MM-DD&end=YYYY-MM-DD
**closed 세션** 과거 내역(시간 역순, 날짜 필터 옵션, 기본 최근).
```json
// 200
{ "table_id": 1,
  "sessions": [
    { "session_id": 4, "started_at": "...", "closed_at": "...", "session_total": 45000,
      "orders": [ { "order_number": "...", "status": "completed", "total_amount": 45000,
        "created_at": "...", "items": [ ... ] } ] }
  ] }
```

### POST /api/admin/orders/{order_id}/status
주문 상태 변경. `pending`|`preparing`|`completed`.
```json
// req { "status": "preparing" }
// 200 { "order_id": 100, "status": "preparing", "updated_at": "..." }
// 400 { "detail": "허용되지 않은 상태값입니다." }
```

### DELETE /api/admin/orders/{order_id}
직권 주문 삭제(확인 팝업은 FE). 삭제 후 테이블 총액은 재계산됨.
```json
// 200 { "deleted_order_id": 100, "table_id": 1, "current_total": 0 }
```

### POST /api/admin/tables/{table_id}/complete
"이용 완료" — active 세션을 `closed` 처리(현재 주문은 과거 내역으로 논리 이동, 현재 총액 0).
```json
// 200 { "table_id": 1, "closed_session_id": 5, "current_total": 0 }
// 409 { "detail": "진행 중인 세션이 없습니다." }
```

### 테이블 관리(초기 설정)
- **GET /api/admin/tables/config** — 등록된 테이블 목록(번호·생성일)
- **POST /api/admin/tables** — 테이블 생성/등록 `{ "table_number": "T7", "password": "0000" }` → 201 `{ "table_id": 7, "table_number": "T7" }`
  - (시드로 T1~T6 존재. 초기 설정은 이 등록 + `/api/table/auth`로 태블릿 토큰 발급 흐름으로 충족.)

### 메뉴 관리 (ADMIN-4)
- **GET /api/admin/menus** — 카테고리별 전체(노출순).
- **POST /api/admin/categories** `{ "name": "디저트", "display_order": 3 }` → 201
- **POST /api/admin/menus** `{ "name","price","description","category_id","image_url","display_order" }` → 201
  - 검증: name 비어있지 않음, price 정수 ≥ 0, category_id 존재. 위반 시 400.
- **PUT /api/admin/menus/{id}** — 부분/전체 수정(노출순 포함). → 200
- **DELETE /api/admin/menus/{id}** — 삭제. → 200 `{ "deleted_menu_id": 10 }`

---

## 4. 실시간 SSE (role=`admin`)

### GET /api/admin/stream?token=<JWT>
관리자당 **단일 스트림**(Q4=A). 매장 전체 주문 이벤트를 수신. `Content-Type: text/event-stream`.

이벤트 종류와 payload:
```
event: order_created
data: {"table_id":1,"order":{"order_id":100,"order_number":"...","status":"pending","total_amount":27000,"created_at":"...","items":[...]},"current_total":27000}

event: order_updated
data: {"table_id":1,"order_id":100,"status":"preparing","updated_at":"..."}

event: order_deleted
data: {"table_id":1,"order_id":100,"current_total":0}

event: session_closed
data: {"table_id":1,"session_id":5,"current_total":0}
```
- 목표: 신규 주문 발생 후 **2초 이내** 대시보드 반영.
- 재연결: EventSource 기본 자동 재연결에 의존(MVP 기본 수준). 서버는 주기적 `: keep-alive` 주석 라인 전송 가능.
- FE 동작: `order_created`는 신규 강조(색상+애니메이션, 약 30초). 나머지는 카드/상세 갱신.

---

## 5. 정적 서빙 (프런트)
| 경로 | 내용 |
|---|---|
| `GET /` | 고객 앱(메뉴/카트/주문/내역) |
| `GET /admin` | 관리자 앱(로그인/대시보드/테이블·메뉴 관리) |
| `GET /static/*` | JS/CSS/이미지(placeholder 포함) |
