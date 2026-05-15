## Context

신규 프로젝트. 기존 코드베이스 없음. Day 2 학습 목표 기준으로 FastAPI + Vanilla JS 스택을 사용하며, 로컬 개발 단순성과 Vercel 배포 표준을 동시에 달성해야 함. 팀 최대 5명, 동시 접속 50명 이하 가정.

## Goals / Non-Goals

**Goals:**
- API 18개 + 화면 9종 완전 동작하는 MVP 완성
- 로컬(SQLite) ↔ 운영(Neon) `DATABASE_URL` 환경변수 단일 전환
- Vercel 배포 시 FE(정적) + BE(Serverless Functions) 한 레포로 배포
- JWT + bcrypt + 권한 미들웨어로 보안 기준선 충족
- 모바일 반응형 (Tailwind breakpoint 768px/1024px)

**Non-Goals:**
- WebSocket 실시간, 이메일 알림, 파일 업로드, 전문 검색
- pytest/jest 자동화 테스트 (수동 동작 확인만)
- JWT refresh token, 다국어, 권한 세분화 (페이지별)

## Decisions

### 1. 프로젝트 구조 — 모노레포 (단일 레포)
`/api` (FastAPI Serverless) + `/frontend` (정적 HTML/JS/CSS) + `vercel.json`으로 FE+BE를 한 Vercel 프로젝트로 배포.
- **대안**: 별도 레포 분리 → Vercel 프로젝트 2개 필요, CORS 설정 복잡
- **이유**: 배포 단순성, 학습 목표 우선

### 2. 백엔드 — FastAPI + SQLAlchemy + Alembic
- SQLAlchemy 2.x (async) + Alembic 마이그레이션으로 SQLite/PostgreSQL 양쪽 호환
- `python-jose` JWT, `passlib[bcrypt]` 비밀번호 해시
- Pydantic v2 request/response 모델
- **대안**: Tortoise ORM → async 지원 좋으나 학습 난이도 높음

### 3. DB 스키마 — users.team_id (1인 1팀)
결정 #1: `users.team_id FK→teams NULL`. 1인 1팀 제약으로 멤버십 테이블 불필요.
- **트레이드오프**: 팀 이탈/재합류 구현이 단순해지나, 복수 팀 참여 불가 (MVP 범위 외)

### 4. tasks.assignee_id (nullable)
결정 #4: `creator_id` ≠ `assignee_id`. 내 태스크 = `WHERE assignee_id = current_user_id`.
- 미할당(`NULL`) 카드는 누구나 가져갈 수 있음

### 5. 채팅 폴링 — since= 증분 방식
`GET /teams/{id}/messages?since=<ISO시각>` 로 마지막 수신 시각 이후 메시지만 가져옴.
- **대안**: WebSocket → 범위 외 명시
- **대안**: 전체 재조회 → 트래픽 낭비, 메시지 누락 위험
- `messages(team_id, created_at)` 복합 인덱스로 since= 쿼리 O(log n)

### 6. PATCH /tasks/{id}/status 분리 (결정 #3)
드래그 상태 변경과 제목/담당자 수정을 별도 엔드포인트로 분리.
- `PATCH /tasks/{id}/status` — 드래그 전용 (status 필드만)
- `PUT /tasks/{id}` — 제목·assignee 수정

### 7. 로그아웃 stateless (결정 #5)
JWT 블랙리스트 없음. 클라이언트가 localStorage 토큰 삭제. 서버는 200만 반환.
- **트레이드오프**: 만료 전(24h) 탈취 토큰 강제 무효화 불가 — MVP 범위에서 감수

### 8. 프론트엔드 — MPA (Multi-Page Application)
각 화면을 별도 HTML 파일로 구성. 라우팅은 `location.href` 이동.
- `api.js` — fetch 래퍼, JWT 헤더 자동 첨부, 401 interceptor
- `auth.js` — localStorage 토큰 관리
- **대안**: SPA (history API) → 복잡도 증가, 범위 외

### 9. Tailwind CSS — CDN Play 방식 (로컬) / CLI 빌드 (운영)
- 로컬 개발: Tailwind CDN `<script>` 태그로 빠른 시작
- 운영 배포: `tailwindcss` CLI로 purge된 CSS 빌드 → Vercel 정적 파일 포함
- **이유**: 로컬 개발 속도 vs 운영 성능 균형

### 11. 순환 FK 해결 — use_alter=True (이슈 #1)
`users.team_id → teams` + `teams.owner_id → users` 상호 참조로 Alembic이 CREATE TABLE 순서를 결정하지 못함.
해결: `teams.owner_id` FK를 `use_alter=True`로 선언 → Alembic이 ALTER TABLE로 후처리.
```python
owner_id = Column(Integer, ForeignKey('users.id', use_alter=True, name='fk_teams_owner_id'))
```
CREATE 순서: `users` (team_id 없이) → `teams` (owner_id ALTER) → `users.team_id` FK 추가.

### 12. users.team_joined_at 컬럼 추가 (이슈 #2)
`GET /teams/{id}/members` 응답의 `joined_at` 필드를 위해 `users.team_joined_at TIMESTAMP NULL` 컬럼 추가.
- 팀 생성 시: `team_joined_at = now()`
- 초대코드 합류 시: `team_joined_at = now()`
- 팀 탈퇴 시: `team_joined_at = NULL`
- `users.created_at` 재활용은 계정 생성 시각과 혼동되므로 사용하지 않음.

### 13. CORS 정책 (이슈 #5)
환경변수 `CORS_ORIGINS`로 허용 도메인을 관리.
- 로컬 개발: `http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000`
- 운영: Vercel 배포 후 실제 도메인 추가 (예: `https://kosta-taskflow.vercel.app`)
- `.env.example`에 `CORS_ORIGINS=http://localhost:5500` 기본값 포함.

### 14. 에러 코드 구분 — UNAUTHORIZED vs TOKEN_EXPIRED (이슈 #7)
- JWT **없음** (Authorization 헤더 미포함): `401 UNAUTHORIZED`
- JWT **만료** (exp 초과): `401 TOKEN_EXPIRED`
- 클라이언트 interceptor는 두 코드 모두 localStorage 삭제 + /login redirect로 처리.

### 10. 에러 응답 표준
모든 4xx/5xx: `{ "error": { "code": "SCREAMING_SNAKE", "message": "한국어" } }`
클라이언트는 `error.code`로 분기, `error.message`를 토스트에 그대로 표시.

## Risks / Trade-offs

- **SQLite → PostgreSQL 타입 차이** → SQLAlchemy ORM 추상화로 완화. `created_at` 기본값 등 dialect-specific 코드 금지.
- **Vercel Serverless cold start** → FastAPI 경량 구조 유지, 불필요한 import 최소화.
- **폴링 5초 × 동시 50명** → 초당 10 req/s. Neon Free 연결 풀(max 10) 초과 가능성 → SQLAlchemy connection pool 설정 필요.
- **localStorage JWT 탈취** → MVP 범위에서 감수. httpOnly cookie는 Day 2 범위 외.
- **Vanilla JS 상태 관리 복잡성** → 전역 변수 + 이벤트 방식으로 단순화. SPA 미사용.

## Migration Plan

1. 로컬: `uvicorn api.main:app --reload` + `python -m http.server` (또는 live-server)
2. 운영: GitHub `main` push → Vercel 자동 배포 → `DATABASE_URL` 환경변수로 Neon 연결
3. Alembic `upgrade head`는 첫 배포 시 Vercel Build Command에 포함

## Open Questions

- ~~Vercel Serverless Functions Python 런타임 버전~~ → **Python 3.12** 사용 (`vercel.json`에 `"runtime": "python3.12"` 명시)
- ~~Neon Free 플랜 연결 수 제한~~ → **NullPool** 사용 (`create_engine(..., poolclass=NullPool)`). Serverless 환경에서 연결을 요청마다 생성/해제하여 연결 풀 고갈 방지.
