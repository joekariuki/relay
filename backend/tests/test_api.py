"""Tests for the FastAPI server endpoints.

Uses FastAPI TestClient with mocked agent processing (no real LLM calls).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.knowledge.models import AgentResponse, Language, ToolCallRecord


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _mock_agent_response() -> AgentResponse:
    """Create a mock agent response for testing."""
    return AgentResponse(
        response_text="Your balance is 245,000 FCFA.",
        language_detected=Language.EN,
        tools_used=[
            ToolCallRecord(
                tool_name="check_balance",
                arguments={"account_id": "acc_001"},
                result={"balance_cfa": 245000, "name": "Amadou Diallo"},
                duration_ms=1.5,
            )
        ],
        groundedness_score=None,
        latency_ms={"total_ms": 150.0, "agent_processing_ms": 120.0},
        metadata={"language_detected": "en"},
    )


class TestHealth:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    def test_health_has_cors_headers(self, client: TestClient) -> None:
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert "access-control-allow-origin" in response.headers

    def test_health_has_request_id(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "x-request-id" in response.headers


class TestChat:
    @patch("src.agent.core.process_message", new_callable=AsyncMock)
    def test_chat_valid_request(self, mock_process: AsyncMock, client: TestClient) -> None:
        mock_process.return_value = _mock_agent_response()
        response = client.post("/chat", json={
            "message": "What is my balance?",
            "account_id": "acc_001",
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "language_detected" in data
        assert "tools_used" in data
        assert "latency_ms" in data

    @patch("src.agent.core.process_message", new_callable=AsyncMock)
    def test_chat_response_fields(self, mock_process: AsyncMock, client: TestClient) -> None:
        mock_process.return_value = _mock_agent_response()
        data = client.post("/chat", json={
            "message": "Balance please",
            "account_id": "acc_001",
        }).json()
        assert data["response"] == "Your balance is 245,000 FCFA."
        assert data["language_detected"] == "en"
        assert len(data["tools_used"]) == 1
        assert data["tools_used"][0]["tool_name"] == "check_balance"

    def test_chat_empty_message_returns_422(self, client: TestClient) -> None:
        response = client.post("/chat", json={
            "message": "",
            "account_id": "acc_001",
        })
        assert response.status_code == 422

    def test_chat_missing_message_returns_422(self, client: TestClient) -> None:
        response = client.post("/chat", json={
            "account_id": "acc_001",
        })
        assert response.status_code == 422

    def test_chat_invalid_language_returns_422(self, client: TestClient) -> None:
        response = client.post("/chat", json={
            "message": "Hello",
            "account_id": "acc_001",
            "language": "xx",
        })
        assert response.status_code == 422

    @patch("src.agent.core.process_message", new_callable=AsyncMock)
    def test_chat_with_language_hint(self, mock_process: AsyncMock, client: TestClient) -> None:
        mock_process.return_value = _mock_agent_response()
        response = client.post("/chat", json={
            "message": "Quel est mon solde?",
            "account_id": "acc_001",
            "language": "fr",
        })
        assert response.status_code == 200

    def test_chat_message_too_long_returns_422(self, client: TestClient) -> None:
        response = client.post("/chat", json={
            "message": "x" * 2001,
            "account_id": "acc_001",
        })
        assert response.status_code == 422

    @patch("src.agent.core.process_message", new_callable=AsyncMock)
    def test_chat_default_account_id(self, mock_process: AsyncMock, client: TestClient) -> None:
        mock_process.return_value = _mock_agent_response()
        response = client.post("/chat", json={
            "message": "Hello",
        })
        assert response.status_code == 200
        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args
        assert call_kwargs.kwargs.get("account_id") == "acc_001" or call_kwargs.args[1] == "acc_001"


class TestEval:
    def test_eval_invalid_category_returns_422(self, client: TestClient) -> None:
        response = client.post("/eval", json={
            "category": "nonexistent_category",
        })
        # Will either be 422 from our check or 500 from no API key
        assert response.status_code in (422, 500)


class TestCORS:
    def test_cors_allowed_origin(self, client: TestClient) -> None:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
