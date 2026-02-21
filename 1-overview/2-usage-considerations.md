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