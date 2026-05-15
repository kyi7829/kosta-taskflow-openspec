## Context

현재 프론트엔드는 Tailwind CSS CDN을 사용하며 `dark:` 클래스가 전혀 없는 라이트 전용 UI. HTML 5개 파일 모두 인라인 스크립트 기반 MPA 구조.

## Goals / Non-Goals

**Goals:**
- 모든 화면(5개)에 다크모드 적용
- 토글 버튼 클릭으로 즉시 전환
- localStorage로 선택 유지 (새로고침/재방문 시 복원)
- 페이지 이동 시에도 모드 유지 (초기 로드 시 깜빡임 없음)

**Non-Goals:**
- OS 다크모드 자동 감지 (수동 토글만)
- 백엔드 저장 (localStorage로 충분)
- 커스텀 컬러 테마 (Tailwind 기본 dark 팔레트만 사용)

## Decisions

### 1. Tailwind `darkMode: 'class'` — CDN 인라인 설정
CDN 환경에서 각 HTML에 아래를 추가:
```html
<script>tailwind.config = { darkMode: 'class' }</script>
```
빌드 없이 `dark:` 클래스가 즉시 동작. `tailwind.config.js`에도 동일하게 추가.

### 2. `<html>` 에 `dark` 클래스 토글
```javascript
document.documentElement.classList.toggle('dark')
localStorage.setItem('theme', 'dark' | 'light')
```
`<html>` 레벨에 적용해야 하위 모든 요소의 `dark:` 클래스가 활성화됨.

### 3. 깜빡임 방지 — `<head>` 최상단 인라인 스크립트
페이지 로드 시 CSS 적용 전에 `dark` 클래스를 미리 설정:
```html
<head>
  <script>
    if (localStorage.getItem('theme') === 'dark')
      document.documentElement.classList.add('dark');
  </script>
  ...
</head>
```
외부 JS 파일보다 먼저 실행되므로 깜빡임 없음.

### 4. 토글 버튼 위치
- 칸반/채팅/팀선택: 헤더 우측 (기존 user 이메일 왼쪽)
- 로그인/회원가입: `fixed top-4 right-4` 고정 버튼

### 5. 아이콘 — 이모지 사용
🌙 (다크모드 진입) / ☀️ (라이트모드 진입). 외부 아이콘 라이브러리 불필요.

## Risks / Trade-offs

- **CDN dark: 클래스 지원** → Tailwind CDN v3은 `darkMode: 'class'` 지원 확인됨. 문제없음.
- **HTML 5개 수작업 수정** → 각 파일마다 `dark:` 클래스 전수 추가 필요. 누락 시 특정 요소만 밝게 보이는 현상 발생 가능.
- **기존 `bg-gray-50` 계열 배경** → `dark:bg-gray-900`으로 매핑. 컬러 일관성 유지 필요.
