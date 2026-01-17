## 3.2 MONITOR

클라이언트가 지정한 REST **GET** 서비스를 주기적으로 호출하고,  
그 결과를 NDJSON 단일 라인 형태로 스트리밍하기 위한 명령입니다.

- 현재 구현에서는 **세션당 하나의 MONITOR만 유지**됩니다.
- 새로운 `MONITOR` 명령이 들어오면, 기존 모니터 세션은 자동으로 폐기되고 새 세션으로 교체됩니다.
- `MONITOR`는 반드시 **HANDSHAKE 성공 이후**에만 사용할 수 있습니다.<br>
  &rightarrow; HANDSHAKE 이전에 호출하면 `handshake_required` 에러가 반환됩니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json
{"cmd":"MONITOR","payload":{"method":"GET","period_ms":2,"url":"/project/robot/joints/joint_states","args":{"jno_start":1,"jno_n":6}}}\n
````

</div>

<div style="max-width:fit-content;">

| Payload Field | Required | Type   | Rules                           |
| ----------- | -------- | ------ | ------------------------------- |
| `url`       | Yes      | string | `/`로 시작, 공백 불가, 최대 길이 2048      |
| `method`    | Yes      | string | `"GET"`만 허용                     |
| `period_ms` | Yes      | int    | 2 ~ 30000 (ms), 범위를 벗어나면 자동 클램프 |
| `args`      | No       | object | 쿼리 파라미터용 객체 (JSON object만 허용)   |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>ACK</i></u></b>)</h4>

<div style="max-width:fit-content;">

```json
{"type":"monitor_ack"}\n
```

</div>

* `monitor_ack` 는 MONITOR 요청이 수락되었음을 의미합니다.
* `monitor_ack` 와 첫 `data` 이벤트의 **도착 순서는 보장되지 않습니다.**

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success (<b><u><i>Streaming</i></u></b>)</h4>

MONITOR가 활성화되면 서버는 지정된 주기(`period_ms`)에 따라
REST API(GET)를 반복 호출하고, 그 결과를 `data` 이벤트로 전송합니다.

<div style="max-width:fit-content;">

```json
{"type":"data","ts":402,"svc_dur_ms":2.960000,"result":{"_type":"JObject","position":[0.0,90.0,0.0,0.0,-90.0,0.0],"effort":[-0.0,98.923641,94.599385,-0.110933,-5.895076,0.0],"velocity":[-0.0,-0.0,0.0,0.0,-0.0,0.0]}}\n
```

</div>

<div style="max-width:fit-content;">

| Response Field | Type | Description |
|------|------|-------------|
| `type` | string | 이벤트 타입 (`data`) |
| `ts` | number | 서버 기준 타임스탬프 (ms) |
| `svc_dur_ms` | number | REST 호출 및 처리에 소요된 시간 (ms) |
| `result` | any | REST 응답 본문 (본문이 존재하는 경우) |
| `status` | number | REST 응답 본문이 비어 있는 경우 반환되는 HTTP 상태 코드 |

</div>


<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

모든 에러 응답은 공통 NDJSON 에러 스키마를 따릅니다.

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Error Codes</h4>

<div style="max-width:fit-content;">

| Error Code           | HTTP Status | Description   | When it occurs           |
| -------------------- | ----------- | ------------- | ------------------------ |
| `handshake_required` | 412         | HANDSHAKE 미수행 | HANDSHAKE 이전에 MONITOR 호출 |
| `missing_url`        | 400         | 필수 필드 누락      | `url` 키가 없음              |
| `invalid_url`        | 400         | URL 형식 오류     | `/`로 시작하지 않거나 공백 포함      |
| `url_too_long`       | 400         | URL 길이 초과     | URL 길이가 2048 초과          |
| `missing_method`     | 400         | 필수 필드 누락      | `method` 키가 없음           |
| `invalid_method`     | 400         | 메서드 오류        | `"GET"`이 아님              |
| `missing_period_ms`  | 400         | 필수 필드 누락      | `period_ms` 키가 없음        |
| `invalid_period`     | 400         | 타입 오류         | `period_ms`가 int가 아님     |
| `invalid_args`       | 400         | 타입 오류         | `args`가 object가 아님       |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4>

<div style="max-width:fit-content;">

| Field       | Attribute | Type   | Validation Rule      | Error Code                            |
| ----------- | --------- | ------ | -------------------- | ------------------------------------- |
| `url`       | 필수        | string | payload에 반드시 존재      | `missing_url`                         |
| `url`       | 형식        | string | `/`로 시작, 공백 불가       | `invalid_url`                         |
| `url`       | 길이        | string | 최대 2048              | `url_too_long`                        |
| `method`    | 필수        | string | 반드시 `"GET"`          | `missing_method`, `invalid_method`    |
| `period_ms` | 필수        | int    | int 타입               | `missing_period_ms`, `invalid_period` |
| `period_ms` | 범위        | int    | 2~30000, 범위 초과 시 클램프 | -                                     |
| `args`      | 타입        | object | JSON object만 허용      | `invalid_args`                        |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Watchdog Behavior</h4>

* MONITOR가 활성화되면 워치독은 **ARM 상태**로 전환됩니다.
* 이 상태에서는 세션 유휴 시간 제한이 기존 **180초 → 5초**로 줄어듭니다.
* 모니터링 도중 TCP 연결이 끊기거나,
  일정 시간 동안 서버 측으로 유의미한 명령어를 호출하지 않는 경우  
  워치독이 이를 감지하고 세션을 자동으로 정리합니다.

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

* MONITOR는 서버 주도형 스트리밍 메커니즘입니다.
* `monitor_ack` 수신 여부와 관계없이 `data` 이벤트는 언제든 도착할 수 있습니다.
* 클라이언트는 항상 수신 루프를 유지하고, `type` 기반으로 이벤트를 처리해야 합니다.