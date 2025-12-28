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