# 성능 테스트 지침 (경량, 선택)

MVP의 성능 목표는 소규모 단일 매장(테이블 ~수십 개) 기준이며, 유일한 명시적
성능 요건은 **신규 주문 후 관리자 화면 2초 이내 반영**이다. 대규모 부하 테스트는
범위 밖이며, 아래는 목표 충족을 확인하는 경량 절차다.

## 성능 요건
- **SSE 반영 지연**: 주문 커밋 → 관리자 이벤트 수신 2초 이내
- **응답 시간**: 로컬 SQLite 기준 일반 REST 요청 체감 즉시(수십 ms)
- **동시성**: 단일 매장 규모(수십 테이블) 동시 사용

## SSE 반영 지연 측정
서버 기동 후, 관리자 토큰으로 SSE를 열어 두고 주문을 발생시켜 수신까지의 시간을 측정한다.
```bash
B=http://127.0.0.1:8000
AT=$(curl -s $B/api/admin/login -H 'Content-Type: application/json' \
  -d '{"store_id":"store001","username":"admin","password":"admin1234"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 터미널 1: 스트림 구독 (order_created 수신 시각 출력)
curl -sN "$B/api/admin/stream?token=$AT" &

# 터미널 2: 테이블 주문 생성
TT=$(curl -s $B/api/table/auth -H 'Content-Type: application/json' \
  -d '{"store_id":"store001","table_number":"T2","password":"0000"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
MID=$(curl -s $B/api/menu -H "Authorization: Bearer $TT" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['categories'][0]['menus'][0]['id'])")
curl -s $B/api/orders -H "Authorization: Bearer $TT" -H 'Content-Type: application/json' \
  -d "{\"items\":[{\"menu_id\":$MID,\"quantity\":1}]}" >/dev/null
# 터미널 1의 order_created 수신이 즉시(<2초) 나타나는지 확인
```
- **관측 결과(개발 스모크)**: `order_created`가 약 0.02초 내 수신 — 목표 2초 대비 충분.

## 참고
- 인메모리 SSE 브로커와 SQLite는 단일 인스턴스 소규모 운영을 전제한다.
- 다중 인스턴스/대규모 트래픽이 필요해지면 브로커(예: Redis pub/sub)와 DB를
  교체해야 하며, 이는 현재 MVP 범위 밖이다.
