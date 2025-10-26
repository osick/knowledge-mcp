"""Data models for Document Intelligence MCP Server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """Single search result from Azure AI Search."""

    document_id: str
    score: float
    content: str
    metadata: dict[str, Any]

    def __repr__(self) -> str:
        """String representation of search result."""
        content_preview = (
            self.content[:100] + "..." if len(self.content) > 100 else self.content
        )
        return (
            f"SearchResult(id={self.document_id}, "
            f"score={self.score:.2f}, "
            f"content='{content_preview}')"
        )


@dataclass
class SearchResponse:
    """Complete search response with multiple results."""

    query: str
    results: list[SearchResult]
    total_count: int
    index_name: str

    def __repr__(self) -> str:
        """String representation of search response."""
        return (
            f"SearchResponse(query='{self.query}', "
            f"total={self.total_count}, "
            f"index='{self.index_name}')"
        )


@dataclass
class Document:
    """Retrieved document from Azure AI Search."""

    document_id: str
    content: str
    metadata: dict[str, Any]
    index_name: str

    def __repr__(self) -> str:
        """String representation of document."""
        content_preview = (
            self.content[:100] + "..." if len(self.content) > 100 else self.content
        )
        return (
            f"Document(id={self.document_id}, "
            f"index='{self.index_name}', "
            f"content='{content_preview}')"
        )
