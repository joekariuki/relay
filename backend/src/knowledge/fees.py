"""DuniaWallet fee calculation rules.

Architecture:
    CORRIDOR_RATES: maps corridor type → base fee percentage
    AMOUNT_TIERS:   shared USD-normalized tiers → (min_usd, max_usd, rate_multiplier, min_fee_usd)
    _resolve_corridor(): country pair → corridor type + corridor code
    calculate_fee(): amount + currency + corridor → FeeResult

Fee calculation flow:
    amount (local currency) → normalize_to_usd → match tier → apply rate × multiplier
    → max(calculated_fee, min_fee) → express in source currency
"""

from __future__ import annotations

from .models import DEMO_EXCHANGE_RATES, FeeResult, normalize_to_usd

# === Corridor Types and Fee Rates ===

# Base fee percentage by corridor type
CORRIDOR_RATES: dict[str, float] = {
    "domestic": 1.0,             # Within country
    "intra_waemu": 1.5,          # WAEMU zone (SN, ML, CI, BF) — same currency
    "west_africa_cross": 2.0,    # West Africa cross-zone (NG↔GH, NG↔SN, etc.)
    "east_africa": 1.5,          # KE↔TZ
    "cross_region": 2.5,         # Cross-region Africa (NG↔KE, ZA↔NG, etc.)
    "international_high": 2.5,   # High-volume diaspora corridors (UK→NG, US→KE)
    "international_low": 3.0,    # Lower-volume international corridors
    "cash_out": 1.0,             # Cash withdrawal
}

# Amount tiers in USD equivalent — shared across all corridors.
# (min_usd, max_usd, rate_multiplier, min_fee_usd)
# rate_multiplier scales the base CORRIDOR_RATE for this tier.
AMOUNT_TIERS: list[tuple[float, float, float, float]] = [
    (0.0, 80.0, 1.0, 0.15),        # Small: up to ~$80
    (80.0, 800.0, 1.0, 0.80),      # Medium: $80–$800
    (800.0, 3_300.0, 0.8, 3.30),   # Large: $800–$3,300
    (3_300.0, 10_000.0, 0.6, 8.00), # Very large: $3,300–$10,000
]

# === Country Code Mapping ===

# Maps country names (lowercase) → 2-letter ISO codes
_COUNTRY_CODES: dict[str, str] = {
    # WAEMU
    "senegal": "SN",
    "mali": "ML",
    "cote d'ivoire": "CI",
    "cote divoire": "CI",
    "ivory coast": "CI",
    "burkina faso": "BF",
    "burkina": "BF",
    # West Africa (Anglophone)
    "nigeria": "NG",
    "ghana": "GH",
    # East Africa
    "kenya": "KE",
    "tanzania": "TZ",
    # Southern Africa
    "south africa": "ZA",
    # North Africa
    "morocco": "MA",
    "egypt": "EG",
    # Diaspora
    "united kingdom": "GB",
    "uk": "GB",
    "united states": "US",
    "usa": "US",
}


def resolve_country_code(name: str) -> str | None:
    """Resolve a country name to its 2-letter ISO code, or None if unknown."""
    return _COUNTRY_CODES.get(name.lower().strip())


# Reverse lookup: country code → default currency
_COUNTRY_CURRENCY: dict[str, str] = {
    "SN": "XOF", "ML": "XOF", "CI": "XOF", "BF": "XOF",
    "NG": "NGN", "GH": "GHS",
    "KE": "KES", "TZ": "TZS",
    "ZA": "ZAR",
    "MA": "MAD", "EG": "EGP",
    "GB": "GBP", "US": "USD",
}

# WAEMU zone countries (share XOF, lower cross-border fees)
_WAEMU = {"SN", "ML", "CI", "BF"}

# East Africa community countries
_EAC = {"KE", "TZ"}

# High-volume international corridors (diaspora → Africa)
_HIGH_VOLUME_INTL: set[tuple[str, str]] = {
    ("GB", "NG"), ("GB", "GH"), ("GB", "ZA"),
    ("US", "KE"), ("US", "NG"), ("US", "ZA"),
}


def _classify_corridor(source_code: str, dest_code: str) -> str:
    """Classify a country pair into a corridor type.

    Returns one of the CORRIDOR_RATES keys.
    """
    if source_code == dest_code:
        return "domestic"

    # WAEMU intra-zone (same currency, low fees)
    if source_code in _WAEMU and dest_code in _WAEMU:
        return "intra_waemu"

    # East Africa community
    if source_code in _EAC and dest_code in _EAC:
        return "east_africa"

    # West Africa cross-zone (WAEMU ↔ Anglophone)
    west_africa = _WAEMU | {"NG", "GH"}
    if source_code in west_africa and dest_code in west_africa:
        return "west_africa_cross"

    # High-volume international
    if (source_code, dest_code) in _HIGH_VOLUME_INTL:
        return "international_high"

    # Any other international corridor involving GB/US
    if source_code in ("GB", "US") or dest_code in ("GB", "US"):
        return "international_low"

    # Cross-region Africa
    return "cross_region"


def _resolve_corridor(
    destination_country: str, source_country: str
) -> tuple[str, str]:
    """Resolve destination and source to (corridor_code, corridor_type).

    Args:
        destination_country: Destination country name or code.
        source_country: Source country 2-letter code (required).

    Returns:
        Tuple of (corridor_code like "SN-ML", corridor_type like "intra_waemu").
    """
    dest = destination_country.lower().strip()

    # Already a corridor code like "SN-ML"
    if "-" in dest and len(dest) <= 6:
        parts = dest.upper().split("-")
        if len(parts) == 2:
            ctype = _classify_corridor(parts[0], parts[1])
            return (dest.upper(), ctype)

    # Domestic / local
    if dest in ("domestic", "local"):
        return ("domestic", "domestic")

    # Cash-out
    if dest in ("cash_out", "cashout", "cash out", "withdrawal"):
        return ("cash_out", "cash_out")

    # Resolve country name to code
    dest_code = _COUNTRY_CODES.get(dest)
    if dest_code is None:
        # Try matching source country name
        src_name_match = [k for k, v in _COUNTRY_CODES.items() if v == source_country]
        if dest in [n.lower() for n in src_name_match]:
            return ("domestic", "domestic")
        return ("domestic", "domestic")  # Unknown destination defaults to domestic

    if dest_code == source_country:
        return ("domestic", "domestic")

    corridor_code = f"{source_country}-{dest_code}"
    corridor_type = _classify_corridor(source_country, dest_code)
    return (corridor_code, corridor_type)


def calculate_fee(
    amount: int,
    currency: str = "XOF",
    destination_country: str = "domestic",
    source_country: str = "SN",
) -> FeeResult | None:
    """Calculate the fee for a transfer amount and destination.

    Uses USD normalization for tier matching so that equivalent amounts in
    different currencies hit the same fee tier.

    Args:
        amount: Transfer amount in source currency.
        currency: Source currency code.
        destination_country: Destination country name, code, or 'domestic'.
        source_country: Source country 2-letter code.

    Returns:
        FeeResult with fee details, or None if amount exceeds all tiers.
    """
    if amount <= 0:
        return None

    corridor_code, corridor_type = _resolve_corridor(destination_country, source_country)
    base_rate = CORRIDOR_RATES.get(corridor_type)
    if base_rate is None:
        return None

    # Normalize amount to USD for tier matching
    try:
        amount_usd = normalize_to_usd(amount, currency)
    except ValueError:
        return None

    # Find matching tier
    for min_usd, max_usd, multiplier, min_fee_usd in AMOUNT_TIERS:
        if min_usd <= amount_usd <= max_usd:
            effective_rate = base_rate * multiplier
            calculated_fee = int(amount * effective_rate / 100)

            # Convert min fee from USD to source currency
            source_rate = DEMO_EXCHANGE_RATES.get(currency, 1.0)
            min_fee_local = int(min_fee_usd * source_rate)

            fee = max(calculated_fee, min_fee_local)
            return FeeResult(
                amount=amount,
                fee=fee,
                total=amount + fee,
                currency=currency,
                corridor=corridor_code,
                fee_percent=effective_rate,
                fee_fixed=min_fee_local,
            )

    return None


# List of corridor type names (e.g. "domestic", "intra_waemu", etc.)
CORRIDOR_NAMES = list(CORRIDOR_RATES.keys())
