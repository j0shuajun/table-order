# 아키텍처

테이블오더는 식당의 태블릿 주문과 관리자 실시간 주문 관리를 제공하는 **단일 FastAPI
서버**다. 고객 앱(`/`)과 관리자 앱(`/admin`)을 정적으로 서빙하고, 모든 기능은
`/api/*` REST와 관리자용 SSE 스트림으로 노출된다.

## 전체 그림

```
[고객 태블릿]            [관리자 브라우저]
     │ REST(Bearer)           │ REST(Bearer) + SSE(?token=)
     ▼                        ▼
┌─────────────────────────────────────────────┐
│                FastAPI (app/)                 │
│  api/      라우터 + 인증 의존성(JWT)           │
│  services/ 비즈니스 로직(프레임워크 독립)       │
│  repositories/ 순수 DB 접근                    │
│  models/   SQLAlchemy ORM   schemas/ Pydantic  │
│  core/     config·db·security·events·errors    │
└─────────────────────────────────────────────┘
     │                        ▲
     ▼                        │ order_created 등 이벤트
  [SQLite]              [EventBroker(인메모리 SSE)]
```

## 계층과 책임
- **api/**: HTTP 경계. 요청/응답 스키마 변환과 JWT 인증 가드(`require_admin`,
  `require_table`)만 담당하고 로직은 서비스에 위임한다.
- **services/**: 규칙이 사는 곳. 주문 생성·세션 라이프사이클·총액·상태/삭제·인증·
  메뉴 관리. FastAPI에 의존하지 않고, 실패는 HTTP 상태코드를 실은 도메인 예외
  (`app/core/errors.py`)로 표현한다. 하나의 예외 핸들러가 `{"detail": ...}`로 변환한다.
- **repositories/**: SQLAlchemy 쿼리만 있는 얇은 데이터 접근층(비즈니스 로직 없음).
- **models/ · schemas/**: ORM 엔티티(9개 테이블)와 API 계약에 대응하는 Pydantic 스키마.
  응답 datetime은 ISO 8601 UTC(`Z`)로 직렬화한다.
- **core/**: 설정(env), DB 엔진/세션, bcrypt·JWT, SSE 브로커, 도메인 예외.

## 핵심 개념
- **테이블 세션**: 한 테이블에 active 세션은 최대 1개. 첫 주문 시 자동 생성되고,
  "이용 완료"로 closed 전환되면 논리적으로 과거 내역이 된다. 다음 주문은 새 세션.
- **현재 총액**: active 세션 주문 `total_amount`의 합(즉석 계산). 세션이 닫히면 0.
- **주문번호**: KST 기준 `YYYYMMDD-HHMM-####`. `####`는 매장·일 단위 시퀀스를 주문
  트랜잭션 안에서 원자 증가시켜 부여한다.
- **가격 권위**: 주문 총액/항목 가격은 서버 DB 기준으로 확정하고 클라이언트 값은 무시한다.
  주문 항목은 `menu_name`/`unit_price`를 스냅샷으로 저장해 이후 메뉴 수정·삭제와 무관하게 보존된다.

## 실시간 흐름
주문 생성/상태변경/삭제/세션완료는 **DB 커밋 성공 후** `EventBroker.publish`로
관리자 스트림에 이벤트를 보낸다. 라우트 핸들러는 threadpool에서 실행되므로 브로커는
시작 시 서빙 이벤트 루프를 바인딩(`bind_loop`)하고 `call_soon_threadsafe`로 큐에 넣어
`asyncio.Queue` 사용을 스레드-세이프하게 유지한다. 목표는 신규 주문 후 2초 이내 반영.

## 인증 경계
HS256 JWT(발급 16시간). 클레임 `role`(`admin`|`table`), `store_id`, 그리고 role별
식별자(admin: `username`, table: `table_id`/`table_number`). REST는 `Authorization:
Bearer`, SSE는 EventSource 헤더 제약 때문에 `?token=` 쿼리로 검증한다. 미인증/만료 401,
role 불일치 403.
