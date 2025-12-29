## 5.1 공통 유틸리티 (utils)

{% hint style="info" %}

이 문서에서는 이후 모든 예제에서 공통으로 사용되는
<b>Open Stream 클라이언트 유틸리티 코드</b>를 제공합니다.

아래 코드는 <b>설명용 샘플이 아니라 실제로 동작하는 코드</b>이며,
사용자는 이를 그대로 복사하여 자신의 프로젝트에 사용할 수 있습니다.

※ 본 예제는 이해와 재현성을 위해
<b>“수신 스레드 + 블로킹 소켓(timeout)” 방식</b>으로 구성했습니다.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">디렉토리 구성</h4>

아래와 같이 `utils/` 디렉토리를 생성하고,
각 파일을 그대로 복사하여 저장하십시오.

<div style = "max-width: fit-content;">

```text
OpenStreamClient/
└── utils/
    ├── net.py
    ├── parser.py
    ├── dispatcher.py
    ├── motion.py
    └── api.py
```

<br>
<h4 style="font-size:16px; font-weight:bold;">유틸 역할</h4>

| 파일명               | 역할                 | 주요 기능                                    |
| ----------------- | ------------------ | ---------------------------------------- |
| <b>net.py</b>        | TCP 네트워크 계층        | TCP 소켓 연결/해제, 수신 루프(thread), raw byte 수신 |
| <b>parser.py</b>     | NDJSON 파서          | NDJSON 스트림 파싱, JSON 객체 생성                |
| <b>dispatcher.py</b> | 메시지 분기             | 메시지 type/error 기준 콜백 분기                  |
| <b>motion.py</b>     | Trajectory 유틸리티    | sin trajectory 생성, 파일 저장/로드              |
| <b>api.py</b>        | Open Stream API 래퍼 | HANDSHAKE / MONITOR / CONTROL / STOP 추상화 |

</div>



<br>
<div style="max-width:fit-content;">

---

<h4 style="font-size:16px; font-weight:bold;">utils/net.py</h4>

TCP 소켓 연결 및 송수신을 담당하는 네트워크 레이어입니다.

<b>역할</b>  
  (1) Open Stream 서버와의 TCP 연결을 생성/유지/종료합니다.  
  (2) 서버로부터 들어오는 raw byte 스트림을 수신 스레드에서 읽어 콜백(`on_bytes`)으로 전달합니다.  
  (3) 상위 계층(parser/dispatcher)은 네트워크 I/O를 직접 다루지 않아도 되도록 분리합니다.

<b>주요 설계 포인트</b>  
  (1) `TCP_NODELAY`(Nagle OFF): 작은 NDJSON 라인의 지연을 줄입니다.  
  (2) `SO_KEEPALIVE`: half-open 연결 감지에 도움을 줍니다.  
  (3) `timeout` 기반 recv loop: 종료/중단 시 반응성을 확보합니다.

<b>주요 API</b>  
  (1) `connect()`: 소켓 연결 및 옵션 설정  
  (2) `send_line(line)`: NDJSON 1라인 전송(자동 개행 포함)  
  (3) `start_recv_loop(on_bytes)`: 수신 스레드 시작  
  (4) `close()`: 연결 종료

<details><summary>Click to check the python code</summary>

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

        # Nagle OFF (low latency)
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

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/parser.py</h4>

NDJSON(Newline Delimited JSON) 스트림을 <b>라인 단위 JSON 객체</b>로 변환하는 파서입니다.

- <b>입력</b>: `bytes` 조각(chunk). TCP는 메시지 경계를 보장하지 않기 때문에, 한 메시지가 여러 chunk로 쪼개지거나 여러 메시지가 한 chunk에 합쳐져 올 수 있습니다.
- <b>출력</b>: 완성된 JSON(dict)을 `on_message(dict)` 콜백으로 전달합니다.
- <b>동작</b><br>
  (1) 내부 버퍼에 누적 후 `\n` 기준으로 라인을 분리합니다.  
  (2) 각 라인을 UTF-8로 디코딩한 뒤 `json.loads()`로 파싱합니다.  
  (3) JSON 파싱 실패 시 에러 로그를 남기고 해당 라인을 스킵합니다.

이 모듈은 “수신(raw bytes)”과 “메시지(dict)” 사이의 경계 처리를 표준화합니다.

<details><summary>Click to check the python code</summary>

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

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/dispatcher.py</h4>

파싱된 메시지(dict)를 <b>type/error 기준으로 분기</b>하여, 등록된 콜백을 호출하는 디스패처입니다.

- <b>역할</b>  
  (1) 메시지 소비 로직(핸들러)을 네트워크/파서로부터 분리합니다.  
  (2) 예제 스크립트(handshake/monitor/control)는 dispatcher에 핸들러만 등록하면 됩니다.

- <b>메시지 분기 규칙(현재 구현 기준)</b>  
  (1) `msg`에 `"error"` 키가 있으면 `on_error(msg)` 호출(등록되어 있지 않으면 print)  
  (2) 그 외에는 `msg.get("type")` 값으로 `on_type[type]` 콜백 호출  
  (3) 매칭되는 콜백이 없으면 기본적으로 이벤트 내용을 출력합니다.

- <b>확장 포인트</b>  
  프로젝트에 따라 `ack/event`를 명시적으로 분리하고 싶다면,  
  `dispatch()` 내부에서 키(예: `ack`, `event`, `type`) 규칙을 확장하면 됩니다.

<details><summary>Click to check the python code</summary>

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

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/motion.py</h4>

`motion.py`는 CONTROL 예제에서 사용할 **joint trajectory 생성/재사용** 기능을 제공합니다.  
핵심 목적은 “CONTROL 전송 로직(control.md)”에서 **trajectory 생성 로직을 분리**하여 문서를 짧게 유지하는 것입니다.

- CONTROL 전송은 “통신/타이밍/스키마”가 복잡해지기 쉬운데,
  trajectory 생성까지 섞이면 예제가 너무 길어집니다.
- 따라서 trajectory는 `motion.py`에서 생성하고,
  control 예제는 “생성된 points를 일정 간격으로 보내는 것”에 집중합니다.

역할1. **단위 변환**
   - `rad_to_deg(rad_list) -> deg_list`
   - HTTP에서 읽은 joint state가 rad인 경우가 많아, CONTROL(point)은 deg로 맞추기 위한 유틸입니다.

역할2. **Trajectory 생성 (sin wave)**
   - `generate_sine_trajectory(base_deg, cycle_sec, amplitude_deg, dt_sec, total_sec, active_joint_count)`
   - `base_deg`를 기준으로 앞쪽 N개 관절만 sin 변위를 적용해 흔들림을 만듭니다.
   - 반환값은 `List[List[float]]` 형태의 **deg 포인트 배열**입니다.  
     &rightarrow; `points_deg[k][i]` = k번째 시점의 i번째 관절 각도(deg)

역할3. **Trajectory 저장/로드**
   - `save_trajectory(points_deg, dt_sec, base_dir="data") -> saved_path`
   - `load_trajectory(path) -> (dt_sec, points_deg)`
   - 저장 포맷(JSON):  
     &rightarrow; `dt_sec`: 포인트 간 시간 간격(sec)  
     &rightarrow; `points_deg`: 포인트 배열(List[List[float]])

사용 위치
- `control.md` 시나리오에서
  - base pose 읽기(rad) → `rad_to_deg()` 변환
  - `generate_sine_trajectory()`로 포인트 생성
  - 필요하면 `save_trajectory()`로 저장한 뒤 재사용(`load_trajectory()`)

주의 사항
- CONTROL `joint_traject_insert_point`의 `point`는 **deg**를 가정합니다(예제 기준).
- `dt_sec`는 전송 타이밍 및 `interval/time_from_start` 설정과 직결되므로,
  저장/로드 시 반드시 함께 유지해야 합니다.

<details><summary>Click to check the python code</summary>

```python
# utils/motion.py
import json
import math
import os
import time
from typing import List, Tuple
from typing import Optional

def rad_to_deg(rad_list: List[float]) -> List[float]:
    return [r * 180.0 / math.pi for r in rad_list]


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

Open Stream 프로토콜 메시지의 JSON 구조를 <b>일관되게 생성</b>하는 얇은 래퍼입니다.

- <b>역할</b>  
  (1) 예제 스크립트가 “JSON 스키마”를 반복 작성하지 않도록 합니다.  
  (2) `cmd`(HANDSHAKE/MONITOR/CONTROL/STOP) 별 payload 구조를 표준화합니다.

- <b>중요</b>  
  (1) `api.py`는 네트워크 전송을 직접 하지 않고, `net.send_line()`을 통해 NDJSON 라인으로 전송합니다.  
  (2) CONTROL은 프로토콜의 1급 명령이며, `joint_traject_*`는 CONTROL 하위 기능(trajectory 전송)을 위한 helper입니다.


프로토콜 명령 구조

| cmd       | 설명                   |
| --------- | -------------------- |
| HANDSHAKE | 세션 초기화 및 버전 협상       |
| MONITOR   | 상태/HTTP API 주기 조회    |
| CONTROL   | 로봇 제어 (trajectory 등) |
| STOP      | 세션 또는 스트림 중단         |

제공 메서드

| API 함수 | 대응 cmd | 설명 |
|--------|----------|------|
| `handshake(major)` | HANDSHAKE | Open Stream 세션 초기화 |
| `monitor(url, period_ms, args=None, monitor_id=1)` | MONITOR | 지정 URL을 주기적으로 조회 |
| `monitor_stop()` | MONITOR | MONITOR 중단 |
| `joint_traject_init()` | CONTROL | joint trajectory 제어 초기화 |
| `joint_traject_insert_point(body)` | CONTROL | trajectory 포인트 1개 전송 |
| `stop(target)` | STOP | 세션 또는 control/monitor 중단 |

<details><summary>Click to check the python code</summary>

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
    # HANDSHAKE
    # -------------------------

    def handshake(self, major: int = 1) -> None:
        self._send({
            "cmd": "HANDSHAKE",
            "payload": {
                "major": major
            },
        })

    # -------------------------
    # MONITOR
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
        """
        Start MONITOR stream.

        - url        : target API path
        - period_ms  : polling period in milliseconds
        - args       : optional query/body args
        - monitor_id : MONITOR stream id
        - method     : HTTP method (default: GET)
        """
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
    # STOP
    # -------------------------

    def stop(self, target: str = "session") -> None:
        self._send({
            "cmd": "STOP",
            "payload": {
                "target": target
            },
        })

    # -------------------------
    # CONTROL (joint trajectory)
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
<h4 style="font-size:16px; font-weight:bold;">요약</h4>

* 위 `utils` 코드는 <b>이후 모든 예제에서 그대로 재사용</b>됩니다.
* 별도 수정 없이 <b>복사–붙여넣기만 해도 정상 동작</b>합니다.
* 다음 문서부터는 이 유틸리티를 기반으로
  <b>HANDSHAKE → MONITOR → CONTROL → STOP</b> 시나리오를 단계적으로 설명합니다.
