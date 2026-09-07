# 테이블오더 (Table Order)

식당용 태블릿 주문 + 관리자 실시간 주문 관리 서비스. 단일 FastAPI 서버가 REST API,
관리자 SSE 스트림, 정적 프런트엔드를 함께 서빙한다.

## 빠른 시작
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --reload
```
최초 실행 시 SQLite DB가 생성되고 데모 데이터가 시드된다. 데모 계정: 관리자
`admin`/`admin1234`, 테이블 `T1`~`T6` 비밀번호 `0000`(매장 `store001`).

## 기능
- 테이블 인증(태블릿) / 관리자 로그인 — HS256 JWT
- 카테고리별 메뉴 조회, 장바구니 주문 생성(서버 가격 확정)
- 테이블 세션 자동 생성/종료, 현재 주문·총액 집계
- 관리자 대시보드: 테이블별 요약, 주문 상태 변경·삭제, 과거 내역, "이용 완료"
- 신규 주문 실시간 반영(관리자 SSE, 목표 2초 이내)
- 관리자 메뉴/카테고리·테이블 관리

## 문서
- 아키텍처: [`docs/guide/architecture.md`](docs/guide/architecture.md)
- 개발/실행/테스트: [`docs/guide/development.md`](docs/guide/development.md)
- API 계약(단일 진실 원천): `aidlc-docs/inception/application-design/api-contract.md`

## 구조
```
app/
  api/          라우터 + JWT 인증 의존성
  services/     비즈니스 로직(프레임워크 독립)
  repositories/ DB 접근
  models/ schemas/ ORM · Pydantic
  core/         config·db·security·events·errors
  seed.py main.py
tests/          모듈 구조를 미러링한 테스트
```
