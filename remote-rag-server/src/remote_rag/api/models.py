"""Pydantic models for API requests and responses."""

from typing import Any

from pydantic import BaseModel, Field, HttpUrl

# Request Models


class IngestRequest(BaseModel):
    """Request model for text ingestion."""

    text: str = Field(..., description="Text content to ingest", min_length=1)
    collection_name: str | None = Field(
        None, description="Collection name (defaults to 'default')"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata to attach to the document"
    )


class IngestURLRequest(BaseModel):
    """Request model for URL-based document ingestion."""

    url: HttpUrl = Field(..., description="HTTPS URL of the document to ingest")
    collection_name: str | None = Field(
        None, description="Collection name (defaults to 'default')"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata to attach to the document"
    )


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query text", min_length=1)
    collection_name: str | None = Field(
        None, description="Collection name (defaults to 'default')"
    )
    limit: int = Field(5, description="Maximum number of results", ge=1, le=100)
    score_threshold: float = Field(
        0.0, description="Minimum similarity score (0.0 to 1.0)", ge=0.0, le=1.0
    )
    filter: dict[str, Any] | None = Field(
        None, description="Optional metadata filters"
    )


# Response Models


class ChunkInfo(BaseModel):
    """Information about a single chunk."""

    chunk_index: int = Field(..., description="Index of the chunk in the document")
    chunk_text: str = Field(..., description="Text content of the chunk")
    chunk_id: str = Field(..., description="Unique ID of the chunk in Qdrant")


class IngestResponse(BaseModel):
    """Response model for text ingestion."""

    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Status message")
    collection_name: str = Field(..., description="Collection where data was stored")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunk_ids: list[str] = Field(..., description="IDs of created chunks in Qdrant")
    chunks: list[ChunkInfo] | None = Field(
        None, description="Detailed chunk information"
    )


class IngestURLResponse(BaseModel):
    """Response model for URL-based ingestion."""

    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Status message")
    url: str = Field(..., description="URL that was processed")
    collection_name: str = Field(..., description="Collection where data was stored")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunk_ids: list[str] = Field(..., description="IDs of created chunks in Qdrant")
    document_length: int = Field(..., description="Length of converted document text")


class SearchResult(BaseModel):
    """Single search result."""

    id: str = Field(..., description="Document/chunk ID")
    score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    text: str = Field(..., description="Text content of the chunk")
    metadata: dict[str, Any] = Field(..., description="Attached metadata")


class SearchResponse(BaseModel):
    """Response model for semantic search."""

    success: bool = Field(..., description="Whether search was successful")
    query: str = Field(..., description="Original query text")
    collection_name: str = Field(..., description="Collection that was searched")
    results: list[SearchResult] = Field(..., description="List of search results")
    count: int = Field(..., description="Number of results returned")


class CollectionInfo(BaseModel):
    """Information about a collection."""

    name: str = Field(..., description="Collection name")


class CollectionsResponse(BaseModel):
    """Response model for listing collections."""

    success: bool = Field(..., description="Whether operation was successful")
    collections: list[str] = Field(..., description="List of collection names")
    count: int = Field(..., description="Number of collections")


class DocumentResponse(BaseModel):
    """Response model for getting a specific document."""

    success: bool = Field(..., description="Whether retrieval was successful")
    document_id: str = Field(..., description="Document ID")
    collection_name: str = Field(..., description="Collection name")
    text: str | None = Field(None, description="Document text content")
    metadata: dict[str, Any] | None = Field(None, description="Document metadata")
    found: bool = Field(..., description="Whether document was found")


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    services: dict[str, str] = Field(..., description="Status of dependent services")
