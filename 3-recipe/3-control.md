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