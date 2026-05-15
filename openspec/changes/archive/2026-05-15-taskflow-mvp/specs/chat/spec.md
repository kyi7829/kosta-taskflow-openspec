## ADDED Requirements

### Requirement: 채팅 메시지 조회 (폴링)
시스템은 팀 채팅 메시지를 반환하며 `since=` 파라미터로 증분 조회를 지원해야 한다.
- `since` 없음: 최근 50개 반환 (created_at DESC)
- `since=<ISO8601시각>`: 해당 시각 이후 메시지만 반환
- 결과 없으면 빈 배열 `[]` 반환 (204 아님)
- `messages(team_id, created_at)` 인덱스로 O(log n) 보장

#### Scenario: 최초 진입 (전체 조회)
- **WHEN** 팀 멤버가 GET /teams/{id}/messages 호출 (since 없음)
- **THEN** HTTP 200, 최근 50개 메시지 배열 반환 (created_at ASC 정렬)

#### Scenario: 증분 폴링
- **WHEN** GET /teams/{id}/messages?since=2026-05-13T14:30:00Z 호출
- **THEN** HTTP 200, `created_at > since` 인 메시지만 반환

#### Scenario: 새 메시지 없음
- **WHEN** 폴링 중 신규 메시지가 없을 때
- **THEN** HTTP 200, `[]` 반환

#### Scenario: 메시지 누락 없음 보장
- **WHEN** 네트워크 끊김 후 재연결 시 마지막 수신 시각으로 since= 조회
- **THEN** 누락된 모든 메시지가 포함된 배열 반환

### Requirement: 메시지 전송
팀 멤버는 1000자 이내 텍스트 메시지를 전송할 수 있어야 한다.
- 최대 1000자: 클라이언트(카운터 + 버튼 disable) + 서버(400) 양쪽 검증
- 발신자 정보(user_id, user_email) 응답에 포함

#### Scenario: 정상 전송
- **WHEN** 팀 멤버가 `{ content: "안녕하세요" }` 로 POST /teams/{id}/messages 호출
- **THEN** HTTP 201, `{ id, team_id, user_id, user_email, content, created_at }` 반환

#### Scenario: 1000자 초과
- **WHEN** 1001자 이상 content 전달
- **THEN** HTTP 400, `{ error: { code: "TOO_LONG", message: "메시지는 1000자 이내로 입력하세요", limit: 1000, actual: <실제 길이> } }` 반환

#### Scenario: 빈 메시지
- **WHEN** 빈 문자열 content 전달
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR" } }` 반환

### Requirement: 메시지 삭제
본인이 작성한 메시지만 삭제할 수 있어야 한다. owner도 타인 메시지 삭제 불가.

#### Scenario: 본인 메시지 삭제
- **WHEN** 메시지 작성자가 DELETE /messages/{id} 호출
- **THEN** HTTP 204 반환

#### Scenario: 타인 메시지 삭제 시도
- **WHEN** 작성자가 아닌 사용자가 DELETE /messages/{id} 호출 (owner 포함)
- **THEN** HTTP 403, `{ error: { code: "NOT_OWNER", message: "본인의 메시지만 삭제할 수 있습니다" } }` 반환

#### Scenario: 존재하지 않는 메시지
- **WHEN** 없는 id로 DELETE /messages/{id} 호출
- **THEN** HTTP 404, `{ error: { code: "NOT_FOUND" } }` 반환
