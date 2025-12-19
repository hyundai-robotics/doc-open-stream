## 5.4 CONTROL 예제

이 예제는 Open Stream 세션에서 **HANDSHAKE를 선행 수행한 뒤 CONTROL 스트리밍**을 시작하고,
주기적으로 수신되는 데이터를 처리하는 기본 흐름을 제공합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">수행 시나리오</h4>

1. TCP 연결 생성
2. NDJSON 수신 루프 시작 (parser + dispatcher 연결)
3. HANDSHAKE 전송 (major)
4. `handshake_ack` 수신 확인 (성공 시에만 다음 단계 진행)
5. CONTROL 전송 (method/url/period_ms/args)
6. `control_ack` 수신 확인 (또는 서버가 정의한 ACK 타입)
7. `control_data`(스트림 데이터) 수신 처리
8. 예제 종료 (연결 종료)

※ 실제 운용에서는 스트리밍 종료 시 `STOP target=control`을 전송하는 것이 권장됩니다. (STOP 예제에서 다룹니다)

<br>
<h4 style="font-size:16px; font-weight:bold;">준비물</h4>

* `utils/` 디렉토리 (net.py / parser.py / dispatcher.py / api.py)
* 서버 주소, 포트(`49000`)
* CONTROL 대상 REST URL, period_ms, args
* HANDSHAKE 버전(`major`)

<br>
<h4 style="font-size:16px; font-weight:bold;">예제 코드</h4>

이 예제를 실행하려면 아래 파일들이 프로젝트에 존재해야 합니다.

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
│   └── control.py        # (이 문서에서 제공하는 시나리오 코드)
│
└── main.py               # 시나리오 런처(엔트리 포인트)
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

<div style="max-width:fit-content;">

```python
# scenarios/control.py
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

    # --- HANDSHAKE ACK 대기용 ---
    handshake_ok = threading.Event()

    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # CONTROL ACK / DATA (서버 구현에 맞게 type 명칭은 조정 가능)
    dispatcher.on_type["control_ack"] = lambda m: print(
        f"[ack] control_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )

    # CONTROL 스트리밍 데이터
    # payload 스키마는 서버 구현에 따라 다를 수 있어, 예제에서는 raw 출력 형태로 둡니다.
    dispatcher.on_type["control_data"] = lambda m: print(
        f"[data] {m}"
    )

    # 에러 공통 처리
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 연결 및 수신 루프 시작
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) HANDSHAKE 선행
    api.handshake(major=major)

    # 2) handshake_ack 수신 대기 (환경에 맞게 timeout 조정)
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack timeout; CONTROL will not be sent.")
        net.close()
        return

    # 3) CONTROL 송신
    # args는 REST 쿼리 파라미터 등에 대응하는 구조로 사용됩니다.
    api.control(url=url, period_ms=period_ms, args={})

    # 스트림 수신을 위해 잠시 대기 후 종료
    # (정상 종료는 STOP 예제에서 STOP target=control 권장)
    time.sleep(2.0)
    net.close()
```

</div>

<div style="max-width:fit-content;">
  &rightarrow; HANDSHAKE 성공을 확인한 뒤 CONTROL 요청을 전송하고, ACK 및 스트리밍 데이터를 수신해 출력하는 실행 가능한 시나리오 코드입니다.
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control


def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # stream options
    p.add_argument("--url", default="/api/health")

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(args.host, args.port, major=args.major, url=args.url, period_ms=args.period_ms)

    elif args.scenario == "control":
        sc_control.run(args.host, args.port, major=args.major, url=args.url, period_ms=args.period_ms)


if __name__ == "__main__":
    main()
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

프로젝트 루트에서 아래 명령을 실행합니다.

<div style="max-width:fit-content;">

```bash
$python3 main.py control --host 192.168.1.150 --port 49000 --major 1 --url /api/control --period-ms 10
```

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1
[tx] {"cmd":"CONTROL","payload":{"method":"GET","url":"/api/control","period_ms":10,"args":{}}}
[ack] control_ack ok=True url=/api/control period_ms=10
[data] {...}
[data] {...}
[net] connection closed
```

</div>

* 참고 : 에러가 발생하면 `{ "error": "...", "message": "...", "hint": "..." }` 형태로 수신됩니다.
* 참고 : `control_data`의 payload 스키마는 서버 구현에 따라 달라질 수 있으므로, 실제 메시지 구조에 맞게 출력/파싱 로직을 조정하십시오.

---

원하시면, 만료된 파일을 다시 업로드해 주시는 즉시 `handshake.md`의 표현/섹션 제목/들여쓰기/문장부호까지 포함해 **완전 동일 톤으로 리라이트**해 드릴 수 있습니다. 또한 `stop.md`도 같은 방식(선행 handshake 요구 여부 포함)으로 바로 작성 가능합니다.
