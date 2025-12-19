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

    # --- 동기화용 이벤트 (ACK 대기) ---
    handshake_ok = threading.Event()

    # 이벤트 핸들러 등록
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # MONITOR ACK / DATA (서버 구현에 맞게 type명은 조정 가능)
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 연결 및 수신 루프 시작
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) HANDSHAKE 선행
    api.handshake(major=major)

    # 2) handshake_ack 수신 대기 (타임아웃은 환경에 맞게 조정)
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack timeout; MONITOR will not be sent.")
        net.close()
        return

    # 3) MONITOR 송신
    api.monitor(url=url, period_ms=period_ms, args={})

    # 스트림 수신을 위해 잠시 대기 후 종료
    # (정상 종료 시에는 STOP 예제에서처럼 STOP target=monitor 권장)
    time.sleep(2.0)
    net.close()
