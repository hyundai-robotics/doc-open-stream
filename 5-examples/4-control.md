## 5.4 CONTROL 예제 (Joint Trajectory)

{% hint style="info" %}

이 문서에서는 Open Stream의 **CONTROL** 명령을 이용해  로봇에 **joint trajectory 포인트를 스트리밍 전송**하는 예제를 제공합니다.

Trajectory 생성/저장은 `utils/motion.py`에서 담당합니다.<br>
Open Stream 메시지 구성/전송은 `utils/api.py`에서 담당합니다.<br>
사용자는 아래 코드를 그대로 복사하여 자신의 프로젝트에 사용할 수 있습니다.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">사전 준비</h4>

- `utils/` 디렉토리 (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream 서버 주소/포트 (예: `192.168.1.150:49000`)
- HTTP로 joint state 조회 가능해야 함  
  예: `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">시나리오 흐름</h4>

1) TCP 연결 및 수신 루프 시작  
2) HANDSHAKE 전송 및 ack 확인  
3) HTTP GET으로 `/project/robot/joints/joint_states` 조회 (rad)  
4) `motion.rad_to_deg()`로 deg 변환  
5) `motion.generate_sine_trajectory()`로 deg trajectory 생성  
6) `CONTROL / joint_traject_init` 전송  
7) `CONTROL / joint_traject_insert_point`를 dt 간격으로 반복 전송  
8) 종료 (필요 시 STOP 예제 사용)
---

<br>
<h4 style="font-size:16px; font-weight:bold;">디렉토리 구성</h4>

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
│   └── control.py
│
└── main.py
````

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">CONTROL Body 규칙</h4>

`joint_traject_insert_point`는 아래 필드를 포함하는 것을 권장합니다.

* `interval` (sec): 포인트 간 간격 (예: `dt_sec`)
* `time_from_start` (sec): 시작 기준 시간 (예: `index * dt_sec`)
  ※ 서버 구현에 따라 이 필드는 **누락 시 오류**가 날 수 있으므로 포함을 권장합니다.
* `look_ahead_time` (sec): 제어 선행 시간
* `point` (deg): joint 각도 리스트

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

아래 코드는 **그대로 복사-붙여넣기 후 실행 가능한 코드**입니다.

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
from utils.motion import generate_sine_trajectory, save_trajectory  # rad_to_deg 제거


def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    /project/robot/joints/joint_states 를 HTTP GET으로 조회해 joint positions(deg) 리스트를 반환한다.

    (서버 C++ 구현 기준)
    - position: deg 단위로 내려옴
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
        # C++ 구현은 {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]} 형태
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # e.g. {"j1": 10.0, "j2": 20.0, ...} 형태도 방어
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
    # trajectory
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

    # 1) connect + recv loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) handshake
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] handshake_ack not received; aborting.")
        net.close()
        return

    # 3) base pose (deg) via HTTP  <-- 여기 핵심
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] base pose joints={len(base_deg)} deg-range={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) trajectory 생성 (deg)
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

    # 5) CONTROL init
    api.joint_traject_init()

    # 6) CONTROL insert_point streaming
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),   # 유효한 time_from_start 사용
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg], # point는 deg (서버가 deg를 rad로 변환)
        }
        api.joint_traject_insert_point(body)

        # dt에 맞춰 송신 (단순 예제)
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 연결 예시</h4>

기존 `main.py` 구조를 유지한다면, `control` 시나리오를 아래처럼 호출할 수 있습니다.

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
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

1. 로봇을 원점 위치로 이동 시킵니다. 
2. joint_traject_insert_point API 의 동작 조건은 Playback 이 재생 중일 때 입니다.  
하기 wait 문을 job 에 그대로 작성합니다.  
0001.job - ```wait di1```
3. 0001.job 을 자동모드에서 start 합니다.
4. 하기 main.py 수행문을 실행합니다.

    <div style="max-width:fit-content;">

    ```bash
    # 예: 30초 길이의 sine trajectory(진폭 1 deg)를 dt=2ms로 전송합니다.
    # - cycle-sec=5  : sine 파 1주기(0→2π)가 5초에 해당합니다.
    # - look-ahead-time=0.04s, dt=0.002s 이므로, look-ahead 버퍼는 0.04/0.002 = 20 포인트입니다.
    #   (버퍼에 20개의 point 가 찰 때까지 추종이 지연될 수 있습니다.)

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

환경에 따라 출력은 달라질 수 있으나, 일반적으로 아래 흐름을 확인할 수 있습니다.

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

## 요약

* CONTROL은 로봇 제어 메시지를 전송하는 프로토콜 명령입니다.
* Trajectory 생성/저장은 `utils/motion.py`에 분리하여, control 예제는 **전송 로직**에 집중합니다.
* `joint_traject_insert_point` 전송 시 `time_from_start`를 포함하고, `dt` 기반으로 증가시키는 것을 권장합니다.