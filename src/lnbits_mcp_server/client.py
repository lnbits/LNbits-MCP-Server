"""LNbits API client for MCP server."""

import asyncio
import json
import re
import sys
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from pydantic import BaseModel, Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings

from .utils.auth import AuthConfig, AuthMethod

logger = structlog.get_logger(__name__)


class LNbitsConfig(BaseSettings):
    """Configuration for LNbits client."""

    lnbits_url: HttpUrl = Field(
        default="https://demo.lnbits.com", description="Base URL for LNbits instance"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for LNbits authentication",
    )
    bearer_token: Optional[str] = Field(
        default=None, description="Bearer token for authentication"
    )
    oauth2_token: Optional[str] = Field(
        default=None, description="OAuth2 token for authentication"
    )
    auth_method: AuthMethod = Field(
        default=AuthMethod.API_KEY_HEADER, description="Authentication method to use"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed requests"
    )
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")

    model_config = {
        "env_prefix": "LNBITS_",
        "case_sensitive": False,
    }


class LNbitsError(Exception):
    """Base exception for LNbits API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class LNbitsClient:
    """Asynchronous client for LNbits API."""

    def __init__(self, config: Optional[LNbitsConfig] = None):
        self.config = config or LNbitsConfig()
        self.auth_config = AuthConfig(
            api_key=self.config.api_key,
            bearer_token=self.config.bearer_token,
            oauth2_token=self.config.oauth2_token,
            auth_method=self.config.auth_method,
        )
        self.client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit_per_minute)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self.client:
            self.client = httpx.AsyncClient(
                base_url=str(self.config.lnbits_url),
                timeout=self.config.timeout,
                headers=self.auth_config.get_headers(),
            )

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the LNbits API."""
        await self._ensure_client()

        # Add auth query params if needed
        if params is None:
            params = {}
        params.update(self.auth_config.get_query_params())

        # Debug output for Claude Desktop logs
        print(
            f"🌐 Making API request to: {self.config.lnbits_url}{path}", file=sys.stderr
        )
        print(f"🔑 Auth headers: {self.auth_config.get_headers()}", file=sys.stderr)
        print(f"🔍 Auth method: {self.auth_config.auth_method}", file=sys.stderr)
        print(
            f"🔐 Auth configured: {self.auth_config.is_configured()}", file=sys.stderr
        )

        # Rate limiting
        async with self._rate_limiter:
            try:
                response = await self.client.request(
                    method=method, url=path, params=params, json=json, **kwargs
                )

                # Log request details
                logger.info(
                    "API request",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration=response.elapsed.total_seconds(),
                )

                # Handle errors
                if response.status_code >= 400:
                    error_msg = f"API request failed: {response.status_code}"
                    try:
                        error_detail = response.json()
                        if "detail" in error_detail:
                            error_msg += f" - {error_detail['detail']}"
                    except:
                        error_msg += f" - {response.text}"

                    # Debug output for Claude Desktop logs
                    print(
                        f"❌ HTTP {response.status_code} error from {self.config.lnbits_url}{path}",
                        file=sys.stderr,
                    )
                    print(f"❌ Response: {response.text[:200]}...", file=sys.stderr)

                    logger.error(
                        "API error",
                        status_code=response.status_code,
                        error=error_msg,
                        path=path,
                    )
                    raise LNbitsError(error_msg, response.status_code)

                # Return JSON response
                return response.json()

            except httpx.RequestError as e:
                logger.error("Request error", error=str(e), path=path)
                raise LNbitsError(f"Request failed: {str(e)}")

    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET request."""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST request."""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """PUT request."""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return await self._request("DELETE", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Dict[str, Any]:
        """PATCH request."""
        return await self._request("PATCH", path, **kwargs)

    # Core API methods
    async def get_wallet_details(self) -> Dict[str, Any]:
        """Get wallet details."""
        return await self.get("/api/v1/wallet")

    async def get_wallet_balance(self) -> Dict[str, Any]:
        """Get wallet balance from wallet details."""
        wallet_data = await self.get("/api/v1/wallet")
        return {"balance": wallet_data.get("balance", 0)}

    async def get_payments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history."""
        response = await self.get("/api/v1/payments", params={"limit": limit})
        return response if isinstance(response, list) else []

    async def create_invoice(
        self,
        amount: int,
        memo: Optional[str] = None,
        description_hash: Optional[str] = None,
        expiry: Optional[int] = None,
        unit: str = "sat",
    ) -> Dict[str, Any]:
        """Create a new invoice."""
        data = {
            "out": False,  # Incoming payment (creating invoice)
            "amount": amount,
            "unit": unit,
            "memo": memo or "",
            "internal": False,
        }
        if description_hash:
            data["description_hash"] = description_hash
        if expiry:
            data["expiry"] = expiry

        return await self.post("/api/v1/payments", json=data)

    async def pay_invoice(
        self,
        bolt11: str,
        amount: Optional[int] = None,
        unit: str = "sat",
    ) -> Dict[str, Any]:
        """Pay a lightning invoice."""
        data = {"out": True, "bolt11": bolt11}
        print(f"💰 Paying invoice: {bolt11} with amount: {amount}", file=sys.stderr)
        if amount:
            print(f"💰 Amount: {amount}", file=sys.stderr)
            data["amount"] = amount
        print(f"💰 Data: {data}", file=sys.stderr)

        return await self.post("/api/v1/payments", json=data)

    async def get_payment_status(self, payment_hash: str) -> Dict[str, Any]:
        """Get payment status."""
        return await self.get(f"/api/v1/payments/{payment_hash}")

    async def decode_invoice(self, bolt11: str) -> Dict[str, Any]:
        """Decode a lightning invoice."""
        return await self.post("/api/v1/payments/decode", json={"data": bolt11})

    async def generate_qr_code(self, data: str) -> str:
        """Generate QR code URL for given data.

        Args:
            data: The data to encode in the QR code (e.g., BOLT11 invoice)

        Returns:
            URL to the QR code image
        """
        # URL encode the data parameter
        from urllib.parse import quote

        encoded_data = quote(data, safe="")
        qr_path = f"api/v1/qrcode/{encoded_data}"

        # Return the full URL to the QR code image using urljoin for proper URL construction
        return urljoin(str(self.config.lnbits_url), qr_path)

    async def check_connection(self) -> bool:
        """Check if connection to LNbits is working."""
        try:
            await self.get("/api/v1/wallet")
            return True
        except Exception as e:
            logger.error("Connection check failed", error=str(e))
            return False

    async def resolve_lightning_address(self, lightning_address: str) -> Optional[str]:
        """Resolve a Lightning address to an LNURL-pay URL.

        Args:
            lightning_address: Lightning address in format user@domain.com

        Returns:
            LNURL-pay URL if successful, None otherwise
        """
        # Validate lightning address format
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", lightning_address):
            raise LNbitsError(f"Invalid lightning address format: {lightning_address}")

        try:
            # Split the address
            user, domain = lightning_address.split("@")

            # Create well-known URL
            well_known_url = f"https://{domain}/.well-known/lnurlp/{user}"

            # Make request to well-known endpoint
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(well_known_url)

                if response.status_code != 200:
                    logger.error(
                        "Failed to resolve lightning address",
                        address=lightning_address,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return None

                # Parse LNURL-pay response
                lnurl_data = response.json()

                # Validate required fields
                if not all(
                    key in lnurl_data
                    for key in ["callback", "minSendable", "maxSendable"]
                ):
                    logger.error(
                        "Invalid LNURL-pay response",
                        address=lightning_address,
                        response=lnurl_data,
                    )
                    return None

                logger.info(
                    "Successfully resolved lightning address",
                    address=lightning_address,
                    callback=lnurl_data["callback"],
                    min_sendable=lnurl_data["minSendable"],
                    max_sendable=lnurl_data["maxSendable"],
                )

                return lnurl_data["callback"]

        except Exception as e:
            logger.error(
                "Error resolving lightning address",
                address=lightning_address,
                error=str(e),
            )
            return None

    async def get_lnurl_pay_invoice(
        self, callback_url: str, amount_msats: int, comment: Optional[str] = None
    ) -> Optional[str]:
        """Get invoice from LNURL-pay callback.

        Args:
            callback_url: LNURL-pay callback URL
            amount_msats: Amount in millisatoshis
            comment: Optional comment for the payment

        Returns:
            BOLT11 invoice if successful, None otherwise
        """
        try:
            # Prepare callback parameters
            params = {"amount": amount_msats}

            if comment:
                params["comment"] = comment

            # Make request to callback URL
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(callback_url, params=params)

                if response.status_code != 200:
                    logger.error(
                        "LNURL-pay callback failed",
                        callback_url=callback_url,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return None

                # Parse response
                callback_data = response.json()

                # Check for error
                if "reason" in callback_data:
                    logger.error(
                        "LNURL-pay callback error",
                        callback_url=callback_url,
                        reason=callback_data["reason"],
                    )
                    return None

                # Extract invoice
                if "pr" not in callback_data:
                    logger.error(
                        "No invoice in LNURL-pay response",
                        callback_url=callback_url,
                        response=callback_data,
                    )
                    return None

                invoice = callback_data["pr"]
                logger.info(
                    "Successfully got LNURL-pay invoice",
                    callback_url=callback_url,
                    amount=amount_msats,
                    invoice=invoice[:50] + "...",
                )

                return invoice

        except Exception as e:
            logger.error(
                "Error getting LNURL-pay invoice",
                callback_url=callback_url,
                error=str(e),
            )
            return None

    async def pay_lightning_address(
        self, lightning_address: str, amount_sats: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pay a Lightning address.

        Args:
            lightning_address: Lightning address in format user@domain.com
            amount_sats: Amount in satoshis
            comment: Optional comment for the payment

        Returns:
            Payment response from LNbits
        """
        print(
            f"💰 Paying Lightning address: {lightning_address} with {amount_sats} sats",
            file=sys.stderr,
        )

        # Convert sats to millisats
        amount_msats = amount_sats * 1000

        # Resolve lightning address to LNURL-pay callback
        callback_url = await self.resolve_lightning_address(lightning_address)
        if not callback_url:
            raise LNbitsError(
                f"Failed to resolve lightning address: {lightning_address}"
            )

        # Get invoice from LNURL-pay callback
        invoice = await self.get_lnurl_pay_invoice(callback_url, amount_msats, comment)
        if not invoice:
            raise LNbitsError(
                f"Failed to get invoice for lightning address: {lightning_address}"
            )

        # Pay the invoice
        return await self.pay_invoice(invoice, amount_sats)
