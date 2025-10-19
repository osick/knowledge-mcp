"""FastAPI application with RAG endpoints."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from markitdown import MarkItDown

from remote_rag.api.auth import api_key_middleware
from remote_rag.api.logging import get_logger, log_error, log_request, log_response, setup_logging
from remote_rag.api.models import (
    ChunkInfo,
    CollectionsResponse,
    DocumentResponse,
    ErrorResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    IngestURLRequest,
    IngestURLResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from remote_rag.config import settings
from remote_rag.services.chunker import ChunkerService, ChunkingError
from remote_rag.services.embedder import EmbedderService, EmbeddingError
from remote_rag.services.qdrant import QdrantError, QdrantService

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Global service instances
chunker: ChunkerService
embedder: EmbedderService
qdrant: QdrantService
markitdown: MarkItDown


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown."""
    global chunker, embedder, qdrant, markitdown

    # Startup
    logger.info("Starting up Remote RAG API server")
    chunker = ChunkerService()
    embedder = EmbedderService()
    qdrant = QdrantService()
    markitdown = MarkItDown()
    logger.info("Services initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Remote RAG API server")
    await embedder.close()
    await qdrant.close()
    logger.info("Services closed successfully")


# Create FastAPI app
app = FastAPI(
    title="Remote RAG API",
    description="REST API for document ingestion and semantic search using Qdrant and Azure OpenAI",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Log all requests and responses."""
    start_time = time.time()

    # Log request
    log_request(
        logger,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration_ms = (time.time() - start_time) * 1000
    log_response(
        logger,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response


# Add authentication middleware
app.middleware("http")(api_key_middleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error="HTTPException",
            message=exc.detail,
            details=None,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    # Let HTTPException be handled by its specific handler
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    log_error(
        logger,
        exc,
        {"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error=type(exc).__name__,
            message="Internal server error",
            details={"error": str(exc)},
        ).model_dump(),
    )


# Health check endpoint (no authentication required)
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    services: dict[str, str] = {}

    # Check Qdrant
    try:
        await qdrant.list_collections()
        services["qdrant"] = "healthy"
    except Exception as e:
        services["qdrant"] = f"unhealthy: {str(e)}"

    # Check embedder (just verify it's initialized)
    services["embedder"] = "healthy" if embedder else "unhealthy"

    # Check chunker (just verify it's initialized)
    services["chunker"] = "healthy" if chunker else "unhealthy"

    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        services=services,
    )


# Ingest endpoint
@app.post("/ingest", response_model=IngestResponse)
async def ingest_text(request: IngestRequest) -> IngestResponse:
    """
    Ingest text content for semantic search.

    Chunks the text, generates embeddings, and stores in Qdrant.
    """
    try:
        collection = request.collection_name or settings.qdrant_default_collection

        # Chunk the text
        chunks = chunker.chunk_text(request.text)
        logger.info("Text chunked", chunks_count=len(chunks), collection=collection)

        # Generate embeddings for all chunks
        embeddings = await embedder.embed_batch(chunks)
        logger.info("Embeddings generated", count=len(embeddings))

        # Prepare metadata for each chunk
        base_metadata = request.metadata or {}
        metadata_list = [
            {
                **base_metadata,
                "text": chunk,
                "chunk_index": idx,
                "total_chunks": len(chunks),
            }
            for idx, chunk in enumerate(chunks)
        ]

        # Store in Qdrant
        chunk_ids = await qdrant.upsert_points(collection, embeddings, metadata_list)
        logger.info("Chunks stored in Qdrant", collection=collection, count=len(chunk_ids))

        # Build chunk info
        chunk_info = [
            ChunkInfo(chunk_index=idx, chunk_text=chunk, chunk_id=chunk_id)
            for idx, (chunk, chunk_id) in enumerate(zip(chunks, chunk_ids))
        ]

        return IngestResponse(
            success=True,
            message=f"Successfully ingested {len(chunks)} chunks",
            collection_name=collection,
            chunks_created=len(chunks),
            chunk_ids=chunk_ids,
            chunks=chunk_info,
        )

    except ChunkingError as e:
        logger.error("Chunking failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunking error: {str(e)}",
        )
    except EmbeddingError as e:
        logger.error("Embedding generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding error: {str(e)}",
        )
    except QdrantError as e:
        logger.error("Qdrant operation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector database error: {str(e)}",
        )


# Ingest URL endpoint
@app.post("/ingest_url", response_model=IngestURLResponse)
async def ingest_url(request: IngestURLRequest) -> IngestURLResponse:
    """
    Ingest document from HTTPS URL.

    Fetches the document, converts to text, chunks, embeds, and stores in Qdrant.
    """
    try:
        url_str = str(request.url)
        collection = request.collection_name or settings.qdrant_default_collection

        # Fetch document from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url_str)
            response.raise_for_status()

        logger.info("Document fetched from URL", url=url_str, size=len(response.content))

        # Convert to text using markitdown
        # Save to temp file (markitdown requires file path)
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        try:
            result = markitdown.convert(tmp_path)
            text = result.text_content
        finally:
            os.unlink(tmp_path)

        logger.info("Document converted to text", length=len(text))

        # Chunk the text
        chunks = chunker.chunk_text(text)
        logger.info("Text chunked", chunks_count=len(chunks))

        # Generate embeddings
        embeddings = await embedder.embed_batch(chunks)

        # Prepare metadata
        base_metadata = request.metadata or {}
        metadata_list = [
            {
                **base_metadata,
                "text": chunk,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "source_url": url_str,
            }
            for idx, chunk in enumerate(chunks)
        ]

        # Store in Qdrant
        chunk_ids = await qdrant.upsert_points(collection, embeddings, metadata_list)
        logger.info("Chunks stored in Qdrant", collection=collection, count=len(chunk_ids))

        return IngestURLResponse(
            success=True,
            message=f"Successfully ingested document from {url_str}",
            url=url_str,
            collection_name=collection,
            chunks_created=len(chunks),
            chunk_ids=chunk_ids,
            document_length=len(text),
        )

    except httpx.HTTPError as e:
        logger.error("HTTP fetch failed", error=str(e), url=url_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch URL: {str(e)}",
        )
    except ChunkingError as e:
        logger.error("Chunking failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunking error: {str(e)}",
        )
    except EmbeddingError as e:
        logger.error("Embedding generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding error: {str(e)}",
        )
    except QdrantError as e:
        logger.error("Qdrant operation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector database error: {str(e)}",
        )


# Search endpoint
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Semantic search across ingested documents.

    Generates embedding for query and searches Qdrant for similar chunks.
    """
    try:
        collection = request.collection_name or settings.qdrant_default_collection

        # Generate embedding for query
        query_embedding = await embedder.embed_text(request.query)
        logger.info("Query embedded", collection=collection)

        # Search in Qdrant
        results = await qdrant.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_conditions=request.filter,
        )
        logger.info("Search completed", collection=collection, results_count=len(results))

        # Format results
        search_results = [
            SearchResult(
                id=result["id"],
                score=result["score"],
                text=result["payload"].get("text", ""),
                metadata={k: v for k, v in result["payload"].items() if k != "text"},
            )
            for result in results
        ]

        return SearchResponse(
            success=True,
            query=request.query,
            collection_name=collection,
            results=search_results,
            count=len(search_results),
        )

    except EmbeddingError as e:
        logger.error("Query embedding failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding error: {str(e)}",
        )
    except QdrantError as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}",
        )


# List collections endpoint
@app.get("/collections", response_model=CollectionsResponse)
async def list_collections() -> CollectionsResponse:
    """List all Qdrant collections."""
    try:
        collections = await qdrant.list_collections()
        logger.info("Collections listed", count=len(collections))

        return CollectionsResponse(
            success=True,
            collections=collections,
            count=len(collections),
        )

    except QdrantError as e:
        logger.error("Failed to list collections", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}",
        )


# Get document endpoint
@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    collection_name: str = settings.qdrant_default_collection,
) -> DocumentResponse:
    """Get a specific document by ID."""
    try:
        document = await qdrant.get_document(collection_name, document_id)
        logger.info(
            "Document retrieved",
            document_id=document_id,
            collection=collection_name,
            found=document is not None,
        )

        if document is None:
            return DocumentResponse(
                success=True,
                document_id=document_id,
                collection_name=collection_name,
                text=None,
                metadata=None,
                found=False,
            )

        return DocumentResponse(
            success=True,
            document_id=document_id,
            collection_name=collection_name,
            text=document.get("text"),
            metadata={k: v for k, v in document.items() if k != "text"},
            found=True,
        )

    except QdrantError as e:
        logger.error("Failed to get document", error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}",
        )
