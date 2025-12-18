# 2.3 CONTROL

CONTROL은 REST API를 단발로 호출하는 제어 커맨드입니다.

## Request

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/robot/start","args":{},"body":{"speed":10}}}\n
```

### payload fields
- method: string, 필수, POST|PUT|DELETE 중 하나
- url: string, 필수 (MONITOR와 동일 규칙)
- args: object, 옵션(있으면 object)
- body: object|array, 옵션(없으면 {}로 처리)

## Response
- 성공(HTTP 200) 시: **응답 바디를 보내지 않습니다. (no response line)**
- 실패 시:
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
