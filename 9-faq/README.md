# 9. FAQ

Q1. Why is HANDSHAKE required first?
A. If the server is not in the `handshake_ok` state, it returns **412 (handshake_required)** for MONITOR / CONTROL / STOP.

Q2. CONTROL succeeded, but there is no response.
A. This is expected behavior. When CONTROL completes with HTTP 200, the response line is intentionally omitted (not sent).

Q3. Can MONITOR use POST or PUT as the method?
A. No. The `method` field in the MONITOR payload must be **"GET"**.

Q4. What if the URL contains spaces?
A. The request is rejected. URLs must not contain spaces.
