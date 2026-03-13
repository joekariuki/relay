"""Simulated DuniaWallet transaction data."""

from __future__ import annotations

from .models import Transaction, TransactionStatus, TransactionType


def _build_transactions() -> list[Transaction]:
    """Create ~80 demo transactions across all accounts."""
    return [
        # === Account acc_001 (Amadou Diallo, Senegal) ===
        Transaction(
            id="txn_001", account_id="acc_001", type=TransactionType.P2P,
            amount=25_000, fee=250, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Transfer to Moussa", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T14:30:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_002", account_id="acc_001", type=TransactionType.AIRTIME,
            amount=5_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+221 77 123 4567",
            description="Airtime purchase Orange", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T09:15:00Z", corridor=None,
        ),
        Transaction(
            id="txn_003", account_id="acc_001", type=TransactionType.CASH_IN,
            amount=100_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Cash deposit at agent Medina", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-18T11:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_004", account_id="acc_001", type=TransactionType.P2P,
            amount=50_000, fee=500, currency="XOF",
            recipient_name="Fatou Ndiaye", recipient_phone="+221 78 234 5678",
            description="Rent payment to Fatou", status=TransactionStatus.PENDING,
            timestamp="2026-02-21T16:45:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_005", account_id="acc_001", type=TransactionType.BILL_PAYMENT,
            amount=15_000, fee=100, currency="XOF",
            recipient_name="Senelec", recipient_phone=None,
            description="Electricity bill payment", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-15T08:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_006", account_id="acc_001", type=TransactionType.P2P,
            amount=10_000, fee=100, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Gift to Ibrahim", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-14T12:00:00Z", corridor="SN-BF",
        ),
        Transaction(
            id="txn_007", account_id="acc_001", type=TransactionType.CASH_OUT,
            amount=30_000, fee=300, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Cash withdrawal at agent Plateau", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-12T15:20:00Z", corridor=None,
        ),
        Transaction(
            id="txn_008", account_id="acc_001", type=TransactionType.P2P,
            amount=75_000, fee=750, currency="XOF",
            recipient_name="Aissatou Bah", recipient_phone="+225 07 456 7890",
            description="Business payment to Aissatou", status=TransactionStatus.FAILED,
            timestamp="2026-02-10T10:00:00Z", corridor="SN-CI",
        ),
        Transaction(
            id="txn_009", account_id="acc_001", type=TransactionType.AIRTIME,
            amount=2_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+221 77 123 4567",
            description="Airtime top-up", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-08T17:45:00Z", corridor=None,
        ),
        Transaction(
            id="txn_010", account_id="acc_001", type=TransactionType.P2P,
            amount=20_000, fee=200, currency="XOF",
            recipient_name="Kadiatou Diarra", recipient_phone="+225 05 890 1234",
            description="Transfer to Kadiatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-05T13:30:00Z", corridor="SN-CI",
        ),

        # === Account acc_002 (Fatou Ndiaye, Senegal, Business) ===
        Transaction(
            id="txn_011", account_id="acc_002", type=TransactionType.P2P,
            amount=500_000, fee=5_000, currency="XOF",
            recipient_name="Supplier Dakar Textiles", recipient_phone="+221 77 999 0000",
            description="Supplier payment - textiles", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T09:00:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_012", account_id="acc_002", type=TransactionType.CASH_IN,
            amount=750_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Business cash deposit", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T10:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_013", account_id="acc_002", type=TransactionType.P2P,
            amount=200_000, fee=2_000, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Payment for goods", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T14:15:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_014", account_id="acc_002", type=TransactionType.BILL_PAYMENT,
            amount=45_000, fee=200, currency="XOF",
            recipient_name="SDE Water", recipient_phone=None,
            description="Water bill business premises", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-17T08:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_015", account_id="acc_002", type=TransactionType.P2P,
            amount=150_000, fee=1_500, currency="XOF",
            recipient_name="Ousmane Coulibaly", recipient_phone="+223 79 789 0123",
            description="Contract payment", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-16T11:45:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_016", account_id="acc_002", type=TransactionType.CASH_OUT,
            amount=200_000, fee=2_000, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Business cash withdrawal", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-14T16:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_017", account_id="acc_002", type=TransactionType.P2P,
            amount=100_000, fee=1_000, currency="XOF",
            recipient_name="Amadou Diallo", recipient_phone="+221 77 123 4567",
            description="Refund to Amadou", status=TransactionStatus.FAILED,
            timestamp="2026-02-13T09:30:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_018", account_id="acc_002", type=TransactionType.P2P,
            amount=350_000, fee=3_500, currency="XOF",
            recipient_name="Aissatou Bah", recipient_phone="+225 07 456 7890",
            description="Business transfer to CI", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-11T13:00:00Z", corridor="SN-CI",
        ),
        Transaction(
            id="txn_019", account_id="acc_002", type=TransactionType.AIRTIME,
            amount=10_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+221 78 234 5678",
            description="Airtime for business line", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-09T07:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_020", account_id="acc_002", type=TransactionType.CASH_IN,
            amount=1_000_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Weekly business deposit", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-07T10:00:00Z", corridor=None,
        ),

        # === Account acc_003 (Moussa Traore, Mali) ===
        Transaction(
            id="txn_021", account_id="acc_003", type=TransactionType.P2P,
            amount=15_000, fee=150, currency="XOF",
            recipient_name="Kadiatou Diarra", recipient_phone="+225 05 890 1234",
            description="Envoi a Kadiatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T08:00:00Z", corridor="ML-CI",
        ),
        Transaction(
            id="txn_022", account_id="acc_003", type=TransactionType.CASH_IN,
            amount=50_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Bamako", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T12:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_023", account_id="acc_003", type=TransactionType.AIRTIME,
            amount=1_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+223 66 345 6789",
            description="Recharge Orange Mali", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-18T06:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_024", account_id="acc_003", type=TransactionType.P2P,
            amount=8_000, fee=80, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Envoi a Ibrahim", status=TransactionStatus.PENDING,
            timestamp="2026-02-22T10:00:00Z", corridor="ML-BF",
        ),
        Transaction(
            id="txn_025", account_id="acc_003", type=TransactionType.BILL_PAYMENT,
            amount=7_500, fee=50, currency="XOF",
            recipient_name="EDM", recipient_phone=None,
            description="Facture electricite", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-16T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_026", account_id="acc_003", type=TransactionType.CASH_OUT,
            amount=20_000, fee=200, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait agent Bamako centre", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-13T14:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_027", account_id="acc_003", type=TransactionType.P2P,
            amount=30_000, fee=300, currency="XOF",
            recipient_name="Amadou Diallo", recipient_phone="+221 77 123 4567",
            description="Remboursement Amadou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-10T11:15:00Z", corridor="ML-SN",
        ),
        Transaction(
            id="txn_028", account_id="acc_003", type=TransactionType.P2P,
            amount=5_000, fee=50, currency="XOF",
            recipient_name="Mariama Sow", recipient_phone="+221 76 678 9012",
            description="Paiement Mariama", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-06T16:00:00Z", corridor="ML-SN",
        ),

        # === Account acc_004 (Aissatou Bah, Cote d'Ivoire) ===
        Transaction(
            id="txn_029", account_id="acc_004", type=TransactionType.P2P,
            amount=100_000, fee=1_000, currency="XOF",
            recipient_name="Fatou Ndiaye", recipient_phone="+221 78 234 5678",
            description="Paiement marchandise", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T10:00:00Z", corridor="CI-SN",
        ),
        Transaction(
            id="txn_030", account_id="acc_004", type=TransactionType.CASH_IN,
            amount=200_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Abidjan Plateau", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T08:45:00Z", corridor=None,
        ),
        Transaction(
            id="txn_031", account_id="acc_004", type=TransactionType.BILL_PAYMENT,
            amount=25_000, fee=150, currency="XOF",
            recipient_name="CIE Electricite", recipient_phone=None,
            description="Facture electricite Abidjan", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-18T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_032", account_id="acc_004", type=TransactionType.P2P,
            amount=75_000, fee=750, currency="XOF",
            recipient_name="Ousmane Coulibaly", recipient_phone="+223 79 789 0123",
            description="Envoi a Ousmane", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-17T14:30:00Z", corridor="CI-ML",
        ),
        Transaction(
            id="txn_033", account_id="acc_004", type=TransactionType.CASH_OUT,
            amount=50_000, fee=500, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait Cocody", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-15T16:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_034", account_id="acc_004", type=TransactionType.AIRTIME,
            amount=3_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+225 07 456 7890",
            description="Recharge MTN CI", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-14T07:15:00Z", corridor=None,
        ),
        Transaction(
            id="txn_035", account_id="acc_004", type=TransactionType.P2P,
            amount=40_000, fee=400, currency="XOF",
            recipient_name="Amadou Diallo", recipient_phone="+221 77 123 4567",
            description="Remboursement Amadou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-12T11:00:00Z", corridor="CI-SN",
        ),
        Transaction(
            id="txn_036", account_id="acc_004", type=TransactionType.P2P,
            amount=60_000, fee=600, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Paiement Moussa", status=TransactionStatus.PENDING,
            timestamp="2026-02-22T08:30:00Z", corridor="CI-ML",
        ),

        # === Account acc_005 (Ibrahim Keita, Burkina Faso) ===
        Transaction(
            id="txn_037", account_id="acc_005", type=TransactionType.CASH_IN,
            amount=20_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Ouagadougou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T10:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_038", account_id="acc_005", type=TransactionType.AIRTIME,
            amount=500, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+226 70 567 8901",
            description="Recharge Telmob", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T06:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_039", account_id="acc_005", type=TransactionType.P2P,
            amount=5_000, fee=50, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Envoi a Moussa", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-17T13:00:00Z", corridor="BF-ML",
        ),
        Transaction(
            id="txn_040", account_id="acc_005", type=TransactionType.CASH_OUT,
            amount=10_000, fee=100, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait agent centre-ville", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-15T11:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_041", account_id="acc_005", type=TransactionType.P2P,
            amount=3_000, fee=30, currency="XOF",
            recipient_name="Kadiatou Diarra", recipient_phone="+225 05 890 1234",
            description="Petit envoi Kadiatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-13T08:45:00Z", corridor="BF-CI",
        ),

        # === Account acc_006 (Mariama Sow, Senegal, Business) ===
        Transaction(
            id="txn_042", account_id="acc_006", type=TransactionType.P2P,
            amount=800_000, fee=8_000, currency="XOF",
            recipient_name="Grand Fournisseur SA", recipient_phone="+221 33 800 0000",
            description="Paiement fournisseur mensuel", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T08:00:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_043", account_id="acc_006", type=TransactionType.CASH_IN,
            amount=1_500_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot recettes hebdomadaire", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T17:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_044", account_id="acc_006", type=TransactionType.P2P,
            amount=250_000, fee=2_500, currency="XOF",
            recipient_name="Aissatou Bah", recipient_phone="+225 07 456 7890",
            description="Paiement commande CI", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T10:30:00Z", corridor="SN-CI",
        ),
        Transaction(
            id="txn_045", account_id="acc_006", type=TransactionType.BILL_PAYMENT,
            amount=85_000, fee=500, currency="XOF",
            recipient_name="Orange Business", recipient_phone=None,
            description="Facture telecom business", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-18T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_046", account_id="acc_006", type=TransactionType.P2P,
            amount=400_000, fee=4_000, currency="XOF",
            recipient_name="Ousmane Coulibaly", recipient_phone="+223 79 789 0123",
            description="Contrat maintenance", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-16T14:00:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_047", account_id="acc_006", type=TransactionType.CASH_OUT,
            amount=500_000, fee=5_000, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait pour salaires", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-14T08:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_048", account_id="acc_006", type=TransactionType.P2P,
            amount=1_200_000, fee=12_000, currency="XOF",
            recipient_name="Import Export Dakar", recipient_phone="+221 33 900 0000",
            description="Gros paiement fournisseur", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-11T11:00:00Z", corridor="domestic",
        ),

        # === Account acc_007 (Ousmane Coulibaly, Mali) ===
        Transaction(
            id="txn_049", account_id="acc_007", type=TransactionType.P2P,
            amount=35_000, fee=350, currency="XOF",
            recipient_name="Amadou Diallo", recipient_phone="+221 77 123 4567",
            description="Envoi Amadou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T12:00:00Z", corridor="ML-SN",
        ),
        Transaction(
            id="txn_050", account_id="acc_007", type=TransactionType.CASH_IN,
            amount=80_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Bamako Hamdallaye", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T10:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_051", account_id="acc_007", type=TransactionType.BILL_PAYMENT,
            amount=12_000, fee=100, currency="XOF",
            recipient_name="Somagep", recipient_phone=None,
            description="Facture eau", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-17T08:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_052", account_id="acc_007", type=TransactionType.P2P,
            amount=20_000, fee=200, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Aide Ibrahim", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-15T14:00:00Z", corridor="ML-BF",
        ),
        Transaction(
            id="txn_053", account_id="acc_007", type=TransactionType.AIRTIME,
            amount=2_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+223 79 789 0123",
            description="Recharge Malitel", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-14T06:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_054", account_id="acc_007", type=TransactionType.CASH_OUT,
            amount=40_000, fee=400, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait agent ACI 2000", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-12T15:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_055", account_id="acc_007", type=TransactionType.P2P,
            amount=15_000, fee=150, currency="XOF",
            recipient_name="Fatou Ndiaye", recipient_phone="+221 78 234 5678",
            description="Paiement Fatou", status=TransactionStatus.FAILED,
            timestamp="2026-02-10T09:00:00Z", corridor="ML-SN",
        ),

        # === Account acc_008 (Kadiatou Diarra, Cote d'Ivoire) ===
        Transaction(
            id="txn_056", account_id="acc_008", type=TransactionType.CASH_IN,
            amount=30_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Yopougon", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-21T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_057", account_id="acc_008", type=TransactionType.P2P,
            amount=10_000, fee=100, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Envoi a Moussa", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-20T14:00:00Z", corridor="CI-ML",
        ),
        Transaction(
            id="txn_058", account_id="acc_008", type=TransactionType.AIRTIME,
            amount=1_500, fee=0, currency="XOF",
            recipient_name=None, recipient_phone="+225 05 890 1234",
            description="Recharge Orange CI", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-19T07:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_059", account_id="acc_008", type=TransactionType.BILL_PAYMENT,
            amount=8_000, fee=50, currency="XOF",
            recipient_name="SODECI Eau", recipient_phone=None,
            description="Facture eau", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-17T10:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_060", account_id="acc_008", type=TransactionType.CASH_OUT,
            amount=15_000, fee=150, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Retrait agent Adjame", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-15T12:30:00Z", corridor=None,
        ),
        Transaction(
            id="txn_061", account_id="acc_008", type=TransactionType.P2P,
            amount=5_000, fee=50, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Cadeau Ibrahim", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-13T16:00:00Z", corridor="CI-BF",
        ),

        # === Additional cross-account transactions for variety ===
        Transaction(
            id="txn_062", account_id="acc_001", type=TransactionType.P2P,
            amount=45_000, fee=450, currency="XOF",
            recipient_name="Mariama Sow", recipient_phone="+221 76 678 9012",
            description="Payment to Mariama", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-03T10:00:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_063", account_id="acc_002", type=TransactionType.P2P,
            amount=175_000, fee=1_750, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Envoi urgent Ibrahim", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-05T08:00:00Z", corridor="SN-BF",
        ),
        Transaction(
            id="txn_064", account_id="acc_003", type=TransactionType.P2P,
            amount=12_000, fee=120, currency="XOF",
            recipient_name="Aissatou Bah", recipient_phone="+225 07 456 7890",
            description="Envoi Aissatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-04T15:00:00Z", corridor="ML-CI",
        ),
        Transaction(
            id="txn_065", account_id="acc_004", type=TransactionType.P2P,
            amount=90_000, fee=900, currency="XOF",
            recipient_name="Mariama Sow", recipient_phone="+221 76 678 9012",
            description="Gros envoi Mariama", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-02T09:00:00Z", corridor="CI-SN",
        ),
        Transaction(
            id="txn_066", account_id="acc_006", type=TransactionType.P2P,
            amount=300_000, fee=3_000, currency="XOF",
            recipient_name="Moussa Traore", recipient_phone="+223 66 345 6789",
            description="Paiement contrat Moussa", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-08T11:00:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_067", account_id="acc_007", type=TransactionType.P2P,
            amount=25_000, fee=250, currency="XOF",
            recipient_name="Kadiatou Diarra", recipient_phone="+225 05 890 1234",
            description="Envoi Kadiatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-07T14:00:00Z", corridor="ML-CI",
        ),
        Transaction(
            id="txn_068", account_id="acc_001", type=TransactionType.CASH_IN,
            amount=150_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Salary deposit", status=TransactionStatus.COMPLETED,
            timestamp="2026-01-31T08:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_069", account_id="acc_002", type=TransactionType.BILL_PAYMENT,
            amount=120_000, fee=600, currency="XOF",
            recipient_name="Expresso Telecom", recipient_phone=None,
            description="Facture internet bureau", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-01T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_070", account_id="acc_005", type=TransactionType.P2P,
            amount=7_000, fee=70, currency="XOF",
            recipient_name="Amadou Diallo", recipient_phone="+221 77 123 4567",
            description="Envoi Amadou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-11T10:00:00Z", corridor="BF-SN",
        ),
        Transaction(
            id="txn_071", account_id="acc_008", type=TransactionType.P2P,
            amount=20_000, fee=200, currency="XOF",
            recipient_name="Fatou Ndiaye", recipient_phone="+221 78 234 5678",
            description="Paiement Fatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-09T13:00:00Z", corridor="CI-SN",
        ),
        Transaction(
            id="txn_072", account_id="acc_003", type=TransactionType.CASH_IN,
            amount=35_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot marche", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-02T07:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_073", account_id="acc_004", type=TransactionType.CASH_IN,
            amount=150_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot salaire", status=TransactionStatus.COMPLETED,
            timestamp="2026-01-31T10:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_074", account_id="acc_006", type=TransactionType.P2P,
            amount=600_000, fee=6_000, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Investissement BF", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-04T08:00:00Z", corridor="SN-BF",
        ),
        Transaction(
            id="txn_075", account_id="acc_001", type=TransactionType.P2P,
            amount=35_000, fee=350, currency="XOF",
            recipient_name="Ousmane Coulibaly", recipient_phone="+223 79 789 0123",
            description="Birthday gift Ousmane", status=TransactionStatus.COMPLETED,
            timestamp="2026-01-28T15:00:00Z", corridor="SN-ML",
        ),
        Transaction(
            id="txn_076", account_id="acc_002", type=TransactionType.P2P,
            amount=450_000, fee=4_500, currency="XOF",
            recipient_name="Kadiatou Diarra", recipient_phone="+225 05 890 1234",
            description="Paiement stock CI", status=TransactionStatus.COMPLETED,
            timestamp="2026-01-30T11:00:00Z", corridor="SN-CI",
        ),
        Transaction(
            id="txn_077", account_id="acc_007", type=TransactionType.CASH_IN,
            amount=60_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot hebdomadaire", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-03T09:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_078", account_id="acc_005", type=TransactionType.CASH_IN,
            amount=25_000, fee=0, currency="XOF",
            recipient_name=None, recipient_phone=None,
            description="Depot agent Ouaga 2000", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-08T08:00:00Z", corridor=None,
        ),
        Transaction(
            id="txn_079", account_id="acc_008", type=TransactionType.P2P,
            amount=12_000, fee=120, currency="XOF",
            recipient_name="Aissatou Bah", recipient_phone="+225 07 456 7890",
            description="Remboursement Aissatou", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-06T14:00:00Z", corridor="domestic",
        ),
        Transaction(
            id="txn_080", account_id="acc_004", type=TransactionType.P2P,
            amount=30_000, fee=300, currency="XOF",
            recipient_name="Ibrahim Keita", recipient_phone="+226 70 567 8901",
            description="Aide Ibrahim", status=TransactionStatus.COMPLETED,
            timestamp="2026-02-08T10:00:00Z", corridor="CI-BF",
        ),
    ]


TRANSACTIONS: list[Transaction] = _build_transactions()

# Index by account_id for fast lookup
_BY_ACCOUNT: dict[str, list[Transaction]] = {}
for _txn in TRANSACTIONS:
    _BY_ACCOUNT.setdefault(_txn.account_id, []).append(_txn)

# Sort each account's transactions by timestamp descending (most recent first)
for _account_txns in _BY_ACCOUNT.values():
    _account_txns.sort(key=lambda t: t.timestamp, reverse=True)


def get_transactions_for_account(
    account_id: str,
    limit: int = 10,
) -> list[Transaction]:
    """Return most recent transactions for an account, sorted by timestamp desc."""
    txns = _BY_ACCOUNT.get(account_id, [])
    return txns[:limit]


def lookup_transaction(
    account_id: str,
    query: str,
) -> list[Transaction]:
    """Search transactions by ID, recipient name, or description. Case-insensitive."""
    query_lower = query.lower()
    results: list[Transaction] = []
    txns = _BY_ACCOUNT.get(account_id, [])
    for txn in txns:
        if (
            query_lower in txn.id.lower()
            or (txn.recipient_name and query_lower in txn.recipient_name.lower())
            or query_lower in txn.description.lower()
        ):
            results.append(txn)
    return results
