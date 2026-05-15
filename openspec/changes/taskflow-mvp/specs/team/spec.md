## ADDED Requirements

### Requirement: 팀 생성
시스템은 팀 이름(1-30자)으로 팀을 생성하고 초대코드를 자동 발급해야 한다.
- 생성자는 자동으로 owner_id가 됨
- 초대코드: `^[A-Z]{4}-[0-9]{4}$` 형식 (예: FRNT-2026), 서버 자동 생성
- 팀 생성 즉시 `users.team_id` 업데이트 (1인 1팀)
- 이미 팀에 속한 사용자는 팀 생성 불가 (409)

#### Scenario: 정상 팀 생성
- **WHEN** team_id가 NULL인 사용자가 유효한 팀 이름으로 POST /teams 호출
- **THEN** HTTP 201, `{ id, name, invite_code, owner_id, created_at }` 반환
- **THEN** users.team_id = 생성된 teams.id 로 업데이트

#### Scenario: 이미 팀 소속
- **WHEN** team_id가 NULL이 아닌 사용자가 POST /teams 호출
- **THEN** HTTP 409, `{ error: { code: "ALREADY_IN_TEAM" } }` 반환

#### Scenario: 팀 이름 빈칸
- **WHEN** 빈 문자열 또는 공백만으로 팀 이름 전달
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR" } }` 반환

### Requirement: 초대코드로 팀 합류
시스템은 초대코드를 검증하고 사용자를 해당 팀에 합류시켜야 한다.
- 형식 검증: `^[A-Z]{4}-[0-9]{4}$` (클라이언트 + 서버)
- 존재하지 않는 코드: 404 NOT_FOUND
- 이미 다른 팀 소속: 409 ALREADY_IN_TEAM
- 성공 시 응답에 팀 정보(미리보기용) 포함

#### Scenario: 정상 합류
- **WHEN** 미소속 사용자가 유효한 초대코드로 POST /teams/join 호출
- **THEN** HTTP 200, `{ team: { id, name, member_count }, redirect: "/teams/{id}" }` 반환
- **THEN** users.team_id = teams.id 로 업데이트

#### Scenario: 잘못된 초대코드 형식
- **WHEN** `abcd1234` 처럼 형식 위반 코드 전달
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "형식이 올바르지 않습니다" } }` 반환

#### Scenario: 존재하지 않는 코드
- **WHEN** 형식은 맞지만 존재하지 않는 코드(예: XXXX-9999) 전달
- **THEN** HTTP 404, `{ error: { code: "NOT_FOUND", message: "해당 초대코드를 찾을 수 없습니다" } }` 반환

#### Scenario: 이미 팀 소속
- **WHEN** 이미 팀에 속한 사용자가 다른 팀 초대코드로 합류 시도
- **THEN** HTTP 409, `{ error: { code: "ALREADY_IN_TEAM", message: "이미 다른 팀에 소속되어 있습니다" } }` 반환

### Requirement: 팀 정보 및 멤버 목록 조회
팀 멤버만 해당 팀 정보와 멤버 목록에 접근할 수 있어야 한다.
- owner는 ★ 표시, 나머지는 member
- 비멤버 접근: 403 FORBIDDEN

#### Scenario: 멤버의 팀 정보 조회
- **WHEN** 해당 팀 멤버가 GET /teams/{id} 호출
- **THEN** HTTP 200, `{ id, name, invite_code, owner_id, member_count }` 반환

#### Scenario: 멤버 목록 조회
- **WHEN** 해당 팀 멤버가 GET /teams/{id}/members 호출
- **THEN** HTTP 200, 멤버 배열 반환 (각 항목: `{ id, email, role: "owner"|"member", joined_at }`)

#### Scenario: 비멤버 접근
- **WHEN** 다른 팀 소속 사용자가 GET /teams/{id}/* 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN", message: "이 팀의 멤버가 아닙니다" } }` 반환

### Requirement: 권한 모델
시스템은 owner와 member를 구분하고 역할별 권한을 강제해야 한다.
- owner: 팀 생성자, tasks DELETE 오버라이드 가능 (타인 카드도 삭제)
- member: 본인 카드/메시지만 DELETE
- 비멤버: 모든 /teams/{id}/* API → 403

#### Scenario: 비멤버 쓰기 시도
- **WHEN** 비멤버가 POST/PATCH/DELETE /teams/{id}/* 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN" } }` 반환

#### Scenario: 미인증 접근
- **WHEN** JWT 없이 인증 필요 API 호출
- **THEN** HTTP 401, `{ error: { code: "TOKEN_EXPIRED" } }` 반환
