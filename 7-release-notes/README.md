# 7. 发行说明

本节总结了开放流接口的逐版本变更历史。<br>
每个版本记录了功能的增加、行为的变化、修复和兼容性说明。

<h4 style="font-size:15px; font-weight:bold;">发行信息</h4>

<div style="max-width:fit-content;">

| *版本 | ${cont_model} 版本 | 发行时间表 | 链接 |
|:--:|:--:|:--:|:--:|
|1.0.0|>=V70.00-00 |2026年3月|[🔗](1-v1-0-0.md)|

----

</div>

*版本: **`MAJOR.MINOR.PATCH`**

<div style="max-width:fit-content;">

| 字段 | 含义 | 兼容性政策 |
|------|---------|----------------------|
| MAJOR | 基本协议变更 | **如果 MAJOR 不同则不兼容** |
| MINOR | 功能添加（向后兼容） | 如果 MAJOR 一致则兼容 |
| PATCH | 修复bug和内部改进 | 始终兼容 |

</div>


<br>

<h4 style="font-size:15px; font-weight:bold;">发行说明类别</h4>

<div style="max-width:fit-content;">

| 分类 | 描述 |
|:--|:--|
|<span style="border-left:4px solid rgb(255,140,0); padding-left:6px;"><b>新增</b></span>|新增的功能、命令、字段或选项|
|<span style="border-left:4px solid #3F51B5; padding-left:6px;"><b>已更改</b></span>|对现有行为、规格或默认值的更改|
|<span style="border-left:4px solid #2E7D32; padding-left:6px;"><b>已修复</b></span>|修复bug、稳定性改进、异常行为纠正|
|<span style="border-left:4px solid #B71C1C; padding-left:6px;"><b>已弃用</b></span>|计划移除或不再推荐的功能|
|<span style="border-left:4px solid #9E9E9E; padding-left:6px;"><b>注意</b></span>|必须确认的重要使用说明|

</div>

<br>

每个发行文档仅描述 **该版本中引入的更改**，按照上述类别。<br>
有关详细的使用说明或协议描述，请参考本文档中相应的参考部分。

如果一个发行版引入了行为上的更改，可能会影响现有系统。<br>
在更新之前，请始终查看目标版本的发行说明。