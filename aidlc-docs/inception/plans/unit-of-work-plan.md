# Unit of Work Plan (분해 계획)

/ Written at (KST): 2026-09-07 13:20 /

## 목적
단일 배포 서비스(FastAPI 서버 하나)를 construction 개발 루프에서 어떻게 나눌지 확정한다.

## 분해 결정 (대화형 확정)
### Q1 — 유닛 분해
A) **2개 유닛: Backend → Frontend** (권장)
B) 1개 유닛(앱 전체 한번에)

[Answer]: A (대화형 확정 2026-09-07) — Unit1 Backend 완성·검증 후 Unit2 Frontend. 배포는 단일 서버 유지.

## 산출물 체크리스트 (Part 2에서 생성)
- [x] `application-design/unit-of-work.md` — 유닛 정의·책임 + 코드 조직 전략(Greenfield)
- [x] `application-design/unit-of-work-dependency.md` — 유닛 의존성 매트릭스
- [x] `application-design/unit-of-work-story-map.md` — 요구사항(스토리 대체)→유닛 매핑
- [x] 유닛 경계·의존성 검증
- [x] 모든 요구사항이 유닛에 배정되었는지 확인

## 분해 개요
- **배포 단위**: 단일 FastAPI 서비스(1 프로세스). API + 정적 프런트 동시 서빙.
- **개발 유닛(순차)**:
  - **U1 Backend** — models/schemas/repositories/services/routers/core + 핵심 로직 단위 테스트. 완료 시 API가 계약대로 동작.
  - **U2 Frontend** — 고객 앱 + 관리자 앱(정적). 확정된 API에 결합.
- **construction 루프**: U1(Code Generation+검증) → U2(Code Generation) → Build & Test.
