## 5.5 STOP 예제 (Session / Stream 종료)

{% hint style="info" %}

이 문서에서는 Open Stream의 **STOP** 명령을 사용하여  
현재 실행 중인 **세션(Session)** 또는 **CONTROL / MONITOR 스트림**을
정상적으로 종료하는 방법을 설명합니다.

- STOP은 안전 종료를 위한 **필수 명령**입니다.
- CONTROL trajectory 전송 중이거나 MONITOR 스트림이 활성화된 상태에서
  즉시 중단해야 할 때 사용합니다.
- 아래 코드는 <b>실제 동작하는 코드</b>이며 그대로 복사하여 사용할 수 있습니다.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP 명령 개요</h4>

STOP은 Open Stream 세션 또는 특정 스트림을 종료하는 제어 명령입니다.

- 로봇을 <b>즉시 정지</b>시키거나
- CONTROL / MONITOR 스트림을 <b>정상적으로 해제</b>할 때 사용합니다.

STOP 명령을 보내면 서버는 내부 상태를 정리하고,
필요 시 관련 리소스(trajectory buffer, monitor task 등)를 해제합니다.

---

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP 대상(target)</h4>

STOP 명령은 `target` 필드로 종료 대상을 지정합니다.

| target 값   | 설명 |
|------------|------|
| `session`  | Open Stream 세션 전체 종료 (권장 기본값) |
| `control`  | CONTROL 스트림만 중단 |
| `monitor`  | MONITOR 스트림만 중단 |

※ 구현/버전에 따라 `control`, `monitor`는 선택적으로 지원될 수 있으며,  
가장 안전한 방법은 `session` 종료입니다.

---

<br>
<h4 style="font-size:16px; font-weight:bold;">시나리오 흐름</h4>

(1) TCP 연결 및 수신 루프 시작  
(2) HANDSHAKE 수행  
(3) STOP 명령 전송  
(4) 서버 응답 확인  
(5) 소켓 종료

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
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   ├── monitor.py
│   ├── control.py
│   └── stop.py
│
└── main.py
````

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

아래 코드는 지정한 target에 대해 STOP 명령을 전송하는 예제입니다.

<details><summary>Click to check the python code</summary>

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

    # 1) connect + recv loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) handshake
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] handshake failed; aborting stop.")
        net.close()
        return

    # 3) STOP
    print(f"[INFO] sending STOP target={target}")
    api.stop(target=target)

    # 짧은 대기 (서버 처리 시간)
    time.sleep(0.5)

    # 4) close socket
    net.close()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 연결 예시</h4>

기존 `main.py` 시나리오 구조에 맞춰 STOP을 호출하는 방식입니다.

<div style="max-width:fit-content;">

```python
# main.py (일부)
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
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

<div style="max-width:fit-content;">

```bash
# 세션 전체 종료 (권장)
python main.py stop --host 192.168.1.150 --port 49000 --target session

# CONTROL만 중단
python main.py stop --host 192.168.1.150 --port 49000 --target control

# MONITOR만 중단
python main.py stop --host 192.168.1.150 --port 49000 --target monitor
```

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

<div style="max-width:fit-content;">

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] sending STOP target=session
[tx] {"cmd":"STOP","payload":{"target":"session"}}
[net] connection closed
```

</div>

---

## 요약

* STOP은 로봇 제어/모니터링을 **안전하게 종료**하기 위한 명령입니다.
* CONTROL trajectory 전송 중에는 반드시 STOP으로 종료하는 것을 권장합니다.
* 가장 안전한 기본 사용법은 `target=session` 입니다.