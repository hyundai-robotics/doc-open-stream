## 5.2 HANDSHAKE Example

This example demonstrates the most basic flow required to start an Open Stream session.


<h4 style="font-size:16px; font-weight:bold;">Execution Scenario</h4>

1. Establish a TCP connection
2. Start the NDJSON receive loop (parser + dispatcher wired)
3. Send HANDSHAKE
4. Confirm receipt of `handshake_ack`
5. Close the connection

<br>
<h4 style="font-size:16px; font-weight:bold;">Prerequisites</h4>

- `utils/` directory (net.py / parser.py / dispatcher.py / api.py)
- Server address and port (`49000`)


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
│   └── handshake.py      # Scenario code provided in this document
│
└── main.py               # Scenario launcher (entry point)
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

    # Register event handlers
    dispatcher.on_type["handshake_ack"] = lambda m: print(
        f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}"
    )
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # Connect and start receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # Send HANDSHAKE
    api.handshake(major=major)

    # Wait briefly for ACK, then close
    time.sleep(0.5)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; This is an executable scenario that sends a HANDSHAKE request and verifies receipt of `handshake_ack`.
</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake

def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
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
<h4 style="font-size:16px; font-weight:bold;">How to Run</h4>

Run the following command from the project root.

<div style="max-width:fit-content;">

```bash
$ python3 main.py handshake --host 192.168.1.150 --port 49000 --major 1
```
</div>

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] connection closed
```

- Note: If an error occurs, it will be received in the form  
  `{ "error": "...", "message": "...", "hint": "..." }`.
