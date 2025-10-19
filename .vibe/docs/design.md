# Design Document - Enterprise RAG System

**Project Complexity**: 🏢 CORE (Small team, MVP timeline)
**Version**: 1.0
**Date**: 2025-10-19

---

<!-- # 🚀 ESSENTIAL - Required for all projects -->

## 1. Naming Conventions

### Classes and Types

**Python Naming Conventions (PEP 8):**

- **Classes**: `PascalCase` (e.g., `IngestRequest`, `SearchResponse`, `QdrantService`)
- **Type Aliases**: `PascalCase` (e.g., `DocumentID`, `CollectionName`)
- **Enums**: `PascalCase` with UPPER_CASE members (e.g., `class SourceType(Enum): LOCAL = "local"`)
- **Pydantic Models**: `PascalCase` with descriptive suffixes
  - Requests: `*Request` (e.g., `IngestRequest`, `SearchRequest`)
  - Responses: `*Response` (e.g., `SearchResponse`, `IngestResponse`)
  - Internal models: `*Model` (e.g., `ChunkModel`, `DocumentModel`)

### Methods and Functions

**Async Functions:**
- Prefix with `async def` (obvious from signature)
- Use descriptive verbs: `fetch_url()`, `generate_embeddings()`, `store_vectors()`

**MCP Tools:**
- Use snake_case with action verbs
- Local MCP: `convert_to_text()`, `convert_and_ingest()`
- Remote MCP: `search()`, `ingest_url()`, `list_collections()`, `get_document()`

**Service Methods:**
- CRUD operations: `create_*`, `read_*`, `update_*`, `delete_*`
- Queries: `get_*`, `find_*`, `list_*`
- Actions: `chunk_text()`, `embed_chunks()`, `search_collection()`

**Private Methods:**
- Prefix with single underscore: `_validate_request()`, `_format_error()`

### Variables and Constants

**Variables:**
- `snake_case` for all variables (e.g., `doc_id`, `chunk_count`, `embedding_vector`)
- Descriptive names: avoid abbreviations unless common (`url`, `api`, `id` are OK)

**Constants:**
- `UPPER_SNAKE_CASE` for module-level constants
- Environment variables match constant names: `QDRANT_URL`, `RAG_API_KEY`
- Default configuration: `DEFAULT_CHUNK_SIZE = 512`, `DEFAULT_TOP_K = 5`

**Configuration:**
- Use pydantic `BaseSettings` for type-safe configuration
- Class name: `Settings` or `*Config` (e.g., `QdrantConfig`, `AzureOpenAIConfig`)

### Packages and Modules

**Project Structure:**
```
local-mcp-server/
├── src/
│   └── local_mcp/          # Package name: snake_case
│       ├── server.py       # Module name: snake_case, descriptive
│       ├── converter.py
│       └── ingest_client.py

remote-rag-server/
├── src/
│   └── rag_server/         # Package name: snake_case
│       ├── api/            # Subpackage: lowercase
│       ├── mcp/
│       └── services/
```

**Module Naming:**
- Single responsibility: `chunker.py`, `embedder.py`, `auth.py`
- Avoid generic names: Use `qdrant_service.py` instead of `database.py`

---

## 2. Design Principles

### Separation of Concerns

**Three-Layer Architecture:**

1. **Protocol Layer** (MCP servers)
   - Handle MCP protocol communication
   - Validate inputs from AI assistants
   - Translate to service layer calls
   - No business logic

2. **Service Layer** (Business logic)
   - Core RAG functionality (chunking, embedding, search)
   - Independent of protocol (HTTP/MCP)
   - Testable without external dependencies

3. **Infrastructure Layer** (External services)
   - Qdrant client, Azure OpenAI client, markitdown
   - Wrapped in adapters for testability
   - Configuration via dependency injection

**Example Structure:**
```python
# Protocol Layer (MCP)
@mcp.tool()
async def search(query: str, collection: str = "default", top_k: int = 5):
    # Validate, call service, return MCP response
    result = await search_service.search(query, collection, top_k)
    return result

# Service Layer (Business Logic)
class SearchService:
    async def search(self, query: str, collection: str, top_k: int):
        # 1. Generate embedding
        # 2. Query Qdrant
        # 3. Format results
        pass

# Infrastructure Layer (External)
class QdrantService:
    async def vector_search(self, collection: str, vector: List[float], limit: int):
        # Direct Qdrant client interaction
        pass
```

### Dependency Injection

**Use constructor injection for testability:**
```python
class IngestService:
    def __init__(
        self,
        chunker: ChunkerService,
        embedder: EmbedderService,
        qdrant: QdrantService
    ):
        self.chunker = chunker
        self.embedder = embedder
        self.qdrant = qdrant
```

**Benefits:**
- Easy to mock in tests
- Clear dependencies
- Swap implementations (e.g., mock Qdrant for testing)

### Error Handling

**Use custom exception hierarchy:**
```python
class RAGException(Exception):
    """Base exception for RAG system"""
    pass

class DocumentConversionError(RAGException):
    """Failed to convert document"""
    pass

class EmbeddingGenerationError(RAGException):
    """Failed to generate embeddings"""
    pass

class QdrantConnectionError(RAGException):
    """Failed to connect to Qdrant"""
    pass
```

**Error response format (FastAPI):**
```python
{
    "error": "DocumentConversionError",
    "detail": "Failed to convert PDF: file is encrypted",
    "status_code": 400,
    "timestamp": "2025-10-19T10:30:00Z",
    "request_id": "uuid"
}
```

### Async Best Practices

**Use async throughout:**
- All service methods are async
- Use `async with` for resource management
- Batch operations where possible (embedding generation)

**Avoid blocking calls:**
```python
# BAD
def blocking_operation():
    time.sleep(1)

# GOOD
async def async_operation():
    await asyncio.sleep(1)
```

---

## 3. Component Design

### Local MCP Server

**Responsibility:** Convert local documents to text; optionally ingest to remote API

**Key Components:**

1. **MCP Server** (`server.py`)
   - Registers MCP tools
   - Handles MCP protocol communication
   - Delegates to converter and ingest client

2. **Document Converter** (`converter.py`)
   - Wraps markitdown library
   - Handles file validation
   - Returns converted text

3. **Ingest Client** (`ingest_client.py`)
   - HTTP client for Remote RAG API
   - Handles authentication (Bearer token)
   - Retry logic for network failures

**Design Pattern:** Facade pattern (simple interface over markitdown complexity)

---

### Remote RAG API

**Responsibility:** Core RAG functionality - ingest, chunk, embed, search

**Key Components:**

1. **FastAPI Application** (`main.py`)
   - Defines all HTTP endpoints
   - Middleware: logging, CORS, error handling
   - Lifespan: initialize services (Qdrant, OpenAI clients)

2. **API Routes** (`api/routes.py`)
   - Endpoint handlers
   - Request validation (Pydantic)
   - Response serialization

3. **Service Layer:**
   - `ChunkerService` (`services/chunker.py`): LangChain RecursiveCharacterTextSplitter
   - `EmbedderService` (`services/embedder.py`): Azure OpenAI embeddings
   - `QdrantService` (`services/qdrant_service.py`): Vector storage and search
   - `ConverterService` (`services/converter.py`): markitdown for URLs

4. **Authentication** (`api/auth.py`)
   - FastAPI dependency for API key validation
   - Secure comparison of API keys

**Design Pattern:** Service Layer pattern with dependency injection

---

### Remote RAG MCP Server

**Responsibility:** Expose RAG API as MCP tools for AI assistants

**Key Components:**

1. **MCP Server** (`mcp/server.py`)
   - Registers 4 MCP tools (search, ingest_url, list_collections, get_document)
   - Thin wrappers around HTTP calls to Remote RAG API (localhost)
   - Error handling and response formatting

**Design Pattern:** Adapter pattern (MCP protocol → HTTP REST API)

---

### Data Models

**Pydantic Models (Remote RAG API):**

```python
# Request Models
class IngestRequest(BaseModel):
    text: str
    metadata: DocumentMetadata

class DocumentMetadata(BaseModel):
    filename: str
    collection: str = "default"
    source: Literal["local", "url"]
    url: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    collection: str = "default"
    top_k: int = Field(default=5, ge=1, le=50)

class IngestURLRequest(BaseModel):
    url: HttpUrl
    collection: str = "default"

# Response Models
class IngestResponse(BaseModel):
    status: Literal["success", "failed"]
    doc_id: str
    chunks: int

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: dict

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    collection: str

class CollectionInfo(BaseModel):
    name: str
    doc_count: int

class CollectionsResponse(BaseModel):
    collections: List[CollectionInfo]
```

---

## 4. Data Modeling

### Qdrant Schema Design

**Collection Strategy:**
- Hybrid: "default" collection + user-defined collections
- Each collection is isolated (separate vector spaces)
- Collection names: alphanumeric + hyphens (e.g., "project-alpha", "team-docs")

**Vector Point Schema:**
```python
{
    "id": "uuid",  # Unique point ID
    "vector": [float] * 1536,  # text-embedding-3-small dimensions
    "payload": {
        "doc_id": str,          # Document identifier (same for all chunks)
        "chunk_index": int,     # Position within document (0, 1, 2, ...)
        "text": str,            # Original chunk text
        "metadata": {
            "filename": str,
            "source": "local" | "url",
            "collection": str,
            "ingested_at": str,  # ISO 8601 timestamp
            "page": int | None,  # Page number if available
            "url": str | None    # Original URL if source="url"
        }
    }
}
```

**Indexing:**
- Distance metric: Cosine similarity
- HNSW parameters: Default (ef_construct=100, m=16)
- Can tune later for performance

**Query Strategy:**
- Search within single collection (collection name = Qdrant collection)
- Metadata filtering: Filter by doc_id to retrieve all chunks of a document

---

### Document Lifecycle

**Ingestion Flow:**
```
Document (PDF/URL)
  ↓
Conversion (markitdown) → Markdown text
  ↓
Chunking (RecursiveCharacterTextSplitter) → List[str]
  ↓
Embedding (Azure OpenAI batch) → List[List[float]]
  ↓
Storage (Qdrant) → Points with metadata
  ↓
Return doc_id, chunk_count
```

**Search Flow:**
```
Query (natural language)
  ↓
Embedding (Azure OpenAI) → List[float]
  ↓
Vector Search (Qdrant) → Top-k points
  ↓
Format Results → List[SearchResult]
  ↓
Return to user
```

**Document Retrieval Flow:**
```
doc_id
  ↓
Query Qdrant (filter: doc_id, collection)
  ↓
Retrieve all chunks (sorted by chunk_index)
  ↓
Return full document text + metadata
```

---

## 5. Implementation Order and Dependencies

### Phase 1: Local MCP Server (Week 1)

**Tasks:**
1. Project setup (pyproject.toml, poetry, directory structure)
2. Implement document converter wrapper (markitdown)
3. Implement MCP server with 2 tools:
   - `convert_to_text(uri: str)`
   - `convert_and_ingest(uri: str, collection: str)`
4. Implement HTTP ingest client (calls Remote RAG API)
5. Unit tests (mock markitdown, mock HTTP client)
6. Integration test (test against mock server)

**Deliverables:**
- Working Local MCP Server
- Can convert documents locally
- Can send to remote API (when available)

**Dependencies:**
- markitdown 0.1.3
- Anthropic MCP SDK
- httpx 0.28+

---

### Phase 2: Remote RAG API - Core Services (Week 2)

**Tasks:**
1. Project setup (pyproject.toml, poetry, directory structure)
2. Implement configuration management (pydantic BaseSettings)
3. Implement ChunkerService (LangChain RecursiveCharacterTextSplitter)
4. Implement EmbedderService (Azure OpenAI embeddings)
5. Implement QdrantService (async client, CRUD operations)
6. Unit tests for each service (mock external dependencies)

**Deliverables:**
- Tested service layer
- Can chunk, embed, store/search in Qdrant

**Dependencies:**
- LangChain 1.0+
- openai 2.5+
- qdrant-client 1.15+

**Breaking Changes Testing:**
- Verify LangChain 1.0 RecursiveCharacterTextSplitter works
- Verify openai 2.5 Azure embeddings work

---

### Phase 3: Remote RAG API - HTTP Endpoints (Week 3)

**Tasks:**
1. Implement FastAPI application (main.py)
2. Implement API routes:
   - `POST /api/v1/ingest`
   - `POST /api/v1/ingest_url`
   - `POST /api/v1/search`
   - `GET /api/v1/collections`
   - `GET /api/v1/documents/{doc_id}`
   - `GET /health`
3. Implement authentication middleware (API key)
4. Implement error handling and logging (structlog)
5. API integration tests (TestClient)

**Deliverables:**
- Working FastAPI application
- All endpoints functional
- Can ingest and search documents

**Dependencies:**
- FastAPI 0.119+
- structlog (for JSON logging)

---

### Phase 4: Remote RAG MCP Server (Week 3-4)

**Tasks:**
1. Implement MCP server in same codebase (`mcp/server.py`)
2. Implement 4 MCP tools (call localhost FastAPI)
3. Implement main.py entrypoint (run both FastAPI + MCP concurrently)
4. Integration tests (test MCP tools)

**Deliverables:**
- MCP server running alongside FastAPI
- AI assistants can call MCP tools

**Dependencies:**
- Anthropic MCP SDK
- httpx 0.28+ (for localhost calls)

---

### Phase 5: OpenShift Deployment (Week 4)

**Tasks:**
1. Create Dockerfile (Python 3.11, multi-stage build)
2. Create OpenShift manifests:
   - deployment.yaml (Pod, Container, Resources)
   - service.yaml (ClusterIP)
   - route.yaml (HTTPS, TLS edge termination)
   - configmap.yaml (non-secret config)
   - secret.yaml (API keys)
3. Test deployment locally (kind/minikube)
4. Deploy to OpenShift dev environment
5. Smoke tests (health check, basic ingestion, search)

**Deliverables:**
- Dockerized application
- OpenShift deployment manifests
- Deployed to dev environment

**Dependencies:**
- Access to OpenShift cluster
- Qdrant URL and API key
- Azure OpenAI credentials

---

### Phase 6: Integration and E2E Testing (Week 5)

**Tasks:**
1. End-to-end test: Local MCP → Remote API → Qdrant
2. End-to-end test: Remote MCP → Remote API → Qdrant
3. Performance testing (1000 queries, measure latency)
4. Load testing (concurrent ingestion)
5. Documentation (README, setup instructions, API docs)

**Deliverables:**
- E2E tests passing
- Performance metrics documented
- User documentation

---

## 6. Test Strategy

### Unit Tests

**Coverage Target:** 80%+ line coverage

**Scope:**
- Service layer methods (chunker, embedder, qdrant_service)
- API routes (mocked services)
- MCP tools (mocked HTTP client)

**Tools:**
- `pytest` for test framework
- `pytest-asyncio` for async tests
- `pytest-mock` for mocking
- `httpx` TestClient for FastAPI

**Example:**
```python
@pytest.mark.asyncio
async def test_chunker_service():
    chunker = ChunkerService(chunk_size=512, chunk_overlap=50)
    text = "..." * 10000  # Long text
    chunks = await chunker.chunk_text(text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 2000 for chunk in chunks)  # Approx 512 tokens
```

---

### Integration Tests

**Scope:**
- FastAPI endpoints with real services but mocked external APIs
- MCP tools with real HTTP calls to test FastAPI
- Qdrant operations (use in-memory Qdrant or test instance)

**Tools:**
- `pytest` + `httpx.AsyncClient`
- Docker Compose for test Qdrant instance

**Example:**
```python
@pytest.mark.asyncio
async def test_ingest_endpoint(test_client, mock_azure_openai):
    response = await test_client.post(
        "/api/v1/ingest",
        json={"text": "Sample text", "metadata": {...}},
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "doc_id" in data
```

---

### End-to-End Tests

**Scope:**
- Full workflow: Local MCP → Remote API → Qdrant → Search
- Full workflow: Remote MCP → Remote API → Qdrant → Search
- Test against deployed OpenShift environment (dev)

**Tools:**
- `pytest` with real services
- Test documents (sample PDFs, URLs)

**Example:**
```python
@pytest.mark.e2e
async def test_full_ingestion_and_search():
    # 1. Ingest document via Local MCP
    result = await local_mcp.convert_and_ingest("test.pdf", "test-collection")
    doc_id = result["doc_id"]

    # 2. Search via Remote MCP
    search_result = await remote_mcp.search("test query", "test-collection")

    # 3. Verify results
    assert len(search_result["results"]) > 0
```

---

### Performance Tests

**Metrics to measure:**
- Search latency (p50, p95, p99)
- Ingestion throughput (docs/minute)
- Concurrent query handling

**Tools:**
- `locust` or `pytest-benchmark`
- OpenShift monitoring (Prometheus, Grafana)

**Targets:**
- Search latency: <3 seconds (95th percentile)
- Ingestion: 100 docs/day (sustained)
- Concurrent queries: Handle 10 concurrent users

---

## 7. Development Workflow

### Local Development Setup

**Prerequisites:**
- Python 3.11+
- Poetry for dependency management
- Docker (for local Qdrant instance)
- Azure OpenAI credentials (dev environment)

**Steps:**
1. Clone repository
2. Install dependencies: `poetry install`
3. Start local Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
4. Configure environment variables (`.env` file)
5. Run tests: `poetry run pytest`
6. Run local server: `poetry run python -m rag_server.main`

---

### Git Workflow

**Branches:**
- `main`: Production-ready code
- `develop`: Integration branch
- Feature branches: `feature/local-mcp`, `feature/remote-api`, etc.

**Commit Messages:**
- Follow Conventional Commits format
- Examples:
  - `feat(local-mcp): implement convert_to_text tool`
  - `fix(embedder): handle Azure OpenAI rate limits`
  - `docs(architecture): update ADR-006 with breaking changes`

---

### CI/CD Pipeline (Future)

**Phases:**
1. **Build**: Install dependencies, run linter (ruff)
2. **Test**: Run unit + integration tests
3. **Build Image**: Create Docker image
4. **Deploy Dev**: Deploy to OpenShift dev environment
5. **E2E Tests**: Run end-to-end tests
6. **Deploy Prod**: Manual approval, deploy to production

---

*End of Design Document*
