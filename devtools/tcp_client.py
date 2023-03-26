import socket
import sys

SERVER = '127.0.0.1'
PORT = 4000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((SERVER, PORT))
print(f'Connected to {SERVER}:{PORT}')

#data = s.recv(1024)
#print(data)

headers = 'Connection: keep-alive\r\nAccept: text/html\r\n'
body = '\r\nBODY GOES HERE...\r\n'
request_body = f'GET / HTTP/1.1\r\n{headers}{body}'
request_no_body = f'GET / HTTP/1.1\r\n{headers}'

while True:
    print('Alternatives:')
    print('1 = HTTP GET request with body')
    print('2 = HTTP GET request without body')
    print('3 = Graceful exit. Sends FIN')
    print('4 = Close the connection without saying goodbye (bad). Sends RST')

    msg = input("Send a message (enter 'bye' to gracefully exit): ")
    
    if msg == '3':
        s.shutdown(socket.SHUT_WR)
        sys.exit(0)
    elif msg == '4':
        s.close() # force ugly shutdown by sending RST
    elif msg == '1':
        s.send(bytes(request_body, 'utf-8'))
    elif msg == '2':
        s.send(bytes(request_no_body, 'utf-8'))
    else:
        s.send(bytes(msg, 'utf-8'))

    data = s.recv(1024)
    print(data.decode())