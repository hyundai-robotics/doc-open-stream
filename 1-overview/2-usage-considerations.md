## 1.2 使用注意事项

Open Stream 旨在高效处理实时控制和状态监控。  
然而，以下限制和假设必须仔细考虑。

- Open Stream 针对周期性数据传输，但不 **保证严格确定性**。
- 可能会因操作系统调度、网络条件以及客户端处理负载而出现周期性抖动。
- 由于 Open Stream 基于 Open APIs，Open Stream 的执行时间可能受到 ${cont_model} 控制器的 API 服务处理时间的影响。
- 当 PLC 或播放任务同时运行时，Open Stream 执行可能会因系统任务优先级而延迟。
- 每个 TCP 连接只能有 **一个 MONITOR 会话** 处于激活状态。
- 所有命令必须遵循定义的协议顺序。
  违反顺序可能导致命令被拒绝或连接终止。

<br><br>

<b>MONITOR 和 CONTROL 操作的性能参考 （测试结果）</b>

以下结果比较了在相同测试环境下 MONITOR 单独操作和同时进行 CONTROL + MONITOR 操作的周期性行为。

测试环境：
- 服务器: ${cont_model} COM
- 客户端: Windows 11 上的 Python 客户端
- 网络: TCP 连接
- 发送/接收周期: 最大可配置的 MONITOR 频率

<br>

结果总结

<div style="max-width:fit-content;">

1. 仅 MONITOR

| **测试条件** | **周期性特征** |
| --- | --- |
| - MONITOR 周期: 2 ms (500 Hz)<br>- 未使用 CONTROL<br>- 持续运行: 10 小时 | - <u><b>平均接收周期: ~2.0 ms</b></u> |

2. CONTROL + MONITOR 并发

| **测试条件** | **周期性特征** |
| --- | --- |
| - CONTROL 周期: 2 ms<br>- MONITOR 周期: 2 ms<br>- CONTROL 和 MONITOR 同时激活 | - CONTROL (发送): <u><b>平均周期 ~2.0 ms</b></u>, 最大延迟 ~30-40 ms<br>- MONITOR (接收): <u><b>平均周期 ~2.1-2.2 ms</b></u>, 最大延迟从数十毫秒到 >100 毫秒 |

</div>

<br><br>

<b>解读与操作注意事项</b>

- 当单独使用 MONITOR 时，即使在长时间的连续操作中，也可以实现相对稳定的周期性接收。
- 当 CONTROL 和 MONITOR 同时使用时，根据系统设计，CONTROL 会话优先级较高。
- 结果是，CONTROL 周期稳定性得以维持，而 MONITOR 接收周期可能会增加并经历间歇性延迟。
- 同时使用 CONTROL 和 MONITOR 的系统必须设计为假设 MONITOR 周期性可能严重下降和抖动。