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