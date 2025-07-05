import asyncio
import json
from typing import Any, Dict

class ClientSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def initialize(self):
        """Optional init message to establish session."""
        await self._send({"type": "init"})
        await self._receive()  # Wait for server ack/response

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        await self._send({
            "type": "tool_call",
            "tool": tool_name,
            "arguments": arguments
        })
        return await self._receive()

    async def list_tools(self) -> Any:
        await self._send({"type": "list_tools"})
        return await self._receive()

    async def read_resource(self, uri: str) -> Any:
        await self._send({
            "type": "read_resource",
            "uri": uri
        })
        return await self._receive()

    async def list_resources(self) -> Any:
        await self._send({"type": "list_resources"})
        return await self._receive()

    async def close(self):
        await self._send({"type": "close"})
        self.writer.close()
        await self.writer.wait_closed()

    async def _send(self, message: Dict[str, Any]):
        """Serialize and send a message to the server."""
        encoded = json.dumps(message) + "\n"
        self.writer.write(encoded.encode("utf-8"))
        await self.writer.drain()

    async def _receive(self) -> Any:
        """Read and decode a message from the server."""
        line = await self.reader.readline()
        if not line:
            raise ConnectionError("MCP server disconnected.")
        return json.loads(line.decode("utf-8"))
