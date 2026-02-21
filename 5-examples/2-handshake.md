## 5.2 握手示例

此示例演示开始 Open Stream 会话所需的最基本流程。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接
2. 启动 NDJSON 接收循环（解析器 + 调度器连接）
3. 发送 握手
4. 确认收到 `handshake_ack`
5. 关闭连接

<br>
<h4 style="font-size:16px; font-weight:bold;">先决条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / api.py)
- 服务器地址和端口 (`49000`)

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，您的项目中必须存在以下文件。

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
│   └── handshake.py      # 本文档提供的场景代码
│
└── main.py               # 场景启动器（入口点）
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

    # 注册事件处理程序
    dispatcher.on_type["handshake_ack"] = lambda m: print(
        f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}"
    )
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 发送 握手
    api.handshake(major=major)

    # 简短等待 ACK，然后关闭
    time.sleep(0.5)
    net.close()
```
<div style="max-width:fit-content;">
  &rightarrow; 这是一个可执行的场景，发送 HANDSHAKE 请求并验证 `handshake_ack` 的接收。
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake

def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream 示例")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # 通用选项
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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

从项目根目录运行以下命令。

<div style="max-width:fit-content;">

```bash
$ python3 main.py handshake --host 192.168.1.150 --port 49000 --major 1
```
</div>

<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] 连接关闭
```

- 注意：如果发生错误，将以以下格式接收  
  `{ "error": "...", "message": "...", "hint": "..." }`.