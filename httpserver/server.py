import sys
import asyncio
import logging

import handle_http


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG, stream=sys.stdout)

async def handleConnection(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter):
    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            break
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f'Received {message!r} from {addr!r}')

        response = handle_http.handle_request(message)
        writer.write(response)
        print(f'Sent {response}')
        await writer.drain()
    print("closing - good bye")
    writer.close()


async def main():
    server = await asyncio.start_server(handleConnection, '127.0.0.1', 5000)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
