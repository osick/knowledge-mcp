"""Tests for EmbedderService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from openai.types import CreateEmbeddingResponse, Embedding
from openai.types.create_embedding_response import Usage
from remote_rag.services.embedder import EmbedderService, EmbeddingError


# ============================================================================
# Test: EmbedderService - Initialization
# ============================================================================

def test_embedder_initialization():
    """Test EmbedderService initializes correctly."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client:
        embedder = EmbedderService()

        assert embedder.deployment == "text-embedding-3-small"
        assert embedder.dimensions == 1536
        assert embedder.client is not None
        mock_client.assert_called_once()


# ============================================================================
# Test: embed_text - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_embed_text_success(sample_short_text, sample_embedding_vector):
    """Test successful single text embedding."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        # Setup mock response
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = CreateEmbeddingResponse(
            data=[
                Embedding(
                    embedding=sample_embedding_vector,
                    index=0,
                    object="embedding",
                )
            ],
            model="text-embedding-3-small",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()
        result = await embedder.embed_text(sample_short_text)

        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_text_with_different_dimensions():
    """Test embedding with custom dimensions."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        with patch("remote_rag.services.embedder.settings") as mock_settings:
            mock_settings.azure_openai_embedding_dimensions = 768
            mock_settings.azure_openai_api_key = "test-key"
            mock_settings.azure_openai_api_version = "2024-02-01"
            mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
            mock_settings.azure_openai_embedding_deployment = "test-deployment"

            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            embedding_768 = [0.1] * 768
            mock_response = CreateEmbeddingResponse(
                data=[Embedding(embedding=embedding_768, index=0, object="embedding")],
                model="test-model",
                object="list",
                usage=Usage(prompt_tokens=10, total_tokens=10),
            )
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)

            embedder = EmbedderService()
            result = await embedder.embed_text("Test text")

            assert len(result) == 768


@pytest.mark.asyncio
async def test_embed_text_with_special_characters(sample_embedding_vector):
    """Test embedding text with special characters."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = CreateEmbeddingResponse(
            data=[Embedding(embedding=sample_embedding_vector, index=0, object="embedding")],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()
        text = "Special chars: @#$% and émojis 🎉"
        result = await embedder.embed_text(text)

        assert len(result) == 1536


# ============================================================================
# Test: embed_text - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_embed_text_empty_string():
    """Test embedding empty string raises error."""
    embedder = EmbedderService()

    with pytest.raises(EmbeddingError, match="empty"):
        await embedder.embed_text("")


@pytest.mark.asyncio
async def test_embed_text_whitespace_only():
    """Test embedding whitespace-only text raises error."""
    embedder = EmbedderService()

    with pytest.raises(EmbeddingError, match="empty or whitespace"):
        await embedder.embed_text("   \n\t  ")


@pytest.mark.asyncio
async def test_embed_text_api_error():
    """Test handling of API errors."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.embeddings.create = AsyncMock(
            side_effect=Exception("API connection failed")
        )

        embedder = EmbedderService()

        with pytest.raises(EmbeddingError, match="Failed to generate embedding"):
            await embedder.embed_text("Test text")


@pytest.mark.asyncio
async def test_embed_text_invalid_dimensions(sample_short_text):
    """Test error when API returns wrong dimension count."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Return wrong dimension count
        wrong_vector = [0.1] * 100  # Should be 1536
        mock_response = CreateEmbeddingResponse(
            data=[Embedding(embedding=wrong_vector, index=0, object="embedding")],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()

        with pytest.raises(EmbeddingError, match="Invalid embedding dimensions"):
            await embedder.embed_text(sample_short_text)


# ============================================================================
# Test: embed_batch - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_embed_batch_success(sample_embedding_batch):
    """Test successful batch embedding."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = CreateEmbeddingResponse(
            data=[
                Embedding(embedding=sample_embedding_batch[0], index=0, object="embedding"),
                Embedding(embedding=sample_embedding_batch[1], index=1, object="embedding"),
                Embedding(embedding=sample_embedding_batch[2], index=2, object="embedding"),
            ],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=30, total_tokens=30),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()
        texts = ["Text 1", "Text 2", "Text 3"]
        results = await embedder.embed_batch(texts)

        assert isinstance(results, list)
        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch_single_text(sample_embedding_vector):
    """Test batch embedding with single text."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = CreateEmbeddingResponse(
            data=[Embedding(embedding=sample_embedding_vector, index=0, object="embedding")],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()
        results = await embedder.embed_batch(["Single text"])

        assert len(results) == 1
        assert len(results[0]) == 1536


@pytest.mark.asyncio
async def test_embed_batch_large_batch():
    """Test batch embedding with many texts."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        batch_size = 10
        embeddings = [[0.1] * 1536 for _ in range(batch_size)]
        mock_response = CreateEmbeddingResponse(
            data=[
                Embedding(embedding=emb, index=i, object="embedding")
                for i, emb in enumerate(embeddings)
            ],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=100, total_tokens=100),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()
        texts = [f"Text {i}" for i in range(batch_size)]
        results = await embedder.embed_batch(texts)

        assert len(results) == batch_size


# ============================================================================
# Test: embed_batch - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_embed_batch_empty_list():
    """Test batch embedding with empty list raises error."""
    embedder = EmbedderService()

    with pytest.raises(EmbeddingError, match="empty list"):
        await embedder.embed_batch([])


@pytest.mark.asyncio
async def test_embed_batch_with_empty_strings():
    """Test batch embedding with some empty strings raises error."""
    embedder = EmbedderService()

    with pytest.raises(EmbeddingError, match="empty"):
        await embedder.embed_batch(["Valid text", "", "Another valid"])


@pytest.mark.asyncio
async def test_embed_batch_all_whitespace():
    """Test batch embedding with all whitespace strings raises error."""
    embedder = EmbedderService()

    with pytest.raises(EmbeddingError, match="empty or whitespace"):
        await embedder.embed_batch(["  ", "\n\t", "   "])


@pytest.mark.asyncio
async def test_embed_batch_count_mismatch():
    """Test error when API returns wrong number of embeddings."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Return fewer embeddings than requested
        mock_response = CreateEmbeddingResponse(
            data=[Embedding(embedding=[0.1] * 1536, index=0, object="embedding")],
            model="test",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedder = EmbedderService()

        with pytest.raises(EmbeddingError, match="count mismatch"):
            await embedder.embed_batch(["Text 1", "Text 2", "Text 3"])


# ============================================================================
# Test: Context Manager
# ============================================================================

@pytest.mark.asyncio
async def test_context_manager():
    """Test EmbedderService as async context manager."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        async with EmbedderService() as embedder:
            assert embedder is not None
            assert embedder.client is mock_client

        # Verify close was called
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close():
    """Test manual close of embedder service."""
    with patch("remote_rag.services.embedder.AsyncAzureOpenAI") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        embedder = EmbedderService()
        await embedder.close()

        mock_client.close.assert_called_once()
