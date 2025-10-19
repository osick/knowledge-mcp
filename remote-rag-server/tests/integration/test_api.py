"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_no_auth_required(self, app_client):
        """Health check should not require authentication."""
        response = app_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data

    def test_health_check_returns_service_status(self, app_client):
        """Health check should return status of all services."""
        response = app_client.get("/health")
        data = response.json()
        assert "qdrant" in data["services"]
        assert "embedder" in data["services"]
        assert "chunker" in data["services"]


class TestAuthentication:
    """Tests for API key authentication."""

    def test_missing_api_key(self, app_client):
        """Requests without API key should be rejected."""
        response = app_client.post("/ingest", json={"text": "test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "API key" in data["message"]

    def test_invalid_api_key(self, app_client):
        """Requests with invalid API key should be rejected."""
        response = app_client.post(
            "/ingest",
            json={"text": "test"},
            headers={"X-API-Key": "invalid-key"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_api_key(self, app_client):
        """Requests with valid API key should be accepted."""
        response = app_client.post(
            "/ingest",
            json={"text": "This is a test document for ingestion."},
            headers={"X-API-Key": "test-api-key"},
        )
        # Should not be auth error (may be other errors depending on mocks)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN


class TestIngestEndpoint:
    """Tests for /ingest endpoint."""

    def test_ingest_text_success(self, app_client):
        """Successfully ingest text."""
        response = app_client.post(
            "/ingest",
            json={
                "text": "This is a test document for semantic search. It contains multiple sentences.",
                "collection_name": "test-collection",
                "metadata": {"source": "test"},
            },
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "chunks_created" in data
        assert data["collection_name"] == "test-collection"
        assert "chunk_ids" in data

    def test_ingest_text_default_collection(self, app_client):
        """Ingest should use default collection if not specified."""
        response = app_client.post(
            "/ingest",
            json={"text": "Test document without collection specified."},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_name"] == "default"

    def test_ingest_empty_text(self, app_client):
        """Ingesting empty text should fail."""
        response = app_client.post(
            "/ingest",
            json={"text": ""},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_whitespace_only(self, app_client):
        """Ingesting whitespace-only text should fail."""
        response = app_client.post(
            "/ingest",
            json={"text": "   \n\t   "},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestIngestURLEndpoint:
    """Tests for /ingest_url endpoint."""

    @patch("remote_rag.api.app.httpx.AsyncClient")
    @patch("remote_rag.api.app.MarkItDown")
    def test_ingest_url_success(self, mock_markitdown, mock_httpx, app_client):
        """Successfully ingest document from URL."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = b"PDF content"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_httpx.return_value = mock_client

        # Mock markitdown conversion
        mock_md_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.text_content = "This is the converted text from the PDF document."
        mock_md_instance.convert.return_value = mock_result
        mock_markitdown.return_value = mock_md_instance

        response = app_client.post(
            "/ingest_url",
            json={
                "url": "https://example.com/document.pdf",
                "collection_name": "test-collection",
            },
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "https://example.com/document.pdf"
        assert "chunks_created" in data
        assert "document_length" in data

    def test_ingest_url_invalid_url(self, app_client):
        """Invalid URL should be rejected."""
        response = app_client.post(
            "/ingest_url",
            json={"url": "not-a-valid-url"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSearchEndpoint:
    """Tests for /search endpoint."""

    def test_search_success(self, app_client):
        """Successfully search for documents."""
        response = app_client.post(
            "/search",
            json={
                "query": "test query",
                "collection_name": "test-collection",
                "limit": 5,
                "score_threshold": 0.5,
            },
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["query"] == "test query"
        assert "results" in data
        assert "count" in data

    def test_search_with_defaults(self, app_client):
        """Search with default parameters."""
        response = app_client.post(
            "/search",
            json={"query": "test query"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_name"] == "default"

    def test_search_empty_query(self, app_client):
        """Empty query should be rejected."""
        response = app_client.post(
            "/search",
            json={"query": ""},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_with_filter(self, app_client):
        """Search with metadata filter."""
        response = app_client.post(
            "/search",
            json={
                "query": "test query",
                "filter": {"source": "test"},
            },
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_limit_validation(self, app_client):
        """Limit should be validated."""
        # Limit too high
        response = app_client.post(
            "/search",
            json={"query": "test", "limit": 1000},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Limit too low
        response = app_client.post(
            "/search",
            json={"query": "test", "limit": 0},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCollectionsEndpoint:
    """Tests for /collections endpoint."""

    def test_list_collections_success(self, app_client):
        """Successfully list collections."""
        response = app_client.get(
            "/collections",
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "collections" in data
        assert "count" in data
        assert isinstance(data["collections"], list)


class TestDocumentsEndpoint:
    """Tests for /documents/{id} endpoint."""

    def test_get_document_success(self, app_client):
        """Successfully get a document."""
        response = app_client.get(
            "/documents/test-id-1?collection_name=test-collection",
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "test-id-1"
        assert data["found"] is True
        assert "text" in data

    def test_get_document_default_collection(self, app_client):
        """Get document should use default collection if not specified."""
        response = app_client.get(
            "/documents/test-id-1",
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_name"] == "default"


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, app_client):
        """Non-existent endpoint should return 404."""
        response = app_client.get(
            "/nonexistent",
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, app_client):
        """Wrong HTTP method should return 405."""
        response = app_client.get(
            "/ingest",
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
