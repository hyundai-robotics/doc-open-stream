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