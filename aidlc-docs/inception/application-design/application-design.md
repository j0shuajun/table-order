# Application Design — 통합본 (Consolidated)

/ Written at (KST): 2026-09-07 13:00 /

이 문서는 테이블오더 MVP의 **설계 잠금 통합본**입니다. 통상 construction의 Functional Design(상세 비즈니스 로직)까지 여기에 흡수해, **construction에서 새 결정이 없도록** 합니다.

## 1. 설계 결정 요약 (대화형 확정)
| # | 결정 | 값 |
|---|---|---|
| Q1 | Backend 구조 | 레이어드(routers/services/repositories/models/core) |
| Q2 | JWT 전달 | REST=Bearer 헤더, SSE=`?token=` 쿼리 |
| Q3 | 주문번호 시퀀스 | 매장·일 단위 글로벌(`YYYYMMDD-HHMM-####`) |
| Q4 | SSE 구조 | 관리자당 단일 스트림 `/api/admin/stream` |
| Q5 | 과거 이력 | 세션 상태 플래그(active/closed) 논리적 이동 |
| Q6 | 에러 형식 | FastAPI 기본형 `{detail}` + HTTP status |

추가 확정 스택: **SQLAlchemy ORM + Pydantic + bcrypt + JWT(HS256)**. 단일 FastAPI 서버가 API + 정적 프런트 서빙.

## 2. 문서 구성 (세부는 각 파일 참조)
| 문서 | 내용 |
|---|---|
| [data-model.md](data-model.md) | SQLite 9개 테이블 스키마 + ERD + 파생값 규칙 |
| [api-contract.md](api-contract.md) | REST + SSE 전체 계약(BE/FE 공통) |
| [business-rules.md](business-rules.md) | 세션 상태머신·총액·주문번호·인증·검증 규칙(R-*) |
| [components.md](components.md) | 레이어·컴포넌트 책임·인터페이스 |
| [component-methods.md](component-methods.md) | 메서드 시그니처·입출력 |
| [services.md](services.md) | 서비스 오케스트레이션·트랜잭션·SSE 매핑 |
| [component-dependency.md](component-dependency.md) | 의존성 매트릭스·통신·데이터 흐름·화면 맵 |

## 3. 확정 프로젝트 구조 (construction이 그대로 생성)
```text
table-order/
├── app/
│   ├── main.py                 # FastAPI 앱, 라우터 등록, startup 시드, 정적 마운트
│   ├── core/
│   │   ├── config.py           # JWT secret, TTL(16h), DB 경로, seed 토글
│   │   ├── db.py               # SQLAlchemy 엔진/세션, create_all
│   │   ├── security.py         # bcrypt, JWT, get_current_admin/table
│   │   ├── events.py           # EventBroker (SSE pub/sub)
│   │   └── seed.py             # 멱등 시드
│   ├── models/                 # SQLAlchemy 모델 (9 테이블)
│   ├── schemas/                # Pydantic 요청/응답
│   ├── repositories/           # DB 접근
│   ├── services/               # 비즈니스 로직(R-*)
│   └── routers/                # auth/customer/admin/sse/static
├── static/                     # 프런트: index.html(고객), admin.html, js/, css/, img/placeholder
├── tests/                      # 핵심 로직 단위 테스트
├── requirements.txt
└── table_order.db              # SQLite (런타임 생성)
```

## 4. NFR · 운영 제약 (최소선 명시 — 별도 NFR 단계 생략 근거)
> 별도 NFR/Infra 설계를 생략하는 대신, 이미 잠긴 최소 비기능선을 여기 못박아 둡니다(requirements §4).

| 영역 | 확정 수준 |
|---|---|
| 실시간 성능 | SSE로 신규 주문 **2초 이내** 대시보드 반영 목표 |
| 보안 | 비밀번호 **bcrypt**, **JWT 16h**. 로그인 시도 제한·2FA·HTTPS 강제는 범위 외 |
| 데이터 지속성 | **SQLite 파일** — 재시작 후 유지 |
| 사용성 | 터치 버튼 ≥ 44px, 카드형 메뉴 |
| 동시성 | 데모 규모 소수 동시성. SQLite 쓰기 직렬화로 주문번호 유일성 확보 |
| 복원력 | SSE는 EventSource 기본 자동 재연결 수준 |
| 관측성/배포 | 로컬 단일 서버 실행. 모니터링·CI/CD·클라우드 인프라 범위 외 |
| 테스트 | 세션 라이프사이클·총액·주문 생성·주문번호 등 **핵심 로직 단위 테스트**(전수 커버리지 아님) |

## 5. 요구사항 → 설계 추적 (커버리지 확인)
| 요구사항 | 설계 반영 |
|---|---|
| CUST-1 자동 로그인/세션 | `POST /api/table/auth` + JWT(role=table) + localStorage (R-AUTH-2) |
| CUST-2 메뉴 조회 | `GET /api/menu` + categories/menus (display_order) |
| CUST-3 장바구니 | **클라이언트 로컬 저장**(FE), 서버 전송은 주문 확정 시(POST /api/orders) |
| CUST-4 주문 생성 | `POST /api/orders`(가격 서버확정·번호·세션연결) + ~5초 후 메뉴 복귀(FE) |
| CUST-5 현재세션 내역 | `GET /api/orders/current`(active 세션만) (R-SES-5) |
| ADMIN-1 인증 | `POST /api/admin/login` JWT 16h bcrypt (R-AUTH-1) |
| ADMIN-2 실시간 모니터링 | `GET /api/admin/tables` + `GET /api/admin/stream`(SSE) + 상태변경 + 최신3 + 강조 |
| ADMIN-3 테이블 관리 | 테이블 등록/설정, 주문 삭제(재계산), 세션 complete, 과거 history(날짜필터) |
| ADMIN-4 메뉴 관리 | 카테고리/메뉴 CRUD + display_order + 검증 (R-MENU) |
| 세션/상태/이력 개념 | table_sessions 상태머신, orders.status, closed 세션 논리 이력 |

## 6. construction 무개입 진행 판단 근거
- 데이터 모델·API 계약·상세 규칙·컴포넌트/서비스·프로젝트 구조·스택·NFR 최소선이 모두 확정됨.
- 남는 것은 "이 설계대로 코드/테스트 작성"과 미시적 구현(변수명·파일 세부)뿐 → 방향/기능 신규 결정 없음.
- 이후 construction에서 설계에 없거나 충돌하는 사항이 나오면, 문서를 임의 변경하지 않고 **사용자에게 반문**한다(source of truth).
