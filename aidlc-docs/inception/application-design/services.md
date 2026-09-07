# Services — 서비스 정의·오케스트레이션

/ Written at (KST): 2026-09-07 12:50 /

## 서비스 경계 원칙
- 서비스는 **비즈니스 규칙(R-*) 실행 + 트랜잭션 경계 + SSE 발행**을 담당.
- DB 접근은 repository에 위임, 인증은 router 의존성(core.security)에서 선처리 후 store_id/table_id를 서비스에 전달.
- 컨트롤러(router)는 얇게: 입력 파싱·검증 위임·응답 직렬화만.

## 오케스트레이션 예시

### 주문 생성 (OrderService.create_order)
1. 항목 검증(비어있지 않음/qty≥1) — 위반 400/404 (R-CRE-2)
2. `MenuRepository.by_ids` 로 가격·이름 서버측 확정 (R-CRE-1)
3. `SessionService.get_or_create_active` (R-SES-1)
4. `SequenceRepository.next_seq` → order_number 조립 (R-ORD)
5. `OrderRepository.create` (orders+items, total 계산) → commit
6. `OrderRepository.session_total` 로 current_total 산출 (R-TOT-2)
7. `EventBroker.publish("order_created", ...)` (R-CRE-3)
8. 주문 상세 반환

### 세션 종료 (SessionService.complete_session)
1. active 세션 조회 — 없으면 409 (R-SES-3)
2. `SessionRepository.close(session_id)` (status=closed, closed_at)
3. current_total=0 (R-TOT-4)
4. `EventBroker.publish("session_closed", ...)`

### 대시보드 요약 (DashboardService.list_tables)
1. 매장 테이블 전체 조회
2. 각 테이블의 active 세션 → 주문 목록 → current_total, order_count, latest 3
3. active 없으면 총액 0/미리보기 빈 배열

### 상태 변경 / 삭제
- `change_status`: 값 검증(R-ST-1) → update → `order_updated` 발행
- `delete_order`: 삭제(CASCADE) → session_total 재계산 → `order_deleted` 발행

## 트랜잭션·동시성
- 주문 생성은 단일 트랜잭션(시퀀스 증가 + 주문/항목 insert). SQLite 쓰기 직렬화로 order_number 유일성 보장 (R-ORD-2).
- SSE 발행은 **커밋 이후**에만.

## SSE 발행 매핑
| 트리거 | 이벤트 |
|---|---|
| 주문 생성 | `order_created` |
| 상태 변경 | `order_updated` |
| 주문 삭제 | `order_deleted` |
| 세션 종료 | `session_closed` |
