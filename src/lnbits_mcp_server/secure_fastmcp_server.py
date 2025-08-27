"""Secure FastMCP Server with session-based credential isolation."""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional
import json
import structlog
from fastmcp import FastMCP
from pydantic import ValidationError

from .client import LNbitsClient, LNbitsConfig, LNbitsError
from .session_manager import get_session_manager, cleanup_session_manager, SessionTools

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

# Create FastMCP app with session support
mcp = FastMCP("LNbits MCP Server 🚀 (Secure Multi-User)")


def extract_session_id(arguments: Dict[str, Any]) -> Optional[str]:
    """Extract session ID from tool arguments."""
    return arguments.pop("__session_id", None)


def get_session_tools(session_id: Optional[str]) -> SessionTools:
    """Get or create session tools for the given session ID."""
    session_manager = get_session_manager()
    
    if not session_id:
        # Create new session for clients that don't provide session ID
        new_session_id = session_manager.create_session()
        logger.info("Created new session for client", session_id=new_session_id)
        return session_manager.get_session(new_session_id)
    
    session_tools = session_manager.get_session(session_id)
    if not session_tools:
        # Session expired or invalid, create new one
        new_session_id = session_manager.create_session()
        session_tools = session_manager.get_session(new_session_id)
        logger.info("Created new session for expired/invalid session", 
                   old_session_id=session_id, new_session_id=new_session_id)
    
    return session_tools


async def handle_tool_error(error: Exception, tool_name: str, session_id: str) -> str:
    """Handle tool execution errors consistently."""
    if isinstance(error, LNbitsError):
        logger.error("LNbits API error", error=str(error), tool=tool_name, session_id=session_id)
        return f"LNbits API error: {str(error)}"
    elif isinstance(error, ValidationError):
        logger.error("Validation error", error=str(error), tool=tool_name, session_id=session_id)
        return f"Validation error: {str(error)}"
    else:
        logger.error("Unexpected error", error=str(error), tool=tool_name, session_id=session_id, exc_info=True)
        return f"Unexpected error: {str(error)}"


# Session Management Tools
@mcp.tool()
async def create_session() -> str:
    """Create a new session for credential isolation.
    
    Returns the session ID that should be included in subsequent tool calls.
    Each session maintains its own LNbits configuration and credentials.
    """
    try:
        session_manager = get_session_manager()
        session_id = session_manager.create_session()
        return json.dumps({
            "success": True,
            "session_id": session_id,
            "message": f"Created new session: {session_id}. Include this session_id in all subsequent tool calls for credential isolation."
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create session: {str(e)}"
        })


@mcp.tool()
async def get_session_info(__session_id: Optional[str] = None) -> str:
    """Get information about the current session."""
    try:
        session_tools = get_session_tools(__session_id)
        session_manager = get_session_manager()
        
        return json.dumps({
            "session_id": session_tools.session_id,
            "created_at": session_tools.created_at.isoformat(),
            "last_accessed": session_tools.last_accessed.isoformat(),
            "total_sessions": session_manager.get_session_count(),
            "is_configured": session_tools.config_manager.is_configured
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get session info: {str(e)}"
        })


# Configuration Tools
@mcp.tool()
async def configure_lnbits(
    __session_id: Optional[str] = None,
    lnbits_url: Optional[str] = None,
    api_key: Optional[str] = None,
    bearer_token: Optional[str] = None,
    oauth2_token: Optional[str] = None,
    auth_method: Optional[str] = None,
    timeout: Optional[int] = None,
    rate_limit_per_minute: Optional[int] = None,
) -> str:
    """Configure LNbits connection parameters for this session.
    
    This configuration is isolated to your session and won't affect other users.
    """
    try:
        session_tools = get_session_tools(__session_id)
        
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
        
        result = await session_tools.config_tools.call_tool("configure_lnbits", arguments)
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "configure_lnbits", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def get_lnbits_configuration(__session_id: Optional[str] = None) -> str:
    """Get current LNbits configuration status for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.config_tools.call_tool("get_lnbits_configuration", {})
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "get_lnbits_configuration", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def test_lnbits_configuration(__session_id: Optional[str] = None) -> str:
    """Test the current LNbits configuration for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.config_tools.call_tool("test_lnbits_configuration", {})
        if isinstance(result, list) and result:
            return result[0].text
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "test_lnbits_configuration", session_tools.session_id if 'session_tools' in locals() else "unknown")


# Core Tools
@mcp.tool()
async def get_wallet_details(__session_id: Optional[str] = None) -> str:
    """Get the details of your wallet for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.core_tools.get_wallet_details()
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "get_wallet_details", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def get_wallet_balance(__session_id: Optional[str] = None) -> str:
    """Get the current balance of your wallet for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.core_tools.get_wallet_balance()
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "get_wallet_balance", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def get_payments(__session_id: Optional[str] = None, limit: int = 10) -> str:
    """Get payment history for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.core_tools.get_payments(limit)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "get_payments", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def check_connection(__session_id: Optional[str] = None) -> str:
    """Check connection to LNbits instance for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.core_tools.check_connection()
        status = "Connected" if result else "Disconnected"
        return f"LNbits connection: {status} (Session: {session_tools.session_id})"
    except Exception as e:
        return await handle_tool_error(e, "check_connection", session_tools.session_id if 'session_tools' in locals() else "unknown")


# Payment Tools
@mcp.tool()
async def pay_invoice(__session_id: Optional[str] = None, bolt11: str = "", amount: Optional[int] = None) -> str:
    """Pay a lightning invoice using this session's wallet."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.payment_tools.pay_invoice(bolt11, amount)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "pay_invoice", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def get_payment_status(__session_id: Optional[str] = None, payment_hash: str = "") -> str:
    """Get the status of a lightning payment for this session."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.payment_tools.get_payment_status(payment_hash)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "get_payment_status", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def decode_invoice(__session_id: Optional[str] = None, bolt11: str = "") -> str:
    """Decode a BOLT11 lightning invoice."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.payment_tools.decode_invoice(bolt11)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "decode_invoice", session_tools.session_id if 'session_tools' in locals() else "unknown")


@mcp.tool()
async def pay_lightning_address(
    __session_id: Optional[str] = None,
    lightning_address: str = "", 
    amount_sats: int = 0, 
    comment: Optional[str] = None
) -> str:
    """Send bitcoin sats to a lightning address using this session's wallet."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.payment_tools.pay_lightning_address(lightning_address, amount_sats, comment)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "pay_lightning_address", session_tools.session_id if 'session_tools' in locals() else "unknown")


# Invoice Tools
@mcp.tool()
async def create_invoice(
    __session_id: Optional[str] = None,
    amount: int = 0,
    memo: Optional[str] = None,
    description_hash: Optional[str] = None,
    expiry: int = 3600
) -> str:
    """Create a new lightning invoice using this session's wallet."""
    try:
        session_tools = get_session_tools(__session_id)
        result = await session_tools.invoice_tools.create_invoice(amount, memo, description_hash, expiry)
        return str(result)
    except Exception as e:
        return await handle_tool_error(e, "create_invoice", session_tools.session_id if 'session_tools' in locals() else "unknown")


def main():
    """Main entry point."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="LNbits Secure FastMCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    print(f"🚀 Starting Secure LNbits FastMCP Server on {args.host}:{args.port}", file=sys.stderr)
    print(f"🔒 Multi-user session isolation enabled", file=sys.stderr)
    print(f"🌍 Working directory: {os.getcwd()}", file=sys.stderr)
    
    def cleanup_handler(signum, frame):
        """Handle shutdown signals."""
        print("\n🛑 Shutting down server...", file=sys.stderr)
        loop = asyncio.get_event_loop()
        loop.create_task(cleanup_session_manager())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # Run the FastMCP server over HTTP
        mcp.run(transport="sse", host=args.host, port=args.port)
    finally:
        # Cleanup on exit
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_session_manager())
        loop.close()


if __name__ == "__main__":
    main()