"""Pydantic models for LNbits API responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


class PaymentStatus(str, Enum):
    """Payment status enum."""

    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class WalletBalance(BaseModel):
    """Wallet balance model."""

    balance: int = Field(description="Wallet balance in millisatoshis")
    currency: str = Field(default="msat", description="Currency unit")

    @validator("balance")
    def validate_balance(cls, v):
        if v < 0:
            logger.warning("Negative balance detected", balance=v)
        return v


class WalletDetails(BaseModel):
    """Wallet details model."""

    id: str = Field(description="Wallet ID")
    name: str = Field(description="Wallet name")
    user: str = Field(description="User ID")
    adminkey: Optional[str] = Field(description="Admin key", default=None)
    inkey: Optional[str] = Field(description="Invoice key", default=None)
    balance_msat: int = Field(description="Balance in millisatoshis")
    currency: str = Field(default="msat", description="Currency unit")

    class Config:
        extra = "allow"


class Payment(BaseModel):
    """Payment model."""

    payment_hash: str = Field(description="Payment hash")
    bolt11: Optional[str] = Field(description="BOLT11 invoice", default=None)
    amount: int = Field(description="Amount in millisatoshis")
    fee: int = Field(description="Fee in millisatoshis", default=0)
    memo: Optional[str] = Field(description="Payment memo", default=None)
    time: datetime = Field(description="Payment timestamp")
    status: PaymentStatus = Field(description="Payment status")
    pending: bool = Field(description="Is payment pending", default=False)

    class Config:
        extra = "allow"


class Invoice(BaseModel):
    """Invoice model."""

    payment_hash: str = Field(description="Payment hash")
    bolt11: str = Field(description="BOLT11 invoice string")
    amount: int = Field(description="Amount in millisatoshis")
    memo: Optional[str] = Field(description="Invoice memo", default=None)
    description_hash: Optional[str] = Field(
        description="Description hash", default=None
    )
    expiry: Optional[int] = Field(description="Expiry in seconds", default=None)
    time: datetime = Field(description="Invoice creation time")
    paid: bool = Field(description="Is invoice paid", default=False)

    class Config:
        extra = "allow"


class DecodedInvoice(BaseModel):
    """Decoded invoice model."""

    payment_hash: str = Field(description="Payment hash")
    amount_msat: int = Field(description="Amount in millisatoshis")
    description: Optional[str] = Field(description="Invoice description", default=None)
    description_hash: Optional[str] = Field(
        description="Description hash", default=None
    )
    payee: Optional[str] = Field(description="Payee public key", default=None)
    date: datetime = Field(description="Invoice date")
    expiry: int = Field(description="Expiry in seconds")
    min_final_cltv_expiry: int = Field(description="Min final CLTV expiry", default=9)

    class Config:
        extra = "allow"


class CreateInvoiceRequest(BaseModel):
    """Request model for creating invoices."""

    amount: int = Field(description="Amount in millisatoshis", gt=0)
    memo: Optional[str] = Field(description="Invoice memo", default=None)
    description_hash: Optional[str] = Field(
        description="Description hash", default=None
    )
    expiry: Optional[int] = Field(description="Expiry in seconds", default=3600)

    class Config:
        extra = "forbid"


class PayInvoiceRequest(BaseModel):
    """Request model for paying invoices."""

    bolt11: str = Field(description="BOLT11 invoice string")
    amount: Optional[int] = Field(
        description="Amount override in millisatoshis", default=None
    )

    class Config:
        extra = "forbid"


class WalletAccount(BaseModel):
    """Watch-only wallet account model."""

    id: str = Field(description="Wallet account ID")
    title: str = Field(description="Wallet title")
    address: str = Field(description="Bitcoin address")
    balance: int = Field(description="Balance in satoshis")
    type: str = Field(description="Wallet type")

    class Config:
        extra = "allow"


class Address(BaseModel):
    """Bitcoin address model."""

    id: str = Field(description="Address ID")
    address: str = Field(description="Bitcoin address")
    wallet: str = Field(description="Wallet ID")
    amount: int = Field(description="Amount in satoshis")

    class Config:
        extra = "allow"


class Extension(BaseModel):
    """LNbits extension model."""

    id: str = Field(description="Extension ID")
    name: str = Field(description="Extension name")
    short_description: Optional[str] = Field(
        description="Short description", default=None
    )
    is_admin_only: bool = Field(description="Is admin only", default=False)
    is_installed: bool = Field(description="Is installed", default=False)

    class Config:
        extra = "allow"


class User(BaseModel):
    """User model."""

    id: str = Field(description="User ID")
    email: Optional[str] = Field(description="User email", default=None)
    extensions: List[str] = Field(
        description="Enabled extensions", default_factory=list
    )
    wallets: List[str] = Field(description="User wallets", default_factory=list)

    class Config:
        extra = "allow"


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(description="Error detail")
    type: Optional[str] = Field(description="Error type", default=None)

    class Config:
        extra = "allow"


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    data: Any = Field(description="Response data")
    success: bool = Field(description="Success status", default=True)
    message: Optional[str] = Field(description="Response message", default=None)

    class Config:
        extra = "allow"
