## 2.1 什么是 NDJSON？

Open Stream 使用 **NDJSON (换行分隔 JSON)** 进行消息框架。  
换句话说，**一行等于一个 JSON 消息**。

<h4 style="font-size:15px; font-weight:bold;">1. 消息框架</h4>

<div style="max-width:fit-content;">

- 客户端发送请求如下：

```json
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
{"cmd":"MONITOR","payload":{"period_ms":10,"method":"GET","url":"/project/robot"}}\n
```

- 服务器以相同方式发送响应和事件：

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
{"type":"data","ts":1730000000000,"svc_dur_ms":0.42,"result":{"status":"ok"}}\n
```

</div>

<br>

<h4 style="font-size:15px; font-weight:bold;">2. 强制规则</h4>

1. 每个消息必须精确序列化一个 JSON 对象为单行。  
   → JSON 字符串内部的换行字符将破坏框架。
2. 每个消息 **必须以换行字符 (`\n`) 结束**。
3. 所有消息必须以 **UTF-8** 编码。

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 建议</h4>

1. 推荐无空格序列化以最小化消息大小。

```python
# Python 示例
import json
json.dumps(recipe_data, separators=(",", ":")) + "\n"
```

<br>

<h4 style="font-size:15px; font-weight:bold;">4. 客户端实现技巧</h4>

<div style="max-width:fit-content;">

{% hint style="info" %}

由于 TCP 流特性，单个 `recv()` 调用并不保证正好一行。  
建议将接收到的数据积累到内部缓冲区，并通过 `\n` 分割消息
然后进行 JSON 解析。

{% endhint %}

```python
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