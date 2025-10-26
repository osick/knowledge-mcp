"""Shared test fixtures for Document Intelligence MCP Server."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_azure_search_client() -> AsyncMock:
    """Create a mock Azure Search client for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def sample_search_results() -> list[dict]:
    """Sample search results matching Azure Search response format."""
    return [
        {
            "@search.score": 0.92,
            "id": "doc-1",
            "content": "Machine learning is a subset of artificial intelligence.",
            "source": "ml-guide.pdf",
            "title": "Introduction to ML",
        },
        {
            "@search.score": 0.87,
            "id": "doc-2",
            "content": "Deep learning uses neural networks with multiple layers.",
            "source": "dl-basics.pdf",
            "title": "Deep Learning Basics",
        },
        {
            "@search.score": 0.81,
            "id": "doc-3",
            "content": "Natural language processing enables computers to understand text.",
            "source": "nlp-intro.pdf",
            "title": "NLP Introduction",
        },
    ]


@pytest.fixture
def sample_document() -> dict:
    """Sample document matching Azure Search document format."""
    return {
        "id": "doc-1",
        "content": "Machine learning is a subset of artificial intelligence that enables "
        "computers to learn from data without being explicitly programmed.",
        "source": "ml-guide.pdf",
        "title": "Introduction to ML",
        "author": "John Doe",
        "date": "2025-01-15",
    }


@pytest.fixture
def sample_indexes() -> list[str]:
    """Sample list of index names."""
    return ["default", "technical-docs", "product-manuals", "company-policies"]
