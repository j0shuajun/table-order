# Unit of Work — 요구사항→유닛 매핑 (Story Map)

/ Written at (KST): 2026-09-07 13:29 /

> User Stories 단계는 생략되었으므로(요구사항이 이미 상세), **요구사항 ID(CUST-*/ADMIN-*)를 스토리 대체**로 사용해 유닛에 매핑한다.
> 대부분 요구사항은 U1(백엔드 로직/API)과 U2(화면)에 **함께** 걸친다 — 아래 표는 각 유닛이 맡는 부분을 구분한다.

| 요구사항 | U1 Backend (API·규칙) | U2 Frontend (화면) |
|---|---|---|
| CUST-1 자동 로그인/세션 | `POST /api/table/auth`, JWT(role=table) 발급·검증 | 최초 설정 입력 UI, 토큰 localStorage 저장·자동 로그인 |
| CUST-2 메뉴 조회 | `GET /api/menu` | 카테고리별 카드 레이아웃, 이미지 placeholder, 터치 UI |
| CUST-3 장바구니 | (해당 없음 — 서버 미저장) | localStorage 카트, 수량 증감·총액·비우기 |
| CUST-4 주문 생성 | `POST /api/orders`(가격확정·번호·세션·총액·SSE) | 최종확인→확정, 번호 표시→~5초 후 메뉴 복귀, 실패 시 유지 |
| CUST-5 현재세션 내역 | `GET /api/orders/current` | 시간순 목록·상태 표시 |
| ADMIN-1 인증 | `POST /api/admin/login`, JWT 16h, bcrypt | 로그인 화면, 토큰 유지·16h 만료 |
| ADMIN-2 실시간 모니터링 | `GET /api/admin/tables`, `GET /api/admin/stream`(SSE), 상태변경 API | 테이블 카드 그리드, 최신3 미리보기, 신규강조(~30s), 필터, 상세 |
| ADMIN-3 테이블 관리 | 테이블 등록, `DELETE order`(재계산), `complete`(세션종료), `history`(날짜필터) | 초기설정 UI, 삭제 확인팝업, 이용완료 버튼, 과거내역 화면 |
| ADMIN-4 메뉴 관리 | categories/menus CRUD + 검증(R-MENU) | 메뉴 관리 화면(등록/수정/삭제/노출순) |
| 도메인(세션/상태/이력) | table_sessions 상태머신, orders.status, closed 논리 이력 | 현재/과거 구분 표시 |

## 커버리지 확인
- 모든 요구사항(CUST-1~5, ADMIN-1~4, 도메인 개념)이 **U1 또는 U2(대개 둘 다)** 에 배정됨 — 누락 없음.
- U1 완료 시 API/규칙 전부 충족, U2 완료 시 화면/시나리오 전부 충족.
