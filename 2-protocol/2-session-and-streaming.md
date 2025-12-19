# Session & Streaming

<div style="fit-content;">

{% hint style="info" %}

이 문서는 Open Stream을 실제로 구현하고 운영하기 위해 반드시 이해해야 하는  
<b>세션 라이프사이클(Session Lifecycle)</b> 과 <b>스트리밍 동작 방식(Streaming Behavior)</b> 을 설명합니다.

{% endhint %}

</div>

<br>

<h4 style="font-size:15px; font-weight:bold;">1. Session Lifecycle</h4>

Open Stream은 <b>TCP 연결 1개를 하나의 세션(Session)</b> 으로 간주합니다.  
일반적인 세션 흐름은 다음과 같습니다.

1. 클라이언트가 서버와 TCP 연결을 생성합니다.
2. 클라이언트는 연결 직후 `HANDSHAKE` 명령을 전송합니다.
3. 클라이언트는 `MONITOR` 및/또는 `CONTROL` 명령을 요청합니다.  
    ※ `MONITOR`가 활성화된 경우, 서버는 주기적으로 `data` 이벤트를 스트리밍합니다.
4. 작업이 완료되면 클라이언트는 `STOP` 명령을 전송합니다.
5. 이후 TCP 연결을 종료합니다.

<br>

<h4 style="font-size:15px; font-weight:bold;">2. 사용 규칙</h4>

다음 규칙은 Open Stream을 올바르게 사용하기 위해 지켜야하는 규칙입니다.

- `HANDSHAKE`는 <b>세션 초기에 수행</b>해야 합니다.
- `HANDSHAKE` 이전에 `MONITOR` 또는 `CONTROL`을 호출하면 서버가 거부할 수 있습니다.
- 하나의 세션에서 동시에 하나의 `MONITOR`만 활성화하는 것을 권장합니다.
- `STOP(target=session)`은 “정상 종료 의도”를 명시하는 용도로 사용하며  
   이후 TCP Close를 수행하는 구조를 권장합니다.

<br>
<h4 style="font-size:15px; font-weight:bold;">3. 메세지 방향</h4>

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
    <div style="font-weight:bold; margin-bottom:6px;">Server → Client (Events)</div>
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
          <td>명령 수신 또는 설정 성공 ACK</td>
          <td>예: <code>handshake_ack</code>, <code>monitor_ack</code>, <code>stop_ack</code></td>
        </tr>
        <tr>
          <td><code>data</code></td>
          <td>MONITOR 활성 시 주기적 데이터 이벤트</td>
          <td>요청과 1:1 매칭되지 않을 수 있음</td>
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

  <ul>
    <li>Server → Client 이벤트는 클라이언트 요청과 <b>1:1로 대응되지 않을 수 있습니다.</b></li>
    <li>특히 <code>data</code> 이벤트는 클라이언트 요청과 무관하게 언제든지 전송될 수 있습니다.</li>
    <li>클라이언트는 항상 수신 루프를 유지해야 합니다.</li>
  </ul>

  {% endhint %}
  
</div>
</div>




---

## 3. Streaming Behavior

`MONITOR`가 활성화되면 서버는 클라이언트 요청과 무관하게 언제든지
`data` 메시지를 푸시할 수 있습니다.

따라서 클라이언트는 다음을 반드시 만족해야 합니다.

- 항상 수신 루프(receive loop)를 유지한다.
- 요청을 보냈다고 해서 “곧바로 응답이 온다”는 가정을 하지 않는다.
- `data`, `ack`, `error`가 <b>임의 순서로 섞여 수신될 수 있음</b>을 전제로 파싱한다.

---

## 4. CONTROL Response Handling

`CONTROL`은 정책/구현에 따라 <b>성공 시 별도 응답 라인이 없을 수 있습니다.</b>

권장 전략:

- 실패 신호는 `error` 또는 `control_err` 이벤트로 감지한다.
- 성공 여부는 다음 방식으로 검증한다.
  - MONITOR 결과 변화 확인
  - 별도 상태 조회 MONITOR endpoint 사용
  - 애플리케이션 레벨의 idempotent 설계

---

## 5. Timeout / Watchdog

서버는 세션이 장기간 유휴 상태로 유지되면 연결을 종료할 수 있습니다.

클라이언트 권장 사항:

- 연결 직후 즉시 `HANDSHAKE` 수행
- 세션이 필요 없으면 `STOP(target=session)` 후 정상 종료
- 스트리밍 사용 시 수신 루프가 중단되지 않도록 구현
- 연결 종료(EOF) 또는 소켓 오류 발생 시 재연결/재HANDSHAKE 로직 준비

---

## 6. Recommended Client Architecture

실전 구현에서는 아래 구조를 권장합니다.

- 송신(Command)과 수신(Event)을 분리한다.
  - 송신: 명령 생성 + sendall
  - 수신: NDJSON 라인 파서 + 디스패처

- 수신 루프는 단일 책임을 갖는다.
  - 라인 분리(`\n`)
  - JSON 파싱
  - `type`/`error` 기반 라우팅

(예제 코드는 Examples 섹션에서 제공합니다.)
