"""Document converter using markitdown library."""

import os
from pathlib import Path
from typing import Optional

from markitdown import MarkItDown


class DocumentConversionError(Exception):
    """Raised when document conversion fails."""
    pass


class DocumentConverter:
    """Converts various document formats to text using markitdown."""

    def __init__(self) -> None:
        """Initialize the document converter."""
        self._converter = MarkItDown()

    async def convert_to_text(self, file_path: str) -> str:
        """
        Convert a document to text.

        Args:
            file_path: Path to the document file (must be a local file path)

        Returns:
            Converted text content

        Raises:
            DocumentConversionError: If conversion fails
            FileNotFoundError: If file doesn't exist
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise DocumentConversionError(f"Path is not a file: {file_path}")

        # Convert document
        try:
            result = self._converter.convert(str(path))
            return result.text_content
        except Exception as e:
            raise DocumentConversionError(
                f"Failed to convert document {file_path}: {str(e)}"
            ) from e

    def get_file_metadata(self, file_path: str) -> dict[str, Optional[str]]:
        """
        Extract metadata from file path.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing filename and other metadata
        """
        path = Path(file_path)
        return {
            "filename": path.name,
            "extension": path.suffix.lstrip(".") if path.suffix else None,
            "size_bytes": str(path.stat().st_size) if path.exists() else None,
        }
