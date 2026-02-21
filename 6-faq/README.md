# 6. 常见问题解答

Q1. 为什么需要先进行握手？
A. 如果服务器不处于 `handshake_ok` 状态，它将返回 **412 (handshake_required)** 用于 MONITOR / CONTROL / STOP。

Q2. CONTROL 成功了，但没有响应。
A. 这是预期的行为。当 CONTROL 完成并返回 HTTP 200 时，响应行故意被省略（未发送）。

Q3. MONITOR 可以使用 POST 或 PUT 作为方法吗？
A. 不可以。MONITOR 负载中的 `method` 字段必须是 **"GET"**。

Q4. 如果 URL 包含空格怎么办？
A. 请求将被拒绝。URL 不得包含空格。