"""LNbits MCP Server implementation."""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import structlog
from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
)
from pydantic import ValidationError

from .client import LNbitsClient, LNbitsConfig, LNbitsError
from .models.schemas import (
    CreateInvoiceRequest,
    Invoice,
    PayInvoiceRequest,
    Payment,
    WalletDetails,
)
from .tools.core import CoreTools
from .tools.invoices import InvoiceTools
from .tools.payments import PaymentTools

logger = structlog.get_logger(__name__)


class LNbitsMCPServer:
    """LNbits MCP Server."""

    def __init__(self, config: Optional[LNbitsConfig] = None):
        self.config = config or LNbitsConfig()
        self.client = LNbitsClient(self.config)
        self.server = Server("lnbits-mcp-server")

        # Tool handlers
        self.core_tools = CoreTools(self.client)
        self.payment_tools = PaymentTools(self.client)
        self.invoice_tools = InvoiceTools(self.client)

        # Register MCP handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            print("🔧 list_tools() called by Claude Desktop", file=sys.stderr)

            try:
                tools = [
                    Tool(
                        name="get_wallet_details",
                        description="Get wallet details including balance and keys",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_wallet_balance",
                        description="Get current wallet balance",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_payments",
                        description="Get payment history",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of payments to return",
                                    "default": 10,
                                    "minimum": 1,
                                    "maximum": 100,
                                },
                            },
                            "required": [],
                        },
                    ),
                    Tool(
                        name="check_connection",
                        description="Check connection to LNbits instance",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="pay_invoice",
                        description="Pay a Lightning invoice",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "bolt11": {
                                    "type": "string",
                                    "description": "BOLT11 invoice string to pay",
                                }
                            },
                            "required": ["bolt11"],
                        },
                    ),
                    Tool(
                        name="get_payment_status",
                        description="Get payment status by payment hash",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "payment_hash": {
                                    "type": "string",
                                    "description": "Payment hash to check",
                                },
                            },
                            "required": ["payment_hash"],
                        },
                    ),
                    Tool(
                        name="decode_invoice",
                        description="Decode a Lightning invoice to see its details",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "bolt11": {
                                    "type": "string",
                                    "description": "BOLT11 invoice string to decode",
                                },
                            },
                            "required": ["bolt11"],
                        },
                    ),
                    Tool(
                        name="create_invoice",
                        description="Create a new Lightning invoice",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "amount": {
                                    "type": "integer",
                                    "description": "Invoice amount in satoshis",
                                    "minimum": 1,
                                },
                                "memo": {
                                    "type": "string",
                                    "description": "Invoice memo/description",
                                },
                                "description_hash": {
                                    "type": "string",
                                    "description": "Description hash for the invoice",
                                },
                                "expiry": {
                                    "type": "integer",
                                    "description": "Invoice expiry in seconds",
                                    "minimum": 60,
                                    "maximum": 86400,
                                    "default": 3600,
                                },
                            },
                            "required": ["amount"],
                        },
                    ),
                    Tool(
                        name="pay_lightning_address",
                        description="Pay a Lightning address (e.g., user@domain.com)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "lightning_address": {
                                    "type": "string",
                                    "description": "Lightning address to pay (e.g., user@domain.com)",
                                    "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                                },
                                "amount_sats": {
                                    "type": "integer",
                                    "description": "Amount to pay in satoshis",
                                    "minimum": 1,
                                },
                                "comment": {
                                    "type": "string",
                                    "description": "Optional comment for the payment",
                                },
                            },
                            "required": ["lightning_address", "amount_sats"],
                        },
                    ),
                ]

                print(f"🔧 Created {len(tools)} tools", file=sys.stderr)
                for i, tool in enumerate(tools):
                    print(
                        f"  {i+1}. {tool.name}: {type(tool)} (hasattr name: {hasattr(tool, 'name')})",
                        file=sys.stderr,
                    )

                # Verify all tools have the required attributes
                for tool in tools:
                    if not hasattr(tool, "name"):
                        print(
                            f"❌ ERROR: Tool missing 'name' attribute: {tool}",
                            file=sys.stderr,
                        )
                        raise ValueError(f"Tool missing 'name' attribute: {tool}")
                    if not hasattr(tool, "description"):
                        print(
                            f"❌ ERROR: Tool missing 'description' attribute: {tool}",
                            file=sys.stderr,
                        )
                        raise ValueError(
                            f"Tool missing 'description' attribute: {tool}"
                        )
                    if not hasattr(tool, "inputSchema"):
                        print(
                            f"❌ ERROR: Tool missing 'inputSchema' attribute: {tool}",
                            file=sys.stderr,
                        )
                        raise ValueError(
                            f"Tool missing 'inputSchema' attribute: {tool}"
                        )

                print(
                    f"🔧 Returning tools list directly: {len(tools)} tools",
                    file=sys.stderr,
                )
                return tools

            except Exception as e:
                print(f"❌ ERROR in list_tools(): {e}", file=sys.stderr)
                print(f"❌ Error type: {type(e)}", file=sys.stderr)
                import traceback

                traceback.print_exc(file=sys.stderr)
                # Return empty tools list on error
                return []

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls."""
            try:
                logger.info("Tool called", tool=name, arguments=arguments)

                # Core tools
                if name == "get_wallet_details":
                    result = await self.core_tools.get_wallet_details()
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "get_wallet_balance":
                    result = await self.core_tools.get_wallet_balance()
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "get_payments":
                    limit = arguments.get("limit", 10)
                    result = await self.core_tools.get_payments(limit)
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "check_connection":
                    result = await self.core_tools.check_connection()
                    status = "Connected" if result else "Disconnected"
                    return {
                        "content": [
                            {"type": "text", "text": f"LNbits connection: {status}"}
                        ]
                    }

                # Payment tools
                elif name == "pay_invoice":
                    bolt11 = arguments["bolt11"]
                    amount = arguments.get("amount")
                    result = await self.payment_tools.pay_invoice(bolt11, amount)
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "get_payment_status":
                    payment_hash = arguments["payment_hash"]
                    result = await self.payment_tools.get_payment_status(payment_hash)
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "decode_invoice":
                    bolt11 = arguments["bolt11"]
                    result = await self.payment_tools.decode_invoice(bolt11)
                    return {"content": [{"type": "text", "text": str(result)}]}

                elif name == "pay_lightning_address":
                    lightning_address = arguments["lightning_address"]
                    amount_sats = arguments["amount_sats"]
                    comment = arguments.get("comment")
                    result = await self.payment_tools.pay_lightning_address(
                        lightning_address, amount_sats, comment
                    )
                    return {"content": [{"type": "text", "text": str(result)}]}

                # Invoice tools
                elif name == "create_invoice":
                    amount = arguments["amount"]
                    memo = arguments.get("memo")
                    description_hash = arguments.get("description_hash")
                    expiry = arguments.get("expiry", 3600)

                    result = await self.invoice_tools.create_invoice(
                        amount, memo, description_hash, expiry
                    )
                    return {"content": [{"type": "text", "text": str(result)}]}

                else:
                    return {
                        "isError": True,
                        "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    }

            except LNbitsError as e:
                logger.error("LNbits API error", error=str(e), tool=name)
                return {
                    "isError": True,
                    "content": [
                        {"type": "text", "text": f"LNbits API error: {str(e)}"}
                    ],
                }
            except ValidationError as e:
                logger.error("Validation error", error=str(e), tool=name)
                return {
                    "isError": True,
                    "content": [
                        {"type": "text", "text": f"Validation error: {str(e)}"}
                    ],
                }
            except Exception as e:
                logger.error("Unexpected error", error=str(e), tool=name, exc_info=True)
                return {
                    "isError": True,
                    "content": [
                        {"type": "text", "text": f"Unexpected error: {str(e)}"}
                    ],
                }

    async def run(self):
        """Run the MCP server."""
        print("🎯 MCP Server run() method started", file=sys.stderr)
        logger.info("Starting LNbits MCP server", config=self.config)

        # Skip connection test to avoid closing the HTTP client
        print(
            "🔌 Skipping initial connection test to keep client open", file=sys.stderr
        )

        # Run server
        print("🚀 Starting MCP stdio server...", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print(
                "📡 MCP stdio streams established, running server...", file=sys.stderr
            )
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="lnbits-mcp-server",
                    server_version="0.1.0",
                    capabilities=types.ServerCapabilities(
                        tools=types.ToolsCapability(listChanged=False),
                        experimental={},
                    ),
                ),
            )


async def async_main():
    """Async main entry point."""
    # Debug output for Claude Desktop logs
    print("🚀 LNbits MCP Server starting...", file=sys.stderr)
    print(f"🌍 Working directory: {os.getcwd()}", file=sys.stderr)
    print(f"🔐 Environment variables from os.getenv():", file=sys.stderr)
    print(f"  LNBITS_URL: {os.getenv('LNBITS_URL', 'NOT SET')}", file=sys.stderr)
    print(
        f"  LNBITS_API_KEY: {'SET' if os.getenv('LNBITS_API_KEY') else 'NOT SET'}",
        file=sys.stderr,
    )
    print(
        f"  LNBITS_AUTH_METHOD: {os.getenv('LNBITS_AUTH_METHOD', 'NOT SET')}",
        file=sys.stderr,
    )

    # Test what Claude Desktop is actually passing
    print(f"🔍 All environment variables:", file=sys.stderr)
    env_vars = {k: v for k, v in os.environ.items() if "LNBITS" in k}
    if env_vars:
        for k, v in env_vars.items():
            print(f"  {k}: {v}", file=sys.stderr)
    else:
        print("  No LNBITS_* environment variables found!", file=sys.stderr)

    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    try:
        # Load configuration
        print("📋 Loading LNbits configuration...", file=sys.stderr)
        config = LNbitsConfig()
        print(
            f"✅ Config loaded: URL={config.lnbits_url}, API_KEY={'SET' if config.api_key else 'NOT SET'}, AUTH={config.auth_method}",
            file=sys.stderr,
        )

        # Create and run server
        print("🏗️ Creating MCP server...", file=sys.stderr)
        server = LNbitsMCPServer(config)
        print("🔗 Starting MCP server...", file=sys.stderr)
        await server.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error("Server error", error=str(e), exc_info=True)
        sys.exit(1)


def main():
    """Synchronous main entry point for console script."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
