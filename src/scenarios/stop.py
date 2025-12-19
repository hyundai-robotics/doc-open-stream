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