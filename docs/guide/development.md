# 개발 가이드

## 요구사항
- Python 3.13
- (권장) 가상환경 `.venv`

## 설치
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # 런타임만 필요하면 requirements.txt
```

## 실행
```bash
.venv/bin/python -m uvicorn app.main:app --reload
```
- 최초 실행 시 `table_order.db`(SQLite)가 생성되고 데모 데이터가 시드된다(멱등).
- 데모 계정: 관리자 `admin` / `admin1234`, 테이블 `T1`~`T6` 비밀번호 `0000`, 매장 `store001`.
- 프런트엔드(U2)가 `frontend/`에 배포되면 `/`(고객)·`/admin`(관리자)·`/static/*`로 서빙된다.

## 환경 변수 (선택)
| 변수 | 기본값 | 설명 |
|---|---|---|
| `TABLE_ORDER_JWT_SECRET` | 로컬 데모용 기본값 | HS256 서명 키(운영에서 반드시 교체) |
| `TABLE_ORDER_DATABASE_URL` | `sqlite:///table_order.db` | DB 접속 URL |

## 테스트
```bash
.venv/bin/python -m pytest -q
```
- 테스트는 프로덕션 모듈 구조를 미러링한다(`app/services/order_service.py` →
  `tests/app/services/test_order_service.py`).
- 서비스/모델은 인메모리 SQLite 픽스처(`tests/conftest.py`)로 격리 검증한다.
- API는 실제 startup 경로(create_all + seed)를 태우는 통합 테스트로 검증한다
  (`tests/app/api/test_api_flow.py`).

## 코드 스타일
커밋 전 포매팅/린트를 적용한다.
```bash
.venv/bin/black app tests
.venv/bin/isort app tests
.venv/bin/ruff check app tests
```

## 코드 지도
- 새 규칙/동작: `app/services/`
- 새 엔드포인트: `app/api/`(라우터) + 필요한 스키마 `app/schemas/`
- 새 쿼리: `app/repositories/`
- 설정·보안·SSE·예외: `app/core/`
- 시드 데이터: `app/seed.py`
