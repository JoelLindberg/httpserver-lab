from dataclasses import dataclass
from dataclasses import field
import re
import typing
import pprint  # for debugging ... add logging (with stdout as option)?
import logging


@dataclass
class Request():
    """Sorted and Verified client request data, ready for processing"""
    request_method: str = field(default="")
    request_resource: str = field(default="")
    request_version: str = field(default="")
    headers: typing.Dict[str, str] = field(default_factory=dict)
    body: str = field(default="")


@dataclass
class Response():
    """Server response data, to assemble the response text message from"""
    headers: typing.Dict[str, str] = field(default_factory=dict)
    body: str = field(default="")
    image: bytes = field(default_factory=bytes)
    status_code: int = field(default=0)


@dataclass
class MessageTmp():
    """Temporary message store while processing and verifying it"""
    request: str = field(default="")
    headers: typing.List[str] = field(default_factory=list)
    body: str = field(default="")


def update_status_code():
    # create logic that will stop processing the request
    # and send a reply to the client with the error immediately
    # 200 OK
    # 400 Bad Request
    # 404 Not Found
    pass


def load_response_data(request: Request, response: Response):
    """Load response data for the requested resource."""
    # we should have a function that is responsible for checking what resource
    # is requested
    if request.request_resource == '/':
        response.body = load_html('index.html')
        response.headers = create_response_headers('html', len(response.body))
    elif request.request_resource == '/favicon.png':
        response.image = load_favicon('favicon.png')
        response.headers = create_response_headers('png', len(response.image))


def load_html(filepath: str):
    with open(filepath, 'r') as f:
        return f.read()


def load_favicon(filepath: str):
    with open(filepath, 'rb') as f:
        return f.read()


def create_response_headers(type: str, content_length: int) -> dict:
    if type == 'html':
        body_length = str(content_length)
        return {
            'content-type': 'text/html;charset=utf-8',
            'content-length': body_length
        }
    elif type == 'png':
        image_length = str(content_length)
        return {
            'content-type': 'image/png',
            'content-length': image_length
        }


def create_response(response: Response) -> bytes:
    """Create the response and return it as a string ready to be delivered
    to the client."""

    response_msg = ""

    # Response status
    if response.status_code != 200:
        response_msg = f'HTTP/1.1 {response.status_code}\r\n'
    else:
        response_msg = f'HTTP/1.1 {response.status_code} OK\r\n'

    # Headers
    print(response.headers)
    for k, v in response.headers.items():
        response_msg += f'{k}: {v}\r\n'

    # Body
    response_msg += '\r\n'
    if response.body != '':
        response_msg += f'{response.body}\r\n'

    # debug
    print(f'HttpData before sending response: {response}')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(response_msg)
    print(f'Response message: {response_msg}')

    # Convert response to bytes object to be sent to the client over the wire.
    # If image is to be returned, this is appended where the body would
    # normally sit.
    if response.image != b'':
        response_ba = bytearray(response_msg, encoding='utf-8')
        for b in response.image:
            response_ba.append(b)
        response_b = bytes(response_ba)
    else:
        response_b = bytes(response_msg, encoding='utf-8')

    return response_b


def verify_data(pattern: str, data: str) -> bool:
    """Utility function.
    :Verify data. Takes a regex pattern and a string to check and
    returns a bool."""

    matched = re.match(pattern, data)
    logging.debug(f"Regex result: {matched}")

    if matched is not None:
        return True
    else:
        return False


def split_request(message_tmp: MessageTmp, request: Request):
    """Split the request. Fetches request message from HttpData.
    : For example 'GET / HTTP/1.1' -> <method> <resource> <version>"""

    pattern = '^(GET|POST){1} /([a-zA-Z0-9-.]+/?)* (HTTP/1.1){1}?'

    print(f'message before split request: {message_tmp.request}')
    if verify_data(pattern, message_tmp.request):
        requestsplit = message_tmp.request.split(' ')

        #request = Request()
        request.request_method = requestsplit[0]
        request.request_resource = requestsplit[1]
        request.request_version = requestsplit[2]

        logging.debug(f"Split request: {request}")

        #return request


def split_headers(message_tmp: MessageTmp, request: Request):
    """Split headers from the temporary ['message']['headers'] store and
    insert them sorted into ['request']['headers']."""
    for header in message_tmp.headers:
        h = header.split(':')
        kv = {
            h[0].strip().lower(): h[1].strip().lower()
        }
        request.headers.update(kv)
        
        logging.debug(f"Split headers: {request.headers}")


def split_message(message: str) -> MessageTmp:
    """Split the received message in to 3 (expected) parts as a list:
    : 0 = Request
    : 1 = Headers
    : 2 = Body"""

    pattern = '^(.*\\r\\n)+'
    if not verify_data(pattern, message):
        logging.debug(f"Error: invalid (raw) message received")  # create error http response
        return

    message_split = MessageTmp()

    # GET / HTTP/1.1\r\n
    # Connection: keep-alive\r\n
    # Accept: text/html\r\n
    # \r\n
    # BODY GOES HERE...\r\n
    m_split = message.split('\r\n')
    # [GET, Connection, Accept, '', BODY, '']
    print(m_split)
    message_split.request = m_split.pop(0)
    print(message_split.request)

    body_found = 0
    for h in m_split:
        if h == '':
            # assume the next item is the body (and the last)
            body_found = 1
            print(h)
            continue
        if body_found == 1:
            message_split.body = h
            print(h)
            break
        message_split.headers.append(h)
        print(h)

    print(message_split)
    logging.debug(f"Split message: {message_split}")

    return message_split


def handle_request(message: str) -> bytes:
    """Process the client request and create the response."""
    # read the request sent by the client
    message_tmp = split_message(message)
    request = Request()
    split_request(message_tmp, request)
    split_headers(message_tmp, request)

    response = Response()
    # create the response data based on the request received
    load_response_data(request, response)
    logging.debug(f"Response data: {response}")
    #response("/", request, response)
    #response("/favicon", request, response)

    # create the response message (a byte encoded string) to send to the client
    response_message = create_response(response)

    return response_message
