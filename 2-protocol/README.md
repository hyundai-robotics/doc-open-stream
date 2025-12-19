# Protocol

이 섹션에서는 Open Stream이 사용하는 전송 규약(Transport)과 메시지 프레이밍 규칙을 설명합니다.

- Open Stream은 **TCP 소켓** 기반의 단일 세션 통신을 사용합니다.
- 클라이언트/서버 간 메시지는 **NDJSON(Newline Delimited JSON)** 형태로 교환합니다.
- 각 메시지는 **JSON 1개를 1줄로 직렬화한 뒤, 줄 끝에 `\n`을 붙여 전송**합니다.

세부 NDJSON 규칙은 아래 문서를 참고하세요.

- [NDJSON 규칙](./1-ndjson.md)