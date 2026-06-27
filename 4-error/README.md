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