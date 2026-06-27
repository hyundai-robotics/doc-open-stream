## 5.3 MONITOR 示例

此示例演示了在 Open Stream 会话中启动 **MONITOR 流** 的基本流程，以及处理周期性接收的数据。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接  
2. 启动 NDJSON 接收循环（解析器 + 派发器连接）  
3. 发送 MONITOR（方法 / URL / period_ms / 参数）  
4. 确认收到 `monitor_ack`（或服务器定义的 ACK 类型）  
5. 处理流式 `monitor_data`  
6. 退出示例（关闭连接）

* 在实际操作中，建议在终止流时发送 `STOP target=monitor`  
（这在 STOP 示例中有所涵盖）。

<br>
<h4 style="font-size:16px; font-weight:bold;">前提条件</h4>

* `utils/` 目录（net.py / parser.py / motion.py / dispatcher.py / api.py）  
* 服务器地址和端口（`49000`）  
* MONITOR 的目标 REST URL、`period_ms` 和 `args`

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，以下文件必须存在于您的项目中。

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
│   └── monitor.py        # 本文档提供的场景代码
│
└── main.py               # 场景启动器（入口点）
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

    # --- 同步事件（等待 ACK） ---
    handshake_ok = threading.Event()

    # 注册事件处理程序
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # MONITOR ACK / 数据（类型名称可能因服务器实现而异）
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) 握手
    api.handshake(major=major)

    # 2) 等待 handshake_ack（超时可调）
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack 超时；将不发送 MONITOR。")
        net.close()
        return

    # 3) 发送 MONITOR
    api.monitor(url=url, period_ms=period_ms, args={})

    # 等待一段时间以接收流，然后退出
    # （为了优雅关机，发送 STOP target=monitor，如 STOP 示例中所示）
    time.sleep(2.0)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; 可执行场景，发送 MONITOR 请求并打印 ACK 和流数据。
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
    p = argparse.ArgumentParser(description="Open Stream 示例")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # 通用选项
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # monitor 选项
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
            period_ms=args.period.ms,
        )


if __name__ == "__main__":
    main()
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

<div style="max-width:fit-content;">

```bash
python3 main.py monitor --host 192.168.1.150 --port 49000 --major 1 --url /project/robot/joints/joint_states --period-ms 1000
```
</div>

<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[tx] {"cmd":"MONITOR","payload":{"method":"GET","url":"/project/robot/joints/joint_states","period_ms":1000,"id":1,"args":{}}}
[ack] monitor_ack ok=None url=None period_ms=None
[event] {'type': 'data', 'id': 1, 'ts': 1000, 'svc_dur_ms': 0.224, 'result': {...}}
[net] 连接关闭
```

* 注意：错误以 `{ "error": "...", "message": "...", "hint": "..." }` 的形式接收。  
* 注意：`monitor_data` 的有效负载模式（`ts`、`值 (value)` 等）可能因服务器实现而异。