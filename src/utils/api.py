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
            "id": 1,
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
