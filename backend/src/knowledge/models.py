"""Central data models used across the entire Relay application."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    FR = "fr"
    SW = "sw"


class TransactionType(str, Enum):
    """Types of mobile money transactions."""

    P2P = "p2p_transfer"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    BILL_PAYMENT = "bill_payment"
    AIRTIME = "airtime_purchase"


class TransactionStatus(str, Enum):
    """Transaction processing status."""

    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"


class KYCTier(str, Enum):
    """Know Your Customer verification tiers with associated limits."""

    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class TicketPriority(str, Enum):
    """Support ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True)
class Account:
    """A DuniaWallet user account."""

    id: str
    name: str
    phone: str
    balance: int
    currency: str
    account_type: str
    kyc_tier: KYCTier
    country: str
    created_at: str


@dataclass(frozen=True)
class Transaction:
    """A mobile money transaction record."""

    id: str
    account_id: str
    type: TransactionType
    amount: int
    fee: int
    currency: str
    recipient_name: str | None
    recipient_phone: str | None
    description: str
    status: TransactionStatus
    timestamp: str
    corridor: str | None


@dataclass(frozen=True)
class FeeRule:
    """Fee calculation rule for a transfer corridor and amount range."""

    corridor: str
    min_amount: int
    max_amount: int
    fee_percent: float
    fee_fixed: int


@dataclass(frozen=True)
class FeeResult:
    """Result of a fee calculation."""

    amount: int
    fee: int
    total: int
    currency: str
    corridor: str
    fee_percent: float
    fee_fixed: int


@dataclass(frozen=True)
class AgentLocation:
    """A DuniaWallet cash-in/cash-out agent location."""

    id: str
    name: str
    city: str
    neighborhood: str
    country: str
    phone: str
    hours: str
    services: tuple[str, ...]


@dataclass
class SupportTicket:
    """A customer support ticket."""

    id: str
    account_id: str
    category: str
    summary: str
    priority: TicketPriority
    status: str
    created_at: str


@dataclass(frozen=True)
class Policy:
    """A service policy document available in EN and FR."""

    topic: str
    title_en: str
    content_en: str
    title_fr: str
    content_fr: str


@dataclass(frozen=True)
class ToolCallRecord:
    """Record of a tool call made during agent processing."""

    tool_name: str
    arguments: dict[str, object]
    result: dict[str, object]
    duration_ms: float


@dataclass
class AgentResponse:
    """Structured response from the agent pipeline."""

    response_text: str
    language_detected: Language
    tools_used: list[ToolCallRecord]
    groundedness_score: float | None
    latency_ms: dict[str, float]
    metadata: dict[str, object] = field(default_factory=dict)
