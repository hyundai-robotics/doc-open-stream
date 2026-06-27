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