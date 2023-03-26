import unittest

from httpserver import handle_http


class TestHandleHttpDataTypes(unittest.TestCase):
    def test_requesttype(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        request = handle_http.Response(status_code=0)

        # assert
        self.assertEqual(request, handle_http.Response(
            status_code=0,
        ))


class TestHandleHttpMethods(unittest.TestCase):
    def test_split_request(self):
        # arrange
        message_tmp = handle_http.MessageTmp()
        request = handle_http.Request()
        message_tmp.request = "GET / HTTP/1.1"

        # act
        handle_http.split_request(message_tmp, request)

        # assert
        self.assertEqual(request.request_method, "GET")
        self.assertEqual(request.request_resource, "/")
        self.assertEqual(request.request_version, "HTTP/1.1")

    def test_split_request_favicon(self):
        # arrange
        message_tmp = handle_http.MessageTmp()
        request = handle_http.Request()
        message_tmp.request = "GET /favicon.png HTTP/1.1"

        # act
        handle_http.split_request(message_tmp, request)

        # assert
        self.assertEqual(request.request_method, "GET")
        self.assertEqual(request.request_resource, "/favicon.png")
        self.assertEqual(request.request_version, "HTTP/1.1")

    def test_split_headers(self):
        # arrange
        message_tmp = handle_http.MessageTmp()
        request = handle_http.Request()
        message_tmp.headers = ["Connection: keep-alive\r\n",
                               "Accept: text/html\r\n"]

        # act
        handle_http.split_headers(message_tmp, request)

        # assert
        control_headers = {
            "connection": "keep-alive",
            "accept": "text/html"
        }
        self.assertEqual(request.headers, control_headers)

    def test_split_message_all(self):
        message_tmp = handle_http.MessageTmp()
        msg = "GET / HTTP/1.1\r\n\
Connection: keep-alive\r\nAccept: text/html\r\n\r\n\
BODY GOES HERE...\r\n"

        handle_http.split_message(msg, message_tmp)
        self.assertEqual(message_tmp.request, "GET / HTTP/1.1")
        self.assertEqual(message_tmp.headers,
                         ["Connection: keep-alive", "Accept: text/html"])
        self.assertEqual(message_tmp.body, "BODY GOES HERE...")

    def test_split_message_req_and_headers(self):
        message_tmp = handle_http.MessageTmp()
        msg = "GET / HTTP/1.1\r\n\
Connection: keep-alive\r\nAccept: text/html\r\n"

        handle_http.split_message(msg, message_tmp)
        self.assertEqual(message_tmp.request, "GET / HTTP/1.1")
        self.assertEqual(message_tmp.headers,
                         ["Connection: keep-alive", "Accept: text/html"])
        self.assertEqual(message_tmp.body, "")

    def test_split_message_req_only(self):
        message_tmp = handle_http.MessageTmp()
        msg = "GET / HTTP/1.1\r\n"

        handle_http.split_message(msg, message_tmp)
        handle_http.split_message(msg, message_tmp)
        self.assertEqual(message_tmp.request, "GET / HTTP/1.1")
        self.assertEqual(message_tmp.headers, [])
        self.assertEqual(message_tmp.body, "")

    def test_split_message_empty(self):
        message_tmp = handle_http.MessageTmp()
        msg = ""

        handle_http.split_message(msg, message_tmp)
        self.assertEqual(message_tmp.request, "")
        self.assertEqual(message_tmp.headers, [])
        self.assertEqual(message_tmp.body, "")
