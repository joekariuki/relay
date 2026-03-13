"""Simulated DuniaWallet user accounts."""

from __future__ import annotations

from .models import Account, KYCTier


def _build_accounts() -> dict[str, Account]:
    """Create demo accounts with realistic West African data."""
    accounts = [
        Account(
            id="acc_001",
            name="Amadou Diallo",
            phone="+221 77 123 4567",
            balance=245_000,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Senegal",
            created_at="2024-03-15",
        ),
        Account(
            id="acc_002",
            name="Fatou Ndiaye",
            phone="+221 78 234 5678",
            balance=1_850_000,
            currency="XOF",
            account_type="business",
            kyc_tier=KYCTier.PREMIUM,
            country="Senegal",
            created_at="2023-11-01",
        ),
        Account(
            id="acc_003",
            name="Moussa Traore",
            phone="+223 66 345 6789",
            balance=72_500,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.BASIC,
            country="Mali",
            created_at="2024-08-20",
        ),
        Account(
            id="acc_004",
            name="Aissatou Bah",
            phone="+225 07 456 7890",
            balance=520_000,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Cote d'Ivoire",
            created_at="2024-01-10",
        ),
        Account(
            id="acc_005",
            name="Ibrahim Keita",
            phone="+226 70 567 8901",
            balance=15_000,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.BASIC,
            country="Burkina Faso",
            created_at="2025-02-01",
        ),
        Account(
            id="acc_006",
            name="Mariama Sow",
            phone="+221 76 678 9012",
            balance=3_200_000,
            currency="XOF",
            account_type="business",
            kyc_tier=KYCTier.PREMIUM,
            country="Senegal",
            created_at="2023-06-15",
        ),
        Account(
            id="acc_007",
            name="Ousmane Coulibaly",
            phone="+223 79 789 0123",
            balance=180_000,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Mali",
            created_at="2024-05-22",
        ),
        Account(
            id="acc_008",
            name="Kadiatou Diarra",
            phone="+225 05 890 1234",
            balance=45_000,
            currency="XOF",
            account_type="personal",
            kyc_tier=KYCTier.BASIC,
            country="Cote d'Ivoire",
            created_at="2025-01-03",
        ),
    ]
    return {a.id: a for a in accounts}


ACCOUNTS: dict[str, Account] = _build_accounts()


def get_account(account_id: str) -> Account | None:
    """Retrieve an account by ID. Returns None if not found."""
    return ACCOUNTS.get(account_id)


def get_all_accounts() -> dict[str, Account]:
    """Return all demo accounts."""
    return ACCOUNTS


def get_default_account_id() -> str:
    """Return the default demo account ID."""
    return "acc_001"
