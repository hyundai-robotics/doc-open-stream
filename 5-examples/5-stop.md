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
