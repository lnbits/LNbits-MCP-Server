"""Payment tools for LNbits MCP server."""

from typing import Any, Dict, List, Optional

import structlog

from ..client import LNbitsClient, LNbitsError
from ..models.schemas import DecodedInvoice, PayInvoiceRequest, Payment
from ..utils.runtime_config import RuntimeConfigManager

logger = structlog.get_logger(__name__)


class PaymentTools:
    """Payment-related tools."""

    def __init__(self, config_manager: RuntimeConfigManager):
        self.config_manager = config_manager

    async def pay_invoice(
        self, bolt11: str, amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Pay a Lightning invoice."""
        try:
            # Make payment directly
            client = await self.config_manager.get_client()
            response = await client.pay_invoice(bolt11, amount)

            payment_data = {
                "payment_hash": response.get("payment_hash"),
                "bolt11": bolt11,
                "amount": amount or response.get("amount", 0),
                "fee": response.get("fee", 0),
                "status": response.get("status", "pending"),
                "preimage": response.get("preimage"),
                "memo": response.get("memo"),
                "created_at": response.get("time"),
                "checking_id": response.get("checking_id"),
                "wallet_id": response.get("wallet_id"),
            }

            logger.info(
                "Payment initiated",
                payment_hash=payment_data["payment_hash"],
                amount=payment_data["amount"],
                status=payment_data["status"],
            )

            return payment_data

        except LNbitsError as e:
            logger.error("Failed to pay invoice", error=str(e), bolt11=bolt11[:50])
            raise
        except Exception as e:
            logger.error(
                "Unexpected error paying invoice", error=str(e), bolt11=bolt11[:50]
            )
            raise LNbitsError(f"Failed to pay invoice: {str(e)}")

    async def get_payment_status(self, payment_hash: str) -> Dict[str, Any]:
        """Get payment status by payment hash."""
        try:
            client = await self.config_manager.get_client()
            response = await client.get_payment_status(payment_hash)

            payment_status = {
                "payment_hash": payment_hash,
                "status": response.get("status", "unknown"),
                "amount": response.get("amount", 0),
                "fee": response.get("fee", 0),
                "bolt11": response.get("bolt11"),
                "memo": response.get("memo"),
                "time": response.get("time"),
                "pending": response.get("pending", False),
                "paid": response.get("paid", False),
                "preimage": response.get("preimage"),
            }

            logger.info(
                "Retrieved payment status",
                payment_hash=payment_hash,
                status=payment_status["status"],
            )

            return payment_status

        except LNbitsError as e:
            logger.error(
                "Failed to get payment status", error=str(e), payment_hash=payment_hash
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error getting payment status",
                error=str(e),
                payment_hash=payment_hash,
            )
            raise LNbitsError(f"Failed to get payment status: {str(e)}")

    async def decode_invoice(self, bolt11: str) -> Dict[str, Any]:
        """Decode a Lightning invoice to see its details."""
        try:
            client = await self.config_manager.get_client()
            response = await client.decode_invoice(bolt11)

            decoded_data = {
                "payment_hash": response.get("payment_hash"),
                "amount_msat": response.get("amount_msat", 0),
                "amount_sat": response.get("amount_msat", 0) // 1000,
                "description": response.get("description"),
                "description_hash": response.get("description_hash"),
                "payee": response.get("payee"),
                "date": response.get("date"),
                "expiry": response.get("expiry"),
                "min_final_cltv_expiry": response.get("min_final_cltv_expiry", 9),
                "route_hints": response.get("route_hints", []),
                "features": response.get("features", {}),
                "is_expired": False,  # TODO: Calculate based on date + expiry
                "is_zero_amount": response.get("amount_msat", 0) == 0,
            }

            logger.info(
                "Decoded invoice",
                payment_hash=decoded_data["payment_hash"],
                amount=decoded_data["amount_msat"],
                description=decoded_data["description"],
            )

            return decoded_data

        except LNbitsError as e:
            logger.error("Failed to decode invoice", error=str(e), bolt11=bolt11[:50])
            raise
        except Exception as e:
            logger.error(
                "Unexpected error decoding invoice", error=str(e), bolt11=bolt11[:50]
            )
            raise LNbitsError(f"Failed to decode invoice: {str(e)}")

    async def pay_lightning_address(
        self, lightning_address: str, amount_sats: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pay a Lightning address (e.g., user@domain.com)."""
        try:
            # Make payment to Lightning address
            client = await self.config_manager.get_client()
            response = await client.pay_lightning_address(
                lightning_address, amount_sats, comment
            )

            payment_data = {
                "payment_hash": response.get("payment_hash"),
                "lightning_address": lightning_address,
                "amount": amount_sats,
                "fee": response.get("fee", 0),
                "status": response.get("status", "pending"),
                "preimage": response.get("preimage"),
                "memo": response.get("memo"),
                "comment": comment,
                "created_at": response.get("time"),
                "checking_id": response.get("checking_id"),
                "wallet_id": response.get("wallet_id"),
                "bolt11": response.get("bolt11"),
            }

            logger.info(
                "Payment to Lightning address initiated",
                lightning_address=lightning_address,
                payment_hash=payment_data["payment_hash"],
                amount=payment_data["amount"],
                status=payment_data["status"],
            )

            return payment_data

        except LNbitsError as e:
            logger.error(
                "Failed to pay Lightning address",
                error=str(e),
                lightning_address=lightning_address,
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error paying Lightning address",
                error=str(e),
                lightning_address=lightning_address,
            )
            raise LNbitsError(f"Failed to pay Lightning address: {str(e)}")
