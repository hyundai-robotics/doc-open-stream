## 1.1 What is Open Stream?

Open Stream is an interface that allows clients to continuously receive results in a streaming manner  
by repeatedly invoking **${cont_model} Open APIs** at short intervals.

<br>

It provides a streaming interface through a **TCP-based lightweight server** embedded inside the ${cont_model} controller,  
enabling external clients to continuously send and receive data over a persistent connection.

<br>

Open Stream has the following characteristics:

- Maintains a **single long-lived TCP connection**
- Uses **NDJSON (Newline Delimited JSON)** for requests and responses
- Supports both **periodic data streaming (`MONITOR`)** and **immediate control commands (`CONTROL`)**
- Eliminates repeated creation of HTTP request/response cycles

<br>

Open Stream is designed for client environments that require handling  
**high-frequency control commands and status monitoring over a single connection**.

<br><br>

<b>Overall Operation Overview</b>

The basic operational flow of Open Stream is as follows.

<div style="display:flex; flex-wrap:wrap; align-items:flex-start;">

<!-- Left: Image -->
<div style="flex:1 1 420px; min-width:420px; max-width:420px;">
  <img
    src="../_assets/1-open_stream_concept.png"
    alt="Open Stream Flow"
    style="width:100%; height:auto; border-radius:6px;"
  />
</div>

<!-- Right: Ordered List -->
<div style="flex:1 1 280px; min-width:280px; max-width:fit-content;">
  <ol style="line-height:1.5;">

  <li>The client establishes a TCP connection to the server, creating a session.</li><br>

  <li>Immediately after connection, the client sends a <code>HANDSHAKE</code> command<br>
      to verify protocol version compatibility with the server.</li><br>

  <li>The server processes the <code>HANDSHAKE</code> request and, if the protocol version is compatible, sends a <code>handshake_ack</code> event.</li><br>

  <li>After a successful <code>HANDSHAKE</code>, the client may request periodic data streaming using the <code>MONITOR</code> command, or execute one-shot requests using the <code>CONTROL</code> command.
      <small>(CONTROL commands can be sent even while MONITOR is active.)</small>
  </li><br>

  <li>When <code>MONITOR</code> is active, the server sends <code>data</code> events at the configured interval, independent of additional client requests.</li><br>
    
  <li>Successful <code>CONTROL</code> commands do not generate ACK responses.<br>
      Only failures may result in <code>error</code> or <code>control_err</code> events.</li><br>

  <li>When operations are complete, the client sends a <code>STOP</code> command
      to indicate termination of active operations or session intent,
      and closes the TCP connection after receiving <code>stop_ack</code>.
  </li>

  </ol>
</div>

</div>

<br>

{% hint style="info" %}

**What is the MONITOR command?**  
The MONITOR command repeatedly invokes a single ${cont_model} Open API service at a client-defined interval  
and continuously streams the results to the client.

**What is the CONTROL command?**  
The CONTROL command is used to send one-shot control requests to the ${cont_model} Open API.  
Clients may send CONTROL commands repeatedly at short intervals as needed.

{% endhint %}

Open Stream allows MONITOR and CONTROL commands to be used together within a single TCP connection.

{% hint style="warning" %}

However, within a single connection, **only one MONITOR session and one CONTROL session** can be active at the same time.

{% endhint %}
