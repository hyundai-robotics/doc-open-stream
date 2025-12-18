# Hi6 Open Stream

{% hint style="warning" %}

본 제품 매뉴얼에 제공된 정보는 **현대 로보틱스(Hyundai Robotics)**의 자산입니다.

본 매뉴얼은 현대 로보틱스의 사전 서면 동의 없이, 전체 또는 일부를 복제하거나 재배포할 수 없으며, 제3자에게 제공하거나 다른 목적으로 사용할 수 없습니다.

본 매뉴얼의 내용은 사전 예고 없이 변경될 수 있습니다.


**Copyright ⓒ 2025 by HD Hyundai Robotics**


{% endhint %}

{% hint style="warning" %}

Hi6 Open Stream 매뉴얼에 공식적으로 명시되지 않은 API를 사용함으로써 발생하는 어떠한 손해나 문제에 대해서도 당사는 책임을 지지 않습니다.

{% endhint %}# 0. 개요

본 문서는 Open Stream을 사용하는 외부 클라이언트를 위한 사용 매뉴얼입니다.<br>
Open Stream의 목적, 기본 개념, 전체 동작 구조와 지원되는 사용 시나리오를 설명합니다.

<br>

이 문서를 통해 사용자는

- Open Stream이 어떤 문제를 해결하는지
- 어떤 방식으로 동작하는지
- 어떤 상황에서 사용하는 것이 적절한지

를 이해할 수 있습니다.## 0.1 Open Stream이란?

해당 기능은 ${cont_model} Open API를 짧은 주기로 반복 호출하여,  
클라이언트가 그 결과를 스트리밍 형태로 지속적으로 수신할 수 있도록 제공되는 인터페이스입니다.

<br>

${cont_model} 제어기 내부의 TCP 기반의 경량 서버를 통해  
외부 클라이언트가 서버와 데이터를 연속적으로 송수신할 수 있도록  
제공되는 스트리밍 인터페이스입니다.

<br>

Open Stream은 다음과 같은 특징을 가집니다.

- 하나의 TCP 연결을 장시간 유지합니다
- 요청과 응답은 NDJSON(Newline Delimited JSON) 형식을 사용합니다
- 주기적인 데이터 송신(`MONITOR`)과 즉시성 제어 명령(`CONTROL`)을 동시에 지원합니다
- HTTP 요청/응답을 반복적으로 생성하지 않습니다

<br>

Open Stream은 짧은 주기로 제어 명령과 상태 수신을 하나의 연결에서 처리해야 하는  
클라이언트 환경을 위해 설계되었습니다.

<br>

## 0.2 전체 동작 개요

Open Stream의 기본 동작 흐름은 다음과 같습니다.

<div style="display:flex; gap:24px; align-items:center;">
  <div style="flex:0 0 190px;">
    <img src="../_assets/image.png"
         alt="Open Stream Flow"
         style="width:100%; height:auto; border-radius:6px;" />
  </div>

  <div style="flex:1;">
    <ol>
      <li>클라이언트가 서버에 TCP로 접속합니다</li>
      <li>클라이언트가 HANDSHAKE 명령을 송신합니다</li>
      <li>서버가 프로토콜 버전을 확인합니다</li>
      <li>클라이언트가 MONITOR* 또는 CONTROL* 명령을 송신합니다</li>
      <li>서버가 주기 데이터 또는 처리 결과를 송신합니다</li>
      <li>필요 시 STOP 명령으로 동작을 종료합니다</li>
    </ol>
  </div>
</div>
<br>

{% hint style="info" %}

MONITOR 명령이란? 클라이언트가 지정한 하나의 ${cont_model} Open API 서비스 함수를 짧은 주기로 반복 호출하여,
그 결과를 스트리밍 형태로 지속적으로 수신합니다.

CONTROL 명령이란? 클라이언트가 ${cont_model} Open API를 통해 단발성 제어 요청을 전달하기 위한 명령입니다. 클라이언트는 필요에 따라 짧은 주기로 반복 송신할 수 있습니다.

{% endhint %}

Open Stream은 하나의 TCP 연결 내에서  
MONITOR와 CONTROL 명령을 함께 사용할 수 있습니다.

{% hint style="warning" %}

단, 하나의 연결에서는 하나의 MONITOR 세션, 하나의 CONTROL 세션만 활성화할 수 있습니다.

{% endhint %}

<br>

## 0.3 사용 전 유의 사항

- Open Stream은 하드 리얼타임을 보장하지 않습니다
- 운영체제 및 네트워크 환경에 따라 주기 지연이 발생할 수 있습니다
- 하나의 TCP 연결에서는 하나의 MONITOR 세션만 활성화할 수 있습니다
- 모든 명령은 지정된 순서를 따라야 합니다
# 1. Protocol

이 장은 전송(Transport), NDJSON 프레이밍, 제한(Limits), 에러 모델을 정의합니다.# 2. Recipe Commands

이 장은 HANDSHAKE / MONITOR / CONTROL / STOP의 payload 규격과 동작을 정의합니다.# 2.1 HANDSHAKE

## Request
```json 
{"cmd":"HANDSHAKE","payload":{"major":1}}\n
```

- major: number(정수), 필수, 0 이상

## Response (success)
```json
{"type":"handshake_ack","ok":true,"version":"<server_version>"}\n
```

## Errors
- busy_session_active (409): CONTROL 또는 MONITOR가 active면 HANDSHAKE 불가
- version_mismatch (400): major 불일치
# 2.2 MONITOR

MONITOR는 서버가 주기적으로 REST GET을 호출하고, 그 결과를 NDJSON으로 스트리밍하는 기능입니다.

## Request

```json
{"cmd":"MONITOR","payload":{"period_ms":10,"method":"GET","url":"/project/robot","args":{}}}\n
```

### payload fields
- period_ms: number, 필수 (2~30000 범위 보정)
- method: string, 필수, 반드시 "GET"
- url: string, 필수
  - '/'로 시작
  - 공백 불가
  - 최대 2048
- args: object, 옵션(있으면 object여야 함)

## Response (ack)

```json
{"type":"monitor_ack"}\n
```

## Stream data
MONITOR가 활성화되면 서버는 주기마다 NDJSON 라인을 전송합니다.  
(데이터 라인의 정확한 스키마는 “해당 url의 REST 응답 스키마”에 의해 결정됩니다.)
# 2.3 CONTROL

CONTROL은 REST API를 단발로 호출하는 제어 커맨드입니다.

## Request

```json
{"cmd":"CONTROL","payload":{"method":"POST","url":"/robot/start","args":{},"body":{"speed":10}}}\n
```

### payload fields
- method: string, 필수, POST|PUT|DELETE 중 하나
- url: string, 필수 (MONITOR와 동일 규칙)
- args: object, 옵션(있으면 object)
- body: object|array, 옵션(없으면 {}로 처리)

## Response
- 성공(HTTP 200) 시: **응답 바디를 보내지 않습니다. (no response line)**
- 실패 시:
{"type":"control_err","status":<http_status>,"body":<optional_json>}\n
# 2.4 STOP

STOP은 대상(target)에 따라 monitor/control/session을 중단합니다.

## Request

```json
{"cmd":"STOP","payload":{"target":"monitor"}}\n
```

- target: string 필수
  - "session": TCP 세션 종료
  - "control": control 상태 리셋
  - "monitor": monitor 중지

## Response (ack)

```json
{"type":"stop_ack","target":"session|control|monitor"}\n
```
# 9. FAQ

## Q1. 왜 HANDSHAKE를 먼저 해야 하나요?
A. 서버는 handshake_ok 상태가 아니면 MONITOR/CONTROL/STOP에 대해 412(handshake_required)를 반환합니다.

## Q2. CONTROL 성공인데 응답이 없어요.
A. 정상입니다. CONTROL이 HTTP 200이면 응답 라인을 비워 “전송하지 않음”으로 처리합니다.

## Q3. MONITOR method는 POST/PUT이 가능한가요?
A. 불가합니다. MONITOR payload의 method는 반드시 "GET" 이어야 합니다.

## Q4. url에 공백이 있으면?
A. 거부됩니다. url은 공백을 포함할 수 없습니다.
