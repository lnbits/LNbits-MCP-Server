"""Configuration tools for LNbits MCP server."""

import json
import logging
from typing import Dict, Any, Optional

import structlog
from mcp.server import Server
from mcp.types import Tool, TextContent

from ..models.schemas import (
    ConfigureLNbitsRequest,
    ConfigurationStatusResponse,
    ConfigurationTestResponse,
)
from ..utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)


class ConfigTools:
    """Configuration tools for the LNbits MCP server."""

    def __init__(self, config_manager: RuntimeConfigManager):
        """Initialize configuration tools.
        
        Args:
            config_manager: Runtime configuration manager instance
        """
        self.config_manager = config_manager

    def register_tools(self, server: Server):
        """Register configuration tools with the MCP server.
        
        Args:
            server: MCP server instance
        """
        
        @server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available configuration tools."""
            return [
                Tool(
                    name="configure_lnbits",
                    description=f"""
                    <use_case>
                    Configure the user's LNbits connection parameters. The user can provide
                    the following parameters:
                    - lnbits_url: The base URL for the LNbits instance.
                    - api_key: The API key for the LNbits instance.
                    - bearer_token: The bearer token for the LNbits instance.
                    - oauth2_token: The OAuth2 token for the LNbits instance.
                    - auth_method: The authentication method to use.
                    - timeout: The request timeout in seconds.
                    - rate_limit_per_minute: The rate limit per minute.
                    </use_case>
                    <important_notes>
                    After setting the URL, API key, bearer token, or OAuth2 token you must double and triple check
                    that what you have set is the same as what the user has provided.
                    After setting the values, get the users balance to ensure that the values are correct.
                    </important_notes>
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lnbits_url": {
                                "type": "string",
                                "description": "Base URL for LNbits instance (e.g., https://demo.lnbits.com)"
                            },
                            "api_key": {
                                "type": "string",
                                "description": "API key for LNbits authentication"
                            },
                            "bearer_token": {
                                "type": "string",
                                "description": "Bearer token for authentication (alternative to api_key)"
                            },
                            "oauth2_token": {
                                "type": "string",
                                "description": "OAuth2 token for authentication (alternative to api_key)"
                            },
                            "auth_method": {
                                "type": "string",
                                "description": "Authentication method",
                                "enum": ["api_key_header", "api_key_query", "http_bearer", "oauth2"]
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Request timeout in seconds",
                                "minimum": 1,
                                "maximum": 300
                            },
                            "rate_limit_per_minute": {
                                "type": "integer",
                                "description": "Rate limit per minute",
                                "minimum": 1,
                                "maximum": 1000
                            }
                        },
                        "required": [],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_lnbits_configuration",
                    description="Get current LNbits configuration status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="test_lnbits_configuration",
                    description="Test the current LNbits configuration by making a test API call",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Handle configuration tool calls.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            List of text content responses
        """
        try:
            if name == "configure_lnbits":
                return await self._configure_lnbits(arguments)
            elif name == "get_lnbits_configuration":
                return await self._get_configuration()
            elif name == "test_lnbits_configuration":
                return await self._test_configuration()
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Configuration tool error: {e}", tool=name, args=arguments)
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    async def _configure_lnbits(self, arguments: Dict[str, Any]) -> list[TextContent]:
        """Configure LNbits connection parameters.
        
        Args:
            arguments: Configuration arguments
            
        Returns:
            List of text content responses
        """
        try:
            logger.info(f"Configuring LNbits with arguments: {arguments}")
            
            # Validate input
            config_request = ConfigureLNbitsRequest(**arguments)
            
            # Update configuration
            result = await self.config_manager.update_configuration(
                lnbits_url=str(config_request.lnbits_url) if config_request.lnbits_url else None,
                api_key=config_request.api_key,
                bearer_token=config_request.bearer_token,
                oauth2_token=config_request.oauth2_token,
                auth_method=config_request.auth_method,
                timeout=config_request.timeout,
                rate_limit_per_minute=config_request.rate_limit_per_minute,
            )
            
            logger.info(f"Configuration update result: {result}")
            
            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"✅ LNbits configuration updated successfully!\n\n"
                         f"Configuration:\n{json.dumps(result['config'], indent=2)}\n\n"
                         f"You can now use the LNbits tools with the new configuration."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Configuration update failed: {result['message']}"
                )]
                
        except Exception as e:
            logger.error(f"Configure LNbits error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Configuration error: {str(e)}"
            )]

    async def _get_configuration(self) -> list[TextContent]:
        """Get current configuration status.
        
        Returns:
            List of text content responses
        """
        try:
            status = self.config_manager.get_configuration_status()
            response = ConfigurationStatusResponse(**status)
            
            config_status = "✅ Runtime configuration active" if response.is_configured else "⚠️ Using environment variables"
            
            return [TextContent(
                type="text",
                text=f"LNbits Configuration Status:\n\n"
                     f"Status: {config_status}\n\n"
                     f"Current Configuration:\n{json.dumps(response.config, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Get configuration error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error getting configuration: {str(e)}"
            )]

    async def _test_configuration(self) -> list[TextContent]:
        """Test the current configuration.
        
        Returns:
            List of text content responses
        """
        try:
            test_result = await self.config_manager.test_configuration()
            response = ConfigurationTestResponse(**test_result)
            
            if response.success:
                wallet_info = response.wallet_info or {}
                return [TextContent(
                    type="text",
                    text=f"✅ LNbits configuration test successful!\n\n"
                         f"Connection Details:\n"
                         f"• Wallet ID: {wallet_info.get('id', 'N/A')}\n"
                         f"• Wallet Name: {wallet_info.get('name', 'N/A')}\n"
                         f"• Balance: {wallet_info.get('balance', 0)} msat\n\n"
                         f"You can now use all LNbits tools with confidence."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Configuration test failed: {response.message}\n\n"
                         f"Error: {response.error or 'Unknown error'}\n\n"
                         f"Please check your configuration and try again."
                )]
                
        except Exception as e:
            logger.error(f"Test configuration error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Configuration test error: {str(e)}"
            )]