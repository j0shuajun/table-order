# Application Design Plan (설계 계획 + 설계 질문)

/ Written at (KST): 2026-09-07 11:55 /

## 목적
이 단계에서 **inception의 실질 잠금**을 완료합니다. 통상 construction의 Functional Design에 해당하는 **상세 비즈니스 규칙·데이터 모델·API 계약**까지 여기서 확정합니다.
→ 이 문서의 질문에 답해 주시면, 그 답을 반영해 실제 설계 산출물을 생성합니다.

## 생성 예정 산출물 (체크리스트)
- [ ] `application-design/components.md` — 컴포넌트 정의·책임·인터페이스
- [ ] `application-design/component-methods.md` — 메서드 시그니처·입출력
- [ ] `application-design/services.md` — 서비스 정의·오케스트레이션
- [ ] `application-design/component-dependency.md` — 의존 관계·통신·데이터 흐름
- [ ] `application-design/data-model.md` — **SQLite 스키마 9개 테이블 전체** (흡수)
- [ ] `application-design/api-contract.md` — **REST + SSE 계약 전체** (BE/FE 공통 준수, 흡수)
- [ ] `application-design/business-rules.md` — **세션 상태머신·총액 재계산·주문번호 생성 등 상세 규칙** (Functional Design 흡수)
- [ ] `application-design/application-design.md` — 위 문서 통합본 (+ 간단한 NFR·운영 제약 섹션)
- [ ] 설계 완전성·일관성 검증

---

## 설계 확정 질문 (진짜 열린 결정만)
각 `[Answer]:` 뒤에 letter를 적어주세요. **A가 시간 제약·단순성 기준 권장안**입니다. 모두 동의하시면 A로 답하시면 됩니다.

### Q1 — Backend 코드 구조(레이어링)
A) **레이어드 구조**: `routers/`(API) · `services/`(비즈니스 로직) · `repositories/`(DB 접근) · `models/`(스키마) · `core/`(auth·db·seed·config). 책임 분리 명확, 단위 테스트 용이 (권장)

B) **단순 평면 구조**: `main.py` + 소수 파일. 빠르지만 규모 커지면 얽힘

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07)

### Q2 — 인증 토큰 전달 방식 (BE/FE 계약에 직접 영향)
관리자·테이블 모두 JWT를 씁니다. 브라우저가 서버에 토큰을 어떻게 전달할까요?
(참고: SSE의 `EventSource`는 커스텀 헤더를 못 실어서, SSE 연결만은 쿼리파라미터 토큰을 허용해야 합니다.)

A) **REST는 `Authorization: Bearer <JWT>` 헤더 + localStorage 저장, SSE는 `?token=<JWT>` 쿼리파라미터**. 표준적이고 단순 (권장)

B) **HttpOnly 쿠키**로 토큰 전달(자동 첨부). XSS엔 강하나 CSRF 대응·설정 부담↑

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07) — REST=Bearer 헤더+localStorage, SSE=?token=<JWT> 쿼리파라미터

### Q3 — 주문번호 일련번호(####) 부여 기준
형식은 확정된 `YYYYMMDD-HHMM-####` 입니다. 뒤 4자리 시퀀스를 어떤 범위로 증가시킬까요?

A) **매장 기준 "그 날(00:00~24:00)" 전체에서 1씩 증가**(일 단위 글로벌 시퀀스). HHMM은 생성 시각 표시용, 시퀀스는 하루 단위로 유일. 충돌 없고 단순 (권장)
  - 예: 그날 15:26 첫 주문 `...-1526-0001`, 15:40 두 번째 주문이면 `...-1540-0002`

B) **분(HHMM)마다 0001로 리셋**되는 시퀀스

C) **테이블별** 시퀀스

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07) — 매장·일 단위 글로벌 시퀀스

### Q4 — SSE 스트림 구조
관리자 대시보드 실시간 갱신용 SSE를 어떻게 구성할까요?

A) **관리자당 단일 스트림**: 매장 전체의 주문 이벤트(생성·상태변경·삭제·세션종료)를 하나의 `/api/admin/stream`으로 수신하고, 프론트가 테이블별로 렌더/필터. 단순 (권장)

B) **테이블별 스트림**: 테이블마다 별도 연결. 연결 수↑·복잡도↑

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07) — 관리자당 단일 스트림 /api/admin/stream

### Q5 — 과거 이력(OrderHistory) 저장 방식
requirements 3.3: "세션 종료 시 현재 주문들을 세션ID로 그룹화해 **이력으로 이동**". 물리적으로 어떻게 구현할까요?

A) **상태 플래그 방식**: `table_sessions`에 상태(active/closed)와 종료시각을 두고, 주문은 그대로 두되 세션 종료로 구분. 활성 화면은 active 세션만 조회, 과거 내역은 closed 세션 조회. 데이터 중복·이관 버그 없음, MVP에 가장 견고 (권장)
  - 요구사항의 "이동"을 **논리적 이동(쿼리로 활성/과거 구분)** 으로 해석

B) **물리적 이동**: 별도 `order_history`/`order_history_items` 테이블로 실제 복사·삭제. 요구사항 문구에 축자적이나 이관 로직·중복 위험↑

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07) — 상태 플래그 방식. requirements 3.3 "이력으로 이동"을 세션 상태(active/closed) 기반 **논리적 이동**으로 해석·확정 (사용자 승인)

### Q6 — API 에러 응답 형식
A) **FastAPI 기본형** `{ "detail": "메시지" }` + 적절한 HTTP status code(400/401/403/404/409 등). 단순·관례적 (권장)

B) 커스텀 형식 `{ "error": { "code": "...", "message": "..." } }`

X) Other (please describe after [Answer]: tag below)

[Answer]: A (대화형 확정 2026-09-07) — FastAPI 기본형 { "detail": ... } + HTTP status

---

## 답변 후 진행
위 6개 답변을 받으면, 이를 반영해 설계 산출물(컴포넌트/서비스/의존성 + 데이터 모델 + API 계약 + 비즈니스 규칙 + 통합본)을 생성하고 승인 게이트를 제시합니다. 그 문서가 곧 **construction 무개입 진행의 근거(빈틈 확인용)** 가 됩니다.
