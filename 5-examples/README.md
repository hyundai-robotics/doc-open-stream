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