import re
import typing


# Request method type
class RequestType(typing.TypedDict):
    method: str
    resource: str
    version: str

# Sorted and Verified client request data, ready for processing
class Request(typing.TypedDict):
    requesttype: RequestType
    headers: typing.Dict[str, str]
    body: str

# Server response data, to assemble the response text message from
class Response(typing.TypedDict):
    headers: typing.Dict[str, str]
    body: str
    status_code: int

# Temporary message store while processing and verifying it
class Message(typing.TypedDict):
    request: str
    headers: typing.List[str]
    body: str

# Main data entry that will be referenced from receiving the message up until delivery
class HttpData(typing.TypedDict):
    request: Request
    response: Response
    message: Message


def update_status_code():
    # create logic that will stop processing the request 
    # and send a reply to the client with the error immediately
    pass


def create_response(httpdata: HttpData) -> str:
    """ Create the response and return it as a string ready to be delivered 
    to the client."""
    
    # Create the text message to return to the client
    # Response status
    status = httpdata['response']['status_code']
    response = f'HTTP {status} OK\r\n'

    # Headers
    for h in httpdata['response']['headers']:
        response += f'{h}\r\n'
    
    # Body
    if httpdata['response']['body'] is not '':
        response += '\r\n'
        response += f'{httpdata["response"]["body"]}\r\n'


    print(f'HttpData before sending response: {httpdata}')
    print(f'Response message: {response}')

    return response


def verify_data(pattern: str, data: str) -> bool:
    """Utility function.
    :Verify data. Takes a regex pattern and a string to check and 
    returns a bool."""
    
    matched = re.match(pattern, data)
    print(f'Regex result: {matched}')

    if matched != None:
        return True
    else:
        return False


def split_request(httpdata: HttpData):
    """Split the request. Fetches request message from HttpData.
    : For example 'GET / HTTP/1.1' -> <method> <resource> <version>"""

    pattern = '^(GET|POST){1} /([a-zA-Z0-9-]+/?)* (HTTP/1.1){1}?'

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
        kv = { h[0].strip().lower(): h[1].strip().lower() }
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


def handle_request(message: str) -> str:
    """Process the client request and create the response."""
    httpdata = HttpData(
        request = Request(
            requesttype = RequestType(
                method = '',
                resource = '',
                version = ''
            ),
            headers = {},
            body = ''
        ),
        response = Response(
            headers = {},
            body= '',
            status_code = 200
        ),
        message = Message(
            request='',
            headers=[],
            body=''
        )
    )

    # read the request sent by the client
    split_message(message, httpdata)
    split_request(httpdata)
    split_headers(httpdata)

    # create the response string to send to the client
    response = create_response(httpdata)

    return response