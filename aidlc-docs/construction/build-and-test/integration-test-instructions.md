# 통합 테스트 지침

## 목적
두 유닛(U1 백엔드, U2 프론트엔드)이 함께 동작하는지 검증한다. 통합 지점은
① 프론트엔드 → REST API, ② 고객 주문 → 관리자 SSE 실시간 반영 두 가지다.

## 자동 통합 테스트 (API 계층)
`tests/app/api/test_api_flow.py`가 실제 앱을 기동(스키마 생성 + 시드)해 API를 관통한다.
```bash
source .venv/bin/activate
python -m pytest tests/app/api/test_api_flow.py -q
```
- 임시 디렉터리에서 실제 startup 경로(create_all + seed)를 태워 격리 실행한다.
- 기대: 전부 통과.

## 수동 통합 시나리오 (프론트엔드 ↔ 백엔드 ↔ SSE)

### 사전 준비
```bash
# 깨끗한 상태로 시작하려면 기존 DB 제거 후 기동
rm -f table_order.db
python -m uvicorn app.main:app --port 8000
```

### 시나리오 1: 고객 주문 → 관리자 실시간 반영 (핵심 통합 지점)
1. 브라우저 A에서 `http://127.0.0.1:8000/admin` 접속 → `store001` / `admin` /
   `admin1234`로 로그인. 상단 연결 배지가 "실시간 연결됨"이 되는지 확인.
2. 브라우저 B(또는 시크릿 창)에서 `http://127.0.0.1:8000/` 접속 → `store001` /
   `T1` / `0000`으로 인증.
3. B에서 메뉴를 담아 주문한다.
4. **기대**: A의 대시보드에서 T1 카드가 즉시(약 2초 이내) 강조되고, 합계·주문
   건수가 증가하며 토스트가 뜬다.
5. A에서 T1 카드를 열어 주문 상태를 "준비중"으로 변경 → B의 "현재 주문" 탭에
   상태가 반영되는지 확인.
6. A에서 "이용 완료" → 세션이 닫히고 대시보드 합계가 0으로 돌아가며, "과거 내역"에
   방금 세션이 남는지 확인.

### 시나리오 2: 메뉴 관리 → 고객 메뉴 반영
1. A의 "메뉴 관리" 탭에서 카테고리/메뉴 추가 또는 가격 수정.
2. B에서 메뉴 화면을 새로고침 → 변경이 반영되는지 확인.

### CLI 스모크(빠른 회귀 확인)
서버 기동 후 아래로 로그인→주문→상세→상태변경→완료→내역 경로를 한 번에 확인한다.
```bash
B=http://127.0.0.1:8000
AT=$(curl -s $B/api/admin/login -H 'Content-Type: application/json' \
  -d '{"store_id":"store001","username":"admin","password":"admin1234"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
TT=$(curl -s $B/api/table/auth -H 'Content-Type: application/json' \
  -d '{"store_id":"store001","table_number":"T1","password":"0000"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
MID=$(curl -s $B/api/menu -H "Authorization: Bearer $TT" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['categories'][0]['menus'][0]['id'])")
curl -s $B/api/orders -H "Authorization: Bearer $TT" -H 'Content-Type: application/json' \
  -d "{\"items\":[{\"menu_id\":$MID,\"quantity\":2}]}"
curl -s $B/api/admin/tables -H "Authorization: Bearer $AT"
```

## 정리
```bash
# 서버 종료
pkill -f "uvicorn app.main"
# 필요 시 테스트 데이터 초기화
rm -f table_order.db
```
