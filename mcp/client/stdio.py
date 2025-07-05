import asyncio
from asyncio.subprocess import Process
from typing import Tuple

def stdio_client(process: Process) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """
    Converts subprocess stdin/stdout into asyncio streams.
    """
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Subprocess must have stdin and stdout pipes.")

    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    transport = loop.run_until_complete(loop.connect_read_pipe(lambda: protocol, process.stdout))

    writer = asyncio.StreamWriter(process.stdin, protocol, reader, loop)

    return reader, writer
