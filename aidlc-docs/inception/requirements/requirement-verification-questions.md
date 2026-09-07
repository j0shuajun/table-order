# 요구사항 검증 질문 (Requirements Verification Questions)

요구사항 문서(`requirements/table-order-requirements.md`, `requirements/constraints.md`)는 기능 범위가 이미 상세합니다.
아래는 **오늘 4-5시간 내 동작하는 MVP**를 만들기 위해 반드시 확정해야 하는 항목들입니다.
각 질문의 `[Answer]:` 태그 뒤에 선택한 letter를 적어주세요. 맞는 항목이 없으면 마지막 `X) Other`를 선택하고 설명을 적어주세요.

> 각 옵션의 첫 번째(A)는 **시간 제약을 고려한 권장안**입니다. 특별한 이유가 없다면 A를 골라주시면 가장 빠르게 진행됩니다.

---

## Question 1
백엔드/프론트엔드 기술 스택을 무엇으로 할까요? (4-5시간 MVP 기준)

A) Python FastAPI (백엔드) + 순수 HTML/CSS/Vanilla JS (프론트, 빌드 과정 없음) — 셋업이 가장 빠르고 SSE 구현이 간단함 (권장)

B) Node.js Express (백엔드) + 순수 HTML/CSS/Vanilla JS (프론트)

C) Python FastAPI (백엔드) + React (프론트, Vite)

D) Node.js Express (백엔드) + React (프론트, Vite)

X) Other (please describe after [Answer]: tag below)

[Answer]: A. BE와 FE로 나누어서 구현하는 것이 좋을 듯 하고, BE/FE간 통신을 위한 API 규격을 정하고, BE/FE 모두 그 규격을 준수하도록 진행하면 좋겠음.

---

## Question 2
데이터 저장소는 무엇으로 할까요?

A) SQLite (파일 기반 관계형 DB — 별도 설치 불필요, 재시작해도 데이터 유지, 셋업 빠름) (권장)

B) In-memory (프로세스 메모리에만 저장 — 가장 단순하지만 서버 재시작 시 데이터 소실)

C) PostgreSQL 등 별도 DB 서버 (Docker/설치 필요)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
관리자 실시간 주문 모니터링의 실시간 갱신 방식은?
(요구사항 원문은 SSE를 명시하고 있습니다.)

A) 요구사항대로 SSE (Server-Sent Events) 구현 — 단방향 실시간, 구현 난이도 중간 (권장)

B) 폴링(polling, 예: 2초마다 조회) — 구현이 가장 단순하나 요구사항의 "SSE" 문구와는 다름

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
관리자 인증(3.2.1)의 보안 강도를 MVP에서 어느 수준으로 구현할까요?
(원문은 bcrypt 해싱 + JWT 16시간 세션 + 로그인 시도 제한을 명시)

A) JWT 16시간 세션 + bcrypt 비밀번호 해싱까지 구현, 단 "로그인 시도 제한"은 MVP 범위에서 제외 — 핵심 인증은 지키되 시간 절약 (권장)

B) 원문대로 로그인 시도 제한까지 모두 구현

C) 최소화: 단순 토큰/세션만 두고 bcrypt·JWT 없이 하드코딩 계정으로 로그인 (가장 빠름, 보안성 낮음)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
초기 데이터(시드)를 어떻게 준비할까요? — 데모/시연을 위해 필요합니다.

A) 서버 시작 시 샘플 매장 1개 + 관리자 계정 1개 + 카테고리/메뉴 여러 개 + 테이블 몇 개를 자동 시드 (권장)

B) 시드 없이 빈 상태로 시작하고, 관리자 화면에서 직접 등록

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6 (Extension: Security)
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 7 (Extension: Resiliency)
Should the resiliency baseline be applied to this project?

이 extension을 켜면 AWS Well-Architected(신뢰성 기둥) 기반의 설계 시점 복원력 모범사례(내결함성, 고가용성, 관측성, 복구성 등)를 요구사항/설계/코드에 반영하도록 유도합니다. 프로덕션 준비 완료를 보장하지는 않으며 시작점 역할입니다.

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects where rapid iteration matters more than reliability)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 8 (Extension: Property-Based Testing)
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)

X) Other (please describe after [Answer]: tag below)

[Answer]: C
