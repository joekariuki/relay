"""Agent tool definitions and handler implementations.

Each tool has:
- An Anthropic API schema (for the LLM)
- A Python handler function (calls into the knowledge layer)
- Input validation and structured error responses
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from src.knowledge.accounts import get_account
from src.knowledge.agents_data import find_agents
from src.knowledge.fees import calculate_fee
from src.knowledge.models import ToolCallRecord
from src.knowledge.policies import get_policy, search_policies
from src.knowledge.transactions import get_transactions_for_account, lookup_transaction

# === Tool Schemas (Anthropic API format) ===

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "check_balance",
        "description": (
            "Check the current balance of a DuniaWallet account. "
            "Returns the balance in CFA Francs, account holder name, and KYC tier. "
            "The account ID is partially masked for security."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The DuniaWallet account ID (e.g. 'acc_001')",
                },
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "get_transactions",
        "description": (
            "Get recent transactions for a DuniaWallet account, sorted by most recent first. "
            "Returns transaction details including type, amount, recipient, status, and timestamp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The DuniaWallet account ID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return (1-20, default 5)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
                },
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "lookup_transaction",
        "description": (
            "Search for specific transactions by transaction ID, recipient name, or description. "
            "Useful when the user asks about a specific transfer or payment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The DuniaWallet account ID",
                },
                "query": {
                    "type": "string",
                    "description": "Search query: transaction ID, recipient name, or keyword",
                },
            },
            "required": ["account_id", "query"],
        },
    },
    {
        "name": "calculate_fees",
        "description": (
            "Calculate the transfer fee for a given amount and destination. "
            "Returns the fee amount, total cost, and fee percentage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": "Transfer amount in CFA Francs",
                    "minimum": 1,
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (default 'XOF')",
                    "default": "XOF",
                },
                "destination_country": {
                    "type": "string",
                    "description": (
                        "Destination: 'domestic' for local, or country name "
                        "(e.g. 'Mali', 'Cote d\\'Ivoire', 'Burkina Faso')"
                    ),
                },
            },
            "required": ["amount", "destination_country"],
        },
    },
    {
        "name": "find_agent",
        "description": (
            "Find DuniaWallet cash-in/cash-out agents near a given location. "
            "Returns agent names, addresses, phone numbers, operating hours, and services."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City, neighborhood, or area name to search",
                },
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_policy",
        "description": (
            "Retrieve a DuniaWallet service policy by topic. Available topics: "
            "transaction_limits, fees, kyc_verification, dispute_resolution, "
            "account_security, send_money_international, cash_in_cash_out, "
            "agent_locations, account_closure, privacy_policy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Policy topic key",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "create_support_ticket",
        "description": (
            "Create a support ticket for issues that cannot be resolved directly. "
            "Use this for disputes, account problems, or complex requests that "
            "require human agent intervention."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The DuniaWallet account ID",
                },
                "category": {
                    "type": "string",
                    "description": "Ticket category",
                    "enum": [
                        "dispute",
                        "account_issue",
                        "transaction_problem",
                        "kyc_upgrade",
                        "other",
                    ],
                },
                "summary": {
                    "type": "string",
                    "description": "Brief description of the issue",
                },
                "priority": {
                    "type": "string",
                    "description": "Ticket priority level",
                    "enum": ["low", "medium", "high", "urgent"],
                    "default": "medium",
                },
            },
            "required": ["account_id", "category", "summary"],
        },
    },
]


# === Tool Handlers ===


def _mask_account_id(account_id: str) -> str:
    """Mask an account ID for security (e.g. 'acc_001' -> '****001')."""
    if len(account_id) > 4:
        return "****" + account_id[-3:]
    return "****"


def _format_cfa(amount: int) -> str:
    """Format a CFA amount with thousands separator."""
    return f"{amount:,} FCFA"


def handle_check_balance(args: dict[str, Any]) -> dict[str, Any]:
    """Handle check_balance tool call."""
    account_id = args.get("account_id", "")
    if not account_id:
        return {"error": "account_id is required"}

    account = get_account(account_id)
    if account is None:
        return {"error": f"Account {_mask_account_id(account_id)} not found"}

    return {
        "account_id_masked": _mask_account_id(account_id),
        "name": account.name,
        "balance": _format_cfa(account.balance_cfa),
        "balance_cfa": account.balance_cfa,
        "currency": account.currency,
        "account_type": account.account_type,
        "kyc_tier": account.kyc_tier.value,
        "country": account.country,
    }


def handle_get_transactions(args: dict[str, Any]) -> dict[str, Any]:
    """Handle get_transactions tool call."""
    account_id = args.get("account_id", "")
    if not account_id:
        return {"error": "account_id is required"}

    limit = min(max(int(args.get("limit", 5)), 1), 20)
    txns = get_transactions_for_account(account_id, limit=limit)

    if not txns:
        account = get_account(account_id)
        if account is None:
            return {"error": f"Account {_mask_account_id(account_id)} not found"}
        return {"transactions": [], "count": 0, "message": "No transactions found"}

    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.type.value,
                "amount": _format_cfa(t.amount_cfa),
                "amount_cfa": t.amount_cfa,
                "fee": _format_cfa(t.fee_cfa),
                "recipient": t.recipient_name or "N/A",
                "description": t.description,
                "status": t.status.value,
                "timestamp": t.timestamp,
                "corridor": t.corridor or "local",
            }
            for t in txns
        ],
        "count": len(txns),
    }


def handle_lookup_transaction(args: dict[str, Any]) -> dict[str, Any]:
    """Handle lookup_transaction tool call."""
    account_id = args.get("account_id", "")
    query = args.get("query", "")
    if not account_id or not query:
        return {"error": "account_id and query are required"}

    results = lookup_transaction(account_id, query)
    if not results:
        return {"results": [], "count": 0, "message": f"No transactions matching '{query}'"}

    return {
        "results": [
            {
                "id": t.id,
                "type": t.type.value,
                "amount": _format_cfa(t.amount_cfa),
                "amount_cfa": t.amount_cfa,
                "fee": _format_cfa(t.fee_cfa),
                "recipient": t.recipient_name or "N/A",
                "description": t.description,
                "status": t.status.value,
                "timestamp": t.timestamp,
                "corridor": t.corridor or "local",
            }
            for t in results
        ],
        "count": len(results),
    }


def handle_calculate_fees(args: dict[str, Any]) -> dict[str, Any]:
    """Handle calculate_fees tool call."""
    amount = args.get("amount")
    if amount is None or not isinstance(amount, (int, float)):
        return {"error": "amount must be a positive integer"}
    amount = int(amount)
    if amount <= 0:
        return {"error": "amount must be a positive integer"}

    currency = str(args.get("currency", "XOF"))
    destination = str(args.get("destination_country", "domestic"))

    result = calculate_fee(amount, currency, destination)
    if result is None:
        return {
            "error": f"No fee rule found for {_format_cfa(amount)} to {destination}. "
            "Amount may exceed maximum transfer limit."
        }

    return {
        "amount": _format_cfa(result.amount),
        "amount_cfa": result.amount,
        "fee": _format_cfa(result.fee),
        "fee_cfa": result.fee,
        "total": _format_cfa(result.total),
        "total_cfa": result.total,
        "currency": result.currency,
        "corridor": result.corridor,
        "fee_percent": result.fee_percent,
    }


def handle_find_agent(args: dict[str, Any]) -> dict[str, Any]:
    """Handle find_agent tool call."""
    location = args.get("location", "")
    if not location:
        return {"error": "location is required"}

    agents = find_agents(location)
    if not agents:
        return {"agents": [], "count": 0, "message": f"No agents found near '{location}'"}

    return {
        "agents": [
            {
                "name": a.name,
                "city": a.city,
                "neighborhood": a.neighborhood,
                "country": a.country,
                "phone": a.phone,
                "hours": a.hours,
                "services": list(a.services),
            }
            for a in agents
        ],
        "count": len(agents),
    }


def handle_get_policy(args: dict[str, Any]) -> dict[str, Any]:
    """Handle get_policy tool call."""
    topic = args.get("topic", "")
    if not topic:
        # Try search instead
        return {"error": "topic is required. Use search_policies for keyword search."}

    policy = get_policy(topic)
    if policy is not None:
        return {
            "topic": policy.topic,
            "title_en": policy.title_en,
            "content_en": policy.content_en,
            "title_fr": policy.title_fr,
            "content_fr": policy.content_fr,
        }

    # Fall back to keyword search
    results = search_policies(topic)
    if results:
        return {
            "note": f"No exact match for '{topic}', showing search results",
            "results": [
                {
                    "topic": p.topic,
                    "title_en": p.title_en,
                    "content_en": p.content_en,
                    "title_fr": p.title_fr,
                    "content_fr": p.content_fr,
                }
                for p in results
            ],
        }

    return {"error": f"No policy found for topic '{topic}'"}


_ticket_counter = 0


def handle_create_support_ticket(args: dict[str, Any]) -> dict[str, Any]:
    """Handle create_support_ticket tool call."""
    global _ticket_counter  # noqa: PLW0603

    account_id = args.get("account_id", "")
    category = args.get("category", "")
    summary = args.get("summary", "")

    if not account_id or not category or not summary:
        return {"error": "account_id, category, and summary are required"}

    account = get_account(account_id)
    if account is None:
        return {"error": f"Account {_mask_account_id(account_id)} not found"}

    valid_categories = {"dispute", "account_issue", "transaction_problem", "kyc_upgrade", "other"}
    if category not in valid_categories:
        return {"error": f"Invalid category. Must be one of: {', '.join(sorted(valid_categories))}"}

    _ticket_counter += 1
    ticket_id = f"TKT-{_ticket_counter:04d}"
    priority = args.get("priority", "medium")

    return {
        "ticket_id": ticket_id,
        "status": "created",
        "category": category,
        "priority": priority,
        "summary": summary,
        "message": (
            f"Support ticket {ticket_id} has been created. "
            "Our team will review it within 24-48 hours."
        ),
    }


# === Tool Dispatcher ===

_HANDLERS: dict[str, Any] = {
    "check_balance": handle_check_balance,
    "get_transactions": handle_get_transactions,
    "lookup_transaction": handle_lookup_transaction,
    "calculate_fees": handle_calculate_fees,
    "find_agent": handle_find_agent,
    "get_policy": handle_get_policy,
    "create_support_ticket": handle_create_support_ticket,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> ToolCallRecord:
    """Execute a tool by name with the given arguments.

    Returns a ToolCallRecord with the result and execution duration.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        result: dict[str, object] = {"error": f"Unknown tool: {name}"}
        return ToolCallRecord(
            tool_name=name,
            arguments=arguments,
            result=result,
            duration_ms=0.0,
        )

    start = time.perf_counter()
    try:
        result = handler(arguments)
    except Exception as e:
        result = {"error": f"Tool execution failed: {e!s}"}
    duration_ms = (time.perf_counter() - start) * 1000

    return ToolCallRecord(
        tool_name=name,
        arguments=arguments,
        result=result,
        duration_ms=duration_ms,
    )
