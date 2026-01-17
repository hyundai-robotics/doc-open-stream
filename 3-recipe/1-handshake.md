## 3.1 HANDSHAKE

This is the **protocol version negotiation** step performed immediately after a session starts.  
If `MONITOR` or `CONTROL` is called before `HANDSHAKE`, the server may reject the request.


<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------- | -------- | ---- | ----- |
| `major` | Yes | int | Integer greater than or equal to 0 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
```

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| `ok` | boolean | No | Explicit success flag for some ACKs (e.g. `handshake_ack`) |
| `version` | string | No | Server protocol version (`MAJOR.MINOR.PATCH`) |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

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
| `busy_session_active` | 409 | An active task already exists | HANDSHAKE requested while CONTROL or MONITOR task is running |
| `version_mismatch` | 400 | Protocol MAJOR version mismatch | Client `major` does not match server MAJOR |
| `missing_major` | 400 | Missing required field | `major` key is missing in payload |
| `invalid_major_type` | 400 | Invalid type | `major` is not a number (int) |
| `invalid_version` | 400 | Invalid value range | `major` is negative |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field | Attribute | Type | Validation Rule | Error Code |
| ---- | --------- | ---- | --------------- | ---------- |
| `major` | Required | int | Must exist in payload | `missing_major` |
| `major` | Type | int | Must be a number | `invalid_major_type` |
| `major` | Range | int | Integer ≥ 0 | `invalid_version` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

- The server validates **only the MAJOR version**.
- MINOR / PATCH changes do not break compatibility with existing clients.
- For version policy details, refer to the [Release Notes](../10-release-notes/README.md).
