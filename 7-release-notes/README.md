# 7. 发布说明

本节总结了开放流接口的版本变更历史。<br>
每个版本都记录了功能添加、行为变化、修复和兼容性说明。

<h4 style="font-size:15px; font-weight:bold;">发布信息</h4>

<div style="max-width:fit-content;">

| *版本 | ${cont_model} 版本 | 发布计划 | 链接 |
|:--:|:--:|:--:|:--:|
|1.0.0|60.34-00 ⇡|计划于2026.03|[🔗](1-0-0.md)|

----

</div>

*版本: **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| 字段 | 说明 | 兼容政策 |
|------|---------|----------------------|
| MAJOR | 基本协议变更 | **如果 MAJOR 不同则不兼容** |
| MINOR | 功能添加（向后兼容） | 如果 MAJOR 匹配则兼容 |
| PATCH | 错误修复和内部改进 | 始终兼容 |

</div>


<br>

<h4 style="font-size:15px; font-weight:bold;">发布说明类别</h4>

<div style="max-width:fit-content;">

| 类别 | 描述 |
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>✨ 添加</b></span>|新增功能、命令、字段或选项|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>🔧 更改</b></span>|对现有行为、规范或默认值的更改|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>🛠 修复</b></span>|错误修复、稳定性改进、异常行为修正|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>❌ 不推荐使用</b></span>|计划删除或不再推荐的功能|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>⚠ 注意</b></span>|重要使用说明，必须对此版本予以重视|

</div>

<br>

每个发布文档仅描述**该版本中引入的更改**，根据上述类别。<br>
有关详细的使用说明或协议描述，请参阅本文件中的相应参考部分。
如果发布引入了行为变化，它可能会影响现有系统。<br>
在更新之前，请始终查看目标版本的发布说明。