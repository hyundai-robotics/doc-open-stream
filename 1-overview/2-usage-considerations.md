## 1.2 Usage Considerations

Open Stream is designed to efficiently handle real-time control and status monitoring.  
However, the following constraints and assumptions must be carefully considered.

- Open Stream targets periodic data delivery but does **not guarantee strict determinism**.
- Periodic jitter may occur depending on operating system scheduling, network conditions,
  and client-side processing load.
- Since Open Stream is based on Open APIs, the execution time of Open Stream may be affected by the API service processing time of the ${cont_model} controller.
- When PLC or Playback tasks are running concurrently, Open Stream execution may be delayed depending on system task priorities.
- Only **one MONITOR session** can be active per TCP connection.
- All commands must follow the defined protocol order.
  Violating the order may result in command rejection or connection termination.

<br><br>

<b>Performance Reference for MONITOR and CONTROL Operation (Test Results)</b>

The following results compare periodic behavior between MONITOR-only operation and
simultaneous CONTROL + MONITOR operation under the same test environment.

Test Environment:
- Server: ${cont_model} COM
- Client: Python client on Windows 11
- Network: TCP connection
- Send/receive period: Maximum configurable MONITOR frequency

<br>

Summary of Results

<div style="max-width:fit-content;">

1. MONITOR Only

| **Test Conditions** | **Periodic Characteristics** |
| --- | --- |
| - MONITOR period: 2 ms (500 Hz)<br>- CONTROL not used<br>- Continuous run: 10 hours | - <u><b>Average receive period: ~2.0 ms</b></u> |

2. CONTROL + MONITOR Concurrent

| **Test Conditions** | **Periodic Characteristics** |
| --- | --- |
| - CONTROL period: 2 ms<br>- MONITOR period: 2 ms<br>- CONTROL and MONITOR active simultaneously | - CONTROL (SEND): <u><b>Average period ~2.0 ms</b></u>, max delay ~30-40 ms<br>- MONITOR (RECV): <u><b>Average period ~2.1-2.2 ms</b></u>, max delay from tens of ms up to >100 ms |

</div>

<br><br>

<b>Interpretation and Operational Notes</b>

- When MONITOR is used alone, relatively stable periodic reception is possible even during long continuous operation.
- When CONTROL and MONITOR are used concurrently, CONTROL sessions are processed with higher priority depending on system design.
- As a result, CONTROL periodic stability is maintained, while MONITOR reception periods may increase and experience intermittent delays.
- Systems using both CONTROL and MONITOR must be designed assuming potential degradation and jitter in MONITOR periodicity.
