# 빌드 지침

테이블오더는 **단일 FastAPI 서비스**다. 백엔드는 Python(빌드 산출물 없음),
프론트엔드는 no-build 정적 자산(HTML/CSS/Vanilla JS)이므로 "빌드"는 사실상
의존성 설치와 서버 기동으로 끝난다. 컴파일/번들 단계가 없다.

## 사전 요구사항
- **런타임**: Python 3.13
- **의존성**: `requirements.txt` (실행), `requirements-dev.txt` (테스트/린트)
  - 실행: fastapi, uvicorn[standard], sqlalchemy, pydantic, PyJWT, bcrypt, sse-starlette
- **환경 변수**(모두 선택 — 로컬 기본값 존재):
  - `TABLE_ORDER_JWT_SECRET` — HS256 서명 키(운영 시 반드시 교체, 32바이트 이상 권장)
  - `TABLE_ORDER_DATABASE_URL` — 기본 `sqlite:///table_order.db`
- **시스템**: OS 무관(macOS/Linux 확인), 디스크/메모리 요구 미미(SQLite 파일 1개)

## 빌드(설치) 단계

### 1. 가상환경 및 의존성 설치
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. 환경 구성(선택)
```bash
# 운영/공유 환경에서는 서명 키를 반드시 교체한다.
export TABLE_ORDER_JWT_SECRET="<32바이트 이상 무작위 문자열>"
# 필요 시 DB 위치 변경
export TABLE_ORDER_DATABASE_URL="sqlite:///table_order.db"
```

### 3. 서버 기동
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
기동 시 `lifespan`에서 (1) 테이블 스키마 생성(`create_all`), (2) SSE 브로커의
이벤트 루프 바인딩, (3) 데모 시드(비어 있을 때만)를 수행한다.

### 4. 기동 성공 확인
- 로그에 uvicorn `Application startup complete.` 출력
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/` → `200`
- 산출물: `table_order.db`(최초 실행 시 생성), 데모 데이터(매장 store001, admin/admin1234,
  테이블 T1–T6 비밀번호 `0000`, 카테고리/메뉴 시드)

## 트러블슈팅

### `ModuleNotFoundError` / 의존성 오류
- **원인**: 가상환경 미활성화 또는 설치 누락
- **해결**: `source .venv/bin/activate` 후 `pip install -r requirements.txt -r requirements-dev.txt`

### 포트 충돌(`Address already in use`)
- **원인**: 이전 uvicorn 프로세스가 남아 있음
- **해결**: `pkill -f "uvicorn app.main"` 또는 `--port`를 다른 값으로 지정

### 시드가 반영되지 않음 / 데이터가 이상함
- **원인**: 기존 `table_order.db`가 남아 있어 시드가 건너뜀(멱등)
- **해결**: 초기화가 필요하면 서버를 멈추고 `rm table_order.db` 후 재기동
