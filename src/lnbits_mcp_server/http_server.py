"""LNbits MCP HTTP Server implementation."""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool
from pydantic import BaseModel, ValidationError

from .client import LNbitsClient, LNbitsConfig, LNbitsError
from .tools.config_tools import ConfigTools
from .tools.core import CoreTools
from .tools.invoices import InvoiceTools
from .tools.payments import PaymentTools
from .utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)


class ToolCallRequest(BaseModel):
    """Request model for tool calls."""
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    content: List[Dict[str, str]]
    isError: Optional[bool] = False


class LNbitsHTTPServer:
    """LNbits MCP HTTP Server."""

    def __init__(self, config: Optional[LNbitsConfig] = None):
        self.config = config or LNbitsConfig()
        self.app = FastAPI(title="LNbits MCP Server", version="0.1.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Runtime configuration manager
        self.config_manager = RuntimeConfigManager(self.config)

        # Tool handlers
        self.core_tools = CoreTools(self.config_manager)
        self.payment_tools = PaymentTools(self.config_manager)
        self.invoice_tools = InvoiceTools(self.config_manager)
        self.config_tools = ConfigTools(self.config_manager)

        self._register_routes()

    def _get_available_tools(self) -> List[Tool]:
        """Get list of available tools."""
        return [
            Tool(
                name="configure_lnbits",
                description="Configure LNbits connection parameters at runtime",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lnbits_url": {"type": "string"},
                        "api_key": {"type": "string"},
                        "bearer_token": {"type": "string"},
                        "oauth2_token": {"type": "string"},
                        "auth_method": {"type": "string", "enum": ["api_key_header", "api_key_query", "http_bearer", "oauth2"]},
                        "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
                        "rate_limit_per_minute": {"type": "integer", "minimum": 1, "maximum": 1000},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="get_lnbits_configuration",
                description="Get current LNbits configuration status",
                inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            ),
            Tool(
                name="test_lnbits_configuration",
                description="Test the current LNbits configuration by making a test API call",
                inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            ),
            Tool(
                name="get_wallet_details",
                description="Get the details of the user's wallet",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_wallet_balance",
                description="Get the current balance of the user's wallet",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_payments",
                description="Get payment history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100}
                    },
                    "required": [],
                },
            ),
            Tool(
                name="check_connection",
                description="Check connection to LNbits instance",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="pay_invoice",
                description="Pay a lightning invoice",
                inputSchema={
                    "type": "object",
                    "properties": {"bolt11": {"type": "string"}},
                    "required": ["bolt11"],
                },
            ),
            Tool(
                name="get_payment_status",
                description="Get the status of a lightning payment using the payment hash",
                inputSchema={
                    "type": "object",
                    "properties": {"payment_hash": {"type": "string"}},
                    "required": ["payment_hash"],
                },
            ),
            Tool(
                name="decode_invoice",
                description="Decode a BOLT11 lightning invoice",
                inputSchema={
                    "type": "object",
                    "properties": {"bolt11": {"type": "string"}},
                    "required": ["bolt11"],
                },
            ),
            Tool(
                name="create_invoice",
                description="Create a new lightning invoice",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer", "minimum": 1},
                        "memo": {"type": "string"},
                        "description_hash": {"type": "string"},
                        "expiry": {"type": "integer", "minimum": 60, "maximum": 86400, "default": 3600},
                    },
                    "required": ["amount"],
                },
            ),
            Tool(
                name="pay_lightning_address",
                description="Send bitcoin sats to another person's wallet using their lightning address",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lightning_address": {"type": "string", "pattern": "^[^@]+@[^@]+\\.[^@]+$"},
                        "amount_sats": {"type": "integer", "minimum": 1},
                        "comment": {"type": "string"},
                    },
                    "required": ["lightning_address", "amount_sats"],
                },
            ),
        ]

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.get("/")
        async def root():
            return {"message": "LNbits MCP Server", "version": "0.1.0"}

        @self.app.get("/tools")
        async def list_tools():
            """List available tools."""
            return {"tools": [{"name": tool.name, "description": tool.description} for tool in self._get_available_tools()]}

        @self.app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, request: ToolCallRequest) -> ToolCallResponse:
            """Call a specific tool."""
            try:
                logger.info("Tool called", tool=tool_name, arguments=request.arguments)
                
                # Configuration tools
                if tool_name in ["configure_lnbits", "get_lnbits_configuration", "test_lnbits_configuration"]:
                    result = await self.config_tools.call_tool(tool_name, request.arguments)
                    if isinstance(result, list) and result:
                        return ToolCallResponse(content=[{"type": "text", "text": result[0].text}])
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                # Core tools
                elif tool_name == "get_wallet_details":
                    result = await self.core_tools.get_wallet_details()
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "get_wallet_balance":
                    result = await self.core_tools.get_wallet_balance()
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "get_payments":
                    limit = request.arguments.get("limit", 10)
                    result = await self.core_tools.get_payments(limit)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "check_connection":
                    result = await self.core_tools.check_connection()
                    status = "Connected" if result else "Disconnected"
                    return ToolCallResponse(content=[{"type": "text", "text": f"LNbits connection: {status}"}])

                # Payment tools
                elif tool_name == "pay_invoice":
                    bolt11 = request.arguments["bolt11"]
                    amount = request.arguments.get("amount")
                    result = await self.payment_tools.pay_invoice(bolt11, amount)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "get_payment_status":
                    payment_hash = request.arguments["payment_hash"]
                    result = await self.payment_tools.get_payment_status(payment_hash)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "decode_invoice":
                    bolt11 = request.arguments["bolt11"]
                    result = await self.payment_tools.decode_invoice(bolt11)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                elif tool_name == "pay_lightning_address":
                    lightning_address = request.arguments["lightning_address"]
                    amount_sats = request.arguments["amount_sats"]
                    comment = request.arguments.get("comment")
                    result = await self.payment_tools.pay_lightning_address(lightning_address, amount_sats, comment)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                # Invoice tools
                elif tool_name == "create_invoice":
                    amount = request.arguments["amount"]
                    memo = request.arguments.get("memo")
                    description_hash = request.arguments.get("description_hash")
                    expiry = request.arguments.get("expiry", 3600)
                    result = await self.invoice_tools.create_invoice(amount, memo, description_hash, expiry)
                    return ToolCallResponse(content=[{"type": "text", "text": str(result)}])

                else:
                    raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

            except LNbitsError as e:
                logger.error("LNbits API error", error=str(e), tool=tool_name)
                return ToolCallResponse(
                    content=[{"type": "text", "text": f"LNbits API error: {str(e)}"}],
                    isError=True
                )
            except ValidationError as e:
                logger.error("Validation error", error=str(e), tool=tool_name)
                return ToolCallResponse(
                    content=[{"type": "text", "text": f"Validation error: {str(e)}"}],
                    isError=True
                )
            except Exception as e:
                logger.error("Unexpected error", error=str(e), tool=tool_name, exc_info=True)
                return ToolCallResponse(
                    content=[{"type": "text", "text": f"Unexpected error: {str(e)}"}],
                    isError=True
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}


def create_app() -> FastAPI:
    """Create FastAPI application."""
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
    
    server = LNbitsHTTPServer()
    return server.app


async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    print(f"🚀 Starting LNbits MCP HTTP Server on {host}:{port}", file=sys.stderr)
    
    config = uvicorn.Config(
        "lnbits_mcp_server.http_server:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="LNbits MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    
    asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()