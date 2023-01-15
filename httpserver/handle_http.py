import re
import typing
import pprint  # for debugging ... add logging (with stdout as option)?


class RequestType(typing.TypedDict):
    """Request method type"""
    method: str
    resource: str
    version: str


class Request(typing.TypedDict):
    """Sorted and Verified client request data, ready for processing"""
    requesttype: RequestType
    headers: typing.Dict[str, str]
    body: str


class Response(typing.TypedDict):
    """Server response data, to assemble the response text message from"""
    headers: typing.Dict[str, str]
    body: str
    image: bytes
    status_code: int


class Message(typing.TypedDict):
    """Temporary message store while processing and verifying it"""
    request: str
    headers: typing.List[str]
    body: str


class HttpData(typing.TypedDict):
    """Main data entry that will be referenced from receiving the message
    up until delivery"""
    request: Request
    response: Response
    message: Message


def update_status_code():
    # create logic that will stop processing the request
    # and send a reply to the client with the error immediately
    # 200 OK
    # 400 Bad Request
    # 404 Not Found
    pass


def router(httpdata: HttpData):
    # we should have a function that is responsible for checking what resource
    # is requested
    if httpdata['request']['requesttype']['resource'] == '/':
        load_html('index.html', httpdata)
        create_response_headers('html', httpdata)
    elif httpdata['request']['requesttype']['resource'] == '/favicon.png':
        load_favicon('favicon.png', httpdata)
        create_response_headers('png', httpdata)


def load_html(filepath: str, httpdata: HttpData):
    with open(filepath, 'r') as f:
        httpdata['response']['body'] = f.read()


def load_favicon(filepath: str, httpdata: HttpData):
    with open(filepath, 'rb') as f:
        httpdata['response']['image'] = f.read()


def create_response_headers(type: str, httpdata: HttpData):
    if type == 'html':
        body_length = str(len(httpdata['response']['body']))
        httpdata['response']['headers'] = {
            'content-type': 'text/html;charset=utf-8',
            'content-length': body_length
        }
    elif type == 'png':
        image_length = str(len(httpdata['response']['image']))
        httpdata['response']['headers'] = {
            'content-type': 'image/png',
            'content-length': image_length
        }


def create_response(httpdata: HttpData) -> bytes:
    """Create the response and return it as a string ready to be delivered
    to the client."""

    # Response status
    status = httpdata['response']['status_code']
    if status != 200:
        response = f'HTTP/1.1 {status}\r\n'
    else:
        response = f'HTTP/1.1 {status} OK\r\n'

    # Headers
    for k, v in httpdata['response']['headers'].items():
        response += f'{k}: {v}\r\n'

    # Body
    response += '\r\n'
    if httpdata['response']['body'] != '':
        response += f'{httpdata["response"]["body"]}\r\n'

    # debug
    print(f'HttpData before sending response: {httpdata}')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(httpdata)
    print(f'Response message: {response}')

    # Convert response to bytes object to be sent to the client over the wire.
    # If image is to be returned, this is appended where the body would
    # normally sit.
    if httpdata['response']['image'] != b'':
        response_ba = bytearray(response, encoding='utf-8')
        for b in httpdata['response']['image']:
            response_ba.append(b)
        response_b = bytes(response_ba)
    else:
        response_b = bytes(response, encoding='utf-8')

    return response_b


def verify_data(pattern: str, data: str) -> bool:
    """Utility function.
    :Verify data. Takes a regex pattern and a string to check and
    returns a bool."""

    matched = re.match(pattern, data)
    print(f'Regex result: {matched}')

    if matched is not None:
        return True
    else:
        return False


def split_request(httpdata: HttpData):
    """Split the request. Fetches request message from HttpData.
    : For example 'GET / HTTP/1.1' -> <method> <resource> <version>"""

    pattern = '^(GET|POST){1} /([a-zA-Z0-9-.]+/?)* (HTTP/1.1){1}?'

    print(f'message before split request: {httpdata["message"]["request"]}')
    if verify_data(pattern, httpdata['message']['request']):
        requestsplit = httpdata['message']['request'].split(' ')

        httpdata['request']['requesttype']['method'] = requestsplit[0]
        httpdata['request']['requesttype']['resource'] = requestsplit[1]
        httpdata['request']['requesttype']['version'] = requestsplit[2]


def split_headers(httpdata: HttpData):
    """Split headers from the temporary ['message']['headers'] store and
    insert them sorted into ['request']['headers']."""
    for header in httpdata['message']['headers']:
        h = header.split(':')
        kv = {
            h[0].strip().lower(): h[1].strip().lower()
        }
        httpdata['request']['headers'].update(kv)
        print(httpdata['request']['headers'])


def split_message(message: str, httpdata: HttpData):
    """Split the received message in to 3 (expected) parts as a list:
    : 0 = Request
    : 1 = Headers
    : 2 = Body
    : No validation of the message content is done by this method."""

    request = ''
    headers = []
    body = ''

    # Get line with request method, resource and version.
    # Expected to be the first line.
    m1 = message.split('\r\n', 1)
    print(f'm1: {m1}')
    request = m1[0]

    # Is there more than the request in the header?
    if len(m1) == 2:
        # Don't proceed if the second index is empty
        if m1[1] != '':
            # Is there a body in the header?
            m2 = m1[1].rsplit('\r\n\r\n')
            print(f'm2: {m2}')
            if len(m2) == 2:
                print(f'm2: {m2}')
                body = m2[-1].strip()

                # Are there headers as well?
                m3 = m2[0].split('\r\n')
                if m3[-1] == '':
                    m3.pop()
                print(f'm3a: {m3}')
                headers = m3
            else:
                # If no body was found, expect the rest to be headers only
                m3 = m2[0].split('\r\n')
                if m3[-1] == '':
                    m3.pop()
                print(f'm3b: {m3}')
                headers = m3

    httpdata['message']['request'] = request
    httpdata['message']['headers'] = headers
    httpdata['message']['body'] = body

    print(httpdata['message'])


def handle_request(message: str) -> bytes:
    """Process the client request and create the response."""
    httpdata = HttpData(
        request=Request(
            requesttype=RequestType(
                method='',
                resource='',
                version=''
            ),
            headers={},
            body=''
        ),
        response=Response(
            headers={},
            body='',
            image=b'',
            status_code=200
        ),
        message=Message(
            request='',
            headers=[],
            body=''
        )
    )

    # read the request sent by the client
    split_message(message, httpdata)
    split_request(httpdata)
    split_headers(httpdata)

    # create the response data based on the request received
    router(httpdata)

    # create the response string to send to the client
    response = create_response(httpdata)

    return response
