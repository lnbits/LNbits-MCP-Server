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
from .tools.config_tools import ConfigTools
from .utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)


class LNbitsMCPServer:
    """LNbits MCP Server."""

    def __init__(self, config: Optional[LNbitsConfig] = None):
        self.config = config or LNbitsConfig()
        self.server = Server("lnbits-mcp-server")

        # Runtime configuration manager
        self.config_manager = RuntimeConfigManager(self.config)

        # Tool handlers - updated to use config_manager
        self.core_tools = CoreTools(self.config_manager)
        self.payment_tools = PaymentTools(self.config_manager)
        self.invoice_tools = InvoiceTools(self.config_manager)
        self.config_tools = ConfigTools(self.config_manager)

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
                        name="configure_lnbits",
                        description="Configure LNbits connection parameters at runtime",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "lnbits_url": {
                                    "type": "string",
                                    "description": "Base URL for LNbits instance (e.g., https://demo.lnbits.com)",
                                },
                                "api_key": {
                                    "type": "string",
                                    "description": "API key for LNbits authentication",
                                },
                                "bearer_token": {
                                    "type": "string",
                                    "description": "Bearer token for authentication (alternative to api_key)",
                                },
                                "oauth2_token": {
                                    "type": "string",
                                    "description": "OAuth2 token for authentication (alternative to api_key)",
                                },
                                "auth_method": {
                                    "type": "string",
                                    "description": "Authentication method",
                                    "enum": [
                                        "api_key_header",
                                        "api_key_query",
                                        "http_bearer",
                                        "oauth2",
                                    ],
                                },
                                "timeout": {
                                    "type": "integer",
                                    "description": "Request timeout in seconds",
                                    "minimum": 1,
                                    "maximum": 300,
                                },
                                "rate_limit_per_minute": {
                                    "type": "integer",
                                    "description": "Rate limit per minute",
                                    "minimum": 1,
                                    "maximum": 1000,
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
                        },
                    ),
                    Tool(
                        name="get_lnbits_configuration",
                        description="Get current LNbits configuration status",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    ),
                    Tool(
                        name="test_lnbits_configuration",
                        description="Test the current LNbits configuration by making a test API call",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    ),
                    Tool(
                        name="get_wallet_details",
                        description="""
                        <use_case>
                        Get the details of the user's wallet.
                        </use_case>
                        <important_notes>
                        This tool will return the user's wallet details, including the wallet ID, name, user, balance in msats (sats * 1000), currency,
                        and whether the wallet has an admin key and invoice key.
                        The balance is in msats (sats * 1000).
                        The currency is msats. Give the user the balance in sats, not msats. So divide the balance by 1000 to get the balance in sats.
                        The wallet ID is the ID of the wallet.
                        The name is the name of the wallet.
                        The user is the user of the wallet.
                        Do not tell the user the admin key or invoice key.
                        </important_notes>
                        """,
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_wallet_balance",
                        description="""
                        <use_case>
                        Get the current balance of the user's wallet.
                        </use_case>
                        <important_notes>
                        Tell the user only their balance in sats (balance_sats) from the data detailed below.
                        This tool returns JSON with the following fields:
                        - balance: The current balance of the user's wallet in msats (sats * 1000).
                        - balance_sats: The current balance of the user's wallet in sats.
                        - currency: The currency of the wallet.
                        - formated_balance: The current balance of the user's wallet in msats and sats e.g. "34,000 msats (34 sats)"
                        </important_notes>
                        """,
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
                        description="""
                        <use_case>
                        Pay a lightning invoice. The user will provide the BOLT11 invoice string.
                        </use_case>
                        <important_notes>
                        This tool will pay an invoice. The user will provide the BOLT11 invoice string.
                        The amount to pay is in sats.
                        The amount to pay is the amount of the invoice.
                        </important_notes>
                        """,
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
                        description="""
                        <use_case>
                        Get the status of a lightning payment using the payment hash.
                        </use_case>
                        <important_notes>
                        This tool will return the status of a payment by payment hash.
                        Tell the user the status of the payment.
                        </important_notes>
                        """,
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
                        description="""
                        <use_case>
                        Decode a BOLT11 lightning invoice to get the amount, memo, and payment hash.
                        </use_case>
                        <important_notes>
                        This tool will return the details of a lightning invoice.
                        - The amount is in msats / millisatoshis = sats * 1000
                        - The memo is the memo of the invoice.
                        - The payment hash is the payment hash of the invoice.
                        </important_notes>
                        """,
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
                        description="""
                        <use_case>
                        Create a new lightning invoice. The user will provide the amount in sats, memo, description hash, and expiry.
                        </use_case>
                        <important_notes>
                        This tool will create a new lightning invoice. The user will provide the amount, memo, description hash, and expiry.
                        The amount is in sats. So if the user provides "10 sats", the amount is 10.
                        The memo is the memo of the invoice.
                        The description hash is the description hash of the invoice.
                        
                        The response includes both a BOLT11 invoice string and a QR code URL that can be used to display a scannable QR code image for Lightning payments.
                        The qr_code field contains a direct URL to a QR code image, while lightning_uri contains the lightning: protocol URI.
                        
                        Display the QR code image in the response then the BOLT11 invoice string.
                        </important_notes>
                        """,
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
                        description="""
                        <use_case>
                        Send bitcoin sats to another person's wallet using their email style lightning address.
                        The user will provide the lightning address (name@domain.com) and the amount to pay.
                        </use_case>
                        <important_notes>
                        The amount to pay is in sats NOT msats. So if the user provides "10 sats", the amount is 10 sats.
                        The comment is an optional comment for the payment.
                        </important_notes>
                        """,
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

                # Configuration tools
                if name in [
                    "configure_lnbits",
                    "get_lnbits_configuration",
                    "test_lnbits_configuration",
                ]:
                    result = await self.config_tools.call_tool(name, arguments)
                    # Convert TextContent list to proper format
                    if isinstance(result, list) and result:
                        return {"content": [{"type": "text", "text": result[0].text}]}
                    return {"content": [{"type": "text", "text": str(result)}]}

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

        try:
            # Run server
            print("🚀 Starting MCP stdio server...", file=sys.stderr)
            async with stdio_server() as (read_stream, write_stream):
                print(
                    "📡 MCP stdio streams established, running server...",
                    file=sys.stderr,
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
        finally:
            # Cleanup runtime configuration manager
            await self.config_manager.close()


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
        # config = LNbitsConfig()
        # print(
        #     f"✅ Config loaded: URL={config.lnbits_url}, API_KEY={'SET' if config.api_key else 'NOT SET'}, AUTH={config.auth_method}",
        #     file=sys.stderr,
        # )

        # Create and run server
        print("🏗️ Creating MCP server...", file=sys.stderr)
        server = LNbitsMCPServer()
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
