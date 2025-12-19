# 1. 명령어

Open Stream에서 **클라이언트가 서버로 보내는 명령(Command) NDJSON 라인**을 의미합니다.  
각 명령은 아래 형태로 전송됩니다.

<div style="max-width:fit-content;">

```json
// Request
{"cmd":"<COMMAND>","payload":{...}}\n
````

</div>

서버는 ACK / 이벤트 / 에러를 동일하게 NDJSON 라인으로 반환합니다.

<div style="max-width:fit-content;">

```json
//  Response
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

메세지 필드들의 의미는 다음과 같습니다.

<h4 style="font-size:16px; font-weight:bold;">Request (Client → Server)</h4>

<div style="max-width:fit-content;">

| Key       | Type   | Required | Description                                       |
| --------- | ------ | -------: | ------------------------------------------------- |
| `cmd`     | string |      Yes | 명령 이름 (`HANDSHAKE`, `MONITOR`, `CONTROL`, `STOP`) |
| `payload` | object |      Yes | 명령 파라미터 객체 (명령별 스키마는 각 문서 참고)                     |

1. [HANDSHAKE](./1-handshake.md) : 프로토콜 버전 협상 (세션 초기에 필수)

2. [MONITOR](./2-monitor.md) : 주기적 REST GET 실행 + `data` 스트리밍

3. [CONTROL](./3-control.md) : 단발 REST 실행 (성공 시 **응답 라인 없음**)

4. [STOP](./4-stop.md) : `monitor` / `control` / `session` 중단

</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">Response (Client ⇠ Server)</h4>

<h4 style="font-size:16px; font-weight:bold;">Success</h4>

<div style="max-width:fit-content;">

| Key       | Type    | Required | Description                                                    |
| --------- | ------- | -------: | -------------------------------------------------------------- |
| `type`    | string  |      Yes | 이벤트 타입 (예: `handshake_ack`, `monitor_ack`, `data`, `stop_ack`) |

- `HANDSHAKE` 명령어 응답의 경우, `ok`(boolean), `version`(string) 을 필드에 추가하여 응답함

</div>

<h4 style="font-size:16px; font-weight:bold;">Error</h4>
<div style="max-width:fit-content;">

| Key       | Type   | Required | Description              |
| --------- | ------ | -------: | ------------------------ |
| `error`   | string |      Yes | 에러 코드 (machine-readable) |
| `message` | string |      Yes | 에러 설명 (human-readable)   |
| `hint`    | string |       No | 해결을 위한 가이드 또는 예시         |

</div>