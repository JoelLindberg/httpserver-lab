import unittest

from httpserver import handle_http


class TestHandleHttpDataTypes(unittest.TestCase):
    def test_requesttype(self):
        requesttype = handle_http.RequestType(method='GET', resource='/', version='HTTP/1.1')
        self.assertEqual(requesttype, dict(method='GET', resource='/', version='HTTP/1.1'))


class TestHandleHttpMethods(unittest.TestCase):
    def setUp(self):    
        self.httpdata = handle_http.HttpData(
            request=handle_http.Request(
                requesttype=handle_http.RequestType(
                    method='',
                    resource='',
                    version=''
                ),
                headers={},
                body=''
            ),
            response=handle_http.Response(
                headers={},
                body='',
                image=b'',
                status_code=200
            ),
            message=handle_http.Message(
                request='',
                headers=[],
                body=''
            )
        )


    def test_split_request(self):
        httpdata = self.httpdata
        httpdata['message']['request'] = 'GET / HTTP/1.1'

        handle_http.split_request(httpdata)
        self.assertEqual(httpdata['request']['requesttype'],
                         {'method': 'GET', 'resource': '/', 'version': 'HTTP/1.1'})


    def test_split_request_favicon(self):
        # arrange
        self.httpdata['message']['request'] = 'GET /favicon.png HTTP/1.1'
        
        # act
        handle_http.split_request(self.httpdata)
        
        # assert
        compare = {'method': 'GET', 'resource': '/favicon.png', 'version': 'HTTP/1.1'}
        self.assertEqual(self.httpdata['request']['requesttype'], compare)


    def test_split_headers(self):
        # arrange
        self.httpdata['message']['headers'] = ['Connection: keep-alive\r\n', 'Accept: text/html\r\n']

        # act
        handle_http.split_headers(self.httpdata)

        # assert
        control = {
            'connection': 'keep-alive',
            'accept': 'text/html'
        }
        self.assertEqual(self.httpdata['request']['headers'], control)


    def test_split_message_all(self):
        msg = 'GET / HTTP/1.1\r\nConnection: keep-alive\r\nAccept: text/html\r\n\r\nBODY GOES HERE...\r\n'
        httpdata = self.httpdata

        handle_http.split_message(msg, httpdata)
        self.assertEqual(httpdata['message']['request'], 'GET / HTTP/1.1')
        self.assertEqual(httpdata['message']['headers'], ['Connection: keep-alive', 'Accept: text/html'])    
        self.assertEqual(httpdata['message']['body'], 'BODY GOES HERE...')
        

    def test_split_message_req_and_headers(self):
        msg = 'GET / HTTP/1.1\r\nConnection: keep-alive\r\nAccept: text/html\r\n'
        httpdata = self.httpdata

        handle_http.split_message(msg, httpdata)
        self.assertEqual(httpdata['message']['request'], 'GET / HTTP/1.1')
        self.assertEqual(httpdata['message']['headers'], ['Connection: keep-alive', 'Accept: text/html'])
        self.assertEqual(httpdata['message']['body'], '')


    def test_split_message_req_only(self):
        msg = 'GET / HTTP/1.1\r\n'
        httpdata = self.httpdata

        handle_http.split_message(msg, httpdata)
        handle_http.split_message(msg, httpdata)
        self.assertEqual(httpdata['message']['request'], 'GET / HTTP/1.1')
        self.assertEqual(httpdata['message']['headers'], [])
        self.assertEqual(httpdata['message']['body'], '')

    
    def test_split_message_empty(self):
        msg = ''
        httpdata = self.httpdata

        handle_http.split_message(msg, httpdata)
        self.assertEqual(httpdata['message']['request'], '')
        self.assertEqual(httpdata['message']['headers'], [])
        self.assertEqual(httpdata['message']['body'], '')


if __name__ == '__main__':
    unittest.main()
