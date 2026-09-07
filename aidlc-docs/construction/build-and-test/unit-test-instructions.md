# 단위 테스트 실행

단위/서비스 테스트는 `pytest`로 실행한다. 테스트는 프로덕션 모듈 구조를 미러링해
`tests/app/...`에 위치한다.

## 전체 실행
```bash
source .venv/bin/activate
python -m pytest -q
```

## 결과 기준
- **기대**: 31개 통과, 0 실패
- **경고**: httpx/starlette Deprecation, JWT 16바이트 키 관련 `InsecureKeyLengthWarning`
  3건은 로컬 기본값에서 예상되는 것으로 실패가 아니다(운영 시 32바이트 이상 키로 해소).
- **리포트 위치**: 콘솔 출력(별도 리포트 파일 없음)

## 테스트 구성(무엇을 검증하나)
| 파일 | 대상 |
| --- | --- |
| `tests/app/core/test_security.py` | bcrypt 해시, JWT 발급/검증(만료·서명 오류 포함) |
| `tests/app/core/test_models.py` | ORM 매핑/관계 |
| `tests/app/services/test_order_service.py` | 주문 생성·총액·세션 자동생성·상태변경·삭제·주문번호 |
| `tests/app/services/test_auth_service.py` | 관리자/테이블 인증, 실패 시 예외 |
| `tests/app/services/test_admin_menu_services.py` | 대시보드 요약, 세션 완료, 테이블/메뉴 관리 |
| `tests/app/api/test_api_flow.py` | 실 앱 기동(create_all+seed) 기반 API 플로우 |

## 특정 범위만 실행
```bash
python -m pytest tests/app/services -q          # 서비스 계층만
python -m pytest tests/app/api/test_api_flow.py # API 플로우만
```

## 실패 시 대응
1. 콘솔의 실패 테스트/트레이스백 확인
2. 해당 서비스·리포지토리 코드 수정
3. 좁은 범위부터 재실행 후 전체 `pytest -q`로 확인
