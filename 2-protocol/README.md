# 2. 프로토콜

이 섹션에서는 Open Stream이 사용하는 전송 규약(Transport)과 메시지 프레이밍 규칙을 설명합니다.

{% hint style="warning" %}

Open Stream은 요청–응답형 프로토콜이 아닌 **비동기 이벤트 스트림**입니다.  
서버 이벤트(`data`, `*_ack`, `error`)는 클라이언트 요청과 무관하게 언제든 도착할 수 있으므로,  
순서 의존 로직 없이 처리해야 합니다.

{% endhint %}

- Open Stream은 **TCP 소켓** 기반의 단일 세션 통신을 사용합니다.
- 클라이언트/서버 간 메시지는 **NDJSON(Newline Delimited JSON)** 형태로 교환합니다.
- 각 메시지는 **JSON 1개를 1줄로 직렬화한 뒤, 줄 끝에 `\n`을 붙여 전송**합니다.

{% hint style="info" %}

TCP 스트림 특성상, 한 번의 `recv()` 호출이 정확히 한 개의 메시지를 반환하지 않을 수 있습니다.  
수신 데이터는 내부 버퍼에 누적한 뒤, `\n` 기준으로 메시지를 분리하여 파싱해야 합니다.

{% endhint %}

세부 NDJSON 규칙은 아래 문서를 참고하세요.

- [NDJSON 규칙](./1-ndjson.md)
