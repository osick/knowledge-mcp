"""Tests for ChunkerService."""

import pytest
from remote_rag.services.chunker import ChunkerService, ChunkingError


# ============================================================================
# Test: ChunkerService - Initialization
# ============================================================================

def test_chunker_initialization_default():
    """Test ChunkerService initializes with default settings."""
    chunker = ChunkerService()

    assert chunker.chunk_size == 512  # Default from settings
    assert chunker.chunk_overlap == 50  # Default from settings
    assert chunker.splitter is not None


def test_chunker_initialization_custom():
    """Test ChunkerService initializes with custom parameters."""
    chunker = ChunkerService(chunk_size=1000, chunk_overlap=100)

    assert chunker.chunk_size == 1000
    assert chunker.chunk_overlap == 100


def test_chunker_initialization_partial_custom():
    """Test ChunkerService with only chunk_size customized."""
    chunker = ChunkerService(chunk_size=800)

    assert chunker.chunk_size == 800
    assert chunker.chunk_overlap == 50  # Default


# ============================================================================
# Test: chunk_text - Success Cases
# ============================================================================

def test_chunk_text_short_document(sample_short_text):
    """Test chunking a short document that fits in one chunk."""
    chunker = ChunkerService()

    chunks = chunker.chunk_text(sample_short_text)

    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(chunk.strip() for chunk in chunks)  # No empty chunks


def test_chunk_text_medium_document(sample_medium_text):
    """Test chunking a medium-length document."""
    chunker = ChunkerService()

    chunks = chunker.chunk_text(sample_medium_text)

    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    # Verify all chunks are within size limit
    assert all(len(chunk) <= chunker.chunk_size + 100 for chunk in chunks)  # Small buffer


def test_chunk_text_long_document(sample_long_text):
    """Test chunking a long document that creates multiple chunks."""
    chunker = ChunkerService(chunk_size=512, chunk_overlap=50)

    chunks = chunker.chunk_text(sample_long_text)

    assert isinstance(chunks, list)
    assert len(chunks) > 1  # Long text should create multiple chunks
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_text_with_small_chunk_size():
    """Test chunking with very small chunk size."""
    text = "This is a test document with multiple sentences. Each sentence provides information."
    chunker = ChunkerService(chunk_size=50, chunk_overlap=10)

    chunks = chunker.chunk_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)  # Small buffer for overlap


def test_chunk_text_with_large_chunk_size():
    """Test chunking with very large chunk size."""
    text = "Short document."
    chunker = ChunkerService(chunk_size=10000, chunk_overlap=0)

    chunks = chunker.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_preserves_content(sample_medium_text):
    """Test that chunking preserves all content (no data loss)."""
    chunker = ChunkerService(chunk_size=200, chunk_overlap=20)

    chunks = chunker.chunk_text(sample_medium_text)

    # Join chunks and verify key phrases are present
    joined = " ".join(chunks)
    assert "medium-length document" in joined
    assert "second paragraph" in joined
    assert "third paragraph" in joined


def test_chunk_text_with_special_characters():
    """Test chunking text with special characters."""
    text = "Document with special chars: @#$%^&*(). Also émojis 🎉 and ñoño."
    chunker = ChunkerService()

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1
    assert "@#$%^&*()" in " ".join(chunks)


def test_chunk_text_with_newlines_and_whitespace():
    """Test chunking handles newlines and whitespace correctly."""
    text = "Line 1\n\nLine 2\n\n\nLine 3\t\tTab separated"
    chunker = ChunkerService()

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1
    joined = " ".join(chunks)
    assert "Line 1" in joined
    assert "Line 3" in joined


# ============================================================================
# Test: chunk_text - Error Cases
# ============================================================================

def test_chunk_text_empty_string(sample_empty_text):
    """Test chunking empty string raises error."""
    chunker = ChunkerService()

    with pytest.raises(ChunkingError, match="empty"):
        chunker.chunk_text(sample_empty_text)


def test_chunk_text_whitespace_only(sample_whitespace_text):
    """Test chunking whitespace-only text raises error."""
    chunker = ChunkerService()

    with pytest.raises(ChunkingError, match="empty or whitespace"):
        chunker.chunk_text(sample_whitespace_text)


def test_chunk_text_none_input():
    """Test chunking None input raises appropriate error."""
    chunker = ChunkerService()

    with pytest.raises((ChunkingError, AttributeError)):
        chunker.chunk_text(None)  # type: ignore


# ============================================================================
# Test: get_chunk_count
# ============================================================================

def test_get_chunk_count_short_text(sample_short_text):
    """Test getting chunk count for short text."""
    chunker = ChunkerService()

    count = chunker.get_chunk_count(sample_short_text)

    assert isinstance(count, int)
    assert count >= 1


def test_get_chunk_count_long_text(sample_long_text):
    """Test getting chunk count for long text."""
    chunker = ChunkerService(chunk_size=512)

    count = chunker.get_chunk_count(sample_long_text)

    assert isinstance(count, int)
    assert count > 1


def test_get_chunk_count_empty_text(sample_empty_text):
    """Test get_chunk_count returns 0 for empty text."""
    chunker = ChunkerService()

    count = chunker.get_chunk_count(sample_empty_text)

    assert count == 0


def test_get_chunk_count_matches_chunk_text(sample_medium_text):
    """Test that get_chunk_count matches actual chunk_text result."""
    chunker = ChunkerService()

    count = chunker.get_chunk_count(sample_medium_text)
    chunks = chunker.chunk_text(sample_medium_text)

    assert count == len(chunks)


# ============================================================================
# Test: ChunkerService - Edge Cases
# ============================================================================

def test_chunk_text_single_character():
    """Test chunking single character."""
    chunker = ChunkerService()

    chunks = chunker.chunk_text("A")

    assert len(chunks) == 1
    assert chunks[0] == "A"


def test_chunk_text_exact_chunk_size():
    """Test text that is exactly chunk_size length."""
    chunker = ChunkerService(chunk_size=50, chunk_overlap=10)
    text = "a" * 50

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1


def test_chunk_text_unicode():
    """Test chunking with various Unicode characters."""
    text = "Hello 世界! Привет мир! مرحبا بالعالم! 🌍🌎🌏"
    chunker = ChunkerService()

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1
    joined = " ".join(chunks)
    assert "世界" in joined
    assert "Привет" in joined


def test_chunker_multiple_instances():
    """Test that multiple ChunkerService instances work independently."""
    chunker1 = ChunkerService(chunk_size=100)
    chunker2 = ChunkerService(chunk_size=500)

    assert chunker1.chunk_size == 100
    assert chunker2.chunk_size == 500

    text = "Test document " * 100

    chunks1 = chunker1.chunk_text(text)
    chunks2 = chunker2.chunk_text(text)

    # Different chunk sizes should produce different chunk counts
    assert len(chunks1) >= len(chunks2)
