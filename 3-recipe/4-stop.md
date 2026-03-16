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