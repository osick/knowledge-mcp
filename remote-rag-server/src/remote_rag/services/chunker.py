"""Document chunking service using LangChain RecursiveCharacterTextSplitter."""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from remote_rag.config import settings


class ChunkingError(Exception):
    """Raised when document chunking fails."""

    pass


class ChunkerService:
    """Service for splitting documents into chunks for embedding and retrieval."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """
        Initialize the chunker service.

        Args:
            chunk_size: Maximum chunk size in characters (defaults to settings.chunk_size)
            chunk_overlap: Overlap between chunks (defaults to settings.chunk_overlap)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Initialize LangChain RecursiveCharacterTextSplitter
        # This splitter tries to keep paragraphs, sentences, and words together
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: The text content to chunk

        Returns:
            List of text chunks

        Raises:
            ChunkingError: If chunking fails
        """
        if not text or not text.strip():
            raise ChunkingError("Cannot chunk empty or whitespace-only text")

        try:
            chunks = self.splitter.split_text(text)

            # Filter out empty chunks (edge case handling)
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

            if not chunks:
                raise ChunkingError("Chunking produced no valid chunks")

            return chunks

        except Exception as e:
            if isinstance(e, ChunkingError):
                raise
            raise ChunkingError(f"Failed to chunk text: {str(e)}") from e

    def get_chunk_count(self, text: str) -> int:
        """
        Get the number of chunks that would be created from the text.

        Args:
            text: The text content to analyze

        Returns:
            Number of chunks that would be created
        """
        try:
            chunks = self.chunk_text(text)
            return len(chunks)
        except ChunkingError:
            return 0
