## 1. 프로젝트 초기 설정

- [ ] 1.1 레포 구조 생성: `/api`, `/frontend`, `vercel.json`, `.env.example`
- [ ] 1.2 Python 가상환경 + `requirements.txt` (fastapi, uvicorn, sqlalchemy, alembic, python-jose, passlib[bcrypt], pydantic)
- [ ] 1.3 `api/main.py` FastAPI 앱 기본 구조 (CORS 설정, 에러 핸들러 등록)
- [ ] 1.4 SQLAlchemy Base + `DATABASE_URL` 환경변수 로딩 (SQLite 기본값)
- [ ] 1.5 Alembic 초기화 + env.py 설정
- [ ] 1.6 Tailwind CSS CDN 포함한 기본 HTML 레이아웃 템플릿

## 2. DB 스키마 & 마이그레이션

- [ ] 2.1 `users` 모델: id, email(UNIQUE), password_hash, team_id(FK→teams NULL), team_joined_at(TIMESTAMP NULL), created_at
- [ ] 2.2 `teams` 모델: id, name(1-30자), invite_code(UNIQUE), owner_id(FK→users, use_alter=True), created_at — 순환FK는 ALTER TABLE로 후처리
- [ ] 2.3 `tasks` 모델: id, team_id(FK), title(1-100자), status(TODO/DOING/DONE), creator_id(FK), assignee_id(FK NULL), created_at
- [ ] 2.4 `messages` 모델: id, team_id(FK), user_id(FK), content(1-1000자), created_at
- [ ] 2.5 인덱스 4개 생성: `tasks(team_id,created_at)`, `messages(team_id,created_at)`, `teams(invite_code)`, `users(team_id)`
- [ ] 2.6 Alembic 최초 마이그레이션 생성 + `upgrade head` 검증 (순환FK: users 먼저 생성 → teams → ALTER로 owner_id FK 추가)

## 3. 인증 API (Auth 4개)

- [ ] 3.1 JWT 유틸리티: 발급(`create_access_token`), 검증(`get_current_user` 의존성), 24h 만료, 미인증 → UNAUTHORIZED / 만료 → TOKEN_EXPIRED 구분
- [ ] 3.2 `POST /auth/signup`: 이메일 중복 체크, bcrypt 해시, 201 + JWT 반환
- [ ] 3.3 `POST /auth/login`: bcrypt 검증, INVALID_CREDENTIALS(이메일 존재 여부 미노출), 200 + JWT
- [ ] 3.4 `POST /auth/logout`: stateless, 200 반환
- [ ] 3.5 `GET /auth/me`: JWT에서 사용자 정보 반환
- [ ] 3.6 에러 응답 표준 미들웨어: 모든 4xx/5xx → `{ error: { code, message } }`
- [ ] 3.7 `CORS_ORIGINS` 환경변수 로딩, `.env.example`에 `http://localhost:5500` 기본값 포함

## 4. 팀 API (Team 5개)

- [ ] 4.1 팀 멤버십 검증 의존성: JWT + `users.team_id == path.team_id` 확인, 비멤버 → 403
- [ ] 4.2 `POST /teams`: 팀 생성, invite_code 자동 생성(`XXXX-9999`), users.team_id 업데이트
- [ ] 4.3 `POST /teams/join`: 초대코드 형식·존재 검증, users.team_id + team_joined_at 업데이트, 팀 미리보기 반환
- [ ] 4.4 `GET /teams/{id}`: 팀 정보 조회
- [ ] 4.5 `GET /teams/{id}/members`: 멤버 목록 (role: owner/member 구분, joined_at = team_joined_at)
- [ ] 4.6 `DELETE /teams/{id}/leave`: member 전용, owner 시도 시 403 OWNER_MUST_TRANSFER, 성공 시 team_id·team_joined_at = NULL
- [ ] 4.7 `PATCH /teams/{id}/transfer-owner`: owner만 호출, 대상 멤버에게 소유권 이전, teams.owner_id 업데이트
- [ ] 4.8 `DELETE /teams/{id}`: owner만 호출, 팀 삭제 (tasks·messages CASCADE, 모든 멤버 team_id = NULL)

## 5. 칸반 API (Task 6개)

- [ ] 5.1 `GET /teams/{id}/tasks`: filter(@me/unassigned/전체), created_at DESC 정렬
- [ ] 5.2 `POST /teams/{id}/tasks`: 태스크 생성, status=TODO, creator_id=현재사용자
- [ ] 5.3 `GET /tasks/{id}`: 단건 조회
- [ ] 5.4 `PUT /tasks/{id}`: 제목·assignee_id 수정
- [ ] 5.5 `PATCH /tasks/{id}/status`: status 변경 전용, 유효값(TODO/DOING/DONE) 검증
- [ ] 5.6 `DELETE /tasks/{id}`: creator OR team owner 권한 검증 → 204, 그 외 → 403

## 6. 채팅 API (Chat 3개)

- [ ] 6.1 `GET /teams/{id}/messages`: `since=` 파라미터 증분 조회, 없으면 최근 50개
- [ ] 6.2 `POST /teams/{id}/messages`: content 1000자 이내 검증, 201 + 메시지 반환
- [ ] 6.3 `DELETE /messages/{id}`: 본인 메시지만 삭제, 타인 → 403 NOT_OWNER

## 7. 프론트엔드 공통

- [ ] 7.1 `api.js`: fetch 래퍼 (JWT Authorization 헤더 자동 첨부, 401 → localStorage 삭제 + /login redirect)
- [ ] 7.2 `auth.js`: localStorage 토큰 저장·읽기·삭제, 페이지 진입 시 토큰 검사
- [ ] 7.3 공통 에러 토스트 컴포넌트: `error.message` 한국어 표시
- [ ] 7.4 Tailwind 반응형 breakpoint 설정 (768px 모바일, 1024px 데스크탑)
- [ ] 7.5 `tailwind.config.js` + `package.json` build 스크립트 설정 (`tailwindcss -i input.css -o dist/output.css --minify`)

## 8. 화면 구현 (9개)

- [ ] 8.1 회원가입 화면: 이메일·비밀번호 입력, 클라이언트 validation, 처리 중 상태
- [ ] 8.2 로그인 화면: 인증, team_id 검사 → NULL이면 팀선택, 있으면 칸반으로 redirect
- [ ] 8.3 팀 선택 화면: 팀 만들기 + 초대코드 합류 (team_id=NULL 사용자 강제 진입)
- [ ] 8.3a Owner 탈퇴 confirm 다이얼로그: "팀장 위임" / "팀 삭제" 선택 → 각 흐름 분기
- [ ] 8.3b 팀장 위임 화면: 멤버 목록에서 1명 선택 → PATCH /teams/{id}/transfer-owner → 성공 후 자동 탈퇴
- [ ] 8.4 팀 만들기 → 초대코드 발급 표시 화면
- [ ] 8.5 칸반 화면: 3컬럼 TODO/DOING/DONE, @me/미할당 필터, + 버튼 인라인 입력
- [ ] 8.6 칸반 드래그 & 드롭: HTML5 native drag API, drop 시 PATCH /tasks/{id}/status
- [ ] 8.7 태스크 상세·수정 모달: 제목·상태·assignee 수정, 삭제 권한별 버튼 표시
- [ ] 8.8 채팅 화면: 말풍선 UI, 5초 setInterval 폴링(`since=`), 1000자 카운터
- [ ] 8.9 팀 멤버 목록 패널: owner(★)/member 구분, 모바일 햄버거 메뉴

## 9. 모바일 반응형

- [ ] 9.1 칸반 모바일: 1컬럼 + 탭 인디케이터 + 좌우 스와이프 (768px 미만)
- [ ] 9.2 채팅 모바일: 풀스크린, visualViewport API로 키보드 올라올 때 영역 축소
- [ ] 9.3 햄버거 메뉴 슬라이드 (칸반·채팅·멤버·로그아웃)

## 10. Vercel 배포

- [ ] 10.0 Vercel CLI 설치: `npm i -g vercel` + `vercel login`
- [ ] 10.1 `vercel.json`: API routes (`/api/*` → FastAPI, runtime: python3.12), 정적 파일 설정
- [ ] 10.2 Vercel 프로젝트 생성 (`vercel link`) + `DATABASE_URL`, `CORS_ORIGINS`, `JWT_SECRET` 환경변수 등록 (Neon)
- [ ] 10.3 Build Command에 `tailwindcss` CLI 빌드 + `alembic upgrade head` 포함
- [ ] 10.4 배포 후 전체 기능 5종 동작 확인 (회원가입→팀→칸반→채팅)
