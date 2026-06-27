
[__SOURCE](README.md)
# ${cont_model} 控制器功能手册 - 打开流

{% hint style="warning" %}

HD 현대 로보틱스 对于因使用本手册中未指定的 ${cont_model} 打开流功能或未在 ${cont_model} 开放 API 手册中记录的 API 而导致的任何损害或问题不承担责任。

{% endhint %}
[__SOURCE](0-about-this-manual/README.md)
# 关于手册
[__SOURCE](0-about-this-manual/precautions.md)
# 注意事项

{% include file="zh/precautions.md" %}
[__SOURCE](0-about-this-manual/safety-notice.md)
# 安全注意事项

{% include file="zh/safety-notice.md" %}
[__SOURCE](1-overview/README.md)
# 1. 概述

本文件是为使用 Open Stream 的外部客户提供的用户指南。  
它解释了 Open Stream 的目的、核心概念、整体架构以及支持的使用场景。  

<br>

通过本文档，读者将了解：
- Open Stream 旨在解决什么问题
- Open Stream 如何运作
- 何时以及在什么情况下应使用 Open Stream

* 有关最新更新和变更，请参阅 [Release Notes](../7-release-notes/README.md)
[__SOURCE](1-overview/1-about-open-stream.md)
## 1.1 什么是 Open Stream？

Open Stream 是一个接口，允许客户端通过短时间间隔反复调用 **${cont_model} Open APIs** 以流式方式持续接收结果。

<br>

它通过嵌入在 ${cont_model} 控制器内的 **基于 TCP 的轻量级服务器** 提供流式接口，使外部客户端能够通过持久连接持续发送和接收数据。

<br>

Open Stream 具有以下特点：

- 维护 **单个长期存在的 TCP 连接**
- 对请求和响应使用 **NDJSON（换行分隔 JSON）**
- 支持 **周期性数据流（`MONITOR`）** 和 **即时控制命令（`CONTROL`）**
- 消除 HTTP 请求/响应周期的重复创建

<br>

Open Stream 是为需要处理  
**高频率控制命令和状态监测的客户端环境** 设计的，且通过单个连接进行。

<br><br>

<b>整体操作概述</b>

Open Stream 的基本操作流程如下。

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
  <ol style="line-height:1.5;">

  <li>客户端与服务器建立 TCP 连接，创建一个会话。</li><br>

  <li>连接后，客户端立即发送 <code>HANDSHAKE</code> 命令<br>
      以验证与服务器的协议版本兼容性。</li><br>

  <li>服务器处理 <code>HANDSHAKE</code> 请求，如果协议版本兼容，则发送 <code>handshake_ack</code> 事件。</li><br>

  <li>在成功执行 <code>HANDSHAKE</code> 后，客户端可以使用 <code>MONITOR</code> 命令请求周期性数据流，或者使用 <code>CONTROL</code> 命令执行一次性请求。
      <small>(即使在 MONITOR 活动期间，也可以发送 CONTROL 命令。)</small>
  </li><br>

  <li>当 <code>MONITOR</code> 活动时，服务器在配置的间隔发送 <code>data</code> 事件，而不受额外客户端请求的影响。</li><br>
    
  <li>成功的 <code>CONTROL</code> 命令不会生成 ACK 响应。<br>
      只有失败才可能导致 <code>error</code> 或 <code>control_err</code> 事件。</li><br>

  <li>当操作完成时，客户端发送 <code>STOP</code> 命令
      以指示终止活动操作或会话意图，
      并在收到 <code>stop_ack</code> 后关闭 TCP 连接。
  </li>

  </ol>
</div>

</div>

<br>

{% hint style="info" %}

**什么是 MONITOR 命令？**  
MONITOR 命令重复在客户端定义的间隔内调用单个 ${cont_model} Open API 服务  
并持续将结果流式传送到客户端。

**什么是 CONTROL 命令？**  
CONTROL 命令用于向 ${cont_model} Open API 发送一次性控制请求。  
客户端可以根据需要在短时间间隔内重复发送 CONTROL 命令。

{% endhint %}

Open Stream 允许 MONITOR 和 CONTROL 命令在单个 TCP 连接中一起使用。

{% hint style="warning" %}

然而，在单个连接中，**只能同时活跃一个 MONITOR 会话和一个 CONTROL 会话**。

{% endhint %}
[__SOURCE](1-overview/2-usage-considerations.md)
## 1.2 使用注意事项

Open Stream 旨在高效处理实时控制和状态监控。  
然而，以下限制和假设必须仔细考虑。

- Open Stream 针对周期性数据传输，但不 **保证严格确定性**。
- 可能会因操作系统调度、网络条件以及客户端处理负载而出现周期性抖动。
- 由于 Open Stream 基于 Open APIs，Open Stream 的执行时间可能受到 ${cont_model} 控制器的 API 服务处理时间的影响。
- 当 PLC 或播放任务同时运行时，Open Stream 执行可能会因系统任务优先级而延迟。
- 每个 TCP 连接只能有 **一个 MONITOR 会话** 处于激活状态。
- 所有命令必须遵循定义的协议顺序。
  违反顺序可能导致命令被拒绝或连接终止。

<br><br>

<b>MONITOR 和 CONTROL 操作的性能参考 （测试结果）</b>

以下结果比较了在相同测试环境下 MONITOR 单独操作和同时进行 CONTROL + MONITOR 操作的周期性行为。

测试环境：
- 服务器: ${cont_model} COM
- 客户端: Windows 11 上的 Python 客户端
- 网络: TCP 连接
- 发送/接收周期: 最大可配置的 MONITOR 频率

<br>

结果总结

<div style="max-width:fit-content;">

1. 仅 MONITOR

| **测试条件** | **周期性特征** |
| --- | --- |
| - MONITOR 周期: 2 ms (500 Hz)<br>- 未使用 CONTROL<br>- 持续运行: 10 小时 | - <u><b>平均接收周期: ~2.0 ms</b></u> |

2. CONTROL + MONITOR 并发

| **测试条件** | **周期性特征** |
| --- | --- |
| - CONTROL 周期: 2 ms<br>- MONITOR 周期: 2 ms<br>- CONTROL 和 MONITOR 同时激活 | - CONTROL (发送): <u><b>平均周期 ~2.0 ms</b></u>, 最大延迟 ~30-40 ms<br>- MONITOR (接收): <u><b>平均周期 ~2.1-2.2 ms</b></u>, 最大延迟从数十毫秒到 >100 毫秒 |

</div>

<br><br>

<b>解读与操作注意事项</b>

- 当单独使用 MONITOR 时，即使在长时间的连续操作中，也可以实现相对稳定的周期性接收。
- 当 CONTROL 和 MONITOR 同时使用时，根据系统设计，CONTROL 会话优先级较高。
- 结果是，CONTROL 周期稳定性得以维持，而 MONITOR 接收周期可能会增加并经历间歇性延迟。
- 同时使用 CONTROL 和 MONITOR 的系统必须设计为假设 MONITOR 周期性可能严重下降和抖动。
[__SOURCE](2-protocol/README.md)
# 2. 协议

本节描述了 Open Stream 使用的传输协议和消息封装规则。

> **警告**
>
> Open Stream 不是请求-响应协议，而是 **事件流**。  
> 服务器事件 (`data`, `*_ack`, `错误 (error)`) 可能会在任何时间到达，无论客户端请求如何，  
> 因此客户端逻辑必须在不依赖消息排序的情况下实现。

- Open Stream 使用基于 **TCP 套接字的单会话通信模型**。
- 客户端和服务器之间交换的消息使用 **NDJSON (新行分隔 JSON)**。
- 每条消息通过 **每行序列化一个 JSON 对象并在末尾附加 `\n` 发送**。

> **信息**
>
> 由于 TCP 流的性质，单个 `recv()` 调用可能不会返回恰好一条消息。  
> 接收到的数据应在内部缓冲区中累积，并通过在 `\n` 上拆分进行解析。

有关详细的 NDJSON 规则，请参阅下面的文档。

- [NDJSON 规范](./1-ndjson.md)
[__SOURCE](2-protocol/1-ndjson.md)
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
[__SOURCE](2-protocol/2-session-and-streaming.md)
## 2.2 会话和流规则

<div style="fit-content;">

{% hint style="info" %}

本文件解释了 <b>会话生命周期</b> 和 <b>流行为</b>  
必须了解，以正确实施和操作 Open Stream。

{% endhint %}

</div>

<br>

<h4 style="font-size:16px; font-weight:bold;">1. 会话生命周期</h4>

Open Stream 将 <b>一个 TCP 连接视为一个会话</b>。  
典型的会话流程如下：

1. 客户端通过 TCP 连接到服务器以创建会话。
2. 连接后，客户端立即发送 `HANDSHAKE` 命令以验证与服务器的协议版本兼容性。
3. 处理 `HANDSHAKE` 请求后，如果协议版本匹配，服务器发送 `handshake_ack` 事件。
4. 在 `HANDSHAKE` 之后，客户端可以通过 `MONITOR` 请求周期性的数据流，或通过 `CONTROL` 执行一次性请求。（在 `MONITOR` 活动时也可以发送 `CONTROL`。）
5. 当 `MONITOR` 活动时，服务器定期发送 `data` 事件，而不管其他客户端请求。
6. `CONTROL` 命令在成功时不发送单独的 ACK；仅在失败时可能发送 `错误 (error)` 或 `control_err` 事件。
7. 工作完成时，客户端发送 `STOP` 表示对活动操作或会话的终止意图，然后在收到服务器的 `stop_ack` 后关闭 TCP 连接。

{% hint style="warning" %}

Open Stream 是一种事件驱动的流协议，不保证请求-响应的顺序。  
由于 `data`、`*_ack` 和 `错误 (error)` 事件之间的到达顺序不保证，客户端必须在不依赖消息顺序的情况下处理事件。

{% endhint %}


<br>

<h4 style="font-size:16px; font-weight:bold;">2. 使用规则</h4>

要正确使用 Open Stream，必须遵循以下规则。

- `HANDSHAKE` 必须在 <b>会话开始时</b> 执行。
- 如果在 `HANDSHAKE` 之前调用 `MONITOR` 或 `CONTROL`，服务器可能会拒绝请求。
- `STOP(target=session)` 用于明确表示“优雅终止意图”，建议在之后关闭 TCP 连接。

<br>
<h4 style="font-size:16px; font-weight:bold;">3. 消息方向</h4>

<p>
在 Open Stream 中使用的消息根据 <b>方向和角色</b> 分类如下。
</p>

<div style="display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start;">

  <!-- Left: Diagram -->
  <div style="flex:1 1 430px; min-width:280px; max-width:430px;">
    <img
      src="../_assets/2-open_stream_message_direction.png"
      alt="open stream message flow chart"
      style="max-width:100%; height:auto;"
    />
  </div>

  <!-- Right: Two tables -->
<div style="flex:1 1 520px; min-width:280px; max-width:fit-content; display:flex; flex-direction:column; gap:12px;">

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">客户端 → 服务器 (命令)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>命令</th>
          <th>描述</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><code>HANDSHAKE</code></td><td>协议版本协商</td></tr>
        <tr><td><code>MONITOR</code></td><td>配置周期性数据流</td></tr>
        <tr><td><code>CONTROL</code></td><td>执行命令类型的 REST 请求</td></tr>
        <tr><td><code>STOP</code></td><td>终止活动操作或会话</td></tr>
      </tbody>
    </table>
  </div>

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">客户端 <-- 服务器 (事件)</div>
    <table style="width:fit-content; min-width:fit-content; border-collapse:collapse;">
      <thead>
        <tr>
          <th>事件</th>
          <th>描述</th>
          <th>备注</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>*_ack</code></td>
          <td>表示命令已被接受的 ACK</td>
          <td>例如 <code>handshake_ack</code>、<code>monitor_ack</code>、<code>stop_ack</code></td>
        </tr>
        <tr>
          <td><code>data</code></td>
          <td>当 MONITOR 活动时的周期性数据事件</td>
          <td>执行 ${cont_model} Open API 服务功能的结果</td>
        </tr>
        <tr>
          <td><code>error</code></td>
          <td>在发生故障时传递的错误消息</td>
          <td>有关详细信息，请参阅错误代码部分</td>
        </tr>
      </tbody>
    </table>
  </div>

  {% hint style="info" %}

  服务器 → 客户端事件可能 <b>与客户端</b> 请求不对应 1:1。  
  虽然 `*_ack` 和 `错误 (error)` 遵循请求-响应模式，  
  由 MONITOR 生成的 `data` 事件是独立流的。  
  客户端必须始终保持接收循环运行。

  {% endhint %}
  
</div>
</div>

<div style="max-width:fit-content;">

| 请求-响应 | 流 |
|---|---|
| 客户端 → `HANDSHAKE/MONITOR/CONTROL/STOP` → 服务器<br>客户端 ← `*_ack`、`错误 (error)` ← 服务器 | （在 `monitor_ack` 之后）<br>服务器 → `data` → 客户端<br>服务器 → `data` → 客户端<br>... |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">4. MONITOR 流行为</h4>

`MONITOR` 是一个由服务器驱动的机制，基于客户端提供的配方，  
服务器在指定的间隔内 (`period_ms`) 执行 ${cont_model} Open API 服务功能  
并将结果作为 `data` 事件流。

客户端必须在以下假设下实现。

- 始终保持接收循环运行。
- 不要假设同步的请求-响应配对。

<br>
<h4 style="font-size:16px; font-weight:bold;">5. CONTROL 命令执行</h4>


根据策略/实现，<b>成功时 CONTROL 不提供单独的响应行。</b>

建议的策略：

- 通过 `错误 (error)` 或 `control_err` 事件检测故障。
- 使用以下方法验证成功：
  - 确认 MONITOR 结果中的变化
  - 使用专用状态查询 MONITOR 端点


<br>
<h4 style="font-size:16px; font-weight:bold;">6. 超时 / 看门狗</h4>

如果会话长时间保持空闲，服务器可能会终止连接。

客户端建议：

- 在连接后立即执行 `HANDSHAKE`
- 使用 `STOP(target=session)` 进行优雅关机
- 在流式传输期间防止接收循环停止
- 在 EOF 或套接字错误时准备重连和重新 HANDSHAKE 的逻辑

在当前服务器实现中，适用以下策略。

- <b>解除武装状态（空闲 / 没有活动 MONITOR）</b>  
  &rightarrow; 在大约 <b>180 秒</b> 没有有意义活动后会话被终止

- <b>武装状态（活动 MONITOR 流）</b>  
  &rightarrow; 如果流式传输中断超过大约 <b>5 秒</b>，会话被终止

* 以上时间值可能会根据服务器策略或操作环境而变化。

<br>
<h4 style="font-size:16px; font-weight:bold;">7. 推荐架构 </h4>

对于实际实现，建议以下结构。

- 分开发送（命令）和接收（事件）  
  &rightarrow; 发送：构建命令 + `sendall`  
  &rightarrow; 接收：NDJSON 行解析器 + 分发器

- 单一责任接收循环  
  &rightarrow; 按 `\n` 拆分行  
  &rightarrow; JSON 解析  
  &rightarrow; 基于 `类型 (type)` / `错误 (error)` 的事件路由
[__SOURCE](3-recipe/README.md)
# 3. Recipe Commands

A **Recipe** refers to an **NDJSON line sent from the client to the server** in Open Stream.  
Each line is transmitted in the following format.

<div style="max-width:fit-content;">

```json
// Request
{"cmd":"<COMMAND>","payload":{...}}\n
````</div>

The server returns ACKs, events, and errors in the same NDJSON line format.

<div style="max-width:fit-content;">

```json
// Response
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

每个消息字段的含义如下。

<h4 style="font-size:16px; font-weight:bold;">Request (Client → Server)</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| (

</div>

The server returns ACKs, events, and errors in the same NDJSON line format.

<div style="max-width:fit-content;">

```json
// Response
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

每个消息字段的含义如下。

<h4 style="font-size:16px; font-weight:bold;">Request (Client → Server)</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| )`cmd`| string | Yes | Command name ( ( | string | Yes | Command name ()`HANDSHAKE` (, )`MONITOR` (, )`CONTROL` (, )`STOP`) |
| () |
| )`payload`| object | Yes | Command parameter object (see each command document for schema details) |

1. [HANDSHAKE](./1-handshake.md): Protocol version negotiation (mandatory at session start)

2. [MONITOR](./2-monitor.md): Periodic REST GET execution + ( | object | Yes | Command parameter object (see each command document for schema details) |

1. [HANDSHAKE](./1-handshake.md): Protocol version negotiation (mandatory at session start)

2. [MONITOR](./2-monitor.md): Periodic REST GET execution + )`data`streaming

3. [CONTROL](./3-control.md): One-shot REST execution (**no response line on success**)

4. [STOP](./4-stop.md): Stop ( streaming

3. [CONTROL](./3-control.md): One-shot REST execution (**no response line on success**)

4. [STOP](./4-stop.md): Stop )`monitor` (, )`control`, or (, or )`session`</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response (Client <-- Server)</h4>

<h4 style="font-size:16px; font-weight:bold;">Success</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| (

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response (Client <-- Server)</h4>

<h4 style="font-size:16px; font-weight:bold;">Success</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| )`type`| string | Yes | Event type (e.g. ( | string | Yes | Event type (e.g. )`handshake_ack` (, )`monitor_ack` (, )`data` (, )`stop_ack`) | - For () |

- For )`HANDSHAKE`responses, the fields ( responses, the fields )`ok`(boolean) and ( (boolean) and )`version`(string) are additionally included.

</div>

<h4 style="font-size:16px; font-weight:bold;">Error</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| ( (string) are additionally included.

</div>

<h4 style="font-size:16px; font-weight:bold;">Error</h4>

<div style="max-width:fit-content;">

| Key | Type | Required | Description |
| --- | ---- | -------: | ----------- |
| )`error`| string | Yes | Error code (machine-readable) |
| ( | string | Yes | Error code (machine-readable) |
| )`message`| string | Yes | Error description (human-readable) |
| ( | string | Yes | Error description (human-readable) |
| )`hint` | string | No | Guidance or example for resolution |

</div>
[__SOURCE](3-recipe/1-handshake.md)
## 3.1 握手

这是在会话开始后立即执行的 **协议版本协商** 步骤。  
如果在 `握手` 之前调用 `监控` 或 `控制`，服务器可能会拒绝请求。

<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

</div>

<div style="max-width:fit-content;">

| Payload 字段 | 必需 | 类型 | 规则 |
| ------- | -------- | ---- | ----- |
| `major` | 是 | int | 大于或等于 0 的整数 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
```

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| `ok` | boolean | 否 | 一些 ACK 的明确成功标志（例如 `handshake_ack`） |
| `version` | string | 否 | 服务器协议版本 (`MAJOR.MINOR.PATCH`) |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">错误代码</h4>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时 |
| ---------- | ----------- | ----------- | -------------- |
| `busy_session_active` | 409 | 已存在一个活动任务 | 在 CONTROL 或 MONITOR 任务运行时请求 HANDSHAKE |
| `version_mismatch` | 400 | 协议 MAJOR 版本不匹配 | 客户端 `major` 与服务器 MAJOR 不匹配 |
| `missing_major` | 400 | 缺少必需字段 | `major` 键在有效载荷中缺失 |
| `invalid_major_type` | 400 | 类型无效 | `major` 不是数字（int） |
| `invalid_version` | 400 | 值范围无效 | `major` 为负数 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效载荷验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ---- | --------- | ---- | --------------- | ---------- |
| `major` | 必需 | int | 必须存在于有效载荷中 | `missing_major` |
| `major` | 类型 | int | 必须是一个数字 | `invalid_major_type` |
| `major` | 范围 | int | 整数 ≥ 0 | `invalid_version` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

- 服务器仅验证 **MAJOR 版本**。
- MINOR / PATCH 更改不会破坏与现有客户端的兼容性。
- 有关版本策略的详细信息，请参阅 [发布说明](../7-release-notes/README.md)。
[__SOURCE](3-recipe/2-monitor.md)
## 3.2 监视器

此命令定期调用客户端指定的 REST **GET** 服务  
并将结果作为单行 NDJSON 消息流式传输。

- 在当前实现中, **每个会话只能维护一个监视器**。
- 当收到新的 `MONITOR` 命令时, 现有的监视会话会自动终止并被替换。
- `MONITOR` 只能在 **成功的握手后使用**。<br>
  &rightarrow; 如果在握手之前调用，将返回 `handshake_required` 错误。

<br>
<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"MONITOR","payload":{"method":"GET","period_ms":2,"url":"/project/robot/joints/joint_states","args":{"jno_start":1,"jno_n":6}}}\n
````</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| (

</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| )`url`| 是 | 字符串 | 必须以 ( | 是 | 字符串 | 必须以 )`/` 开头，无空格，最大长度 2048 |
| (, 无空格，最大长度 2048 |
| )`method`| 是 | 字符串 | 仅 ( | 是 | 字符串 | 仅允许 )`"GET"` |
| ( 被允许 |
| )`period_ms`| 是 | int | 2 ~ 30000 (ms)，超出范围的值会被限制 |
| ( | 是 | int | 2 ~ 30000 (ms)，超出范围的值会被限制 |
| )`args`| 否 | 对象 | 查询参数的对象（仅限 JSON 对象） |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* ( | 否 | 对象 | 查询参数的对象（仅限 JSON 对象） |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* )`monitor_ack`表示 MONITOR 请求已被接受。
* ( 的到达顺序表示 MONITOR 请求已被接受。
* )`monitor_ack` 和第一个 ( 以及第一个 )`data`事件的到达顺序 **不能保证**。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>流式传输</i></u></b>)</h4>

当 MONITOR 处于活动状态时，服务器会重复调用 REST API (GET)  
在指定的间隔 ()`period_ms`) 并将结果作为 )`data`事件发送。

<div style="max-width:fit-content;">

```json
{"type":"data","ts":402,"svc_dur_ms":2.960000,"result":{"_type":"JObject","position":[0.0,90.0,0.0,0.0,-90.0,0.0],"effort":[-0.0,98.923641,94.599385,-0.110933,-5.895076,0.0],"velocity":[-0.0,-0.0,0.0,0.0,-0.0,0.0]}}\n
```

</div>

<div style="max-width:fit-content;">

| 响应字段 | 类型 | 描述 |
| -------------- | ---- | ----------- |
| ( 事件。

<div style="max-width:fit-content;">

```json
{"type":"data","ts":402,"svc_dur_ms":2.960000,"result":{"_type":"JObject","position":[0.0,90.0,0.0,0.0,-90.0,0.0],"effort":[-0.0,98.923641,94.599385,-0.110933,-5.895076,0.0],"velocity":[-0.0,-0.0,0.0,0.0,-0.0,0.0]}}\n
```

</div>

<div style="max-width:fit-content;">

| 响应字段 | 类型 | 描述 |
| -------------- | ---- | ----------- |
| )`type`| 字符串 | 事件类型 ( | 字符串 | 事件类型 ()`data`) |
| () |
| )`ts`| 数字 | 服务器端时间戳 (ms) |
| ( | 数字 | 服务器端时间戳 (ms) |
| )`svc_dur_ms`| 数字 | REST 调用和处理耗时 (ms) |
| ( | 数字 | REST 调用和处理耗时 (ms) |
| )`result`| 任何 | REST 响应主体（如果存在） |
| ( | 任何 | REST 响应主体（如果存在） |
| )`status`| 数字 | 当 REST 主体为空时返回的 HTTP 状态码 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的 NDJSON 错误架构。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">错误代码</h4>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 出现时间 |
| ---------- | ----------- | ----------- | -------------- |
| ( | 数字 | 当 REST 主体为空时返回的 HTTP 状态码 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的 NDJSON 错误架构。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">错误代码</h4>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 出现时间 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | 未执行握手 | MONITOR 在握手之前调用 |
| ( | 412 | 未执行握手 | MONITOR 在握手之前调用 |
| )`missing_url`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`url` 键丢失 |
| ( 键丢失 |
| )`invalid_url`| 400 | 无效的 URL 格式 | 不以 ( | 400 | 无效的 URL 格式 | 不以 )`/` 开头或包含空格 |
| ( 或包含空格 |
| )`url_too_long`| 400 | URL 太长 | URL 长度超过 2048 |
| ( | 400 | URL 太长 | URL 长度超过 2048 |
| )`missing_method`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`method` 键丢失 |
| ( 键丢失 |
| )`invalid_method`| 400 | 无效的方法 | 不是 ( | 400 | 无效的方法 | 不是 )`"GET"` |
| ( |
| )`missing_period_ms`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`period_ms` 键丢失 |
| ( 键丢失 |
| )`invalid_period`| 400 | 无效类型 | ( | 400 | 无效类型 | )`period_ms` 不是整数 |
| ( 不是整数 |
| )`invalid_args`| 400 | 无效类型 | ( | 400 | 无效类型 | )`args` 不是对象 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| ( 不是对象 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| )`url`| 必填 | 字符串 | 必须在有效负载中存在 | ( | 必填 | 字符串 | 必须在有效负载中存在 | )`missing_url` |
| ( |
| )`url`| 格式 | 字符串 | 必须以 ( | 格式 | 字符串 | 必须以 )`/` 开头，无空格 | (, 无空格 | )`invalid_url` |
| ( |
| )`url`| 长度 | 字符串 | 最大 2048 | ( | 长度 | 字符串 | 最大 2048 | )`url_too_long` |
| ( |
| )`method`| 必填 | 字符串 | 必须是 ( | 必填 | 字符串 | 必须是 )`"GET"`| ( | )`missing_method` (, )`invalid_method` |
| ( |
| )`period_ms`| 必填 | int | 必须是整数 | ( | 必填 | int | 必须是整数 | )`missing_period_ms` (, )`invalid_period` |
| ( |
| )`period_ms`| 范围 | int | 2~30000, 超出范围时限制 | - |
| ( | 范围 | int | 2~30000, 超出范围时限制 | - |
| )`args`| 类型 | 对象 | 仅限 JSON 对象 | ( | 类型 | 对象 | 仅限 JSON 对象 | )`invalid_args` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗行为</h4>

* 当 MONITOR 被激活时，看门狗将过渡到 **ARM 状态**。
* 在此状态下，会议空闲超时从 **180 秒减少到 5 秒**。
* 如果在监视过程中 TCP 连接丢失，或  
  如果在一定时间内未从客户端接收到任何有效指令，  
  看门狗会检测到这一点并自动清理会话。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* MONITOR 是一种服务器驱动的流式传输机制。
* ( |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗行为</h4>

* 当 MONITOR 被激活时，看门狗将过渡到 **ARM 状态**。
* 在此状态下，会议空闲超时从 **180 秒减少到 5 秒**。
* 如果在监视过程中 TCP 连接丢失，或  
  如果在一定时间内未从客户端接收到任何有效指令，  
  看门狗会检测到这一点并自动清理会话。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* MONITOR 是一种服务器驱动的流式传输机制。
* )`data` 事件可能随时到达，无论是否 ( 事件可能随时到达，无论是否 )`monitor_ack` 已被接收。
* 客户端必须始终保持接收循环运行，并根据 ( 已被接收。
* 客户端必须始终保持接收循环运行，并根据 )`type` 字段处理事件。
[__SOURCE](3-recipe/3-control.md)
## 3.3 控制

控制是客户端用于控制机器人或更新内部控制器数据的命令。  
在内部，它调用<b>POST / PUT / DELETE基础的 ${cont_model} OpenAPI</b>，即使在流环境中，  
也应用与现有 OpenAPI 相同的<b>REST 路径和验证逻辑</b>。

- 控制只能在**成功的握手后**使用。<br>
  &rightarrow; 如果在握手之前调用，它将立即以`handshake_required`错误被拒绝。
- 控制是<b>一次性命令</b>，并且<b style="color:#ec1249;">成功时不发送响应 NDJSON 行。</b>
- 控制即使在监视器激活时也可以执行。

<br>
<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/project/robot/trajectory/joint_traject_insert_point","args":{},"body":{"interval":0.005,"time_from_start":-1,"look_ahead_time":0.004,"point":[1.014532178568314,91.01453217856832,1.014532178568314,1.014532178568314,1.014532178568314,0.013294178568314]}}}\n
````</div>

<div style="max-width:fit-content;">

| 有效负载字段 | 必需 | 类型 | 规则 |
| ------------- | -------- | ---- | ----- |
| (
</div>

<div style="max-width:fit-content;">

| 有效负载字段 | 必需 | 类型 | 规则 |
| ------------- | -------- | ---- | ----- |
| )`url`| 是 | 字符串 | 必须以( | 是 | 字符串 | 必须以) `/`开头，且没有空格 |
| (, 没有空格 |
| )`method`| 是 | 字符串 | 其中之一( | 是 | 字符串 | 其中之一) `POST`（,）`PUT`（,）`DELETE`|
| ( |
| )`args`| 否 | 对象 | REST 查询参数的对象 |
| ( | 否 | 对象 | REST 查询参数的对象 |
| )`body`| 否 | 对象 \\| 数组 | REST 请求主体 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>无响应行</i></u></b>)</h4>

如果控制命令成功处理，  
<b>服务器不会发送响应 NDJSON 行。</b>  
客户端必须实现命令而不期待返回值。

* 此行为是 Stream 协议的设计。
* 控制成功应通过<b>状态变化或监视器结果</b>来验证，而不是通过接收 ACK。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

如果发生错误，服务器将发送( | 否 | 对象 \\| 数组 | REST 请求主体 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>无响应行</i></u></b>)</h4>

如果控制命令成功处理，  
<b>服务器不会发送响应 NDJSON 行。</b>  
客户端必须实现命令而不期待返回值。

* 此行为是 Stream 协议的设计。
* 控制成功应通过<b>状态变化或监视器结果</b>来验证，而不是通过接收 ACK。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

如果发生错误，服务器将发送 )`control_err`事件到当前会话。

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生的条件 |
| ---------- | ----------- | ----------- | -------------- |
| ( 事件到当前会话。

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生的条件 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | 未执行握手 | 控制在握手之前调用 |
| ( | 412 | 未执行握手 | 控制在握手之前调用 |
| )`missing_url`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`url`键缺失 |
| ( 键缺失 |
| )`invalid_url`| 400 | 无效的 URL 格式 | 不以( | 400 | 无效的 URL 格式 | 不以) `/`开头或包含空格 |
| ( 或包含空格 |
| )`missing_method`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`method`键缺失 |
| ( 键缺失 |
| )`invalid_method`| 400 | 无效的方法 | 不是( | 400 | 无效的方法 | 不是) `POST/PUT/DELETE`|
| ( |
| )`invalid_args`| 400 | 类型无效 | ( | 400 | 类型无效 | )`args`不是对象 |
| ( 不是对象 |
| )`invalid_body`| 400 | 类型无效 | ( | 400 | 类型无效 | )`body`不是对象或数组 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| ( 不是对象或数组 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| )`url`| 必需 | 字符串 | 必须存在于有效负载中 | ( | 必需 | 字符串 | 必须存在于有效负载中 | )`missing_url`|
| ( |
| )`url`| 格式 | 字符串 | 必须以( | 格式 | 字符串 | 必须以) `/`开头，且没有空格 | (, 没有空格 | )`invalid_url`|
| ( |
| )`method`| 必需 | 字符串 | 其中之一( | 必需 | 字符串 | 其中之一) `POST/PUT/DELETE`| ( | )`missing_method` (, )`invalid_method`|
| ( |
| )`args`| 类型 | 对象 | 仅限 JSON 对象 | ( | 类型 | 对象 | 仅限 JSON 对象 | )`invalid_args`|
| ( |
| )`body`| 类型 | 对象 \\| 数组 | 仅限对象或数组 | ( | 类型 | 对象 \\| 数组 | 仅限对象或数组 | )`invalid_body` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗交互</h4>

- 当成功执行控制命令时，看门狗更新其监视的最后活动时间戳。
[__SOURCE](3-recipe/4-stop.md)
## 3.4 停止

STOP 是一个用于中断当前会话中正在进行的操作的命令，  
或明确通知服务器终止会话的意图。

- STOP **只能在成功的握手之后使用**。
- 根据 `目标 (target)` 值，它停止 `monitor`、`control` 或 `session` 之一。
- `target=session` 用于明确表示优雅关闭的意图，  
  之后建议客户端关闭 TCP 连接。

<br>
<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"STOP","payload":{"target":"session"}}\n
````</div>
<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| (

</div>
<div style="max-width:fit-content;">

| Payload Field | Required | Type | Rules |
| ------------ | -------- | ---- | ----- |
| )`target`| 是 | string | 必须是 ( | 是 | string | 必须是 )`"session"` (, )`"control"` (, )`"monitor"`|

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* ( 的值 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* )`stop_ack.target`的值与请求的 ( 的值相同，  
* 表示 STOP 请求已成功接受。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的 NDJSON 错误模式。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| ( 值。
* 表示 STOP 请求已成功接受。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的 NDJSON 错误模式。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | 未执行握手 | 在握手之前调用 STOP |
| ( | 412 | 未执行握手 | 在握手之前调用 STOP |
| )`missing_target`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`target`键丢失 |
| ( 键丢失 |
| )`invalid_target`| 400 | 无效的目标值 | 不支持的 ( | 400 | 无效的目标值 | 不支持的 )`target`值 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| ( 值 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| )`target`| 必填 | string | 必须存在于有效负载中 | ( | 必填 | string | 必须存在于有效负载中 | )`missing_target`|
| ( |
| )`target`| 值 | string | 必须是 ( | 值 | string | 必须是 )`"session"` (, )`"control"` (, )`"monitor"`| ( | )`invalid_target`|

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">行为注意事项</h4>

* ( |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">行为注意事项</h4>

* )`target=monitor`* 停止活动的 MONITOR 流。
* (
  * 停止活动的 MONITOR 流。
* )`target=control`* 清理 CONTROL 执行状态。
* (
  * 清理 CONTROL 执行状态。
* )`target=session`* 明确通知服务器会话终止意图。
  * 在接收到 (
  * 明确通知服务器会话终止意图。
  * 在收到 )`stop_ack`后关闭 TCP 连接是推荐的。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* STOP 旨在安全释放服务器资源。
* 使用 ( 是推荐的。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* STOP 旨在安全释放服务器资源。
* 使用 )`target=session` 强烈推荐用于优雅关闭的场景。
[__SOURCE](4-error/README.md)
# 4. 错误代码

本文档描述了 Open Stream 服务器返回的 **错误代码** 及其含义。

错误通常以 **单行 NDJSON 消息** 的以下格式发送。

<div style="max-width: fit-content;">

```json
{"error":"<error_code>","message":"...","hint":"..."}
```

| 字段     | 描述               |
| -------- | ------------------ |
| error    | 机器可读错误代码   |
| message  | 人可读简短描述     |
| hint     | 可选字段。故障排除的附加提示 |

- （注意）并非所有错误都包含 `hint` 字段。

</div>

<br>

<div style="max-width: fit-content;">

<h4 style="font-size:15px; font-weight:bold;">1. 协议 / 会话错误</h4>

在协议解析、会话状态处理或初始化程序违反过程期间发生的错误。

| 错误代码               | 描述                     | 典型原因                              | 客户端操作                                  |
| ---------------------- | ------------------------ | ------------------------------------- | ------------------------------------------- |
| invalid_ndjson         | NDJSON 解析失败         | JSON 损坏，缺少换行符 (`\n`)         | 遵循每行一个 JSON + 换行规则                |
| rx_buf_overflow        | 接收缓冲区溢出         | 消息过大或突发过多                   | 减少消息大小，限制发送速率                  |
| handshake_required     | 未执行握手             | 初始握手被省略                       | 在连接后立即执行握手                        |
| version_mismatch       | 协议版本不匹配         | MAJOR 版本不匹配                     | 匹配服务器 MAJOR 版本                       |
| busy_session_active    | 会话已经在使用中       | MONITOR/CONTROL 处于活动状态        | 在 STOP 后重试                             |
| session_timeout        | 会话空闲超时           | 看门狗超时                           | 维护周期性活动或重新连接                    |

<br>

<h4 style="font-size:15px; font-weight:bold;">2. 命令 / 有效负载验证错误</h4>

在请求消息结构或字段验证期间发生的错误。

| 错误代码         | 描述                     | 典型原因                  | 客户端操作                   |
| ---------------- | ------------------------ | ------------------------ | --------------------------- |
| invalid_cmd      | 不支持的命令            | 打字错误或不支持的命令  | 验证 `cmd` 值               |
| invalid_payload  | 无效的有效负载格式      | 不是对象                  | 将有效负载更改为对象       |
| missing_field    | 缺少必需字段            | 缺少 `url`、`method` 等   | 添加必需字段               |
| invalid_type     | 无效的字段类型          | 数字 ↔ 字符串混淆        | 修正字段类型               |
| invalid_value    | 无效的值                | 超出枚举范围              | 使用允许的值               |

<br>

<h4 style="font-size:15px; font-weight:bold;">3. HANDSHAKE 错误</h4>

在 HANDSHAKE 处理期间发生的错误。

| 错误代码              | 描述                          | 典型原因                         | 客户端操作                   |
| --------------------- | ----------------------------- | -------------------------------- | --------------------------- |
| version_mismatch      | 协议 MAJOR 不匹配             | 客户端/服务器 MAJOR 不同          | 使用服务器 MAJOR 版本      |
| handshake_rejected    | HANDSHAKE 被拒绝              | 无效的会话状态                   | 关闭现有会话，重试          |

<br>

<h4 style="font-size:15px; font-weight:bold;">4. MONITOR 错误</h4>

在 MONITOR 配置或执行期间发生的错误。  
这些主要在周期性 REST 调用验证期间出现。

| 错误代码                   | 描述                          | 典型原因                          | 客户端操作                    |
| -------------------------- | ----------------------------- | --------------------------------- | ---------------------------- |
| invalid_method             | MONITOR 中使用了非 GET 方法    | 使用了 POST/PUT                   | 将方法更改为 GET             |
| invalid_url                | 无效的 URL 格式               | 未以 ` (/)` 开头，有空格         | 遵循 URL 规则                |
| invalid_period             | 无效的 `period_ms` 范围      | 太小或太大                        | 调整为允许的范围             |
| monitor_already_active     | 重复的 MONITOR 请求            | 已处于活动状态                    | STOP 然后重试                |
| monitor_internal_error     | 内部 REST 调用失败           | 内部服务器错误                    | 检查服务器日志               |

<br>

<h4 style="font-size:15px; font-weight:bold;">5. CONTROL 错误</h4>

在 CONTROL 请求处理期间发生的错误。  
它们可能会根据 REST 执行结果被报告。

| 错误代码              | 描述                         | 典型原因               | 客户端操作                   |
| --------------------- | ---------------------------- | --------------------- | --------------------------- |
| control_err           | CONTROL 执行失败            | REST 4xx/5xx         | 检查状态/主体              |
| invalid_body          | 无效的主体 JSON             | 序列化错误           | 验证主体结构               |
| method_not_allowed    | 不允许的方法                 | 使用 GET 等          | 使用 POST/PUT/DELETE        |
| control_busy          | 控制不可用状态               | 另一个控制活动        | 稍后重试                   |

{% hint style="warning" %}

CONTROL 不会在成功时返回响应。  
只有在失败时可能会传递 `control_err` 或通用错误消息。

{% endhint %}

<br>

<h4 style="font-size:15px; font-weight:bold;">6. STOP 错误</h4>

在 STOP 请求处理期间发生的错误。

| 错误代码           | 描述                      | 典型原因             | 客户端操作                                   |
| ------------------ | ------------------------- | ------------------- | --------------------------------------------- |
| invalid_target     | 无效的 STOP 目标        | 目标拼写错误       | 选择 monitor / control / session             |
| nothing_to_stop    | 没有什么可停止的        | 已经终止            | 可以忽略                                      |
| stop_failed        | 内部清理失败            | 内部状态错误       | 推荐重新连接                                   |

<br>

<h4 style="font-size:15px; font-weight:bold;">7. 错误处理指南</h4>

错误消息始终以单行 NDJSON 接收。

建议客户端：
- 首先检查接收循环中 `错误 (error)` 字段的存在，并在发生错误时明确清理会话状态（STOP 或重新连接）。

- 一些错误是可恢复的，而其他错误可能需要重新连接（致命）。

- 根据每个错误的 "客户端操作" 列确定可恢复性。

</div>
[__SOURCE](5-examples/README.md)
# 5. 示例

{% hint style="info" %}

本部分提供逐步示例，以帮助首次使用 Open Stream 的用户理解  
<b>如何设计客户端架构</b>。  
每个示例专注于 <b>理解结构和控制流</b> 而不是提供完全优化或准备投入生产的代码。

{% endhint %}

<h4 style="font-size:16px; font-weight:bold;">手动示例部分结构</h4>

<div style="max-width:fit-content;">

```text
5. 示例
├── 5.1 utils       # 常用工具（发送/接收、解析、事件分发）
├── 5.2 handshake   # 独立的 HANDSHAKE 示例
├── 5.3 monitor     # MONITOR 流媒体示例
├── 5.4 control     # CONTROL 一次性请求示例
└── 5.5 stop        # STOP 和优雅关闭示例
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">客户端目录结构</h4>

以下是使用 Open Stream 的客户端应用程序推荐的最小目录结构。

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py            # TCP 套接字连接和发送/接收
│   ├── parser.py         # NDJSON 流解析
│   ├── dispatcher.py     # 基于类型/错误的事件分发
│   ├── motion.py         # 生成正弦波运动
│   └── api.py            # HANDSHAKE / MONITOR / CONTROL / STOP 的包装器
│
├── scenarios/
│   ├── handshake.py      # 独立的 HANDSHAKE 场景
│   ├── monitor.py        # MONITOR 流媒体场景
│   ├── control.py        # CONTROL 一次性请求场景
│   └── stop.py           # STOP 和优雅关闭场景
│
└── main.py               # 客户端入口点
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">执行环境</h4>

<div style="max-width:fit-content;">

| 项目 | 描述 |
| ---- | ----------- |
| 语言 | Python 3.8.0 |
| 操作系统 | Linux / macOS / Windows（任何支持 TCP 套接字的环境） |
| 库 | 仅标准库 |

</div>

- 这些示例故意最小化外部依赖  
  以专注于理解 Open Stream 协议本身。
[__SOURCE](5-examples/1-utils.md)
## 5.1 Common Utilities (utils)

{% hint style="info" %}

本文档提供了<b>Open Stream客户端工具代码</b>  
该代码通常用于后续所有示例。

下面的代码是<b>完全面能的可运行代码</b>，而不仅仅是示例样本。  
您可以将其直接复制到自己的项目中并按原样使用。

为了清晰和可重复性，这个示例故意使用了  
<b>"接收线程 + 阻塞套接字（带超时）"</b>模型。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

创建如下所示的`utils/`目录  
并精确复制每个文件。

<div style="max-width: fit-content;">

```text
OpenStreamClient/
└── utils/
    ├── net.py
    ├── parser.py
    ├── dispatcher.py
    ├── motion.py
    └── api.py
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">工具角色</h4>

| 文件 | 角色 | 主要职责 |
| ---- | ---- | --------------------- |
| <b>net.py</b> | TCP网络层 | TCP套接字连接/断开，接收循环（线程），原始字节接收 |
| <b>parser.py</b> | NDJSON解析器 | NDJSON流解析，JSON对象创建 |
| <b>dispatcher.py</b> | 消息调度器 | 基于消息`类型 (type)` / `错误 (error)`的回调调度 |
| <b>motion.py</b> | 轨迹工具 | 正弦轨迹生成，文件保存/加载 |
| <b>api.py</b> | Open Stream API封装 | HANDSHAKE / MONITOR / CONTROL / STOP的抽象 |

</div>

<br>
<div style="max-width:fit-content;">

---

<h4 style="font-size:16px; font-weight:bold;">utils/net.py</h4>

该模块实现了负责TCP套接字连接和I/O的网络层。

<b>职责</b>  
(1) 创建、维护并关闭与Open Stream服务器的TCP连接。  
(2) 在接收线程中读取来自服务器的原始字节流，并通过回调（`on_bytes`）转发它们。  
(3) 将更高层（解析器/调度器）与直接网络I/O处理解耦。

<b>关键设计点</b>  
(1) `TCP_NODELAY`（Nagle OFF）：减少小NDJSON行的延迟。  
(2) `SO_KEEPALIVE`：帮助检测半开放连接。  
(3) 基于超时的接收循环：确保在关闭或中断期间的响应能力。

<b>主要API</b>  
(1) `connect()`：建立套接字连接并配置选项  
(2) `send_line(line)`：发送一行NDJSON（换行符自动追加）  
(3) `start_recv_loop(on_bytes)`：启动接收线程  
(4) `close()`：关闭连接

<details><summary>点击查看python代码</summary>

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

        # Nagle OFF (低延迟)
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
        print(f"[net] 已连接到 {self.host}:{self.port}")

    def close(self) -> None:
        self._running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        print("[net] 连接已关闭")

    def send_line(self, line: str) -> None:
        if not self.sock:
            raise RuntimeError("套接字未连接")
        self.sock.sendall((line + "\n").encode("utf-8"))
        print(f"[tx] {line}")

    def start_recv_loop(self, on_bytes: Callable[[bytes], None]) -> None:
        if not self.sock:
            raise RuntimeError("套接字未连接")

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

该解析器将NDJSON（换行分隔的JSON）流转换为  
<b>基于行的JSON对象</b>。

- <b>输入</b>: 字节块。 TCP不会保留消息边界，因此一条消息可能会跨块分裂，或者多个消息可能会合并。
- <b>输出</b>: 传递给`on_message(dict)`回调的完整JSON字典。
- <b>行为</b><br>
  (1) 在内部缓冲区中累积数据并按`\n`分割。  
  (2) 将每一行解码为UTF-8，并通过`json.loads()`解析。  
  (3) 在JSON解析失败时，记录错误并跳过该行。

该模块标准化了"原始字节"和"解析消息"之间的边界。

<details><summary>点击查看python代码</summary>

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
                print(f"[parser] json解码错误: {e}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/dispatcher.py</h4>

该调度器根据<b>`类型 (type)` / `错误 (error)`</b>将解析消息（dict）路由到注册的回调。

- <b>职责</b>  
  (1) 将消息处理逻辑与网络/解析层分开。  
  (2) 示例脚本（握手/监控/控制）只需要向调度器注册处理程序。

- <b>调度规则（当前实现）</b>  
  (1) 如果`内容 (msg)`包含键`"error"`，则调用`on_error(msg)`（如果未注册则打印）。  
  (2) 否则，使用`msg.get("type")`调度到相应的`on_type[type]`回调。  
  (3) 如果没有匹配的回调存在，默认情况下打印事件。

- <b>扩展点</b>  
  项目可以通过扩展`dispatch()`内部的基于键的调度逻辑，明确分离`ack` / `event`处理。

<details><summary>点击查看python代码</summary>

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
                print(f"[错误] {msg}")
            return

        msg_type = msg.get("type")
        if msg_type and msg_type in self.on_type:
            self.on_type[msg_type](msg)
        else:
            print(f"[事件] {msg}")
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">utils/motion.py</h4>

`motion.py`提供了**关节轨迹生成和重用工具**  
在CONTROL示例中使用。

其主要目的是通过  
<b>将轨迹生成逻辑与通信逻辑分离</b>来保持CONTROL示例的专注。

- CONTROL传输已经涉及复杂的时序和方案处理。
- 将轨迹生成混合到同一示例中会使其过长。
- 因此，轨迹在`motion.py`中生成，而CONTROL示例专注于  
  “以固定间隔发送生成的点”。

角色1. **轨迹生成（正弦波）**
- `generate_sine_trajectory(base_deg, cycle_sec, amplitude_deg, dt_sec, total_sec, active_joint_count)`
- 仅对前N个关节应用正弦位移，以产生振荡运动。
- 返回`List[List[float]]`的**基于度数的点**。

角色2. **轨迹保存/加载**
- `save_trajectory(points_deg, dt_sec, base_dir="data") -> saved_path`
- `load_trajectory(path) -> (dt_sec, points_deg)`
- JSON格式：  
  → `dt_sec`：点之间的时间间隔（秒）  
  → `points_deg`：关节角度点的列表

使用位置
- 在`control.md`场景中：
  - 读取基准姿态（弧度）→通过`rad_to_deg()`转换
  - 使用`generate_sine_trajectory()`生成点
  - 可选地通过`save_trajectory()` / `load_trajectory()`保存和重用轨迹

备注
- CONTROL `joint_traject_insert_point`假定`point`值为**度**（示例标准）。
- `dt_sec`直接影响传输时序和`interval/time_from_start`设置，保存/加载时必须保留。

<details><summary>点击查看python代码</summary>

```python
# utils/motion.py
import json
import math
import os
import time
from typing import List, Tuple, Optional


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

该模块是一个薄包装器，<b>一致地构建JSON消息</b>  
用于Open Stream协议。

- <b>职责</b>  
  (1) 防止示例脚本重复编写原始JSON模式。  
  (2) 针对`cmd`（HANDSHAKE / MONITOR / CONTROL / STOP）标准化负载结构。

- <b>重要说明</b>  
  (1) `api.py`不直接发送网络数据；它通过`net.send_line()`发送NDJSON行。  
  (2) CONTROL是一个一流的协议命令；`joint_traject_*`辅助工具是轨迹控制的从属工具。

协议命令概述

| cmd | 描述 |
| --- | ----------- |
| HANDSHAKE | 会话初始化和版本协商 |
| MONITOR | 周期性状态 / HTTP API轮询 |
| CONTROL | 机器人控制（轨迹等） |
| STOP | 停止会话或流 |

提供的方法

| API方法 | cmd | 描述 |
| ---------- | --- | ----------- |
| `handshake(major)` | HANDSHAKE | 初始化Open Stream会话 |
| `monitor(url, period_ms, args=None, monitor_id=1)` | MONITOR | 定期轮询目标URL |
| `monitor_stop()` | MONITOR | 停止MONITOR |
| `joint_traject_init()` | CONTROL | 初始化关节轨迹控制 |
| `joint_traject_insert_point(body)` | CONTROL | 发送一个轨迹点 |
| `stop(target)` | STOP | 停止会话或控制/监控 |
<details><summary>点击以查看python代码</summary>

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
    # 握手
    # -------------------------

    def handshake(self, major: int = 1) -> None:
        self._send({
            "cmd": "HANDSHAKE",
            "payload": {
                "major": major
            },
        })

    # -------------------------
    # 监控
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
    # 停止
    # -------------------------

    def stop(self, target: str = "session") -> None:
        self._send({
            "cmd": "STOP",
            "payload": {
                "target": target
            },
        })

    # -------------------------
    # 控制（关节轨迹）
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

<br>
<h4 style="font-size:16px; font-weight:bold;">关于main.py</h4>

虽然不是<code>utils/</code>包的一部分，<code>main.py</code>在所有示例场景中扮演着重要角色  
作为<b>执行入口点</b>。

<code>main.py</code>负责：
<ul>
  <li>解析命令行参数（场景类型、主机、端口等）</li>
  <li>选择并调用适当的场景模块</li>
  <li>为所有示例提供统一的执行接口</li>
</ul>

这种分离是故意的：
<ul>
  <li><code>utils/</code>包含<b>可重用、不依赖场景的构建模块</b></li>
  <li><code>scenarios/*.py</code>包含<b>逐步的协议流程</b></li>
  <li><code>main.py</code>只是协调执行，并不实现协议逻辑</li>
</ul>

以下部分中的每个示例假定通过<code>main.py</code>执行。

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py（场景启动器）</h4>

<code>main.py</code>提供了一个统一的入口点，通过命令行参数运行每个示例场景。
它解析常见选项（主机/端口/主要等），并分发到<code>scenarios/</code>下的相应模块。

<details><summary>点击以查看python代码</summary>

```python
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
    # 监控选项
    # -------------------------
    p.add_argument("--url", default="/api/health")
    p.add_argument("--period-ms", type=int, default=1000)

    # -------------------------
    # 控制选项
    # -------------------------
    p.add_argument("--http-port", type=int, default=8888)
    p.add_argument("--dt-sec", type=float, default=0.02)
    p.add_argument("--total-duration-sec", type=float, default=1.0)
    p.add_argument("--cycle-sec", type=float, default=5.0)
    p.add_argument("--amplitude-deg", type=float, default=1.0)
    p.add_argument("--active-joint-count", type=int, default=6)
    p.add_argument("--look-ahead-time", type=float, default=0.04)

    p.add_argument("--target", \
                   choices=["session", "control", "monitor"], \
                   default="session", \
                   help="停止目标（session | control | monitor）")


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

</details>

<h4 style="font-size:16px; font-weight:bold;">总结</h4>

* 上面的`utils`代码在所有后续示例中<b>保持不变地重用</b>。
* 它正确运行，<b>只需复制和粘贴</b>，无需修改。
* 从下一个文档开始，将使用这些工具逐步解释  
  <b>握手 → 监控 → 控制 → 停止</b>的场景。
[__SOURCE](5-examples/2-handshake.md)
## 5.2 HANDSHAKE 示例

此示例演示了开始 Open Stream 会话所需的最基本流程。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接
2. 启动 NDJSON 接收循环（解析器 + 派发器连接）
3. 发送 HANDSHAKE
4. 确认收到 `handshake_ack`
5. 关闭连接

<br>
<h4 style="font-size:16px; font-weight:bold;">前提条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / api.py)
- 服务器地址和端口 (`49000`)

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，以下文件必须存在于您的项目中。

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
│   └── handshake.py      # 文档中提供的场景代码
│
└── main.py               # 场景启动器（入口点）
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

    # 注册事件处理程序
    dispatcher.on_type["handshake_ack"] = lambda m: print(
        f"[ack] handshake_ack ok={m.get('ok')} version={m.get('version')}"
    )
    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 发送 HANDSHAKE
    api.handshake(major=major)

    # 简要等待 ACK，然后关闭
    time.sleep(0.5)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; 这是一个可执行的场景，它发送一个 HANDSHAKE 请求并验证收到 `handshake_ack`。
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py</h4>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake

def main() -> None:
    p = argparse.ArgumentParser(description="Open Stream 示例")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # 通用选项
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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

从项目根目录运行以下命令。

<div style="max-width:fit-content;">

```bash
$ python3 main.py handshake --host 192.168.1.150 --port 49000 --major 1
```
</div>

<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

```text
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] connection closed
```

- 注意：如果发生错误，将以以下形式接收  
  `{ "error": "...", "message": "...", "hint": "..." }`.
[__SOURCE](5-examples/3-monitor.md)
## 5.3 MONITOR 示例

此示例演示了在 Open Stream 会话中启动 **MONITOR 流** 的基本流程，以及处理周期性接收的数据。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接  
2. 启动 NDJSON 接收循环（解析器 + 派发器连接）  
3. 发送 MONITOR（方法 / URL / period_ms / 参数）  
4. 确认收到 `monitor_ack`（或服务器定义的 ACK 类型）  
5. 处理流式 `monitor_data`  
6. 退出示例（关闭连接）

* 在实际操作中，建议在终止流时发送 `STOP target=monitor`  
（这在 STOP 示例中有所涵盖）。

<br>
<h4 style="font-size:16px; font-weight:bold;">前提条件</h4>

* `utils/` 目录（net.py / parser.py / motion.py / dispatcher.py / api.py）  
* 服务器地址和端口（`49000`）  
* MONITOR 的目标 REST URL、`period_ms` 和 `args`

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，以下文件必须存在于您的项目中。

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
│   └── monitor.py        # 本文档提供的场景代码
│
└── main.py               # 场景启动器（入口点）
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

    # --- 同步事件（等待 ACK） ---
    handshake_ok = threading.Event()

    # 注册事件处理程序
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # MONITOR ACK / 数据（类型名称可能因服务器实现而异）
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) 握手
    api.handshake(major=major)

    # 2) 等待 handshake_ack（超时可调）
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack 超时；将不发送 MONITOR。")
        net.close()
        return

    # 3) 发送 MONITOR
    api.monitor(url=url, period_ms=period_ms, args={})

    # 等待一段时间以接收流，然后退出
    # （为了优雅关机，发送 STOP target=monitor，如 STOP 示例中所示）
    time.sleep(2.0)
    net.close()
```
</div>

<div style="max-width:fit-content;">
  &rightarrow; 可执行场景，发送 MONITOR 请求并打印 ACK 和流数据。
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
    p = argparse.ArgumentParser(description="Open Stream 示例")
    p.add_argument("scenario", choices=["handshake", "monitor", "control", "stop"])
    p.add_argument("--host", default="192.168.1.150")
    p.add_argument("--port", type=int, default=49000)

    # 通用选项
    p.add_argument("--major", type=int, default=1)
    p.add_argument("--period-ms", type=int, default=10)
    p.add_argument("--target", choices=["session", "control", "monitor"], default="session")

    # monitor 选项
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
            period_ms=args.period.ms,
        )


if __name__ == "__main__":
    main()
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

<div style="max-width:fit-content;">

```bash
python3 main.py monitor --host 192.168.1.150 --port 49000 --major 1 --url /project/robot/joints/joint_states --period-ms 1000
```
</div>

<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[tx] {"cmd":"MONITOR","payload":{"method":"GET","url":"/project/robot/joints/joint_states","period_ms":1000,"id":1,"args":{}}}
[ack] monitor_ack ok=None url=None period_ms=None
[event] {'type': 'data', 'id': 1, 'ts': 1000, 'svc_dur_ms': 0.224, 'result': {...}}
[net] 连接关闭
```

* 注意：错误以 `{ "error": "...", "message": "...", "hint": "..." }` 的形式接收。  
* 注意：`monitor_data` 的有效负载模式（`ts`、`值 (value)` 等）可能因服务器实现而异。
[__SOURCE](5-examples/4-control.md)
## 5.4 控制示例 (关节轨迹)

{% hint style="info" %}

本文档提供了使用 Open Stream **控制** 命令向机器人**流式传输关节轨迹点**的示例。

轨迹生成和存储由 `utils/motion.py` 处理。<br>
Open Stream 消息构建和传输由 `utils/api.py` 处理。<br>
您可以将以下代码直接复制到自己的项目中。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">先决条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream 服务器地址/端口 (例如 `192.168.1.150:49000`)
- 必须通过 HTTP 访问关节状态  
  例如 `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

1) 建立 TCP 连接并开始接收循环  
2) 发送握手并确认 ACK  
3) 通过 HTTP GET 检索 `/project/robot/joints/joint_states`（度）  
4) 使用 `motion.generate_sine_trajectory()` 生成基于度数的轨迹  
5) 发送 `CONTROL / joint_traject_init`  
6) 在 dt 间隔重复发送 `CONTROL / joint_traject_insert_point`  
7) 退出（如果需要，请使用 STOP 示例）
---

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

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
````</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">控制体规则</h4>

建议 `joint_traject_insert_point` 包含以下字段。

* ( 包含以下字段。

* )`interval`(秒): 点之间的间隔 (例如 )`dt_sec`
* ()
* )`time_from_start`(秒): 从开始的时间偏移 (例如 )`index * dt_sec`
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* ()
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* )`look_ahead_time`(秒): 控制器前视时间
* ( (秒): 控制器前视时间
* )`point`(度): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

以下代码是**复制并粘贴后可直接运行的**。

<details><summary>点击查看 Python 代码</summary>

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
from utils.motion import generate_sine_trajectory, save_trajectory


def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    通过 HTTP GET 从 /project/robot/joints/joint_states 获取关节位置。

    服务器端：
    - 位置：度
    - 速度：deg/s
    - 努力：Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET 失败: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP 响应不是有效的 JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式，例如 {"j1": 10.0, "j2": 20.0, ...}
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
        raise RuntimeError(f"无法从响应中提取关节位置: {data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # 轨迹参数
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # 控制定时
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

    # 1) 建立 TCP 连接并开始接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 执行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 未收到 handshake_ack；中止。")
        net.close()
        return

    # 3) 通过 HTTP 检索基准关节姿态（度数）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] 基准姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) 生成关节轨迹（度数）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] 轨迹已保存: {saved_path} (points={len(points_deg)}, dt={dt_sec})")

    # 5) 初始化关节轨迹控制
    api.joint_traject_init()

    # 6) 使用控制流式传输轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据 dt 调整传输步伐
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

如果您保持现有的 ( (度): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

以下代码是**复制并粘贴后可直接运行的**。

<details><summary>点击查看 Python 代码</summary>

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
from utils.motion import generate_sine_trajectory, save_trajectory


def http_get_joint_states(host: str, *, http_port: int = 8888, timeout_sec: float = 1.0) -> List[float]:
    """
    通过 HTTP GET 从 /project/robot/joints/joint_states 获取关节位置。

    服务器端：
    - 位置：度
    - 速度：deg/s
    - 努力：Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET 失败: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP 响应不是有效的 JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式，例如 {"j1": 10.0, "j2": 20.0, ...}
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
        raise RuntimeError(f"无法从响应中提取关节位置: {data!r}")

    return q


def run(
    host: str,
    port: int,
    *,
    major: int = 1,
    http_port: int = 8888,
    # 轨迹参数
    cycle_sec: float = 1.0,
    amplitude_deg: float = 5.0,
    dt_sec: float = 0.02,
    total_sec: float = 1.0,
    active_joint_count: Optional[int] = 6,
    # 控制定时
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

    # 1) 建立 TCP 连接并开始接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 执行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 未收到 handshake_ack；中止。")
        net.close()
        return

    # 3) 通过 HTTP 检索基准关节姿态（度数）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] 基准姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) 生成关节轨迹（度数）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] 轨迹已保存: {saved_path} (points={len(points_deg)}, dt={dt_sec})")

    # 5) 初始化关节轨迹控制
    api.joint_traject_init()

    # 6) 使用控制流式传输轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据 dt 调整传输步伐
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()
```
</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

如果您保持现有的 )`main.py`结构，您可以调用( 结构，您可以调用 )`control`场景，如下所示。

<details><summary>点击查看 python 代码</summary>

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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

1. 将机器人移动到参考位置。
2. (场景，如下所示。

<details><summary>点击查看 python 代码</summary>

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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

1. 将机器人移动到参考位置。
2. )`joint_traject_insert_point`API 仅在播放期间运行。  
将以下等待指令按原样添加到作业文件中。  
0001.job - ```wait di1```
3. 启动( API 仅在播放期间运行。  
将以下等待指令按原样添加到作业文件中。  
0001.job - ```wait di1```
3. 在自动模式下启动 )`0001.job`。
4. 在自动模式下运行以下(。
4. 在自动模式下运行以下 )`main.py`命令。

    <div style="max-width:fit-content;">

    ```bash
    # 示例：发送一个 30 秒的正弦轨迹（振幅 1 deg）与 dt = 2 ms。
    # - cycle-sec=5  : 一个正弦周期 (0 → 2π) 对应 5 秒。
    # - 使用 look-ahead-time = 0.04 s 和 dt = 0.002 s,
    #   前瞻缓冲区大小为 0.04 / 0.002 = 20 点。
    #   (跟踪可能会延迟，直到缓冲区填满 20 点。)

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
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

输出可能因环境而异，但通常应观察到以下流程。

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

#### 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储被分开到(命令中。

    <div style="max-width:fit-content;">

    ```bash
    # 示例：发送一个 30 秒的正弦轨迹（振幅 1 deg）与 dt = 2 ms。
    # - cycle-sec=5  : 一个正弦周期 (0 → 2π) 对应 5 秒。
    # - 使用 look-ahead-time = 0.04 s 和 dt = 0.002 s,
    #   前瞻缓冲区大小为 0.04 / 0.002 = 20 点。
    #   (跟踪可能会延迟，直到缓冲区填满 20 点。)

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
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

输出可能因环境而异，但通常应观察到以下流程。

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

#### 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储被分开到 )`utils/motion.py`，因此控制示例集中于**传输逻辑**。
* 发送(时，因此控制示例集中于**传输逻辑**。
* 发送 )`joint_traject_insert_point`时，建议包括(，建议包括 )`time_from_start`并根据(进行递增并根据 )`dt`进行递增。
[__SOURCE](5-examples/5-stop.md)
## 5.5 停止示例 (会话 / 流终止)

{% hint style="info" %}

本文件解释如何使用 Open Stream **停止** 命令 
以受控和安全的方式优雅地终止当前运行的 **会话** 或 **控制 / 监控流**。

- 停止是安全终止的 **强制命令**。
- 当正在传输控制轨迹或监控流处于活动状态并需要立即中断时，请使用停止。
- 下面的代码是 <b>完全功能性</b> 的，可以直接复制和使用。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">停止命令概述</h4>

停止是一个控制命令，用于终止 Open Stream 会话或特定流。

- <b>立即停止</b> 机器人，或
- <b>优雅释放</b> 控制 / 监控流。

当发送停止命令时，服务器会清理其内部状态
并在必要时释放相关资源（轨迹缓冲区、监控任务等）。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">停止目标</h4>

停止命令通过 `目标 (target)` 字段指定其终止范围。

| target value | 描述 |
|------------|------|
| `session`  | 终止整个 Open Stream 会话（推荐默认） |
| `control`  | 仅终止控制流 |
| `monitor`  | 仅终止监控流 |

* 根据实现或版本，`control` 和 `monitor` 可能是可选的。  
最安全的方法是终止整个 `session`。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

(1) 建立 TCP 连接并开始接收循环  
(2) 执行握手  
(3) 发送停止命令  
(4) 检查服务器响应  
(5) 关闭套接字

---

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

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
````</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

以下示例为指定目标发送停止命令。

<details><summary>点击查看 Python 代码</summary>

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

    # 1) connect + receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) handshake
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 握手失败；中止停止。")
        net.close()
        return

    # 3) 停止
    print(f"[INFO] 发送停止 target={target}")
    api.stop(target=target)

    # 短暂等待（服务器端处理时间）
    time.sleep(0.5)

    # 4) 关闭套接字
    net.close()
```


</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

这显示了如何根据现有的 (

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

以下示例为指定目标发送停止命令。

<details><summary>点击查看 Python 代码</summary>

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

    # 1) connect + receive loop
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) handshake
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 握手失败；中止停止。")
        net.close()
        return

    # 3) 停止
    print(f"[INFO] 发送停止 target={target}")
    api.stop(target=target)

    # 短暂等待（服务器端处理时间）
    time.sleep(0.5)

    # 4) 关闭套接字
    net.close()
```


</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

这显示了如何根据现有的 )`main.py` 场景结构调用停止。

<div style="max-width:fit-content;">

```python
# main.py 
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
<h4 style="font-size:16px; font-weight:bold;">如何运行</h4>

<div style="max-width:fit-content;">

```bash
# 终止整个会话（推荐）
python main.py stop --host 192.168.1.150 --port 49000 --target session

# 仅终止控制
python main.py stop --host 192.168.1.150 --port 49000 --target control

# 仅终止监控
python main.py stop --host 192.168.1.150 --port 49000 --target monitor
```

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

<div style="max-width:fit-content;">

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] 发送停止 target=session
[tx] {"cmd":"STOP","payload":{"target":"session"}}
[net] 连接关闭
```

</div>

---

#### 摘要

* 停止是用于 **安全终止** 机器人控制和监控的命令。
* 强烈建议使用停止终止控制轨迹传输。
* 最安全的默认用法是 )`target=session`。
[__SOURCE](6-faq/README.md)
# 6. FAQ

Q1. 为什么首先需要 HANDSHAKE?
A. 如果服务器不在 `handshake_ok` 状态，它将对 MONITOR / CONTROL / STOP 返回 **412 (handshake_required)**。

Q2. CONTROL 成功了，但没有响应。
A. 这是预期行为。当 CONTROL 完成并返回 HTTP 200 时，响应行故意被省略（未发送）。

Q3. MONITOR 可以使用 POST 或 PUT 作为方法吗？
A. 不可以。MONITOR payload 中的 `method` 字段必须是 **"GET"**。

Q4. 如果 URL 包含空格怎么办？
A. 请求将被拒绝。URL 不能包含空格。
[__SOURCE](7-release-notes/README.md)
# 7. 发行说明

本节总结了开放流接口的逐版本变更历史。<br>
每个版本记录了功能的增加、行为的变化、修复和兼容性说明。

<h4 style="font-size:15px; font-weight:bold;">发行信息</h4>

<div style="max-width:fit-content;">

| *版本 | ${cont_model} 版本 | 发行时间表 | 链接 |
|:--:|:--:|:--:|:--:|
|1.0.0|>=V70.00-00 |2026年3月|[🔗](1-v1-0-0.md)|

----

</div>

*版本: **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| 字段 | 含义 | 兼容性政策 |
|------|---------|----------------------|
| MAJOR | 基本协议变更 | **如果 MAJOR 不同则不兼容** |
| MINOR | 功能添加（向后兼容） | 如果 MAJOR 一致则兼容 |
| PATCH | 修复bug和内部改进 | 始终兼容 |

</div>


<br>

<h4 style="font-size:15px; font-weight:bold;">发行说明类别</h4>

<div style="max-width:fit-content;">

| 分类 | 描述 |
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>新增</b></span>|新增的功能、命令、字段或选项|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>已更改</b></span>|对现有行为、规格或默认值的更改|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>已修复</b></span>|修复bug、稳定性改进、异常行为纠正|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>已弃用</b></span>|计划移除或不再推荐的功能|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>注意</b></span>|必须确认的重要使用说明|

</div>

<br>

每个发行文档仅描述 **该版本中引入的更改**，按照上述类别。<br>
有关详细的使用说明或协议描述，请参考本文档中相应的参考部分。

如果一个发行版引入了行为上的更改，可能会影响现有系统。<br>
在更新之前，请始终查看目标版本的发行说明。
[__SOURCE](7-release-notes/1-v1-0-0.md)
## 7.1 Release Notes - v1.0.0
  <span style="
    font-size:14px;
    font-weight:bold;
    padding:2px 6px;
    border-radius:4px;
    border:1px solid #c62828;
    color:#c62828;
  ">
    预览
  </span>


{% hint style="warning" %}

<h4 style="font-size:15px; font-weight:bold;">状态</h4>

- 此版本是 Open Stream 接口的首次公开发布。
- 官方发布：2026 年 3 月（计划）

{% endhint %}

{% hint style="info" %}

<h4 style="font-size:15px; font-weight:bold;">概述</h4>

- Open Stream 是一种基于实时流媒体的接口，旨在用于机器人控制和状态获取。
- 本次发布提供了核心 Open Stream 协议、配方命令和相关通信规则。

{% endhint %}

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid rgb(255, 140, 0);
  font-size:15px;
  font-weight:bold;
">
  添加
</h4>

<ul>
  <li>协议
    <ul>
      <li>基于 NDJSON 的轻量级流媒体协议</li>
      <li>通过单个 TCP 连接实现双向通信</li>
      <li>基于命令的会话管理模型</li>
    </ul>
  </li>

  <li>配方命令
    <ul>
      <li>HANDSHAKE: 协议版本协商</li>
      <li>MONITOR: 定期状态数据流（毫秒级间隔）</li>
      <li>CONTROL: 实时控制命令传输（高优先级）</li>
      <li>STOP: 结束活动会话或配方</li>
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
  更改
</h4>

<ul>
  <li>这是首次公开发布；与以前版本相比没有更改。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #2E7D32;
  font-size:15px;
  font-weight:bold;
">
  修复
</h4>

<ul>
  <li>这是首次公开发布；没有修复问题。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #B71C1C;
  font-size:15px;
  font-weight:bold;
">
  弃用
</h4>

<ul>
  <li>这是首次公开发布；没有被弃用或移除的功能。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #9E9E9E;
  font-size:15px;
  font-weight:bold;
">
  注意
</h4>

<ul>
  <li>当 CONTROL 和 MONITOR 同时运行时，优先考虑 CONTROL 的实时性能。</li>
  <li>根据操作系统调度和网络条件，可能会发生周期性延迟。</li>
  <li>每个 TCP 连接最多只能有一个 MONITOR 会话处于活动状态。</li>
  <li>MONITOR 数据不适合用于实时控制决策。</li>
  <li>根据网络和客户端性能，可能会发生延迟和抖动。</li>
</ul>

<br>

<h4 style="font-size:15px; font-weight:bold;">相关文档</h4>

<ul>
  <li><a href="../1-overview/README.md">Open Stream 概述</a></li>
  <li><a href="../1-overview/2-usage-considerations.md">使用注意事项</a></li>
  <li><a href="../2-protocol/README.md">协议</a></li>
  <li><a href="../3-recipe/README.md">配方命令</a></li>
  <li><a href="../5-examples/README.md">示例</a></li>
  <li><a href="../6-faq/README.md">常见问题解答</a></li>
</ul>