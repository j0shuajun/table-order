# UI 리디자인 — 배달의민족 톤 (Brownfield 챌린지 A)

Written at (KST): 2026-09-07 22:10

## 목적 / 왜 중요한가
동작하는 MVP는 완성됐지만 UI는 기본 톤(주황 계열)에 머물러 있다. 실제 서비스처럼
보이도록 **배달의민족 브랜드 톤**(민트 포인트 컬러 + 둥글고 친근한 타이포그래피)으로
고객·관리자 화면을 리디자인한다. 이는 AI-DLC의 **Brownfield(기존 코드 개선/확장)**
흐름을 체험하는 보너스 챌린지 A이다.

## 현재 상태 (Reverse Engineering 대체)
- 프론트엔드: 순수 HTML/CSS/Vanilla JS, 빌드 없음. FastAPI가 `/`(고객), `/admin`(관리자),
  `/static/*`로 서빙.
- 스타일은 `frontend/static/css/app.css` 한 곳에 **CSS 변수 + 클래스 체계**로 집약.
  화면 마크업은 `index.html`(고객), `admin.html`(관리자)이 클래스만 참조.
- 따라서 시스템 이해 자료는 기존 `aidlc-docs`로 충분 → 별도 Reverse Engineering 문서 불요.

## 범위 (Accepted Scope)
- 고객 화면(`/`)과 관리자 화면(`/admin`) **전부** 배민 톤으로 리스타일.
- **기능·동작·API·인증·SSE는 일절 변경하지 않는다.** CSS와, 필요한 경우 클래스/폰트
  링크 정도의 최소 마크업 훅만 수정.
- 새 빌드 단계·npm 의존성 도입 금지.

## 디자인 방향 (Requirements)
- **컬러**: 배민 민트를 포인트로. `--brand: #2AC1BC`, `--brand-dark: #1EA7A2`.
  밝고 깔끔한 배경(near-white), 진한 잉크 텍스트. 주문 상태 배지는 민트 팔레트와
  조화되도록 재조정(접수/준비중/완료 구분은 유지).
- **타이포그래피**: 배민 서체 계열 웹폰트로 친근한 느낌 —
  로고/제목에 **주아체(Google Fonts "Jua")**, 숫자·강조에 **도현체("Do Hyeon")**.
  본문은 가독성 위해 시스템 산세리프 유지. Google Fonts `<link>`로 로드하고,
  오프라인/차단 시 둥근 시스템 폰트로 graceful fallback.
- **형태/촉감**: 더 둥근 모서리(radius↑), 부드러운 그림자, 두툼하고 누르기 쉬운 버튼,
  메뉴 카드의 큰 이미지, 카드 hover 살짝 떠오르는 효과. 태블릿 터치 타깃 확대(≥44px).

## 스테이지 계획 (AI-DLC, adaptive)
- Workspace Detection: Brownfield(코드 존재), 기존 문서로 이해 충족 → RE SKIP
- Requirements Analysis: 본 문서(디자인 방향)로 충족
- User Stories: SKIP — 새 사용자 기능 없음(순수 리스타일)
- Workflow Planning: 본 문서에 포함
- Application Design / Units Generation: SKIP — 새 컴포넌트/유닛 없음(단일 프론트 스타일 변경)
- Construction: Functional/NFR/Infra Design SKIP → **Code Generation**(실제 작업) → **Build & Test**(검증)
- Extensions(Security/Resiliency/Property-Based): 모두 Disabled → CSS 변경에 N/A

## 대표 시나리오 (변화는 시각적으로만)
1. 손님이 `/`에서 메뉴를 본다 → 배민 톤의 큰 이미지 카드·민트 담기 버튼. 담기/수량/주문
   동작은 이전과 동일.
2. 관리자가 `/admin` 대시보드를 본다 → 민트 톤 탭·카드·배지. 실시간 강조/상태 변경/모달
   동작 동일.

## 검증 (Verification)
- 기존 백엔드 테스트 37개 여전히 통과(코드 무변경이므로 회귀 없음 확인).
- `node --check`로 JS 무변경/무손상 확인.
- uvicorn 실서버 스모크: 고객(로그인→메뉴→담기→주문→현재주문), 관리자(로그인→대시보드→
  상태변경→모달→테이블/메뉴 관리) 흐름이 시각적으로 정상 동작.

## 제약 / 리스크
- Google Fonts 웹폰트는 외부 리소스 → 온라인 필요. 차단 시 fallback 폰트로 자연 저하.
- 다크모드는 범위 밖(현재도 라이트 전용).
