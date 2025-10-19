"""Tests for IngestClient."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from local_mcp.ingest_client import IngestClient, IngestError


@pytest.fixture
def ingest_client():
    """Create an IngestClient instance."""
    return IngestClient(
        api_url="http://localhost:8000",
        api_key="test-api-key"
    )


# ============================================================================
# Test: ingest_text - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_ingest_text_success(ingest_client):
    """Test successful text ingestion."""
    mock_response = {
        "status": "success",
        "doc_id": "abc123",
        "chunks": 5
    }

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        result = await ingest_client.ingest_text(
            text="Sample document text",
            filename="test.txt",
            collection="test-collection"
        )

        assert result["status"] == "success"
        assert result["doc_id"] == "abc123"
        assert result["chunks"] == 5

        # Verify API was called with correct parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/api/v1/ingest"
        payload = call_args[1]["json"]
        assert payload["text"] == "Sample document text"
        assert payload["metadata"]["filename"] == "test.txt"
        assert payload["metadata"]["collection"] == "test-collection"
        assert payload["metadata"]["source"] == "local"


@pytest.mark.asyncio
async def test_ingest_text_with_default_collection(ingest_client):
    """Test ingestion with default collection."""
    mock_response = {"status": "success", "doc_id": "xyz", "chunks": 3}

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        await ingest_client.ingest_text(
            text="Text content",
            filename="doc.txt"
        )

        # Should use default collection
        payload = mock_post.call_args[1]["json"]
        assert payload["metadata"]["collection"] == "default"


@pytest.mark.asyncio
async def test_ingest_text_with_additional_metadata(ingest_client):
    """Test ingestion with additional metadata."""
    mock_response = {"status": "success", "doc_id": "test", "chunks": 1}

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        await ingest_client.ingest_text(
            text="Content",
            filename="doc.txt",
            collection="test",
            page="5",
            section="introduction"
        )

        # Verify additional metadata is included
        payload = mock_post.call_args[1]["json"]
        assert payload["metadata"]["page"] == "5"
        assert payload["metadata"]["section"] == "introduction"


@pytest.mark.asyncio
async def test_ingest_text_with_long_content(ingest_client):
    """Test ingesting a document with long text content."""
    long_text = "This is a test. " * 10000  # ~160KB of text
    mock_response = {"status": "success", "doc_id": "large", "chunks": 50}

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        result = await ingest_client.ingest_text(
            text=long_text,
            filename="large.txt"
        )

        assert result["chunks"] == 50
        payload = mock_post.call_args[1]["json"]
        assert len(payload["text"]) > 100000


# ============================================================================
# Test: ingest_text - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_ingest_text_http_401_unauthorized(ingest_client):
    """Test ingestion with 401 Unauthorized error."""
    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 401
        # Make json() return the dict directly, not a coroutine
        mock_response.json = lambda: {"detail": "Invalid API key"}

        # Make raise_for_status raise the exception
        def raise_status_error():
            raise httpx.HTTPStatusError(
                "401 Unauthorized",
                request=AsyncMock(),
                response=mock_response
            )
        mock_response.raise_for_status = raise_status_error

        mock_post.return_value = mock_response

        with pytest.raises(IngestError, match="401.*Invalid API key"):
            await ingest_client.ingest_text(
                text="Sample text",
                filename="test.txt"
            )


@pytest.mark.asyncio
async def test_ingest_text_http_400_bad_request(ingest_client):
    """Test ingestion with 400 Bad Request error."""
    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid text format"}

        # Make raise_for_status raise the exception
        def raise_status_error():
            raise httpx.HTTPStatusError(
                "400 Bad Request",
                request=AsyncMock(),
                response=mock_response
            )
        mock_response.raise_for_status = raise_status_error

        mock_post.return_value = mock_response

        with pytest.raises(IngestError, match="400"):
            await ingest_client.ingest_text(
                text="",
                filename="empty.txt"
            )


@pytest.mark.asyncio
async def test_ingest_text_http_500_server_error(ingest_client):
    """Test ingestion with 500 Internal Server Error."""
    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Invalid JSON")

        # Make raise_for_status raise the exception
        def raise_status_error():
            raise httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=AsyncMock(),
                response=mock_response
            )
        mock_response.raise_for_status = raise_status_error

        mock_post.return_value = mock_response

        with pytest.raises(IngestError, match="500"):
            await ingest_client.ingest_text(
                text="Text",
                filename="test.txt"
            )


@pytest.mark.asyncio
async def test_ingest_text_network_timeout(ingest_client):
    """Test ingestion with network timeout."""
    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timeout")

        with pytest.raises(IngestError, match="Network error"):
            await ingest_client.ingest_text(
                text="Text",
                filename="test.txt"
            )


@pytest.mark.asyncio
async def test_ingest_text_connection_refused(ingest_client):
    """Test ingestion when connection is refused."""
    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(IngestError, match="Network error"):
            await ingest_client.ingest_text(
                text="Text",
                filename="test.txt"
            )


# ============================================================================
# Test: IngestClient - Initialization and Configuration
# ============================================================================

def test_ingest_client_initialization():
    """Test IngestClient initializes correctly."""
    client = IngestClient(
        api_url="https://api.example.com",
        api_key="secret-key"
    )

    assert client.api_url == "https://api.example.com"
    assert client.api_key == "secret-key"
    assert client._client is None


def test_ingest_client_trailing_slash_removal():
    """Test that trailing slash is removed from API URL."""
    client = IngestClient(
        api_url="https://api.example.com/",
        api_key="key"
    )

    assert client.api_url == "https://api.example.com"


def test_ingest_client_multiple_trailing_slashes():
    """Test removal of multiple trailing slashes."""
    client = IngestClient(
        api_url="https://api.example.com///",
        api_key="key"
    )

    # rstrip('/') removes all trailing slashes
    assert not client.api_url.endswith('/')


# ============================================================================
# Test: IngestClient - Client Management
# ============================================================================

@pytest.mark.asyncio
async def test_get_client_creates_client():
    """Test that _get_client creates a new client."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    assert ingest_client._client is None

    client = await ingest_client._get_client()

    assert client is not None
    assert isinstance(client, httpx.AsyncClient)
    assert ingest_client._client is client


@pytest.mark.asyncio
async def test_get_client_reuses_existing_client():
    """Test that _get_client reuses existing client."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    client1 = await ingest_client._get_client()
    client2 = await ingest_client._get_client()

    assert client1 is client2


@pytest.mark.asyncio
async def test_close_client():
    """Test closing the HTTP client."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    # Create client
    await ingest_client._get_client()
    assert ingest_client._client is not None

    # Close it
    await ingest_client.close()
    assert ingest_client._client is None


@pytest.mark.asyncio
async def test_close_when_no_client_exists():
    """Test closing when no client has been created."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    # Should not raise an error
    await ingest_client.close()
    assert ingest_client._client is None


# ============================================================================
# Test: IngestClient - Context Manager
# ============================================================================

@pytest.mark.asyncio
async def test_context_manager():
    """Test IngestClient as async context manager."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    async with ingest_client as client:
        assert client is ingest_client
        assert client._client is None  # Not created until first use

    # Client should be closed after context exit
    assert ingest_client._client is None


@pytest.mark.asyncio
async def test_context_manager_with_usage():
    """Test context manager with actual client usage."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "success", "doc_id": "test", "chunks": 1}
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        async with ingest_client as client:
            # Use the client
            await client.ingest_text(text="Test", filename="test.txt")
            assert client._client is not None

        # Client should be closed
        assert ingest_client._client is None


@pytest.mark.asyncio
async def test_context_manager_exception_handling():
    """Test context manager properly closes client on exception."""
    ingest_client = IngestClient("http://localhost:8000", "key")

    try:
        async with ingest_client:
            await ingest_client._get_client()
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Client should still be closed despite exception
    assert ingest_client._client is None


# ============================================================================
# Test: IngestClient - URL Construction
# ============================================================================

@pytest.mark.asyncio
async def test_correct_url_construction():
    """Test that API URLs are constructed correctly."""
    client = IngestClient("https://example.com:8443/api", "key")

    with patch.object(httpx.AsyncClient, "post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "success", "doc_id": "x", "chunks": 1}
        )
        mock_post.return_value.raise_for_status = AsyncMock()

        await client.ingest_text(text="Test", filename="test.txt")

        # Verify URL
        called_url = mock_post.call_args[0][0]
        assert called_url == "https://example.com:8443/api/api/v1/ingest"
