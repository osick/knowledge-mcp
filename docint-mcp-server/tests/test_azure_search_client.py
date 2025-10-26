"""Tests for AzureSearchClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

from docint_mcp.azure_search_client import AzureSearchClient, AzureSearchError
from docint_mcp.models import SearchResult, Document


class TestAzureSearchClientInit:
    """Tests for AzureSearchClient initialization."""

    def test_init_with_valid_credentials(self) -> None:
        """Test initialization with valid endpoint and key."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )
        assert client.endpoint == "https://test.search.windows.net"
        assert client.credential is not None

    def test_init_with_empty_endpoint(self) -> None:
        """Test initialization fails with empty endpoint."""
        with pytest.raises(ValueError, match="endpoint cannot be empty"):
            AzureSearchClient(endpoint="", credential="test-key")

    def test_init_with_empty_credential(self) -> None:
        """Test initialization fails with empty credential."""
        with pytest.raises(ValueError, match="credential cannot be empty"):
            AzureSearchClient(
                endpoint="https://test.search.windows.net", credential=""
            )


class TestAzureSearchClientSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_success(
        self, mock_azure_search_client: AsyncMock, sample_search_results: list[dict]
    ) -> None:
        """Test successful search operation."""
        # Setup mock - search() returns an async iterator
        mock_search_client = MagicMock()

        async def mock_search_iterator():
            for result in sample_search_results:
                yield result

        mock_search_client.search.return_value = mock_search_iterator()

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            results = await client.search(
                index_name="test-index", query="machine learning", top=3
            )

            # Verify results
            assert len(results) == 3
            assert isinstance(results[0], SearchResult)
            assert results[0].document_id == "doc-1"
            assert results[0].score == 0.92
            assert "Machine learning" in results[0].content

    @pytest.mark.asyncio
    async def test_search_empty_query(self) -> None:
        """Test search with empty query raises error."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )

        with pytest.raises(ValueError, match="query cannot be empty"):
            await client.search(index_name="test-index", query="", top=5)

    @pytest.mark.asyncio
    async def test_search_empty_index(self) -> None:
        """Test search with empty index name raises error."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )

        with pytest.raises(ValueError, match="index_name cannot be empty"):
            await client.search(index_name="", query="test", top=5)

    @pytest.mark.asyncio
    async def test_search_invalid_top_value(self) -> None:
        """Test search with invalid top value raises error."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )

        with pytest.raises(ValueError, match="top must be between 1 and 50"):
            await client.search(index_name="test-index", query="test", top=0)

        with pytest.raises(ValueError, match="top must be between 1 and 50"):
            await client.search(index_name="test-index", query="test", top=100)

    @pytest.mark.asyncio
    async def test_search_no_results(self) -> None:
        """Test search that returns no results."""
        mock_search_client = MagicMock()

        async def mock_empty_iterator():
            return
            yield  # Make it a generator

        mock_search_client.search.return_value = mock_empty_iterator()

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            results = await client.search(
                index_name="test-index", query="nonexistent query", top=5
            )

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_index_not_found(self) -> None:
        """Test search with non-existent index raises error."""
        mock_search_client = MagicMock()

        async def mock_error_iterator():
            raise ResourceNotFoundError("Index not found")
            yield

        mock_search_client.search.return_value = mock_error_iterator()

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            with pytest.raises(AzureSearchError, match="Index 'test-index' not found"):
                await client.search(index_name="test-index", query="test", top=5)

    @pytest.mark.asyncio
    async def test_search_network_error(self) -> None:
        """Test search with network error raises AzureSearchError."""
        mock_search_client = MagicMock()

        async def mock_http_error_iterator():
            raise HttpResponseError("Network error")
            yield

        mock_search_client.search.return_value = mock_http_error_iterator()

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            with pytest.raises(AzureSearchError, match="Search failed"):
                await client.search(index_name="test-index", query="test", top=5)


class TestAzureSearchClientGetDocument:
    """Tests for get_document functionality."""

    @pytest.mark.asyncio
    async def test_get_document_success(self, sample_document: dict) -> None:
        """Test successful document retrieval."""
        mock_search_client = MagicMock()
        mock_search_client.get_document = AsyncMock(return_value=sample_document)

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            document = await client.get_document(
                index_name="test-index", document_id="doc-1"
            )

            assert document is not None
            assert isinstance(document, Document)
            assert document.document_id == "doc-1"
            assert "Machine learning" in document.content
            assert document.metadata["source"] == "ml-guide.pdf"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self) -> None:
        """Test get_document returns None when document not found."""
        mock_search_client = MagicMock()
        mock_search_client.get_document = AsyncMock(
            side_effect=ResourceNotFoundError("Document not found")
        )

        with patch("docint_mcp.azure_search_client.SearchClient") as mock_search_class:
            mock_search_class.return_value = mock_search_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            document = await client.get_document(
                index_name="test-index", document_id="nonexistent"
            )

            assert document is None

    @pytest.mark.asyncio
    async def test_get_document_empty_id(self) -> None:
        """Test get_document with empty document_id raises error."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )

        with pytest.raises(ValueError, match="document_id cannot be empty"):
            await client.get_document(index_name="test-index", document_id="")

    @pytest.mark.asyncio
    async def test_get_document_empty_index(self) -> None:
        """Test get_document with empty index_name raises error."""
        client = AzureSearchClient(
            endpoint="https://test.search.windows.net", credential="test-key"
        )

        with pytest.raises(ValueError, match="index_name cannot be empty"):
            await client.get_document(index_name="", document_id="doc-1")


class TestAzureSearchClientListIndexes:
    """Tests for list_indexes functionality."""

    @pytest.mark.asyncio
    async def test_list_indexes_success(self, sample_indexes: list[str]) -> None:
        """Test successful index listing."""
        mock_index_client = MagicMock()
        mock_index = MagicMock()
        mock_index.name = "default"
        mock_index2 = MagicMock()
        mock_index2.name = "technical-docs"

        async def mock_indexes_iterator():
            yield mock_index
            yield mock_index2

        mock_index_client.list_indexes.return_value = mock_indexes_iterator()

        with patch(
            "docint_mcp.azure_search_client.SearchIndexClient"
        ) as mock_index_class:
            mock_index_class.return_value = mock_index_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            indexes = await client.list_indexes()

            assert len(indexes) == 2
            assert "default" in indexes
            assert "technical-docs" in indexes

    @pytest.mark.asyncio
    async def test_list_indexes_empty(self) -> None:
        """Test list_indexes when no indexes exist."""
        mock_index_client = MagicMock()

        async def mock_empty_indexes_iterator():
            return
            yield

        mock_index_client.list_indexes.return_value = mock_empty_indexes_iterator()

        with patch(
            "docint_mcp.azure_search_client.SearchIndexClient"
        ) as mock_index_class:
            mock_index_class.return_value = mock_index_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            indexes = await client.list_indexes()

            assert len(indexes) == 0

    @pytest.mark.asyncio
    async def test_list_indexes_error(self) -> None:
        """Test list_indexes with service error raises AzureSearchError."""
        mock_index_client = MagicMock()

        async def mock_error_indexes_iterator():
            raise HttpResponseError("Service error")
            yield

        mock_index_client.list_indexes.return_value = mock_error_indexes_iterator()

        with patch(
            "docint_mcp.azure_search_client.SearchIndexClient"
        ) as mock_index_class:
            mock_index_class.return_value = mock_index_client

            client = AzureSearchClient(
                endpoint="https://test.search.windows.net", credential="test-key"
            )

            with pytest.raises(AzureSearchError, match="Failed to list indexes"):
                await client.list_indexes()
