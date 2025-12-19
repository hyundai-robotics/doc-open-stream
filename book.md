# ${cont_model} Open Stream

{% hint style="warning" %}

본 제품 메뉴얼에 제공된 정보는 <b>HD현대로보틱스(HD Hyundai Robotics)</b>의 자산입니다.

본 메뉴얼은 HD현대로보틱스의 사전 서면 동의 없이, 전체 또는 일부를 복제하거나 재배포할 수 없으며, 제3자에게 제공하거나 다른 목적으로 사용할 수 없습니다.

본 메뉴얼의 내용은 사전 예고 없이 변경될 수 있습니다.


**Copyright ⓒ 2025 by HD Hyundai Robotics**

{% endhint %}

{% hint style="warning" %}

본 매뉴얼에 명시되지 않은 ${cont_model} Open Stream 기능 또는 ${cont_model} Open API 매뉴얼에 명시되지 않은 API를 사용함으로써 발생하는 어떠한 손해나 문제에 대해서도 당사는 책임을 지지 않습니다.

{% endhint %}# 1. 개요

본 문서는 Open Stream을 사용하는 외부 클라이언트를 위한 사용 메뉴얼입니다.<br>
Open Stream의 목적, 기본 개념, 전체 동작 구조와 지원되는 사용 시나리오를 설명합니다.

<br>

이 문서를 통해 사용자는

- Open Stream이 어떤 문제를 해결하는지
- 어떤 방식으로 동작하는지
- 어떤 상황에서 사용하는 것이 적절한지

를 이해할 수 있습니다.

 📌 최신 변경 사항은 [Release Notes](../10-release-notes/README.md)를 참고하세요.## 1.1 Open Stream이란?

해당 기능은 ${cont_model} Open API를 짧은 주기로 반복 호출하여,  
클라이언트가 그 결과를 스트리밍 형태로 지속적으로 수신할 수 있도록 제공되는 인터페이스입니다.

<br>

${cont_model} 제어기 내부의 TCP 기반의 경량 서버를 통해  
외부 클라이언트가 서버와 데이터를 연속적으로 송수신할 수 있도록  
제공되는 스트리밍 인터페이스입니다.

<br>

Open Stream은 다음과 같은 특징을 가집니다.

- 하나의 TCP 연결을 장시간 유지합니다
- 요청과 응답은 NDJSON(Newline Delimited JSON) 형식을 사용합니다
- 주기적인 데이터 송신(`MONITOR`)과 즉시성 제어 명령(`CONTROL`)을 동시에 지원합니다
- HTTP 요청/응답을 반복적으로 생성하지 않습니다

<br>

Open Stream은 짧은 주기로 제어 명령과 상태 수신을 하나의 연결에서 처리해야 하는  
클라이언트 환경을 위해 설계되었습니다.

<br><br>

<b> 전체 동작 개요 </b>

Open Stream의 기본 동작 흐름은 다음과 같습니다.
<div style="display:flex; flex-wrap:wrap; align-items:flex-start;">

<!-- Left: Image -->
<div style="flex:1 1 420px; min-width:420px; max-width:420px;">
  <img
    src="../_assets/1-open_stream_concept.png"
    alt="Open Stream Flow"
    style="width:100%; height:auto; border-radius:6px;"
  />
</div>

<!-- Right: Ordered List -->
<div style="flex:1 1 280px; min-width:280px; max-width:fit-content;">
  <ol style="line-height:1.5; ">

  <li>클라이언트가 서버에 TCP로 접속하여 세션을 생성합니다.</li><br>

  <li>클라이언트는 연결 직후 <code>HANDSHAKE</code> 명령을 송신하여<br>
    서버와 프로토콜 버전 호환성을 확인합니다.</li><br>

  <li>서버는 <code>HANDSHAKE</code> 요청을 처리한 뒤, 프로토콜 버전이 일치하는 경우 <code>handshake_ack</code> 이벤트를 송신합니다.</li><br>

  <li>클라이언트는 <code>HANDSHAKE</code> 이후
    <code>MONITOR</code> 명령을 통해 주기적 데이터 스트리밍을 요청하거나,
    <code>CONTROL</code> 명령을 통해 단발성 요청을 수행할 수 있습니다.
    <small>(MONITOR가 활성화된 상태에서도 CONTROL 명령을 송신할 수 있습니다.)</small>
  </li><br>

  <li><code>MONITOR</code>가 활성화되면 서버는 클라이언트의 추가 요청과 무관하게
    주기적으로 <code>data</code> 이벤트를 비동기적으로 송신합니다.</li><br>
    
  <li><code>CONTROL</code> 명령은 성공 시 별도의 ACK를 송신하지 않으며,<br>
    실패한 경우에만 <code>error</code> 또는 <code>control_err</code>
    이벤트가 전달될 수 있습니다.</li><br>

  <li>작업이 완료되면 클라이언트는 <code>STOP</code> 명령을 송신하여
    활성 동작 또는 세션 종료 의도를 전달하고,
    서버의 <code>stop_ack</code> 이후 TCP 연결을 종료합니다.
  </li>

  </ol>
</div>

</div>

<br>


{% hint style="info" %}

*MONITOR 명령이란? 클라이언트가 지정한 하나의 ${cont_model} Open API 서비스 함수를 짧은 주기로 반복 호출하여,
그 결과를 스트리밍 형태로 지속적으로 수신합니다.

*CONTROL 명령이란? 클라이언트가 ${cont_model} Open API를 통해 단발성 제어 요청을 전달하기 위한 명령입니다. 클라이언트는 필요에 따라 짧은 주기로 반복 송신할 수 있습니다.

{% endhint %}

Open Stream은 하나의 TCP 연결 내에서 MONITOR와 CONTROL 명령을 함께 사용할 수 있습니다.

{% hint style="warning" %}

단, 하나의 연결에서는 하나의 MONITOR 세션, 하나의 CONTROL 세션만 활성화할 수 있습니다.

{% endhint %}## 1.2 사용 전 유의 사항

Open Stream은 실시간 제어 및 상태 수신을 효율적으로 처리하기 위한 인터페이스이지만,  
다음과 같은 제약 및 전제를 반드시 고려해야 합니다.

- Open Stream은 정주기 데이터 전달을 목표로 하지만 보장하지는 않습니다.
- 운영체제 스케줄링, 네트워크 상태 및 클라이언트 처리 부하에 따라 주기 지연(jitter) 이 발생할 수 있습니다.
- 하나의 TCP 연결에서는 하나의 MONITOR 세션만 활성화할 수 있습니다.
- 모든 명령은 정의된 프로토콜 순서를 따라야 하며,  
  순서 위반 시 서버는 명령을 거부하거나 연결을 종료할 수 있습니다.

<br><br>

<b> MONITOR 및 CONTROL 운용 시 참고 성능 (시험 결과) </b>

아래 결과는 동일한 시험 환경에서 MONITOR 단독 수행과  
CONTROL과 MONITOR를 동시에 수행한 경우의 주기 특성을 비교한 참고 자료입니다.


시험 환경 
- 서버 : ${cont_model} COM
- 클라이언트 : Windows 11 기반 Python 클라이언트
- 네트워크 : TCP 연결
- 송/수신 주기 : MONITOR 명령으로 설정 가능한 최대 주기로 설정

<br>

시험 결과 요약

1. MONITOR 단독 수행

    | **시험 조건**                                                              | **주기 특성 요약**                                                                                                    |
    | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
    | - MONITOR 주기: 2 ms (500 Hz)<br>- CONTROL 미사용<br>- 연속 실행: 10시간          | - <u><b>평균 수신 주기: 약 2.0 ms</b></u><br>- 수신 프레임 수: 약 1,800만<br>- 누락 프레임 비율: 약 0.001%                                           |

2. CONTROL + MONITOR 동시 수행

    | **시험 조건**                                                              | **주기 특성 요약**                                                                                                    |
    | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
    | - CONTROL 주기: 2 ms<br>- MONITOR 주기: 2 ms<br>- CONTROL / MONITOR 동시 활성화 | - CONTROL(SEND): <u><b>평균 주기 약 2.0 ms</b></u>, 최대 지연 약 30~40 ms<br>- MONITOR(RECV): <b><u>평균 주기 약 2.1~2.2 ms</b></u>, 최대 지연 수십 ms~100 ms 이상 |

<br><br>

<b> 해석 및 운용 시 유의 사항 </b>

- MONITOR 레시피를 단독으로 운용하는 경우, 장시간 연속 실행에서도 비교적 안정적인 주기 수신이 가능합니다.  

- CONTROL과 MONITOR를 동시에 운용할 경우, 시스템 설계에 따라 CONTROL 세션이 더 높은 우선순위로 처리됩니다.  

- 이로 인해 CONTROL 주기 안정성은 유지되지만,  
MONITOR 수신 주기는 평균 증가 및 간헐적인 지연이 발생할 수 있습니다.  

- CONTROL과 MONITOR를 동시에 사용하는 환경에서는  
MONITOR 데이터의 정주기성 저하 및 지연 발생을 전제로 시스템을 설계해야 합니다.  # Protocol

이 섹션에서는 Open Stream이 사용하는 전송 규약(Transport)과 메시지 프레이밍 규칙을 설명합니다.

- Open Stream은 **TCP 소켓** 기반의 단일 세션 통신을 사용합니다.
- 클라이언트/서버 간 메시지는 **NDJSON(Newline Delimited JSON)** 형태로 교환합니다.
- 각 메시지는 **JSON 1개를 1줄로 직렬화한 뒤, 줄 끝에 `\n`을 붙여 전송**합니다.

세부 NDJSON 규칙은 아래 문서를 참고하세요.

- [NDJSON 규칙](./1-ndjson.md)# NDJSON 규칙

Open Stream은 메시지 프레이밍을 위해 **NDJSON(Newline Delimited JSON)** 을 사용합니다.  
즉, “한 줄 = 하나의 JSON 메시지” 입니다.

<h4 style="font-size:15px; font-weight:bold;">1. 메시지 프레이밍</h4>

<div style = "max-width:fit-content">

- 클라이언트는 요청을 아래처럼 전송합니다.

    ```json
    {"cmd":"HANDSHAKE","payload":{"major":1}}\n
    {"cmd":"MONITOR","payload":{"period_ms":10,"method":"GET","url":"/project/robot"}}\n
    ```

- 서버 또한 응답/이벤트를 동일한 방식으로 전송합니다.

    ```json
    {"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
    {"type":"data","ts":1730000000000,"svc_dur_ms":0.42,"result":{"status":"ok"}}\n
    ```

</div>

<br>

<h4 style="font-size:15px; font-weight:bold;">2. 필수 규칙</h4>

1. 모든 메시지는 JSON 1개를 정확히 1줄로 직렬화해야 합니다.  
   &rightarrow; JSON 문자열 내부에 개행 문자가 포함되면 프레이밍이 깨집니다.
2. 각 메시지 끝에는 반드시 개행 문자 \n 가 포함되어야 합니다.  
3. 모든 메시지는 UTF-8 인코딩으로 전송되어야 합니다.

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 권장 사항</h4>

1. 메시지 크기 최소화를 위해 공백 없는 직렬화를 권장합니다.

    <div style="max-width:fit-content;">

    ```py
    # python example
    import json
    json.dumps(recipe_data, separators=(",", ":")) + "\n"
    ```

    </div>

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 클라이언트 구현 팁</h4>

<div style="max-width: fit-content;">

{% hint style="info" %}

TCP 스트림 특성상, 한 번의 recv() 호출이 정확히 한 줄을 반환한다는 보장은 없습니다.  
수신 데이터는 내부 버퍼에 누적한 뒤, \n 기준으로 라인을 분리하여 JSON 파싱을 수행하는 구조를  권장합니다.

{% endhint %}

python 예제 코드

```py
def recv_lines(sock):
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if line:
                yield line.decode("utf-8", errors="replace")

```

</div>

# Session & Streaming

<div style="fit-content;">

{% hint style="info" %}

이 문서는 Open Stream을 실제로 구현하고 운영하기 위해 반드시 이해해야 하는  
<b>세션 라이프사이클(Session Lifecycle)</b> 과 <b>스트리밍 동작 방식(Streaming Behavior)</b> 을 설명합니다.

{% endhint %}

</div>

<br>

<h4 style="font-size:16px; font-weight:bold;">1. 세션 라이프사이클</h4>

Open Stream은 <b>TCP 연결 1개를 하나의 세션(Session)</b> 으로 간주합니다.  
일반적인 세션 흐름은 다음과 같습니다.

1. 클라이언트가 서버와 TCP 연결을 생성합니다.
2. 클라이언트는 연결 직후 `HANDSHAKE` 명령을 전송합니다.
3. 클라이언트는 `MONITOR` 및/또는 `CONTROL` 명령을 요청합니다.  
    ※ `MONITOR`가 활성화된 경우, 서버는 주기적으로 `data` 이벤트를 스트리밍합니다.
4. 작업이 완료되면 클라이언트는 `STOP` 명령을 전송합니다.
5. 이후 TCP 연결을 종료합니다.

<br>

<h4 style="font-size:16px; font-weight:bold;">2. 사용 규칙</h4>

다음 규칙은 Open Stream을 올바르게 사용하기 위해 지켜야하는 규칙입니다.

- `HANDSHAKE`는 <b>세션 초기에 수행</b>해야 합니다.
- `HANDSHAKE` 이전에 `MONITOR` 또는 `CONTROL`을 호출하면 서버가 거부할 수 있습니다.
- 하나의 세션에서 동시에 하나의 `MONITOR`만 활성화하는 것을 권장합니다.
- `STOP(target=session)`은 “정상 종료 의도”를 명시하는 용도로 사용하며  
   이후 TCP Close를 수행하는 구조를 권장합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">3. 메세지 방향</h4>

<p>
Open Stream에서 사용되는 메시지는 <b>방향과 역할</b>에 따라 다음과 같이 구분됩니다.
</p>

<div style="display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start;">

  <!-- Left: Diagram -->
  <div style="flex:1 1 430px; min-width:280px; max-width:430px;">
    <img
      src="../_assets/2-open_stream_message_direction.png"
      alt="open stream 메세지 플로우 차트"
      style="max-width:100%; height:auto;"
    />
  </div>

  <!-- Right: Two tables -->
<div style="flex:1 1 520px; min-width:280px; max-width:fit-content; display:flex; flex-direction:column; gap:12px;">

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">Client → Server (Commands)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>Command</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><code>HANDSHAKE</code></td><td>프로토콜 버전 협상</td></tr>
        <tr><td><code>MONITOR</code></td><td>주기적 데이터 스트리밍 설정</td></tr>
        <tr><td><code>CONTROL</code></td><td>명령성 REST 요청 실행</td></tr>
        <tr><td><code>STOP</code></td><td>활성 동작 또는 세션 종료</td></tr>
      </tbody>
    </table>
  </div>

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">Client ⇠ Server (Events)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>Event</th>
          <th>Description</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>*_ack</code></td>
          <td>명령이 수락되었음을 알리는 ACK</td>
          <td>예: <code>handshake_ack</code>, <code>monitor_ack</code>, <code>stop_ack</code></td>
        </tr>
        <tr>
          <td><code>data</code></td>
          <td>MONITOR 활성 시 주기적 데이터 이벤트</td>
          <td>Hi6 Open API 서비스 함수를 수행한 결과</td>
        </tr>
        <tr>
          <td><code>error</code></td>
          <td>오류 발생 시 전달되는 에러 메시지</td>
          <td>상세 코드는 Error Codes 섹션 참고</td>
        </tr>
      </tbody>
    </table>
  </div>

  {% hint style="info" %}

  Server → Client 이벤트는 클라이언트 요청과 <b>1:1로 대응되지 않을 수 있습니다.</b>  
  특히 <code>data</code> 이벤트는 클라이언트 요청과 무관하게 언제든지 전송될 수 있습니다.  
  클라이언트는 항상 수신 루프를 유지해야 합니다.

  {% endhint %}
  
</div>
</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">4. MONITOR 스트리밍 동작 방식</h4>

`MONITOR`는 클라이언트가 전달한 레시피를 기준으로  
서버가 지정된 주기(`period_ms`)마다 Hi6 Open API 서비스 함수를 실행하고,  
그 결과를 `data` 이벤트로 스트리밍하는 서버 주도형 메커니즘입니다.

클라이언트는 다음 사항을 전제로 구현해야 합니다.

- 항상 수신 루프를 유지합니다.
- 요청–응답의 동기적 대응을 가정하지 않습니다.
- `data`, `*_ack`, `error` 이벤트는
  순서 보장이 없음을 전제로 처리해야 합니다.


<br>
<h4 style="font-size:16px; font-weight:bold;">5. CONTROL 명령 수행</h4>


`CONTROL`은 정책/구현에 따라 <b>성공 시 별도 응답 라인이 없습니다.</b>

권장 전략:

- 실패 신호는 `error` 또는 `control_err` 이벤트로 감지한다.
- 성공 여부는 다음 방식으로 검증한다.
  - MONITOR 결과 변화 확인
  - 별도 상태 조회 MONITOR endpoint 사용


<br>
<h4 style="font-size:16px; font-weight:bold;">6. Timeout / Watchdog</h4>

서버는 세션이 장시간 유휴 상태일 경우 연결을 종료할 수 있습니다.

클라이언트 권장 사항:

- 연결 직후 즉시 `HANDSHAKE` 수행
- 사용 종료 시 `STOP(target=session)` 후 정상 종료
- 스트리밍 중 수신 루프 중단 방지
- EOF 또는 소켓 오류 발생 시 재연결 및 재HANDSHAKE 로직 준비

현재 서버 구현 기준으로는 다음과 같은 정책이 적용됩니다.

- <b>비무장 상태(Idle / No active MONITOR)</b>  
  &rightarrow; 약 <b>180초</b> 동안 유의미한 활동이 없을 경우 세션 종료

- <b>무장 상태(Active MONITOR streaming)</b>  
  &rightarrow; 스트리밍이 중단된 상태가 <b>약 5초</b> 이상 지속될 경우 세션 종료

※ 위 시간 값은 서버 정책 또는 운영 환경에 따라 변경될 수 있습니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">7. 권장 아키텍쳐 </h4>

실전 구현에서는 다음 구조를 권장합니다.

- 송신(Command)과 수신(Event)을 분리
  - 송신: 명령 생성 + sendall
  - 수신: NDJSON 라인 파서 + 디스패처

- 수신 루프의 단일 책임
  - `\n` 기준 라인 분리
  - JSON 파싱
  - `type` / `error` 기반 이벤트 라우팅# 3.1 HANDSHAKE

## Request
```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

- major: number(정수), 필수, 0 이상

## Response (success)
```json
{"type":"handshake_ack","ok":true,"version":"<server_version>"}\n
```

## Errors
- busy_session_active (409): CONTROL 또는 MONITOR가 active면 HANDSHAKE 불가
- version_mismatch (400): major 불일치
# 3.2 MONITOR

MONITOR는 서버가 주기적으로 REST GET을 호출하고, 그 결과를 NDJSON으로 스트리밍하는 기능입니다.

## Request

```json
{"cmd":"MONITOR","payload":{"period_ms":10,"method":"GET","url":"/project/robot","args":{}}}\n
```

### payload fields
- period_ms: number, 필수 (2~30000 범위 보정)
- method: string, 필수, 반드시 "GET"
- url: string, 필수
  - '/'로 시작
  - 공백 불가
  - 최대 2048
- args: object, 옵션(있으면 object여야 함)

## Response (ack)

```json
{"type":"monitor_ack"}\n
```

## Stream data
MONITOR가 활성화되면 서버는 주기마다 NDJSON 라인을 전송합니다.  
(데이터 라인의 정확한 스키마는 “해당 url의 REST 응답 스키마”에 의해 결정됩니다.)
# 3.3 CONTROL

CONTROL은 REST API를 단발로 호출하는 제어 커맨드입니다.

## Request

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/robot/start","args":{},"body":{"speed":10}}}\n
```

### payload fields
- method: string, 필수, POST|PUT|DELETE 중 하나
- url: string, 필수 (MONITOR와 동일 규칙)
- args: object, 옵션(있으면 object)
- body: object|array, 옵션(없으면 {}로 처리)

## Response
- 성공(HTTP 200) 시: **응답 바디를 보내지 않습니다. (no response line)**
- 실패 시:
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
# 3.4 STOP

STOP은 대상(target)에 따라 monitor/control/session을 중단합니다.

## Request

```json
{"cmd":"STOP","payload":{"target":"monitor"}}\n
```

- target: string 필수
  - "session": TCP 세션 종료
  - "control": control 상태 리셋
  - "monitor": monitor 중지

## Response (ack)

```json
{"type":"stop_ack","target":"session|control|monitor"}\n
```
# Error Codes

이 문서는 Open Stream 서버가 반환할 수 있는 **에러 코드(error code)** 와 그 의미를 설명합니다.

에러는 일반적으로 다음과 같은 **NDJSON 단일 라인 메시지** 형태로 전달됩니다.

<div style="max-width: fit-content;">

```json
{"error":"<error_code>","message":"...","hint":"..."}
```

| Field   | Description            |
| ------- | ---------------------- |
| error   | 기계 판독용 에러 코드           |
| message | 사람이 읽을 수 있는 간단한 설명     |
| hint    | 선택 필드. 문제 해결을 위한 추가 힌트 |

- (주의) 모든 에러가 `hint` 필드를 포함하는 것은 아닙니다.

</div>

<br>

<div style="max-width: fit-content;">

<h4 style="font-size:15px; font-weight:bold;">1. Protocol / Session Errors</h4>

프로토콜 파싱, 세션 상태, 초기 절차 위반 시 발생하는 에러입니다.  

| Error Code          | Description   | Typical Cause         | Client Action         |
| ------------------- | ------------- | --------------------- | --------------------- |
| invalid_ndjson      | NDJSON 파싱 실패  | JSON 깨짐, 개행(`\n`) 누락  | JSON 1줄 + 개행 규칙 준수    |
| rx_buf_overflow     | 수신 버퍼 초과      | 너무 큰 메시지 또는 과도한 burst | 메시지 크기 축소, 전송 rate 제한 |
| handshake_required  | HANDSHAKE 미수행 | 초기 핸드셰이크 누락           | 연결 직후 HANDSHAKE 수행    |
| version_mismatch    | 프로토콜 버전 불일치   | major 값 불일치           | 서버 MAJOR에 맞게 수정       |
| busy_session_active | 세션이 이미 사용 중   | MONITOR/CONTROL 활성 상태 | STOP 후 재시도            |
| session_timeout     | 세션 유휴 타임아웃    | watchdog 시간 초과        | 주기적 활동 유지 또는 재연결      |

<br>

<h4 style="font-size:15px; font-weight:bold;">2. Command / Payload Validation Errors</h4>

요청 메시지 구조 또는 필드 검증 단계에서 발생하는 에러입니다.  

| Error Code      | Description   | Typical Cause      | Client Action       |
| --------------- | ------------- | ------------------ | ------------------- |
| invalid_cmd     | 지원하지 않는 cmd   | 오타 또는 미지원 명령       | cmd 값 확인            |
| invalid_payload | payload 형식 오류 | object 아님          | payload를 object로 수정 |
| missing_field   | 필수 필드 누락      | url, method 등 누락   | 필수 필드 추가            |
| invalid_type    | 필드 타입 오류      | number ↔ string 혼동 | 타입 수정               |
| invalid_value   | 허용되지 않은 값     | enum 범위 벗어남        | 허용 값 사용             |

<br>

<h4 style="font-size:15px; font-weight:bold;">3. HANDSHAKE Errors</h4>

HANDSHAKE 처리 중 발생하는 에러입니다.

| Error Code         | Description    | Typical Cause          | Client Action  |
| ------------------ | -------------- | ---------------------- | -------------- |
| version_mismatch   | 프로토콜 MAJOR 불일치 | client/server major 다름 | 서버 기준 major 사용 |
| handshake_rejected | 핸드셰이크 거부       | 세션 상태 부적합              | 기존 세션 종료 후 재시도 |

<br>

<h4 style="font-size:15px; font-weight:bold;">4. MONITOR Errors</h4>

MONITOR 설정 또는 실행 중 발생하는 에러입니다.  
주기적 REST 호출 설정 검증 단계에서 주로 발생합니다.

| Error Code             | Description        | Typical Cause  | Client Action    |
| ---------------------- | ------------------ | -------------- | ---------------- |
| invalid_method         | MONITOR에서 GET 외 사용 | POST/PUT 사용    | method를 GET으로 수정 |
| invalid_url            | url 형식 오류          | `/` 미시작, 공백 포함 | url 규칙 준수        |
| invalid_period         | period_ms 범위 오류    | 너무 작거나 큼       | 허용 범위로 조정        |
| monitor_already_active | MONITOR 중복 요청      | 이미 활성 상태       | STOP 후 재요청       |
| monitor_internal_error | 내부 REST 호출 실패      | 내부 서버 오류       | 서버 로그 확인         |

<br>

<h4 style="font-size:15px; font-weight:bold;">5. CONTROL Errors</h4>

CONTROL 요청 처리 중 발생하는 에러입니다.  
REST 명령 실행 결과에 따라 동기 또는 비동기로 보고될 수 있습니다.

| Error Code         | Description    | Typical Cause | Client Action      |
| ------------------ | -------------- | ------------- | ------------------ |
| control_err        | CONTROL 실행 실패  | REST 4xx/5xx  | status/body 확인     |
| invalid_body       | body JSON 오류   | 직렬화 실패        | body 구조 점검         |
| method_not_allowed | 허용되지 않은 method | GET 사용 등      | POST/PUT/DELETE 사용 |
| control_busy       | 제어 불가 상태       | 다른 제어 수행 중    | 잠시 후 재시도           |

{% hint style="warning" %}

CONTROL은 성공 시 응답이 없습니다.  
실패 시에만 control_err 또는 공통 에러 메시지가 전달될 수 있습니다.

{% endhint %}

<br>

<h4 style="font-size:15px; font-weight:bold;">6. STOP Errors</h4>

STOP 요청 처리 중 발생하는 에러입니다.

| Error Code      | Description | Typical Cause | Client Action                    |
| --------------- | ----------- | ------------- | -------------------------------- |
| invalid_target  | STOP 대상 오류  | target 오타     | monitor / control / session 중 선택 |
| nothing_to_stop | 중지할 대상 없음   | 이미 종료됨        | 무시 가능                            |
| stop_failed     | 내부 정리 실패    | 내부 상태 오류      | 재연결 권장                           |

<br>

<h4 style="font-size:15px; font-weight:bold;">7. Error Handling Guidelines</h4>

에러 메시지는 항상 NDJSON 단일 라인으로 수신됩니다.

클라이언트는
- 수신 루프에서 error 필드 존재 여부를 먼저 검사하고  
에러 발생 시 세션 상태를 명확히 정리(STOP 또는 재연결) 하는 것을 권장합니다.

- 일부 에러는 복구 가능(recoverable) 하며, 일부는 재연결이 필요(fatal) 할 수 있습니다.

- 복구 가능 여부는 각 에러의 "Client Action"을 기준으로 판단하십시오.

</div># 9. FAQ

## Q1. 왜 HANDSHAKE를 먼저 해야 하나요?
A. 서버는 handshake_ok 상태가 아니면 MONITOR/CONTROL/STOP에 대해 412(handshake_required)를 반환합니다.

## Q2. CONTROL 성공인데 응답이 없어요.
A. 정상입니다. CONTROL이 HTTP 200이면 응답 라인을 비워 “전송하지 않음”으로 처리합니다.

## Q3. MONITOR method는 POST/PUT이 가능한가요?
A. 불가합니다. MONITOR payload의 method는 반드시 "GET" 이어야 합니다.

## Q4. url에 공백이 있으면?
A. 거부됩니다. url은 공백을 포함할 수 없습니다.
<h2 style="display:flex; align-items:center; gap:8px;">
  10. 릴리즈 노트
</h2>

본 섹션은 Open Stream 인터페이스의 버전별 변경 이력을 정리한 릴리즈 노트입니다.<br>
각 버전에서는 기능 추가, 동작 변경, 수정 사항 및 호환성 관련 정보를 제공합니다.


<h4 style="font-size:15px; font-weight:bold;">릴리즈 정보</h4>

<div style="max-width:fit-content;">

| Version| ${cont_model} Version|Release Schedule|Link|
|:--:|:--:|:--:|:--:|
|1.0.0|60.34-00 ⇡|2026.03 예정|[🔗](1-0-0.md)|

</div>


<br>


<h4 style="font-size:15px; font-weight:bold;">릴리즈 노트 분류 기준</h4>

<div style="max-width:fit-content;">

|구분|설명|
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>✨ Added</b></span>|신규 기능, 명령어, 필드 또는 옵션이 추가된 경우|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>🔧 Changed</b></span>|기존 동작 방식, 사양, 기본값이 변경된 경우|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>🛠 Fixed</b></span>|오류 수정, 안정성 개선, 비정상 동작 보완|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>❌ Deprecated</b></span>|향후 제거 예정이거나 사용이 권장되지 않는 기능|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>⚠ Caution</b></span>|해당 버전 사용 시 반드시 인지해야 할 주의 사항|

</div>

<br>

각 릴리즈 문서에서는 <b>해당 버전에서 변경된 내용만</b>을 위 기준에 따라 기술합니다.<br>
상세한 사용 방법이나 프로토콜 설명은 본 문서의 각 레퍼런스 섹션을 따릅니다.

릴리즈 간 동작 변경 사항이 있는 경우, 기존 시스템에 영향을 줄 수 있으므로<br>
업데이트 전 반드시 해당 버전의 릴리즈 노트를 확인하시기 바랍니다.<h2 style="display:flex; align-items:center; gap:8px;">
  Release Notes – v1.0.0
  <span style="
    font-size:14px;
    font-weight:bold;
    padding:2px 6px;
    border-radius:4px;
    border:1px solid #c62828;
    color:#c62828;
  ">
    PREVIEW
  </span>
</h2>


{% hint style="warning" %}

<h4 style="font-size:15px; font-weight:bold;">Status</h4>

- 본 버전은 Open Stream 인터페이스의 최초 공개 버전입니다.
- 정식 배포 : 2026년 3월 (예정)

{% endhint %}

{% hint style="info" %}

<h4 style="font-size:15px; font-weight:bold;">Overview</h4>

- Open Stream은 로봇 제어 및 상태 수신을 위해 설계된 실시간 스트리밍 기반 인터페이스입니다.
- 본 릴리즈에서는 Open Stream의 기본 프로토콜, 레시피 명령어, 그리고 이를 위한 통신 규칙을 제공합니다.

{% endhint %}

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid rgb(255, 140, 0);
  font-size:15px;
  font-weight:bold;
">
  ✨ Added
</h4>

<ul>
  <li>프로토콜
    <ul>
      <li>NDJSON 기반의 경량 스트리밍 프로토콜</li>
      <li>단일 TCP 연결 기반 양방향 통신</li>
      <li>명령 기반 세션 관리 구조</li>
    </ul>
  </li>

  <li>Recipe 명령어
    <ul>
      <li>HANDSHAKE : 프로토콜 버전 협상</li>
      <li>MONITOR : 주기적인 상태 데이터 수신 (ms 단위 주기 설정)</li>
      <li>CONTROL : 실시간 제어 명령 전송 (우선순위 높음)</li>
      <li>STOP : 활성 세션 또는 레시피 종료</li>
    </ul>
  </li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 6px;
  border-left:4px solid #3F51B5;
  font-size:15px;
  font-weight:bold;
">
  🔧 Changed
</h4>

<ul>
  <li>본 버전은 최초 공개 버전으로, 이전 버전 대비 변경 사항은 없습니다.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #2E7D32;
  font-size:15px;
  font-weight:bold;
">
  🛠 Fixed
</h4>

<ul>
  <li>본 버전은 최초 공개 버전으로, 수정된 이슈는 없습니다.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #B71C1C;
  font-size:15px;
  font-weight:bold;
">
  ❌ Deprecated
</h4>

<ul>
  <li>본 버전은 최초 공개 버전으로, 사용 중단되거나 제거된 기능은 없습니다.</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #9E9E9E;
  font-size:15px;
  font-weight:bold;
">
  ⚠ Caution
</h4>

<ul>
  <li>CONTROL과 MONITOR를 동시에 수행하는 경우 CONTROL 세션의 실시간성이 우선 보장됩니다.</li>
  <li>운영체제 스케줄링 및 네트워크 환경에 따라 주기 지연이 발생할 수 있습니다.</li>
  <li>하나의 TCP 연결에서는 하나의 MONITOR 세션만 활성화할 수 있습니다.</li>
  <li>MONITOR 데이터는 실시간 제어 판단 용도로 적합하지 않습니다.</li>
  <li>네트워크 및 클라이언트 성능에 따라 지연 및 지터가 발생할 수 있습니다.</li>
</ul>

<br>

<h4 style="font-size:15px; font-weight:bold;">Related Documentation</h4>

<ul>
  <li><a href="../1-overview/README.md">Open Stream 개요</a></li>
  <li><a href="../1-overview/2-usage-considerations.md">사용 전 유의 사항</a></li>
  <li><a href="../2-protocol/README.md">프로토콜</a></li>
  <li><a href="../3-recipe/README.md">Recipe 명령어</a></li>
  <li><a href="../4-examples/README.md">예제</a></li>
  <li><a href="../9-faq/README.md">F&Q</a></li>
</ul>
