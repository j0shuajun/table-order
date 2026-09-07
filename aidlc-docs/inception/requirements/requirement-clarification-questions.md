# 요구사항 확정(잠금) 질문 — Inception 완결성용

목적: **construction에서 새 결정이 필요 없도록**, MVP 구현에 필요한 남은 결정들을 지금 모두 확정합니다.
각 `[Answer]:` 뒤에 letter를 적어주세요. A가 시간 제약을 고려한 권장안입니다.

---

## Question 1 — 실행/서빙 구조
프론트엔드(HTML/CSS/JS)와 백엔드(FastAPI)를 어떻게 실행할까요?

A) **단일 서버**: FastAPI 하나가 REST/SSE API와 정적 프론트 파일을 함께 서빙 (단일 포트, 실행/데모 가장 단순, CORS 불필요) (권장)

B) **분리 서버**: 프론트는 별도 정적 서버로, 백엔드는 FastAPI로 분리 실행 (CORS 설정 필요, 배포 유연성↑)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2 — 고객(테이블) 인증 메커니즘
고객 태블릿의 "자동 로그인/세션"을 기술적으로 어떻게 구현할까요?
(관리자가 초기 1회 매장ID·테이블번호·테이블비밀번호 입력 → 서버 검증 → 토큰 발급 → 로컬 저장 → 이후 자동 로그인)

A) 관리자와 **동일하게 JWT 토큰** 사용(테이블용 클레임 포함), 브라우저 localStorage에 저장, 자동 로그인. 메커니즘 일관성↑ (권장)

B) 테이블 전용 **단순 랜덤 토큰**(서버 DB에 저장·조회) 방식

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3 — 다중 매장(멀티테넌시) 범위
MVP에서 매장을 몇 개까지 다룰까요?

A) **단일 매장 데모로 고정**: 스키마에는 store_id를 두되 시드 매장 1개만 사용 (범위 최소화) (권장)

B) 다중 매장 등록/관리까지 구현

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4 — 고객 "주문 내역" 화면 표시 방식
requirements가 "페이지네이션 또는 무한 스크롤"로 열어두어 하나로 확정이 필요합니다.

A) **단순 전체 표시**(현재 세션 주문을 시간순으로 모두 표시, 페이지네이션/무한스크롤 없음) — MVP 단순화 (권장)

B) 간단한 페이지네이션

C) 무한 스크롤

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5 — 시드 데이터 구체값 승인
데모/로그인을 위해 아래 초기 데이터를 자동 시드하려 합니다. 승인하시겠습니까?

- **매장**: `store_id = "store001"`, 매장명 "데모 식당"
- **관리자 계정**: username `admin` / password `admin1234` (bcrypt 해싱 저장)
- **테이블**: 6개(T1~T6), 각 테이블 비밀번호 `0000`
- **메뉴 카테고리 3종**: 메인 / 사이드 / 음료
- **메뉴**: 카테고리별 3~4개(총 약 10개), 각 항목에 가격·설명·이미지URL(placeholder) 포함

A) 위 제안대로 시드 (권장)

B) 값 일부를 바꾸고 싶음 (X에 구체적으로 지정)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6 — 아래 "세부 기본값"을 이대로 확정할까요?
다음 항목들은 제품 방향과 무관한 세부라 기본값으로 잠그려 합니다. 이의 없으면 A를 선택해주세요.

- 주문 성공 후 **자동 리다이렉트 대기시간**: 약 **5초**
- **주문번호 형식**: `일자+일련번호`(예: `20260907-0001`)
- 관리자 카드 **"최신 주문 미리보기" 개수**: **3개**
- **신규 주문 강조**: 최근 생성 주문을 색상+간단 애니메이션으로 강조(예: 30초간)
- **메뉴 이미지가 없거나 로드 실패 시**: placeholder 이미지 표시
- **과거 내역 날짜 필터**: 시작일~종료일 선택 방식(기본 최근 표시)
- 주문 **상태 값**: 대기중(pending) / 준비중(preparing) / 완료(completed)

A) 위 기본값대로 모두 확정 (권장)

B) 일부 수정 원함 (X에 지정)

X) Other (please describe after [Answer]: tag below)

[Answer]: X. 주문번호는 HHMM 형태로 (ex. 20260907-1526-0001) 와 같은 형태면 좋겠음. 나머지는 동의
