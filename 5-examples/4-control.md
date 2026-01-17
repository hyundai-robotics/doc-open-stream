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
  * Depending on server implementation, **omitting this field may cause errors**, so it is recommended to include it.
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
