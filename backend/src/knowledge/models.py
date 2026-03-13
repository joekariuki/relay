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


# === Multi-Currency Support ===

# Static demo exchange rates — all expressed as units per 1 USD.
DEMO_EXCHANGE_RATES: dict[str, float] = {
    "XOF": 605.0,    # CFA Franc (WAEMU)
    "NGN": 1550.0,   # Nigerian Naira
    "GHS": 15.5,     # Ghanaian Cedi
    "KES": 153.0,    # Kenyan Shilling
    "TZS": 2650.0,   # Tanzanian Shilling
    "ZAR": 18.5,     # South African Rand
    "MAD": 10.0,     # Moroccan Dirham
    "EGP": 50.0,     # Egyptian Pound
    "GBP": 0.79,     # British Pound
    "USD": 1.0,      # US Dollar
}

# Currency formatting rules: (symbol, position, decimal_places)
# position: "prefix" means $100, "suffix" means 100 FCFA
CURRENCY_FORMAT: dict[str, tuple[str, str, int]] = {
    "XOF": ("FCFA", "suffix", 0),
    "NGN": ("₦", "prefix", 0),
    "GHS": ("GH₵", "prefix", 2),
    "KES": ("KSh", "prefix", 0),
    "TZS": ("TSh", "prefix", 0),
    "ZAR": ("R", "prefix", 2),
    "MAD": ("MAD", "suffix", 2),
    "EGP": ("E£", "prefix", 2),
    "GBP": ("£", "prefix", 2),
    "USD": ("$", "prefix", 2),
}


def format_currency(amount: int | float, currency: str) -> str:
    """Format an amount with the appropriate currency symbol and separators.

    >>> format_currency(245000, "XOF")
    '245,000 FCFA'
    >>> format_currency(1200, "GBP")
    '£1,200.00'
    >>> format_currency(150000, "NGN")
    '₦150,000'
    """
    symbol, position, decimals = CURRENCY_FORMAT.get(
        currency, (currency, "suffix", 0)
    )
    if decimals > 0:
        formatted = f"{amount:,.{decimals}f}"
    else:
        formatted = f"{int(amount):,}"
    if position == "prefix":
        return f"{symbol}{formatted}"
    return f"{formatted} {symbol}"


def convert_currency(
    amount: float, from_currency: str, to_currency: str, spread: float = 0.01
) -> tuple[float, float]:
    """Convert an amount between currencies using demo exchange rates.

    Args:
        amount: Amount in the source currency.
        from_currency: Source currency code.
        to_currency: Target currency code.
        spread: FX spread applied on top of the reference rate (default 1%).

    Returns:
        Tuple of (converted_amount, applied_rate) where applied_rate is the
        effective rate from source to target currency (including spread).

    Raises:
        ValueError: If either currency code is unknown.
    """
    if from_currency == to_currency:
        return (amount, 1.0)

    from_rate = DEMO_EXCHANGE_RATES.get(from_currency)
    to_rate = DEMO_EXCHANGE_RATES.get(to_currency)

    if from_rate is None:
        raise ValueError(f"Unknown currency: {from_currency}")
    if to_rate is None:
        raise ValueError(f"Unknown currency: {to_currency}")
    if from_rate == 0:
        raise ValueError(f"Exchange rate for {from_currency} is zero")

    # Convert: source → USD → target, applying spread
    mid_rate = to_rate / from_rate
    applied_rate = mid_rate * (1 + spread)
    converted = amount * applied_rate

    return (round(converted, 2), round(applied_rate, 6))


def normalize_to_usd(amount: float, currency: str) -> float:
    """Convert an amount to USD equivalent for fee tier matching.

    Raises:
        ValueError: If the currency code is unknown.
    """
    rate = DEMO_EXCHANGE_RATES.get(currency)
    if rate is None:
        raise ValueError(f"Unknown currency: {currency}")
    if rate == 0:
        raise ValueError(f"Exchange rate for {currency} is zero")
    return round(amount / rate, 2)


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
