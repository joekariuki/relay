"""Tests for RAG policy retrieval with ChromaDB and OpenAI embeddings.

Uses mocked OpenAI API calls — no real embeddings generated during testing.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.knowledge.models import Policy
from src.knowledge.policies import POLICIES
from src.knowledge.rag import PolicyRAG, query_policies_rag


def _fake_embedding(dim: int = 16) -> list[float]:
    """Return a deterministic fake embedding vector."""
    return [0.1] * dim


def _fake_embeddings_response(texts: list[str], dim: int = 16) -> MagicMock:
    """Build a mock OpenAI embeddings response with unique vectors per text."""
    mock_response = MagicMock()
    data = []
    for i, _ in enumerate(texts):
        item = MagicMock()
        # Give each text a slightly different embedding so ChromaDB can distinguish
        vec = [0.1 + (i * 0.05)] * dim
        item.embedding = vec
        data.append(item)
    mock_response.data = data
    return mock_response


class TestPolicyRAGInit:
    """Test PolicyRAG initialization and indexing."""

    @patch("src.knowledge.rag.OpenAI")
    def test_init_indexes_all_policies(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.embeddings.create.return_value = _fake_embeddings_response(
            list(POLICIES.keys())
        )

        rag = PolicyRAG(openai_api_key="test-key")

        assert rag._indexed is True
        mock_client.embeddings.create.assert_called_once()
        # Verify all policies were embedded
        call_args = mock_client.embeddings.create.call_args
        assert len(call_args.kwargs["input"]) == len(POLICIES)

    @patch("src.knowledge.rag.OpenAI")
    def test_init_handles_embedding_failure(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.embeddings.create.side_effect = Exception("API timeout")

        rag = PolicyRAG(openai_api_key="test-key")

        assert rag._indexed is False

    @patch("src.knowledge.rag.OpenAI")
    def test_embedding_model_is_text_embedding_3_small(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.embeddings.create.return_value = _fake_embeddings_response(
            list(POLICIES.keys())
        )

        PolicyRAG(openai_api_key="test-key")

        call_args = mock_client.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-small"


class TestPolicyRAGQuery:
    """Test RAG query functionality."""

    @patch("src.knowledge.rag.OpenAI")
    def test_query_returns_ranked_results(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Index embeddings
        mock_client.embeddings.create.return_value = _fake_embeddings_response(
            list(POLICIES.keys())
        )
        rag = PolicyRAG(openai_api_key="test-key")

        # Query embedding
        query_mock = MagicMock()
        query_item = MagicMock()
        query_item.embedding = [0.1] * 16
        query_mock.data = [query_item]
        mock_client.embeddings.create.return_value = query_mock

        results = rag.query("What are the fees for transfers?", top_k=3)

        assert len(results) > 0
        assert len(results) <= 3
        # Each result is a (Policy, score) tuple
        for policy, score in results:
            assert isinstance(policy, Policy)
            assert 0.0 <= score <= 1.0

    @patch("src.knowledge.rag.OpenAI")
    def test_query_falls_back_on_failure(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Index succeeds
        mock_client.embeddings.create.return_value = _fake_embeddings_response(
            list(POLICIES.keys())
        )
        rag = PolicyRAG(openai_api_key="test-key")

        # Query fails
        mock_client.embeddings.create.side_effect = Exception("API error")

        results = rag.query("fees")

        # Should still return results via keyword fallback
        assert len(results) > 0
        assert any(p.topic == "fees" for p, _ in results)

    @patch("src.knowledge.rag.OpenAI")
    def test_query_falls_back_when_not_indexed(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Index fails
        mock_client.embeddings.create.side_effect = Exception("API timeout")
        rag = PolicyRAG(openai_api_key="test-key")
        assert rag._indexed is False

        # Query should use fallback
        results = rag.query("transaction_limits")

        assert len(results) == 1
        assert results[0][0].topic == "transaction_limits"
        assert results[0][1] == 1.0  # Exact match score

    @patch("src.knowledge.rag.OpenAI")
    def test_query_keyword_fallback_partial_match(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Index fails
        mock_client.embeddings.create.side_effect = Exception("API timeout")
        rag = PolicyRAG(openai_api_key="test-key")

        # Should find policies via keyword search
        results = rag.query("KYC")

        assert len(results) > 0
        topics = {p.topic for p, _ in results}
        assert "kyc_verification" in topics

    @patch("src.knowledge.rag.OpenAI")
    def test_query_respects_top_k(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.embeddings.create.return_value = _fake_embeddings_response(
            list(POLICIES.keys())
        )
        rag = PolicyRAG(openai_api_key="test-key")

        # Query
        query_mock = MagicMock()
        query_item = MagicMock()
        query_item.embedding = [0.1] * 16
        query_mock.data = [query_item]
        mock_client.embeddings.create.return_value = query_mock

        results = rag.query("policy", top_k=2)

        assert len(results) <= 2


class TestQueryPoliciesRAG:
    """Test the module-level query_policies_rag convenience function."""

    def test_returns_results_without_rag_initialized(self) -> None:
        """When RAG is not initialized, should fallback to keyword search."""
        # Reset module-level singleton
        import src.knowledge.rag as rag_mod
        original = rag_mod._rag_instance
        rag_mod._rag_instance = None
        try:
            results = query_policies_rag("fees")
            assert len(results) > 0
            assert any(p.topic == "fees" for p, _ in results)
        finally:
            rag_mod._rag_instance = original

    def test_exact_topic_match_without_rag(self) -> None:
        """Exact topic match returns score 1.0."""
        import src.knowledge.rag as rag_mod
        original = rag_mod._rag_instance
        rag_mod._rag_instance = None
        try:
            results = query_policies_rag("dispute_resolution")
            assert len(results) == 1
            assert results[0][0].topic == "dispute_resolution"
            assert results[0][1] == 1.0
        finally:
            rag_mod._rag_instance = original

    def test_no_match_returns_empty(self) -> None:
        """Queries with no match return empty list."""
        import src.knowledge.rag as rag_mod
        original = rag_mod._rag_instance
        rag_mod._rag_instance = None
        try:
            results = query_policies_rag("quantum_physics_explanation")
            assert results == []
        finally:
            rag_mod._rag_instance = original


class TestToolHandlerIntegration:
    """Test that handle_get_policy uses RAG correctly."""

    def test_handle_get_policy_returns_results_without_rag(self) -> None:
        """Tool handler works even when RAG is not initialized."""
        import src.knowledge.rag as rag_mod
        original = rag_mod._rag_instance
        rag_mod._rag_instance = None
        try:
            from src.agent.tools import handle_get_policy

            result = handle_get_policy({"topic": "fees"})
            assert "topic" in result
            assert result["topic"] == "fees"
        finally:
            rag_mod._rag_instance = original

    def test_handle_get_policy_empty_topic_returns_error(self) -> None:
        from src.agent.tools import handle_get_policy

        result = handle_get_policy({"topic": ""})
        assert "error" in result

    def test_handle_get_policy_unknown_topic_returns_error(self) -> None:
        """Unknown topic with no keyword match returns error."""
        import src.knowledge.rag as rag_mod
        original = rag_mod._rag_instance
        rag_mod._rag_instance = None
        try:
            from src.agent.tools import handle_get_policy

            result = handle_get_policy({"topic": "xyzzy_nonexistent_topic_999"})
            assert "error" in result
        finally:
            rag_mod._rag_instance = original
