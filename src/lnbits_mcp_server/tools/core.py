"""Core wallet tools for LNbits MCP server."""

from typing import Any, Dict, List, Optional

import structlog

from ..client import LNbitsClient, LNbitsError
from ..models.schemas import Payment, WalletBalance, WalletDetails
from ..utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)


class CoreTools:
    """Core wallet tools."""

    def __init__(self, config_manager: RuntimeConfigManager):
        self.config_manager = config_manager

    async def get_wallet_details(self) -> Dict[str, Any]:
        """Get wallet details including balance and keys."""
        try:
            client = await self.config_manager.get_client()
            response = await client.get_wallet_details()

            # Parse response into structured format
            wallet_data = {
                "id": response.get("id"),
                "name": response.get("name"),
                "user": response.get("user"),
                "balance_msat": response.get("balance", 0),
                "currency": "msat",
                "has_admin_key": bool(response.get("adminkey")),
                "has_invoice_key": bool(response.get("inkey")),
            }

            logger.info("Retrieved wallet details", wallet_id=wallet_data["id"])
            return wallet_data

        except LNbitsError as e:
            logger.error("Failed to get wallet details", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error getting wallet details", error=str(e))
            raise LNbitsError(f"Failed to get wallet details: {str(e)}")

    async def get_wallet_balance(self) -> Dict[str, Any]:
        """Get current wallet balance."""
        try:
            client = await self.config_manager.get_client()
            response = await client.get_wallet_balance()

            # Handle different response formats
            if isinstance(response, dict):
                balance = response.get("balance", 0)
            else:
                # Fallback to wallet details if balance endpoint doesn't exist
                wallet_details = await client.get_wallet_details()
                balance = wallet_details.get("balance", 0)

            balance_data = {
                "balance": balance,
                "balance_sat": balance // 1000 if balance > 0 else 0,
                "currency": "msat",
                "formatted": f"{balance:,} msat ({balance // 1000:,} sat)",
            }

            logger.info("Retrieved wallet balance", balance=balance)
            return balance_data

        except LNbitsError as e:
            logger.error("Failed to get wallet balance", error=str(e))
            # Try fallback method
            try:
                wallet_details = await self.get_wallet_details()
                return {
                    "balance": wallet_details["balance_msat"],
                    "balance_sat": wallet_details["balance_msat"] // 1000,
                    "currency": "msat",
                    "formatted": f"{wallet_details['balance_msat']:,} msat ({wallet_details['balance_msat'] // 1000:,} sat)",
                }
            except Exception:
                raise e
        except Exception as e:
            logger.error("Unexpected error getting wallet balance", error=str(e))
            raise LNbitsError(f"Failed to get wallet balance: {str(e)}")

    async def get_payments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history."""
        try:
            client = await self.config_manager.get_client()
            response = await client.get_payments(limit)

            # Parse payments into structured format
            payments = []
            for payment_data in response:
                payment = {
                    "payment_hash": payment_data.get("payment_hash"),
                    "bolt11": payment_data.get("bolt11"),
                    "amount": payment_data.get("amount", 0),
                    "fee": payment_data.get("fee", 0),
                    "memo": payment_data.get("memo"),
                    "time": payment_data.get("time"),
                    "status": payment_data.get("status", "unknown"),
                    "pending": payment_data.get("pending", False),
                    "type": (
                        "outgoing" if payment_data.get("amount", 0) < 0 else "incoming"
                    ),
                }
                payments.append(payment)

            logger.info("Retrieved payment history", count=len(payments))
            return payments

        except LNbitsError as e:
            logger.error("Failed to get payment history", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error getting payment history", error=str(e))
            raise LNbitsError(f"Failed to get payment history: {str(e)}")

    async def check_connection(self) -> bool:
        """Check connection to LNbits instance."""
        try:
            client = await self.config_manager.get_client()
            is_connected = await client.check_connection()

            logger.info("Connection check", connected=is_connected)
            return is_connected

        except Exception as e:
            logger.error("Connection check failed", error=str(e))
            return False
