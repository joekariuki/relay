"""Simulated DuniaWallet user accounts."""

from __future__ import annotations

from .models import Account, KYCTier


def _build_accounts() -> dict[str, Account]:
    """Create demo accounts across pan-African and international regions."""
    accounts = [
        # === West Africa (WAEMU) — XOF ===
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
        # === West Africa (Anglophone) ===
        Account(
            id="acc_009",
            name="Chinedu Okafor",
            phone="+234 803 123 4567",
            balance=150_000,
            currency="NGN",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Nigeria",
            created_at="2024-06-10",
        ),
        Account(
            id="acc_010",
            name="Akua Mensah",
            phone="+233 24 234 5678",
            balance=2_500,
            currency="GHS",
            account_type="business",
            kyc_tier=KYCTier.PREMIUM,
            country="Ghana",
            created_at="2024-02-15",
        ),
        # === East Africa ===
        Account(
            id="acc_011",
            name="Wanjiku Muthoni",
            phone="+254 712 345 678",
            balance=45_000,
            currency="KES",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Kenya",
            created_at="2024-04-01",
        ),
        Account(
            id="acc_012",
            name="Juma Hassan",
            phone="+255 754 456 789",
            balance=850_000,
            currency="TZS",
            account_type="personal",
            kyc_tier=KYCTier.BASIC,
            country="Tanzania",
            created_at="2024-09-20",
        ),
        # === Southern Africa ===
        Account(
            id="acc_013",
            name="Thabo Molefe",
            phone="+27 82 567 8901",
            balance=8_500,
            currency="ZAR",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="South Africa",
            created_at="2024-07-12",
        ),
        # === North Africa ===
        Account(
            id="acc_014",
            name="Youssef El Amrani",
            phone="+212 661 678 901",
            balance=12_000,
            currency="MAD",
            account_type="business",
            kyc_tier=KYCTier.PREMIUM,
            country="Morocco",
            created_at="2024-01-25",
        ),
        Account(
            id="acc_015",
            name="Nour Ibrahim",
            phone="+20 100 789 0123",
            balance=35_000,
            currency="EGP",
            account_type="personal",
            kyc_tier=KYCTier.STANDARD,
            country="Egypt",
            created_at="2024-05-18",
        ),
        # === Diaspora (International) ===
        Account(
            id="acc_016",
            name="Oluwaseun Adeyemi",
            phone="+44 7911 123 456",
            balance=1_200,
            currency="GBP",
            account_type="personal",
            kyc_tier=KYCTier.PREMIUM,
            country="United Kingdom",
            created_at="2024-03-01",
        ),
        Account(
            id="acc_017",
            name="Amina Odhiambo",
            phone="+1 202 555 0198",
            balance=2_800,
            currency="USD",
            account_type="personal",
            kyc_tier=KYCTier.PREMIUM,
            country="United States",
            created_at="2024-06-22",
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
