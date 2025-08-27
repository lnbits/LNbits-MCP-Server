"""LNbits FastMCP Server implementation."""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

import structlog
from fastmcp import FastMCP
from pydantic import ValidationError

from .client import LNbitsClient, LNbitsConfig, LNbitsError
from .tools.config_tools import ConfigTools
from .tools.core import CoreTools
from .tools.invoices import InvoiceTools
from .tools.payments import PaymentTools
from .utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)

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

# Create FastMCP app
mcp = FastMCP("LNbits MCP Server 🚀")

# Global instances - will be initialized in main()
config_manager: Optional[RuntimeConfigManager] = None
core_tools: Optional[CoreTools] = None
payment_tools: Optional[PaymentTools] = None
invoice_tools: Optional[InvoiceTools] = None
config_tools: Optional[ConfigTools] = None


def initialize_tools():
    """Initialize tool handlers."""
    global config_manager, core_tools, payment_tools, invoice_tools, config_tools
    
    config = LNbitsConfig()
    config_manager = RuntimeConfigManager(config)
    core_tools = CoreTools(config_manager)
    payment_tools = PaymentTools(config_manager)
    invoice_tools = InvoiceTools(config_manager)
    config_tools = ConfigTools(config_manager)


# Configuration Tools
@mcp.tool()
async def configure_lnbits(
    lnbits_url: Optional[str] = None,
    api_key: Optional[str] = None,
    bearer_token: Optional[str] = None,
    oauth2_token: Optional[str] = None,
    auth_method: Optional[str] = None,
    timeout: Optional[int] = None,
    rate_limit_per_minute: Optional[int] = None,
) -> str:
    """Configure LNbits connection parameters at runtime."""
    try:
        arguments = {
            k: v for k, v in {
                "lnbits_url": lnbits_url,
                "api_key": api_key,
                "bearer_token": bearer_token,
                "oauth2_token": oauth2_token,
                "auth_method": auth_method,
                "timeout": timeout,
                "rate_limit_per_minute": rate_limit_per_minute,
            }.items() if v is not None
        }
        result = await config_tools.call_tool("configure_lnbits", arguments)
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        logger.error("Error in configure_lnbits", error=str(e))
        return f"Error configuring LNbits: {str(e)}"


@mcp.tool()
async def get_lnbits_configuration() -> str:
    """Get current LNbits configuration status."""
    try:
        result = await config_tools.call_tool("get_lnbits_configuration", {})
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        logger.error("Error in get_lnbits_configuration", error=str(e))
        return f"Error getting configuration: {str(e)}"


@mcp.tool()
async def test_lnbits_configuration() -> str:
    """Test the current LNbits configuration by making a test API call."""
    try:
        result = await config_tools.call_tool("test_lnbits_configuration", {})
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        logger.error("Error in test_lnbits_configuration", error=str(e))
        return f"Error testing configuration: {str(e)}"


# Core Tools
@mcp.tool()
async def get_wallet_details() -> str:
    """Get the details of the user's wallet.
    
    Returns wallet details including ID, name, user, balance in msats (sats * 1000), 
    currency, and whether the wallet has admin and invoice keys.
    The balance is converted to sats for user display (divide by 1000).
    """
    try:
        result = await core_tools.get_wallet_details()
        return str(result)
    except Exception as e:
        logger.error("Error in get_wallet_details", error=str(e))
        return f"Error getting wallet details: {str(e)}"


@mcp.tool()
async def get_wallet_balance() -> str:
    """Get the current balance of the user's wallet.
    
    Returns balance in both msats and sats. Tell the user only their balance in sats.
    """
    try:
        result = await core_tools.get_wallet_balance()
        return str(result)
    except Exception as e:
        logger.error("Error in get_wallet_balance", error=str(e))
        return f"Error getting wallet balance: {str(e)}"


@mcp.tool()
async def get_payments(limit: int = 10) -> str:
    """Get payment history."""
    try:
        result = await core_tools.get_payments(limit)
        return str(result)
    except Exception as e:
        logger.error("Error in get_payments", error=str(e))
        return f"Error getting payments: {str(e)}"


@mcp.tool()
async def check_connection() -> str:
    """Check connection to LNbits instance."""
    try:
        result = await core_tools.check_connection()
        status = "Connected" if result else "Disconnected"
        return f"LNbits connection: {status}"
    except Exception as e:
        logger.error("Error in check_connection", error=str(e))
        return f"Error checking connection: {str(e)}"


# Payment Tools
@mcp.tool()
async def pay_invoice(bolt11: str, amount: Optional[int] = None) -> str:
    """Pay a lightning invoice.
    
    The user will provide the BOLT11 invoice string. The amount to pay is in sats.
    """
    try:
        result = await payment_tools.pay_invoice(bolt11, amount)
        return str(result)
    except Exception as e:
        logger.error("Error in pay_invoice", error=str(e))
        return f"Error paying invoice: {str(e)}"


@mcp.tool()
async def get_payment_status(payment_hash: str) -> str:
    """Get the status of a lightning payment using the payment hash."""
    try:
        result = await payment_tools.get_payment_status(payment_hash)
        return str(result)
    except Exception as e:
        logger.error("Error in get_payment_status", error=str(e))
        return f"Error getting payment status: {str(e)}"


@mcp.tool()
async def decode_invoice(bolt11: str) -> str:
    """Decode a BOLT11 lightning invoice to get amount, memo, and payment hash.
    
    The amount is in msats (millisatoshis = sats * 1000).
    """
    try:
        result = await payment_tools.decode_invoice(bolt11)
        return str(result)
    except Exception as e:
        logger.error("Error in decode_invoice", error=str(e))
        return f"Error decoding invoice: {str(e)}"


@mcp.tool()
async def pay_lightning_address(
    lightning_address: str, 
    amount_sats: int, 
    comment: Optional[str] = None
) -> str:
    """Send bitcoin sats to another person's wallet using their lightning address.
    
    The amount to pay is in sats NOT msats.
    """
    try:
        result = await payment_tools.pay_lightning_address(lightning_address, amount_sats, comment)
        return str(result)
    except Exception as e:
        logger.error("Error in pay_lightning_address", error=str(e))
        return f"Error paying lightning address: {str(e)}"


# Invoice Tools
@mcp.tool()
async def create_invoice(
    amount: int,
    memo: Optional[str] = None,
    description_hash: Optional[str] = None,
    expiry: int = 3600
) -> str:
    """Create a new lightning invoice.
    
    The amount is in sats. The response includes both a BOLT11 invoice string and 
    a QR code URL that can be used to display a scannable QR code image.
    """
    try:
        result = await invoice_tools.create_invoice(amount, memo, description_hash, expiry)
        return str(result)
    except Exception as e:
        logger.error("Error in create_invoice", error=str(e))
        return f"Error creating invoice: {str(e)}"


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LNbits FastMCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Initialize tool handlers
    initialize_tools()
    
    print(f"🚀 Starting LNbits FastMCP Server on {args.host}:{args.port}", file=sys.stderr)
    print(f"🌍 Working directory: {os.getcwd()}", file=sys.stderr)
    print(f"🔐 Environment variables:", file=sys.stderr)
    print(f"  LNBITS_URL: {os.getenv('LNBITS_URL', 'NOT SET')}", file=sys.stderr)
    print(
        f"  LNBITS_API_KEY: {'SET' if os.getenv('LNBITS_API_KEY') else 'NOT SET'}",
        file=sys.stderr,
    )
    
    # Run the FastMCP server over HTTP
    mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()