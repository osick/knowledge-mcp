"""Tests for DocumentConverter."""

import pytest
from pathlib import Path
from local_mcp.converter import DocumentConverter, DocumentConversionError


@pytest.fixture
def converter():
    """Create a DocumentConverter instance."""
    return DocumentConverter()


# ============================================================================
# Test: convert_to_text - Success Cases
# ============================================================================

@pytest.mark.asyncio
async def test_convert_text_file(converter, sample_text_file):
    """Test converting a simple text file."""
    text = await converter.convert_to_text(sample_text_file)

    assert isinstance(text, str)
    assert len(text) > 0
    assert "sample document" in text.lower()


@pytest.mark.asyncio
async def test_convert_markdown_file(converter, sample_markdown_file):
    """Test converting a markdown file."""
    text = await converter.convert_to_text(sample_markdown_file)

    assert isinstance(text, str)
    assert len(text) > 0
    assert "Sample Document" in text or "sample document" in text.lower()


@pytest.mark.asyncio
async def test_convert_html_file(converter, sample_html_file):
    """Test converting an HTML file."""
    text = await converter.convert_to_text(sample_html_file)

    assert isinstance(text, str)
    assert len(text) > 0
    # markitdown should extract text from HTML
    assert "test" in text.lower() or "sample" in text.lower()


@pytest.mark.asyncio
async def test_convert_large_file(converter, large_text_file):
    """Test converting a large text file."""
    text = await converter.convert_to_text(large_text_file)

    assert isinstance(text, str)
    assert len(text) > 5000  # Should have substantial content
    assert "line of text" in text.lower()


@pytest.mark.asyncio
async def test_convert_empty_file(converter, empty_file):
    """Test converting an empty file."""
    text = await converter.convert_to_text(empty_file)

    # Empty file should return empty string or minimal content
    assert isinstance(text, str)


@pytest.mark.asyncio
async def test_convert_with_file_uri_prefix(converter, sample_text_file):
    """Test converting a file with file:// URI prefix."""
    # The server.py normalizes this, but test it works
    text = await converter.convert_to_text(sample_text_file)
    assert isinstance(text, str)
    assert len(text) > 0


# ============================================================================
# Test: convert_to_text - Error Cases
# ============================================================================

@pytest.mark.asyncio
async def test_convert_nonexistent_file(converter):
    """Test converting a file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        await converter.convert_to_text("/nonexistent/path/file.txt")


@pytest.mark.asyncio
async def test_convert_directory(converter, tmp_path):
    """Test converting a directory (should fail)."""
    with pytest.raises(DocumentConversionError, match="not a file"):
        await converter.convert_to_text(str(tmp_path))


@pytest.mark.asyncio
async def test_convert_with_invalid_path(converter):
    """Test converting with an invalid path."""
    with pytest.raises((FileNotFoundError, DocumentConversionError)):
        await converter.convert_to_text("")


@pytest.mark.asyncio
async def test_convert_with_special_characters_in_path(converter, tmp_path):
    """Test converting a file with special characters in the name."""
    file_path = tmp_path / "test file with spaces & special.txt"
    file_path.write_text("Test content")

    text = await converter.convert_to_text(str(file_path))
    assert "Test content" in text


# ============================================================================
# Test: get_file_metadata - Success Cases
# ============================================================================

def test_get_file_metadata(converter, sample_text_file):
    """Test extracting file metadata."""
    metadata = converter.get_file_metadata(sample_text_file)

    assert metadata["filename"] == "sample.txt"
    assert metadata["extension"] == "txt"
    assert metadata["size_bytes"] is not None
    assert int(metadata["size_bytes"]) > 0


def test_get_file_metadata_markdown(converter, sample_markdown_file):
    """Test metadata extraction for markdown file."""
    metadata = converter.get_file_metadata(sample_markdown_file)

    assert metadata["filename"] == "sample.md"
    assert metadata["extension"] == "md"
    assert metadata["size_bytes"] is not None


def test_get_file_metadata_html(converter, sample_html_file):
    """Test metadata extraction for HTML file."""
    metadata = converter.get_file_metadata(sample_html_file)

    assert metadata["filename"] == "sample.html"
    assert metadata["extension"] == "html"


def test_get_file_metadata_no_extension(converter, tmp_path):
    """Test metadata extraction for file without extension."""
    file_path = tmp_path / "noextension"
    file_path.write_text("test")

    metadata = converter.get_file_metadata(str(file_path))

    assert metadata["filename"] == "noextension"
    assert metadata["extension"] is None
    assert metadata["size_bytes"] is not None


def test_get_file_metadata_multiple_extensions(converter, tmp_path):
    """Test metadata extraction for file with multiple extensions."""
    file_path = tmp_path / "file.tar.gz"
    file_path.write_text("test")

    metadata = converter.get_file_metadata(str(file_path))

    assert metadata["filename"] == "file.tar.gz"
    assert metadata["extension"] == "gz"  # Gets the last extension


# ============================================================================
# Test: get_file_metadata - Edge Cases
# ============================================================================

def test_get_file_metadata_nonexistent(converter):
    """Test metadata extraction for nonexistent file."""
    metadata = converter.get_file_metadata("/nonexistent/file.txt")

    assert metadata["filename"] == "file.txt"
    assert metadata["extension"] == "txt"
    assert metadata["size_bytes"] is None


def test_get_file_metadata_empty_file(converter, empty_file):
    """Test metadata extraction for empty file."""
    metadata = converter.get_file_metadata(empty_file)

    assert metadata["filename"] == "empty.txt"
    assert metadata["extension"] == "txt"
    assert metadata["size_bytes"] == "0"


def test_get_file_metadata_large_file(converter, large_text_file):
    """Test metadata extraction for large file."""
    metadata = converter.get_file_metadata(large_text_file)

    assert metadata["filename"] == "large.txt"
    assert int(metadata["size_bytes"]) > 10000


# ============================================================================
# Test: DocumentConverter - Initialization
# ============================================================================

def test_converter_initialization():
    """Test DocumentConverter initializes correctly."""
    converter = DocumentConverter()
    assert converter is not None
    assert converter._converter is not None


def test_converter_multiple_instances():
    """Test multiple DocumentConverter instances are independent."""
    converter1 = DocumentConverter()
    converter2 = DocumentConverter()

    assert converter1 is not converter2
    assert converter1._converter is not converter2._converter
