# NDJSON 규칙

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


<h4 style="font-size:15px; font-weight:bold;">2. 반드시 지켜야 할 규칙</h4>

1. JSON은 반드시 1줄이어야 합니다.
    - JSON 문자열 내부에 줄바꿈(개행)이 들어가면 프레이밍이 깨집니다.

2. 각 메시지 끝에는 \n이 반드시 있어야 합니다.
    - 권장: json.dumps(obj) + "\n" 형태로 전송

3. (권장) 공백 없는 직렬화
    - 메시지 크기를 줄이기 위해 아래 형태를 권장합니다.
        <div style="max-width:fit-content;">

        ```py
        json.dumps(obj, separators=(",", ":")) + "\n"
        ```

        </div>

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 클라이언트 구현 팁</h4>

<div style="max-width: fit-content;">

{% hint style = "info" %}

수신 시에는 TCP 스트림 특성상 “한 번의 recv가 한 줄”이 아닐 수 있으므로,  
내부 버퍼에 누적하고, \n 기준으로 라인을 분리하여, 라인 단위로 JSON 파싱을 수행하는 구조를 권장합니다.

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

