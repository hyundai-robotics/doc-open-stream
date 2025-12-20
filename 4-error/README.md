# 4. Error Codes

This document describes the **error codes** that can be returned by the Open Stream server and their meanings.

Errors are generally delivered as **single-line NDJSON messages** in the following format.

<div style="max-width: fit-content;">

```json
{"error":"<error_code>","message":"...","hint":"..."}
```

| Field   | Description |
| ------- | ----------- |
| error   | Machine-readable error code |
| message | Human-readable short description |
| hint    | Optional field. Additional hint for troubleshooting |

- (Note) Not all errors include the `hint` field.

</div>

<br>

<div style="max-width: fit-content;">

<h4 style="font-size:15px; font-weight:bold;">1. Protocol / Session Errors</h4>

Errors that occur during protocol parsing, session state handling, or violations of initialization procedures.

| Error Code          | Description                 | Typical Cause                              | Client Action                                  |
| ------------------- | --------------------------- | ------------------------------------------ | ---------------------------------------------- |
| invalid_ndjson      | NDJSON parsing failure      | Broken JSON, missing newline (`\n`)        | Follow one-JSON-per-line + newline rule        |
| rx_buf_overflow     | Receive buffer overflow     | Oversized messages or excessive bursts     | Reduce message size, limit send rate           |
| handshake_required  | HANDSHAKE not performed     | Initial handshake omitted                  | Perform HANDSHAKE immediately after connect    |
| version_mismatch    | Protocol version mismatch   | MAJOR version mismatch                     | Match server MAJOR version                     |
| busy_session_active | Session already in use      | MONITOR/CONTROL active                     | Retry after STOP                               |
| session_timeout     | Session idle timeout        | Watchdog timeout                           | Maintain periodic activity or reconnect        |

<br>

<h4 style="font-size:15px; font-weight:bold;">2. Command / Payload Validation Errors</h4>

Errors that occur during request message structure or field validation.

| Error Code      | Description               | Typical Cause               | Client Action                 |
| --------------- | ------------------------- | --------------------------- | ----------------------------- |
| invalid_cmd     | Unsupported cmd           | Typo or unsupported command | Verify `cmd` value            |
| invalid_payload | Invalid payload format    | Not an object               | Change payload to object      |
| missing_field   | Missing required field    | Missing `url`, `method`, etc.| Add required fields           |
| invalid_type    | Invalid field type        | number ↔ string confusion   | Fix field type                |
| invalid_value   | Invalid value             | Out of enum range           | Use allowed values            |

<br>

<h4 style="font-size:15px; font-weight:bold;">3. HANDSHAKE Errors</h4>

Errors that occur during HANDSHAKE processing.

| Error Code         | Description                     | Typical Cause                     | Client Action                 |
| ------------------ | ------------------------------- | --------------------------------- | ----------------------------- |
| version_mismatch   | Protocol MAJOR mismatch         | Client/server MAJOR differs       | Use server MAJOR version      |
| handshake_rejected | HANDSHAKE rejected              | Invalid session state             | Close existing session, retry |

<br>

<h4 style="font-size:15px; font-weight:bold;">4. MONITOR Errors</h4>

Errors that occur during MONITOR configuration or execution.  
These mainly arise during periodic REST invocation validation.

| Error Code             | Description                         | Typical Cause              | Client Action               |
| ---------------------- | ----------------------------------- | -------------------------- | --------------------------- |
| invalid_method         | Non-GET method used in MONITOR      | POST/PUT used              | Change method to GET        |
| invalid_url            | Invalid URL format                  | Not starting with `/`, spaces | Follow URL rules            |
| invalid_period         | Invalid `period_ms` range           | Too small or too large     | Adjust to allowed range     |
| monitor_already_active | Duplicate MONITOR request           | Already active             | STOP then retry             |
| monitor_internal_error | Internal REST invocation failure    | Internal server error      | Check server logs           |

<br>

<h4 style="font-size:15px; font-weight:bold;">5. CONTROL Errors</h4>

Errors that occur during CONTROL request processing.  
They may be reported depending on REST execution results.

| Error Code         | Description                    | Typical Cause       | Client Action               |
| ------------------ | ------------------------------ | ------------------- | --------------------------- |
| control_err        | CONTROL execution failure      | REST 4xx/5xx        | Inspect status/body         |
| invalid_body       | Invalid body JSON              | Serialization error | Verify body structure       |
| method_not_allowed | Method not allowed             | Using GET, etc.     | Use POST/PUT/DELETE         |
| control_busy       | Control unavailable state      | Another control active | Retry later              |

{% hint style="warning" %}

CONTROL does not return a response on success.  
Only on failure may `control_err` or a common error message be delivered.

{% endhint %}

<br>

<h4 style="font-size:15px; font-weight:bold;">6. STOP Errors</h4>

Errors that occur during STOP request processing.

| Error Code      | Description             | Typical Cause     | Client Action                                   |
| --------------- | ----------------------- | ----------------- | ----------------------------------------------- |
| invalid_target  | Invalid STOP target     | Target typo       | Choose monitor / control / session              |
| nothing_to_stop | Nothing to stop         | Already terminated| Can be ignored                                  |
| stop_failed     | Internal cleanup failure| Internal state error | Reconnection recommended                     |

<br>

<h4 style="font-size:15px; font-weight:bold;">7. Error Handling Guidelines</h4>

Error messages are always received as single-line NDJSON.

Clients are recommended to:
- First check for the presence of the `error` field in the receive loop, and  
  clearly clean up session state (STOP or reconnect) when an error occurs.

- Some errors are recoverable, while others may require reconnection (fatal).

- Determine recoverability based on the "Client Action" column for each error.

</div>
