"""Tests for QdrantService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qdrant_client.models import (
    CollectionsResponse,
    CollectionDescription,
    Distance,
    ScoredPoint,
    Record,
)
from remote_rag.services.qdrant import QdrantService, QdrantError


# ============================================================================
# Test: QdrantService - Initialization
# ============================================================================

def test_qdrant_initialization():
    """Test QdrantService initializes correctly."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client:
        service = QdrantService()

        assert service.vector_size == 1536
        assert service.client is not None
        mock_client.assert_called_once()


# ============================================================================
# Test: create_collection - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_create_collection_success():
    """Test successful collection creation."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock get_collections to return empty list (collection doesn't exist)
        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )
        mock_client.create_collection = AsyncMock()

        service = QdrantService()
        await service.create_collection("test-collection")

        mock_client.create_collection.assert_called_once()
        call_kwargs = mock_client.create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "test-collection"


@pytest.mark.asyncio
async def test_create_collection_already_exists():
    """Test creating collection that already exists (should not error)."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock collection already exists
        existing_collection = CollectionDescription(name="test-collection")
        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[existing_collection])
        )
        mock_client.create_collection = AsyncMock()

        service = QdrantService()
        await service.create_collection("test-collection")

        # Should NOT call create_collection since it exists
        mock_client.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_create_collection_with_distance_metric():
    """Test creating collection with custom distance metric."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )
        mock_client.create_collection = AsyncMock()

        service = QdrantService()
        await service.create_collection("test-collection", distance=Distance.EUCLID)

        call_kwargs = mock_client.create_collection.call_args[1]
        vectors_config = call_kwargs["vectors_config"]
        assert vectors_config.distance == Distance.EUCLID


# ============================================================================
# Test: create_collection - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_create_collection_api_error():
    """Test error handling when collection creation fails."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(side_effect=Exception("Connection failed"))

        service = QdrantService()

        with pytest.raises(QdrantError, match="Failed to create collection"):
            await service.create_collection("test-collection")


# ============================================================================
# Test: upsert_points - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_upsert_points_success(sample_embedding_batch, sample_metadata_batch):
    """Test successful point upsert."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock()

        service = QdrantService()
        point_ids = await service.upsert_points(
            "test-collection",
            sample_embedding_batch,
            sample_metadata_batch,
        )

        assert isinstance(point_ids, list)
        assert len(point_ids) == 3
        assert all(isinstance(pid, str) for pid in point_ids)
        mock_client.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_points_single(sample_embedding_vector, sample_metadata):
    """Test upserting a single point."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock()

        service = QdrantService()
        point_ids = await service.upsert_points(
            "test-collection",
            [sample_embedding_vector],
            [sample_metadata],
        )

        assert len(point_ids) == 1


# ============================================================================
# Test: upsert_points - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_upsert_points_count_mismatch():
    """Test error when embeddings and metadata counts don't match."""
    service = QdrantService()

    with pytest.raises(QdrantError, match="count mismatch"):
        await service.upsert_points(
            "test-collection",
            [[0.1] * 1536, [0.2] * 1536],  # 2 embeddings
            [{"key": "value"}],  # 1 metadata
        )


@pytest.mark.asyncio
async def test_upsert_points_empty_list():
    """Test error when upserting empty list."""
    service = QdrantService()

    with pytest.raises(QdrantError, match="empty list"):
        await service.upsert_points("test-collection", [], [])


@pytest.mark.asyncio
async def test_upsert_points_api_error():
    """Test error handling when upsert fails."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock(side_effect=Exception("Upsert failed"))

        service = QdrantService()

        with pytest.raises(QdrantError, match="Failed to upsert points"):
            await service.upsert_points(
                "test-collection",
                [[0.1] * 1536],
                [{"key": "value"}],
            )


# ============================================================================
# Test: search - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_search_success(sample_embedding_vector):
    """Test successful semantic search."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock search results
        mock_results = [
            ScoredPoint(
                id="point-1",
                version=1,
                score=0.95,
                payload={"text": "Result 1", "filename": "doc1.txt"},
                vector=None,
            ),
            ScoredPoint(
                id="point-2",
                version=1,
                score=0.85,
                payload={"text": "Result 2", "filename": "doc2.txt"},
                vector=None,
            ),
        ]
        mock_client.search = AsyncMock(return_value=mock_results)

        service = QdrantService()
        results = await service.search(
            "test-collection",
            sample_embedding_vector,
            limit=2,
        )

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["id"] == "point-1"
        assert results[0]["score"] == 0.95
        assert "text" in results[0]["payload"]


@pytest.mark.asyncio
async def test_search_with_score_threshold(sample_embedding_vector):
    """Test search with score threshold."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_results = [
            ScoredPoint(id="p1", version=1, score=0.95, payload={"text": "High score"}, vector=None),
        ]
        mock_client.search = AsyncMock(return_value=mock_results)

        service = QdrantService()
        results = await service.search(
            "test-collection",
            sample_embedding_vector,
            limit=5,
            score_threshold=0.9,
        )

        # Verify score_threshold was passed
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["score_threshold"] == 0.9


@pytest.mark.asyncio
async def test_search_with_filter(sample_embedding_vector):
    """Test search with metadata filters."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_results = []
        mock_client.search = AsyncMock(return_value=mock_results)

        service = QdrantService()
        results = await service.search(
            "test-collection",
            sample_embedding_vector,
            filter_conditions={"collection": "specific-collection"},
        )

        # Verify filter was constructed
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["query_filter"] is not None


@pytest.mark.asyncio
async def test_search_no_results(sample_embedding_vector):
    """Test search that returns no results."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.search = AsyncMock(return_value=[])

        service = QdrantService()
        results = await service.search("test-collection", sample_embedding_vector)

        assert results == []


# ============================================================================
# Test: search - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_search_api_error(sample_embedding_vector):
    """Test error handling when search fails."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.search = AsyncMock(side_effect=Exception("Search failed"))

        service = QdrantService()

        with pytest.raises(QdrantError, match="Failed to search"):
            await service.search("test-collection", sample_embedding_vector)


# ============================================================================
# Test: get_document - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_get_document_success():
    """Test successful document retrieval."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_record = Record(
            id="doc-123",
            payload={"text": "Document content", "filename": "test.txt"},
            vector=None,
        )
        mock_client.retrieve = AsyncMock(return_value=[mock_record])

        service = QdrantService()
        result = await service.get_document("test-collection", "doc-123")

        assert result is not None
        assert result["text"] == "Document content"
        assert result["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_get_document_not_found():
    """Test getting document that doesn't exist."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.retrieve = AsyncMock(return_value=[])

        service = QdrantService()
        result = await service.get_document("test-collection", "nonexistent-id")

        assert result is None


# ============================================================================
# Test: list_collections - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_list_collections_success():
    """Test successful collection listing."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_collections = [
            CollectionDescription(name="collection1"),
            CollectionDescription(name="collection2"),
            CollectionDescription(name="collection3"),
        ]
        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=mock_collections)
        )

        service = QdrantService()
        collections = await service.list_collections()

        assert isinstance(collections, list)
        assert len(collections) == 3
        assert "collection1" in collections
        assert "collection2" in collections
        assert "collection3" in collections


@pytest.mark.asyncio
async def test_list_collections_empty():
    """Test listing when no collections exist."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_collections = AsyncMock(
            return_value=CollectionsResponse(collections=[])
        )

        service = QdrantService()
        collections = await service.list_collections()

        assert collections == []


# ============================================================================
# Test: delete_collection - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_delete_collection_success():
    """Test successful collection deletion."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.delete_collection = AsyncMock()

        service = QdrantService()
        await service.delete_collection("test-collection")

        mock_client.delete_collection.assert_called_once_with(
            collection_name="test-collection"
        )


@pytest.mark.asyncio
async def test_delete_collection_error():
    """Test error handling when deletion fails."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.delete_collection = AsyncMock(side_effect=Exception("Delete failed"))

        service = QdrantService()

        with pytest.raises(QdrantError, match="Failed to delete collection"):
            await service.delete_collection("test-collection")


# ============================================================================
# Test: Context Manager
# ============================================================================

@pytest.mark.asyncio
async def test_context_manager():
    """Test QdrantService as async context manager."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        async with QdrantService() as service:
            assert service is not None
            assert service.client is mock_client

        # Verify close was called
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close():
    """Test manual close of Qdrant service."""
    with patch("remote_rag.services.qdrant.AsyncQdrantClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        service = QdrantService()
        await service.close()

        mock_client.close.assert_called_once()
