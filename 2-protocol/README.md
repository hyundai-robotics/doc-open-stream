# 2. Protocol

This section describes the transport protocol and message framing rules used by Open Stream.

> **Warning**
>
> Open Stream is not a request–response protocol but an **event stream**.  
> Server events (`data`, `*_ack`, `error`) may arrive at any time regardless of client requests,  
> so client logic must be implemented without relying on message ordering.

- Open Stream uses a **single-session communication model based on a TCP socket**.
- Messages exchanged between the client and server use **NDJSON (Newline Delimited JSON)**.
- Each message is sent by **serializing exactly one JSON object per line and appending `\n` at the end**.

> **Info**
>
> Due to the nature of TCP streams, a single `recv()` call may not return exactly one message.  
> Received data should be accumulated in an internal buffer and parsed by splitting on `\n`.

For detailed NDJSON rules, refer to the document below.

- [NDJSON Specification](./1-ndjson.md)
