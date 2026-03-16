
[__SOURCE](README.md)
# ${cont_model} 控制器功能手册 - Open Stream

{% hint style="warning" %}

HD Hyundai Robotics 对因使用本手册未指定的 ${cont_model} Open Stream 功能或未在 ${cont_model} 打开 API 手册中记录的 API 而造成的任何损害或问题不承担责任。

{% endhint %}
[__SOURCE](0-about-this-manual/precautions.md)
# 注意事项

{% include file="zh/precautions.md" %}
[__SOURCE](1-overview/README.md)
# 1. 概述

本文档是针对使用 Open Stream 的外部客户的用户指南。  
它解释了 Open Stream 的目的、核心概念、整体架构以及支持的使用场景。

<br>

通过本文档，读者将了解：
- Open Stream 旨在解决哪些问题
- Open Stream 如何操作
- 何时以及在什么情况下应使用 Open Stream

📌 有关最新更新和更改，请参阅 [Release Notes](../10-release-notes/README.md)
[__SOURCE](1-overview/1-about-open-stream.md)
## 1.1 什么是开放流？

开放流是一个接口，允许客户端以流式方式持续接收结果  
通过在短时间间隔内反复调用 **${cont_model} Open APIs**。

<br>

它通过嵌入在 ${cont_model} 控制器内的 **基于TCP的轻量级服务器** 提供流式接口，  
使外部客户端能够在持久连接上持续发送和接收数据。

<br>

开放流具有以下特点：

- 维护 **单一的长期TCP连接**
- 对请求和响应使用 **NDJSON（新行分隔的JSON）**
- 支持 **周期性数据流（`MONITOR`）** 和 **即时控制命令（`CONTROL`）**
- 消除了重复创建HTTP请求/响应循环

<br>

开放流旨在为需要处理  
**通过单一连接进行高频控制命令和状态监控** 的客户端环境设计。

<br><br>

<b>整体操作概述</b>

开放流的基本操作流程如下。

<div style="display:flex; flex-wrap:wrap; align-items:flex-start;">

<!-- Left: Image -->
<div style="flex:1 1 420px; min-width:420px; max-width:420px;">
  <img
    src="../_assets/1-open_stream_concept.png"
    alt="开放流流程"
    style="width:100%; height:auto; border-radius:6px;"
  />
</div>

<!-- Right: Ordered List -->
<div style="flex:1 1 280px; min-width:280px; max-width:fit-content;">
  <ol style="line-height:1.5;">

  <li>客户端与服务器建立TCP连接，创建会话。</li><br>

  <li>连接后，客户端立即发送 <code>HANDSHAKE</code> 命令<br>
      以验证与服务器的协议版本兼容性。</li><br>
<li>服务器处理<code>HANDSHAKE</code>请求，并且如果协议版本兼容，则发送<code>handshake_ack</code>事件。</li><br>

<li>在成功的<code>HANDSHAKE</code>后，客户端可以使用<code>MONITOR</code>命令请求定期数据流，或使用<code>CONTROL</code>命令执行一次性请求。
    <small>（即使在MONITOR活动期间，也可以发送CONTROL命令。）</small>
</li><br>

<li>当<code>MONITOR</code>处于活动状态时，服务器在配置的间隔内发送<code>data</code>事件，而不考虑额外的客户端请求。</li><br>

<li>成功的<code>CONTROL</code>命令不会生成ACK响应。<br>
    只有失败可能导致<code>error</code>或<code>control_err</code>事件。</li><br>

<li>当操作完成时，客户端发送<code>STOP</code>命令
    以指示终止活动操作或会话意图，
    并在收到<code>stop_ack</code>后关闭TCP连接。
</li>

</ol>
</div>

</div>

<br>

{% hint style="info" %}

**MONITOR命令是什么？**  
MONITOR命令在客户端定义的间隔内重复调用单个${cont_model} Open API服务  
并持续将结果流传输到客户端。

**CONTROL命令是什么？**  
CONTROL命令用于向${cont_model} Open API发送一次性控制请求。  
客户端可以根据需要以短间隔重复发送CONTROL命令。

{% endhint %}

Open Stream允许在单个TCP连接内一起使用MONITOR和CONTROL命令。

{% hint style="warning" %}

然而，在单个连接内，**只能同时激活一个MONITOR会话和一个CONTROL会话**。

{% endhint %}
[__SOURCE](1-overview/2-usage-considerations.md)
## 1.2 使用注意事项

Open Stream 旨在高效处理实时控制和状态监控。  
然而，以下约束和假设必须被仔细考虑。

- Open Stream 以周期性数据传输为目标，但不**保证严格的确定性**。
- 根据操作系统调度、网络状况和客户端处理负载，可能会出现周期性抖动。
- 由于 Open Stream 基于开放 API，Open Stream 的执行时间可能会受到 ${cont_model} 控制器的 API 服务处理时间的影响。
- 当 PLC 或播放任务同时运行时，Open Stream 执行可能会因系统任务优先级而延迟。
- 每个 TCP 连接只能有**一个 MONITOR 会话**处于活动状态。
- 所有命令必须遵循定义的协议顺序。
  违反顺序可能导致命令拒绝或连接终止。

<br><br>

<b>MONITOR 和 CONTROL 操作性能参考（测试结果）</b>

以下结果比较了 MONITOR 仅操作与在相同测试环境下同时进行 CONTROL + MONITOR 操作的周期性行为。

测试环境：
- 服务器：${cont_model} COM
- 客户端：Windows 11 上的 Python 客户端
- 网络：TCP 连接
- 发送/接收周期：最大可配置的 MONITOR 频率

<br>

结果摘要

<div style="max-width:fit-content;">

1. 仅 MONITOR

| **测试条件** | **周期特性** |
| --- | --- |
| - MONITOR 周期：2 ms (500 Hz)<br>- 未使用 CONTROL<br>- 持续运行：10 小时 | - <u><b>平均接收周期：~2.0 ms</b></u> |

2. 同时进行 CONTROL + MONITOR

| **测试条件** | **周期特性** |
| --- | --- |
| - CONTROL 周期：2 ms<br>- MONITOR 周期：2 ms<br>- CONTROL 和 MONITOR 同时激活 | - CONTROL (发送)：<u><b>平均周期 ~2.0 ms</b></u>，最大延迟 ~30-40 ms<br>- MONITOR (接收)：<u><b>平均周期 ~2.1-2.2 ms</b></u>，最大延迟从数十毫秒到 >100 ms |

</div>

<br><br>

<b>解读和操作说明</b>
- 当单独使用 MONITOR 时，即使在长时间连续操作期间，也可以相对稳定地进行周期接收。
- 当 CONTROL 和 MONITOR 同时使用时，CONTROL 会话根据系统设计以更高的优先级处理。
- 因此，CONTROL 的周期稳定性得以维持，而 MONITOR 的接收周期可能会增加并经历间歇性延迟。
- 同时使用 CONTROL 和 MONITOR 的系统必须在设计时假设 MONITOR 周期性可能出现降级和抖动。
[__SOURCE](2-protocol/README.md)
# 2. 协议

本节描述了 Open Stream 使用的传输协议和消息帧规则。

> **警告**
>
> Open Stream 不是请求-响应协议，而是一个 **事件流**。  
> 服务器事件（`data`、`*_ack`、`error`）可能随时到达，而不考虑客户端请求，  
> 因此客户端逻辑必须在不依赖消息顺序的情况下实现。

- Open Stream 使用一个 **基于 TCP 套接字的单会话通信模型**。
- 客户端和服务器之间交换的消息使用 **NDJSON（换行分隔 JSON）**。
- 每条消息通过 **每行序列化一个 JSON 对象并在末尾附加 `\n` 发送**。

> **信息**
>
> 由于 TCP 流的特性，单个 `recv()` 调用可能不会恰好返回一条消息。  
> 收到的数据应积累在内部缓冲区中，并通过在 `\n` 处分割进行解析。

有关详细的 NDJSON 规则，请参阅以下文档。

- [NDJSON 规范](./1-ndjson.md)
[__SOURCE](2-protocol/1-ndjson.md)
## 2.1 什么是 NDJSON？

Open Stream 使用 **NDJSON (换行分隔的 JSON)** 进行消息框架。  
换句话说，**一行等于一个 JSON 消息**。

<h4 style="font-size:15px; font-weight:bold;">1. 消息框架</h4>

<div style="max-width:fit-content;">

- 客户端按如下方式发送请求：

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

1. 每个消息必须将一个 JSON 对象序列化为一行。  
   → JSON 字符串内部的换行符会破坏框架。
2. 每个消息 **必须以换行符 (`\n`) 结束**。
3. 所有消息必须编码为 **UTF-8**。

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 建议</h4>

1. 建议使用无空格序列化以最小化消息大小。

```python
# Python 示例
import json
json.dumps(recipe_data, separators=(",", ":")) + "\n"
```

<br>

<h4 style="font-size:15px; font-weight:bold;">4. 客户端实现提示</h4>
<div style="max-width:fit-content;">

{% hint style="info" %}

由于TCP流特性，单个`recv()`调用并不能保证接收到恰好一行。  
建议将接收到的数据累积到内部缓冲区，并通过`\n`进行消息分割，  
然后再执行JSON解析。

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
必须理解以正确实现和操作 Open Stream。

{% endhint %}

</div>

<br>

<h4 style="font-size:16px; font-weight:bold;">1. 会话生命周期</h4>

Open Stream 将 <b>一个 TCP 连接视为一个会话</b>。  
典型的会话流程如下：

1. 客户端通过 TCP 连接到服务器以创建会话。
2. 在连接后，客户端立即发送 `HANDSHAKE` 命令以验证与服务器的协议版本兼容性。
3. 处理完 `HANDSHAKE` 请求后，如果协议版本匹配，服务器将发送 `handshake_ack` 事件。
4. 在 `HANDSHAKE` 之后，客户端可以通过 `MONITOR` 请求周期性数据流，或通过 `CONTROL` 执行一次性请求。（在 `MONITOR` 活动时，也可以发送 `CONTROL`。）
5. 当 `MONITOR` 活动时，服务器会定期发送 `data` 事件，而不管额外的客户端请求。
6. `CONTROL` 命令在成功时不会单独发送 ACK；仅在失败时可能会发送 `error` 或 `control_err` 事件。
7. 工作完成后，客户端发送 `STOP` 以表示终止活动操作或会话的意图，然后在收到服务器的 `stop_ack` 后关闭 TCP 连接。

{% hint style="warning" %}

Open Stream 是一种事件驱动的流协议，不保证请求-响应的顺序。  
由于 `data`、`*_ack` 和 `error` 事件之间的到达顺序不 guaranteed，因此客户端必须在不依赖消息顺序的情况下处理事件。

{% endhint %}


<br>

<h4 style="font-size:16px; font-weight:bold;">2. 使用规则</h4>

以下规则必须遵循以正确使用 Open Stream。

- `HANDSHAKE` 必须在 <b>会话开始时</b> 执行。
- 如果在 `HANDSHAKE` 之前调用 `MONITOR` 或 `CONTROL`，服务器可能会拒绝请求。
- `STOP(target=session)` 用于明确表示"优雅终止意图"，并建议在之后关闭 TCP 连接。

<br>
<h4 style="font-size:16px; font-weight:bold;">3. 消息方向</h4>

<p>
消息在开放流中根据 <b>方向和角色</b> 被分类为以下几种。
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
        <tr><td><code>CONTROL</code></td><td>执行命令类型的REST请求</td></tr>
        <tr><td><code>STOP</code></td><td>终止活动操作或会话</td></tr>
      </tbody>
    </table>
  </div>

  <div style="overflow-x:auto;">
    <div style="font-weight:bold; margin-bottom:6px;">客户端 ⇠ 服务器 (事件)</div>
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
          <td>确认已接受命令的ACK</td>
          <td>例如 <code>handshake_ack</code>, <code>monitor_ack</code>, <code>stop_ack</code></td>
</tr>
<tr>
  <td><code>data</code></td>
  <td>当监控激活时的周期性数据事件</td>
  <td>执行${cont_model} Open API服务功能的结果</td>
</tr>
<tr>
  <td><code>error</code></td>
  <td>发生故障时发送的错误消息</td>
  <td>有关详细信息，请参阅错误代码部分</td>
</tr>
</tbody>
</table>
</div>

{% hint style="info" %}

服务器 → 客户端事件可能<b>无法与客户端</b>请求一一对应。  
虽然`*_ack`和`error`遵循请求响应模式，  
但由监控生成的`data`事件是独立流式传输的。  
客户端必须始终保持接收循环运行。

{% endhint %}

</div>
</div>

<div style="max-width:fit-content;">


| 请求-响应 | 流媒体 |
|---|---|
| 客户端 → `HANDSHAKE/MONITOR/CONTROL/STOP` → 服务器<br>客户端 ← `*_ack`, `error` ← 服务器 | （在`monitor_ack`之后）<br>服务器 → `data` → 客户端<br>服务器 → `data` → 客户端<br>... |
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">4. MONITOR 流媒体行为</h4>

`MONITOR` 是一个服务器驱动的机制，基于客户端提供的配方，  
服务器以指定的时间间隔（`period_ms`）执行${cont_model} Open API服务功能  
并将结果作为`data`事件流式传输。

客户端必须在以下假设下实现。

- 始终保持接收循环运行。
- 不要假定同步请求-响应配对。

<br>
<h4 style="font-size:16px; font-weight:bold;">5. 控制命令执行</h4>
根据政策/实施，<b>CONTROL在成功时不提供单独的响应行。</b>

推荐策略：

- 通过`error`或`control_err`事件检测故障。
- 使用以下方法验证成功：
  - 确认MONITOR结果的变化
  - 使用专用状态查询MONITOR端点


<br>
<h4 style="font-size:16px; font-weight:bold;">6. 超时 / 看门狗</h4>

如果会话长时间保持空闲，服务器可能会终止连接。

客户端建议：

- 在连接后立即执行`HANDSHAKE`
- 使用`STOP(target=session)`进行优雅关机
- 在流媒体期间防止接收循环停止
- 在EOF或套接字错误时准备重新连接和重新执行HANDSHAKE逻辑

在当前服务器实施中，适用以下政策。

- <b>解除武装状态（空闲/无活动MONITOR）</b>  
  &rightarrow; 在大约<b>180秒</b>没有有意义的活动后，会话被终止

- <b>武装状态（活动MONITOR流媒体）</b>  
  &rightarrow; 如果流媒体中断超过大约<b>5秒</b>，则会话被终止

* 上述时间值可能会根据服务器政策或操作环境而变化。

<br>
<h4 style="font-size:16px; font-weight:bold;">7. 推荐架构 </h4>

对于实际实施，推荐以下结构。

- 分开发送（命令）和接收（事件）  
  &rightarrow; 发送：构建命令 + `sendall`  
  &rightarrow; 接收：NDJSON行解析器 + 分发器

- 单一责任接收循环  
  &rightarrow; 按`\n`拆分行  
  &rightarrow; JSON解析  
  &rightarrow; 基于`类型 (type)` / `error`的事件路由
[__SOURCE](3-recipe/README.md)
# 3. 配方命令

**配方**指的是在 Open Stream 中从客户端发送到服务器的 **NDJSON 行**。  
每一行采用以下格式传输。

<div style="max-width:fit-content;">

```json
// 请求
{"cmd":"<COMMAND>","payload":{...}}\n
````</div>

服务器以相同的 NDJSON 行格式返回 ACK、事件和错误。

<div style="max-width:fit-content;">

```json
// 响应
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

每个消息字段的含义如下。

<h4 style="font-size:16px; font-weight:bold;">请求 (客户端 → 服务器)</h4>

<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| (

</div>

服务器以相同的 NDJSON 行格式返回 ACK、事件和错误。

<div style="max-width:fit-content;">

```json
// 响应
{"type":"*_ack", ...}\n
{"type":"data", ...}\n
{"error":"<code>","message":"<msg>", "hint":"<hint>"}\n
```

</div>

<br>

每个消息字段的含义如下。

<h4 style="font-size:16px; font-weight:bold;">请求（客户端 → 服务器）</h4>

<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| )`cmd`| 字符串 | 是 | 命令名称 ( ( | 字符串 | 是 | 命令名称 ()`HANDSHAKE`, (, )`MONITOR`, (, )`CONTROL`, (, )`STOP`) |
| () |
| )`payload`| 对象 | 是 | 命令参数对象（有关架构详细信息，请参阅每个命令文档） |

1. [HANDSHAKE](./1-handshake.md): 协议版本协商（会话开始时必需）

2. [MONITOR](./2-monitor.md): 定期REST GET执行 + ( | 对象 | 是 | 命令参数对象（有关架构详细信息，请参阅每个命令文档） |

1. [HANDSHAKE](./1-handshake.md): 协议版本协商（会话开始时必需）

2. [MONITOR](./2-monitor.md): 定期REST GET执行 + )`数据`流

3. [CONTROL](./3-control.md): 单次REST执行（**成功时没有响应行**）

4. [STOP](./4-stop.md): 停止（流）

3. [CONTROL](./3-control.md): 单次REST执行（**成功时没有响应行**）

4. [STOP](./4-stop.md): 停止 )`monitor`, (, )`control`, 或 (, 或 )`session`</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应（客户端 ⇠ 服务器）</h4>

<h4 style="font-size:16px; font-weight:bold;">成功</h4>

<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| (

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应（客户端 ⇠ 服务器）</h4>

<h4 style="font-size:16px; font-weight:bold;">成功</h4>
<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| )`type`| 字符串 | 是 | 事件类型（例如（ | 字符串 | 是 | 事件类型（例如）`handshake_ack`、（、）`monitor_ack`、（、）`data`、（、）`stop_ack`） | - 对于（） |

- 对于）`HANDSHAKE`响应，字段（响应，字段）`ok`（布尔值）和（（布尔值）和）`version`（字符串）也包括在内。

</div>

<h4 style="font-size:16px; font-weight:bold;">错误</h4>

<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| (（字符串）也包括在内。

</div>

<h4 style="font-size:16px; font-weight:bold;">错误</h4>

<div style="max-width:fit-content;">

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| )`error`| 字符串 | 是 | 错误代码（机器可读） |
| ( | 字符串 | 是 | 错误代码（机器可读） |
| )`message`| 字符串 | 是 | 错误描述（人类可读） |
| ( | 字符串 | 是 | 错误描述（人类可读） |
| )`hint` | 字符串 | 否 | 解决方案的指南或示例 |

</div>
[__SOURCE](3-recipe/1-handshake.md)
## 3.1 握手

这是会话开始后立即执行的**协议版本协商**步骤。  
如果在`HANDSHAKE`之前调用`MONITOR`或`CONTROL`，服务器可能会拒绝请求。


<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

</div>

<div style="max-width:fit-content;">

| 载荷字段 | 必需 | 类型 | 规则 |
| ------- | -------- | ---- | ----- |
| `major` | 是 | int | 大于或等于0的整数 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
```

| 键 | 类型 | 必需 | 描述 |
| --- | ---- | -------: | ----------- |
| `ok` | boolean | 否 | 一些ACK的显式成功标志（例如`handshake_ack`） |
| `version` | string | 否 | 服务器协议版本（`MAJOR.MINOR.PATCH`） |

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

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| `busy_session_active` | 409 | 已经存在一个活动任务 | 在 CONTROL 或 MONITOR 任务运行时请求 HANDSHAKE |
| `version_mismatch` | 400 | 协议 MAJOR 版本不匹配 | 客户端 `major` 与服务器 MAJOR 不匹配 |
| `missing_major` | 400 | 缺少必填字段 | 负载中缺少 `major` 键 |
| `invalid_major_type` | 400 | 无效类型 | `major` 不是数字 (int) |
| `invalid_version` | 400 | 无效值范围 | `major` 是负数 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ---- | --------- | ---- | --------------- | ---------- |
| `major` | 必填 | int | 必须存在于负载中 | `missing_major` |
| `major` | 类型 | int | 必须是一个数字 | `invalid_major_type` |
| `major` | 范围 | int | 整数 ≥ 0 | `invalid_version` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

- 服务器只验证 **MAJOR 版本**。
- MINOR / PATCH 更改不会破坏与现有客户端的兼容性。
- 有关版本政策的详细信息，请参阅 [发布说明](../10-release-notes/README.md)。
[__SOURCE](3-recipe/2-monitor.md)
## 3.2 监视

此命令定期调用客户端指定的 REST **GET** 服务  
并将结果流式传输为单行 NDJSON 消息。

- 在当前实现中，**每个会话仅维护一个监视器**。
- 当接收到新的 `MONITOR` 命令时，现有的监视会话会自动终止并被替换。
- `MONITOR` 只能在成功的 HANDSHAKE 之后使用。<br>
  &rightarrow; 如果在 HANDSHAKE 之前调用，将返回 `handshake_required` 错误。

<br>
<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"MONITOR","payload":{"method":"GET","period_ms":2,"url":"/project/robot/joints/joint_states","args":{"jno_start":1,"jno_n":6}}}\n
````</div>

<div style="max-width:fit-content;">

| 负载字段 | 必需 | 类型 | 规则 |
| ------------ | -------- | ---- | ----- |
| (

</div>

<div style="max-width:fit-content;">

| 负载字段 | 必需 | 类型 | 规则 |
| ------------ | -------- | ---- | ----- |
| )`url`| 是 | 字符串 | 必须以 ( | 是 | 字符串 | 必须以 )`/` 开头，不能有空格，最大长度 2048 |
| (, 不能有空格，最大长度 2048 |
| )`method`| 是 | 字符串 | 仅允许 ( | 是 | 字符串 | 仅允许 )`"GET"` |
| ( 被允许 |
| )`period_ms`| 是 | 整数 | 2 ~ 30000 (毫秒)，范围外值将被限制 |
| ( | 是 | 整数 | 2 ~ 30000 (毫秒)，范围外值将被限制 |
| )`args`| 否 | 对象 | 查询参数对象（仅 JSON 对象） |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```
<div>

* ( | No | object | 查询参数的对象（仅限 JSON 对象） |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* )`monitor_ack`表示 MONITOR 请求已被接受。
* 到达顺序 ( 表示 MONITOR 请求已被接受。
* 到达顺序 )`monitor_ack`与第一个 ( 以及第一个 )`data`事件的顺序**无保证**。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>Streaming</i></u></b>)</h4>

当 MONITOR 活动时，服务器在规定的间隔内重复调用 REST API (GET)  
的事件是**无保证**。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>Streaming</i></u></b>)</h4>

当 MONITOR 活动时，服务器在规定的间隔内重复调用 REST API (GET)  
() `period_ms` 并将结果作为 () 发送，并将结果作为 )`data`事件发送。

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
| ------------ | ---- | ----------- |
| )`type`| 字符串 | 事件类型 ( ( | 字符串 | 事件类型 ()`data`) |
| () |
| )`ts`| 数字 | 服务器端时间戳 (毫秒) |
| ( | 数字 | 服务器端时间戳 (毫秒) |
| )`svc_dur_ms`| 数字 | REST调用和处理所花费的时间 (毫秒) |
| ( | 数字 | REST调用和处理所花费的时间 (毫秒) |
| )`result`| 任意 | REST响应主体 (如果存在) |
| ( | 任意 | REST响应主体 (如果存在) |
| )`status`| 数字 | 当REST主体为空时返回的HTTP状态代码 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的NDJSON错误架构。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">错误代码</h4>

<div style="max-width:fit-content;">

| 错误代码 | HTTP状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| ( | 数字 | 当REST主体为空时返回的HTTP状态代码 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用的NDJSON错误架构。

<div style="max-width:fit-content;">
```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">错误代码</h4>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | 未执行 HANDSHAKE | 在执行 HANDSHAKE 之前调用了 MONITOR |
| ( | 412 | 未执行 HANDSHAKE | 在执行 HANDSHAKE 之前调用了 MONITOR |
| )`missing_url`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`url`键缺失 |
| ( 键缺失 |
| )`invalid_url`| 400 | 无效的 URL 格式 | 不以 ( | 400 | 无效的 URL 格式 | 不以 )`/`开头或包含空格 |
| ( 或包含空格 |
| )`url_too_long`| 400 | URL 过长 | URL 长度超过 2048 |
| ( | 400 | URL 过长 | URL 长度超过 2048 |
| )`missing_method`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`method`键缺失 |
| ( 键缺失 |
| )`invalid_method`| 400 | 无效的方法 | 不是 ( | 400 | 无效的方法 | 不是 )`"GET"`|
| ( |
| )`missing_period_ms`| 400 | 缺少必填字段 | ( | 400 | 缺少必填字段 | )`period_ms`键缺失 |
| ( 键缺失 |
| )`invalid_period`| 400 | 无效类型 | ( | 400 | 无效类型 | )`period_ms`不是整数 |
| ( 不是整数 |
| )`invalid_args`| 400 | 无效类型 | ( | 400 | 无效类型 | )`args`不是对象 |

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
| )`url`| 必需 | string | 必须存在于有效负载中 | ( | 必需 | string | 必须存在于有效负载中 | )`missing_url`|
| ( |
| )`url`| 格式 | string | 必须以 ( | 格式 | string | 必须以 )`/` 开头, 无空格 | (, 无空格 | )`invalid_url`|
| ( |
| )`url`| 长度 | string | 最大 2048 | ( | 长度 | string | 最大 2048 | )`url_too_long`|
| ( |
| )`method`| 必需 | string | 必须是 ( | 必需 | string | 必须是 )`"GET"`| ( | )`missing_method`, (, )`invalid_method`|
| ( |
| )`period_ms`| 必需 | int | 必须是整数 | ( | 必需 | int | 必须是整数 | )`missing_period_ms`, (, )`invalid_period`|
| ( |
| )`period_ms`| 范围 | int | 2~30000, 超出范围时限制 | - |
| ( | 范围 | int | 2~30000, 超出范围时限制 | - |
| )`args`| 类型 | object | 仅限 JSON 对象 | ( | 类型 | object | 仅限 JSON 对象 | )`invalid_args`|

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗行为</h4>

* 当 MONITOR 被激活时，看门狗转换到 **ARM 状态**。
* 在此状态下，会话空闲超时从 **180 秒减少到 5 秒**。
* 如果在监控期间 TCP 连接丢失，或  
  在一定时间内未从客户端接收到有意义的命令，  
  看门狗将检测到此情况并自动清理会话。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* MONITOR 是一种服务器驱动的流机制。
* ( |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗行为</h4>

* 当 MONITOR 被激活时，看门狗转换到 **ARM 状态**。
* 在此状态下，会话空闲超时从 **180 秒减少到 5 秒**。
* 如果在监控期间 TCP 连接丢失，或  
  在一定时间内未从客户端接收到有意义的命令，  
  看门狗将检测到此情况并自动清理会话。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* MONITOR 是一种服务器驱动的流机制。
* )`data` 事件可能在任何时间到达，无论 ( 事件可能在任何时间到达，无论是否 )`monitor_ack` 已被接收。
* 客户端必须始终保持接收循环运行，并根据 ( 已被接收处理事件。
* 客户端必须始终保持接收循环运行，并根据 )`type` 字段处理事件。

[__SOURCE](3-recipe/3-control.md)
## 3.3 控制

控制是客户用于控制机器人或更新内部控制器数据的命令。  
内部调用 <b>POST / PUT / DELETE-based ${cont_model} OpenAPI</b>，即使在流环境中，  
也应用与现有 OpenAPI 相同的 <b>REST 路径和验证逻辑</b>。

- 控制只能在 **成功握手后** 使用。<br>
  &rightarrow; 如果在握手之前调用，将立即以 `handshake_required` 错误被拒绝。
- 控制是一个 <b>一次性命令</b>，而且 <b style="color:#ec1249;">在成功时不会发送响应 NDJSON 行。</b>
- 即使在监控活动期间也可以执行控制。

<br>
<h4 style="font-size:16px; font-weight:bold;">请求</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/project/robot/trajectory/joint_traject_insert_point","args":{},"body":{"interval":0.005,"time_from_start":-1,"look_ahead_time":0.004,"point":[1.014532178568314,91.01453217856832,1.014532178568314,1.014532178568314,1.014532178568314,0.013294178568314]}}}\n
````</div>

<div style="max-width:fit-content;">

| 载荷字段 | 必填 | 类型 | 规则 |
| ------------- | -------- | ---- | ----- |
| (
</div>

<div style="max-width:fit-content;">

| 载荷字段 | 必填 | 类型 | 规则 |
| ------------- | -------- | ---- | ----- |
| )`url`| 是 | 字符串 | 必须以 ( | 是 | 字符串 | 必须以 )`/` 开头，不能有空格 |
| (,不能有空格 |
| )`method`| 是 | 字符串 | 其中之一 ( | 是 | 字符串 | 其中之一 )`POST`、( )`PUT`、( )`DELETE`|
| ( |
| )`args`| 否 | 对象 | REST 查询参数的对象 |
| ( | 否 | 对象 | REST 查询参数的对象 |
| )`body`| 否 | 对象 \\| 数组 | REST 请求主体 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>无响应行</i></u></b>)</h4>

如果控制命令成功处理，  
<b>服务器不会发送响应 NDJSON 行。</b>  
客户端必须实现该命令，而不期望返回值。

* 这种行为是在流协议中设计的。
* 控制成功应通过 <b>状态变化或监控结果</b> 来验证，而不是通过接收 ACK。
<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

如果发生错误，服务器将发送一个 ( | 无 | 对象 \\| 数组 | REST 请求主体 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>无响应行</i></u></b>)</h4>

如果 CONTROL 命令成功处理，  
<b>服务器不会发送响应的 NDJSON 行。</b>  
客户端必须实现发出命令而不期待返回值。

* 这种行为是 Stream 协议的设计使然。
* CONTROL 成功应通过 <b>状态变化或 MONITOR 结果</b> 验证，而不是通过接收 ACK。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

如果发生错误，服务器将发送一个 )`control_err`事件到当前会话。

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| ( 事件到当前会话。

<div style="max-width:fit-content;">

```json
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP 状态 | 描述 | 发生时机 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | 未执行 HANDSHAKE | 在执行 CONTROL 之前调用 HANDSHAKE |
| ( | 412 | 未执行握手 | 控制在握手之前调用 |
| )`missing_url`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`url`键缺失 |
| ( 键缺失 |
| )`invalid_url`| 400 | 无效的URL格式 | 不以 ( | 400 | 无效的URL格式 | 不以 )`/`开头或包含空格 |
| ( 或包含空格 |
| )`missing_method`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`method`键缺失 |
| ( 键缺失 |
| )`invalid_method`| 400 | 无效的方法 | 不是 ( | 400 | 无效的方法 | 不是 )`POST/PUT/DELETE`|
| ( |
| )`invalid_args`| 400 | 无效类型 | ( | 400 | 无效类型 | )`args`不是一个对象 |
| ( 不是一个对象 |
| )`invalid_body`| 400 | 无效类型 | ( | 400 | 无效类型 | )`body`不是一个对象或数组 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| ( 不是一个对象或数组 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">有效负载验证规则</h4>

<div style="max-width:fit-content;">

| 字段 | 属性 | 类型 | 验证规则 | 错误代码 |
| ----- | --------- | ---- | --------------- | ---------- |
| )`url`| 必需 | 字符串 | 必须存在于有效负载中 | ( | 必需 | 字符串 | 必须存在于有效负载中 | )`missing_url`|
| ( |
| )`url`| 格式 | 字符串 | 必须以 ( | 格式 | 字符串 | 必须以 )`/`开头，没有空格 | (, 没有空格 | )`invalid_url`|
| ( |
| )`method`| 必需 | 字符串 | 之一 ( | 必需 | 字符串 | 之一 )`POST/PUT/DELETE`| ( | )`missing_method`，( | )`invalid_method`|
| ( |
| )`args`| 类型 | 对象 | 仅JSON对象 | ( | 类型 | 对象 | 仅JSON对象 | )`invalid_args`|
| ( |
| )`body`| 类型 | 对象 \\| 数组 | 仅对象或数组 | ( | 类型 | 对象 \\| 数组 | 仅对象或数组 | )`invalid_body` |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">看门狗交互</h4>

- 当控制命令成功执行时，看门狗更新其监控的最后活动时间戳。
[__SOURCE](3-recipe/4-stop.md)
## 3.4 停止

STOP 是一个食谱命令，用于中断当前会话中的正在进行的操作  
或明确通知服务器终止会话的意图。

- STOP 只能在 **成功的握手后** 使用。
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

| Payload 字段 | 必需 | 类型 | 规则 |
| ------------ | -------- | ---- | ----- |
| (

</div>
<div style="max-width:fit-content;">

| Payload 字段 | 必需 | 类型 | 规则 |
| ------------ | -------- | ---- | ----- |
| )`target`| 是 | 字符串 | 其中之一 ( | 是 | 字符串 | 其中之一 )`"session"`、(、)`"control"`、(、)`"monitor"`|

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* （的值 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 成功 (<b><u><i>ACK</i></u></b>)</h4>
<div style="max-width:fit-content;">

```json
{"type":"stop_ack","target":"session"}\n
```

</div>

* )`stop_ack.target`的值与请求的 )`target`值相同。
* 表示STOP请求已成功接受。

<br>
<h4 style="font-size:16px; font-weight:bold;">响应 - 错误</h4>

所有错误响应遵循通用NDJSON错误 schema。

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<div style="max-width:fit-content;">

| 错误代码 | HTTP状态 | 描述 | 发生时 |
| ---------- | ----------- | ----------- | -------------- |
| )`handshake_required`| 412 | HANDSHAKE未执行 | 在HANDSHAKE之前调用STOP |
| ( | 412 | 未执行握手 | 在握手之前调用了停止 |
| )`missing_target`| 400 | 缺少必需字段 | ( | 400 | 缺少必需字段 | )`target`键缺失 |
| ( 键缺失 |
| )`invalid_target`| 400 | 无效的目标值 | 不支持 ( | 400 | 无效的目标值 | 不支持 )`target`值 |

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
| )`target`| 必需 | 字符串 | 必须存在于有效负载中 | ( | 必需 | 字符串 | 必须存在于有效负载中 | )`missing_target`|
| ( |
| )`target`| 值 | 字符串 | 必须是 ( | 值 | 字符串 | 必须是 )`"session"`, (, )`"control"`, (, )`"monitor"`| ( | )`invalid_target`|

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">行为说明</h4>

* ( |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">行为说明</h4>

* )`target=monitor`* 停止活动的监视流。
* (
  * 停止活动的监视流。
* )`target=control`* 清理控制执行状态。
* (
  * 清理控制执行状态。
* )`target=session`* 明确通知服务器会话终止意图。
  * 在接收后关闭 TCP 连接 (
  * 明确通知服务器会话终止意图。
* 建议在接收到 )`stop_ack` 后关闭 TCP 连接。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* STOP 旨在安全释放服务器资源。
* 建议使用 (。

<br>
<h4 style="font-size:16px; font-weight:bold;">注意</h4>

* STOP 旨在安全释放服务器资源。
* 在优雅关闭场景中，强烈建议使用 )`target=session`。
[__SOURCE](4-error/README.md)
# 4. 错误代码

本文档描述了 Open Stream 服务器返回的 **错误代码** 及其含义。

错误通常以 **单行 NDJSON 消息** 的格式传递，格式如下。

<div style="max-width: fit-content;">

```json
{"error":"<error_code>","message":"...","hint":"..."}
```

| 字段     | 描述                   |
| -------- | ---------------------- |
| error    | 机器可读的错误代码    |
| message  | 人类可读的简短描述    |
| hint     | 可选字段。故障排除的额外提示 |

- （注意）并非所有错误都包含 `hint` 字段。

</div>

<br>

<div style="max-width: fit-content;">

<h4 style="font-size:15px; font-weight:bold;">1. 协议 / 会话错误</h4>

在协议解析、会话状态处理或初始化程序违反过程中发生的错误。

| 错误代码              | 描述                           | 典型原因                                | 客户端操作                                      |
| --------------------- | ------------------------------ | --------------------------------------- | ---------------------------------------------- |
| invalid_ndjson        | NDJSON 解析失败                | JSON 损坏，缺少换行符 (`\n`)             | 遵循每行一个 JSON + 换行规则                     |
| rx_buf_overflow       | 接收缓冲区溢出                | 消息过大或突发消息过多                   | 减少消息大小，限制发送速率                      |
| handshake_required    | 未执行 HANDSHAKE              | 初始握手省略                            | 连接后立即执行 HANDSHAKE                       |
| version_mismatch      | 协议版本不匹配                | MAJOR 版本不匹配                        | 匹配服务器 MAJOR 版本                           |
| busy_session_active   | 会话已在使用                  | MONITOR/CONTROL 活动                    | 停止后重试                                    |
| session_timeout       | 会话空闲超时                  | 看门狗超时                              | 保持定期活动或重新连接                          |

<br>

<h4 style="font-size:15px; font-weight:bold;">2. 命令 / 载荷验证错误</h4>

在请求消息结构或字段验证过程中发生的错误。

| 错误代码              | 描述                           | 典型原因                                | 客户端操作                                      |
| --------------------- | ------------------------------ | --------------------------------------- | ---------------------------------------------- |
| invalid_cmd           | 不支持的命令                  | 输入错误或不支持的命令                 | 验证 `cmd` 值                                   |
| invalid_payload       | 无效的载荷格式                | 不是对象                                | 将载荷更改为对象                               |
| missing_field         | 缺少必填字段                  | 缺少 `url`、`method` 等                 | 添加必填字段                                   |
| invalid_type    | 无效字段类型        | number ↔ string confusion   | 修复字段类型                |
| invalid_value   | 无效值             | 超出枚举范围           | 使用允许的值            |

<br>

<h4 style="font-size:15px; font-weight:bold;">3. 握手错误</h4>

在握手处理期间发生的错误。

| 错误代码         | 描述                     | 典型原因                     | 客户端操作                 |
| ------------------ | ------------------------------- | --------------------------------- | ----------------------------- |
| version_mismatch   | 协议主要版本不匹配         | 客户端/服务器主要版本不同       | 使用服务器的主要版本      |
| handshake_rejected | 握手被拒绝              | 无效的会话状态             | 关闭现有会话，重试 |

<br>

<h4 style="font-size:15px; font-weight:bold;">4. 监控错误</h4>

在监控配置或执行期间发生的错误。  
这些主要在定期的REST调用验证期间发生。

| 错误代码             | 描述                         | 典型原因              | 客户端操作               |
| ---------------------- | ----------------------------------- | -------------------------- | --------------------------- |
| invalid_method         | 在监控中使用了非GET方法      | 使用了POST/PUT              | 将方法更改为GET        |
| invalid_url            | 无效的URL格式                  | 不以`/`开头，存在空格 | 遵循URL规则            |
| invalid_period         | 无效的`period_ms`范围           | 太小或太大     | 调整到允许的范围     |
| monitor_already_active | 重复的监控请求           | 已经处于活动状态             | 停止然后重试             |
| monitor_internal_error | 内部REST调用失败    | 服务器内部错误      | 检查服务器日志           |

<br>

<h4 style="font-size:15px; font-weight:bold;">5. 控制错误</h4>

在控制请求处理期间发生的错误。  
这些错误可能会根据REST执行结果报告。

| 错误代码         | 描述                    | 典型原因       | 客户端操作               |
| ------------------ | ------------------------------ | ------------------- | --------------------------- |
| control_err        | 控制执行失败      | REST 4xx/5xx        | 检查状态/正文         |
| invalid_body       | 无效的正文JSON              | 序列化错误 | 验证正文结构       |
| method_not_allowed | 方法不允许             | 使用GET等     | 使用POST/PUT/DELETE         |
| control_busy       | 控制不可用状态      | 另一个控制活动 | 稍后重试              |

{% hint style="warning" %}

控制在成功时不会返回响应。  
仅在失败时可能会返回`control_err`或通用错误消息。

{% endhint %}
<h4 style="font-size:15px; font-weight:bold;">6. 停止错误</h4>

在处理停止请求时发生的错误。

| 错误代码        | 描述                   | 典型原因          | 客户端操作                                   |
| --------------- | --------------------- | ---------------- | --------------------------------------------- |
| invalid_target  | 无效的停止目标         | 目标拼写错误     | 选择监视器 / 控制 / 会话                       |
| nothing_to_stop | 没有什么可停止的       | 已经终止         | 可以忽略                                      |
| stop_failed     | 内部清理失败          | 内部状态错误     | 建议重新连接                                  |

<br>

<h4 style="font-size:15px; font-weight:bold;">7. 错误处理指南</h4>

错误消息始终以单行NDJSON的形式接收。

建议客户端：
- 首先检查接收循环中`error`字段的存在，并在发生错误时清晰地清理会话状态（停止或重新连接）。

- 一些错误是可恢复的，而另一些可能需要重新连接（致命）。

- 根据每个错误的"客户端操作"列确定可恢复性。
[__SOURCE](5-examples/README.md)
# 5. 示例

{% hint style="info" %}

本节提供逐步示例，以帮助首次使用 Open Stream 的用户理解  
<b>如何设计客户端架构</b>。  
每个示例侧重于 <b>理解结构和控制流</b>，而不是提供完全优化或生产就绪的代码。

{% endhint %}

<h4 style="font-size:16px; font-weight:bold;">手动示例章节结构</h4>

<div style="max-width:fit-content;">

```text
5. 示例
├── 5.1 utils       # 常用工具 (发送/接收, 解析, 事件分发)
├── 5.2 handshake   # 独立的 HANDSHAKE 示例
├── 5.3 monitor     # MONITOR 流示例
├── 5.4 control     # CONTROL 一次性请求示例
└── 5.5 stop        # STOP 和优雅关闭示例
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">客户端目录结构</h4>

下面是使用 Open Stream 的客户端应用程序推荐的最小目录结构。

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py            # TCP 套接字连接和发送/接收
│   ├── parser.py         # NDJSON 流解析
│   ├── dispatcher.py     # 根据类型/错误的事件分发
│   ├── motion.py         # 生成正弦波运动
│   └── api.py            # HANDSHAKE / MONITOR / CONTROL / STOP 的包装器
│
├── scenarios/
│   ├── handshake.py      # 独立的 HANDSHAKE 场景
│   ├── monitor.py        # MONITOR 流场景
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
| 操作系统 | Linux / macOS / Windows (任何支持 TCP 套接字的环境) |
| 库 | 仅限标准库 |

</div>

- 这些示例故意最小化外部依赖  
  以便专注于理解 Open Stream 协议本身。
[__SOURCE](5-examples/1-utils.md)
## 5.1 常用工具（utils）

{% hint style="info" %}

本文件提供了 <b>Open Stream 客户端工具代码</b>  
这是在所有后续示例中常用的代码。

下面的代码是 <b>完全可运行的代码</b>，不仅仅是示例。  
您可以直接将其复制到自己的项目中并原样使用。

为了清晰和可重复性，该示例故意采用了  
<b>"接收线程 + 阻塞套接字（带超时）"</b> 模型。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">目录结构</h4>

创建如下面所示的 `utils/` 目录  
并准确复制每个文件。

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
| <b>net.py</b> | TCP 网络层 | TCP 套接字连接/断开，接收循环（线程），原始字节接收 |
| <b>parser.py</b> | NDJSON 解析器 | NDJSON 流解析，JSON 对象创建 |
| <b>dispatcher.py</b> | 消息调度器 | 基于消息 `类型 (type)` / `error` 的回调调度 |
| <b>motion.py</b> | 轨迹实用工具 | 正弦轨迹生成，文件保存/加载 |
| <b>api.py</b> | Open Stream API 封装 | HANDSHAKE / MONITOR / CONTROL / STOP 的抽象 |

</div>

<br>
<div style="max-width:fit-content;">
<h4 style="font-size:16px; font-weight:bold;">utils/net.py</h4>

本模块实现了负责TCP套接字连接和I/O的网络层。

<b>职责</b>  
(1) 创建、维护和关闭与Open Stream服务器的TCP连接。  
(2) 在接收线程中读取来自服务器的原始字节流，并通过回调(`on_bytes`)转发它们。  
(3) 将更高层（解析器/调度器）与直接的网络I/O处理解耦。

<b>关键设计点</b>  
(1) `TCP_NODELAY`（Nagle关闭）：减少小NDJSON行的延迟。  
(2) `SO_KEEPALIVE`：帮助检测半开放连接。  
(3) 基于超时的接收循环：确保在关闭或中断期间的响应性。

<b>主要API</b>  
(1) `connect()`：建立套接字连接并配置选项  
(2) `send_line(line)`：发送一行NDJSON（换行符自动附加）  
(3) `start_recv_loop(on_bytes)`：启动接收线程  
(4) `close()`：关闭连接

<details><summary>点击查看Python代码</summary>

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

此解析器将NDJSON（新行分隔JSON）流转换为  
<b>基于行的JSON对象</b>。

- <b>输入</b>: 字节块。TCP不保留消息边界，因此一个消息可能会分散在多个块之间，或者多个消息可能会合并。
- <b>输出</b>: 完成的JSON字典传递给`on_message(dict)`回调。
- <b>行为</b><br>
  (1) 在内部缓冲区中累积数据，并按`\n`拆分。  
  (2) 将每一行解码为UTF-8并通过`json.loads()`解析。  
  (3) 在JSON解析失败时，记录错误并跳过该行。

该模块标准化"原始字节"和"解析消息"之间的边界。

<details><summary>点击检查Python代码</summary>

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

该调度程序根据 <b>`类型 (type)` / `error`</b> 将解析的消息 (dict) 路由到注册的回调。

- <b>职责</b>  
  (1) 将消息处理逻辑与网络/解析器层分离。  
  (2) 示例脚本 (handshake/monitor/control) 只需将处理程序注册到调度程序。

- <b>调度规则 (当前实现)</b>  
  (1) 如果 `消息 (msg)` 包含关键字 `"error"`，则调用 `on_error(msg)`（如果未注册则打印）。  
  (2) 否则，使用 `msg.get("type")` 将消息调度到相应的 `on_type[type]` 回调。  
  (3) 如果不存在匹配的回调，则默认打印事件。

- <b>扩展点</b>  
  项目可以通过扩展 `dispatch()` 内的基于关键字的调度逻辑，明确分离 `ack` / `event` 处理。

<details><summary>点击查看 Python 代码</summary>

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
<br>
<h4 style="font-size:16px; font-weight:bold;">utils/motion.py</h4>

`motion.py` 提供 **关节轨迹生成和重用工具**  
用于 CONTROL 示例。

主要目的是通过  
<b>将轨迹生成逻辑与通信逻辑分离</b> 来保持 CONTROL 示例的专注。

- CONTROL 传输已经涉及复杂的时序和模式处理。
- 将轨迹生成混入同一个示例会使其过长。
- 因此，轨迹在 `motion.py` 中生成，而 CONTROL 示例专注于  
  "以固定间隔发送生成的点"。

角色 1. **轨迹生成（正弦波）**
- `generate_sine_trajectory(base_deg, cycle_sec, amplitude_deg, dt_sec, total_sec, active_joint_count)`
- 仅对前 N 个关节应用正弦位移以创建振荡运动。
- 返回 **基于角度的点** 的 `List[List[float]]`。

角色 2. **轨迹保存 / 加载**
- `save_trajectory(points_deg, dt_sec, base_dir="data") -> saved_path`
- `load_trajectory(path) -> (dt_sec, points_deg)`
- JSON 格式：  
  → `dt_sec`: 点之间的时间间隔（秒）  
  → `points_deg`: 关节角度点的列表

使用位置
- 在 `control.md` 场景中：
  - 读取基本姿态（弧度）→ 通过 `rad_to_deg()` 转换
  - 使用 `generate_sine_trajectory()` 生成点
  - 可选地通过 `save_trajectory()` / `load_trajectory()` 保存和重用轨迹

注意事项
- CONTROL `joint_traject_insert_point` 假设 **角度** 为 `point` 值（示例标准）。
- `dt_sec` 直接影响传输时序和 `interval/time_from_start` 设置，保存/加载时必须保持不变。

<details><summary>点击查看 Python 代码</summary>

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

该模块是一个薄包装，<b>一致构建 JSON 消息</b>  
用于 Open Stream 协议。

- <b>职责</b>  
  (1) 防止示例脚本重复编写原始 JSON 架构。  
  (2) 根据 `cmd` (握手 / 监视 / 控制 / 停止) 标准化负载结构。

- <b>重要说明</b>  
  (1) `api.py` 并不直接发送网络数据；它通过 `net.send_line()` 发送 NDJSON 行。  
  (2) CONTROL 是一个一级协议命令；`joint_traject_*` 辅助工具是轨迹控制的从属工具。

协议命令概述

| cmd | 描述 |
| --- | ----------- |
| HANDSHAKE | 会话初始化和版本协商 |
| MONITOR | 定期状态 / HTTP API 轮询 |
| CONTROL | 机器人控制（轨迹等） |
| STOP | 停止会话或流 |

提供的方法

| API 方法 | cmd | 描述 |
| ---------- | --- | ----------- |
| `handshake(major)` | HANDSHAKE | 初始化 Open Stream 会话 |
| `monitor(url, period_ms, args=None, monitor_id=1)` | MONITOR | 定期轮询目标 URL |
| `monitor_stop()` | MONITOR | 停止 MONITOR |
| `joint_traject_init()` | CONTROL | 初始化关节轨迹控制 |
| `joint_traject_insert_point(body)` | CONTROL | 发送一个轨迹点 |
| `stop(target)` | STOP | 停止会话或控制/监视 |

<details><summary>点击查看 Python 代码</summary>

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

<br>
<h4 style="font-size:16px; font-weight:bold;">关于 main.py</h4>

虽然不是 <code>utils/</code> 包的一部分，但 <code>main.py</code>  
作为所有示例场景的 <b>执行入口点</b> 起着重要作用。

<code>main.py</code> 负责：
<ul>
  <li>解析命令行参数（场景类型、主机、端口等）</li>
  <li>选择并调用相应的场景模块</li>
  <li>为所有示例提供统一的执行接口</li>
</ul>

这种分离是故意的：
<ul>
  <li><code>utils/</code> 包含 <b>可重用的、与场景无关的构建块</b></li>
  <li><code>scenarios/*.py</code> 包含 <b>逐步协议流程</b></li>
  <li><code>main.py</code> 仅协调执行，而不自己实现协议逻辑</li>
</ul>

以下各节中的每个示例假定通过 <code>main.py</code> 执行。


<br>
<h4 style="font-size:16px; font-weight:bold;">main.py（场景启动器）</h4>

<code>main.py</code> 提供一个统一的入口点，通过命令行参数运行每个示例场景。  
它解析通用选项（主机/端口/主要版本等），并调度到 <code>scenarios/</code> 下的相应模块。

<details><summary>点击查看 Python 代码</summary>
</details>



<h4 style="font-size:16px; font-weight:bold;">摘要</h4>

* 上述的 `utils` 代码在所有后续示例中 <b>保持不变地重用</b>。
* 它在 <b>仅复制和粘贴</b> 的情况下正常工作，无需修改。
* 从下一个文档开始，将使用这些工具解释  
  <b>握手 → 监控 → 控制 → 停止</b> 的逐步场景。
[__SOURCE](5-examples/2-handshake.md)
## 5.2 握手示例

此示例演示开始 Open Stream 会话所需的最基本流程。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接
2. 启动 NDJSON 接收循环（解析器 + 调度器连接）
3. 发送 握手
4. 确认收到 `handshake_ack`
5. 关闭连接

<br>
<h4 style="font-size:16px; font-weight:bold;">先决条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / api.py)
- 服务器地址和端口 (`49000`)

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，您的项目中必须存在以下文件。

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
│   └── handshake.py      # 本文档提供的场景代码
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

    # 发送 握手
    api.handshake(major=major)

    # 简短等待 ACK，然后关闭
    time.sleep(0.5)
    net.close()
```
<div style="max-width:fit-content;">
  &rightarrow; 这是一个可执行的场景，发送 HANDSHAKE 请求并验证 `handshake_ack` 的接收。
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
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[net] 连接关闭
```

- 注意：如果发生错误，将以以下格式接收  
  `{ "error": "...", "message": "...", "hint": "..." }`.
[__SOURCE](5-examples/3-monitor.md)
## 5.3 MONITOR 示例

此示例演示了在 Open Stream 会话中启动 **MONITOR 流** 的基本流程，并处理定期接收的数据。

<h4 style="font-size:16px; font-weight:bold;">执行场景</h4>

1. 建立 TCP 连接  
2. 启动 NDJSON 接收循环（解析器 + 派发器连接）  
3. 发送 MONITOR（方法 / url / period_ms / 参数）  
4. 确认收到 `monitor_ack`（或服务器定义的 ACK 类型）  
5. 处理流式 `monitor_data`  
6. 退出示例（关闭连接）

* 在实际操作中，建议在终止流时发送 `STOP target=monitor`  
（这在 STOP 示例中有说明）。

<br>
<h4 style="font-size:16px; font-weight:bold;">先决条件</h4>

* `utils/` 目录（net.py / parser.py / motion.py / dispatcher.py / api.py）  
* 服务器地址和端口（`49000`）  
* MONITOR 的目标 REST URL、`period_ms` 和 `args`

<br>
<h4 style="font-size:16px; font-weight:bold;">示例代码</h4>

要运行此示例，以下文件必须存在于您的项目中。

<div style="max-width:fit-content;">

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

    # --- 同步事件（等待确认）---
    handshake_ok = threading.Event()

    # 注册事件处理程序
    def _on_handshake_ack(m: dict) -> None:
        ok = bool(m.get("ok"))
        print(f"[ack] handshake_ack ok={ok} version={m.get('version')}")
        if ok:
            handshake_ok.set()

    dispatcher.on_type["handshake_ack"] = _on_handshake_ack

    # 监控确认 / 数据（类型名称可能因服务器实现而异）
    dispatcher.on_type["monitor_ack"] = lambda m: print(
        f"[ack] monitor_ack ok={m.get('ok')} url={m.get('url')} period_ms={m.get('period_ms')}"
    )
    dispatcher.on_type["monitor_data"] = lambda m: print(
        f"[data] {m}"
    )

    dispatcher.on_error = lambda e: print(
        f"[ERR] code={e.get('error')} message={e.get('message')} hint={e.get('hint')}"
    )

    # 连接并开始接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 1) 握手
    api.handshake(major=major)

    # 2) 等待握手确认（超时可调）
    if not handshake_ok.wait(timeout=1.0):
        print("[ERR] handshake_ack 超时；监控将不会被发送。")
        net.close()
        return

    # 3) 发送监控
    api.monitor(url=url, period_ms=period_ms, args={})

    # 简要等待以接收流，然后退出
    # （为了优雅的关闭，发送停止目标=监控，如停止示例所示）
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
[net] 连接已关闭
```

* 注意：错误以 `{ "error": "...", "message": "...", "hint": "..." }` 形式接收。  
* 注意：`monitor_data` 的有效载荷架构 (`ts`, `值 (value)`, 等) 可能会根据服务器实现而有所不同。
[__SOURCE](5-examples/4-control.md)
## 5.4 控制示例（关节轨迹）

{% hint style="info" %}

本文档提供了一个使用 Open Stream **控制** 命令向机器人**流式传输关节轨迹点**的示例。

轨迹生成和存储由 `utils/motion.py` 处理。<br>
Open Stream 消息构建和传输由 `utils/api.py` 处理。<br>
您可以将以下代码直接复制到您自己的项目中。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">前提条件</h4>

- `utils/` 目录 (net.py / parser.py / dispatcher.py / motion.py / api.py)
- Open Stream 服务器地址/端口 (例如 `192.168.1.150:49000`)
- 必须通过 HTTP 访问关节状态  
  例如 `GET http://{host}:8888/project/robot/joints/joint_states`

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

1) 建立 TCP 连接并启动接收循环  
2) 发送握手并确认 ACK  
3) 通过 HTTP GET 获取 `/project/robot/joints/joint_states`（度）  
4) 使用 `motion.generate_sine_trajectory()` 生成基于度的轨迹  
5) 发送 `CONTROL / joint_traject_init`  
6) 在 dt 间隔内重复发送 `CONTROL / joint_traject_insert_point`  
7) 退出（如有需要，请使用停止示例）
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
<h4 style="font-size:16px; font-weight:bold;">控制主体规则</h4>

建议 (

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">控制主体规则</h4>

建议 )`joint_traject_insert_point`包括以下字段。

* ( 包括以下字段。

* )`interval`(秒): 点之间的间隔 (例如 ( (秒): 点之间的间隔 (例如 )`dt_sec`)
* ()
* )`time_from_start`(秒): 从开始的时间偏移 (例如 ( (秒): 从开始的时间偏移 (例如 )`index * dt_sec`)
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* ()
  * 根据服务器实现，**省略此字段可能会导致错误**，因此建议包含它。
* )`look_ahead_time`(秒): 控制器的前瞻时间
* ( (秒): 控制器的前瞻时间
* )`point`(度): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

下面的代码是**在复制和粘贴后可直接运行的**。

<details><summary>点击查看python代码</summary>

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
    通过HTTP GET从 /project/robot/joints/joint_states 获取关节位置。

    服务器端：
    - 位置：度
    - 速度：度/秒
    - 努力：牛米
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET失败: {url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP响应不是有效的JSON: {raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[度...], "velocity":[度/秒...], "effort":[牛米...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式如 {"j1": 10.0, "j2": 20.0, ...}
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
    # 控制时机
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

    # 1) 建立TCP连接并开始接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 进行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 没有收到握手确认；正在中止。")
        net.close()
        return

    # 3) 通过HTTP获取基础关节姿势（度）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[INFO] 基础姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4) 生成关节轨迹（度）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[INFO] 轨迹已保存: {saved_path} (点数={len(points_deg)}, dt={dt_sec})")

    # 5) 初始化关节轨迹控制
    api.joint_traject_init()

    # 6) 使用控制流轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据dt调整传输速率
        target = t0 + (i + 1) * dt_sec
        remain = target - time.time()
        if remain > 0:
            time.sleep(remain)

    net.close()

</details>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">main.py 集成示例</h4>

如果您保留现有的 ( (deg): 关节角度列表

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/control.py</h4>

下面的代码是**在复制和粘贴后可以直接运行的**。

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
    - position: 度
    - velocity: deg/s
    - effort: Nm
    """
    url = f"http://{host}:{http_port}/project/robot/joints/joint_states"

    try:
        with urlopen(url, timeout=timeout_sec) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as e:
        raise RuntimeError(f"HTTP GET 失败：{url} ({e})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP 响应不是有效的 JSON：{raw[:200]!r}") from e

    q: List[float] = []

    if isinstance(data, list):
        q = [float(v) for v in data if isinstance(v, (int, float))]

    elif isinstance(data, dict):
        # 预期格式：
        # {"position":[deg...], "velocity":[deg/s...], "effort":[Nm...]}
        if "position" in data and isinstance(data["position"], list):
            q = [float(v) for v in data["position"] if isinstance(v, (int, float))]
        else:
            # 备用格式像 {"j1": 10.0, "j2": 20.0, ...}
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
        raise RuntimeError(f"无法从响应中提取关节位置：{data!r}")

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
    # 控制时序
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

    # 1）建立 TCP 连接并启动接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2）执行握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 未收到 handshake_ack；中止。")
        net.close()
        return

    # 3）通过 HTTP 获取基础关节姿态（度）
    base_deg = http_get_joint_states(host, http_port=http_port, timeout_sec=1.0)
    print(f"[信息] 基础姿态关节={len(base_deg)} 度范围={min(base_deg):.2f}..{max(base_deg):.2f}")

    # 4）生成关节轨迹（度）
    points_deg = generate_sine_trajectory(
        base_deg=base_deg,
        cycle_sec=cycle_sec,
        amplitude_deg=amplitude_deg,
        dt_sec=dt_sec,
        total_sec=total_sec,
        active_joint_count=active_joint_count,
    )

    saved_path = save_trajectory(points_deg, dt_sec, base_dir="data")
    print(f"[信息] 轨迹已保存：{saved_path} （点数={len(points_deg)}, dt={dt_sec}）")

    # 5）初始化关节轨迹控制
    api.joint_traject_init()

    # 6）使用控制流轨迹点
    t0 = time.time()
    for i, point_deg in enumerate(points_deg):
        body = {
            "interval": float(dt_sec),
            "time_from_start": float(i * dt_sec),
            "look_ahead_time": float(look_ahead_time),
            "point": [float(x) for x in point_deg],  # 度（在服务器端转换为弧度）
        }
        api.joint_traject_insert_point(body)

        # 根据 dt 调整传输速度
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

如果保持现有的`)`main.py`结构，可以调用(`)control`场景，如下所示。

<details><summary>点击检查 Python 代码</summary>

<div style="max-width:fit-content;">

```python
# main.py
import argparse

from scenarios import handshake as sc_handshake
from scenarios import monitor as sc_monitor
from scenarios import control as sc_control
from scenarios import stop as sc_stop


def main():
    p = argparse.ArgumentParser(description="Open Stream 客户端示例")

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
<h4 style="font-size:16px; font-weight:bold;">运行方法</h4>

1. 将机器人移动到参考位置。
2. ( 场景如下所示。

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
2. )`joint_traject_insert_point`API仅在播放过程中有效。  
请如实将以下等待指令添加到作业文件中。  
0001.job - ```wait di1```
3. 启动( API仅在播放过程中有效。  
请如实将以下等待指令添加到作业文件中。  
0001.job - ```wait di1```
3. 以自动模式启动)`0001.job`。
4. 以自动模式运行以下(。
4. 以自动模式运行以下)`main.py`命令。

    <div style="max-width:fit-content;">

    ```bash
    # 示例：发送一个30秒的正弦轨迹（幅度1度），dt = 2毫秒。
    # - cycle-sec=5  : 一个正弦周期（0 → 2π）对应5秒。
    # - 设定前瞻时间为0.04秒，dt为0.002秒，
    #   前瞻缓冲区大小为0.04 / 0.002 = 20个点。
    #   （跟踪可能会延迟，直到缓冲区填充20个点。）

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

输出可能会因环境而异，但您通常应该观察到以下流程。
<div style="max-width:fit-content;">

```text
[net] 连接到 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] 基础姿态 关节数=6
[INFO] 轨迹已保存: .../data/trajectory_XXXXXX.json (点数=51, dt=0.02)
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_init", ...}
[tx] {"cmd":"CONTROL",... "url":"/project/robot/trajectory/joint_traject_insert_point", ...}
...
[net] 连接已关闭
```

</div>

---

## 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储被分开成（命令。

    <div style="max-width:fit-content;">

    ```bash
    # 示例: 发送 30 秒的正弦轨迹 (振幅 1 度)，dt = 2 毫秒。
    # - cycle-sec=5  : 一个正弦周期 (0 → 2π) 对应 5 秒。
    # - 预瞻时间 = 0.04 s 和 dt = 0.002 s,
    #   预瞻缓冲区大小为 0.04 / 0.002 = 20 个点。
    #   (跟踪可能会延迟，直到缓冲区填满 20 个点。)

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

输出可能因环境而异，但您通常应观察到以下流程。

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

## 摘要

* CONTROL 是用于传输机器人控制消息的协议命令。
* 轨迹生成和存储分开到)`utils/motion.py`中，因此控制示例专注于**传输逻辑**。
* 发送时(，因此控制示例专注于**传输逻辑**。
* 发送)`joint_traject_insert_point`时，建议包含(，建议包含)`time_from_start`并基于(和基于)`dt`进行增量。
[__SOURCE](5-examples/5-stop.md)
## 5.5 停止示例（会话 / 流终止）

{% hint style="info" %}

本文档解释如何使用 Open Stream **STOP** 命令以  
受控和安全的方式优雅地终止当前运行的 **session** 或 **CONTROL / MONITOR 流**。

- STOP 是安全终止的 **强制性命令**。
- 当 CONTROL 轨迹正在传输或 MONITOR 流处于活动状态  
  并且需要立即中断时，使用 STOP。
- 下面的代码是 <b>完全有效的</b>，可以按原样复制并使用。

{% endhint %}

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP 命令概述</h4>

STOP 是用于终止 Open Stream 会话或特定流的控制命令。

- <b>立即停止</b> 机器人，或
- <b>优雅地释放</b> CONTROL / MONITOR 流。

当发送 STOP 命令时，服务器会清理其内部状态  
并在必要时释放相关资源（轨迹缓冲区、监视任务等）。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">STOP 目标</h4>

STOP 命令使用 `目标 (target)` 字段指定其终止范围。

| 目标值      | 描述                           |
|------------|------------------------------|
| `session`  | 终止整个 Open Stream 会话（推荐默认）   |
| `control`  | 仅终止 CONTROL 流            |
| `monitor`  | 仅终止 MONITOR 流            |

* 根据实现或版本，`control` 和 `monitor` 可能是可选的。  
最安全的方法是终止整个 `session`。

---

<br>
<h4 style="font-size:16px; font-weight:bold;">场景流程</h4>

(1) 建立 TCP 连接并开始接收循环  
(2) 执行握手  
(3) 发送 STOP 命令
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

以下示例发送指定目标的停止命令。

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

    # 1) 连接 + 接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 握手失败; 正在中止停止.")
        net.close()
        return

    # 3) 停止
    print(f"[INFO] 发送停止目标={target}")
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

这显示了如何根据现有的调用 STOP (

</div>

---

<br>
<h4 style="font-size:16px; font-weight:bold;">scenarios/stop.py</h4>

以下示例发送指定目标的 STOP 命令。

<details><summary>点击以检查 Python 代码</summary>

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

    # 1) 连接 + 接收循环
    net.connect()
    net.start_recv_loop(lambda b: parser.feed(b, dispatcher.dispatch))

    # 2) 握手
    api.handshake(major=major)

    t_wait = time.time() + 2.0
    while time.time() < t_wait and not handshake_ok["ok"]:
        time.sleep(0.01)

    if not handshake_ok["ok"]:
        print("[ERR] 握手失败；正在中止停止。")
        net.close()
        return

    # 3) STOP
    print(f"[INFO] 发送 STOP target={target}")
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

这显示了如何根据现有的)`main.py`场景结构调用STOP。

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

# 仅终止CONTROL
python main.py stop --host 192.168.1.150 --port 49000 --target control

# 仅终止MONITOR
python main.py stop --host 192.168.1.150 --port 49000 --target monitor
```

</div>

---
<br>
<h4 style="font-size:16px; font-weight:bold;">预期输出</h4>

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

## 摘要

* STOP 是一个用于 **安全终止** 机器人控制和监控的命令。
* 强烈建议使用 STOP 终止 CONTROL 轨迹传输。
* 最安全的默认用法是 ( 场景结构。

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
[net] connected to 192.168.1.150:49000
[tx] {"cmd":"HANDSHAKE","payload":{"major":1}}
[ack] handshake_ack ok=True version=1.0.0
[INFO] sending STOP target=session
[tx] {"cmd":"STOP","payload":{"target":"session"}}
[net] connection closed
```

</div>

---

## 概要

* STOP 是一个用于 **安全终止** 机器人控制和监控的命令。
* 强烈建议使用 STOP 终止 CONTROL 轨迹传输。
* 最安全的默认用法是 )`target=session`。

[__SOURCE](6-faq/README.md)
# 6. 常见问题解答

Q1. 为什么需要先进行握手？
A. 如果服务器不处于 `handshake_ok` 状态，它将返回 **412 (handshake_required)** 用于 MONITOR / CONTROL / STOP。

Q2. CONTROL 成功了，但没有响应。
A. 这是预期的行为。当 CONTROL 完成并返回 HTTP 200 时，响应行故意被省略（未发送）。

Q3. MONITOR 可以使用 POST 或 PUT 作为方法吗？
A. 不可以。MONITOR 负载中的 `method` 字段必须是 **"GET"**。

Q4. 如果 URL 包含空格怎么办？
A. 请求将被拒绝。URL 不得包含空格。
[__SOURCE](7-release-notes/README.md)
# 7. 发布说明

本节总结了开放流接口的版本变更历史。<br>
每个版本都记录了功能添加、行为变化、修复和兼容性说明。

<h4 style="font-size:15px; font-weight:bold;">发布信息</h4>

<div style="max-width:fit-content;">

| *版本 | ${cont_model} 版本 | 发布计划 | 链接 |
|:--:|:--:|:--:|:--:|
|1.0.0|60.34-00 ⇡|计划于2026.03|[🔗](1-0-0.md)|

----

</div>

*版本: **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| 字段 | 说明 | 兼容政策 |
|------|---------|----------------------|
| MAJOR | 基本协议变更 | **如果 MAJOR 不同则不兼容** |
| MINOR | 功能添加（向后兼容） | 如果 MAJOR 匹配则兼容 |
| PATCH | 错误修复和内部改进 | 始终兼容 |

</div>


<br>

<h4 style="font-size:15px; font-weight:bold;">发布说明类别</h4>

<div style="max-width:fit-content;">

| 类别 | 描述 |
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>✨ 添加</b></span>|新增功能、命令、字段或选项|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>🔧 更改</b></span>|对现有行为、规范或默认值的更改|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>🛠 修复</b></span>|错误修复、稳定性改进、异常行为修正|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>❌ 不推荐使用</b></span>|计划删除或不再推荐的功能|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>⚠ 注意</b></span>|重要使用说明，必须对此版本予以重视|

</div>

<br>

每个发布文档仅描述**该版本中引入的更改**，根据上述类别。<br>
有关详细的使用说明或协议描述，请参阅本文件中的相应参考部分。
如果发布引入了行为变化，它可能会影响现有系统。<br>
在更新之前，请始终查看目标版本的发布说明。
[__SOURCE](7-release-notes/1-v1-0-0.md)
## 7.1 发布说明 - v1.0.0
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
- 官方发布：2026 年 3 月（计划中）

{% endhint %}

{% hint style="info" %}

<h4 style="font-size:15px; font-weight:bold;">概述</h4>

- Open Stream 是一个基于实时流的接口，旨在用于机器人控制和状态获取。
- 此版本提供核心 Open Stream 协议、食谱命令和相关通信规则。

{% endhint %}

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid rgb(255, 140, 0);
  font-size:15px;
  font-weight:bold;
">
  ✨ 添加
</h4>

<ul>
  <li>协议
    <ul>
      <li>基于 NDJSON 的轻量级流协议</li>
      <li>通过单个 TCP 连接实现双向通信</li>
      <li>基于命令的会话管理模型</li>
    </ul>
</li>

  <li>配方命令
    <ul>
      <li>握手：协议版本协商</li>
      <li>监视：周期性状态数据流 (毫秒级间隔)</li>
      <li>控制：实时控制命令传输 (高优先级)</li>
      <li>停止：终止活跃会话或配方</li>
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
  🔧 更改
</h4>

<ul>
  <li>这是初始公开版本；与之前版本相比没有更改。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #2E7D32;
  font-size:15px;
  font-weight:bold;
">
  🛠 修复
</h4>

<ul>
  <li>这是初始公开版本；没有修复的问题。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #B71C1C;
<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #9E9E9E;
  font-size:15px;
  font-weight:bold;
">
  ❌ 已弃用
</h4>

<ul>
  <li>这是初始公共发布；没有弃用或删除的功能。</li>
</ul>

<br>

<h4 style="
  display:inline-block;
  padding:2px 8px;
  border-left:4px solid #9E9E9E;
  font-size:15px;
  font-weight:bold;
">
  ⚠ 注意
</h4>

<ul>
  <li>当 CONTROL 和 MONITOR 同时运行时，CONTROL 的实时性能优先考虑。</li>
  <li>根据操作系统调度和网络状况可能会出现周期性延迟。</li>
  <li>每个 TCP 连接只能有一个 MONITOR 会话处于活动状态。</li>
  <li>MONITOR 数据不适合实时控制决策。</li>
  <li>根据网络和客户端性能可能会出现延迟和抖动。</li>
</ul>

<br>

<h4 style="font-size:15px; font-weight:bold;">相关文档</h4>

<ul>
  <li><a href="../1-overview/README.md">开放流概述</a></li>
  <li><a href="../1-overview/2-usage-considerations.md">使用考虑</a></li>
  <li><a href="../2-protocol/README.md">协议</a></li>
  <li><a href="../3-recipe/README.md">食谱命令</a></li>
  <li><a href="../5-examples/README.md">示例</a></li>
  <li><a href="../6-faq/README.md">常见问题</a></li>
</ul>