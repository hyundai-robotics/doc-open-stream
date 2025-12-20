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
