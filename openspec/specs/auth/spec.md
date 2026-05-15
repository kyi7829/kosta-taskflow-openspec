# auth

## Purpose

이메일 + 비밀번호 기반 인증 및 JWT 발급/검증을 담당한다.

## Requirements

### Requirement: 회원가입
시스템은 이메일 + 비밀번호로 신규 계정을 생성하고 JWT를 즉시 발급해야 한다.
- 이메일: RFC 5322 형식 검증 (클라이언트 + 서버 양쪽)
- 비밀번호: 8자 이상, bcrypt 해시 저장 (평문 저장 금지)
- 중복 이메일: 409 EMAIL_TAKEN 반환
- 성공 시 HTTP 201 + JWT 반환

#### Scenario: 정상 가입
- **WHEN** 유효한 이메일과 8자 이상 비밀번호로 POST /auth/signup 호출
- **THEN** HTTP 201, `{ token, user: { id, email, team_id: null } }` 반환

#### Scenario: 이메일 중복
- **WHEN** 이미 가입된 이메일로 POST /auth/signup 호출
- **THEN** HTTP 409, `{ error: { code: "EMAIL_TAKEN", message: "이미 가입된 이메일입니다" } }` 반환

#### Scenario: 이메일 형식 오류
- **WHEN** `user@invalid` 처럼 형식이 잘못된 이메일로 호출
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR" } }` 반환

#### Scenario: 비밀번호 7자 이하
- **WHEN** 7자 이하 비밀번호로 호출
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "8자 이상 입력해주세요" } }` 반환

### Requirement: 로그인
시스템은 이메일 + 비밀번호를 검증하고 JWT(24h)를 발급해야 한다.
- 이메일 존재 여부를 에러 메시지에서 노출하면 안 됨 (보안)
- 성공 응답에 `user.team_id` 포함 (NULL이면 팀 선택 화면으로 분기)

#### Scenario: 정상 로그인
- **WHEN** 등록된 이메일과 올바른 비밀번호로 POST /auth/login 호출
- **THEN** HTTP 200, `{ token: "eyJ...", user: { id, email, team_id } }` 반환

#### Scenario: 비밀번호 불일치
- **WHEN** 등록된 이메일이지만 틀린 비밀번호로 호출
- **THEN** HTTP 401, `{ error: { code: "INVALID_CREDENTIALS", message: "이메일 또는 비밀번호가 일치하지 않습니다" } }` 반환

#### Scenario: 미등록 이메일
- **WHEN** 존재하지 않는 이메일로 호출
- **THEN** HTTP 401, 이메일 존재 여부를 알 수 없는 동일 메시지 `INVALID_CREDENTIALS` 반환

### Requirement: 로그아웃 (stateless)
시스템은 POST /auth/logout 요청에 HTTP 200만 반환해야 한다. JWT 블랙리스트를 유지하지 않는다.
클라이언트는 `localStorage.removeItem('token')` 으로 토큰을 폐기한다.

#### Scenario: 로그아웃 요청
- **WHEN** 유효한 JWT Bearer 헤더로 POST /auth/logout 호출
- **THEN** HTTP 200, `{}` 반환

#### Scenario: 로그아웃 후 토큰 사용
- **WHEN** 로그아웃 후 만료되지 않은 토큰으로 API 호출
- **THEN** 서버는 여전히 200 처리 (블랙리스트 없음) — 클라이언트 책임

### Requirement: 현재 사용자 조회
JWT에서 사용자 정보를 조회하여 반환해야 한다.

#### Scenario: 정상 조회
- **WHEN** 유효한 JWT로 GET /auth/me 호출
- **THEN** HTTP 200, `{ id, email, team_id }` 반환

#### Scenario: JWT 만료
- **WHEN** 유효한 형식이지만 만료된 JWT로 API 호출
- **THEN** HTTP 401, `{ error: { code: "TOKEN_EXPIRED", message: "인증이 만료되었습니다" } }` 반환
- **THEN** 클라이언트는 localStorage 토큰 삭제 후 /login으로 redirect

#### Scenario: JWT 없음 (미인증)
- **WHEN** Authorization 헤더 없이 인증 필요 API 호출
- **THEN** HTTP 401, `{ error: { code: "UNAUTHORIZED", message: "로그인이 필요합니다" } }` 반환
