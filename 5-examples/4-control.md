## 5.4 控制示例（关节轨迹）

{% hint style="info" %}

本文档提供了一个使用 Open Stream **控制** 命令向机器人**流式传输关节轨迹点**的示例。

轨迹生成和存储由 `utils/motion.py` 处理。<br>
Open Stream 消息构建和传输由 `utils/api.py` 处理。<br>
您可以将以下代码直接复制到您自己的项目中。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">前提条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream 服务器地址/端口 (例如 `192.168.1.150:49000`)
- 必须通过 HTTP 访问关节状态  
  例如 `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

1) 建立 TCP 连接并启动接收循环  
2) 发送握手并确认 ACK  
3) 通过 HTTP GET 获取 `/project/robot/joints/joint_states`（度）  
4) 使用 `motion.generate_sine_trajectory()` 生成基于度的轨迹  
5) 发送 `CONTROL / joint_traject_init`  
6) 在 dt 间隔内重复发送 `CONTROL / joint_traject_insert_point`  
7) 退出（如有需要，请使用停止示例）
---

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

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
````</div>
---

<br>
<h4 style="font-size:16px; font-weight:bold;">控制主体规则</h4>

建议 (

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">控制主体规则</h4>

建议 )`joint_traject_insert_point`包括以下字段。

* ( 包括以下字段。

* )`interval`(秒): 点之间的间隔 (例如 ( (秒): 点之间的间隔 (例如 )`dt_sec`)
* ()
* )`time_from_start`(秒): 从开始的时间偏移 (例如 ( (秒): 从开始的时间偏移 (例如 )`index * dt_sec`)
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* ()
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* )`look_ahead_time`(秒): 控制器的前瞻时间
* ( (秒): 控制器的前瞻时间
* )`point`(度): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

下面的代码是**在复制和粘贴后可直接运行的**。

<details><summary>点击查看python代码</summary>

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
    通过HTTP GET从 /project/robot/joints/joint_states 获取关节位置。

    服务器端：
    - 位置：度
    - 速度：度/秒
    - 努力：牛米
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET失败: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP响应不是有效的JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[度...], "velocity":[度/秒...], "effort":[牛米...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式如 {"j1": 10.0, "j2": 20.0, ...}
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
        raise RuntimeError(f"无法从响应中提取关节位置: {data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # 轨迹参数
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # 控制时机
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

    # 1) 建立TCP连接并开始接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 进行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 没有收到握手确认；正在中止。")
        net.close()
        return

    # 3) 通过HTTP获取基础关节姿势（度）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] 基础姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) 生成关节轨迹（度）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] 轨迹已保存: {saved_path} (点数={len(points_deg)}, dt={dt_sec})")

    # 5) 初始化关节轨迹控制
    api.joint_traject_init()

    # 6) 使用控制流轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据dt调整传输速率
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

如果您保留现有的 ( (deg): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

下面的代码是**在复制和粘贴后可以直接运行的**。

<details><summary>点击查看 Python 代码</summary>

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
    通过 HTTP GET 从 /project/robot/joints/joint_states 获取关节位置。

    服务器端：
    - position: 度
    - velocity: deg/s
    - effort: Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET 失败：{url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP 响应不是有效的 JSON：{raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式像 {"j1": 10.0, "j2": 20.0, ...}
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
        raise RuntimeError(f"无法从响应中提取关节位置：{data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # 轨迹参数
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # 控制时序
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

    # 1）建立 TCP 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2）执行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 未收到 handshake_ack；中止。")
        net.close()
        return

    # 3）通过 HTTP 获取基础关节姿态（度）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[信息] 基础姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4）生成关节轨迹（度）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[信息] 轨迹已保存：{saved_path} （点数={len(points_deg)}, dt={dt_sec}）")

    # 5）初始化关节轨迹控制
    api.joint_traject_init()

    # 6）使用控制流轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据 dt 调整传输速度
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```
</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

如果保持现有的`)`main.py`结构，可以调用(`)control`场景，如下所示。

<details><summary>点击检查 Python 代码</summary>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control
from scenarios import stop as sc_stop


def main():
    p = argparse.ArgumentParser(description="Open Stream 客户端示例")

    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)
    p.add_argument("--major", type=int, default=1)

    # -------------------------
    # 监控选项
    # -------------------------
    p.add_argument("--url", default="/api/health")
    p.add_argument("--period-ms", type=int, default=1000)

    # -------------------------
    # 控制选项
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
<h4 style="font-size:16px; font-weight:bold;">运行方法</h4>

1. 将机器人移动到参考位置。
2. ( 场景如下所示。

<details><summary>点击查看 python 代码</summary>

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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

1. 将机器人移动到参考位置。
2. )`joint_traject_insert_point`API仅在播放过程中有效。  
请如实将以下等待指令添加到作业文件中。  
0001.job - ```wait di1```
3. 启动( API仅在播放过程中有效。  
请如实将以下等待指令添加到作业文件中。  
0001.job - ```wait di1```
3. 以自动模式启动)`0001.job`。
4. 以自动模式运行以下(。
4. 以自动模式运行以下)`main.py`命令。

    <div style="max-width:fit-content;">

    ```bash
    # 示例：发送一个30秒的正弦轨迹（幅度1度），dt = 2毫秒。
    # - cycle-sec=5  : 一个正弦周期（0 → 2π）对应5秒。
    # - 设定前瞻时间为0.04秒，dt为0.002秒，
    #   前瞻缓冲区大小为0.04 / 0.002 = 20个点。
    #   （跟踪可能会延迟，直到缓冲区填充20个点。）

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
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

输出可能会因环境而异，但您通常应该观察到以下流程。
<div style="max-width:fit-content;">

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] 基础姿态 关节数=6
[INFO] 轨迹已保存: .../data/trajectory_XXXXXX.json (点数=51, dt=0.02)
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_init", ...}
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_insert_point", ...}
...
[net] 连接已关闭
```

</div>

---

## 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储被分开成（命令。

    <div style="max-width:fit-content;">

    ```bash
    # 示例: 发送 30 秒的正弦轨迹 (振幅 1 度)，dt = 2 毫秒。
    # - cycle-sec=5  : 一个正弦周期 (0 → 2π) 对应 5 秒。
    # - 预瞻时间 = 0.04 s 和 dt = 0.002 s,
    #   预瞻缓冲区大小为 0.04 / 0.002 = 20 个点。
    #   (跟踪可能会延迟，直到缓冲区填满 20 个点。)

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
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

输出可能因环境而异，但您通常应观察到以下流程。

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

## 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储分开到)`utils/motion.py`中，因此控制示例专注于**传输逻辑**。
* 发送时(，因此控制示例专注于**传输逻辑**。
* 发送)`joint_traject_insert_point`时，建议包含(，建议包含)`time_from_start`并基于(和基于)`dt`进行增量。