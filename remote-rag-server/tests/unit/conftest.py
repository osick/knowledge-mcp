"""Shared test fixtures for unit tests."""

import pytest
from typing import List


@pytest.fixture
def sample_short_text() -> str:
    """Short text sample for testing."""
    return "This is a short test document with just a few sentences. It's used for basic testing."


@pytest.fixture
def sample_medium_text() -> str:
    """Medium-length text sample for testing."""
    return """
    This is a medium-length document for testing chunking and embedding.
    It contains multiple paragraphs to test how the chunker handles different content.

    The second paragraph discusses additional topics and provides more context.
    We need enough text to create multiple chunks but not too much for unit tests.

    The third paragraph wraps up the document and provides a conclusion.
    This should be sufficient for testing purposes.
    """


@pytest.fixture
def sample_long_text() -> str:
    """Long text sample that will definitely create multiple chunks."""
    # Create a long text by repeating paragraphs
    paragraph = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute
    irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
    pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
    deserunt mollit anim id est laborum.
    """
    return "\n\n".join([f"Paragraph {i+1}:\n{paragraph}" for i in range(10)])


@pytest.fixture
def sample_empty_text() -> str:
    """Empty text for error case testing."""
    return ""


@pytest.fixture
def sample_whitespace_text() -> str:
    """Whitespace-only text for error case testing."""
    return "   \n\t  \n   "


@pytest.fixture
def sample_embedding_vector() -> List[float]:
    """Sample embedding vector with 1536 dimensions."""
    return [0.1] * 1536


@pytest.fixture
def sample_embedding_batch() -> List[List[float]]:
    """Sample batch of 3 embedding vectors."""
    return [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]


@pytest.fixture
def sample_metadata() -> dict:
    """Sample metadata for documents."""
    return {
        "filename": "test.txt",
        "collection": "test-collection",
        "source": "local",
        "page": "1",
    }


@pytest.fixture
def sample_metadata_batch() -> List[dict]:
    """Sample batch of metadata dicts."""
    return [
        {"filename": "doc1.txt", "collection": "test", "source": "local"},
        {"filename": "doc2.txt", "collection": "test", "source": "remote"},
        {"filename": "doc3.txt", "collection": "test", "source": "local"},
    ]
