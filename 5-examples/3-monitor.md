## 5.3 MONITOR Example

This example demonstrates the basic flow for starting **MONITOR streaming**  
in an Open Stream session and processing periodically received data.

<h4 style="font-size:16px; font-weight:bold;">Execution Scenario</h4>

1. Establish a TCP connection  
2. Start NDJSON receive loop (parser + dispatcher wired)  
3. Send MONITOR (method / url / period_ms / args)  
4. Confirm receipt of `monitor_ack` (or server-defined ACK type)  
5. Process streamed `monitor_data`  
6. Exit example (close connection)

* In real operation, it is recommended to send `STOP target=monitor` when terminating streaming  
(this is covered in the STOP example).

<br>
<h4 style="font-size:16px; font-weight:bold;">Prerequisites</h4>

* `utils/` directory (net.py / parser.py / motion.py / dispatcher.py / api.py)  
* Server address and port (`49000`)  
* Target REST URL for MONITOR, `period_ms`, and `args`

<br>
<h4 style="font-size:16px; font-weight:bold;">Example Code</h4>

To run this example, the following files must exist in your project.

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
│   └── monitor.py        # Scenario code provided in this document
│
└── main.py               # Scenario launcher (entry point)
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

    # --- synchronization event (wait for ACK) ---
    handshake_ok = threading.Event()

    # register event handlers
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # MONITOR ACK / DATA (type names may vary by server implementation)
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # connect and start receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) HANDSHAKE
    api.handshake(major=major)

    # 2) wait for handshake_ack (timeout adjustable)
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack timeout; MONITOR will not be sent.")
        net.close()
        return

    # 3) send MONITOR
    api.monitor(url=url, period_ms=period_ms, args={})

    # wait briefly to receive stream, then exit
    # (for graceful shutdown, send STOP target=monitor as shown in STOP example)
    time.sleep(2.0)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; Executable scenario that sends a MONITOR request and prints ACK and streaming data.
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
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # monitor options
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
            period_ms=args.period_ms,
        )


if __name__ == "__main__":
    main()
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

<div style="max-width:fit-content;">

```bash
python3 main.py monitor --host 192.168.1.150 --port 49000 --major 1 --url /project/robot/joints/joint_states --period-ms 1000
```
</div>

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[tx] {"cmd":"MONITOR","payload":{"method":"GET","url":"/project/robot/joints/joint_states","period_ms":1000,"id":1,"args":{}}}
[ack] monitor_ack ok=None url=None period_ms=None
[event] {'type': 'data', 'id': 1, 'ts': 1000, 'svc_dur_ms': 0.224, 'result': {...}}
[net] connection closed
```

* Note: Errors are received in the form `{ "error": "...", "message": "...", "hint": "..." }`.  
* Note: The payload schema of `monitor_data` (`ts`, `value`, etc.) may vary depending on server implementation.
