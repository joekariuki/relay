"""DuniaWallet fee calculation rules."""

from __future__ import annotations

from .models import FeeResult, FeeRule

# Fee rules: corridor, min_amount, max_amount, fee_percent, fee_fixed (minimum fee)
FEE_RULES: list[FeeRule] = [
    # Domestic transfers
    FeeRule(corridor="domestic", min_amount=0, max_amount=10_000, fee_percent=1.0, fee_fixed=100),
    FeeRule(corridor="domestic", min_amount=10_001, max_amount=100_000, fee_percent=1.0, fee_fixed=100),
    FeeRule(corridor="domestic", min_amount=100_001, max_amount=500_000, fee_percent=1.0, fee_fixed=500),
    FeeRule(corridor="domestic", min_amount=500_001, max_amount=2_000_000, fee_percent=0.8, fee_fixed=2_000),
    # Senegal to Mali
    FeeRule(corridor="SN-ML", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="SN-ML", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    FeeRule(corridor="SN-ML", min_amount=500_001, max_amount=2_000_000, fee_percent=1.2, fee_fixed=3_000),
    # Senegal to Cote d'Ivoire
    FeeRule(corridor="SN-CI", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="SN-CI", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    FeeRule(corridor="SN-CI", min_amount=500_001, max_amount=2_000_000, fee_percent=1.2, fee_fixed=3_000),
    # Senegal to Burkina Faso
    FeeRule(corridor="SN-BF", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="SN-BF", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    FeeRule(corridor="SN-BF", min_amount=500_001, max_amount=2_000_000, fee_percent=1.2, fee_fixed=3_000),
    # Mali to Senegal
    FeeRule(corridor="ML-SN", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="ML-SN", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Mali to Cote d'Ivoire
    FeeRule(corridor="ML-CI", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="ML-CI", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Mali to Burkina Faso
    FeeRule(corridor="ML-BF", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="ML-BF", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Cote d'Ivoire to Senegal
    FeeRule(corridor="CI-SN", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="CI-SN", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Cote d'Ivoire to Mali
    FeeRule(corridor="CI-ML", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="CI-ML", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Cote d'Ivoire to Burkina Faso
    FeeRule(corridor="CI-BF", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="CI-BF", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Burkina Faso to Senegal
    FeeRule(corridor="BF-SN", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="BF-SN", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Burkina Faso to Mali
    FeeRule(corridor="BF-ML", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="BF-ML", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Burkina Faso to Cote d'Ivoire
    FeeRule(corridor="BF-CI", min_amount=0, max_amount=50_000, fee_percent=1.5, fee_fixed=150),
    FeeRule(corridor="BF-CI", min_amount=50_001, max_amount=500_000, fee_percent=1.5, fee_fixed=500),
    # Cash-out fees
    FeeRule(corridor="cash_out", min_amount=0, max_amount=50_000, fee_percent=1.0, fee_fixed=100),
    FeeRule(corridor="cash_out", min_amount=50_001, max_amount=500_000, fee_percent=1.0, fee_fixed=300),
    FeeRule(corridor="cash_out", min_amount=500_001, max_amount=2_000_000, fee_percent=0.8, fee_fixed=2_000),
]

# Country code mapping for destination_country -> corridor prefix
_COUNTRY_CODES: dict[str, str] = {
    "senegal": "SN",
    "mali": "ML",
    "cote d'ivoire": "CI",
    "cote divoire": "CI",
    "ivory coast": "CI",
    "burkina faso": "BF",
    "burkina": "BF",
}


def _resolve_corridor(destination_country: str, source_country: str = "SN") -> str:
    """Resolve a destination country name to a corridor code."""
    dest = destination_country.lower().strip()

    # Check if it's already a corridor code
    if "-" in dest and len(dest) <= 6:
        return dest.upper()

    # Check for domestic
    if dest in ("domestic", "local", source_country.lower()):
        return "domestic"

    dest_code = _COUNTRY_CODES.get(dest)
    if dest_code is None:
        return "domestic"  # Default to domestic if unknown

    if dest_code == source_country:
        return "domestic"

    return f"{source_country}-{dest_code}"


def calculate_fee(
    amount: int,
    currency: str = "XOF",
    destination_country: str = "domestic",
) -> FeeResult | None:
    """Calculate the fee for a transfer amount and destination.

    Returns None if no matching fee rule is found.
    """
    corridor = _resolve_corridor(destination_country)

    # Find matching fee rule
    for rule in FEE_RULES:
        if rule.corridor == corridor and rule.min_amount <= amount <= rule.max_amount:
            calculated_fee = int(amount * rule.fee_percent / 100)
            fee = max(calculated_fee, rule.fee_fixed)
            return FeeResult(
                amount=amount,
                fee=fee,
                total=amount + fee,
                currency=currency,
                corridor=corridor,
                fee_percent=rule.fee_percent,
                fee_fixed=rule.fee_fixed,
            )

    return None
