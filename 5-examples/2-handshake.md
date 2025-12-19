## 5.2 HANDSHAKE 예제

이 예제는 Open Stream 세션을 시작하기 위한 가장 기본적인 흐름을 제공합니다.


<h4 style="font-size:16px; font-weight:bold;">수행 시나리오</h4>

1. TCP 연결 생성
2. NDJSON 수신 루프 시작 (parser + dispatcher 연결)
3. HANDSHAKE 전송
4. `handshake_ack` 수신 확인
5. 연결 종료

<br>
<h4 style="font-size:16px; font-weight:bold;">준비물</h4>

- `utils/` 디렉토리 (net.py / parser.py / dispatcher.py / api.py)
- 서버 주소, 포트(`49000`)


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
│   └── handshake.py      # (이 문서에서 제공하는 시나리오 코드)
│
└── main.py               # 시나리오 런처(엔트리 포인트)
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

    # 이벤트 핸들러 등록
    dispatcher.on_type["handshake_ack"] = lambda m: print(
        f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}"
    )
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 연결 및 수신 루프 시작
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # HANDSHAKE 송신
    api.handshake(major=major)

    # ACK 수신을 위해 잠시 대기 후 종료
    time.sleep(0.5)
    net.close()
```

</div>

<div style="max-width:fit-content;">
  &rightarrow; HANDSHAKE 요청을 전송하고 handshake_ack 수신을 확인하는 실행 가능한 시나리오 코드입니다.



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
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

프로젝트 루트에서 아래 명령을 실행합니다.


<div style="max-width:fit-content;">

```bash
$python3 main.py handshake --host 192.168.1.150 --port 49000 --major 1
````

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] connection closed
```
</div>

- 참고 : 에러가 발생하면 `{ "error": "...", "message": "...", "hint": "..." }` 형태로 수신됩니다.
