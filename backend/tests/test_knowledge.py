"""Tests for the knowledge/data layer."""

import pytest

from src.knowledge.accounts import ACCOUNTS, get_account, get_all_accounts, get_default_account_id
from src.knowledge.agents_data import AGENT_LOCATIONS, find_agents
from src.knowledge.fees import FEE_RULES, calculate_fee
from src.knowledge.models import (
    Account,
    CURRENCY_FORMAT,
    DEMO_EXCHANGE_RATES,
    KYCTier,
    TransactionStatus,
    TransactionType,
    convert_currency,
    format_currency,
    normalize_to_usd,
)
from src.knowledge.policies import POLICIES, get_policy, search_policies
from src.knowledge.transactions import (
    TRANSACTIONS,
    get_transactions_for_account,
    lookup_transaction,
)


# === Multi-Currency Tests ===


class TestExchangeRates:
    def test_all_rates_positive(self) -> None:
        for currency, rate in DEMO_EXCHANGE_RATES.items():
            assert rate > 0, f"{currency} has non-positive rate: {rate}"

    def test_usd_is_one(self) -> None:
        assert DEMO_EXCHANGE_RATES["USD"] == 1.0

    def test_known_currencies_exist(self) -> None:
        expected = {"XOF", "NGN", "GHS", "KES", "TZS", "ZAR", "MAD", "EGP", "GBP", "USD"}
        assert set(DEMO_EXCHANGE_RATES.keys()) == expected

    def test_format_rules_match_rates(self) -> None:
        assert set(CURRENCY_FORMAT.keys()) == set(DEMO_EXCHANGE_RATES.keys())


class TestFormatCurrency:
    def test_xof_suffix(self) -> None:
        assert format_currency(245_000, "XOF") == "245,000 FCFA"

    def test_gbp_prefix_decimals(self) -> None:
        assert format_currency(1200, "GBP") == "£1,200.00"

    def test_ngn_prefix_no_decimals(self) -> None:
        assert format_currency(150_000, "NGN") == "₦150,000"

    def test_usd_prefix_decimals(self) -> None:
        assert format_currency(2800, "USD") == "$2,800.00"

    def test_kes_prefix_no_decimals(self) -> None:
        assert format_currency(45_000, "KES") == "KSh45,000"

    def test_unknown_currency_fallback(self) -> None:
        result = format_currency(100, "ZZZ")
        assert "100" in result
        assert "ZZZ" in result

    def test_zero_amount(self) -> None:
        assert format_currency(0, "XOF") == "0 FCFA"


class TestConvertCurrency:
    def test_same_currency_no_conversion(self) -> None:
        amount, rate = convert_currency(1000, "XOF", "XOF")
        assert amount == 1000
        assert rate == 1.0

    def test_xof_to_ngn(self) -> None:
        amount, rate = convert_currency(605_000, "XOF", "NGN", spread=0.0)
        # 605,000 XOF = 1000 USD = 1,550,000 NGN (at zero spread)
        assert abs(amount - 1_550_000) < 1

    def test_gbp_to_kes(self) -> None:
        amount, rate = convert_currency(100, "GBP", "KES", spread=0.0)
        # 100 GBP = ~126.58 USD = ~19,367 KES
        assert amount > 19_000

    def test_spread_increases_cost(self) -> None:
        no_spread, _ = convert_currency(1000, "USD", "NGN", spread=0.0)
        with_spread, _ = convert_currency(1000, "USD", "NGN", spread=0.01)
        assert with_spread > no_spread

    def test_unknown_from_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown currency: ZZZ"):
            convert_currency(100, "ZZZ", "USD")

    def test_unknown_to_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown currency: ZZZ"):
            convert_currency(100, "USD", "ZZZ")


class TestNormalizeToUsd:
    def test_usd_unchanged(self) -> None:
        assert normalize_to_usd(1000, "USD") == 1000.0

    def test_xof_normalization(self) -> None:
        # 605 XOF = 1 USD
        result = normalize_to_usd(605, "XOF")
        assert abs(result - 1.0) < 0.01

    def test_gbp_normalization(self) -> None:
        # 0.79 GBP = 1 USD, so 79 GBP ≈ 100 USD
        result = normalize_to_usd(79, "GBP")
        assert abs(result - 100.0) < 0.5

    def test_unknown_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown currency"):
            normalize_to_usd(100, "ZZZ")


# === Account Tests ===


class TestAccounts:
    def test_account_count(self) -> None:
        assert len(ACCOUNTS) == 17

    def test_all_accounts_have_unique_ids(self) -> None:
        ids = [a.id for a in ACCOUNTS.values()]
        assert len(ids) == len(set(ids))

    def test_all_accounts_have_valid_fields(self) -> None:
        valid_currencies = {"XOF", "NGN", "GHS", "KES", "TZS", "ZAR", "MAD", "EGP", "GBP", "USD"}
        for acc in ACCOUNTS.values():
            assert isinstance(acc, Account)
            assert acc.id.startswith("acc_")
            assert len(acc.name) > 0
            assert acc.phone.startswith("+")
            assert acc.balance >= 0
            assert acc.currency in valid_currencies, f"{acc.id} has unknown currency {acc.currency}"
            assert acc.account_type in ("personal", "business")
            assert isinstance(acc.kyc_tier, KYCTier)
            assert len(acc.country) > 0
            assert len(acc.created_at) == 10  # YYYY-MM-DD

    def test_get_account_valid(self) -> None:
        acc = get_account("acc_001")
        assert acc is not None
        assert acc.name == "Amadou Diallo"
        assert acc.balance == 245_000

    def test_get_account_invalid(self) -> None:
        assert get_account("acc_999") is None
        assert get_account("") is None

    def test_get_all_accounts(self) -> None:
        all_accounts = get_all_accounts()
        assert len(all_accounts) == 17
        assert "acc_001" in all_accounts

    def test_get_default_account_id(self) -> None:
        default = get_default_account_id()
        assert default in ACCOUNTS

    def test_waemu_countries_covered(self) -> None:
        countries = {a.country for a in ACCOUNTS.values()}
        assert "Senegal" in countries
        assert "Mali" in countries
        assert "Cote d'Ivoire" in countries
        assert "Burkina Faso" in countries

    def test_pan_african_countries_covered(self) -> None:
        countries = {a.country for a in ACCOUNTS.values()}
        assert "Nigeria" in countries
        assert "Ghana" in countries
        assert "Kenya" in countries
        assert "Tanzania" in countries
        assert "South Africa" in countries
        assert "Morocco" in countries
        assert "Egypt" in countries

    def test_diaspora_countries_covered(self) -> None:
        countries = {a.country for a in ACCOUNTS.values()}
        assert "United Kingdom" in countries
        assert "United States" in countries

    def test_multi_currency_accounts(self) -> None:
        currencies = {a.currency for a in ACCOUNTS.values()}
        assert len(currencies) >= 8, "Should have accounts in at least 8 currencies"

    def test_new_account_data_integrity(self) -> None:
        # Spot-check a few new accounts
        ng = get_account("acc_009")
        assert ng is not None
        assert ng.name == "Chinedu Okafor"
        assert ng.currency == "NGN"
        assert ng.country == "Nigeria"

        uk = get_account("acc_016")
        assert uk is not None
        assert uk.name == "Oluwaseun Adeyemi"
        assert uk.currency == "GBP"
        assert uk.country == "United Kingdom"

    def test_kyc_tiers_represented(self) -> None:
        tiers = {a.kyc_tier for a in ACCOUNTS.values()}
        assert KYCTier.BASIC in tiers
        assert KYCTier.STANDARD in tiers
        assert KYCTier.PREMIUM in tiers


# === Transaction Tests ===


class TestTransactions:
    def test_transaction_count(self) -> None:
        assert len(TRANSACTIONS) >= 70

    def test_all_transactions_reference_valid_accounts(self) -> None:
        for txn in TRANSACTIONS:
            assert txn.account_id in ACCOUNTS, (
                f"Transaction {txn.id} references unknown account {txn.account_id}"
            )

    def test_all_transactions_have_valid_fields(self) -> None:
        for txn in TRANSACTIONS:
            assert txn.id.startswith("txn_")
            assert isinstance(txn.type, TransactionType)
            assert txn.amount > 0
            assert txn.fee >= 0
            assert txn.currency == "XOF"
            assert isinstance(txn.status, TransactionStatus)
            assert len(txn.timestamp) > 0
            assert len(txn.description) > 0

    def test_get_transactions_for_account(self) -> None:
        txns = get_transactions_for_account("acc_001")
        assert len(txns) > 0
        assert all(t.account_id == "acc_001" for t in txns)

    def test_get_transactions_limit(self) -> None:
        txns = get_transactions_for_account("acc_001", limit=3)
        assert len(txns) == 3

    def test_get_transactions_sorted_by_timestamp(self) -> None:
        txns = get_transactions_for_account("acc_001", limit=5)
        timestamps = [t.timestamp for t in txns]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_transactions_empty_account(self) -> None:
        txns = get_transactions_for_account("acc_999")
        assert txns == []

    def test_lookup_transaction_by_id(self) -> None:
        results = lookup_transaction("acc_001", "txn_001")
        assert len(results) == 1
        assert results[0].id == "txn_001"

    def test_lookup_transaction_by_recipient(self) -> None:
        results = lookup_transaction("acc_001", "Moussa")
        assert len(results) >= 1
        assert any("Moussa" in (t.recipient_name or "") for t in results)

    def test_lookup_transaction_no_results(self) -> None:
        results = lookup_transaction("acc_001", "nonexistent_xyz_123")
        assert results == []

    def test_transaction_statuses_diverse(self) -> None:
        statuses = {t.status for t in TRANSACTIONS}
        assert TransactionStatus.COMPLETED in statuses
        assert TransactionStatus.PENDING in statuses
        assert TransactionStatus.FAILED in statuses

    def test_transaction_types_diverse(self) -> None:
        types = {t.type for t in TRANSACTIONS}
        assert TransactionType.P2P in types
        assert TransactionType.CASH_IN in types
        assert TransactionType.CASH_OUT in types
        assert TransactionType.BILL_PAYMENT in types
        assert TransactionType.AIRTIME in types


# === Policy Tests ===


class TestPolicies:
    def test_policy_count(self) -> None:
        assert len(POLICIES) == 10

    def test_all_policies_have_content(self) -> None:
        for policy in POLICIES.values():
            assert len(policy.title_en) > 0
            assert len(policy.content_en) > 10
            assert len(policy.title_fr) > 0
            assert len(policy.content_fr) > 10

    def test_get_policy_valid(self) -> None:
        policy = get_policy("transaction_limits")
        assert policy is not None
        assert "50,000" in policy.content_en or "50000" in policy.content_en

    def test_get_policy_invalid(self) -> None:
        assert get_policy("nonexistent_policy") is None

    def test_search_policies(self) -> None:
        results = search_policies("KYC")
        assert len(results) >= 1

    def test_search_policies_empty(self) -> None:
        results = search_policies("xyznonexistent123")
        assert results == []

    def test_expected_topics_exist(self) -> None:
        expected = [
            "transaction_limits", "fees", "kyc_verification",
            "dispute_resolution", "account_security",
            "send_money_international", "cash_in_cash_out",
            "agent_locations", "account_closure", "privacy_policy",
        ]
        for topic in expected:
            assert topic in POLICIES, f"Missing policy topic: {topic}"


# === Fee Tests ===


class TestFees:
    def test_fee_rules_exist(self) -> None:
        assert len(FEE_RULES) > 0

    def test_calculate_domestic_fee(self) -> None:
        result = calculate_fee(50_000, "XOF", "domestic")
        assert result is not None
        assert result.fee > 0
        assert result.total == result.amount + result.fee
        assert result.corridor == "domestic"

    def test_calculate_international_fee(self) -> None:
        result = calculate_fee(50_000, "XOF", "Mali")
        assert result is not None
        assert result.fee > 0
        assert result.corridor == "SN-ML"

    def test_calculate_fee_cote_divoire(self) -> None:
        result = calculate_fee(100_000, "XOF", "Cote d'Ivoire")
        assert result is not None
        assert result.corridor == "SN-CI"

    def test_calculate_fee_burkina(self) -> None:
        result = calculate_fee(25_000, "XOF", "Burkina Faso")
        assert result is not None
        assert result.corridor == "SN-BF"

    def test_international_fee_higher_than_domestic(self) -> None:
        domestic = calculate_fee(50_000, "XOF", "domestic")
        international = calculate_fee(50_000, "XOF", "Mali")
        assert domestic is not None
        assert international is not None
        assert international.fee >= domestic.fee

    def test_fee_minimum_applied(self) -> None:
        result = calculate_fee(1_000, "XOF", "domestic")
        assert result is not None
        assert result.fee >= 100  # Minimum domestic fee

    def test_fee_scales_with_amount(self) -> None:
        small = calculate_fee(10_000, "XOF", "domestic")
        large = calculate_fee(200_000, "XOF", "domestic")
        assert small is not None
        assert large is not None
        assert large.fee > small.fee


# === Agent Location Tests ===


class TestAgentLocations:
    def test_agent_count(self) -> None:
        assert len(AGENT_LOCATIONS) >= 15

    def test_find_agents_dakar(self) -> None:
        agents = find_agents("Dakar")
        assert len(agents) >= 3

    def test_find_agents_bamako(self) -> None:
        agents = find_agents("Bamako")
        assert len(agents) >= 2

    def test_find_agents_abidjan(self) -> None:
        agents = find_agents("Abidjan")
        assert len(agents) >= 2

    def test_find_agents_ouagadougou(self) -> None:
        agents = find_agents("Ouagadougou")
        assert len(agents) >= 2

    def test_find_agents_by_neighborhood(self) -> None:
        agents = find_agents("Medina")
        assert len(agents) >= 1

    def test_find_agents_case_insensitive(self) -> None:
        agents_lower = find_agents("dakar")
        agents_upper = find_agents("DAKAR")
        assert len(agents_lower) == len(agents_upper)

    def test_find_agents_no_results(self) -> None:
        agents = find_agents("Antarctica")
        assert agents == []

    def test_all_agents_have_valid_fields(self) -> None:
        for agent in AGENT_LOCATIONS:
            assert agent.id.startswith("agt_")
            assert len(agent.name) > 0
            assert len(agent.city) > 0
            assert len(agent.phone) > 0
            assert len(agent.hours) > 0
            assert len(agent.services) > 0
