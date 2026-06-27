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