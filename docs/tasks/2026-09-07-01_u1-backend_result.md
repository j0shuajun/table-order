# U1 Backend — 결과

Written at (KST): 2026-09-07 12:56

## 왜 필요했나
테이블오더 서비스의 서버(단일 FastAPI)를 구현하는 단위(U1)이다. 고객 태블릿의
메뉴 조회·주문과 관리자 대시보드의 실시간 주문 관리가 하나의 API 계약
(`aidlc-docs/.../api-contract.md`) 위에서 동작해야 한다. 이 단위는 그 계약을
그대로 구현하는 백엔드 전체(인증·주문·세션·메뉴·실시간 SSE·시드)를 담당한다.

## 무엇이 바뀌었나 (동작 기준)
- **인증**: 관리자(`store_id`+`username`+`password`)와 테이블(`store_id`+`table_number`+`password`)
  자격을 bcrypt로 검증하고 HS256 JWT(16시간)를 발급한다. REST는
  `Authorization: Bearer`, SSE는 `?token=` 쿼리로 인증하며 role 불일치는 403이다.
- **주문 생성**: 가격은 서버 DB 기준으로 확정(클라이언트 가격 무시)하고, 테이블의
  active 세션을 찾아 없으면 새로 만든 뒤 주문을 붙인다. 주문번호는 KST 기준
  `YYYYMMDD-HHMM-####`(매장·일 단위 시퀀스)로 부여하고, 총액을 계산해 저장한다.
  커밋 성공 후에만 `order_created` SSE를 발행한다.
- **현재 주문 / 대시보드**: 고객은 active 세션 주문만 시간순으로 본다. 관리자
  대시보드는 테이블별 현재 총액·주문 수·최신 3건 미리보기를 제공하고, 카드 클릭 시
  세션 상세를, "과거 내역"에서 closed 세션을 조회한다.
- **상태 변경 / 삭제 / 세션 완료**: 상태는 `pending|preparing|completed`만 허용하며
  변경 시 `order_updated`를 발행한다. 직권 삭제는 항목까지 CASCADE 삭제 후 총액을
  재계산하고 `order_deleted`를 발행한다. "이용 완료"는 active 세션을 closed로
  전환(논리적으로 과거 이동)하고 `session_closed`를 발행한다.
- **메뉴 관리**: 관리자용 카테고리/메뉴 CRUD(이름 비어있지 않음, price≥0, category 존재
  검증). 메뉴 삭제는 hard delete이며 과거 주문은 항목 스냅샷(menu_name/unit_price)으로
  보존되어 표시에 영향이 없다.
- **실시간**: 관리자당 단일 SSE 스트림으로 매장 전체 주문 이벤트를 수신한다. sync
  라우트(threadpool)에서 발행해도 안전하도록 브로커가 서빙 이벤트 루프를 바인딩해
  `call_soon_threadsafe`로 큐에 넣는다.
- **시드**: 서버 시작 시 데모 매장(store001), 관리자(admin/admin1234), 테이블 T1~T6
  (비번 0000), 카테고리 3종·메뉴 10종을 멱등하게 생성한다(매장 존재 시 skip).

## 대표 시나리오
1. 태블릿이 `POST /api/table/auth`로 토큰을 받고 `GET /api/menu`로 메뉴를 그린다.
2. 손님이 담은 항목으로 `POST /api/orders` → 새 세션·주문번호·총액이 반환되고,
   관리자 대시보드에는 2초 이내(실측 ~0.02s) `order_created`가 도착한다.
3. 관리자가 상태를 `preparing`으로 바꾸고, 필요 시 주문을 삭제하며, 식사 종료 시
   "이용 완료"로 세션을 닫는다. 같은 테이블의 다음 주문은 새 세션에서 시작된다.

## 현재 제약
- 단일 프로세스·단일 매장(store001) MVP. SSE 브로커는 인메모리(수평 확장 시 별도 필요).
- SQLite 파일 DB. 동시 주문은 트랜잭션 직렬화 + 시퀀스 원자 증가로 번호 충돌을 막는다.
- 프런트엔드(U2)는 별도 단위로, 서버는 `frontend/`가 있으면 `/`·`/admin`·`/static`을 서빙한다.

## 검증
- 서비스/모델 단위 테스트와 실제 startup 경로 기반 API 통합 테스트로 31개 통과.
- uvicorn 런타임에서 주문 생성 → 관리자 SSE `order_created` 수신을 실측 확인.
