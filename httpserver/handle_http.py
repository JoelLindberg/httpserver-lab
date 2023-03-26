from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import typing
import pprint
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
    status_code: int
    headers: typing.Dict[str, str] = field(default_factory=dict)
    body: str = field(default="")
    image: bytes = field(default_factory=bytes)


@dataclass
class MessageTmp():
    """Temporary message store while processing and verifying it"""
    request: str = field(default="")
    headers: typing.List[str] = field(default_factory=list)
    body: str = field(default="")
    error_code: int = field(default=0)


def load_response_data(request: Request, response: Response):
    """Load response data for the requested resource."""
    # we should have a function that is responsible for checking what resource
    # is requested
    if response.status_code != 0:
        logging.debug("load_response_data() -> error code is set - skipping")
        return

    if request.request_resource == '/':
        response.body = load_html('index.html')
        response.headers = create_response_headers('html', len(response.body))
    elif request.request_resource == '/favicon.png':
        response.image = load_favicon('favicon.png')
        response.headers = create_response_headers('png', len(response.image))
    else:
        response.status_code = 404
        logging.debug("load_response_data() -> 404 - (resource) not found")
        return

    logging.debug(f"load_response_data() -> response data created: {response}")


def load_html(filepath: str):
    with open(filepath, 'r') as f:
        return f.read()


def load_favicon(filepath: str):
    with open(filepath, 'rb') as f:
        return f.read()


def create_response_headers(type: str, content_length: int) -> dict:
    # Date header example = Date: Sat, 13 Aug 2022 09:02:26 GMT
    datenow = datetime.now(ZoneInfo("Europe/Stockholm"))
    date = datenow.strftime("%a, %d %b %Y %H:%M:%S %Z")

    if type == "html":
        body_length = str(content_length)
        return {
            "content-type": "text/html;charset=utf-8",
            "content-length": body_length,
            "Date": date
        }
    elif type == "png":
        image_length = str(content_length)
        return {
            "content-type": "image/png",
            "content-length": image_length,
            "Date": date
        }


def error_message(status_code: int):
    if status_code == 400:
        return "400 Bad Request"
    elif status_code == 404:
        return "404 Not Found"


def create_response(response: Response) -> bytes:
    """Create the response and return it as a string ready to be delivered
    to the client."""
    response_msg = ""

    # Response status
    if response.status_code != 0:
        response_msg = f"HTTP/1.1 {error_message(response.status_code)}\r\n"
        return bytes(response_msg, encoding='utf-8')
    else:
        response_msg = "HTTP/1.1 200 OK\r\n"

    # Headers
    logging.debug(f"create_response() -> response.headers: {response.headers}")
    for k, v in response.headers.items():
        response_msg += f'{k}: {v}\r\n'

    # Body
    response_msg += '\r\n'
    if response.body != '':
        response_msg += f'{response.body}\r\n'

    # debug response (\r\n)
    pp = pprint.PrettyPrinter()
    logging.debug(f"create_response() -> response_msg raw:\n\
                  {repr(response_msg)}")
    logging.debug(f"create_response() -> response_msg semi-formatted:\n\
                  {pp.pformat(response_msg)}")

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
    if matched is not None:
        logging.debug(f"verify_data() regex match: {matched.groups()}")

    if matched is not None:
        return True
    else:
        return False


def split_request(message_tmp: MessageTmp, request: Request):
    """Split the request. Fetches request message from HttpData.
    : For example 'GET / HTTP/1.1' -> <method> <resource> <version>"""
    if message_tmp.error_code != 0:
        logging.debug("split_request() -> error code is set - skipping")
        return

    pattern = '^(GET|POST){1} /([a-zA-Z0-9-.]+/?)* (HTTP/1.1){1}?'

    if verify_data(pattern, message_tmp.request):
        requestsplit = message_tmp.request.split(' ')

        request.request_method = requestsplit[0]
        request.request_resource = requestsplit[1]
        request.request_version = requestsplit[2]

        logging.debug(f"split_request() -> after split: {request}")
    else:
        message_tmp.error_code = 400
        logging.debug("split_request() -> split failed - bad request?")
        return


def split_headers(message_tmp: MessageTmp, request: Request):
    """Split headers from the temporary ['message']['headers'] store and
    insert them sorted into ['request']['headers']."""
    if message_tmp.error_code != 0:
        logging.debug("split_headers() -> error code is set - skipping")
        return

    for header in message_tmp.headers:
        h = header.split(':')
        try:
            kv = {
                h[0].strip().lower(): h[1].strip().lower()
            }
            request.headers.update(kv)
        except IndexError:
            message_tmp.error_code = 400
            logging.debug("split_headers() -> split failed - bad request?")
            return

    logging.debug(f"split_headers() -> request.headers: {request.headers}")


def split_message(message: str, message_tmp: MessageTmp):
    """Split the received message in to 3 (expected) parts as a list:
    : 0 = Request
    : 1 = Headers
    : 2 = Body"""
    pattern = '^(.*\\r\\n)+'
    if not verify_data(pattern, message):
        logging.debug("Error: invalid raw message received")
        message_tmp.error_code = 400
        return

    m_split = message.split('\r\n')

    # Request
    message_tmp.request = m_split.pop(0)

    # Headers and Body
    body_found = 0
    for h in m_split:
        if h == '':
            # Assume the next item is the body (and no more after that)
            body_found = 1
            continue
        if body_found == 1:
            message_tmp.body = h
            break
        message_tmp.headers.append(h)

    logging.debug(f"split_message() -> message_split: {message_tmp}")

    return message_tmp


def handle_request(message: str) -> bytes:
    """Process the client request and create the response."""
    # Read the request sent by the client
    message_tmp = MessageTmp()
    split_message(message, message_tmp)
    request = Request()
    split_request(message_tmp, request)
    split_headers(message_tmp, request)

    # Create the response data based on the request received
    response = Response(status_code=message_tmp.error_code)
    load_response_data(request, response)

    # Create the response message (a byte encoded string) to send to the client
    response_message = create_response(response)

    return response_message
