## 3.4 STOP

STOP is a recipe command used to interrupt ongoing operations in the current session  
or to explicitly notify the server of the intent to terminate the session.

- STOP can be used **only after a successful HANDSHAKE**.
- Depending on the `target` value, it stops one of `monitor`, `control`, or `session`.
- `target=session` is used to explicitly indicate a graceful shutdown intent,  
  after which the client is recommended to close the TCP connection.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"STOP","payload":{"target":"session"}}\n
````

</div>
<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| `target` | Yes | string | One of `"session"`, `"control"`, `"monitor"` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* The value of `stop_ack.target` is identical to the requested `target` value.
* Indicates that the STOP request has been successfully accepted.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

All error responses follow the common NDJSON error schema.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| Error Code | HTTP Status | Description | When it occurs |
| ---------- | ----------- | ----------- | -------------- |
| `handshake_required` | 412 | HANDSHAKE not performed | STOP called before HANDSHAKE |
| `missing_target` | 400 | Missing required field | `target` key is missing |
| `invalid_target` | 400 | Invalid target value | Unsupported `target` value |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field | Attribute | Type | Validation Rule | Error Code |
| ----- | --------- | ---- | --------------- | ---------- |
| `target` | Required | string | Must exist in payload | `missing_target` |
| `target` | Value | string | One of `"session"`, `"control"`, `"monitor"` | `invalid_target` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Behavior Notes</h4>

* `target=monitor`
  * Stops the active MONITOR streaming.
* `target=control`
  * Cleans up the CONTROL execution state.
* `target=session`
  * Explicitly notifies the server of session termination intent.
  * Closing the TCP connection after receiving `stop_ack` is recommended.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* STOP is intended to safely release server resources.
* Using `target=session` is strongly recommended for graceful shutdown scenarios.
