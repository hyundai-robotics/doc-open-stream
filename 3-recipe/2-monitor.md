## 3.2 MONITOR

This command periodically invokes a client-specified REST **GET** service  
and streams the results as single-line NDJSON messages.

- In the current implementation, **only one MONITOR is maintained per session**.
- When a new `MONITOR` command is received, the existing monitor session is automatically terminated and replaced.
- `MONITOR` can be used **only after a successful HANDSHAKE**.<br>
  &rightarrow; If called before HANDSHAKE, a `handshake_required` error is returned.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"MONITOR","payload":{"method":"GET","period_ms":2,"url":"/project/robot/joints/joint_states","args":{"jno_start":1,"jno_n":6}}}\n
````

</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| `url` | Yes | string | Must start with `/`, no spaces, max length 2048 |
| `method` | Yes | string | Only `"GET"` is allowed |
| `period_ms` | Yes | int | 2 ~ 30000 (ms), out-of-range values are clamped |
| `args` | No | object | Object for query parameters (JSON object only) |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* `monitor_ack` indicates that the MONITOR request has been accepted.
* The arrival order of `monitor_ack` and the first `data` event is **not guaranteed**.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>Streaming</i></u></b>)</h4>

When MONITOR is active, the server repeatedly invokes the REST API (GET)  
at the specified interval (`period_ms`) and sends the results as `data` events.

<div style="max-width:fit-content;">

```json
{"type":"data","ts":402,"svc_dur_ms":2.960000,"result":{"_type":"JObject","position":[0.0,90.0,0.0,0.0,-90.0,0.0],"effort":[-0.0,98.923641,94.599385,-0.110933,-5.895076,0.0],"velocity":[-0.0,-0.0,0.0,0.0,-0.0,0.0]}}\n
```

</div>

<div style="max-width:fit-content;">

| Response Field | Type | Description |
| -------------- | ---- | ----------- |
| `type` | string | Event type (`data`) |
| `ts` | number | Server-side timestamp (ms) |
| `svc_dur_ms` | number | Time spent on REST invocation and processing (ms) |
| `result` | any | REST response body (if present) |
| `status` | number | HTTP status code returned when REST body is empty |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

All error responses follow the common NDJSON error schema.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Error Codes</h4>

<div style="max-width:fit-content;">

| Error Code | HTTP Status | Description | When it occurs |
| ---------- | ----------- | ----------- | -------------- |
| `handshake_required` | 412 | HANDSHAKE not performed | MONITOR called before HANDSHAKE |
| `missing_url` | 400 | Missing required field | `url` key is missing |
| `invalid_url` | 400 | Invalid URL format | Does not start with `/` or contains spaces |
| `url_too_long` | 400 | URL too long | URL length exceeds 2048 |
| `missing_method` | 400 | Missing required field | `method` key is missing |
| `invalid_method` | 400 | Invalid method | Not `"GET"` |
| `missing_period_ms` | 400 | Missing required field | `period_ms` key is missing |
| `invalid_period` | 400 | Invalid type | `period_ms` is not an int |
| `invalid_args` | 400 | Invalid type | `args` is not an object |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field | Attribute | Type | Validation Rule | Error Code |
| ----- | --------- | ---- | --------------- | ---------- |
| `url` | Required | string | Must exist in payload | `missing_url` |
| `url` | Format | string | Must start with `/`, no spaces | `invalid_url` |
| `url` | Length | string | Max 2048 | `url_too_long` |
| `method` | Required | string | Must be `"GET"` | `missing_method`, `invalid_method` |
| `period_ms` | Required | int | Must be int | `missing_period_ms`, `invalid_period` |
| `period_ms` | Range | int | 2~30000, clamp if out of range | — |
| `args` | Type | object | JSON object only | `invalid_args` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Watchdog Behavior</h4>

* When MONITOR is activated, the watchdog transitions to the **ARM state**.
* In this state, the session idle timeout is reduced from **180 seconds to 5 seconds**.
* If the TCP connection is lost during monitoring, or  
  if no meaningful commands are received from the client for a certain period,  
  the watchdog detects this and automatically cleans up the session.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* MONITOR is a server-driven streaming mechanism.
* `data` events may arrive at any time, regardless of whether `monitor_ack` has been received.
* The client must always keep a receive loop running and handle events based on the `type` field.
