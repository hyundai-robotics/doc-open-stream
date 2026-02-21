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