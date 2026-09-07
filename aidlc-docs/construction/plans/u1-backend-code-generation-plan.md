# U1 Backend — Code Generation Plan

/ Written at (KST): 2026-09-07 13:40 /

> 이 계획은 U1 Backend 코드 생성의 **단일 진실 원천**이다. Part 2(생성)는 이 계획의 단계를 순서대로 실행하며, 완료 즉시 체크박스를 [x]로 갱신한다.

## 유닛 컨텍스트
- **유닛**: U1 Backend (단일 FastAPI 서비스 내 백엔드 개발 단위)
- **의존**: 없음(독립). U2 Frontend가 이 유닛의 계약(api-contract.md)에 의존.
- **소유 엔티티**: 9개 SQLite 테이블 전부 (stores, admin_users, tables, table_sessions, categories, menus, orders, order_items, order_sequences)
- **경계/계약**: `aidlc-docs/inception/application-design/api-contract.md`가 U1↔U2 유일 결합점
- **설계 원장**: data-model.md, business-rules.md(R-*), components.md, component-methods.md, services.md
- **완료 정의(DoD)**: api-contract의 모든 엔드포인트가 계약대로 응답 + 핵심 로직 단위 테스트 통과(주문 생성·주문번호·총액·세션 라이프사이클·인증)

## 코드 위치 (Greenfield, 확정 구조)
```text
app/{main.py, core/, models/, schemas/, repositories/, services/, routers/}
tests/            # pytest, 모듈 구조 미러링
requirements.txt  requirements-dev.txt
table_order.db    # 런타임 생성
```
- 애플리케이션 코드: 워크스페이스 루트(`app/`, `tests/`). 절대 `aidlc-docs/`에 두지 않음.
- 코드 요약 문서: `aidlc-docs/construction/u1-backend/code/`(markdown).

## 스토리 매핑 (요구사항 = 스토리 대체)
CUST-1(테이블 인증), CUST-2(메뉴), CUST-4(주문 생성), CUST-5(현재 세션 내역),
ADMIN-1(관리자 인증), ADMIN-2(실시간 모니터링·SSE), ADMIN-3(테이블 관리·이용완료·이력), ADMIN-4(메뉴 관리), 도메인(세션 상태머신·논리 이력).
> CUST-3(장바구니)는 클라이언트 전용 → U1 대상 아님.

---

## 실행 규약 (문서·커밋·브랜치) — U1 적용
- **브랜치**: `feat/u1-backend` (main에서 분기)
- **작업 문서**: `docs/tasks/2026-09-07-01_u1-backend_plan.md` → 완료 후 `_result.md` (한국어, 사람용)
- **커밋 리듬**: 아래 "논리 슬라이스" 1개 완료 → 최소 검증(pytest 해당 범위) → 로컬 커밋 → 다음 슬라이스. 끝에 몰아쓰기 금지.
- **pre-commit**: 커밋 전 `black . && isort . && ruff check .`
- **guide 동기화**: U1 완료 시 `docs/guide/architecture.md`, `docs/guide/development.md` 생성(하나의 `docs:` 커밋)
- **병합**: U1 검증 완료 후 `git switch main && git merge --no-ff feat/u1-backend`
- **언어**: 코드/주석/테스트/커밋 제목 = 영어, 작업·가이드 문서/커밋 본문 = 한국어

---

# PART 1 산출: 아래 단계 계획 (승인 대상)

## Step 1 — 프로젝트 셋업 & core 기반  [슬라이스 1]
- [ ] `requirements.txt`(fastapi, uvicorn, sqlalchemy, pydantic, python-jose 또는 pyjwt, passlib[bcrypt], sse-starlette 등) + `requirements-dev.txt`(pytest, black, isort, ruff)
- [ ] `app/core/config.py`(설정: JWT 시크릿·만료 16h, DB 경로), `app/core/db.py`(SQLAlchemy 엔진·세션·Base)
- [ ] `app/core/security.py`(bcrypt 해시/검증, JWT 발급/검증 — role claim: admin|table)
- [ ] `app/core/events.py`(SSE EventBroker: 관리자당 단일 스트림, publish/subscribe)
- **검증**: security 단위 테스트(해시 왕복, JWT 발급→검증→만료). **커밋**: `feat: add core config, db, security, and SSE broker`

## Step 2 — 데이터 모델 & 스키마  [슬라이스 2]
- [ ] `app/models/`: 9개 테이블 SQLAlchemy 모델(data-model.md 스키마 준수, money=INTEGER, created_at UTC)
- [ ] `app/schemas/`: Pydantic 요청/응답(api-contract.md와 1:1)
- **검증**: 모델 import·테이블 생성 스모크. **커밋**: `feat: add SQLAlchemy models and Pydantic schemas`

## Step 3 — 리포지토리 계층  [슬라이스 2에 포함 가능]
- [ ] `app/repositories/`: 순수 DB 접근(비즈니스 로직 없음) — menus, orders, sessions, tables, sequences, users
- **검증**: 리포지토리 CRUD 단위 테스트(인메모리 SQLite). **커밋**: `feat: add repository layer for data access`

## Step 4 — 주문 생성 규칙  [슬라이스 3, 핵심]
- [ ] `app/services/order_service.py`: 가격 서버 확정, 주문번호 `YYYYMMDD-HHMM-####`(일 단위 글로벌 시퀀스, 트랜잭션 원자 증가), 세션 연결(없으면 생성→Active), order_items 스냅샷(menu_name/unit_price), SSE `order_created` 발행
- [ ] TDD: 주문번호 형식·시퀀스 증가, 총액 계산, 세션 자동 생성 테스트 **먼저**
- **검증**: order_service 단위 테스트 통과. **커밋**: `feat: implement order creation with numbering, session, and totals`

## Step 5 — 세션 라이프사이클 & 상태  [슬라이스 4]
- [ ] `app/services/session_service.py`: NoActive→Active→Closed 상태머신, 테이블당 최대 1 active, "이용 완료"→Closed(논리 이력), 상태 플래그 기반 이력
- [ ] `app/services/order_service.py` 보강: 상태 변경(pending/preparing/completed), 삭제 시 총액 재계산, SSE `order_updated`/`order_deleted`/`session_closed`
- [ ] TDD: 상태 전이·이용완료·삭제 재계산 테스트
- **검증**: session/order 상태 테스트 통과. **커밋**: `feat: implement table session lifecycle and order status/delete`

## Step 6 — 인증 & 메뉴 서비스  [슬라이스 5]
- [ ] `app/services/auth_service.py`(admin login, table auth — JWT 발급), `app/services/menu_service.py`(조회), `app/services/menu_admin_service.py`(categories/menus CRUD + R-MENU 검증)
- [ ] `app/services/dashboard_service.py`(테이블 현황·상세·이력 조회)
- **검증**: auth/menu 검증 규칙 단위 테스트. **커밋**: `feat: add auth, menu, and dashboard services`

## Step 7 — API 라우터 (계약 구현)  [슬라이스 6]
- [ ] `app/routers/`: auth / customer / admin / sse — api-contract.md의 모든 엔드포인트
- [ ] Bearer 헤더 인증 의존성, SSE는 `?token=` 쿼리 인증
- [ ] 에러: `{detail}` + HTTP status(FastAPI 기본형)
- **검증**: TestClient로 대표 엔드포인트 계약 응답 확인. **커밋**: `feat: expose REST and SSE endpoints per API contract`

## Step 8 — 시드 & 앱 조립  [슬라이스 6에 포함]
- [ ] `app/core/seed.py`(startup: store001 "데모 식당", admin/admin1234, T1-T6 pw 0000, 3 카테고리, ~10 메뉴)
- [ ] `app/main.py`(라우터 등록, startup 시드, StaticFiles 마운트 — static/ 자리)
- **검증**: 앱 기동 + 시드 확인 + `/api/menu` 실제 응답. **커밋**: `feat: add startup seeding and app assembly`

## Step 9 — 문서화 & 병합  [문서 슬라이스]
- [ ] `docs/tasks/2026-09-07-01_u1-backend_result.md` 작성
- [ ] `docs/guide/architecture.md`(레이어·세션 상태머신·SSE 흐름·주문번호 정책), `docs/guide/development.md`(설치·실행·pytest·pre-commit) 생성
- [ ] 하나의 `docs:` 커밋
- [ ] `main`으로 `--no-ff` 로컬 병합

---

## 요약
- **총 9단계 / 6개 논리 슬라이스** → 슬라이스 단위 로컬 커밋(예상 6 feat + 1 docs).
- **접근**: core→모델→핵심 규칙(주문/세션) TDD→서비스→라우터/시드→문서·병합.
- **스토리 커버리지**: CUST-1/2/4/5 + ADMIN-1/2/3/4 + 도메인 전부 U1 범위에서 충족(CUST-3 제외 — 클라이언트 전용).
- **검증**: 핵심 로직은 단위 테스트, 계약은 TestClient. 통합·브라우저 시나리오는 Build & Test 단계.
