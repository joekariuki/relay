"""Tests for agent tool handlers."""

from src.agent.tools import (
    execute_tool,
    handle_calculate_fees,
    handle_check_balance,
    handle_create_support_ticket,
    handle_find_agent,
    handle_get_policy,
    handle_get_transactions,
    handle_lookup_transaction,
)


class TestCheckBalance:
    def test_valid_account(self) -> None:
        result = handle_check_balance({"account_id": "acc_001"})
        assert result["account_id_masked"] == "****001"
        assert result["name"] == "Amadou Diallo"
        assert result["balance_cfa"] == 245_000
        assert "FCFA" in result["balance"]
        assert result["kyc_tier"] == "standard"

    def test_invalid_account(self) -> None:
        result = handle_check_balance({"account_id": "acc_999"})
        assert "error" in result

    def test_empty_account_id(self) -> None:
        result = handle_check_balance({"account_id": ""})
        assert "error" in result

    def test_missing_account_id(self) -> None:
        result = handle_check_balance({})
        assert "error" in result

    def test_account_id_is_masked(self) -> None:
        result = handle_check_balance({"account_id": "acc_001"})
        assert "acc_001" not in str(result)
        assert "****001" in str(result)


class TestGetTransactions:
    def test_valid_account(self) -> None:
        result = handle_get_transactions({"account_id": "acc_001"})
        assert "transactions" in result
        assert result["count"] > 0

    def test_with_limit(self) -> None:
        result = handle_get_transactions({"account_id": "acc_001", "limit": 3})
        assert result["count"] == 3

    def test_limit_capped_at_20(self) -> None:
        result = handle_get_transactions({"account_id": "acc_001", "limit": 50})
        assert result["count"] <= 20

    def test_invalid_account(self) -> None:
        result = handle_get_transactions({"account_id": "acc_999"})
        assert "error" in result

    def test_transaction_fields(self) -> None:
        result = handle_get_transactions({"account_id": "acc_001", "limit": 1})
        txn = result["transactions"][0]
        assert "id" in txn
        assert "type" in txn
        assert "amount" in txn
        assert "status" in txn
        assert "timestamp" in txn


class TestLookupTransaction:
    def test_by_id(self) -> None:
        result = handle_lookup_transaction({"account_id": "acc_001", "query": "txn_001"})
        assert result["count"] == 1
        assert result["results"][0]["id"] == "txn_001"

    def test_by_recipient(self) -> None:
        result = handle_lookup_transaction({"account_id": "acc_001", "query": "Moussa"})
        assert result["count"] >= 1

    def test_no_results(self) -> None:
        result = handle_lookup_transaction(
            {"account_id": "acc_001", "query": "nonexistent_xyz_123"}
        )
        assert result["count"] == 0

    def test_missing_params(self) -> None:
        result = handle_lookup_transaction({"account_id": "acc_001"})
        assert "error" in result


class TestCalculateFees:
    def test_domestic_fee(self) -> None:
        result = handle_calculate_fees(
            {"amount": 50_000, "currency": "XOF", "destination_country": "domestic"}
        )
        assert "error" not in result
        assert result["fee_cfa"] > 0
        assert result["total_cfa"] == result["amount_cfa"] + result["fee_cfa"]
        assert result["corridor"] == "domestic"

    def test_international_fee(self) -> None:
        result = handle_calculate_fees(
            {"amount": 50_000, "currency": "XOF", "destination_country": "Mali"}
        )
        assert "error" not in result
        assert result["corridor"] == "SN-ML"

    def test_zero_amount(self) -> None:
        result = handle_calculate_fees(
            {"amount": 0, "destination_country": "domestic"}
        )
        assert "error" in result

    def test_missing_amount(self) -> None:
        result = handle_calculate_fees({"destination_country": "domestic"})
        assert "error" in result

    def test_default_currency(self) -> None:
        result = handle_calculate_fees(
            {"amount": 10_000, "destination_country": "domestic"}
        )
        assert result["currency"] == "XOF"


class TestFindAgent:
    def test_find_dakar(self) -> None:
        result = handle_find_agent({"location": "Dakar"})
        assert result["count"] >= 3

    def test_find_bamako(self) -> None:
        result = handle_find_agent({"location": "Bamako"})
        assert result["count"] >= 2

    def test_no_results(self) -> None:
        result = handle_find_agent({"location": "Antarctica"})
        assert result["count"] == 0

    def test_empty_location(self) -> None:
        result = handle_find_agent({"location": ""})
        assert "error" in result

    def test_agent_fields(self) -> None:
        result = handle_find_agent({"location": "Dakar"})
        agent = result["agents"][0]
        assert "name" in agent
        assert "city" in agent
        assert "phone" in agent
        assert "hours" in agent
        assert "services" in agent


class TestGetPolicy:
    def test_valid_topic(self) -> None:
        result = handle_get_policy({"topic": "transaction_limits"})
        assert "content_en" in result
        assert "content_fr" in result
        assert "50,000" in result["content_en"] or "50000" in result["content_en"]

    def test_invalid_topic_falls_back_to_search(self) -> None:
        result = handle_get_policy({"topic": "KYC"})
        # Should find policy via search fallback
        assert "results" in result or "content_en" in result

    def test_completely_unknown_topic(self) -> None:
        result = handle_get_policy({"topic": "xyznonexistent123"})
        assert "error" in result

    def test_empty_topic(self) -> None:
        result = handle_get_policy({"topic": ""})
        assert "error" in result


class TestCreateSupportTicket:
    def test_create_valid_ticket(self) -> None:
        result = handle_create_support_ticket({
            "account_id": "acc_001",
            "category": "dispute",
            "summary": "Unauthorized transaction on my account",
            "priority": "high",
        })
        assert result["status"] == "created"
        assert result["ticket_id"].startswith("TKT-")
        assert result["category"] == "dispute"

    def test_invalid_account(self) -> None:
        result = handle_create_support_ticket({
            "account_id": "acc_999",
            "category": "dispute",
            "summary": "Test issue",
        })
        assert "error" in result

    def test_invalid_category(self) -> None:
        result = handle_create_support_ticket({
            "account_id": "acc_001",
            "category": "invalid_cat",
            "summary": "Test issue",
        })
        assert "error" in result

    def test_missing_params(self) -> None:
        result = handle_create_support_ticket({"account_id": "acc_001"})
        assert "error" in result


class TestExecuteTool:
    def test_dispatch_known_tool(self) -> None:
        record = execute_tool("check_balance", {"account_id": "acc_001"})
        assert record.tool_name == "check_balance"
        assert record.duration_ms >= 0
        assert "error" not in record.result

    def test_dispatch_unknown_tool(self) -> None:
        record = execute_tool("nonexistent_tool", {})
        assert "error" in record.result

    def test_record_has_arguments(self) -> None:
        args = {"account_id": "acc_001"}
        record = execute_tool("check_balance", args)
        assert record.arguments == args
