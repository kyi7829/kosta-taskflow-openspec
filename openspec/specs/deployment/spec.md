# deployment

## Purpose

로컬 개발 환경 설정, Vercel 배포 파이프라인, 반응형 UI 지원을 담당한다.

## Requirements

### Requirement: 로컬 개발 환경
시스템은 `DATABASE_URL` 환경변수 하나로 로컬(SQLite)과 운영(Neon PostgreSQL)을 전환할 수 있어야 한다.

#### Scenario: 로컬 실행
- **WHEN** `DATABASE_URL=sqlite:///./taskflow.db` 로 `uvicorn api.main:app --reload` 실행
- **THEN** FastAPI 서버가 SQLite로 동작하며 API 18개가 모두 응답

#### Scenario: 환경변수 미설정
- **WHEN** DATABASE_URL 없이 서버 실행
- **THEN** SQLite 기본값(`sqlite:///./taskflow.db`)으로 폴백

### Requirement: Vercel 배포
시스템은 GitHub main 브랜치 push 시 Vercel에 자동 배포되어야 한다.
- FE(정적 파일) + BE(FastAPI Serverless Functions) 단일 레포 배포
- DB: Vercel Storage Neon (Pooled connection 자동 주입)
- `DATABASE_URL` 환경변수는 Vercel 프로젝트 설정에 등록

#### Scenario: 운영 배포
- **WHEN** main 브랜치에 push
- **THEN** Vercel이 자동으로 FE + BE 빌드 및 배포 완료 (5분 이내)

#### Scenario: DB 마이그레이션
- **WHEN** 배포 Build Command 실행
- **THEN** `alembic upgrade head` 실행으로 Neon DB 스키마 최신 상태 유지

### Requirement: 반응형 UI
프론트엔드는 Tailwind CSS breakpoint 기준 반응형을 지원해야 한다.
- `< 768px`: 모바일 (1컬럼 칸반 스와이프, 햄버거 메뉴)
- `768px ~ 1024px`: 태블릿 (헤더 통합)
- `> 1024px`: 데스크탑 (사이드 패널, 3컬럼 칸반)

#### Scenario: 모바일 칸반
- **WHEN** viewport width < 768px
- **THEN** 칸반이 1컬럼으로 표시되며 좌우 스와이프로 TODO/DOING/DONE 전환

#### Scenario: 데스크탑 칸반
- **WHEN** viewport width > 1024px
- **THEN** TODO/DOING/DONE 3컬럼이 나란히 표시
