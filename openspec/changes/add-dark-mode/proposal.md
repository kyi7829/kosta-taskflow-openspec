## Why

밝은 화면을 오래 사용할 때 눈의 피로를 줄이고 야간 환경에서 편의성을 높이기 위해 다크모드 토글을 추가한다. 모든 화면에 일관된 다크 테마를 적용하고 사용자의 선택을 유지한다.

## What Changes

- `frontend/js/darkmode.js` 신규 생성 — 토글 로직, `<html>` 클래스 제어, localStorage 저장
- HTML 5개 파일 수정:
  - `tailwind.config` 인라인 설정 추가 (`darkMode: 'class'`)
  - 모든 UI 요소에 `dark:` 클래스 추가
  - 칸반/채팅/팀선택: 헤더 우측에 🌙/☀️ 토글 버튼 추가
  - 로그인/회원가입: 우상단 고정(fixed) 토글 버튼 추가

## Capabilities

### New Capabilities

- `dark-mode`: 다크모드 토글 — 활성화/비활성화, localStorage 유지, 페이지 간 상태 공유

### Modified Capabilities

- `kanban`: 헤더에 토글 버튼 UI 추가 (요구사항 변경 없음, 구현 사항만)
- `chat`: 헤더에 토글 버튼 UI 추가 (요구사항 변경 없음, 구현 사항만)

## Impact

- **Frontend**: HTML 5개, JS 1개 신규, tailwind.config 인라인 설정
- **Backend**: 없음 (순수 프론트엔드 변경)
- **API**: 없음
- **DB**: 없음
