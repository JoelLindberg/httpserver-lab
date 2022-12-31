# HTTP Server #

**What:** A study of HTTP/1.1 by implementing it as a simple server

**Goal:** Serve a standard "GET / HTTP/1.1" request from Firefox and Chrome

**Why and how:** Experiment to learn more about the transport (tcp) and application protocols (http) as it's so widely used today (and growing). I decided to approach this with a reverse engineering mindset while also looking at any protocol documentation that can be found. Using tools such as netcat/telnet, network trace (tcpdump/wireshark) and my own custom tcp client to create dummy requests during development leading up to the final goal.

* Learn more about the TCP/IP stack
* Learn about the HTTP protocol by implementing a simple HTTP server
* Learn about concurrency (processes, threads, async)
  - Learn about basic differences to be able to pick the most suitable alternative for my case

Tasks:
 - [x] TCP server
 - [x] Handle connections concurrently
   - Persistence in each connection is expected by HTTP/1.1
 - [ ] HTTP/1.1 responses
   - Make sure to add appropriate header information for the connection to persist until the client is satisfied.
   - Respond only to the absolut minimum amount of request and header information. Just enough for the browser to be satisfied when browsing the url.
 - [ ] Serve a standard "GET / HTTP/1.1" request from Firefox and Chrome

![Flow](https://github.com/joellindberg/httpserver-lab/raw/main/diagrams/httpserver-lab.png)

<br />
<br />

## HTTP/1.1 ##

### TCP server ###

Requirements for the **TCP server** to fulfil in order to successfully serve a HTTP/1.1 request.

1. Listen for and establish a TCP connection.<br />
The connection is handled at the transport layer (reference the TCP/IP and OSI model).

       Keep in mind that in HTTP 1.0 a new connection is opened for each HTTP request unless the client explicitly requests persistence by adding "Connection: keep-alive" in the request header. We will be implementing HTTP/1.1, which expects persistence by default, so we will not be checking for "Connection: keep-alive" in the header. Our program's default behaviour will be persistence but we will listen to "Connection: close" which will signal to close the connection.
       
       In versions newer than 1.1 persistence is also the default behavior. A more broad definition of this is behavior called multiplexing. 

2. Handle the TCP connection in a persistent manner.<br />
Handle each request/response pair concurrently.<br />
Header information is used to communicate when the exchange is complete and when the connection should be closed.

3. Make sure the TCP connection is properly closed.<br />
Give the client what it needs to be satisfied with the response so that it sends a FIN TCP flag when it's done. This can be done by making sure "Content-Length" is added to the response header.<br />
Set a TCP timeout to ensure the resource is released if something goes wrong.<br />

<br />

### HTTP server/handler ###

* Line feed:
  - Follow RFCs 2616 and the newer 7230 regarding line feed
  - Always send a proper carriage return (CR = \r = x0d) and a newline (LF = \n = 0xa) character at the end of each line.
  - No need for CRLF at the end of the body according to RFC2616
* Persistent connection management:
  - Add "Content-Length" to the response header to avoid having the client guessing or simply left in a state where it's waiting for more data which will leave the connection lingering.
  - If we need to explicitly signal to the client to disconnect we should add "Connection: close" in the header.
* **Favicon:** To avoid a separate favicon being sent from Firefox and Chrome we need to inform the browser where the favicon can be found by linking it in the html in the GET / request.
~~~html
<head><link rel=\"icon\" sizes=\"16x16\" type=\"image/png\" href=\"favicon.png\"></head>
~~~
* 

Persistence:
In HTTP/1.0 a "Connection: Keep-alive" header needs to be sent by the client if it wants to persist the connection. Firefox is sending "Connection: keep-alive" which means that it wants to process more than one request/response pair in the same connection. Since we only serve HTTP/1.1 which implicity use persistence we don't need to act on this. We should still listen for "Connection: close" in the header though as this would indicate to stop the persistent mode for this connection and close the connection.

Is the "Date" header required?
Date: Sat, 13 Aug 2022 09:02:26 GMT

Notes to myself, but not certain it is required. Test again:
Needed to add this for the client to know that it has received all the requested data. The client should then proceed with sending a FIN/ACK to terminate the connection (firefox does this for example). Without this the connection stays alive.

<br />

## Testing ##

~~~console
python3 -m pytest tests
~~~

Create junitxml report when adding tests to git actions?
~~~console
python3 -m pytest tests --junitxml=junit/test-results.xml
~~~

## Conclusions (notes to myself mostly) ##

HTTP/3 might be worth looking at later. It seems to be a promising successor to HTTP/1.1. Will probably skip any deep dives in HTTP/2 as I have not yet encountered any real cases for it yet (except for seeing some bigger sites using it). HTTP/3 is also multiplexed but with the difference from its predecessors that it's using a new protocol named QUIC which operates on top of UDP.

<br />
<br />

## Resources ##

TCP

Python asyncio
* https://docs.python.org/3/library/asyncio-stream.html

Python3 sockets
* https://docs.python.org/3/library/socket.html

HTTP
* https://developer.mozilla.org/en-US/docs/Web/HTTP/Connection_management_in_HTTP_1.x
* https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Connection
* https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Keep-Alive
* https://developer.mozilla.org/en-US/docs/Web/HTTP/
* https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages
* https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml
* https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
* https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
* https://stackoverflow.com/questions/5757290/http-header-line-break-style
* https://httpwg.org/specs/rfc7230.html#compatibility.with.http.1.0.persistent.connections
* https://www.rfc-editor.org/rfc/rfc2068.html#section-19.7.1
* https://tools.ietf.org/html/rfc7230
* https://tools.ietf.org/html/rfc7231
* https://tools.ietf.org/html/rfc2616

Favicon
* https://en.wikipedia.org/wiki/Favicon

REGEX
* https://docs.microsoft.com/en-us/dotnet/api/system.text.regularexpressions.regex?view=net-6.0

Testing
Python testing using Github actions:
* https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

Other tools/utilities
tcpdump
* https://www.redhat.com/sysadmin/tcpdump-part-3
* https://www.tcpdump.org/manpages/tcpdump.1.html

<br />
<br />

## Scrap notes

Temporary notes that will be organized or removed as work progress.

### tcpdump

Capture network traffic and display the data part in ascii.
~~~bash
sudo tcpdump -ni lo port 9000 -A
~~~

TCP flags:
> Tcpflags are some combination of S (SYN), F (FIN), P (PUSH), R (RST), U (URG), W (ECN CWR), E (ECN-Echo) or `.' (ACK), or `none' if no flags are set.

Hex output to debug for example what line ending characters you have received. I used this to verify why I received 2 bytes I knew I only had sent 1 character using netcat. The second byte was simply the line feed as expected from a Linux client.

~~~console
$ sudo tcpdump -nni lo port 8000 -XX
~~~

### curl

Useful verbose mode to see what it was missing. This helped giving a clue that Contant-Length need to be specified for the connection to be properly closed, unless close is sent of course.

