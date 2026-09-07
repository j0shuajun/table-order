# U1 Backend 구현 계획

/ Written at (KST): 2026-09-07 13:45 /

## 작업 목적
테이블오더 서비스의 **백엔드 전체**를 만든다. 고객(태블릿)과 관리자가 쓰는 모든 기능의 **API·데이터·비즈니스 규칙·실시간 이벤트**를 담당한다. 이 유닛이 끝나면 프런트(U2) 없이도 API만으로 주문 접수·조회·관리·실시간 알림이 계약대로 동작한다.

## 현재 상태
- Greenfield. 코드 없음. 설계 원장(`aidlc-docs/inception/application-design/`)에 데이터 모델(9테이블)·API 계약·비즈니스 규칙(R-*)이 확정되어 있다.
- 기술: Python FastAPI + SQLAlchemy + Pydantic + bcrypt + JWT(HS256) + SQLite, 실시간은 SSE.

## 목표 상태
- `api-contract.md`의 모든 엔드포인트가 계약대로 응답.
- 핵심 규칙(주문 생성/번호/총액, 세션 라이프사이클, 인증)이 단위 테스트로 입증.
- 서버 기동 시 데모 데이터가 자동 시드되어 즉시 사용 가능.
- 단일 FastAPI 프로세스가 API + (이후 U2의) 정적 프런트를 함께 서빙할 준비 완료.

## 대표 시나리오
1. **주문**: 고객이 메뉴 2개를 담아 `POST /api/orders` → 서버가 가격을 DB에서 확정, 주문번호 `YYYYMMDD-HHMM-####` 부여, active 세션에 연결(없으면 생성), 총액 계산, 관리자에게 `order_created` SSE 발행 → 201 응답.
2. **실시간 모니터링**: 관리자가 `GET /api/admin/stream`으로 SSE 구독 → 신규 주문이 2초 내 대시보드에 반영.
3. **이용 완료**: 관리자가 `POST /api/admin/tables/{id}/complete` → active 세션 `closed` 전환(논리 이력), 현재 총액 0, `session_closed` SSE.

## 진행 방식 (문서·커밋·브랜치)
- 브랜치 `feat/u1-backend`에서 작업, 논리 슬라이스(core → 모델/스키마/리포지토리 → 주문 생성 → 세션 라이프사이클 → 서비스 → 라우터/시드 → 문서) 단위로 로컬 커밋.
- 비즈니스 로직은 TDD(실패 테스트 먼저). 커밋 전 `black/isort/ruff`.
- 완료 후 결과 문서 + `docs/guide` 동기화 → `main`으로 `--no-ff` 병합.

## 중요한 결정·제약
- 금액은 원 단위 정수, `created_at`은 UTC 저장, 주문번호의 날짜·시각만 KST 기준.
- 주문번호 시퀀스는 매장·일 단위 글로벌, 주문 트랜잭션 내 원자 증가.
- 세션 종료는 물리 삭제가 아닌 `status=closed` 논리 이동. 테이블당 active 세션 최대 1.
- 가격은 항상 서버 확정, `order_items`에 이름·단가 스냅샷 저장(메뉴 삭제와 무관하게 과거 표시 유지).

## 리스크·완화
- 동시 주문 시 번호 충돌 → 시퀀스 원자 증가 + `order_number` UNIQUE + 트랜잭션.
- 계약 구멍 발견 시 → 임의 변경 없이 반문 후 재확정(inception이 source of truth).

## 검증 접근
- 단위 테스트: 주문번호 형식·시퀀스, 총액, 세션 전이, bcrypt/JWT.
- 계약 검증: FastAPI TestClient로 대표 엔드포인트.
- 런타임: 앱 기동 + 시드 확인 + `/api/menu` 실제 응답. (통합·브라우저 시나리오는 Build & Test 단계.)
