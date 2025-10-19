"""Shared fixtures for integration tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_qdrant_client():
    """Mock AsyncQdrantClient for integration tests."""
    mock_client = AsyncMock()

    # Mock get_collections
    mock_collection = MagicMock()
    mock_collection.name = "test-collection"
    mock_collections_response = MagicMock()
    mock_collections_response.collections = [mock_collection]
    mock_client.get_collections.return_value = mock_collections_response

    # Mock create_collection
    mock_client.create_collection.return_value = None

    # Mock upsert
    mock_client.upsert.return_value = None

    # Mock search
    mock_result = MagicMock()
    mock_result.id = "test-id-1"
    mock_result.score = 0.95
    mock_result.payload = {"text": "Test chunk", "chunk_index": 0}
    mock_client.search.return_value = [mock_result]

    # Mock retrieve
    mock_point = MagicMock()
    mock_point.payload = {"text": "Test document", "metadata": "test"}
    mock_client.retrieve.return_value = [mock_point]

    # Mock delete_collection
    mock_client.delete_collection.return_value = None

    # Mock close
    mock_client.close.return_value = None

    return mock_client


@pytest.fixture
def mock_azure_openai_client():
    """Mock AsyncAzureOpenAI for integration tests."""
    mock_client = AsyncMock()

    # Mock embeddings.create for single text
    mock_embedding_response = MagicMock()
    mock_embedding_data = MagicMock()
    mock_embedding_data.embedding = [0.1] * 1536  # 1536-dimensional vector
    mock_embedding_response.data = [mock_embedding_data]
    mock_client.embeddings.create.return_value = mock_embedding_response

    # Mock close
    mock_client.close.return_value = None

    return mock_client


@pytest.fixture
def app_client(mock_qdrant_client, mock_azure_openai_client):
    """Create TestClient with mocked dependencies."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient", return_value=mock_qdrant_client):
        with patch(
            "remote_rag.services.embedder.AsyncAzureOpenAI", return_value=mock_azure_openai_client
        ):
            # Import fresh to ensure lifespan events run
            import sys
            if "remote_rag.api.app" in sys.modules:
                del sys.modules["remote_rag.api.app"]
            if "remote_rag.api" in sys.modules:
                del sys.modules["remote_rag.api"]

            from remote_rag.api import app

            # Use TestClient with proper lifespan context
            # raise_server_exceptions=False allows us to test error responses
            with TestClient(app, raise_server_exceptions=False) as client:
                yield client
