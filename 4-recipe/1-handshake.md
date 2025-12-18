# 2.1 HANDSHAKE

## Request
```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

- major: number(정수), 필수, 0 이상

## Response (success)
```json
{"type":"handshake_ack","ok":true,"version":"<server_version>"}\n
```

## Errors
- busy_session_active (409): CONTROL 또는 MONITOR가 active면 HANDSHAKE 불가
- version_mismatch (400): major 불일치
