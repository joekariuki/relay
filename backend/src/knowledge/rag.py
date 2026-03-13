"""RAG policy retrieval using ChromaDB and OpenAI embeddings.

Provides semantic search over DuniaWallet policy documents with a
fallback chain: RAG -> keyword search -> exact topic match.

Architecture:
    User query
        |
        v
    EMBED QUERY (OpenAI text-embedding-3-small)
        |
        v
    VECTOR SEARCH (ChromaDB in-memory)
        |
        v
    RANK & RETURN top-k Policy objects
        |
        v  (on any failure)
    FALLBACK: keyword search_policies() / get_policy()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import chromadb
from openai import OpenAI

from .models import Policy
from .policies import POLICIES, get_policy, search_policies

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_COLLECTION_NAME = "duniawallet_policies"


class PolicyRAG:
    """Semantic search over DuniaWallet policies via ChromaDB + OpenAI embeddings.

    Embeds all policy documents (EN + FR content) at initialization and
    provides a query method that returns ranked Policy results.

    Falls back to keyword search if embedding or vector search fails.
    """

    def __init__(self, openai_api_key: str) -> None:
        self._client = OpenAI(api_key=openai_api_key)
        self._chroma = chromadb.EphemeralClient()
        self._collection = self._chroma.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._indexed = False
        self._index_policies()

    def _index_policies(self) -> None:
        """Embed and index all policies into ChromaDB."""
        policies = list(POLICIES.values())
        if not policies:
            logger.warning("No policies to index for RAG")
            return

        # Build documents: combine EN + FR content for multilingual retrieval
        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, str]] = []

        for policy in policies:
            doc_text = (
                f"{policy.title_en}\n{policy.content_en}\n"
                f"{policy.title_fr}\n{policy.content_fr}"
            )
            documents.append(doc_text)
            ids.append(policy.topic)
            metadatas.append({"topic": policy.topic, "title_en": policy.title_en})

        try:
            embeddings = self._embed_texts(documents)
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            self._indexed = True
            logger.info("Indexed %d policies for RAG retrieval", len(policies))
        except Exception:
            logger.exception("Failed to index policies for RAG — falling back to keyword search")
            self._indexed = False

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings from OpenAI API."""
        response = self._client.embeddings.create(
            model=_EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def query(self, text: str, top_k: int = 3) -> list[tuple[Policy, float]]:
        """Query policies by semantic similarity.

        Returns a list of (Policy, relevance_score) tuples, ordered by
        relevance (highest first). Scores are cosine similarity (0-1).

        Falls back to keyword search on any failure.
        """
        if not self._indexed:
            return self._fallback_query(text, top_k)

        try:
            query_embedding = self._embed_texts([text])[0]
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, len(POLICIES)),
            )
        except Exception:
            logger.exception("RAG query failed — falling back to keyword search")
            return self._fallback_query(text, top_k)

        # Parse results into (Policy, score) tuples
        ranked: list[tuple[Policy, float]] = []
        if results["ids"] and results["ids"][0]:
            topics = results["ids"][0]
            # ChromaDB returns distances; for cosine space, distance = 1 - similarity
            distances = results["distances"][0] if results["distances"] else [0.0] * len(topics)
            for topic, distance in zip(topics, distances):
                policy = POLICIES.get(topic)
                if policy is not None:
                    similarity = 1.0 - distance
                    ranked.append((policy, similarity))

        if not ranked:
            return self._fallback_query(text, top_k)

        return ranked

    def _fallback_query(self, text: str, top_k: int) -> list[tuple[Policy, float]]:
        """Fallback: use keyword search when RAG is unavailable."""
        logger.info("Using keyword fallback for query: %s", text[:80])

        # Try exact topic match first
        policy = get_policy(text)
        if policy is not None:
            return [(policy, 1.0)]

        # Keyword search
        results = search_policies(text)
        return [(p, 0.5) for p in results[:top_k]]


# Module-level singleton, initialized lazily
_rag_instance: PolicyRAG | None = None


def get_policy_rag() -> PolicyRAG | None:
    """Get the singleton PolicyRAG instance.

    Returns None if RAG is not configured (no OpenAI API key or use_rag=False).
    """
    return _rag_instance


def initialize_rag(openai_api_key: str) -> PolicyRAG:
    """Initialize the RAG instance. Called at server startup."""
    global _rag_instance  # noqa: PLW0603
    _rag_instance = PolicyRAG(openai_api_key)
    return _rag_instance


def query_policies_rag(text: str, top_k: int = 3) -> list[tuple[Policy, float]]:
    """Query policies using RAG if available, otherwise keyword search.

    This is the main entry point for tool handlers.
    """
    rag = get_policy_rag()
    if rag is not None:
        return rag.query(text, top_k)

    # No RAG available — use keyword fallback
    policy = get_policy(text)
    if policy is not None:
        return [(policy, 1.0)]
    results = search_policies(text)
    return [(p, 0.5) for p in results[:top_k]]
