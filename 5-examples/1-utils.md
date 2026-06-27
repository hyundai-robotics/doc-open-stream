## 5.1 Common Utilities (utils)

{% hint style="info" %}

本文档提供了<b>Open Stream客户端工具代码</b>  
该代码通常用于后续所有示例。

下面的代码是<b>完全面能的可运行代码</b>，而不仅仅是示例样本。  
您可以将其直接复制到自己的项目中并按原样使用。

为了清晰和可重复性，这个示例故意使用了  
<b>"接收线程 + 阻塞套接字（带超时）"</b>模型。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

创建如下所示的`utils/`目录  
并精确复制每个文件。

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
<h4 style="font-size:16px; font-weight:bold;">工具角色</h4>

| 文件 | 角色 | 主要职责 |
| ---- | ---- | --------------------- |
| <b>net.py</b> | TCP网络层 | TCP套接字连接/断开，接收循环（线程），原始字节接收 |
| <b>parser.py</b> | NDJSON解析器 | NDJSON流解析，JSON对象创建 |
| <b>dispatcher.py</b> | 消息调度器 | 基于消息`类型 (type)` / `错误 (error)`的回调调度 |
| <b>motion.py</b> | 轨迹工具 | 正弦轨迹生成，文件保存/加载 |
| <b>api.py</b> | Open Stream API封装 | HANDSHAKE / MONITOR / CONTROL / STOP的抽象 |

</div>

<br>
<div style="max-width:fit-content;">

---

<h4 style="font-size:16px; font-weight:bold;">utils/net.py</h4>

该模块实现了负责TCP套接字连接和I/O的网络层。

<b>职责</b>  
(1) 创建、维护并关闭与Open Stream服务器的TCP连接。  
(2) 在接收线程中读取来自服务器的原始字节流，并通过回调（`on_bytes`）转发它们。  
(3) 将更高层（解析器/调度器）与直接网络I/O处理解耦。

<b>关键设计点</b>  
(1) `TCP_NODELAY`（Nagle OFF）：减少小NDJSON行的延迟。  
(2) `SO_KEEPALIVE`：帮助检测半开放连接。  
(3) 基于超时的接收循环：确保在关闭或中断期间的响应能力。

<b>主要API</b>  
(1) `connect()`：建立套接字连接并配置选项  
(2) `send_line(line)`：发送一行NDJSON（换行符自动追加）  
(3) `start_recv_loop(on_bytes)`：启动接收线程  
(4) `close()`：关闭连接

<details><summary>点击查看python代码</summary>

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

        # Nagle OFF (低延迟)
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
        print(f"[net] 已连接到 {self.host}:{self.port}")

    def close(self) -> None:
        self._running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        print("[net] 连接已关闭")

    def send_line(self, line: str) -> None:
        if not self.sock:
            raise RuntimeError("套接字未连接")
        self.sock.sendall((line + "\n").encode("utf-8"))
        print(f"[tx] {line}")

    def start_recv_loop(self, on_bytes: Callable[[bytes], None]) -> None:
        if not self.sock:
            raise RuntimeError("套接字未连接")

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

该解析器将NDJSON（换行分隔的JSON）流转换为  
<b>基于行的JSON对象</b>。

- <b>输入</b>: 字节块。 TCP不会保留消息边界，因此一条消息可能会跨块分裂，或者多个消息可能会合并。
- <b>输出</b>: 传递给`on_message(dict)`回调的完整JSON字典。
- <b>行为</b><br>
  (1) 在内部缓冲区中累积数据并按`\n`分割。  
  (2) 将每一行解码为UTF-8，并通过`json.loads()`解析。  
  (3) 在JSON解析失败时，记录错误并跳过该行。

该模块标准化了"原始字节"和"解析消息"之间的边界。

<details><summary>点击查看python代码</summary>

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
                print(f"[parser] json解码错误: {e}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/dispatcher.py</h4>

该调度器根据<b>`类型 (type)` / `错误 (error)`</b>将解析消息（dict）路由到注册的回调。

- <b>职责</b>  
  (1) 将消息处理逻辑与网络/解析层分开。  
  (2) 示例脚本（握手/监控/控制）只需要向调度器注册处理程序。

- <b>调度规则（当前实现）</b>  
  (1) 如果`内容 (msg)`包含键`"error"`，则调用`on_error(msg)`（如果未注册则打印）。  
  (2) 否则，使用`msg.get("type")`调度到相应的`on_type[type]`回调。  
  (3) 如果没有匹配的回调存在，默认情况下打印事件。

- <b>扩展点</b>  
  项目可以通过扩展`dispatch()`内部的基于键的调度逻辑，明确分离`ack` / `event`处理。

<details><summary>点击查看python代码</summary>

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
                print(f"[错误] {msg}")
            return

        msg_type = msg.get("type")
        if msg_type and msg_type in self.on_type:
            self.on_type[msg_type](msg)
        else:
            print(f"[事件] {msg}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/motion.py</h4>

`motion.py`提供了**关节轨迹生成和重用工具**  
在CONTROL示例中使用。

其主要目的是通过  
<b>将轨迹生成逻辑与通信逻辑分离</b>来保持CONTROL示例的专注。

- CONTROL传输已经涉及复杂的时序和方案处理。
- 将轨迹生成混合到同一示例中会使其过长。
- 因此，轨迹在`motion.py`中生成，而CONTROL示例专注于  
  “以固定间隔发送生成的点”。

角色1. **轨迹生成（正弦波）**
- `generate_sine_trajectory(base_deg, cycle_sec, amplitude_deg, dt_sec, total_sec, active_joint_count)`
- 仅对前N个关节应用正弦位移，以产生振荡运动。
- 返回`List[List[float]]`的**基于度数的点**。

角色2. **轨迹保存/加载**
- `save_trajectory(points_deg, dt_sec, base_dir="data") -> saved_path`
- `load_trajectory(path) -> (dt_sec, points_deg)`
- JSON格式：  
  → `dt_sec`：点之间的时间间隔（秒）  
  → `points_deg`：关节角度点的列表

使用位置
- 在`control.md`场景中：
  - 读取基准姿态（弧度）→通过`rad_to_deg()`转换
  - 使用`generate_sine_trajectory()`生成点
  - 可选地通过`save_trajectory()` / `load_trajectory()`保存和重用轨迹

备注
- CONTROL `joint_traject_insert_point`假定`point`值为**度**（示例标准）。
- `dt_sec`直接影响传输时序和`interval/time_from_start`设置，保存/加载时必须保留。

<details><summary>点击查看python代码</summary>

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

该模块是一个薄包装器，<b>一致地构建JSON消息</b>  
用于Open Stream协议。

- <b>职责</b>  
  (1) 防止示例脚本重复编写原始JSON模式。  
  (2) 针对`cmd`（HANDSHAKE / MONITOR / CONTROL / STOP）标准化负载结构。

- <b>重要说明</b>  
  (1) `api.py`不直接发送网络数据；它通过`net.send_line()`发送NDJSON行。  
  (2) CONTROL是一个一流的协议命令；`joint_traject_*`辅助工具是轨迹控制的从属工具。

协议命令概述

| cmd | 描述 |
| --- | ----------- |
| HANDSHAKE | 会话初始化和版本协商 |
| MONITOR | 周期性状态 / HTTP API轮询 |
| CONTROL | 机器人控制（轨迹等） |
| STOP | 停止会话或流 |

提供的方法

| API方法 | cmd | 描述 |
| ---------- | --- | ----------- |
| `handshake(major)` | HANDSHAKE | 初始化Open Stream会话 |
| `monitor(url, period_ms, args=None, monitor_id=1)` | MONITOR | 定期轮询目标URL |
| `monitor_stop()` | MONITOR | 停止MONITOR |
| `joint_traject_init()` | CONTROL | 初始化关节轨迹控制 |
| `joint_traject_insert_point(body)` | CONTROL | 发送一个轨迹点 |
| `stop(target)` | STOP | 停止会话或控制/监控 |
<details><summary>点击以查看python代码</summary>

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
    # 握手
    # -------------------------

    def handshake(self, major: int = 1) -> None:
        self._send({
            "cmd": "HANDSHAKE",
            "payload": {
                "major": major
            },
        })

    # -------------------------
    # 监控
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
    # 停止
    # -------------------------

    def stop(self, target: str = "session") -> None:
        self._send({
            "cmd": "STOP",
            "payload": {
                "target": target
            },
        })

    # -------------------------
    # 控制（关节轨迹）
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
<h4 style="font-size:16px; font-weight:bold;">关于main.py</h4>

虽然不是<code>utils/</code>包的一部分，<code>main.py</code>在所有示例场景中扮演着重要角色  
作为<b>执行入口点</b>。

<code>main.py</code>负责：
<ul>
  <li>解析命令行参数（场景类型、主机、端口等）</li>
  <li>选择并调用适当的场景模块</li>
  <li>为所有示例提供统一的执行接口</li>
</ul>

这种分离是故意的：
<ul>
  <li><code>utils/</code>包含<b>可重用、不依赖场景的构建模块</b></li>
  <li><code>scenarios/*.py</code>包含<b>逐步的协议流程</b></li>
  <li><code>main.py</code>只是协调执行，并不实现协议逻辑</li>
</ul>

以下部分中的每个示例假定通过<code>main.py</code>执行。

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py（场景启动器）</h4>

<code>main.py</code>提供了一个统一的入口点，通过命令行参数运行每个示例场景。
它解析常见选项（主机/端口/主要等），并分发到<code>scenarios/</code>下的相应模块。

<details><summary>点击以查看python代码</summary>

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
    p.add_argument("--cycle-sec", type=float, default=5.0)
    p.add_argument("--amplitude-deg", type=float, default=1.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--look-ahead-time", type=float, default=0.04)

    p.add_argument("--target", \
                   choices=["session", "control", "monitor"], \
                   default="session", \
                   help="停止目标（session | control | monitor）")


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

<h4 style="font-size:16px; font-weight:bold;">总结</h4>

* 上面的`utils`代码在所有后续示例中<b>保持不变地重用</b>。
* 它正确运行，<b>只需复制和粘贴</b>，无需修改。
* 从下一个文档开始，将使用这些工具逐步解释  
  <b>握手 → 监控 → 控制 → 停止</b>的场景。