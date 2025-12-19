# 5. 예제

{% hint style="info" %}

이 섹션은 Open Stream을 처음 사용하는 사용자가 <b>클라이언트 구조를 어떻게 설계해야 하는지</b>를 단계적으로 이해할 수 있도록 구성된 예제입니다. 각 예제는 "동작하는 코드"보다  <b>구조와 흐름을 이해하는 것</b>에 목적을 둡니다.

{% endhint %}

<h4 style="font-size:16px; font-weight:bold;">메뉴얼 예제 섹션 구조</h4>

<div style="max-width:fit-content;">

```text
5. 예제
├── 5.1 utils       # 공통 유틸리티 (송수신, 파싱, 이벤트 분기)
├── 5.2 handshake   # HANDSHAKE 단독 예제
├── 5.3 monitor     # MONITOR 스트리밍 예제
├── 5.4 control     # CONTROL 단발 요청 예제
└── 5.5 stop        # STOP 및 정상 종료 예제
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">클라이언트가 생성할 디렉토리 구조</h4>

아래는 Open Stream을 사용하는 클라이언트 애플리케이션에서  
권장하는 최소 디렉토리 구조 예시입니다.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py            # TCP 소켓 연결 및 송수신
│   ├── parser.py         # NDJSON 스트림 파싱
│   ├── dispatcher.py     # type / error 기반 이벤트 분기
│   └── api.py            # HANDSHAKE / MONITOR / CONTROL / STOP 래퍼
│
├── scenarios/
│   ├── handshake.py      # HANDSHAKE 단독 실행 시나리오
│   ├── monitor.py        # MONITOR 스트리밍 시나리오
│   ├── control.py        # CONTROL 단발 요청 시나리오
│   └── stop.py           # STOP 및 정상 종료 시나리오
│
└── main.py               # 클라이언트 엔트리 포인트
```
</div>



<br>
<h4 style="font-size:16px; font-weight:bold;">실행 환경</h4>

<div style="max-width:fit-content;">

| 항목 | 내용 |
|------|------|
| Language | Python 3.8.0 |
| OS | Linux / macOS / Windows (TCP 소켓 사용 가능 환경) |
| Libraries | 표준 라이브러리만 사용 |

</div>

- 본 예제는 Open Stream 프로토콜의 이해를 돕기 위해  
의도적으로 외부 의존성을 최소화했습니다.
