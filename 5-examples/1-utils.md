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
﻿import argparse

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
