## Why

소규모 팀(3-5인)이 칸반 보드와 실시간 채팅을 한 화면에서 함께 사용할 수 있는 MVP가 없음. 기존 도구는 과하거나 분산되어 있어 빠른 합의와 진행 추적이 어려움.

## What Changes

- 이메일/비밀번호 기반 회원가입·로그인 (JWT 24h, bcrypt 해시)
- 팀 생성 + 초대코드(XXXX-9999 형식) 발급·합류 시스템 (1인 1팀)
- TODO/DOING/DONE 3컬럼 칸반 보드 (드래그 상태 이동, assignee 지정)
- 팀 단위 채팅 (5초 폴링, `since=` 증분 조회, 1000자 제한)
- Vercel 배포 (FE + FastAPI Serverless) + Vercel Storage Neon (운영 DB)
- 로컬 개발: SQLite / 운영: Neon — `DATABASE_URL` 환경변수 하나로 전환

## Capabilities

### New Capabilities

- `auth`: 회원가입, 로그인, JWT 발급·검증, 로그아웃(stateless), 현재 사용자 조회
- `team`: 팀 생성, 초대코드 발급·합류, 팀 정보 조회, 멤버 목록, 팀 떠나기
- `kanban`: 태스크 CRUD, TODO/DOING/DONE 상태 전환(PATCH 분리), assignee(nullable), 필터(@me/미할당)
- `chat`: 팀 채팅 메시지 송수신, 5초 폴링(`since=`), 1000자 제한, 본인 메시지 삭제
- `deployment`: Vercel(FE+BE) + Neon 배포, 환경 분리(로컬 SQLite / 운영 Neon)

### Modified Capabilities

(없음 — 신규 프로젝트)

## Impact

- **Backend**: FastAPI, SQLAlchemy, python-jose, bcrypt, Pydantic — API 18개 구현
- **Frontend**: Vanilla JS (ES6+), Tailwind CSS — 9개 화면, HTML5 Drag & Drop, fetch API
- **DB**: 4테이블 (users, teams, tasks, messages) + 인덱스 4개
- **Infra**: Vercel Serverless Functions, Neon PostgreSQL (Free Tier), GitHub main push 자동 배포
- **Out of Scope**: 알림, 파일첨부, 전문검색, 권한세분화, 다국어, WebSocket, 자동화테스트
