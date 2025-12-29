# 4. 에러 코드

이 문서는 Open Stream 서버가 반환할 수 있는 **에러 코드(error code)** 와 그 의미를 설명합니다.

에러는 일반적으로 다음과 같은 **NDJSON 단일 라인 메시지** 형태로 전달됩니다.

<div style="max-width: fit-content;">

```json
{"error":"<error_code>","message":"...","hint":"..."}
```

| Field   | Description            |
| ------- | ---------------------- |
| error   | 기계 판독용 에러 코드           |
| message | 사람이 읽을 수 있는 간단한 설명     |
| hint    | 선택 필드. 문제 해결을 위한 추가 힌트 |

- (주의) 모든 에러가 `hint` 필드를 포함하는 것은 아닙니다.

</div>

<br>

<div style="max-width: fit-content;">

<h4 style="font-size:15px; font-weight:bold;">1. Protocol / Session Errors</h4>

프로토콜 파싱, 세션 상태, 초기 절차 위반 시 발생하는 에러입니다.  

| Error Code          | Description   | Typical Cause         | Client Action         |
| ------------------- | ------------- | --------------------- | --------------------- |
| invalid_ndjson      | NDJSON 파싱 실패  | JSON 깨짐, 개행(`\n`) 누락  | JSON 1줄 + 개행 규칙 준수    |
| rx_buf_overflow     | 수신 버퍼 초과      | 너무 큰 메시지 또는 과도한 burst | 메시지 크기 축소, 전송 rate 제한 |
| handshake_required  | HANDSHAKE 미수행 | 초기 핸드셰이크 누락           | 연결 직후 HANDSHAKE 수행    |
| version_mismatch    | 프로토콜 버전 불일치   | major 값 불일치           | 서버 MAJOR에 맞게 수정       |
| busy_session_active | 세션이 이미 사용 중   | MONITOR/CONTROL 활성 상태 | STOP 후 재시도            |
| session_timeout     | 세션 유휴 타임아웃    | watchdog 시간 초과        | 주기적 활동 유지 또는 재연결      |

<br>

<h4 style="font-size:15px; font-weight:bold;">2. Command / Payload Validation Errors</h4>

요청 메시지 구조 또는 필드 검증 단계에서 발생하는 에러입니다.  

| Error Code      | Description   | Typical Cause      | Client Action       |
| --------------- | ------------- | ------------------ | ------------------- |
| invalid_cmd     | 지원하지 않는 cmd   | 오타 또는 미지원 명령       | cmd 값 확인            |
| invalid_payload | payload 형식 오류 | object 아님          | payload를 object로 수정 |
| missing_field   | 필수 필드 누락      | url, method 등 누락   | 필수 필드 추가            |
| invalid_type    | 필드 타입 오류      | number ↔ string 혼동 | 타입 수정               |
| invalid_value   | 허용되지 않은 값     | enum 범위 벗어남        | 허용 값 사용             |

<br>

<h4 style="font-size:15px; font-weight:bold;">3. HANDSHAKE Errors</h4>

HANDSHAKE 처리 중 발생하는 에러입니다.

| Error Code         | Description    | Typical Cause          | Client Action  |
| ------------------ | -------------- | ---------------------- | -------------- |
| version_mismatch   | 프로토콜 MAJOR 불일치 | client/server major 다름 | 서버 기준 major 사용 |
| handshake_rejected | 핸드셰이크 거부       | 세션 상태 부적합              | 기존 세션 종료 후 재시도 |

<br>

<h4 style="font-size:15px; font-weight:bold;">4. MONITOR Errors</h4>

MONITOR 설정 또는 실행 중 발생하는 에러입니다.  
주기적 REST 호출 설정 검증 단계에서 주로 발생합니다.

| Error Code             | Description        | Typical Cause  | Client Action    |
| ---------------------- | ------------------ | -------------- | ---------------- |
| invalid_method         | MONITOR에서 GET 외 사용 | POST/PUT 사용    | method를 GET으로 수정 |
| invalid_url            | url 형식 오류          | `/` 미시작, 공백 포함 | url 규칙 준수        |
| invalid_period         | period_ms 범위 오류    | 너무 작거나 큼       | 허용 범위로 조정        |
| monitor_already_active | MONITOR 중복 요청      | 이미 활성 상태       | STOP 후 재요청       |
| monitor_internal_error | 내부 REST 호출 실패      | 내부 서버 오류       | 서버 로그 확인         |

<br>

<h4 style="font-size:15px; font-weight:bold;">5. CONTROL Errors</h4>

CONTROL 요청 처리 중 발생하는 에러입니다.  
REST 명령 실행 결과에 따라 동기 또는 비동기로 보고될 수 있습니다.

| Error Code         | Description    | Typical Cause | Client Action      |
| ------------------ | -------------- | ------------- | ------------------ |
| control_err        | CONTROL 실행 실패  | REST 4xx/5xx  | status/body 확인     |
| invalid_body       | body JSON 오류   | 직렬화 실패        | body 구조 점검         |
| method_not_allowed | 허용되지 않은 method | GET 사용 등      | POST/PUT/DELETE 사용 |
| control_busy       | 제어 불가 상태       | 다른 제어 수행 중    | 잠시 후 재시도           |

{% hint style="warning" %}

CONTROL은 성공 시 응답이 없습니다.  
실패 시에만 control_err 또는 공통 에러 메시지가 전달될 수 있습니다.

{% endhint %}

<br>

<h4 style="font-size:15px; font-weight:bold;">6. STOP Errors</h4>

STOP 요청 처리 중 발생하는 에러입니다.

| Error Code      | Description | Typical Cause | Client Action                    |
| --------------- | ----------- | ------------- | -------------------------------- |
| invalid_target  | STOP 대상 오류  | target 오타     | monitor / control / session 중 선택 |
| nothing_to_stop | 중지할 대상 없음   | 이미 종료됨        | 무시 가능                            |
| stop_failed     | 내부 정리 실패    | 내부 상태 오류      | 재연결 권장                           |

<br>

<h4 style="font-size:15px; font-weight:bold;">7. Error Handling Guidelines</h4>

에러 메시지는 항상 NDJSON 단일 라인으로 수신됩니다.

클라이언트는
- 수신 루프에서 error 필드 존재 여부를 먼저 검사하고  
에러 발생 시 세션 상태를 명확히 정리(STOP 또는 재연결) 하는 것을 권장합니다.

- 일부 에러는 복구 가능(recoverable) 하며, 일부는 재연결이 필요(fatal) 할 수 있습니다.

- 복구 가능 여부는 각 에러의 "Client Action"을 기준으로 판단하십시오.

</div>