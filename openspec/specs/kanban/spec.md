# kanban

## Purpose

팀 태스크의 칸반 보드 표시, 생성, 수정, 삭제 및 상태 관리를 담당한다.

## Requirements

### Requirement: 팀 접근 불가 시 자동 리다이렉트
칸반 화면 진입 시 팀 정보 조회가 403 또는 404를 반환하면(팀 삭제 또는 강제 탈퇴), 클라이언트는 사용자의 team_id를 null로 초기화하고 팀 선택 화면으로 자동 이동해야 한다.

#### Scenario: 팀 삭제 후 팀원 접근
- **WHEN** 팀장이 팀을 삭제한 후, 팀원이 칸반 화면을 새로고침
- **THEN** GET /teams/{id} 응답이 403 FORBIDDEN
- **THEN** 클라이언트는 localStorage의 team_id = null 처리
- **THEN** /team-select.html 로 자동 이동

### Requirement: 태스크 목록 조회 및 필터
시스템은 팀의 태스크를 컬럼별로 반환하며 assignee 기반 필터를 지원해야 한다.
- 기본 정렬: `tasks.created_at DESC`
- 필터: `전체`(기본), `@me`(assignee_id = 현재 사용자), `미할당`(assignee_id IS NULL)
- 팀 멤버만 조회 가능

#### Scenario: 전체 태스크 조회
- **WHEN** 팀 멤버가 GET /teams/{id}/tasks 호출 (filter 없음)
- **THEN** HTTP 200, 해당 팀의 모든 태스크 배열 반환 (created_at DESC)

#### Scenario: @me 필터
- **WHEN** GET /teams/{id}/tasks?filter=me 호출
- **THEN** `assignee_id = current_user_id` 인 태스크만 반환

#### Scenario: 미할당 필터
- **WHEN** GET /teams/{id}/tasks?filter=unassigned 호출
- **THEN** `assignee_id IS NULL` 인 태스크만 반환

### Requirement: 태스크 생성
팀 멤버는 태스크를 생성할 수 있어야 한다.
- 제목: 1-100자 필수
- 초기 status: TODO
- assignee_id: nullable (미지정 시 NULL)
- creator_id: 요청한 사용자 자동 설정

#### Scenario: 정상 생성
- **WHEN** 팀 멤버가 `{ title, assignee_id? }` 로 POST /teams/{id}/tasks 호출
- **THEN** HTTP 201, `{ id, team_id, title, status: "TODO", creator_id, assignee_id, created_at }` 반환

#### Scenario: 제목 빈칸
- **WHEN** 빈 제목으로 호출
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR" } }` 반환

### Requirement: 태스크 상태 변경 (드래그)
시스템은 드래그 완료 시 태스크 status를 변경해야 한다.
- 유효한 값: `TODO`, `DOING`, `DONE`
- 팀 멤버만 가능

#### Scenario: 상태 변경 성공
- **WHEN** 팀 멤버가 `{ status: "DOING" }` 으로 PATCH /tasks/{id}/status 호출
- **THEN** HTTP 200, 업데이트된 태스크 반환

#### Scenario: 잘못된 status 값
- **WHEN** `{ status: "INPROGRESS" }` 처럼 유효하지 않은 값 전달
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR" } }` 반환

### Requirement: 태스크 제목·담당자 수정
팀 멤버는 태스크의 제목과 assignee를 수정할 수 있어야 한다.

#### Scenario: 제목 수정
- **WHEN** 팀 멤버가 `{ title: "새 제목" }` 으로 PUT /tasks/{id} 호출
- **THEN** HTTP 200, 업데이트된 태스크 반환

#### Scenario: 담당자 변경
- **WHEN** 팀 멤버가 `{ assignee_id: 5 }` 또는 `{ assignee_id: null }` 로 호출
- **THEN** HTTP 200, assignee_id 변경된 태스크 반환

### Requirement: 태스크 삭제
태스크 삭제 권한은 creator 또는 team owner로 제한된다.

#### Scenario: creator가 본인 태스크 삭제
- **WHEN** creator_id = 현재 사용자인 태스크에 DELETE /tasks/{id} 호출
- **THEN** HTTP 204 반환

#### Scenario: owner가 타인 태스크 삭제
- **WHEN** team owner가 다른 멤버의 태스크에 DELETE /tasks/{id} 호출
- **THEN** HTTP 204 반환

#### Scenario: 비creator 일반 멤버 삭제 시도
- **WHEN** creator도 owner도 아닌 멤버가 DELETE /tasks/{id} 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN" } }` 반환

### Requirement: 태스크 단건 조회
팀 멤버는 특정 태스크의 상세 정보를 조회할 수 있어야 한다.

#### Scenario: 단건 조회
- **WHEN** 팀 멤버가 GET /tasks/{id} 호출
- **THEN** HTTP 200, `{ id, team_id, title, status, creator_id, assignee_id, created_at }` 반환

#### Scenario: 존재하지 않는 태스크
- **WHEN** 없는 id로 GET /tasks/{id} 호출
- **THEN** HTTP 404, `{ error: { code: "NOT_FOUND" } }` 반환
