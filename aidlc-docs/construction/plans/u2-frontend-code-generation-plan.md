# U2 Frontend — Code Generation Plan (Part 1)

Written at (KST): 2026-09-07 13:10

## 목적
U1 백엔드의 확정 API(REST + 관리자 SSE) 위에 고객 앱(`/`)과 관리자 앱(`/admin`)을
순수 HTML/CSS/Vanilla JS로 구현한다. 빌드 스텝 없이 브라우저가 곧바로 로드한다.
완료 정의(DoD): requirements §6 시나리오 1~5를 브라우저 수동 워크스루로 통과.

## 정적 서빙 레이아웃 (결정)
U1이 이미 `frontend/`에서 서빙하도록 병합됨 — api-contract가 고정하는 URL과 일치:
- `GET /` → `frontend/index.html` (고객)
- `GET /admin` → `frontend/admin.html` (관리자)
- `GET /static/*` → `frontend/static/*` (css/js/img)

따라서 파일은 다음 구조로 생성한다:
```
frontend/
  index.html            # 고객 앱 셸
  admin.html            # 관리자 앱 셸
  static/
    css/app.css
    js/api.js           # fetch 래퍼 + 토큰(localStorage) + 에러 처리
    js/customer.js      # 고객 앱 로직
    js/admin.js         # 관리자 앱 로직(SSE 포함)
    img/                # placeholder(원격 placehold.co 사용, 로컬 최소)
```

## 논리 슬라이스 (커밋 후보)
> 슬라이스는 고정 커밋 계획이 아니라 작업 경계. 구현 중 더 나은 경계가 보이면 조정.

- **S1. 공통 셸 + API 클라이언트**: index.html/admin.html 골격, app.css, api.js
  (Bearer 토큰 localStorage 저장/주입, `{detail}` 에러 표준 처리, 401 시 재로그인).
- **S2. 고객 — 자동 로그인·메뉴·카트**: 저장된 테이블 토큰으로 자동 진입(없으면 1회
  입력 폼), `GET /api/menu` 렌더(카테고리/노출순), 카트 담기·수량·합계(localStorage).
  → CUST-1
- **S3. 고객 — 주문 확정·현재 내역**: `POST /api/orders` 확정→주문번호·총액 표시,
  `GET /api/orders/current`로 현재 세션 내역·세션 총액 갱신. → CUST-2, CUST-4, CUST-5
- **S4. 관리자 — 로그인 + 대시보드 골격**: `POST /api/admin/login`, 자동 로그인,
  `GET /api/admin/tables` 테이블 그리드(현재총액·주문수·최신3). → ADMIN-1
- **S5. 관리자 — 실시간·상세·상태변경·삭제**: `GET /api/admin/stream?token=`(EventSource)
  결합, `order_created` 신규 강조(~30s), 카드 클릭 상세(`.../orders`), 상태 변경
  (`POST .../status`)·삭제(`DELETE`). → ADMIN-2
- **S6. 관리자 — 관리(테이블 초기설정·이용완료·과거내역·메뉴 CRUD)**: 테이블 등록/목록
  (`/tables/config`,`POST /tables`), 이용완료(`POST .../complete`), 과거내역
  (`.../history`), 메뉴/카테고리 CRUD(`/menus`,`/categories`). → ADMIN-3, ADMIN-4

## 검증 방식 (경계에 맞게)
프런트는 자동화 단위 테스트 대신 **실제 브라우저/런타임 워크스루**로 검증한다.
- uvicorn 기동 후 시드 계정으로 시나리오 1~5 수동 확인(주문→대시보드 실시간 반영,
  상태변경/삭제/이용완료/과거내역/메뉴CRUD).
- 정적 자산 로딩(`/`,`/admin`,`/static/*` 200)과 콘솔 에러 없음 확인.
- 필요 시 U1 통합 테스트가 API 계약 회귀를 계속 보증(프런트 변경은 서버 무영향).

## 커밋·문서·병합 규약 (유닛 공통)
- 슬라이스 완료 → 브라우저 확인 → `feat/u2-frontend`에 논리 커밋. 커밋 제목 영어.
- 정적 프런트는 포매터 대상 아님(black/isort/ruff는 파이썬 한정). HTML/JS는 일관 스타일 유지.
- 완료 시 `docs/tasks/2026-09-07-02_u2-frontend_result.md`, `docs/guide/architecture.md`에
  프런트 화면맵 보강(필요 시 development.md 정적 서빙 메모).
- `feat/u2-frontend` → `main` `--no-ff` 로컬 병합(원격 없음 → push/PR 생략).

## 스토리 커버리지
- 고객: CUST-1(메뉴/카트) · CUST-2(주문) · CUST-4(현재 내역) · CUST-5(자동 로그인)
  (CUST-3는 서버 스냅샷 규칙으로 이미 충족, 클라이언트 표시만 해당)
- 관리자: ADMIN-1(대시보드) · ADMIN-2(실시간·상태) · ADMIN-3(테이블/세션) · ADMIN-4(메뉴)
