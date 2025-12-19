## 3.4 STOP

STOP은 현재 세션에서 수행 중인 동작을 중단하거나,  
세션 종료 의도를 서버에 명시적으로 전달하기 위한 레시피 명령입니다.

- STOP은 반드시 **HANDSHAKE 성공 이후**에만 사용할 수 있습니다.
- `target` 값에 따라 `monitor`, `control`, `session` 중 하나를 중단합니다.
- `target=session`은 정상 종료 의도를 명시하는 용도로 사용되며,  
  이후 클라이언트가 TCP 연결을 종료하는 구조를 권장합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"STOP","payload":{"target":"session"}}\n
````

</div>
<div style="max-width:fit-content;">

| Payload Field    | Required | Type   | Rules                                      |
| -------- | -------- | ------ | ------------------------------------------ |
| `target` | Yes      | string | `"session"`, `"control"`, `"monitor"` 중 하나 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* `stop_ack.target` 값은 클라이언트가 요청한 `target` 값과 동일합니다.
* STOP 요청이 정상적으로 수락되었음을 의미합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

모든 에러 응답은 공통 NDJSON 에러 스키마를 따릅니다.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| Error Code           | HTTP Status | Description   | When it occurs        |
| -------------------- | ----------- | ------------- | --------------------- |
| `handshake_required` | 412         | HANDSHAKE 미수행 | HANDSHAKE 이전에 STOP 호출 |
| `missing_target`     | 400         | 필수 필드 누락      | `target` 키가 없음        |
| `invalid_target`     | 400         | target 값 오류   | 허용되지 않은 target 값      |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field    | Attribute | Type   | Validation Rule                            | Error Code       |
| -------- | --------- | ------ | ------------------------------------------ | ---------------- |
| `target` | 필수        | string | payload에 반드시 존재                            | `missing_target` |
| `target` | 값         | string | `"session"`, `"control"`, `"monitor"` 중 하나 | `invalid_target` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Behavior Notes</h4>

* `target=monitor`

  * 활성화된 MONITOR 스트리밍을 중단합니다.
* `target=control`

  * CONTROL 수행 상태를 정리합니다.
* `target=session`

  * 세션 종료 의도를 서버에 명시적으로 전달합니다.
  * `stop_ack` 수신 후 TCP 연결을 종료하는 것을 권장합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* STOP은 서버 리소스를 안전하게 정리하기 위한 명령입니다.
* 특히 `target=session` 사용은 정상 종료 시나리오에서 권장됩니다.
