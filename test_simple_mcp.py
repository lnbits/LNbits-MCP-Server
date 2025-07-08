#!/usr/bin/env python3
"""Test simple MCP server to isolate the issue."""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ListToolsResult


async def main():
    server = Server("test-server")
    
    @server.list_tools()
    async def list_tools() -> ListToolsResult:
        tools = [
            Tool(
                name="test_tool",
                description="A test tool",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
        return ListToolsResult(tools=tools)
    
    async with stdio_server() as (read_stream, write_stream):
        from mcp.server.models import InitializationOptions
        await server.run(read_stream, write_stream, InitializationOptions(
            server_name="test-server",
            server_version="1.0.0"
        ))


if __name__ == "__main__":
    asyncio.run(main())