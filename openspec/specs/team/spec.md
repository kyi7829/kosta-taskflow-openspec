# team

## Purpose

팀 생성, 합류, 멤버 관리, 권한 제어를 담당한다.

## Requirements

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

### Requirement: 팀장 위임
Owner는 다른 팀 멤버에게 소유권을 이전할 수 있어야 한다.
- Owner만 호출 가능, 대상은 같은 팀 멤버여야 함
- 위임 성공 시 호출자는 member로 강등, 대상자가 owner가 됨
- `teams.owner_id` 업데이트

#### Scenario: 정상 위임
- **WHEN** owner가 같은 팀 멤버 id로 PATCH /teams/{id}/transfer-owner `{ new_owner_id }` 호출
- **THEN** HTTP 200, `{ id, name, owner_id: <new_owner_id> }` 반환

#### Scenario: 비owner 위임 시도
- **WHEN** member가 PATCH /teams/{id}/transfer-owner 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN" } }` 반환

#### Scenario: 다른 팀 멤버에게 위임 시도
- **WHEN** new_owner_id가 같은 팀 소속이 아닌 경우
- **THEN** HTTP 400, `{ error: { code: "NOT_TEAM_MEMBER" } }` 반환

### Requirement: 팀 탈퇴 (일반 멤버)
일반 멤버는 팀을 탈퇴할 수 있어야 한다. Owner는 이 엔드포인트로 탈퇴 불가.
- 탈퇴 성공 시 `users.team_id = NULL`, `users.team_joined_at = NULL`

#### Scenario: 멤버 탈퇴
- **WHEN** member가 DELETE /teams/{id}/leave 호출
- **THEN** HTTP 204, users.team_id = NULL 업데이트
- **THEN** 해당 멤버가 담당(assignee_id)인 팀 내 모든 tasks의 assignee_id = NULL로 자동 정리

#### Scenario: Owner가 탈퇴 시도
- **WHEN** owner가 DELETE /teams/{id}/leave 호출
- **THEN** HTTP 403, `{ error: { code: "OWNER_MUST_TRANSFER", message: "팀장은 위임 또는 팀 삭제 후 탈퇴할 수 있습니다" } }` 반환

### Requirement: 팀 삭제 (Owner 전용)
Owner는 팀 전체를 삭제할 수 있어야 한다. 삭제 전 클라이언트에서 confirm 다이얼로그를 표시한다.
- 팀 삭제 시 연관 tasks, messages, 멤버 team_id 모두 CASCADE 처리
- Owner만 호출 가능

#### Scenario: 팀 삭제 성공
- **WHEN** owner가 DELETE /teams/{id} 호출
- **THEN** HTTP 204, teams·tasks·messages 삭제, 모든 멤버 `team_id = NULL`

#### Scenario: 비owner 팀 삭제 시도
- **WHEN** member가 DELETE /teams/{id} 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN" } }` 반환

### Requirement: Owner 탈퇴 UI 흐름
Owner가 탈퇴를 시도할 때 클라이언트는 반드시 confirm 다이얼로그를 표시해야 한다.

#### Scenario: Owner 탈퇴 UI 분기
- **WHEN** owner가 '로그아웃' 외 '팀 떠나기' 버튼 클릭
- **THEN** 다이얼로그 표시: "팀장은 바로 탈퇴할 수 없습니다. 팀원에게 팀장을 위임하거나 팀을 삭제하세요." + [팀장 위임] [팀 삭제] 버튼

#### Scenario: 팀장 위임 후 탈퇴
- **WHEN** owner가 [팀장 위임] 선택 → 멤버 선택 → PATCH /teams/{id}/transfer-owner 성공 후 DELETE /teams/{id}/leave 호출
- **THEN** HTTP 204, 탈퇴 완료 → 팀 선택 화면으로 redirect

#### Scenario: 팀 삭제 후 탈퇴
- **WHEN** owner가 [팀 삭제] 선택 → 2차 confirm → DELETE /teams/{id} 호출
- **THEN** HTTP 204, 팀 삭제 완료 → 팀 선택 화면으로 redirect

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
