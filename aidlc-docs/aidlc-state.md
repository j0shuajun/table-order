# AI-DLC State Tracking

## Project Information
- **Project Type**: Greenfield
- **Start Date**: 2026-09-07T01:52:11Z
- **Current Stage**: CONSTRUCTION - U2 Frontend Code Generation 완료 (완료 게이트 대기)
- **Construction Gate Mode**: 단계별 승인 (유닛/단계마다 사용자 승인)
- **Key Constraint**: Working MVP within 4-5 hours today. Prioritize functional completeness over non-functional perfection.

## Workspace State
- **Existing Code**: No
- **Reverse Engineering Needed**: No
- **Programming Languages**: None yet (to be decided)
- **Build System**: None yet
- **Project Structure**: Empty (greenfield)
- **Workspace Root**: /Users/joshua/Desktop/aidlc-workshop/table-order

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Stage Progress
### 🔵 INCEPTION PHASE
- [x] Workspace Detection
- [x] Requirements Analysis
- [x] User Stories (SKIPPED — 사용자 확정, 오늘 MVP 체험 범위에서 불필요)
- [x] Workflow Planning (APPROVED)
- [x] Application Design (APPROVED)
- [x] Units Generation (APPROVED) — Part1 Planning [x], Part2 Generation [x]. Units: U1 Backend → U2 Frontend (single deployable service)

### 🟢 CONSTRUCTION PHASE
> **실행 규약** (unit-of-work.md "구현 실행 규약" 참조): 유닛별 `feat/<unit>` 브랜치 → plan(docs/tasks/) → TDD 논리 슬라이스 즉시 로컬 커밋 → 검증 → result → docs/guide 동기화 → main으로 `--no-ff` 로컬 병합. 원격 없음(push/PR 생략). pre-commit: black/isort/ruff.
- [ ] Functional Design (per-unit, TBD)
- [ ] NFR Requirements (per-unit, TBD)
- [ ] NFR Design (per-unit, TBD)
- [ ] Infrastructure Design (per-unit, TBD)
- [x] Code Generation — U1 Backend (Part 1 Planning [x APPROVED], Part 2 Generation [x]) — 31 tests pass, uvicorn+SSE 런타임 스모크 확인, feat/u1-backend → main `--no-ff` 병합
- [x] Code Generation — U2 Frontend (Part 1 Planning [x APPROVED], Part 2 Generation [x]) — 고객 앱/관리자 앱 3커밋(공용 셸+api.js+css, 고객 앱, 관리자 앱), uvicorn 실서버 기능 스모크(로그인→주문→상태변경→완료→내역→메뉴) 확인, 완료 게이트 대기
- [ ] Build and Test

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Resiliency Baseline | No | Requirements Analysis |
| Property-Based Testing | No | Requirements Analysis |

## Technical Decisions (from Requirements Analysis)
- **Backend**: Python FastAPI
- **Frontend**: 순수 HTML/CSS/Vanilla JS (no build step), served separately; BE/FE는 사전 정의한 REST/SSE API 규격을 준수
- **Data store**: SQLite (file-based, persistent)
- **Realtime**: Server-Sent Events (SSE)
- **Admin auth**: JWT 16h session + bcrypt password hashing (login attempt throttling out of scope)
- **Seed data**: auto-seed on server start (store001 "데모 식당", admin/admin1234, tables T1-T6 pw 0000, 3 categories, ~10 menus)
- **Serving**: single FastAPI server serves REST/SSE API + static frontend (single port, no CORS)
- **Table (customer) auth**: same JWT mechanism, role=table claim, localStorage, auto-login
- **Multi-store**: single-store demo fixed (store_id in schema, one seed store)
- **Customer order history UI**: simple full list (no pagination/infinite scroll)
- **Order number format**: `YYYYMMDD-HHMM-####` (e.g. 20260907-1526-0001)
- **Order statuses**: pending / preparing / completed
