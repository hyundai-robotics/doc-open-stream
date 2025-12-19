```python
# scenarios/control.py
"""
CONTROL 시나리오 (복사-붙여넣기용 단일 파일)

구성(문서 TOC 흐름에 맞춤)
- 1. 개요
- 2. Base Pose 획득 (HTTP GET /project/robot/joints/joint_states)
- 3. Trajectory 생성(사인 스윙) + 파일 저장/로드
- 4. Trajectory 전송 (Open Stream CONTROL: joint_traject_init + joint_traject_insert_point)
- 5. 실행 흐름(run)
- 6. 참고(중단/정지)

전제:
- utils/ 디렉토리(5.1 공통 유틸리티) 존재:
  - utils/net.py, utils/parser.py, utils/dispatcher.py, utils/api.py
"""

from __future__ import annotations

import json
import math
import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI


# =============================================================================
# 2. Base Pose 획득
# =============================================================================

def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    로봇의 /project/robot/joints/joint_states 를 HTTP GET으로 조회해
    joint positions(rad) 리스트를 반환한다.

    반환 형식은 서버 구현에 따라 다음을 모두 허용하도록 방어적으로 파싱한다.
    - [j0, j1, ...]
    - {"position":[...]} (ROS JointState 유사)
    - {"j1":..., "j2":..., ...}
    """
    base_url = f"http://{host}:{http_port}"
    url = f"{base_url}/project/robot/joints/joint_states"

    resp = requests.get(url, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()

    q: List[float] = []

    if isinstance(data, list):
        for v in data:
            if isinstance(v, (int, float)):
                q.append(float(v))

    elif isinstance(data, dict):
        if "position" in data and isinstance(data["position"], list):
            for v in data["position"]:
                if isinstance(v, (int, float)):
                    q.append(float(v))
        else:
            # j1, j2, ... 형태를 가정
            # 키가 섞여 있어도 정렬 가능한 것만 처리
            items: List[Tuple[int, float]] = []
            for k, v in data.items():
                if not isinstance(v, (int, float)):
                    continue
                if isinstance(k, str) and k.startswith("j"):
                    try:
                        idx = int(k[1:])  # j1 -> 1
                        items.append((idx, float(v)))
                    except ValueError:
                        continue
            for _, v in sorted(items, key=lambda x: x[0]):
                q.append(v)

    if not q:
        raise RuntimeError(f"Cannot extract joints from joint_states response: {data!r}")

    return q


def rad_list_to_deg(rad_list: List[float]) -> List[float]:
    return [float(r) * 180.0 / math.pi for r in rad_list]


# =============================================================================
# 3. Trajectory 생성/저장/로드
# =============================================================================

def _make_trajectory_filename(base_dir: str = "data") -> str:
    os.makedirs(base_dir, exist_ok=True)
    stamp = time.strftime("%m%d%H%M%S", time.localtime())
    return os.path.join(base_dir, f"traject_{stamp}.json")


def generate_multi_swing_point(
    base_deg: List[float],
    t_local: float,
    *,
    cycle_sec: float = 1.0,
    max_ampl_deg: float = 5.0,
    phase_mode: str = "sync",   # "sync" or "offset"
    active_joint_count: Optional[int] = 6,
) -> List[float]:
    """
    기준 자세(base_deg)에서 ±max_ampl_deg 진폭으로 sin 스윙을 생성한다.
    active_joint_count: 앞에서 N축까지만 스윙. None이면 전체 축.
    """
    n = len(base_deg)
    if n == 0:
        return []

    if active_joint_count is None or active_joint_count > n:
        active_joint_count = n

    omega = 2.0 * math.pi / cycle_sec
    out: List[float] = []

    for i, base in enumerate(base_deg):
        if i < active_joint_count:
            phase = omega * t_local + (math.radians(30.0 * i) if phase_mode == "offset" else 0.0)
            offset = max_ampl_deg * math.sin(phase)
            out.append(float(base + offset))
        else:
            out.append(float(base))

    return out


def build_swing_trajectory(
    base_deg_list: List[float],
    *,
    cycle_sec: float = 1.0,
    max_ampl_deg: float = 5.0,
    sample_interval_sec: float = 0.02,
    total_duration_sec: float = 1.0,
    phase_mode: str = "sync",
    active_joint_count: Optional[int] = 6,
) -> List[List[float]]:
    """
    base_deg_list를 기준으로 사인 스윙 trajectory(points_deg)를 생성한다.
    루프 경계에서 끊김이 덜하도록 total_duration_sec을 cycle_sec의 정수배로 맞춘다.
    """
    if total_duration_sec <= 0:
        total_duration_sec = cycle_sec

    n_cycle = max(1, int(total_duration_sec / cycle_sec))
    total_duration_sec = n_cycle * cycle_sec

    n_steps = int(total_duration_sec / sample_interval_sec) + 1

    traj: List[List[float]] = []
    for k in range(n_steps):
        t_local = k * sample_interval_sec
        traj.append(
            generate_multi_swing_point(
                base_deg=base_deg_list,
                t_local=t_local,
                cycle_sec=cycle_sec,
                max_ampl_deg=max_ampl_deg,
                phase_mode=phase_mode,
                active_joint_count=active_joint_count,
            )
        )
    return traj


def save_trajectory_to_file(
    traj_points_deg: List[List[float]],
    dt_sec: float,
    *,
    base_dir: str = "data",
) -> str:
    path = _make_trajectory_filename(base_dir)
    payload = {
        "meta": {
            "dt_sec": float(dt_sec),
            "total_points": int(len(traj_points_deg)),
            "total_time_sec": float(round(len(traj_points_deg) * dt_sec, 6)),
            "saved_at_ns": int(time.time_ns()),
        },
        "points_deg": traj_points_deg,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return os.path.abspath(path)


def load_trajectory_from_file(path: str) -> Tuple[float, List[List[float]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "meta" in data and "dt_sec" in data["meta"]:
        dt = float(data["meta"]["dt_sec"])
        points = data["points_deg"]
    else:
        # legacy fallback
        dt = float(data["dt_sec"])
        points = data["points_deg"]

    return dt, points


def prepare_and_save_swing_trajectory(
    base_pose_deg: List[float],
    *,
    cycle_sec: float = 1.0,
    max_ampl_deg: float = 5.0,
    sample_interval_sec: float = 0.02,
    total_duration_sec: Optional[float] = None,
    phase_mode: str = "sync",
    active_joint_count: Optional[int] = 6,
    base_dir: str = "data",
) -> Tuple[List[List[float]], float, str]:
    """
    고수준 헬퍼:
    - base_pose_deg 기준 swing trajectory 생성
    - 파일 저장
    - (points_deg, dt_sec, saved_path) 반환
    """
    if total_duration_sec is None:
        total_duration_sec = cycle_sec

    points = build_swing_trajectory(
        base_deg_list=base_pose_deg,
        cycle_sec=cycle_sec,
        max_ampl_deg=max_ampl_deg,
        sample_interval_sec=sample_interval_sec,
        total_duration_sec=total_duration_sec,
        phase_mode=phase_mode,
        active_joint_count=active_joint_count,
    )
    saved = save_trajectory_to_file(points, sample_interval_sec, base_dir=base_dir)
    return points, sample_interval_sec, saved


# =============================================================================
# 4. Trajectory 전송 (CONTROL: init + insert_point)
# =============================================================================

JOINT_TRAJECT_INIT_URL = "/project/robot/trajectory/joint_traject_init"
JOINT_TRAJECT_INSERT_URL = "/project/robot/trajectory/joint_traject_insert_point"


def make_control_init_body() -> Dict[str, Any]:
    """
    init body가 서버에서 필요하면 여기서 확장.
    현재는 빈 dict를 기본으로 둔다.
    """
    return {}


def make_insert_point_body(
    point_deg: List[float],
    *,
    interval: float,
    look_ahead_time: float,
    time_from_start: float,
) -> Dict[str, Any]:
    """
    서버가 요구하는 필드들을 고정적으로 구성한다.
    - interval: 포인트 간 간격(sec)
    - time_from_start: 시작 기준 시간(sec) (서버가 요구하는 경우가 많음)
    - look_ahead_time: 제어 선행 시간(sec)
    - point: joint 각도(deg) 리스트
    """
    return {
        "interval": float(interval),
        "time_from_start": float(time_from_start),
        "look_ahead_time": float(look_ahead_time),
        "point": [float(x) for x in point_deg],
    }


def send_control_init(api: OpenStreamAPI) -> None:
    api.control(method="POST", url=JOINT_TRAJECT_INIT_URL, args={}, body=make_control_init_body())


def send_control_insert_point(
    api: OpenStreamAPI,
    point_deg: List[float],
    *,
    interval: float,
    look_ahead_time: float,
    time_from_start: float,
) -> None:
    body = make_insert_point_body(
        point_deg,
        interval=interval,
        look_ahead_time=look_ahead_time,
        time_from_start=time_from_start,
    )
    api.control(method="POST", url=JOINT_TRAJECT_INSERT_URL, args={}, body=body)


# =============================================================================
# 4.2 고주기 전송 최적화: 큐 + 송신 스레드 + 정밀 스케줄링
# =============================================================================

class FastSender(threading.Thread):
    """
    OpenStreamAPI.control을 반복 호출하면 json.dumps + print + 함수 호출 비용이 누적될 수 있어,
    고주기(예: 2ms~10ms)에서는 '라인 생성 후 소켓 sendall'만 수행하는 전용 sender를 둔다.
    """

    def __init__(self, net: NetClient, q: "queue.Queue[str]", shutdown_evt: threading.Event):
        super().__init__(name="FastSender", daemon=True)
        self.net = net
        self.q = q
        self.shutdown_evt = shutdown_evt
        self._lock = threading.Lock()

    def run(self) -> None:
        if not self.net.sock:
            raise RuntimeError("FastSender: net.sock is None (call net.connect first)")
        sock = self.net.sock

        while not self.shutdown_evt.is_set():
            try:
                line = self.q.get(timeout=0.2)
            except queue.Empty:
                continue

            if line is None:
                break

            data = (line + "\n").encode("utf-8")
            with self._lock:
                try:
                    sock.sendall(data)
                except OSError:
                    break


@dataclass
class TrajectoryConfig:
    dt_sec: float = 0.02
    look_ahead_time: float = 0.1
    loop_traj: bool = False


class TrajectoryStreamer(threading.Thread):
    """
    traj_points_deg를 dt_sec 간격으로 CONTROL(insert_point)로 전송한다.
    - '이상적 시간축' 기반으로 스케줄링하여, 지연 시 burst를 줄인다.
    """

    def __init__(
        self,
        send_line_q: "queue.Queue[str]",
        shutdown_evt: threading.Event,
        traj_points_deg: List[List[float]],
        cfg: TrajectoryConfig,
    ):
        super().__init__(name="TrajectoryStreamer", daemon=True)
        self.send_line_q = send_line_q
        self.shutdown_evt = shutdown_evt
        self.points = list(traj_points_deg)
        self.cfg = cfg
        self._stop_req = threading.Event()

    def request_stop(self) -> None:
        self._stop_req.set()

    def _enqueue_control_line(self, body: Dict[str, Any]) -> None:
        msg = {
            "cmd": "CONTROL",
            "payload": {
                "method": "POST",
                "url": JOINT_TRAJECT_INSERT_URL,
                "args": {},
                "body": body,
            },
        }
        line = json.dumps(msg, separators=(",", ":"))
        self.send_line_q.put(line)

    def run(self) -> None:
        if not self.points:
            return

        t0 = time.perf_counter()

        while not self.shutdown_evt.is_set() and not self._stop_req.is_set():
            now = time.perf_counter()
            elapsed = now - t0

            k_target = int(elapsed / self.cfg.dt_sec)

            if self.cfg.loop_traj:
                idx = k_target % len(self.points)
            else:
                if k_target >= len(self.points):
                    break
                idx = k_target

            point_deg = self.points[idx]

            body = make_insert_point_body(
                point_deg,
                interval=self.cfg.dt_sec,
                look_ahead_time=self.cfg.look_ahead_time,
                time_from_start=k_target * self.cfg.dt_sec,
            )
            self._enqueue_control_line(body)

            next_target = t0 + (k_target + 1) * self.cfg.dt_sec
            remain = next_target - time.perf_counter()
            if remain > 0:
                time.sleep(remain)


def enqueue_control_init(send_line_q: "queue.Queue[str]") -> None:
    msg = {
        "cmd": "CONTROL",
        "payload": {
            "method": "POST",
            "url": JOINT_TRAJECT_INIT_URL,
            "args": {},
            "body": make_control_init_body(),
        },
    }
    send_line_q.put(json.dumps(msg, separators=(",", ":")))


# =============================================================================
# 5. 실행 흐름 (run)
# =============================================================================

def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    # base pose를 가져올 HTTP host는 보통 컨트롤러와 동일 host를 쓰므로 기본 host 재사용
    http_port: int = 8888,
    # trajectory 생성 파라미터
    cycle_sec: float = 1.0,
    max_ampl_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_duration_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    phase_mode: str = "sync",
    # 전송 파라미터
    look_ahead_time: float = 0.1,
    loop_traj: bool = False,
    # 파일로 저장된 trajectory를 재사용하고 싶으면 지정
    load_traj_path: Optional[str] = None,
) -> None:
    """
    end-to-end:
    1) TCP 연결 + 수신 루프
    2) HANDSHAKE
    3) base pose HTTP GET
    4) trajectory 생성(또는 파일 로드)
    5) joint_traject_init
    6) dt 기준 insert_point 스트리밍
    """

    # --- Open Stream plumbing ---
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    shutdown_evt = threading.Event()

    handshake_ok = threading.Event()

    def _on_handshake_ack(m: dict) -> None:
        if bool(m.get("ok")):
            handshake_ok.set()
        print(f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}")

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 연결 및 수신 루프 시작
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) HANDSHAKE
    api.handshake(major=major)
    if not handshake_ok.wait(timeout=2.0):
        print("[ERR] handshake_ack timeout; aborting.")
        shutdown_evt.set()
        net.close()
        return

    # 2) base pose (HTTP GET)
    q_rad = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    base_deg = rad_list_to_deg(q_rad)
    print(f"[INFO] base pose joints={len(base_deg)}")

    # 3) trajectory 준비
    if load_traj_path:
        dt_loaded, points_deg = load_trajectory_from_file(load_traj_path)
        dt_sec_use = float(dt_loaded)
        print(f"[INFO] loaded trajectory: {load_traj_path} (points={len(points_deg)}, dt={dt_sec_use})")
    else:
        points_deg, dt_sec_use, saved = prepare_and_save_swing_trajectory(
            base_pose_deg=base_deg,
            cycle_sec=cycle_sec,
            max_ampl_deg=max_ampl_deg,
            sample_interval_sec=dt_sec,
            total_duration_sec=total_duration_sec,
            phase_mode=phase_mode,
            active_joint_count=active_joint_count,
            base_dir="data",
        )
        print(f"[INFO] generated trajectory: points={len(points_deg)}, dt={dt_sec_use}, saved={saved}")

    # 4) 고주기 전송: init + insert_point 는 FastSender 경로 사용
    send_line_q: "queue.Queue[str]" = queue.Queue(maxsize=5000)

    sender = FastSender(net, send_line_q, shutdown_evt)
    sender.start()

    # init enqueue
    enqueue_control_init(send_line_q)

    # 5) streaming start
    cfg = TrajectoryConfig(dt_sec=dt_sec_use, look_ahead_time=look_ahead_time, loop_traj=loop_traj)
    streamer = TrajectoryStreamer(send_line_q, shutdown_evt, points_deg, cfg)
    streamer.start()

    try:
        # loop_traj=False면 streamer가 끝나면 자연 종료.
        while streamer.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("[INFO] KeyboardInterrupt: stopping trajectory streamer...")
        streamer.request_stop()

    # shutdown
    shutdown_evt.set()
    try:
        send_line_q.put_nowait(None)  # sender exit
    except Exception:
        pass
    net.close()


# =============================================================================
# 6. CLI Entry
# =============================================================================

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Open Stream CONTROL trajectory runner (copy-paste ready)")
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)
    p.add_argument("--major", type=int, default=1)

    p.add_argument("--http-port", type=int, default=8888)

    # trajectory gen
    p.add_argument("--cycle-sec", type=float, default=1.0)
    p.add_argument("--max-ampl-deg", type=float, default=5.0)
    p.add_argument("--dt-sec", type=float, default=0.02)
    p.add_argument("--total-duration-sec", type=float, default=1.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--phase-mode", choices=["sync", "offset"], default="sync")

    # send
    p.add_argument("--look-ahead-time", type=float, default=0.1)
    p.add_argument("--loop-traj", action="store_true")

    # reuse file
    p.add_argument("--load-traj", default=None, help="load trajectory JSON path instead of generating")

    args = p.parse_args()

    run(
        args.host,
        args.port,
        major=args.major,
        http_port=args.http_port,
        cycle_sec=args.cycle_sec,
        max_ampl_deg=args.max_ampl_deg,
        dt_sec=args.dt_sec,
        total_duration_sec=args.total_duration_sec,
        active_joint_count=args.active_joint_count,
        phase_mode=args.phase_mode,
        look_ahead_time=args.look_ahead_time,
        loop_traj=args.loop_traj,
        load_traj_path=args.load_traj,
    )
```

---

### 사용 예시

```bash
# 생성한 trajectory로 1회 실행 (저장도 됨)
python3 main.py control --host 192.168.1.150 --port 49000

# dt를 10ms로, 진폭 10deg로, 3초 길이 생성 후 전송
python3 scenarios/control.py --host 192.168.1.150 --port 49000 --dt-sec 0.01 --max-ampl-deg 10 --total-duration-sec 3.0

# 저장된 trajectory 재사용
python3 scenarios/control.py --host 192.168.1.150 --port 49000 --load-traj data/traject_1219090300.json
```