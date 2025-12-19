# 5.1 공통 유틸리티 (utils)

이 문서에서는 이후 모든 예제에서 공통으로 사용되는  
**Open Stream 클라이언트 유틸리티 코드**를 제공합니다.

아래 코드는 **설명용 샘플이 아니라 실제로 동작하는 코드**이며,  
사용자는 이를 그대로 복사하여 자신의 프로젝트에 사용할 수 있습니다.

※ 본 예제는 이해와 재현성을 위해 "수신 스레드 + 블로킹 소켓(timeout)" 방식으로 구성했습니다.  


## 디렉토리 구성

아래와 같이 `utils/` 디렉토리를 생성하고,
각 파일을 그대로 복사하여 저장하십시오.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
└── utils/
    ├── net.py
    ├── parser.py
    ├── dispatcher.py
    └── api.py
```

</div>

## utils/net.py

TCP 소켓 연결 및 송수신 담당

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

        # --- socket options (recommended defaults) ---
        # 1) Nagle OFF: reduce latency for small NDJSON lines (ACK/STOP/etc.)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

        # 2) Keep-Alive ON: detect half-open TCP connections at OS level
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass

        # recv loop responsiveness
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

---

## utils/parser.py

NDJSON 스트림 파서 (`\n` 기준)

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

---

## utils/dispatcher.py

type / error 기반 이벤트 분기

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

---

## utils/api.py

레시피 명령 래퍼 (HANDSHAKE / MONITOR / CONTROL / STOP)

```python
# utils/api.py
import json
from typing import Any, Dict, Optional

from utils.net import NetClient


class OpenStreamAPI:
    def __init__(self, net: NetClient):
        self.net = net

    def handshake(self, major: int) -> None:
        self._send_cmd("HANDSHAKE", {"major": major})

    def monitor(self, *, url: str, period_ms: int, args: Dict[str, Any]) -> None:
        payload = {
            "method": "GET",
            "url": url,
            "period_ms": period_ms,
            "id": 1, # this required field is only for the initial version.
            "args": args,
        }
        self._send_cmd("MONITOR", payload)

    def control(
        self,
        *,
        method: str,
        url: str,
        args: Dict[str, Any],
        body: Optional[Any] = None,
    ) -> None:
        payload = {
            "method": method,
            "url": url,
            "args": args,
        }
        if body is not None:
            payload["body"] = body

        self._send_cmd("CONTROL", payload)

    def stop(self, target: str) -> None:
        self._send_cmd("STOP", {"target": target})

    def _send_cmd(self, cmd: str, payload: dict) -> None:
        line = json.dumps({"cmd": cmd, "payload": payload}, separators=(",", ":"))
        self.net.send_line(line)
```

---

## 요약

* 위 `utils` 코드는 **이후 모든 예제에서 그대로 재사용**됩니다.
* 수정 없이 복사하여 사용해도 정상 동작합니다.
* 다음 예제부터는 이 유틸리티를 기반으로  
  HANDSHAKE, MONITOR, CONTROL, STOP 시나리오를 단계적으로 실행합니다.
