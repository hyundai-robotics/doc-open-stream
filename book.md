
[__SOURCE](README.md)
# ${cont_model} 제어기 기능설명서 - Open Stream

{% hint style="warning" %}

본 매뉴얼에 명시되지 않은 ${cont_model} Open Stream 기능 또는 ${cont_model} Open API 매뉴얼에 명시되지 않은 API를 사용함으로써 발생하는 어떠한 손해나 문제에 대해서도 당사는 책임을 지지 않습니다.

{% endhint %}
[__SOURCE](1-overview/README.md)
# 1. 개요

본 문서는 Open Stream을 사용하는 외부 클라이언트를 위한 사용 메뉴얼입니다.<br>
Open Stream의 목적, 기본 개념, 전체 동작 구조와 지원되는 사용 시나리오를 설명합니다.

<br>

이 문서를 통해 사용자는

- Open Stream이 어떤 문제를 해결하는지
- 어떤 방식으로 동작하는지
- 어떤 상황에서 사용하는 것이 적절한지

를 이해할 수 있습니다.

 📌 최신 변경 사항은 [Release Notes](../10-release-notes/README.md)를 참고하세요.
[__SOURCE](1-overview/1-about-open-stream.md)
## 1.1 Open Stream이란?

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
    <code>*MONITOR</code> 명령을 통해 주기적 데이터 스트리밍을 요청하거나,
    <code>*CONTROL</code> 명령을 통해 단발성 요청을 수행할 수 있습니다.<br>
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

{% endhint %}
[__SOURCE](1-overview/2-usage-considerations.md)
## 1.2 사용 전 유의 사항

Open Stream은 실시간 제어 및 상태 수신을 효율적으로 처리하기 위한 인터페이스이지만,  
다음과 같은 제약 및 전제를 반드시 고려해야 합니다.

- Open Stream은 정주기 데이터 전달을 목표로 하지만 보장하지는 않습니다.
- 운영체제 스케줄링, 네트워크 상태 및 클라이언트 처리 부하에 따라 주기 지연(jitter) 이 발생할 수 있습니다.
- Open API를 활용하므로, ${cont_model} 제어기의 API 서비스 처리 시간이 길어질 경우 Open Stream 의 전체 수행 시간이 증가할 수 있습니다.
- PLC 또는 Playback 작업이 동시에 수행되는 경우, 작업 우선순위에 따라 Open Stream 처리가 지연될 수 있습니다.
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

<div style="max-width:fit-content;">

1. MONITOR 단독 수행

    | **시험 조건**                                                              | **주기 특성 요약**                                                                                                    |
    | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
    | - MONITOR 주기: 2 ms (500 Hz)<br>- CONTROL 미사용<br>- 연속 실행: 10시간          | - <u><b>평균 수신 주기: 약 2.0 ms</b></u><br>                                           |

2. CONTROL + MONITOR 동시 수행

    | **시험 조건**                                                              | **주기 특성 요약**                                                                                                    |
    | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
    | - CONTROL 주기: 2 ms<br>- MONITOR 주기: 2 ms<br>- CONTROL / MONITOR 동시 활성화 | - CONTROL(SEND): <u><b>평균 주기 약 2.0 ms</b></u>, 최대 지연 약 30~40 ms<br>- MONITOR(RECV): <b><u>평균 주기 약 2.1~2.2 ms</b></u>, 최대 지연 수십 ms~100 ms 이상 |

</div>

<br><br>

<b> 해석 및 운용 시 유의 사항 </b>

- MONITOR 레시피를 단독으로 운용하는 경우, 장시간 연속 실행에서도 비교적 안정적인 주기 수신이 가능합니다.  

- CONTROL과 MONITOR를 동시에 운용할 경우, 시스템 설계에 따라 CONTROL 세션이 더 높은 우선순위로 처리됩니다.  

- 이로 인해 CONTROL 주기 안정성은 유지되지만,  
MONITOR 수신 주기는 평균 증가 및 간헐적인 지연이 발생할 수 있습니다.  

- CONTROL과 MONITOR를 동시에 사용하는 환경에서는  
MONITOR 데이터의 정주기성 저하 및 지연 발생을 전제로 시스템을 설계해야 합니다.  
[__SOURCE](2-protocol/README.md)
# 2. 프로토콜

이 섹션에서는 Open Stream이 사용하는 전송 규약(Transport)과 메시지 프레이밍 규칙을 설명합니다.

{% hint style="warning" %}

Open Stream은 요청-응답형 프로토콜이 아닌 **비동기 이벤트 스트림**입니다.  
서버 이벤트(`data`, `*_ack`, `error`)는 클라이언트 요청과 무관하게 언제든 도착할 수 있으므로,  
순서 의존 로직 없이 처리해야 합니다.

{% endhint %}

- Open Stream은 **TCP 소켓** 기반의 단일 세션 통신을 사용합니다.
- 클라이언트/서버 간 메시지는 **NDJSON(Newline Delimited JSON)** 형태로 교환합니다.
- 각 메시지는 **JSON 1개를 1줄로 직렬화한 뒤, 줄 끝에 `\n`을 붙여 전송**합니다.

{% hint style="info" %}

TCP 스트림 특성상, 한 번의 `recv()` 호출이 정확히 한 개의 메시지를 반환하지 않을 수 있습니다.  
수신 데이터는 내부 버퍼에 누적한 뒤, `\n` 기준으로 메시지를 분리하여 파싱해야 합니다.

{% endhint %}

세부 NDJSON 규칙은 아래 문서를 참고하세요.

- [NDJSON 규칙](./1-ndjson.md)

[__SOURCE](2-protocol/1-ndjson.md)
## 2.1 NDJSON 이란?

Open Stream은 메시지 프레이밍을 위해 **NDJSON(Newline Delimited JSON)** 을 사용합니다.  
즉, "한 줄 = 하나의 JSON 메시지" 입니다.

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

<h4 style="font-size:15px; font-weight:bold;">4. 클라이언트 구현 팁</h4>

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


[__SOURCE](2-protocol/2-session-and-streaming.md)
## 2. 세션 및 스트리밍 동작 규칙

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

1. 클라이언트가 서버에 TCP로 접속하여 세션을 생성합니다.
2. 클라이언트는 연결 직후 `HANDSHAKE` 명령을 송신하여 서버와 프로토콜 버전 호환성을 확인합니다.
3. 서버는 `HANDSHAKE` 요청을 처리한 뒤, 프로토콜 버전이 일치하는 경우 `handshake_ack` 이벤트를 송신합니다.
4. 클라이언트는 `HANDSHAKE` 이후 `MONITOR` 명령을 통해 주기적 데이터 스트리밍을 요청하거나, `CONTROL` 명령을 통해 단발성 요청을 수행할 수 있습니다. (`MONITOR`가 활성화된 상태에서도 `CONTROL` 명령을 송신할 수 있습니다.)
5. `MONITOR`가 활성화되면 서버는 클라이언트의 추가 요청과 무관하게 주기적으로 data 이벤트를 비동기적으로 송신합니다.
6. `CONTROL` 명령은 성공 시 별도의 ACK를 송신하지 않으며,
실패한 경우에만 `error` 또는 `control_err` 이벤트가 전달될 수 있습니다.
7. 작업이 완료되면 클라이언트는 `STOP` 명령을 송신하여 활성 동작 또는 세션 종료 의도를 전달하고, 서버의 `stop_ack` 이후 TCP 연결을 종료합니다.

{% hint style="warning" %}

Open Stream은 비동기 이벤트 기반 스트리밍 방식으로, 요청-응답 순서를 보장하지 않습니다.  
`data`, `*_ack`, `error` 이벤트는 서로 간의 선후 관계가 보장되지 않으므로 순서 의존 로직 없이 처리해야 합니다.

{% endhint %}


<br>

<h4 style="font-size:16px; font-weight:bold;">2. 사용 규칙</h4>

다음 규칙은 Open Stream을 올바르게 사용하기 위해 지켜야하는 규칙입니다.

- `HANDSHAKE`는 <b>세션 초기에 수행</b>해야 합니다.
- `HANDSHAKE` 이전에 `MONITOR` 또는 `CONTROL`을 호출하면 서버가 거부할 수 있습니다.
- 하나의 세션에서 동시에 하나의 `MONITOR`만 활성화하는 것을 권장합니다.
- `STOP(target=session)`은 "정상 종료 의도"를 명시하는 용도로 사용하며  
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
          <td>${cont_model} Open API 서비스 함수를 수행한 결과</td>
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
서버가 지정된 주기(`period_ms`)마다 ${cont_model} Open API 서비스 함수를 실행하고,  
그 결과를 `data` 이벤트로 스트리밍하는 서버 주도형 메커니즘입니다.

클라이언트는 다음 사항을 전제로 구현해야 합니다.

- 항상 수신 루프를 유지합니다.
- 요청-응답의 동기적 대응을 가정하지 않습니다.

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

* 위 시간 값은 서버 정책 또는 운영 환경에 따라 변경될 수 있습니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">7. 권장 아키텍쳐 </h4>

실전 구현에서는 다음 구조를 권장합니다.

- 송신(Command)과 수신(Event)을 분리  
  &rightarrow; 송신: 명령 생성 + sendall  
  &rightarrow; 수신: NDJSON 라인 파서 + 디스패처

- 수신 루프의 단일 책임  
  &rightarrow; `\n` 기준 라인 분리  
  &rightarrow; JSON 파싱  
  &rightarrow; `type` / `error` 기반 이벤트 라우팅
[__SOURCE](3-recipe/README.md)
# 1. Recipe 명령어

Recipe 는 Open Stream에서 **클라이언트가 서버로 보내는 NDJSON 라인**을 의미합니다.  
각 라인은 아래 형태로 전송됩니다.

<div style="max-width:fit-content;">

```json
// Request
{"cmd":"<COMMAND>","payload":{...}}\n
````

</div>

서버는 ACK / 이벤트 / 에러를 동일하게 NDJSON 라인으로 반환합니다.

<div style="max-width:fit-content;">

```json
//  Response
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

메세지 필드들의 의미는 다음과 같습니다.

<h4 style="font-size:16px; font-weight:bold;">Request (Client → Server)</h4>

<div style="max-width:fit-content;">

| Key       | Type   | Required | Description                                       |
| --------- | ------ | -------: | ------------------------------------------------- |
| `cmd`     | string |      Yes | 명령 이름 (`HANDSHAKE`, `MONITOR`, `CONTROL`, `STOP`) |
| `payload` | object |      Yes | 명령 파라미터 객체 (명령별 스키마는 각 문서 참고)                     |

1. [HANDSHAKE](./1-handshake.md) : 프로토콜 버전 협상 (세션 초기에 필수)

2. [MONITOR](./2-monitor.md) : 주기적 REST GET 실행 + `data` 스트리밍

3. [CONTROL](./3-control.md) : 단발 REST 실행 (성공 시 **응답 라인 없음**)

4. [STOP](./4-stop.md) : `monitor` / `control` / `session` 중단

</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">Response (Client ⇠ Server)</h4>

<h4 style="font-size:16px; font-weight:bold;">Success</h4>

<div style="max-width:fit-content;">

| Key       | Type    | Required | Description                                                    |
| --------- | ------- | -------: | -------------------------------------------------------------- |
| `type`    | string  |      Yes | 이벤트 타입 (예: `handshake_ack`, `monitor_ack`, `data`, `stop_ack`) |

- `HANDSHAKE` 명령어 응답의 경우, `ok`(boolean), `version`(string) 을 필드에 추가하여 응답함

</div>

<h4 style="font-size:16px; font-weight:bold;">Error</h4>
<div style="max-width:fit-content;">

| Key       | Type   | Required | Description              |
| --------- | ------ | -------: | ------------------------ |
| `error`   | string |      Yes | 에러 코드 (machine-readable) |
| `message` | string |      Yes | 에러 설명 (human-readable)   |
| `hint`    | string |       No | 해결을 위한 가이드 또는 예시         |

</div>
[__SOURCE](3-recipe/1-handshake.md)
## 3.1 HANDSHAKE

세션 시작 직후 수행하는 **프로토콜 버전 협상** 단계입니다.  
`HANDSHAKE` 이전에 `MONITOR`/`CONTROL`을 호출하면 서버가 거부할 수 있습니다.


<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

</div>

<div style="max-width:fit-content;">

| Payload Field   | Required | Type | Rules    |
| ------- | -------- | ---- | -------- |
| `major` | Yes      | int  | 0 이상의 정수 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
```

| Key       | Type    | Required | Description                                                    |
| --------- | ------- | -------: | -------------------------------------------------------------- |
| `ok`      | boolean |       No | 일부 ACK에서 성공 여부를 명시 (`handshake_ack` 등)                         |
| `version` | string  |       No | 서버 프로토콜 버전 (`MAJOR.MINOR.PATCH`)                               |


</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Error Codes</h4>

<div style="max-width:fit-content;">

| Error Code            | HTTP Status | Description       | When it occurs                           |
| --------------------- | ----------- | ----------------- | ---------------------------------------- |
| `busy_session_active` | 409         | 이미 활성화된 작업이 존재함   | CONTROL 또는 MONITOR 태스크 수행 중 HANDSHAKE 요청 |
| `version_mismatch`    | 400         | 프로토콜 MAJOR 버전 불일치 | 클라이언트 `major` 값이 서버 MAJOR와 다름            |
| `missing_major`       | 400         | 필수 필드 누락          | payload에 `major` 키가 없음                   |
| `invalid_major_type`  | 400         | 타입 오류             | `major`가 number(int)가 아님                 |
| `invalid_version`     | 400         | 값 범위 오류           | `major` 값이 음수                            |
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4> 

<div style="max-width:fit-content;">

| Field   | Attribute | Type | Validation Rule     | Error Code           |
| ------- | --------- | ---- | ------------------- | -------------------- |
| `major` | 필수        | int  | payload에 반드시 존재해야 함 | `missing_major`      |
| `major` | 타입        | int  | number 타입이어야 함      | `invalid_major_type` |
| `major` | 범위        | int  | 0 이상의 정수            | `invalid_version`    |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

- 서버는 MAJOR 버전만 검사합니다.
- MINOR / PATCH 변경은 기존 클라이언트와의 호환성을 깨지 않습니다.
- 버전 정책 관련 내용은 [릴리즈 노트 페이지](../10-release-notes/README.md)를 확인하십시오.

</div>
[__SOURCE](3-recipe/2-monitor.md)
## 3.2 MONITOR

클라이언트가 지정한 REST **GET** 서비스를 주기적으로 호출하고,  
그 결과를 NDJSON 단일 라인 형태로 스트리밍하기 위한 명령입니다.

- 현재 구현에서는 **세션당 하나의 MONITOR만 유지**됩니다.
- 새로운 `MONITOR` 명령이 들어오면, 기존 모니터 세션은 자동으로 폐기되고 새 세션으로 교체됩니다.
- `MONITOR`는 반드시 **HANDSHAKE 성공 이후**에만 사용할 수 있습니다.<br>
  &rightarrow; HANDSHAKE 이전에 호출하면 `handshake_required` 에러가 반환됩니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"MONITOR","payload":{"method":"GET","period_ms":2,"url":"/project/robot/joints/joint_states","args":{"jno_start":1,"jno_n":6}}}\n
````

</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type   | Rules                           |
| ----------- | -------- | ------ | ------------------------------- |
| `url`       | Yes      | string | `/`로 시작, 공백 불가, 최대 길이 2048      |
| `method`    | Yes      | string | `"GET"`만 허용                     |
| `period_ms` | Yes      | int    | 2 ~ 30000 (ms), 범위를 벗어나면 자동 클램프 |
| `args`      | No       | object | 쿼리 파라미터용 객체 (JSON object만 허용)   |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* `monitor_ack` 는 MONITOR 요청이 수락되었음을 의미합니다.
* `monitor_ack` 와 첫 `data` 이벤트의 **도착 순서는 보장되지 않습니다.**

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>Streaming</i></u></b>)</h4>

MONITOR가 활성화되면 서버는 지정된 주기(`period_ms`)에 따라
REST API(GET)를 반복 호출하고, 그 결과를 `data` 이벤트로 전송합니다.

<div style="max-width:fit-content;">

```json
{"type":"data","ts":402,"svc_dur_ms":2.960000,"result":{"_type":"JObject","position":[0.0,90.0,0.0,0.0,-90.0,0.0],"effort":[-0.0,98.923641,94.599385,-0.110933,-5.895076,0.0],"velocity":[-0.0,-0.0,0.0,0.0,-0.0,0.0]}}\n
```

</div>

<div style="max-width:fit-content;">

| Response Field | Type | Description |
|------|------|-------------|
| `type` | string | 이벤트 타입 (`data`) |
| `ts` | number | 서버 기준 타임스탬프 (ms) |
| `svc_dur_ms` | number | REST 호출 및 처리에 소요된 시간 (ms) |
| `result` | any | REST 응답 본문 (본문이 존재하는 경우) |
| `status` | number | REST 응답 본문이 비어 있는 경우 반환되는 HTTP 상태 코드 |

</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

모든 에러 응답은 공통 NDJSON 에러 스키마를 따릅니다.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Error Codes</h4>

<div style="max-width:fit-content;">

| Error Code           | HTTP Status | Description   | When it occurs           |
| -------------------- | ----------- | ------------- | ------------------------ |
| `handshake_required` | 412         | HANDSHAKE 미수행 | HANDSHAKE 이전에 MONITOR 호출 |
| `missing_url`        | 400         | 필수 필드 누락      | `url` 키가 없음              |
| `invalid_url`        | 400         | URL 형식 오류     | `/`로 시작하지 않거나 공백 포함      |
| `url_too_long`       | 400         | URL 길이 초과     | URL 길이가 2048 초과          |
| `missing_method`     | 400         | 필수 필드 누락      | `method` 키가 없음           |
| `invalid_method`     | 400         | 메서드 오류        | `"GET"`이 아님              |
| `missing_period_ms`  | 400         | 필수 필드 누락      | `period_ms` 키가 없음        |
| `invalid_period`     | 400         | 타입 오류         | `period_ms`가 int가 아님     |
| `invalid_args`       | 400         | 타입 오류         | `args`가 object가 아님       |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field       | Attribute | Type   | Validation Rule      | Error Code                            |
| ----------- | --------- | ------ | -------------------- | ------------------------------------- |
| `url`       | 필수        | string | payload에 반드시 존재      | `missing_url`                         |
| `url`       | 형식        | string | `/`로 시작, 공백 불가       | `invalid_url`                         |
| `url`       | 길이        | string | 최대 2048              | `url_too_long`                        |
| `method`    | 필수        | string | 반드시 `"GET"`          | `missing_method`, `invalid_method`    |
| `period_ms` | 필수        | int    | int 타입               | `missing_period_ms`, `invalid_period` |
| `period_ms` | 범위        | int    | 2~30000, 범위 초과 시 클램프 | -                                     |
| `args`      | 타입        | object | JSON object만 허용      | `invalid_args`                        |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Watchdog Behavior</h4>

* MONITOR가 활성화되면 워치독은 **ARM 상태**로 전환됩니다.
* 이 상태에서는 세션 유휴 시간 제한이 기존 **180초 → 5초**로 줄어듭니다.
* 모니터링 도중 TCP 연결이 끊기거나,
  일정 시간 동안 서버 측으로 유의미한 명령어를 호출하지 않는 경우  
  워치독이 이를 감지하고 세션을 자동으로 정리합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* MONITOR는 서버 주도형 스트리밍 메커니즘입니다.
* `monitor_ack` 수신 여부와 관계없이 `data` 이벤트는 언제든 도착할 수 있습니다.
* 클라이언트는 항상 수신 루프를 유지하고, `type` 기반으로 이벤트를 처리해야 합니다.
[__SOURCE](3-recipe/3-control.md)
## 3.3 CONTROL

CONTROL은 클라이언트가 로봇을 제어하거나 제어기 내부 데이터를 갱신하기 위해 사용하는 레시피 명령입니다.  
내부적으로는 <b>POST / PUT / DELETE 기반의 ${cont_model} OpenAPI</b>를 호출하며,  
Stream 환경에서도 기존 OpenAPI와 <b>동일한 REST 호출 경로와 유효성 검사 로직</b>이 적용됩니다.

- CONTROL은 반드시 <b>HANDSHAKE 성공 이후</b>에만 사용할 수 있습니다.<br>
  &rightarrow; HANDSHAKE 이전에 호출하면 `handshake_required` 에러로 즉시 거부됩니다.
- CONTROL은 <b>단발성 명령</b>이며, <b style="color:#ec1249;">성공 시 응답 NDJSON 라인을 전송하지 않습니다.</b>
- MONITOR가 활성화된 상태에서도 CONTROL을 수행할 수 있습니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/project/robot/trajectory/joint_traject_insert_point","args":{},"body":{"interval":0.005,"time_from_start":-1,"look_ahead_time":0.004,"point":[1.014532178568314,91.01453217856832,1.014532178568314,1.014532178568314,1.014532178568314,0.013294178568314]}}}\n
````
</div>

<div style="max-width:fit-content;">

| Payload Field    | Required | Type           | Rules                        |
| -------- | -------- | -------------- | ---------------------------- |
| `url`    | Yes      | string         | `/`로 시작, 공백 불가               |
| `method` | Yes      | string         | `POST`, `PUT`, `DELETE` 중 하나 |
| `args`   | No       | object         | REST 쿼리 파라미터용 객체             |
| `body`   | No       | object | array | REST 요청 본문                   |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>no response line</i></u></b>)</h4>

CONTROL 명령이 성공적으로 처리된 경우,
<b>서버는 응답 NDJSON 라인을 전송하지 않습니다.<b>  
클라이언트 측에서는 해당 명령어를 호출만하고 반환값을 돌려받지 않는 구조로 구현해야 합니다.

* 이는 Stream 프로토콜의 설계 특성에 따른 동작입니다.
* CONTROL 성공 여부는 ACK 수신이 아니라 <b>상태 변화 또는 MONITOR 결과</b>를 통해 확인해야 합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

오류가 발생한 경우, 서버는 현재 세션으로 `control_err` 이벤트를 전송합니다.

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| Error Code           | HTTP Status | Description   | When it occurs              |
| -------------------- | ----------- | ------------- | --------------------------- |
| `handshake_required` | 412         | HANDSHAKE 미수행 | HANDSHAKE 이전에 CONTROL 호출    |
| `missing_url`        | 400         | 필수 필드 누락      | `url` 키가 없음                 |
| `invalid_url`        | 400         | URL 형식 오류     | `/`로 시작하지 않거나 공백 포함         |
| `missing_method`     | 400         | 필수 필드 누락      | `method` 키가 없음              |
| `invalid_method`     | 400         | 메서드 오류        | `POST/PUT/DELETE`가 아님       |
| `invalid_args`       | 400         | 타입 오류         | `args`가 object가 아님          |
| `invalid_body`       | 400         | 타입 오류         | `body`가 object 또는 array가 아님 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field    | Attribute | Type           | Validation Rule        | Error Code                         |
| -------- | --------- | -------------- | ---------------------- | ---------------------------------- |
| `url`    | 필수        | string         | payload에 반드시 존재        | `missing_url`                      |
| `url`    | 형식        | string         | `/`로 시작, 공백 불가         | `invalid_url`                      |
| `method` | 필수        | string         | `POST/PUT/DELETE` 중 하나 | `missing_method`, `invalid_method` |
| `args`   | 타입        | object         | JSON object만 허용        | `invalid_args`                     |
| `body`   | 타입        | object | array | object 또는 array만 허용    | `invalid_body`                     |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Watchdog Interaction</h4>

- CONTROL 명령이 성공적으로 수행되면 워치독이 감시하는 최근 활동 시간이 갱신됩니다.
[__SOURCE](3-recipe/4-stop.md)
## 3.4 STOP

STOP은 현재 세션에서 수행 중인 동작을 중단하거나,  
세션 종료 의도를 서버에 명시적으로 전달하기 위한 레시피 명령입니다.

- STOP은 반드시 **HANDSHAKE 성공 이후**에만 사용할 수 있습니다.
- `target` 값에 따라 `monitor`, `control`, `session` 중 하나를 중단합니다.
- `target=session`은 정상 종료 의도를 명시하는 용도로 사용되며,  
  이후 클라이언트가 TCP 연결을 종료하는 구조를 권장합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"STOP","payload":{"target":"session"}}\n
````

</div>
<div style="max-width:fit-content;">

| Payload Field    | Required | Type   | Rules                                      |
| -------- | -------- | ------ | ------------------------------------------ |
| `target` | Yes      | string | `"session"`, `"control"`, `"monitor"` 중 하나 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* `stop_ack.target` 값은 클라이언트가 요청한 `target` 값과 동일합니다.
* STOP 요청이 정상적으로 수락되었음을 의미합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

모든 에러 응답은 공통 NDJSON 에러 스키마를 따릅니다.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| Error Code           | HTTP Status | Description   | When it occurs        |
| -------------------- | ----------- | ------------- | --------------------- |
| `handshake_required` | 412         | HANDSHAKE 미수행 | HANDSHAKE 이전에 STOP 호출 |
| `missing_target`     | 400         | 필수 필드 누락      | `target` 키가 없음        |
| `invalid_target`     | 400         | target 값 오류   | 허용되지 않은 target 값      |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field    | Attribute | Type   | Validation Rule                            | Error Code       |
| -------- | --------- | ------ | ------------------------------------------ | ---------------- |
| `target` | 필수        | string | payload에 반드시 존재                            | `missing_target` |
| `target` | 값         | string | `"session"`, `"control"`, `"monitor"` 중 하나 | `invalid_target` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Behavior Notes</h4>

* `target=monitor`

  * 활성화된 MONITOR 스트리밍을 중단합니다.
* `target=control`

  * CONTROL 수행 상태를 정리합니다.
* `target=session`

  * 세션 종료 의도를 서버에 명시적으로 전달합니다.
  * `stop_ack` 수신 후 TCP 연결을 종료하는 것을 권장합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* STOP은 서버 리소스를 안전하게 정리하기 위한 명령입니다.
* 특히 `target=session` 사용은 정상 종료 시나리오에서 권장됩니다.

[__SOURCE](4-error/README.md)
# 4. 에러 코드

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

</div>
[__SOURCE](5-examples/README.md)
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

[__SOURCE](5-examples/1-utils.md)
## 5.1 공통 유틸리티 (utils)

{% hint style="info" %}

이 문서에서는 이후 모든 예제에서 공통으로 사용되는
<b>Open Stream 클라이언트 유틸리티 코드</b>를 제공합니다.

아래 코드는 <b>설명용 샘플이 아니라 실제로 동작하는 코드</b>이며,
사용자는 이를 그대로 복사하여 자신의 프로젝트에 사용할 수 있습니다.

* 본 예제는 이해와 재현성을 위해
<b>"수신 스레드 + 블로킹 소켓(timeout)" 방식</b>으로 구성했습니다.

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

이 모듈은 "수신(raw bytes)"과 "메시지(dict)" 사이의 경계 처리를 표준화합니다.

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
핵심 목적은 "CONTROL 전송 로직(control.md)"에서 **trajectory 생성 로직을 분리**하여 문서를 짧게 유지하는 것입니다.

- CONTROL 전송은 "통신/타이밍/스키마"가 복잡해지기 쉬운데,
  trajectory 생성까지 섞이면 예제가 너무 길어집니다.
- 따라서 trajectory는 `motion.py`에서 생성하고,
  control 예제는 "생성된 points를 일정 간격으로 보내는 것"에 집중합니다.

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
  (1) 예제 스크립트가 "JSON 스키마"를 반복 작성하지 않도록 합니다.  
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
* 별도 수정 없이 <b>복사-붙여넣기만 해도 정상 동작</b>합니다.
* 다음 문서부터는 이 유틸리티를 기반으로
  <b>HANDSHAKE → MONITOR → CONTROL → STOP</b> 시나리오를 단계적으로 설명합니다.

[__SOURCE](5-examples/2-handshake.md)
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

[__SOURCE](5-examples/3-monitor.md)
## 5.3 MONITOR 예제

이 예제는 Open Stream 세션에서 **MONITOR 스트리밍**을 시작하고,
주기적으로 수신되는 데이터를 처리하는 기본 흐름을 제공합니다.

<h4 style="font-size:16px; font-weight:bold;">수행 시나리오</h4>

1. TCP 연결 생성
2. NDJSON 수신 루프 시작 (parser + dispatcher 연결)
3. MONITOR 전송 (method/url/period_ms/args)
4. `monitor_ack` 수신 확인 (또는 서버가 정의한 ACK 타입)
5. `monitor_data`(스트림 데이터) 수신 처리
6. 예제 종료 (연결 종료)

* 실제 운용에서는 스트리밍 종료 시 `STOP target=monitor`를 전송하는 것이 권장됩니다. (STOP 예제에서 다룹니다)

<br>
<h4 style="font-size:16px; font-weight:bold;">준비물</h4>

* `utils/` 디렉토리 (net.py / parser.py / dispatcher.py / api.py) 
* 서버 주소, 포트(`49000`)
* MONITOR 대상 REST URL, period_ms, args

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
│   ├── handshake.py
│   └── monitor.py        # (이 문서에서 제공하는 시나리오 코드)
│
└── main.py               # 시나리오 런처(엔트리 포인트)
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/monitor.py</h4>

<div style="max-width:fit-content;">

```python
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
```

</div>

<div style="max-width:fit-content;">
  &rightarrow; MONITOR 요청을 전송하고, ACK 및 스트리밍 데이터를 수신해 출력하는 실행 가능한 시나리오 코드입니다.
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor


def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream Examples")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # common options
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # monitor options
    p.add_argument("--url", default="/api/health")

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(
            args.host,
            args.port,
            major=args.major,
            url=args.url,
            period_ms=args.period_ms,
        )


if __name__ == "__main__":
    main()
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

프로젝트 루트에서 아래 명령을 실행합니다.

<div style="max-width:fit-content;">

```bash
python3 main.py monitor --host 192.168.1.150 --port 49000 --major 1 --url /project/robot/joints/joint_states --period-ms 1000
```

<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[tx] {"cmd":"MONITOR","payload":{"method":"GET","url":"/project/robot/joints/joint_states","period_ms":1000,"id":1,"args":{}}}
[ack] monitor_ack ok=None url=None period_ms=None
[event] {'type': 'data', 'id': 1, 'ts': 1000, 'svc_dur_ms': 0.224, 'result': {'_type': 'JObject', 'position': [2.870257, 92.870159, 2.869597, 2.86937, -87.129492, 2.868506], 'effort': [0.0, 83.719222, 92.270308, 0.773519, -4.086226, 0.336679], 'velocity': [-0.0, -0.0, 0.0, 0.0, -0.0, 0.0]}}
[net] connection closed
```

</div>

* 참고 : 에러가 발생하면 `{ "error": "...", "message": "...", "hint": "..." }` 형태로 수신됩니다.
* 참고 : `monitor_data`의 payload 스키마(`ts`, `value` 등)는 서버 구현에 따라 달라질 수 있으므로, 실제 메시지 구조에 맞게 출력/파싱 로직을 조정하십시오.

[__SOURCE](5-examples/4-control.md)
## 5.4 CONTROL 예제 (Joint Trajectory)

{% hint style="info" %}

이 문서에서는 Open Stream의 **CONTROL** 명령을 이용해  로봇에 **joint trajectory 포인트를 스트리밍 전송**하는 예제를 제공합니다.

Trajectory 생성/저장은 `utils/motion.py`에서 담당합니다.<br>
Open Stream 메시지 구성/전송은 `utils/api.py`에서 담당합니다.<br>
사용자는 아래 코드를 그대로 복사하여 자신의 프로젝트에 사용할 수 있습니다.

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">사전 준비</h4>

- `utils/` 디렉토리 (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream 서버 주소/포트 (예: `192.168.1.150:49000`)
- HTTP로 joint state 조회 가능해야 함  
  예: `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">시나리오 흐름</h4>

1) TCP 연결 및 수신 루프 시작  
2) HANDSHAKE 전송 및 ack 확인  
3) HTTP GET으로 `/project/robot/joints/joint_states` 조회 (rad)  
4) `motion.rad_to_deg()`로 deg 변환  
5) `motion.generate_sine_trajectory()`로 deg trajectory 생성  
6) `CONTROL / joint_traject_init` 전송  
7) `CONTROL / joint_traject_insert_point`를 dt 간격으로 반복 전송  
8) 종료 (필요 시 STOP 예제 사용)
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
│   ├── motion.py
│   └── api.py
│
├── scenarios/
│   ├── handshake.py
│   ├── monitor.py
│   └── control.py
│
└── main.py
````

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">CONTROL Body 규칙</h4>

`joint_traject_insert_point`는 아래 필드를 포함하는 것을 권장합니다.

* `interval` (sec): 포인트 간 간격 (예: `dt_sec`)
* `time_from_start` (sec): 시작 기준 시간 (예: `index * dt_sec`)
  * 서버 구현에 따라 이 필드는 **누락 시 오류**가 날 수 있으므로 포함을 권장합니다.
* `look_ahead_time` (sec): 제어 선행 시간
* `point` (deg): joint 각도 리스트

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

아래 코드는 **그대로 복사-붙여넣기 후 실행 가능한 코드**입니다.

<details><summary>Click to check the python code</summary>

```python
# scenarios/control.py
import json
import math
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from utils.net import NetClient
from utils.parser import NDJSONParser
from utils.dispatcher import Dispatcher
from utils.api import OpenStreamAPI
from utils.motion import generate_sine_trajectory, save_trajectory  # rad_to_deg 제거


def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    /project/robot/joints/joint_states 를 HTTP GET으로 조회해 joint positions(deg) 리스트를 반환한다.

    (서버 C++ 구현 기준)
    - position: deg 단위로 내려옴
    - velocity: deg/s
    - effort: Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET failed: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP response is not valid JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # C++ 구현은 {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]} 형태
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # e.g. {"j1": 10.0, "j2": 20.0, ...} 형태도 방어
            items: List[Tuple[int, float]] = []
            for k, v in data.items():
                if not isinstance(v, (int, float)):
                    continue
                if isinstance(k, str) and k.startswith("j"):
                    try:
                        idx = int(k[1:])
                        items.append((idx, float(v)))
                    except ValueError:
                        continue
            q = [v for _, v in sorted(items, key=lambda x: x[0])]

    if not q:
        raise RuntimeError(f"Cannot extract joint positions from response: {data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # trajectory
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # control timing
    look_ahead_time: float = 0.1,
) -> None:
    net = NetClient(host, port)
    parser = NDJSONParser()
    dispatcher = Dispatcher()
    api = OpenStreamAPI(net)

    handshake_ok = {"ok": False}

    def on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        handshake_ok["ok"] = ok
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")

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
        print("[ERR] handshake_ack not received; aborting.")
        net.close()
        return

    # 3) base pose (deg) via HTTP  <-- 여기 핵심
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] base pose joints={len(base_deg)} deg-range={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) trajectory 생성 (deg)
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] trajectory saved: {saved_path} (points={len(points_deg)}, dt={dt_sec})")

    # 5) CONTROL init
    api.joint_traject_init()

    # 6) CONTROL insert_point streaming
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),   # 유효한 time_from_start 사용
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg], # point는 deg (서버가 deg를 rad로 변환)
        }
        api.joint_traject_insert_point(body)

        # dt에 맞춰 송신 (단순 예제)
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 연결 예시</h4>

기존 `main.py` 구조를 유지한다면, `control` 시나리오를 아래처럼 호출할 수 있습니다.

<details><summary>Click to check the python code</summary>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control
from scenarios import stop as sc_stop


def main():
    p = argparse.ArgumentParser(description="Open Stream Client Examples")

    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)
    p.add_argument("--major", type=int, default=1)

    # -------------------------
    # MONITOR options
    # -------------------------
    p.add_argument("--url", default="/api/health")
    p.add_argument("--period-ms", type=int, default=1000)

    # -------------------------
    # CONTROL options
    # -------------------------
    p.add_argument("--http-port", type=int, default=8888)
    p.add_argument("--dt-sec", type=float, default=0.02)
    p.add_argument("--total-duration-sec", type=float, default=1.0)
    p.add_argument("--cycle-sec", type=float, default=1.0)
    p.add_argument("--amplitude-deg", type=float, default=5.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--look-ahead-time", type=float, default=0.1)

    args = p.parse_args()

    if args.scenario == "handshake":
        sc_handshake.run(args.host, args.port, major=args.major)

    elif args.scenario == "monitor":
        sc_monitor.run(
            args.host,
            args.port,
            major=args.major,
            url=args.url,
            period_ms=args.period_ms,
        )

    elif args.scenario == "control":
        sc_control.run(
            args.host,
            args.port,
            major=args.major,
            http_port=args.http_port,
            cycle_sec=args.cycle_sec,
            amplitude_deg=args.amplitude_deg,
            dt_sec=args.dt_sec,
            total_sec=args.total_duration_sec,
            active_joint_count=args.active_joint_count,
            look_ahead_time=args.look_ahead_time,
        )

    elif args.scenario == "stop":
        sc_stop.run(args.host, args.port, target="session")


if __name__ == "__main__":
    main()

```

---

</div>

</details>

<br>
<h4 style="font-size:16px; font-weight:bold;">실행 방법</h4>

1. 로봇을 원점 위치로 이동 시킵니다. 
2. joint_traject_insert_point API 의 동작 조건은 Playback 이 재생 중일 때 입니다.  
하기 wait 문을 job 에 그대로 작성합니다.  
0001.job - ```wait di1```
3. 0001.job 을 자동모드에서 start 합니다.
4. 하기 main.py 수행문을 실행합니다.

    <div style="max-width:fit-content;">

    ```bash
    # 예: 30초 길이의 sine trajectory(진폭 1 deg)를 dt=2ms로 전송합니다.
    # - cycle-sec=5  : sine 파 1주기(0→2π)가 5초에 해당합니다.
    # - look-ahead-time=0.04s, dt=0.002s 이므로, look-ahead 버퍼는 0.04/0.002 = 20 포인트입니다.
    #   (버퍼에 20개의 point 가 찰 때까지 추종이 지연될 수 있습니다.)

    python3 main.py control \
    --host 192.168.1.150 \
    --port 49000 \
    --major 1 \
    --http-port 8888 \
    --total-duration-sec 30.0 \
    --dt-sec 0.002 \
    --look-ahead-time 0.04 \
    --amplitude-deg 1 \
    --cycle-sec 5
    ```

    </div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">Expected Output</h4>

환경에 따라 출력은 달라질 수 있으나, 일반적으로 아래 흐름을 확인할 수 있습니다.

<div style="max-width:fit-content;">

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] base pose joints=6
[INFO] trajectory saved: .../data/trajectory_XXXXXX.json (points=51, dt=0.02)
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_init", ...}
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_insert_point", ...}
...
[net] connection closed
```

</div>

---

## 요약

* CONTROL은 로봇 제어 메시지를 전송하는 프로토콜 명령입니다.
* Trajectory 생성/저장은 `utils/motion.py`에 분리하여, control 예제는 **전송 로직**에 집중합니다.
* `joint_traject_insert_point` 전송 시 `time_from_start`를 포함하고, `dt` 기반으로 증가시키는 것을 권장합니다.
[__SOURCE](5-examples/5-stop.md)
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

* 구현/버전에 따라 `control`, `monitor`는 선택적으로 지원될 수 있으며,  
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
[__SOURCE](9-faq/README.md)
# 9. FAQ

## Q1. 왜 HANDSHAKE를 먼저 해야 하나요?
A. 서버는 handshake_ok 상태가 아니면 MONITOR/CONTROL/STOP에 대해 412(handshake_required)를 반환합니다.

## Q2. CONTROL 성공인데 응답이 없어요.
A. 정상입니다. CONTROL이 HTTP 200이면 응답 라인을 비워 "전송하지 않음"으로 처리합니다.

## Q3. MONITOR method는 POST/PUT이 가능한가요?
A. 불가합니다. MONITOR payload의 method는 반드시 "GET" 이어야 합니다.

## Q4. url에 공백이 있으면?
A. 거부됩니다. url은 공백을 포함할 수 없습니다.

[__SOURCE](10-release-notes/README.md)
<h2 style="display:flex; align-items:center; gap:8px;">
  10. 릴리즈 노트
</h2>

본 섹션은 Open Stream 인터페이스의 버전별 변경 이력을 정리한 릴리즈 노트입니다.<br>
각 버전에서는 기능 추가, 동작 변경, 수정 사항 및 호환성 관련 정보를 제공합니다.




<h4 style="font-size:15px; font-weight:bold;">릴리즈 정보</h4>

<div style="max-width:fit-content;">

| *Version| ${cont_model} Version|Release Schedule|Link|
|:--:|:--:|:--:|:--:|
|1.0.0|60.34-00 ⇡|2026.03 예정|[🔗](1-0-0.md)|

----

</div>

*Version : **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| Field | 의미 | 호환성 정책 |
|------|------|-------------|
| MAJOR | 프로토콜의 근본적인 변경 | **MAJOR가 다르면 호환되지 않음** |
| MINOR | 기능 추가(하위 호환) | MAJOR가 같으면 호환 |
| PATCH | 버그 수정 및 내부 개선 | 항상 호환 |

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
업데이트 전 반드시 해당 버전의 릴리즈 노트를 확인하시기 바랍니다.
[__SOURCE](10-release-notes/1-0-0.md)
<h2 style="display:flex; align-items:center; gap:8px;">
  Release Notes - v1.0.0
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
