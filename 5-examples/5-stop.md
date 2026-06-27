## 5.5 停止示例 (会话 / 流终止)

{% hint style="info" %}

本文件解释如何使用 Open Stream **停止** 命令 
以受控和安全的方式优雅地终止当前运行的 **会话** 或 **控制 / 监控流**。

- 停止是安全终止的 **强制命令**。
- 当正在传输控制轨迹或监控流处于活动状态并需要立即中断时，请使用停止。
- 下面的代码是 <b>完全功能性</b> 的，可以直接复制和使用。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">停止命令概述</h4>

停止是一个控制命令，用于终止 Open Stream 会话或特定流。

- <b>立即停止</b> 机器人，或
- <b>优雅释放</b> 控制 / 监控流。

当发送停止命令时，服务器会清理其内部状态
并在必要时释放相关资源（轨迹缓冲区、监控任务等）。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">停止目标</h4>

停止命令通过 `目标 (target)` 字段指定其终止范围。

| target value | 描述 |
|------------|------|
| `session`  | 终止整个 Open Stream 会话（推荐默认） |
| `control`  | 仅终止控制流 |
| `monitor`  | 仅终止监控流 |

* 根据实现或版本，`control` 和 `monitor` 可能是可选的。  
最安全的方法是终止整个 `session`。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

(1) 建立 TCP 连接并开始接收循环  
(2) 执行握手  
(3) 发送停止命令  
(4) 检查服务器响应  
(5) 关闭套接字

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
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   ├── monitor.py
│   ├── control.py
│   └── stop.py
│
└── main.py
````</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

以下示例为指定目标发送停止命令。

<details><summary>点击查看 Python 代码</summary>

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
        print("[ERR] 握手失败；中止停止。")
        net.close()
        return

    # 3) 停止
    print(f"[INFO] 发送停止 target={target}")
    api.stop(target=target)

    # 短暂等待（服务器端处理时间）
    time.sleep(0.5)

    # 4) 关闭套接字
    net.close()
```


</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

这显示了如何根据现有的 (

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

以下示例为指定目标发送停止命令。

<details><summary>点击查看 Python 代码</summary>

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
        print("[ERR] 握手失败；中止停止。")
        net.close()
        return

    # 3) 停止
    print(f"[INFO] 发送停止 target={target}")
    api.stop(target=target)

    # 短暂等待（服务器端处理时间）
    time.sleep(0.5)

    # 4) 关闭套接字
    net.close()
```


</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

这显示了如何根据现有的 )`main.py` 场景结构调用停止。

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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

<div style="max-width:fit-content;">

```bash
# 终止整个会话（推荐）
python main.py stop --host 192.168.1.150 --port 49000 --target session

# 仅终止控制
python main.py stop --host 192.168.1.150 --port 49000 --target control

# 仅终止监控
python main.py stop --host 192.168.1.150 --port 49000 --target monitor
```

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

<div style="max-width:fit-content;">

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] 发送停止 target=session
[tx] {"cmd":"STOP","payload":{"target":"session"}}
[net] 连接关闭
```

</div>

---

#### 摘要

* 停止是用于 **安全终止** 机器人控制和监控的命令。
* 强烈建议使用停止终止控制轨迹传输。
* 最安全的默认用法是 )`target=session`。