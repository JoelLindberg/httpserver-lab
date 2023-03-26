import sys
import asyncio
import logging
import argparse

import handle_http


parser = argparse.ArgumentParser(
                    prog='HTTP Server Lab',
                    description="Serve a GET / request for a browser \
                                 request. Tested only with Firefox and \
                                 Chrome.")

parser.add_argument('-p',
                    '--port',
                    type=int,
                    default=4000,
                    help="Listen on specified TCP port")
parser.add_argument('-d',
                    '--debug',
                    action="store_true",
                    help="Verbose logging to the console")

args = parser.parse_args()

PORT = args.port

if args.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=log_level,
                    stream=sys.stdout)


async def handleConnection(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    logging.info(f"Client connected: {addr!r}")
    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            break
        message = data.decode()
        logging.info(f"Received message: {message!r} from {addr!r}")

        response = handle_http.handle_request(message)
        writer.write(response)
        logging.info(f"Sent response: {response} to {addr!r}")
        await writer.drain()

    writer.close()
    logging.info(f"Client disconnected: {addr!r}")


async def main():
    server = await asyncio.start_server(handleConnection, '127.0.0.1', PORT)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
