# 1. Recipe Commands

A **Recipe** refers to an **NDJSON line sent from the client to the server** in Open Stream.  
Each line is transmitted in the following format.

<div style="max-width:fit-content;">

```json
// Request
{"cmd":"<COMMAND>","payload":{...}}\n
````

</div>

The server returns ACKs, events, and errors in the same NDJSON line format.

<div style="max-width:fit-content;">

```json
// Response
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

The meaning of each message field is as follows.

<h4 style="font-size:16px; font-weight:bold;">Request (Client → Server)</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| `cmd` | string | Yes | Command name (`HANDSHAKE`, `MONITOR`, `CONTROL`, `STOP`) |
| `payload` | object | Yes | Command parameter object (see each command document for schema details) |

1. [HANDSHAKE](./1-handshake.md): Protocol version negotiation (mandatory at session start)

2. [MONITOR](./2-monitor.md): Periodic REST GET execution + `data` streaming

3. [CONTROL](./3-control.md): One-shot REST execution (**no response line on success**)

4. [STOP](./4-stop.md): Stop `monitor`, `control`, or `session`

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response (Client ⇠ Server)</h4>

<h4 style="font-size:16px; font-weight:bold;">Success</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| `type` | string | Yes | Event type (e.g. `handshake_ack`, `monitor_ack`, `data`, `stop_ack`) |

- For `HANDSHAKE` responses, the fields `ok` (boolean) and `version` (string) are additionally included.

</div>

<h4 style="font-size:16px; font-weight:bold;">Error</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| `error` | string | Yes | Error code (machine-readable) |
| `message` | string | Yes | Error description (human-readable) |
| `hint` | string | No | Guidance or example for resolution |

</div>
