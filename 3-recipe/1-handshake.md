## 3.1 HANDSHAKE

세션 시작 직후 수행하는 **프로토콜 버전 협상** 단계입니다.  
`HANDSHAKE` 이전에 `MONITOR`/`CONTROL`을 호출하면 서버가 거부할 수 있습니다.



<br>
<h4 style="font-size:16px; font-weight:bold;">Request</h4>

<div style="max-width:fit-content;">

```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

</div>

<div style="max-width:fit-content;">

| Payload Field   | Required | Type | Rules    |
| ------- | -------- | ---- | -------- |
| `major` | Yes      | int  | 0 이상의 정수 |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Success</h4>

<div style="max-width:fit-content;">

```json
{"type":"handshake_ack","ok":true,"version":"1.0.0"}\n
```

| Key       | Type    | Required | Description                                                    |
| --------- | ------- | -------: | -------------------------------------------------------------- |
| `ok`      | boolean |       No | 일부 ACK에서 성공 여부를 명시 (`handshake_ack` 등)                         |
| `version` | string  |       No | 서버 프로토콜 버전 (`MAJOR.MINOR.PATCH`)                               |


</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Response - Error</h4>

<div style="max-width:fit-content;">

```json
{"error":"<code>","message":"<msg>","hint":"<optional hint>"}\n
```

</div>
<br> <h4 style="font-size:16px; font-weight:bold;">Error Codes</h4> <div style="max-width:fit-content;">
<div style="max-width:fit-content;">

| Error Code            | HTTP Status | Description       | When it occurs                           |
| --------------------- | ----------- | ----------------- | ---------------------------------------- |
| `busy_session_active` | 409         | 이미 활성화된 작업이 존재함   | CONTROL 또는 MONITOR 태스크 수행 중 HANDSHAKE 요청 |
| `version_mismatch`    | 400         | 프로토콜 MAJOR 버전 불일치 | 클라이언트 `major` 값이 서버 MAJOR와 다름            |
| `missing_major`       | 400         | 필수 필드 누락          | payload에 `major` 키가 없음                   |
| `invalid_major_type`  | 400         | 타입 오류             | `major`가 number(int)가 아님                 |
| `invalid_version`     | 400         | 값 범위 오류           | `major` 값이 음수                            |
</div>

<br> <h4 style="font-size:16px; font-weight:bold;">Payload Validation Rules</h4> 

<div style="max-width:fit-content;">

| Field   | Attribute | Type | Validation Rule     | Error Code           |
| ------- | --------- | ---- | ------------------- | -------------------- |
| `major` | 필수        | int  | payload에 반드시 존재해야 함 | `missing_major`      |
| `major` | 타입        | int  | number 타입이어야 함      | `invalid_major_type` |
| `major` | 범위        | int  | 0 이상의 정수            | `invalid_version`    |

</div>

<br>
<h4 style="font-size:16px; font-weight:bold;">Note</h4>

- 서버는 MAJOR 버전만 검사합니다.
- MINOR / PATCH 변경은 기존 클라이언트와의 호환성을 깨지 않습니다.
- 버전 정책 관련 내용은 [릴리즈 노트 페이지](../10-release-notes/README.md)를 확인하십시오.

</div>