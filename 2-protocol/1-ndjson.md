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

