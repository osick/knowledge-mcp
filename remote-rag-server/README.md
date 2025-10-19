# Remote RAG Server

A production-ready REST API for document ingestion and semantic search using Qdrant vector database and Azure OpenAI embeddings.

## Overview

The Remote RAG Server provides HTTP endpoints for:
- Text and document ingestion with automatic chunking
- URL-based document ingestion
- Semantic search across stored documents
- Collection management
- Document retrieval

Built with FastAPI, the server features async operations, structured logging, API key authentication, and comprehensive error handling.

## Architecture

### Components

1. **API Layer** (`src/remote_rag/api/`)
   - FastAPI application with 6 REST endpoints
   - API key authentication middleware
   - Structured logging with structlog
   - Pydantic models for request/response validation

2. **Service Layer** (`src/remote_rag/services/`)
   - **ChunkerService**: Text chunking using LangChain RecursiveCharacterTextSplitter
   - **EmbedderService**: Embedding generation via Azure OpenAI
   - **QdrantService**: Vector database operations

3. **Configuration** (`src/remote_rag/config.py`)
   - Environment-based configuration using pydantic-settings
   - All settings configurable via environment variables

### Technology Stack

- **Python**: 3.11+
- **Web Framework**: FastAPI 0.119.0+
- **Vector Database**: Qdrant 1.15.0+
- **Embeddings**: Azure OpenAI (text-embedding-3-small, 1536 dimensions)
- **Text Processing**: LangChain 1.0.0+
- **Document Conversion**: markitdown 0.1.3+
- **Logging**: structlog 24.0.0+
- **Testing**: pytest 8.0.0+ with 89% code coverage

## Installation

### Prerequisites

- Python 3.11 or higher
- Access to Azure OpenAI API
- Qdrant instance (local or cloud)

### Setup

1. Install dependencies using uv (recommended):

```bash
cd remote-rag-server
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

2. Create environment configuration:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Configure environment variables (see Configuration section)

## Configuration

All configuration is managed through environment variables or a `.env` file.

### Required Configuration

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_DEFAULT_COLLECTION=default

# API Configuration
API_KEY=your-secure-api-key
API_HOST=0.0.0.0
API_PORT=8000

# Chunking Configuration (optional, defaults shown)
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Logging Configuration (optional, defaults shown)
LOG_LEVEL=INFO
LOG_FORMAT=json  # or "console" for development
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Required |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment name for embeddings | `text-embedding-3-small` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-01` |
| `AZURE_OPENAI_EMBEDDING_DIMENSIONS` | Embedding dimensions | `1536` |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key | Required |
| `QDRANT_DEFAULT_COLLECTION` | Default collection name | `default` |
| `API_KEY` | API authentication key | `test-api-key` |
| `API_HOST` | Server bind address | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `CHUNK_SIZE` | Maximum chunk size in characters | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `LOG_FORMAT` | Log format (json or console) | `json` |

## Running the Server

### Development Mode

```bash
uvicorn remote_rag.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn remote_rag.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python

```python
import uvicorn
from remote_rag.api import app

uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Reference

All endpoints except `/health` require authentication via the `X-API-Key` header.

### Authentication

Include the API key in the request header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/collections
```

### Endpoints

#### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "qdrant": "healthy",
    "embedder": "healthy",
    "chunker": "healthy"
  }
}
```

#### POST /ingest

Ingest text content for semantic search.

**Request Body:**
```json
{
  "text": "Your document text content here...",
  "collection_name": "my-collection",  // optional, defaults to "default"
  "metadata": {                         // optional
    "source": "document.pdf",
    "author": "John Doe"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested 5 chunks",
  "collection_name": "my-collection",
  "chunks_created": 5,
  "chunk_ids": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"],
  "chunks": [
    {
      "chunk_index": 0,
      "chunk_text": "First chunk text...",
      "chunk_id": "uuid1"
    }
  ]
}
```

#### POST /ingest_url

Ingest document from HTTPS URL.

**Request Body:**
```json
{
  "url": "https://example.com/document.pdf",
  "collection_name": "my-collection",  // optional
  "metadata": {                         // optional
    "category": "research"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested document from https://example.com/document.pdf",
  "url": "https://example.com/document.pdf",
  "collection_name": "my-collection",
  "chunks_created": 10,
  "chunk_ids": ["uuid1", "uuid2", ...],
  "document_length": 5420
}
```

#### POST /search

Semantic search across ingested documents.

**Request Body:**
```json
{
  "query": "What is the main topic?",
  "collection_name": "my-collection",   // optional
  "limit": 5,                           // optional, default: 5, max: 100
  "score_threshold": 0.7,               // optional, default: 0.0 (0.0-1.0)
  "filter": {                           // optional metadata filters
    "source": "document.pdf"
  }
}
```

**Response:**
```json
{
  "success": true,
  "query": "What is the main topic?",
  "collection_name": "my-collection",
  "results": [
    {
      "id": "uuid1",
      "score": 0.92,
      "text": "Relevant chunk text...",
      "metadata": {
        "source": "document.pdf",
        "chunk_index": 3
      }
    }
  ],
  "count": 5
}
```

#### GET /collections

List all Qdrant collections.

**Response:**
```json
{
  "success": true,
  "collections": ["default", "my-collection", "another-collection"],
  "count": 3
}
```

#### GET /documents/{document_id}?collection_name=my-collection

Retrieve a specific document by ID.

**Query Parameters:**
- `collection_name` (optional): Collection name, defaults to "default"

**Response (found):**
```json
{
  "success": true,
  "document_id": "uuid1",
  "collection_name": "my-collection",
  "text": "Document text content...",
  "metadata": {
    "source": "document.pdf",
    "chunk_index": 0
  },
  "found": true
}
```

**Response (not found):**
```json
{
  "success": true,
  "document_id": "uuid999",
  "collection_name": "my-collection",
  "text": null,
  "metadata": null,
  "found": false
}
```

### Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "error": "Additional error context"
  }
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing API key
- `403 Forbidden`: Invalid API key
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: Wrong HTTP method
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Testing

### Run All Tests

```bash
# Run all tests with coverage
uv run pytest -v

# Run only unit tests
uv run pytest tests/unit/ -v

# Run only integration tests
uv run pytest tests/integration/ -v
```

### Test Coverage

Current test coverage: 89% (83 tests total)

```bash
# Generate HTML coverage report
uv run pytest --cov=src/remote_rag --cov-report=html
# Open htmlcov/index.html in browser
```

### Code Quality

```bash
# Run linter
uv run ruff check src/

# Auto-fix linter issues
uv run ruff check src/ --fix

# Run type checker
uv run mypy src/remote_rag/
```

## Development

### Project Structure

```
remote-rag-server/
├── src/
│   └── remote_rag/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py            # FastAPI application
│       │   ├── auth.py           # Authentication middleware
│       │   ├── logging.py        # Structured logging
│       │   └── models.py         # Pydantic models
│       ├── services/
│       │   ├── __init__.py
│       │   ├── chunker.py        # Text chunking service
│       │   ├── embedder.py       # Embedding generation service
│       │   └── qdrant.py         # Qdrant database service
│       └── mcp/
│           └── __init__.py       # (Phase 4: MCP server)
├── tests/
│   ├── unit/                     # Unit tests (62 tests)
│   │   ├── test_chunker.py
│   │   ├── test_embedder.py
│   │   └── test_qdrant.py
│   └── integration/              # Integration tests (21 tests)
│       ├── conftest.py
│       └── test_api.py
├── pyproject.toml                # Project dependencies and config
├── .env.example                  # Example environment configuration
└── README.md                     # This file
```

### Adding New Endpoints

1. Define Pydantic models in `api/models.py`
2. Implement endpoint in `api/app.py`
3. Add integration tests in `tests/integration/test_api.py`
4. Update this README with endpoint documentation

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use modern Python 3.11+ type syntax (dict, list instead of Dict, List)
- All code must pass ruff linter and mypy type checker

## Troubleshooting

### Common Issues

**Issue**: `qdrant_client` connection errors
- **Solution**: Verify `QDRANT_URL` and `QDRANT_API_KEY` are correct
- Check Qdrant server is running and accessible

**Issue**: Azure OpenAI authentication errors
- **Solution**: Verify `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT`
- Ensure API key has necessary permissions
- Check API version compatibility

**Issue**: Empty search results
- **Solution**: Ensure documents are ingested first
- Check collection name matches between ingest and search
- Verify embeddings are generated correctly

**Issue**: Chunking produces too many/few chunks
- **Solution**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` in configuration
- Recommended: 512 characters with 50 character overlap

### Logging

Logs include structured information for debugging:

```json
{
  "event": "http_request",
  "method": "POST",
  "path": "/ingest",
  "client": "192.168.1.100",
  "level": "info",
  "timestamp": "2025-10-19T20:00:00.000000Z"
}
```

Set `LOG_FORMAT=console` for human-readable logs during development.

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Use `/ingest` with large text instead of multiple small requests
2. **Chunk Size**: Larger chunks (512-1024) reduce embedding API calls but may reduce search precision
3. **Connection Pooling**: Async clients automatically manage connection pools
4. **Search Limits**: Use appropriate `limit` values to reduce response size
5. **Score Threshold**: Set `score_threshold` to filter low-relevance results

### Scaling

For production deployments:

1. **Multiple Workers**: Run with `--workers 4` or more (1-2x CPU cores)
2. **Reverse Proxy**: Use nginx or similar for SSL termination and load balancing
3. **Qdrant Clustering**: Use Qdrant cluster for high availability
4. **Rate Limiting**: Implement rate limiting middleware for API protection
5. **Caching**: Add caching layer for frequent queries

## Security

### Best Practices

1. **API Key Management**:
   - Use strong, randomly generated API keys
   - Rotate keys regularly
   - Never commit keys to version control

2. **Network Security**:
   - Use HTTPS in production (configure reverse proxy)
   - Restrict API access to known IP ranges if possible
   - Use VPN or private networks for internal deployments

3. **Input Validation**:
   - All inputs validated via Pydantic models
   - File size limits enforced
   - URL validation for `/ingest_url`

4. **Azure OpenAI**:
   - Use managed identity when possible
   - Store API keys in secure vault (Azure Key Vault, etc.)
   - Monitor usage and costs

## License

[Specify your license here]

## Support

For issues and questions:
- Create an issue in the project repository
- Check existing documentation and troubleshooting section
- Review logs for detailed error information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass and code quality checks pass
5. Submit a pull request

## Changelog

### Version 0.1.0 (Phase 1-3 Complete)

**Added:**
- FastAPI REST API with 6 endpoints
- API key authentication
- Text and URL-based document ingestion
- Semantic search with filters
- Structured logging with structlog
- Comprehensive test suite (89% coverage)
- Complete API documentation

**Services:**
- ChunkerService with LangChain integration
- EmbedderService with Azure OpenAI
- QdrantService for vector operations

**Testing:**
- 62 unit tests
- 21 integration tests
- Linter and type checker compliance
