"""Invoice management tools for LNbits MCP server."""

from typing import Any, Dict, List, Optional

import structlog

from ..client import LNbitsClient, LNbitsError
from ..models.schemas import CreateInvoiceRequest, Invoice

logger = structlog.get_logger(__name__)


class InvoiceTools:
    """Invoice management tools."""

    def __init__(self, client: LNbitsClient):
        self.client = client

    async def create_invoice(
        self,
        amount: int,
        memo: Optional[str] = None,
        description_hash: Optional[str] = None,
        expiry: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new Lightning invoice."""
        try:
            response = await self.client.create_invoice(
                amount=amount,
                memo=memo,
                description_hash=description_hash,
                expiry=expiry,
            )

            invoice_info = {
                "payment_hash": response.get("payment_hash"),
                "bolt11": response.get("payment_request", response.get("bolt11")),
                "amount": amount,
                "memo": memo,
                "description_hash": description_hash,
                "expiry": expiry or 3600,
                "created_at": response.get("time"),
                "paid": False,
                "settled": False,
                "expires_at": None,  # TODO: Calculate from created_at + expiry
                "qr_code": f"lightning:{response.get('payment_request', response.get('bolt11'))}",
                "status": response.get("status", "pending"),
            }

            logger.info(
                "Created invoice",
                payment_hash=invoice_info["payment_hash"],
                amount=amount,
                memo=memo,
            )

            return invoice_info

        except LNbitsError as e:
            logger.error("Failed to create invoice", error=str(e), amount=amount)
            raise
        except Exception as e:
            logger.error(
                "Unexpected error creating invoice", error=str(e), amount=amount
            )
            raise LNbitsError(f"Failed to create invoice: {str(e)}")
