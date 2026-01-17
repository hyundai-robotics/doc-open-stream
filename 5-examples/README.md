# 5. Examples

{% hint style="info" %}

This section provides step-by-step examples to help first-time Open Stream users understand  
<b>how to design the client-side architecture</b>.  
Each example focuses on <b>understanding structure and control flow</b> rather than providing fully optimized or production-ready code.

{% endhint %}

<h4 style="font-size:16px; font-weight:bold;">Manual Example Section Structure</h4>

<div style="max-width:fit-content;">

```text
5. Examples
├── 5.1 utils       # Common utilities (send/receive, parsing, event dispatch)
├── 5.2 handshake   # Standalone HANDSHAKE example
├── 5.3 monitor     # MONITOR streaming example
├── 5.4 control     # CONTROL one-shot request example
└── 5.5 stop        # STOP and graceful shutdown example
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Client Directory Structure</h4>

Below is a recommended minimal directory structure  
for a client application that uses Open Stream.

<div style="max-width:fit-content;">

```text
OpenStreamClient/
├── utils/
│   ├── net.py            # TCP socket connection and send/receive
│   ├── parser.py         # NDJSON stream parsing
│   ├── dispatcher.py     # Event dispatch based on type / error
│   ├── motion.py         # Generating sine wave motion
│   └── api.py            # Wrappers for HANDSHAKE / MONITOR / CONTROL / STOP
│
├── scenarios/
│   ├── handshake.py      # Standalone HANDSHAKE scenario
│   ├── monitor.py        # MONITOR streaming scenario
│   ├── control.py        # CONTROL one-shot request scenario
│   └── stop.py           # STOP and graceful shutdown scenario
│
└── main.py               # Client entry point
```
</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Execution Environment</h4>

<div style="max-width:fit-content;">

| Item | Description |
| ---- | ----------- |
| Language | Python 3.8.0 |
| OS | Linux / macOS / Windows (any environment supporting TCP sockets) |
| Libraries | Standard library only |

</div>

- These examples intentionally minimize external dependencies  
  to focus on understanding the Open Stream protocol itself.
