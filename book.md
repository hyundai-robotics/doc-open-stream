# ${cont_model} Open Stream

{% hint style="warning" %}

The information provided in this product manual is the property of <b>HD Hyundai Robotics</b>.

This manual may not be reproduced or redistributed, in whole or in part, without prior written consent from HD Hyundai Robotics,  
and may not be provided to third parties or used for any other purpose.

The contents of this manual are subject to change without prior notice.


**Copyright ⓒ 2025 by HD Hyundai Robotics**

{% endhint %}

{% hint style="warning" %}

HD Hyundai Robotics shall not be held responsible for any damages or issues arising from the use of  
${cont_model} Open Stream features not specified in this manual, or APIs not documented in the ${cont_model} Open API manual.

{% endhint %}
# 1. Overview

This document is a user guide for external clients that use Open Stream.  
It explains the purpose, core concepts, overall architecture, and supported usage scenarios of Open Stream.  

<br>

Through this document, readers will understand: 
- What problems Open Stream is designed to solve
- How Open Stream operates
- When and in what situations Open Stream should be used

📌 For the latest updates and changes, please refer to the [Release Notes](../10-release-notes/README.md)

## 1.1 What is Open Stream?

Open Stream is an interface that allows clients to continuously receive results in a streaming manner  
by repeatedly invoking **${cont_model} Open APIs** at short intervals.

<br>

It provides a streaming interface through a **TCP-based lightweight server** embedded inside the ${cont_model} controller,  
enabling external clients to continuously send and receive data over a persistent connection.

<br>

Open Stream has the following characteristics:

- Maintains a **single long-lived TCP connection**
- Uses **NDJSON (Newline Delimited JSON)** for requests and responses
- Supports both **periodic data streaming (`MONITOR`)** and **immediate control commands (`CONTROL`)**
- Eliminates repeated creation of HTTP request/response cycles

<br>

Open Stream is designed for client environments that require handling  
**high-frequency control commands and status monitoring over a single connection**.

<br><br>

<b>Overall Operation Overview</b>

The basic operational flow of Open Stream is as follows.

<div style="display:flex; flex-wrap:wrap; align-items:flex-start;">

<!-- Left: Image -->
<div style="flex:1 1 420px; min-width:420px; max-width:420px;">
  <img
    src="../_assets/1-open_stream_concept.png"
    alt="Open Stream Flow"
    style="width:100%; height:auto; border-radius:6px;"
  />
</div>

<!-- Right: Ordered List -->
<div style="flex:1 1 280px; min-width:280px; max-width:fit-content;">
  <ol style="line-height:1.5;">

  <li>The client establishes a TCP connection to the server, creating a session.</li><br>

  <li>Immediately after connection, the client sends a <code>HANDSHAKE</code> command<br>
      to verify protocol version compatibility with the server.</li><br>

  <li>The server processes the <code>HANDSHAKE</code> request and, if the protocol version is compatible, sends a <code>handshake_ack</code> event.</li><br>

  <li>After a successful <code>HANDSHAKE</code>, the client may request periodic data streaming using the <code>MONITOR</code> command, or execute one-shot requests using the <code>CONTROL</code> command.
      <small>(CONTROL commands can be sent even while MONITOR is active.)</small>
  </li><br>

  <li>When <code>MONITOR</code> is active, the server sends <code>data</code> events at the configured interval, independent of additional client requests.</li><br>
    
  <li>Successful <code>CONTROL</code> commands do not generate ACK responses.<br>
      Only failures may result in <code>error</code> or <code>control_err</code> events.</li><br>

  <li>When operations are complete, the client sends a <code>STOP</code> command
      to indicate termination of active operations or session intent,
      and closes the TCP connection after receiving <code>stop_ack</code>.
  </li>

  </ol>
</div>

</div>

<br>

{% hint style="info" %}

**What is the MONITOR command?**  
The MONITOR command repeatedly invokes a single ${cont_model} Open API service at a client-defined interval  
and continuously streams the results to the client.

**What is the CONTROL command?**  
The CONTROL command is used to send one-shot control requests to the ${cont_model} Open API.  
Clients may send CONTROL commands repeatedly at short intervals as needed.

{% endhint %}

Open Stream allows MONITOR and CONTROL commands to be used together within a single TCP connection.

{% hint style="warning" %}

However, within a single connection, **only one MONITOR session and one CONTROL session** can be active at the same time.

{% endhint %}
## 1.2 Usage Considerations

Open Stream is designed to efficiently handle real-time control and status monitoring.  
However, the following constraints and assumptions must be carefully considered.

- Open Stream targets periodic data delivery but does **not guarantee strict determinism**.
- Periodic jitter may occur depending on operating system scheduling, network conditions,
  and client-side processing load.
- Only **one MONITOR session** can be active per TCP connection.
- All commands must follow the defined protocol order.
  Violating the order may result in command rejection or connection termination.

<br><br>

<b>Performance Reference for MONITOR and CONTROL Operation (Test Results)</b>

The following results compare periodic behavior between MONITOR-only operation and
simultaneous CONTROL + MONITOR operation under the same test environment.

Test Environment:
- Server: ${cont_model} COM
- Client: Python client on Windows 11
- Network: TCP connection
- Send/receive period: Maximum configurable MONITOR frequency

<br>

Summary of Results

<div style="max-width:fit-content;">

1. MONITOR Only

| **Test Conditions** | **Periodic Characteristics** |
| --- | --- |
| - MONITOR period: 2 ms (500 Hz)<br>- CONTROL not used<br>- Continuous run: 10 hours | - <u><b>Average receive period: ~2.0 ms</b></u> |

2. CONTROL + MONITOR Concurrent

| **Test Conditions** | **Periodic Characteristics** |
| --- | --- |
| - CONTROL period: 2 ms<br>- MONITOR period: 2 ms<br>- CONTROL and MONITOR active simultaneously | - CONTROL (SEND): <u><b>Average period ~2.0 ms</b></u>, max delay ~30–40 ms<br>- MONITOR (RECV): <u><b>Average period ~2.1–2.2 ms</b></u>, max delay from tens of ms up to >100 ms |

</div>

<br><br>

<b>Interpretation and Operational Notes</b>

- When MONITOR is used alone, relatively stable periodic reception is possible even during long continuous operation.
- When CONTROL and MONITOR are used concurrently, CONTROL sessions are processed with higher priority depending on system design.
- As a result, CONTROL periodic stability is maintained, while MONITOR reception periods may increase and experience intermittent delays.
- Systems using both CONTROL and MONITOR must be designed assuming potential degradation and jitter in MONITOR periodicity.
# 2. Protocol

This section describes the transport protocol and message framing rules used by Open Stream.

> **Warning**
>
> Open Stream is not a request–response protocol but an **event stream**.  
> Server events (`data`, `*_ack`, `error`) may arrive at any time regardless of client requests,  
> so client logic must be implemented without relying on message ordering.

- Open Stream uses a **single-session communication model based on a TCP socket**.
- Messages exchanged between the client and server use **NDJSON (Newline Delimited JSON)**.
- Each message is sent by **serializing exactly one JSON object per line and appending `\n` at the end**.

> **Info**
>
> Due to the nature of TCP streams, a single `recv()` call may not return exactly one message.  
> Received data should be accumulated in an internal buffer and parsed by splitting on `\n`.

For detailed NDJSON rules, refer to the document below.

- [NDJSON Specification](./1-ndjson.md)
## 2.1 What is NDJSON?

Open Stream uses **NDJSON (Newline Delimited JSON)** for message framing.  
In other words, **one line equals one JSON message**.

<h4 style="font-size:15px; font-weight:bold;">1. Message Framing</h4>

<div style="max-width:fit-content;">

- Clients send requests as follows:

```json
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
{"cmd":"MONITOR","payload":{"period_ms":10,"method":"GET","url":"/project/robot"}}\n
```

- The server sends responses and events in the same manner:

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
{"type":"data","ts":1730000000000,"svc_dur_ms":0.42,"result":{"status":"ok"}}\n
```

</div>

<br>

<h4 style="font-size:15px; font-weight:bold;">2. Mandatory Rules</h4>

1. Each message must serialize exactly one JSON object into a single line.  
   → Newline characters inside a JSON string will break framing.
2. Each message **must end with a newline character (`\n`)**.
3. All messages must be encoded in **UTF-8**.

<br>

<h4 style="font-size:15px; font-weight:bold;">3. Recommendations</h4>

1. Whitespace-free serialization is recommended to minimize message size.

```python
# Python example
import json
json.dumps(recipe_data, separators=(",", ":")) + "\n"
```

<br>

<h4 style="font-size:15px; font-weight:bold;">4. Client Implementation Tips</h4>

<div style="max-width:fit-content;">

{% hint style="info" %}

Due to TCP stream characteristics, a single `recv()` call does not guarantee exactly one line.  
It is recommended to accumulate received data into an internal buffer and split messages by `\n`
before performing JSON parsing.

{% endhint %}

```python
def recv_lines(sock):
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if line:
                yield line.decode("utf-8", errors="replace")
```
</div>
## 2. Session and Streaming Rules

<div style="fit-content;">

{% hint style="info" %}

This document explains the <b>Session Lifecycle</b> and <b>Streaming Behavior</b>  
that must be understood to properly implement and operate Open Stream.

{% endhint %}

</div>

<br>

<h4 style="font-size:16px; font-weight:bold;">1. Session Lifecycle</h4>

Open Stream treats <b>one TCP connection as one session</b>.  
A typical session flow is as follows:

1. The client connects to the server over TCP to create a session.
2. Immediately after connection, the client sends the `HANDSHAKE` command to verify protocol version compatibility with the server.
3. After processing the `HANDSHAKE` request, if the protocol version matches, the server sends a `handshake_ack` event.
4. After `HANDSHAKE`, the client can request periodic data streaming via `MONITOR`, or execute one-shot requests via `CONTROL`. (`CONTROL` can also be sent while `MONITOR` is active.)
5. When `MONITOR` is active, the server sends `data` events periodically regardless of additional client requests.
6. A `CONTROL` command sends no separate ACK on success; only on failure may an `error` or `control_err` event be delivered.
7. When work is complete, the client sends `STOP` to indicate termination intent for the active operation or session, then closes the TCP connection after receiving `stop_ack` from the server.

{% hint style="warning" %}

Open Stream is an event-driven streaming protocol and does not guarantee request–response ordering.  
Since the arrival order between `data`, `*_ack`, and `error` events is not guaranteed, clients must handle events without relying on message order.

{% endhint %}


<br>

<h4 style="font-size:16px; font-weight:bold;">2. Usage Rules</h4>

The following rules must be followed to use Open Stream correctly.

- `HANDSHAKE` must be performed <b>at the beginning of the session</b>.
- If `MONITOR` or `CONTROL` is called before `HANDSHAKE`, the server may reject the request.
- `STOP(target=session)` is used to explicitly indicate “graceful termination intent,” and it is recommended to close the TCP connection afterward.

<br>
<h4 style="font-size:16px; font-weight:bold;">3. Message Direction</h4>

<p>
Messages used in Open Stream are categorized as follows based on <b>direction and role</b>.
</p>

<div style="display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start;">

  <!-- Left: Diagram -->
  <div style="flex:1 1 430px; min-width:280px; max-width:430px;">
    <img
      src="../_assets/2-open_stream_message_direction.png"
      alt="open stream message flow chart"
      style="max-width:100%; height:auto;"
    />
  </div>

  <!-- Right: Two tables -->
<div style="flex:1 1 520px; min-width:280px; max-width:fit-content; display:flex; flex-direction:column; gap:12px;">

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">Client → Server (Commands)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>Command</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><code>HANDSHAKE</code></td><td>Protocol version negotiation</td></tr>
        <tr><td><code>MONITOR</code></td><td>Configure periodic data streaming</td></tr>
        <tr><td><code>CONTROL</code></td><td>Execute command-type REST requests</td></tr>
        <tr><td><code>STOP</code></td><td>Terminate active operation or session</td></tr>
      </tbody>
    </table>
  </div>

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">Client ⇠ Server (Events)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>Event</th>
          <th>Description</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>*_ack</code></td>
          <td>ACK indicating that a command has been accepted</td>
          <td>e.g. <code>handshake_ack</code>, <code>monitor_ack</code>, <code>stop_ack</code></td>
        </tr>
        <tr>
          <td><code>data</code></td>
          <td>Periodic data event while MONITOR is active</td>
          <td>Result of executing the Hi6 Open API service function</td>
        </tr>
        <tr>
          <td><code>error</code></td>
          <td>Error message delivered when a failure occurs</td>
          <td>Refer to the Error Codes section for details</td>
        </tr>
      </tbody>
    </table>
  </div>

  {% hint style="info" %}

  Server → Client events may <b>not correspond 1:1 with client</b> requests.  
  While `*_ack` and `error` follow a request–response pattern,  
  `data` events generated by MONITOR are streamed independently.  
  The client must always keep the receive loop running.

  {% endhint %}
  
</div>
</div>

<div style="max-width:fit-content;">


| Request–Response | Streaming |
|---|---|
| Client → `HANDSHAKE/MONITOR/CONTROL/STOP` → Server<br>Client ← `*_ack`, `error` ← Server | (after `monitor_ack`)<br>Server → `data` → Client<br>Server → `data` → Client<br>... |
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">4. MONITOR Streaming Behavior</h4>

`MONITOR` is a server-driven mechanism where, based on the recipe provided by the client,  
the server executes the Hi6 Open API service function at the specified interval (`period_ms`)  
and streams the result as `data` events.

Clients must be implemented with the following assumptions.

- Always keep the receive loop running.
- Do not assume synchronous request–response pairing.

<br>
<h4 style="font-size:16px; font-weight:bold;">5. CONTROL Command Execution</h4>


Depending on policy/implementation, <b>CONTROL provides no separate response line on success.</b>

Recommended strategy:

- Detect failures via `error` or `control_err` events.
- Verify success using the following approaches:
  - Confirm changes in MONITOR results
  - Use a dedicated state-query MONITOR endpoint


<br>
<h4 style="font-size:16px; font-weight:bold;">6. Timeout / Watchdog</h4>

The server may terminate the connection if the session remains idle for an extended period.

Client recommendations:

- Perform `HANDSHAKE` immediately after connection
- Perform a graceful shutdown using `STOP(target=session)`
- Prevent the receive loop from stopping during streaming
- Prepare reconnection and re-HANDSHAKE logic on EOF or socket errors

In the current server implementation, the following policies apply.

- <b>Disarmed state (Idle / No active MONITOR)</b>  
  &rightarrow; Session is terminated after approximately <b>180 seconds</b> of no meaningful activity

- <b>Armed state (Active MONITOR streaming)</b>  
  &rightarrow; Session is terminated if streaming remains interrupted for more than approximately <b>5 seconds</b>

※ The above time values may change depending on server policy or operating environment.

<br>
<h4 style="font-size:16px; font-weight:bold;">7. Recommended Architecture </h4>

For practical implementations, the following structure is recommended.

- Separate sending (Commands) and receiving (Events)  
  &rightarrow; Send: build command + `sendall`  
  &rightarrow; Receive: NDJSON line parser + dispatcher

- Single-responsibility receive loop  
  &rightarrow; Split lines by `\n`  
  &rightarrow; JSON parsing  
  &rightarrow; Event routing based on `type` / `error`
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
## 3.3 CONTROL

CONTROL is a recipe command used by the client to control the robot or update internal controller data.  
Internally, it invokes <b>POST / PUT / DELETE–based Hi6 OpenAPI</b>, and even in the Stream environment,  
the <b>same REST paths and validation logic</b> as the existing OpenAPI are applied.

- CONTROL can be used **only after a successful HANDSHAKE**.<br>
  &rightarrow; If called before HANDSHAKE, it is immediately rejected with a `handshake_required` error.
- CONTROL is a <b>one-shot command</b>, and <b style="color:#ec1249;">no response NDJSON line is sent on success.</b>
- CONTROL can be executed even while MONITOR is active.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/project/robot/trajectory/joint_traject_insert_point","args":{},"body":{"interval":0.005,"time_from_start":-1,"look_ahead_time":0.004,"point":[1.014532178568314,91.01453217856832,1.014532178568314,1.014532178568314,1.014532178568314,0.013294178568314]}}}\n
````
</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------- | -------- | ---- | ----- |
| `url` | Yes | string | Must start with `/`, no spaces |
| `method` | Yes | string | One of `POST`, `PUT`, `DELETE` |
| `args` | No | object | Object for REST query parameters |
| `body` | No | object \\| array | REST request body |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>no response line</i></u></b>)</h4>

If the CONTROL command is processed successfully,  
<b>the server does not send a response NDJSON line.</b>  
The client must be implemented to issue the command without expecting a return value.

* This behavior is by design in the Stream protocol.
* CONTROL success should be verified through <b>state changes or MONITOR results</b>, not by receiving an ACK.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

If an error occurs, the server sends a `control_err` event to the current session.

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| Error Code | HTTP Status | Description | When it occurs |
| ---------- | ----------- | ----------- | -------------- |
| `handshake_required` | 412 | HANDSHAKE not performed | CONTROL called before HANDSHAKE |
| `missing_url` | 400 | Missing required field | `url` key is missing |
| `invalid_url` | 400 | Invalid URL format | Does not start with `/` or contains spaces |
| `missing_method` | 400 | Missing required field | `method` key is missing |
| `invalid_method` | 400 | Invalid method | Not `POST/PUT/DELETE` |
| `invalid_args` | 400 | Invalid type | `args` is not an object |
| `invalid_body` | 400 | Invalid type | `body` is not an object or array |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field | Attribute | Type | Validation Rule | Error Code |
| ----- | --------- | ---- | --------------- | ---------- |
| `url` | Required | string | Must exist in payload | `missing_url` |
| `url` | Format | string | Must start with `/`, no spaces | `invalid_url` |
| `method` | Required | string | One of `POST/PUT/DELETE` | `missing_method`, `invalid_method` |
| `args` | Type | object | JSON object only | `invalid_args` |
| `body` | Type | object \\| array | Object or array only | `invalid_body` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Watchdog Interaction</h4>

- When a CONTROL command is executed successfully, the watchdog updates the last-activity timestamp it monitors.
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
# 5. Examples

{% hint style="info" %}

This section provides step-by-step examples to help first-time Open Stream users understand  
<b>how to design the client-side architecture</b>.  
Each example focuses on <b>understanding structure and control flow</b> rather than providing fully optimized or production-ready code.

{% endhint %}

<h4 style="font-size:16px; font-weight:bold;">Manual Example Section Structure</h4>

<div style="max-width:fit-content;">

```text
5. Examples
├── 5.1 utils       # Common utilities (send/receive, parsing, event dispatch)
├── 5.2 handshake   # Standalone HANDSHAKE example
├── 5.3 monitor     # MONITOR streaming example
├── 5.4 control     # CONTROL one-shot request example
└── 5.5 stop        # STOP and graceful shutdown example
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Client Directory Structure</h4>

Below is a recommended minimal directory structure  
for a client application that uses Open Stream.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py            # TCP socket connection and send/receive
│   ├── parser.py         # NDJSON stream parsing
│   ├── dispatcher.py     # Event dispatch based on type / error
│   ├── motion.py         # Generating sine wave motion
│   └── api.py            # Wrappers for HANDSHAKE / MONITOR / CONTROL / STOP
│
├── scenarios/
│   ├── handshake.py      # Standalone HANDSHAKE scenario
│   ├── monitor.py        # MONITOR streaming scenario
│   ├── control.py        # CONTROL one-shot request scenario
│   └── stop.py           # STOP and graceful shutdown scenario
│
└── main.py               # Client entry point
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Execution Environment</h4>

<div style="max-width:fit-content;">

| Item | Description |
| ---- | ----------- |
| Language | Python 3.8.0 |
| OS | Linux / macOS / Windows (any environment supporting TCP sockets) |
| Libraries | Standard library only |

</div>

- These examples intentionally minimize external dependencies  
  to focus on understanding the Open Stream protocol itself.
## 5.1 Common Utilities (utils)

{% hint style="info" %}

This document provides the <b>Open Stream client utility code</b>  
that is commonly used across all subsequent examples.

The code below is <b>fully functional, runnable code</b>, not just illustrative samples.  
You may copy it directly into your own project and use it as-is.

For clarity and reproducibility, this example is intentionally implemented using a  
<b>"receive thread + blocking socket (with timeout)"</b> model.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">Directory Structure</h4>

Create the `utils/` directory as shown below  
and copy each file exactly as provided.

<div style="max-width: fit-content;">

```text
OpenStreamClient/
└── utils/
    ├── net.py
    ├── parser.py
    ├── dispatcher.py
    ├── motion.py
    └── api.py
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Utility Roles</h4>

| File | Role | Main Responsibilities |
| ---- | ---- | --------------------- |
| <b>net.py</b> | TCP network layer | TCP socket connect/disconnect, receive loop (thread), raw byte reception |
| <b>parser.py</b> | NDJSON parser | NDJSON stream parsing, JSON object creation |
| <b>dispatcher.py</b> | Message dispatcher | Callback dispatch based on message `type` / `error` |
| <b>motion.py</b> | Trajectory utilities | Sine trajectory generation, file save/load |
| <b>api.py</b> | Open Stream API wrapper | Abstraction for HANDSHAKE / MONITOR / CONTROL / STOP |

</div>

<br>
<div style="max-width:fit-content;">

---

<h4 style="font-size:16px; font-weight:bold;">utils/net.py</h4>

This module implements the network layer responsible for TCP socket connection and I/O.

<b>Responsibilities</b>  
(1) Create, maintain, and close the TCP connection to the Open Stream server.  
(2) Read incoming raw byte streams from the server in a receive thread and forward them via a callback (`on_bytes`).  
(3) Decouple higher layers (parser/dispatcher) from direct network I/O handling.

<b>Key Design Points</b>  
(1) `TCP_NODELAY` (Nagle OFF): reduces latency for small NDJSON lines.  
(2) `SO_KEEPALIVE`: helps detect half-open connections.  
(3) Timeout-based recv loop: ensures responsiveness during shutdown or interruption.

<b>Main APIs</b>  
(1) `connect()`: establish socket connection and configure options  
(2) `send_line(line)`: send one NDJSON line (newline appended automatically)  
(3) `start_recv_loop(on_bytes)`: start receive thread  
(4) `close()`: close the connection

<details><summary>Click to check the python code</summary>

```python
# utils/net.py
import socket
import threading
from typing import Callable, Optional


class NetClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port))

        # Nagle OFF (low latency)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

        # TCP keepalive
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass

        self.sock.settimeout(1.0)
        self._running = True
        print(f"[net] connected to {self.host}:{self.port}")

    def close(self) -> None:
        self._running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        print("[net] connection closed")

    def send_line(self, line: str) -> None:
        if not self.sock:
            raise RuntimeError("socket not connected")
        self.sock.sendall((line + "\n").encode("utf-8"))
        print(f"[tx] {line}")

    def start_recv_loop(self, on_bytes: Callable[[bytes], None]) -> None:
        if not self.sock:
            raise RuntimeError("socket not connected")

        def loop():
            while self._running:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    on_bytes(chunk)
                except socket.timeout:
                    continue
                except OSError:
                    break

        self._rx_thread = threading.Thread(target=loop, daemon=True)
        self._rx_thread.start()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/parser.py</h4>

This parser converts an NDJSON (Newline Delimited JSON) stream into  
<b>line-based JSON objects</b>.

- <b>Input</b>: byte chunks. TCP does not preserve message boundaries, so a message may be split across chunks or multiple messages may be combined.
- <b>Output</b>: completed JSON dictionaries passed to the `on_message(dict)` callback.
- <b>Behavior</b><br>
  (1) Accumulate data in an internal buffer and split by `\n`.  
  (2) Decode each line as UTF-8 and parse via `json.loads()`.  
  (3) On JSON parse failure, log the error and skip the line.

This module standardizes the boundary between "raw bytes" and "parsed messages".

<details><summary>Click to check the python code</summary>

```python
# utils/parser.py
import json
from typing import Callable


class NDJSONParser:
    def __init__(self):
        self._buffer = b""

    def feed(self, data: bytes, on_message: Callable[[dict], None]) -> None:
        self._buffer += data

        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            if not line:
                continue

            try:
                msg = json.loads(line.decode("utf-8"))
                on_message(msg)
            except json.JSONDecodeError as e:
                print(f"[parser] json decode error: {e}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/dispatcher.py</h4>

This dispatcher routes parsed messages (dict) to registered callbacks  
based on <b>`type` / `error`</b>.

- <b>Responsibilities</b>  
  (1) Separate message handling logic from the network/parser layers.  
  (2) Example scripts (handshake/monitor/control) only need to register handlers with the dispatcher.

- <b>Dispatch Rules (current implementation)</b>  
  (1) If `msg` contains the key `"error"`, call `on_error(msg)` (or print if not registered).  
  (2) Otherwise, dispatch using `msg.get("type")` to the corresponding `on_type[type]` callback.  
  (3) If no matching callback exists, print the event by default.

- <b>Extension Points</b>  
  Projects may explicitly separate `ack` / `event` handling by extending  
  the key-based dispatch logic inside `dispatch()`.

<details><summary>Click to check the python code</summary>

```python
# utils/dispatcher.py
from typing import Callable, Dict, Optional


class Dispatcher:
    def __init__(self):
        self.on_type: Dict[str, Callable[[dict], None]] = {}
        self.on_error: Optional[Callable[[dict], None]] = None

    def dispatch(self, msg: dict) -> None:
        if "error" in msg:
            if self.on_error:
                self.on_error(msg)
            else:
                print(f"[error] {msg}")
            return

        msg_type = msg.get("type")
        if msg_type and msg_type in self.on_type:
            self.on_type[msg_type](msg)
        else:
            print(f"[event] {msg}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/motion.py</h4>

`motion.py` provides **joint trajectory generation and reuse utilities**  
used by the CONTROL examples.

The primary purpose is to keep the CONTROL example focused by  
<b>separating trajectory generation logic</b> from communication logic.

- CONTROL transmission already involves complex timing and schema handling.
- Mixing trajectory generation into the same example would make it excessively long.
- Therefore, trajectories are generated in `motion.py`, while CONTROL examples focus on  
  "sending generated points at fixed intervals".

Role 1. **Trajectory Generation (sine wave)**
- `generate_sine_trajectory(base_deg, cycle_sec, amplitude_deg, dt_sec, total_sec, active_joint_count)`
- Applies sine displacement only to the first N joints to create oscillatory motion.
- Returns a `List[List[float]]` of **degree-based points**.

Role 2. **Trajectory Save / Load**
- `save_trajectory(points_deg, dt_sec, base_dir="data") -> saved_path`
- `load_trajectory(path) -> (dt_sec, points_deg)`
- JSON format:  
  → `dt_sec`: time interval between points (sec)  
  → `points_deg`: list of joint angle points

Usage Locations
- In `control.md` scenarios:
  - Read base pose (rad) → convert via `rad_to_deg()`
  - Generate points with `generate_sine_trajectory()`
  - Optionally save and reuse trajectories via `save_trajectory()` / `load_trajectory()`

Notes
- CONTROL `joint_traject_insert_point` assumes **degrees** for `point` values (example standard).
- `dt_sec` directly affects transmission timing and `interval/time_from_start` settings and must be preserved when saving/loading.

<details><summary>Click to check the python code</summary>

```python
# utils/motion.py
import json
import math
import os
import time
from typing import List, Tuple, Optional


def generate_sine_trajectory(
    base_deg: List[float],
    *,
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6
) -> List[List[float]]:
    if active_joint_count is None:
        active_joint_count = len(base_deg)

    omega = 2.0 * math.pi / cycle_sec
    steps = int(total_sec / dt_sec) + 1

    traj = []
    for k in range(steps):
        t = k * dt_sec
        point = []
        for i, base in enumerate(base_deg):
            if i < active_joint_count:
                offset = amplitude_deg * math.sin(omega * t)
                point.append(base + offset)
            else:
                point.append(base)
        traj.append(point)

    return traj


def save_trajectory(
    points_deg: List[List[float]],
    dt_sec: float,
    *,
    base_dir: str = "data",
) -> str:
    os.makedirs(base_dir, exist_ok=True)
    ts = time.strftime("%m%d%H%M%S")
    path = os.path.join(base_dir, f"trajectory_{ts}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "dt_sec": dt_sec,
                "points_deg": points_deg,
            },
            f,
            indent=2,
        )

    return os.path.abspath(path)


def load_trajectory(path: str) -> Tuple[float, List[List[float]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["dt_sec"], data["points_deg"]
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/api.py</h4>

This module is a thin wrapper that <b>consistently constructs JSON messages</b>  
for the Open Stream protocol.

- <b>Responsibilities</b>  
  (1) Prevent example scripts from repeatedly writing raw JSON schemas.  
  (2) Standardize payload structures per `cmd` (HANDSHAKE / MONITOR / CONTROL / STOP).

- <b>Important Notes</b>  
  (1) `api.py` does not send network data directly; it sends NDJSON lines via `net.send_line()`.  
  (2) CONTROL is a first-class protocol command; `joint_traject_*` helpers are subordinate utilities for trajectory control.

Protocol Command Overview

| cmd | Description |
| --- | ----------- |
| HANDSHAKE | Session initialization and version negotiation |
| MONITOR | Periodic state / HTTP API polling |
| CONTROL | Robot control (trajectory, etc.) |
| STOP | Stop session or streams |

Provided Methods

| API Method | cmd | Description |
| ---------- | --- | ----------- |
| `handshake(major)` | HANDSHAKE | Initialize Open Stream session |
| `monitor(url, period_ms, args=None, monitor_id=1)` | MONITOR | Periodically poll target URL |
| `monitor_stop()` | MONITOR | Stop MONITOR |
| `joint_traject_init()` | CONTROL | Initialize joint trajectory control |
| `joint_traject_insert_point(body)` | CONTROL | Send one trajectory point |
| `stop(target)` | STOP | Stop session or control/monitor |

<details><summary>Click to check the python code</summary>

```python
# utils/api.py
import json
from typing import Any, Dict, Optional


class OpenStreamAPI:
    def __init__(self, net):
        self.net = net

    def _send(self, msg: dict) -> None:
        line = json.dumps(msg, separators=(",", ":"))
        self.net.send_line(line)

    # -------------------------
    # HANDSHAKE
    # -------------------------

    def handshake(self, major: int = 1) -> None:
        self._send({
            "cmd": "HANDSHAKE",
            "payload": {
                "major": major
            },
        })

    # -------------------------
    # MONITOR
    # -------------------------

    def monitor(
        self,
        *,
        url: str,
        period_ms: int,
        args: Optional[Dict[str, Any]] = None,
        monitor_id: int = 1,
        method: str = "GET",
    ) -> None:
        if args is None:
            args = {}

        self._send({
            "cmd": "MONITOR",
            "payload": {
                "method": method,
                "url": url,
                "args": args,
                "id": monitor_id,
                "period_ms": period_ms,
            },
        })

    def monitor_stop(self) -> None:
        self._send({
            "cmd": "MONITOR",
            "payload": {
                "stop": True
            },
        })

    # -------------------------
    # STOP
    # -------------------------

    def stop(self, target: str = "session") -> None:
        self._send({
            "cmd": "STOP",
            "payload": {
                "target": target
            },
        })

    # -------------------------
    # CONTROL (joint trajectory)
    # -------------------------

    def joint_traject_init(self) -> None:
        self._send({
            "cmd": "CONTROL",
            "payload": {
                "method": "POST",
                "url": "/project/robot/trajectory/joint_traject_init",
                "args": {},
                "body": {},
            },
        })

    def joint_traject_insert_point(self, body: dict) -> None:
        self._send({
            "cmd": "CONTROL",
            "payload": {
                "method": "POST",
                "url": "/project/robot/trajectory/joint_traject_insert_point",
                "args": {},
                "body": body,
            },
        })
```

</details>

---

</div>

<br>

<br>
<h4 style="font-size:16px; font-weight:bold;">About main.py</h4>

Although not part of the <code>utils/</code> package, <code>main.py</code> plays an important role  
as the <b>execution entry point</b> for all example scenarios.

<code>main.py</code> is responsible for:
<ul>
  <li>Parsing command-line arguments (scenario type, host, port, etc.)</li>
  <li>Selecting and invoking the appropriate scenario module</li>
  <li>Providing a unified execution interface for all examples</li>
</ul>

This separation is intentional:
<ul>
  <li><code>utils/</code> contains <b>reusable, scenario-agnostic building blocks</b></li>
  <li><code>scenarios/*.py</code> contains <b>step-by-step protocol flows</b></li>
  <li><code>main.py</code> only orchestrates execution and does not implement protocol logic itself</li>
</ul>

Each example in the following sections assumes execution via <code>main.py</code>.


<br>
<h4 style="font-size:16px; font-weight:bold;">main.py (Scenario Launcher)</h4>

<code>main.py</code> provides a unified entry point for running each example scenario via command-line arguments.
It parses common options (host/port/major, etc.) and dispatches to the corresponding module under <code>scenarios/</code>.

<details><summary>Click to check the python code</summary>

```python
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control
from scenarios import stop as sc_stop


def main():
    p = argparse.ArgumentParser(description="Open Stream Client Examples")

    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)
    p.add_argument("--major", type=int, default=1)

    # -------------------------
    # MONITOR options
    # -------------------------
    p.add_argument("--url", default="/api/health")
    p.add_argument("--period-ms", type=int, default=1000)

    # -------------------------
    # CONTROL options
    # -------------------------
    p.add_argument("--http-port", type=int, default=8888)
    p.add_argument("--dt-sec", type=float, default=0.02)
    p.add_argument("--total-duration-sec", type=float, default=1.0)
    p.add_argument("--cycle-sec", type=float, default=5.0)
    p.add_argument("--amplitude-deg", type=float, default=1.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--look-ahead-time", type=float, default=0.04)

    p.add_argument("--target", \
                   choices=["session", "control", "monitor"], \
                   default="session", \
                   help="STOP target (session | control | monitor)")


    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, major=args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(
            args.host,
            args.port,
            major=args.major,
            url=args.url,
            period_ms=args.period_ms,
        )

    elif args.scenario == "control":
        sc_control.run(
            args.host,
            args.port,
            major=args.major,
            http_port=args.http_port,
            cycle_sec=args.cycle_sec,
            amplitude_deg=args.amplitude_deg,
            dt_sec=args.dt_sec,
            total_sec=args.total_duration_sec,
            active_joint_count=args.active_joint_count,
            look_ahead_time=args.look_ahead_time,
        )

    elif args.scenario == "stop":
        sc_stop.run(args.host, args.port, target="session")


if __name__ == "__main__":
    main()
```

</details>



<h4 style="font-size:16px; font-weight:bold;">Summary</h4>

* The `utils` code above is <b>reused unchanged in all subsequent examples</b>.
* It works correctly with <b>copy-and-paste only</b>, without modification.
* Starting from the next document, step-by-step scenarios for  
  <b>HANDSHAKE → MONITOR → CONTROL → STOP</b> will be explained using these utilities.
## 5.2 HANDSHAKE Example

This example demonstrates the most basic flow required to start an Open Stream session.


<h4 style="font-size:16px; font-weight:bold;">Execution Scenario</h4>

1. Establish a TCP connection
2. Start the NDJSON receive loop (parser + dispatcher wired)
3. Send HANDSHAKE
4. Confirm receipt of `handshake_ack`
5. Close the connection

<br>
<h4 style="font-size:16px; font-weight:bold;">Prerequisites</h4>

- `utils/` directory (net.py / parser.py / dispatcher.py / api.py)
- Server address and port (`49000`)


<br>
<h4 style="font-size:16px; font-weight:bold;">Example Code</h4>

To run this example, the following files must exist in your project.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py
│   ├── parser.py
│   ├── dispatcher.py
│   ├── motion.py
│   └── api.py
│
├── scenarios/
│   └── handshake.py      # Scenario code provided in this document
│
└── main.py               # Scenario launcher (entry point)
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/handshake.py</h4>

<div style="max-width:fit-content;">

```python
# scenarios/handshake.py
import time
from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI


def run(host: str, port: int, major: int) -> None:
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    # Register event handlers
    dispatcher.on_type["handshake_ack"] = lambda m: print(
        f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}"
    )
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # Connect and start receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # Send HANDSHAKE
    api.handshake(major=major)

    # Wait briefly for ACK, then close
    time.sleep(0.5)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; This is an executable scenario that sends a HANDSHAKE request and verifies receipt of `handshake_ack`.
</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake

def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, args.major)


if __name__ == "__main__":
    main()
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

Run the following command from the project root.

<div style="max-width:fit-content;">

```bash
$ python3 main.py handshake --host 192.168.1.150 --port 49000 --major 1
```
</div>

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] connection closed
```

- Note: If an error occurs, it will be received in the form  
  `{ "error": "...", "message": "...", "hint": "..." }`.
## 5.3 MONITOR Example

This example demonstrates the basic flow for starting **MONITOR streaming**  
in an Open Stream session and processing periodically received data.

<h4 style="font-size:16px; font-weight:bold;">Execution Scenario</h4>

1. Establish a TCP connection  
2. Start NDJSON receive loop (parser + dispatcher wired)  
3. Send MONITOR (method / url / period_ms / args)  
4. Confirm receipt of `monitor_ack` (or server-defined ACK type)  
5. Process streamed `monitor_data`  
6. Exit example (close connection)

※ In real operation, it is recommended to send `STOP target=monitor` when terminating streaming  
(this is covered in the STOP example).

<br>
<h4 style="font-size:16px; font-weight:bold;">Prerequisites</h4>

* `utils/` directory (net.py / parser.py / motion.py / dispatcher.py / api.py)  
* Server address and port (`49000`)  
* Target REST URL for MONITOR, `period_ms`, and `args`

<br>
<h4 style="font-size:16px; font-weight:bold;">Example Code</h4>

To run this example, the following files must exist in your project.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py
│   ├── parser.py
│   ├── dispatcher.py
│   ├── motion.py
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   └── monitor.py        # Scenario code provided in this document
│
└── main.py               # Scenario launcher (entry point)
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/monitor.py</h4>

<div style="max-width:fit-content;">

```python
# scenarios/monitor.py
import time
import threading

from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI


def run(host: str, port: int, *, major: int, url: str, period_ms: int) -> None:
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    # --- synchronization event (wait for ACK) ---
    handshake_ok = threading.Event()

    # register event handlers
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # MONITOR ACK / DATA (type names may vary by server implementation)
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # connect and start receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) HANDSHAKE
    api.handshake(major=major)

    # 2) wait for handshake_ack (timeout adjustable)
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack timeout; MONITOR will not be sent.")
        net.close()
        return

    # 3) send MONITOR
    api.monitor(url=url, period_ms=period_ms, args={})

    # wait briefly to receive stream, then exit
    # (for graceful shutdown, send STOP target=monitor as shown in STOP example)
    time.sleep(2.0)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; Executable scenario that sends a MONITOR request and prints ACK and streaming data.
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor


def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # monitor options
    p.add_argument("--url", default="/api/health")

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(
            args.host,
            args.port,
            major=args.major,
            url=args.url,
            period_ms=args.period_ms,
        )


if __name__ == "__main__":
    main()
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

<div style="max-width:fit-content;">

```bash
python3 main.py monitor --host 192.168.1.150 --port 49000 --major 1 --url /project/robot/joints/joint_states --period-ms 1000
```
</div>

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[tx] {"cmd":"MONITOR","payload":{"method":"GET","url":"/project/robot/joints/joint_states","period_ms":1000,"id":1,"args":{}}}
[ack] monitor_ack ok=None url=None period_ms=None
[event] {'type': 'data', 'id': 1, 'ts': 1000, 'svc_dur_ms': 0.224, 'result': {...}}
[net] connection closed
```

* Note: Errors are received in the form `{ "error": "...", "message": "...", "hint": "..." }`.  
* Note: The payload schema of `monitor_data` (`ts`, `value`, etc.) may vary depending on server implementation.
## 5.4 CONTROL Example (Joint Trajectory)

{% hint style="info" %}

This document provides an example of **streaming joint trajectory points** to a robot using the Open Stream **CONTROL** command.

Trajectory generation and storage are handled by `utils/motion.py`.<br>
Open Stream message construction and transmission are handled by `utils/api.py`.<br>
You can copy the code below directly into your own project.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">Prerequisites</h4>

- `utils/` directory (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream server address/port (e.g. `192.168.1.150:49000`)
- Joint state must be accessible via HTTP  
  e.g. `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Scenario Flow</h4>

1) Establish TCP connection and start receive loop  
2) Send HANDSHAKE and confirm ACK  
3) Retrieve `/project/robot/joints/joint_states` via HTTP GET (degree)  
4) Generate a degree-based trajectory using `motion.generate_sine_trajectory()`  
5) Send `CONTROL / joint_traject_init`  
6) Repeatedly send `CONTROL / joint_traject_insert_point` at dt intervals  
7) Exit (use STOP example if needed)
---

<br>
<h4 style="font-size:16px; font-weight:bold;">Directory Structure</h4>

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py
│   ├── parser.py
│   ├── dispatcher.py
│   ├── motion.py
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   ├── monitor.py
│   └── control.py
│
└── main.py
````

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">CONTROL Body Rules</h4>

It is recommended that `joint_traject_insert_point` includes the following fields.

* `interval` (sec): interval between points (e.g. `dt_sec`)
* `time_from_start` (sec): time offset from start (e.g. `index * dt_sec`)
  ※ Depending on server implementation, **omitting this field may cause errors**, so it is recommended to include it.
* `look_ahead_time` (sec): controller look-ahead time
* `point` (deg): list of joint angles

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

The code below is **runnable as-is after copy and paste**.

<details><summary>Click to check the python code</summary>

```python
# scenarios/control.py
import json
import math
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI
from utils.motion import generate_sine_trajectory, save_trajectory


def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    Retrieve joint positions via HTTP GET from /project/robot/joints/joint_states.

    Server-side:
    - position: degrees
    - velocity: deg/s
    - effort: Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET failed: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP response is not valid JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # Expected format:
        # {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # Fallback for formats like {"j1": 10.0, "j2": 20.0, ...}
            items: List[Tuple[int, float]] = []
            for k, v in data.items():
                if not isinstance(v, (int, float)):
                    continue
                if isinstance(k, str) and k.startswith("j"):
                    try:
                        idx = int(k[1:])
                        items.append((idx, float(v)))
                    except ValueError:
                        continue
            q = [v for _, v in sorted(items, key=lambda x: x[0])]

    if not q:
        raise RuntimeError(f"Cannot extract joint positions from response: {data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # trajectory parameters
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # control timing
    look_ahead_time: float = 0.1,
) -> None:
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    handshake_ok = {"ok": False}

    def on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        handshake_ok["ok"] = ok
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")

    dispatcher.on_type["handshake_ack"] = on_handshake_ack
    dispatcher.on_error = lambda e: print(f"[ERR] {e}")

    # 1) Establish TCP connection and start receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) Perform HANDSHAKE
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] handshake_ack not received; aborting.")
        net.close()
        return

    # 3) Retrieve base joint pose (degrees) via HTTP
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] base pose joints={len(base_deg)} deg-range={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) Generate joint trajectory in degrees
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] trajectory saved: {saved_path} (points={len(points_deg)}, dt={dt_sec})")

    # 5) Initialize joint trajectory control
    api.joint_traject_init()

    # 6) Stream trajectory points using CONTROL
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # degrees (converted to rad on server side)
        }
        api.joint_traject_insert_point(body)

        # Pace transmission according to dt
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py Integration Example</h4>

If you keep the existing `main.py` structure, you can invoke the `control` scenario as shown below.

<details><summary>Click to check the python code</summary>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control
from scenarios import stop as sc_stop


def main():
    p = argparse.ArgumentParser(description="Open Stream Client Examples")

    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)
    p.add_argument("--major", type=int, default=1)

    # -------------------------
    # MONITOR options
    # -------------------------
    p.add_argument("--url", default="/api/health")
    p.add_argument("--period-ms", type=int, default=1000)

    # -------------------------
    # CONTROL options
    # -------------------------
    p.add_argument("--http-port", type=int, default=8888)
    p.add_argument("--dt-sec", type=float, default=0.02)
    p.add_argument("--total-duration-sec", type=float, default=1.0)
    p.add_argument("--cycle-sec", type=float, default=1.0)
    p.add_argument("--amplitude-deg", type=float, default=5.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--look-ahead-time", type=float, default=0.1)

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, major=args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(
            args.host,
            args.port,
            major=args.major,
            url=args.url,
            period_ms=args.period_ms,
        )

    elif args.scenario == "control":
        sc_control.run(
            args.host,
            args.port,
            major=args.major,
            http_port=args.http_port,
            cycle_sec=args.cycle_sec,
            amplitude_deg=args.amplitude_deg,
            dt_sec=args.dt_sec,
            total_sec=args.total_duration_sec,
            active_joint_count=args.active_joint_count,
            look_ahead_time=args.look_ahead_time,
        )

    elif args.scenario == "stop":
        sc_stop.run(args.host, args.port, target="session")


if __name__ == "__main__":
    main()

```

---

</div>

</details>

<br>
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

1. Move the robot to its reference position. 
2. The `joint_traject_insert_point` API works only while Playback is running.  
Add the following wait instruction to the job file as-is.  
0001.job - ```wait di1```
3. Start `0001.job` in auto mode.
4. Run the following `main.py` command.

    <div style="max-width:fit-content;">

    ```bash
    # Example: Send a 30-second sine trajectory (amplitude 1 deg) with dt = 2 ms.
    # - cycle-sec=5  : One sine period (0 → 2π) corresponds to 5 seconds.
    # - With look-ahead-time = 0.04 s and dt = 0.002 s,
    #   the look-ahead buffer size is 0.04 / 0.002 = 20 points.
    #   (Tracking may be delayed until the buffer is filled with 20 points.)

    python3 main.py control \
    --host 192.168.1.150 \
    --port 49000 \
    --major 1 \
    --http-port 8888 \
    --total-duration-sec 30.0 \
    --dt-sec 0.002 \
    --look-ahead-time 0.04 \
    --amplitude-deg 1 \
    --cycle-sec 5
    ```

    </div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

Output may vary by environment, but you should generally observe the following flow.

<div style="max-width:fit-content;">

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] base pose joints=6
[INFO] trajectory saved: .../data/trajectory_XXXXXX.json (points=51, dt=0.02)
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_init", ...}
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_insert_point", ...}
...
[net] connection closed
```

</div>

---

## Summary

* CONTROL is the protocol command used to transmit robot control messages.
* Trajectory generation and storage are separated into `utils/motion.py`, so the control example focuses on the **transmission logic**.
* When sending `joint_traject_insert_point`, it is recommended to include `time_from_start` and increment it based on `dt`.
## 5.5 STOP Example (Session / Stream Termination)

{% hint style="info" %}

This document explains how to use the Open Stream **STOP** command to  
gracefully terminate the currently running **session** or **CONTROL / MONITOR stream**
in a controlled and safe manner.

- STOP is a **mandatory command** for safe termination.
- Use STOP when a CONTROL trajectory is being transmitted or a MONITOR stream is active
  and an immediate interruption is required.
- The code below is <b>fully functional</b> and can be copied and used as-is.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP Command Overview</h4>

STOP is a control command used to terminate an Open Stream session or a specific stream.

- To <b>immediately stop</b> the robot, or
- To <b>gracefully release</b> CONTROL / MONITOR streams.

When a STOP command is sent, the server cleans up its internal state
and releases related resources if necessary (trajectory buffers, monitor tasks, etc.).

---

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP Target</h4>

The STOP command specifies its termination scope using the `target` field.

| target value | Description |
|------------|------|
| `session`  | Terminate the entire Open Stream session (recommended default) |
| `control`  | Terminate only the CONTROL stream |
| `monitor`  | Terminate only the MONITOR stream |

※ Depending on implementation or version, `control` and `monitor` may be optional.  
The safest approach is to terminate the entire `session`.

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Scenario Flow</h4>

(1) Establish TCP connection and start receive loop  
(2) Perform HANDSHAKE  
(3) Send STOP command  
(4) Check server response  
(5) Close socket

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Directory Structure</h4>

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py
│   ├── parser.py
│   ├── dispatcher.py
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   ├── monitor.py
│   ├── control.py
│   └── stop.py
│
└── main.py
````

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

The following example sends a STOP command for the specified target.

<details><summary>Click to check the python code</summary>

```python
# scenarios/stop.py
import time

from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    target: str = "session",
) -> None:
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    handshake_ok = {"ok": False}

    def on_handshake_ack(m: dict) -> None:
        handshake_ok["ok"] = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}")

    dispatcher.on_type["handshake_ack"] = on_handshake_ack
    dispatcher.on_error = lambda e: print(f"[ERR] {e}")

    # 1) connect + receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) handshake
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] handshake failed; aborting stop.")
        net.close()
        return

    # 3) STOP
    print(f"[INFO] sending STOP target={target}")
    api.stop(target=target)

    # short wait (server-side processing time)
    time.sleep(0.5)

    # 4) close socket
    net.close()
```


</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py Integration Example</h4>

This shows how to invoke STOP according to the existing `main.py` scenario structure.

<div style="max-width:fit-content;">

```python
# main.py 
from scenarios import stop as sc_stop

# ...
elif args.scenario == "stop":
    sc_stop.run(
        args.host,
        args.port,
        target=args.target,
    )
```


</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

<div style="max-width:fit-content;">

```bash
# Terminate the entire session (recommended)
python main.py stop --host 192.168.1.150 --port 49000 --target session

# Terminate CONTROL only
python main.py stop --host 192.168.1.150 --port 49000 --target control

# Terminate MONITOR only
python main.py stop --host 192.168.1.150 --port 49000 --target monitor
```

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

<div style="max-width:fit-content;">

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] sending STOP target=session
[tx] {"cmd":"STOP","payload":{"target":"session"}}
[net] connection closed
```

</div>

---

## Summary

* STOP is a command used to **safely terminate** robot control and monitoring.
* It is strongly recommended to terminate CONTROL trajectory transmission using STOP.
* The safest default usage is `target=session`.
# 9. FAQ

Q1. Why is HANDSHAKE required first?
A. If the server is not in the `handshake_ok` state, it returns **412 (handshake_required)** for MONITOR / CONTROL / STOP.

Q2. CONTROL succeeded, but there is no response.
A. This is expected behavior. When CONTROL completes with HTTP 200, the response line is intentionally omitted (not sent).

Q3. Can MONITOR use POST or PUT as the method?
A. No. The `method` field in the MONITOR payload must be **"GET"**.

Q4. What if the URL contains spaces?
A. The request is rejected. URLs must not contain spaces.
<h2 style="display:flex; align-items:center; gap:8px;">
  10. Release Notes
</h2>

This section summarizes the version-by-version change history of the Open Stream interface.<br>
Each version documents feature additions, behavioral changes, fixes, and compatibility notes.

<h4 style="font-size:15px; font-weight:bold;">Release Information</h4>

<div style="max-width:fit-content;">

| *Version | ${cont_model} Version | Release Schedule | Link |
|:--:|:--:|:--:|:--:|
|1.0.0|60.34-00 ⇡|Planned for 2026.03|[🔗](1-0-0.md)|

----

</div>

*Version: **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| Field | Meaning | Compatibility Policy |
|------|---------|----------------------|
| MAJOR | Fundamental protocol changes | **Incompatible if MAJOR differs** |
| MINOR | Feature additions (backward compatible) | Compatible if MAJOR matches |
| PATCH | Bug fixes and internal improvements | Always compatible |

</div>


<br>

<h4 style="font-size:15px; font-weight:bold;">Release Note Categories</h4>

<div style="max-width:fit-content;">

| Category | Description |
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>✨ Added</b></span>|New features, commands, fields, or options added|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>🔧 Changed</b></span>|Changes to existing behavior, specifications, or defaults|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>🛠 Fixed</b></span>|Bug fixes, stability improvements, abnormal behavior corrections|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>❌ Deprecated</b></span>|Features planned for removal or no longer recommended|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>⚠ Caution</b></span>|Important usage notes that must be acknowledged for this version|

</div>

<br>

Each release document describes **only the changes introduced in that version** according to the categories above.<br>
For detailed usage instructions or protocol descriptions, refer to the corresponding reference sections in this documentation.

If a release introduces behavioral changes, it may impact existing systems.<br>
Always review the release notes for the target version before updating.
<h2 style="display:flex; align-items:center; gap:8px;">
  Release Notes – v1.0.0
  <span style="
    font-size:14px;
    font-weight:bold;
    padding:2px 6px;
    border-radius:4px;
    border:1px solid #c62828;
    color:#c62828;
  ">
    PREVIEW
  </span>
</h2>


{% hint style="warning" %}

<h4 style="font-size:15px; font-weight:bold;">Status</h4>

- This version is the first public release of the Open Stream interface.
- Official release: March 2026 (planned)

{% endhint %}

{% hint style="info" %}

<h4 style="font-size:15px; font-weight:bold;">Overview</h4>

- Open Stream is a real-time streaming-based interface designed for robot control and state acquisition.
- This release provides the core Open Stream protocol, recipe commands, and related communication rules.

{% endhint %}

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid rgb(255, 140, 0);
  font-size:15px;
  font-weight:bold;
">
  ✨ Added
</h4>

<ul>
  <li>Protocol
    <ul>
      <li>Lightweight streaming protocol based on NDJSON</li>
      <li>Bidirectional communication over a single TCP connection</li>
      <li>Command-based session management model</li>
    </ul>
  </li>

  <li>Recipe Commands
    <ul>
      <li>HANDSHAKE: Protocol version negotiation</li>
      <li>MONITOR: Periodic state data streaming (millisecond-level interval)</li>
      <li>CONTROL: Real-time control command transmission (high priority)</li>
      <li>STOP: Terminate an active session or recipe</li>
    </ul>
  </li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 6px;
  border-left:4px solid #3F51B5;
  font-size:15px;
  font-weight:bold;
">
  🔧 Changed
</h4>

<ul>
  <li>This is the initial public release; there are no changes compared to previous versions.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #2E7D32;
  font-size:15px;
  font-weight:bold;
">
  🛠 Fixed
</h4>

<ul>
  <li>This is the initial public release; there are no fixed issues.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #B71C1C;
  font-size:15px;
  font-weight:bold;
">
  ❌ Deprecated
</h4>

<ul>
  <li>This is the initial public release; there are no deprecated or removed features.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #9E9E9E;
  font-size:15px;
  font-weight:bold;
">
  ⚠ Caution
</h4>

<ul>
  <li>When CONTROL and MONITOR run concurrently, real-time performance of CONTROL is prioritized.</li>
  <li>Periodic delays may occur depending on OS scheduling and network conditions.</li>
  <li>Only one MONITOR session can be active per TCP connection.</li>
  <li>MONITOR data is not suitable for real-time control decisions.</li>
  <li>Latency and jitter may occur depending on network and client performance.</li>
</ul>

<br>

<h4 style="font-size:15px; font-weight:bold;">Related Documentation</h4>

<ul>
  <li><a href="../1-overview/README.md">Open Stream Overview</a></li>
  <li><a href="../1-overview/2-usage-considerations.md">Usage Considerations</a></li>
  <li><a href="../2-protocol/README.md">Protocol</a></li>
  <li><a href="../3-recipe/README.md">Recipe Commands</a></li>
  <li><a href="../4-examples/README.md">Examples</a></li>
  <li><a href="../9-faq/README.md">FAQ</a></li>
</ul>
