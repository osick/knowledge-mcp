"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("This is a sample document for testing.")
    return str(file_path)


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file for testing."""
    file_path = tmp_path / "sample.md"
    content = """# Sample Document

This is a sample markdown document for testing.

## Section 1
Some content here.

## Section 2
More content here.
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_html_file(tmp_path):
    """Create a sample HTML file for testing."""
    file_path = tmp_path / "sample.html"
    content = """<!DOCTYPE html>
<html>
<head><title>Test Document</title></head>
<body>
    <h1>Sample HTML Document</h1>
    <p>This is a test paragraph.</p>
</body>
</html>
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def large_text_file(tmp_path):
    """Create a large text file for testing."""
    file_path = tmp_path / "large.txt"
    # Create a file with ~10KB of text
    content = "This is a line of text.\n" * 500
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def empty_file(tmp_path):
    """Create an empty file for testing."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")
    return str(file_path)
