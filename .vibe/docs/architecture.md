# Enterprise RAG Architecture Documentation

*arc42 Architecture Documentation*
*Version: 1.0*
*Date: 2025-10-19*
*Project: qdrant-full-mcp*

---

# Introduction and Goals

## Requirements Overview

This architecture implements an **Enterprise RAG (Retrieval-Augmented Generation) system** using a three-component design that addresses the MCP protocol's text-only limitation while enabling semantic search over document corpora.

**Key Requirements:**
- **REQ-1 to REQ-11**: See [requirements.md](requirements.md) for complete EARS-formatted requirements
- **Core Capabilities**:
  - Convert local binary documents (PDF, DOCX, XLSX, etc.) to text
  - Ingest and index documents in vector database
  - Semantic search using natural language queries
  - Collection-based document organization
  - HTTPS-reachable document ingestion

**Motivation:**

Technical developers need to perform semantic searches across large document corpora (10k documents, ~30-40 pages each) without building custom RAG infrastructure. The system must work seamlessly with AI assistants (Claude Code) via the MCP protocol while handling binary document conversion locally.

**Scale Requirements (MVP):**
- Max 10,000 documents total corpus
- ~100 documents/day ingestion rate
- Average document size: 30-40 pages
- Max 10 concurrent developer users
- Max 1,000 queries/day
- Reasonable response times (no strict SLA for MVP)

## Quality Goals

| Priority | Quality Goal | Scenario | Rationale |
|----------|-------------|----------|-----------|
| 1 | **Developer Experience** | Developers can ingest documents and search with <5 commands via MCP | Primary users are technical staff; UX must be seamless |
| 2 | **Extensibility** | System can evolve to Graph RAG and Hybrid RAG without major rewrites | Explicitly called out for future roadmap |
| 3 | **Reliability** | 99% uptime for search queries during business hours | Core productivity tool for development teams |
| 4 | **Performance** | Search results return in <3 seconds for 95% of queries | Developer productivity depends on fast feedback |
| 5 | **Maintainability** | Clear separation of concerns (conversion, API, MCP wrapper) | Technical debt must be minimized for small team |

## Stakeholders

| Role | Contact | Expectations |
|------|---------|--------------|
| **Technical Developers** | End Users | Simple MCP interface, accurate search results, <3s response time |
| **DevOps Team** | Deployment | Clear OpenShift manifests, environment configuration, logging |
| **System Administrators** | Operations | Simple API key authentication, health monitoring, troubleshooting |
| **Solution Architect** | Decision Maker | Extensibility to Graph RAG / Hybrid RAG, cost efficiency |

---

# Architecture Constraints

## Technical Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **OpenShift Deployment** | All remote components must deploy to OpenShift cluster | Kubernetes manifests required; container-first design |
| **Existing Qdrant Instance** | Qdrant already deployed with API key and URL | No Qdrant installation needed; use existing infrastructure |
| **MCP Protocol** | AI assistants interact via MCP (text-only protocol) | Binary documents must be converted locally before transmission |
| **Azure OpenAI** | Embeddings via Azure OpenAI (text-embedding-3-small) | Cloud dependency; requires Azure subscription |
| **Python 3.11+** | Remote components must use Python 3.11 or newer | Leverage async improvements and modern features |

## Organizational Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Internal Users Only** | Technical developers (internal staff) | Simplified authentication (API key); no OAuth/SSO needed |
| **No Web UI (MVP)** | MCP-only interface for first release | Focus on backend quality; defer UI complexity |
| **Minimal Security** | API key authentication sufficient for MVP | Enhanced security (audit logs, RBAC) deferred |

## Conventions

| Convention | Description |
|------------|-------------|
| **Async-First** | All remote components use async Python (FastAPI, Qdrant, OpenAI) |
| **Environment Variables** | All configuration via env vars (12-factor app) |
| **Structured Logging** | JSON-formatted logs for OpenShift log aggregation |
| **API Versioning** | REST API endpoints prefixed with `/api/v1/` for future compatibility |

---

# Context and Scope

## Business Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Assistant (Claude Code)               │
│                                                                 │
│  - Developer uses natural language to search documents          │
│  - Developer ingests local PDFs via MCP commands               │
└───────────┬────────────────────────────────────┬────────────────┘
            │                                    │
            │ MCP Protocol                       │ MCP Protocol
            │ (text-only)                        │ (text-only)
            │                                    │
┌───────────▼─────────────┐          ┌──────────▼─────────────────┐
│   Local MCP Server      │          │  Remote RAG MCP Server     │
│   (Developer Machine)   │          │  (OpenShift Cluster)       │
│                         │          │                            │
│  - Convert PDF to text  │          │  - search()                │
│  - Optional: POST to    │          │  - ingest_url()            │
│    Remote RAG API       │          │  - list_collections()      │
└───────────┬─────────────┘          └──────────┬─────────────────┘
            │                                    │
            │ HTTP POST /ingest                  │ HTTP (internal)
            │                                    │
            └─────────────┬──────────────────────┘
                          │
                ┌─────────▼──────────────────────────────────┐
                │      Remote RAG API (FastAPI)              │
                │      (OpenShift Cluster)                   │
                │                                            │
                │  HTTP REST Endpoints:                      │
                │  - POST /api/v1/ingest                     │
                │  - POST /api/v1/ingest_url                 │
                │  - POST /api/v1/search                     │
                │  - GET  /api/v1/collections                │
                │  - GET  /api/v1/documents/{id}             │
                │  - GET  /health                            │
                └────┬──────────────┬──────────────────┬──────┘
                     │              │                  │
                     │              │                  │
          ┌──────────▼─────┐ ┌─────▼─────────┐ ┌─────▼──────────┐
          │ Qdrant Vector  │ │ Azure OpenAI  │ │ Document Fetch │
          │ Database       │ │ Embeddings    │ │ (HTTPS URLs)   │
          │ (Existing)     │ │ (Cloud)       │ │                │
          └────────────────┘ └───────────────┘ └────────────────┘
```

### Communication Partners

| Partner | Input | Output | Protocol |
|---------|-------|--------|----------|
| **AI Assistant** | MCP tool calls (search, ingest) | Search results, ingestion status | MCP (JSON-RPC over stdio/HTTP) |
| **Local MCP Server** | Local file paths | Converted text, ingestion status | MCP + HTTP (to Remote RAG API) |
| **Remote RAG MCP** | Search queries, URL ingestion requests | Search results, document metadata | MCP + HTTP (to Remote RAG API) |
| **Remote RAG API** | Text, URLs, search queries | Ingestion status, search results | HTTP REST (JSON) |
| **Qdrant** | Vectors, metadata, search queries | Search results | Qdrant gRPC/HTTP |
| **Azure OpenAI** | Text chunks | Embedding vectors (1536 dimensions) | Azure OpenAI REST API |

## Technical Context

### Local MCP Server (Developer Machine)

**Technology:** Python 3.11+, Anthropic MCP SDK, markitdown library

**Interfaces:**
- **Input**: MCP tool calls from AI assistant
  - `convert_to_text(uri: str)` → text content
  - `convert_and_ingest(uri: str, collection: str)` → ingestion status
- **Output**:
  - Text content (for conversion-only)
  - HTTP POST to Remote RAG API `/api/v1/ingest` (for ingestion)

**Environment Configuration:**
- `RAG_API_URL`: Remote RAG API base URL (e.g., `https://rag-api.example.com`)
- `RAG_API_KEY`: Bearer token for authentication

### Remote RAG API (OpenShift - FastAPI)

**Technology:** Python 3.11+, FastAPI, async throughout

**Interfaces:**
- **HTTP REST Endpoints** (all require `Authorization: Bearer <API_KEY>` except `/health`):
  - `POST /api/v1/ingest` - Accept text, chunk, embed, store
  - `POST /api/v1/ingest_url` - Fetch URL, convert, ingest
  - `POST /api/v1/search` - Semantic search
  - `GET /api/v1/collections` - List collections
  - `GET /api/v1/documents/{doc_id}` - Retrieve document
  - `GET /health` - Health check (no auth)

**Environment Configuration:**
- `QDRANT_URL`: Qdrant instance URL
- `QDRANT_API_KEY`: Qdrant authentication
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Deployment name (e.g., "text-embedding-3-small")
- `RAG_API_KEY`: API key for authenticating clients

### Remote RAG MCP Server (OpenShift - MCP Wrapper)

**Technology:** Python 3.11+, Anthropic MCP SDK

**Interfaces:**
- **Input**: MCP tool calls from AI assistant
  - `search(query: str, collection: str, top_k: int)`
  - `ingest_url(uri: str, collection: str)`
  - `list_collections()`
  - `get_document(doc_id: str)`
- **Output**:
  - HTTP calls to Remote RAG API (internal, same container/pod)
  - MCP responses to AI assistant

**Environment Configuration:**
- `RAG_API_URL`: `http://localhost:8000` (same container)
- `RAG_API_KEY`: Shared with Remote RAG API

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   OpenShift Cluster                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Pod: rag-server                                      │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  Container: rag-server                          │ │ │
│  │  │                                                 │ │ │
│  │  │  ┌────────────────────┐  ┌──────────────────┐  │ │ │
│  │  │  │ FastAPI            │  │ MCP Server       │  │ │ │
│  │  │  │ (Port 8000)        │  │ (stdio/HTTP)     │  │ │ │
│  │  │  │                    │  │                  │  │ │ │
│  │  │  │ Remote RAG API     │◄─┤ Remote RAG MCP   │  │ │ │
│  │  │  └────────────────────┘  └──────────────────┘  │ │ │
│  │  │                                                 │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │                                                       │ │
│  │  Exposed via:                                         │ │
│  │  - Service (ClusterIP) → Internal FastAPI            │ │
│  │  - Route (HTTPS) → External access for MCP/API       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────┐                           │
│  │  Existing Qdrant Service    │                           │
│  │  (Pre-deployed)             │                           │
│  └─────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

# Solution Strategy

## Fundamental Decisions

### 1. Three-Component Architecture

**Decision:** Separate Local MCP, Remote RAG API, and Remote RAG MCP

**Rationale:**
- **Separation of Concerns**: Conversion (local), business logic (API), protocol adapter (MCP)
- **Scalability**: API and MCP can scale independently if needed
- **Security**: API not directly exposed to AI assistants; MCP acts as controlled gateway
- **Testability**: Each component can be unit/integration tested independently

**Alternative Considered:** Two-component (Local MCP + Remote API/MCP combined)
- **Rejected**: Mixing HTTP REST API and MCP protocol in same interface creates confusion; harder to test

### 2. Single Container Deployment (Remote Components)

**Decision:** Deploy Remote RAG API + Remote RAG MCP in single Docker container

**Rationale:**
- **Simplicity**: Easier deployment, fewer moving parts for MVP
- **Low Traffic**: 1000 queries/day doesn't require separate scaling
- **No Network Overhead**: MCP → API is localhost communication
- **Easier Debugging**: Single log stream, single pod to inspect

**Alternative Considered:** Separate containers/pods
- **Deferred**: Can split later if scaling needs emerge; YAGNI for MVP

### 3. Async-First Python Stack

**Decision:** Use async FastAPI, async Qdrant client, async OpenAI client

**Rationale:**
- **Performance**: Handle 1000 queries/day with <10 concurrent connections efficiently
- **IO-Bound Workload**: Document ingestion, embeddings, vector search are all IO-heavy
- **Modern Python**: Python 3.11+ has excellent async support
- **Future-Proof**: Easier to scale to higher traffic later

**Trade-off:** Slightly more complex code, but FastAPI makes async natural

### 4. RecursiveCharacterTextSplitter for Chunking

**Decision:** Use LangChain's RecursiveCharacterTextSplitter (not fixed-size or semantic)

**Rationale:**
- **Semantic Boundaries**: Splits at paragraphs, sentences (better than fixed-size)
- **Proven**: Battle-tested in production RAG systems
- **Extensibility**: Works well for future Graph RAG (entity extraction) and Hybrid RAG (BM25)
- **Configurable**: Easy to tune chunk_size (512 tokens) and chunk_overlap (50 tokens)

**Alternative Considered:** Advanced semantic chunking with LLM
- **Deferred**: Too expensive and complex for MVP; RecursiveCharacterTextSplitter provides 80% of benefit

### 5. Hybrid Collection Strategy

**Decision:** Support both default collection and user-defined collections

**Rationale:**
- **Flexibility**: Users can organize by project/team/domain
- **Simple Default**: New users get started immediately with "default" collection
- **Scoped Search**: Search within specific collections for better precision

**Implementation:** Each Qdrant collection is isolated; metadata filtering within collections

### 6. markitdown Library (Not Fork)

**Decision:** Build new MCP server using markitdown library (not forking markitdown-mcp)

**Rationale:**
- **Full Control**: Custom MCP tool design for our exact requirements
- **Simpler**: No upstream merge conflicts or dependency on external repo
- **Minimal Scope**: Local MCP is thin wrapper around markitdown

**Alternative Considered:** Fork markitdown-mcp
- **Rejected**: Adds maintenance burden; our requirements differ enough to justify fresh start

---

# Building Block View

## Level 1: System Context

### Whitebox Overall System

**Overview Diagram:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enterprise RAG System                        │
│                                                                 │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │   Local MCP      │  │  Remote RAG    │  │  Remote RAG    │  │
│  │   Server         │  │  API           │  │  MCP Server    │  │
│  │                  │  │  (FastAPI)     │  │  (MCP Wrapper) │  │
│  │  - Document      │  │                │  │                │  │
│  │    Conversion    │  │  - Chunking    │  │  - MCP Tools   │  │
│  │  - Optional      │  │  - Embedding   │  │  - Protocol    │  │
│  │    Ingestion     │  │  - Storage     │  │    Adapter     │  │
│  │                  │  │  - Search      │  │                │  │
│  └──────────────────┘  └────────────────┘  └────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Motivation:**

Clear separation of concerns:
1. **Local MCP**: Handles binary-to-text conversion locally (addresses MCP text-only limitation)
2. **Remote RAG API**: Core business logic (chunking, embedding, search) as HTTP REST API
3. **Remote RAG MCP**: Protocol adapter exposing API functionality as MCP tools for AI assistants

### Contained Building Blocks

| Building Block | Responsibility | Technology |
|----------------|----------------|------------|
| **Local MCP Server** | Convert local binary documents to text; optionally POST to Remote RAG API | Python 3.11+, markitdown, MCP SDK |
| **Remote RAG API** | Accept text/URLs, chunk documents, generate embeddings, store in Qdrant, perform semantic search | Python 3.11+, FastAPI, LangChain, openai, qdrant-client |
| **Remote RAG MCP Server** | Expose RAG functionality as MCP tools; translate MCP calls to HTTP API calls | Python 3.11+, MCP SDK, httpx |
| **Qdrant Vector DB** | Store document embeddings and metadata; perform vector similarity search | Qdrant (existing instance) |
| **Azure OpenAI** | Generate text embeddings (text-embedding-3-small, 1536 dimensions) | Azure OpenAI Service |

### Important Interfaces

**Interface: Local MCP → Remote RAG API**
- **Protocol**: HTTP REST (JSON)
- **Authentication**: `Authorization: Bearer <RAG_API_KEY>`
- **Endpoint**: `POST /api/v1/ingest`
- **Payload**: `{text: string, metadata: {filename, collection, source}}`

**Interface: Remote RAG MCP → Remote RAG API**
- **Protocol**: HTTP REST (JSON) - localhost within container
- **Authentication**: `Authorization: Bearer <RAG_API_KEY>` (shared secret)
- **Endpoints**: All `/api/v1/*` endpoints

**Interface: Remote RAG API → Qdrant**
- **Protocol**: Qdrant gRPC/HTTP client (async)
- **Authentication**: API key in client initialization
- **Operations**: Insert vectors, search, create collections, retrieve points

**Interface: Remote RAG API → Azure OpenAI**
- **Protocol**: Azure OpenAI REST API (async)
- **Authentication**: Azure API key
- **Operation**: Batch embedding generation

---

## Level 2: Component Details

### Local MCP Server

**Purpose:** Convert local binary documents to text using markitdown; optionally ingest to remote system

**Architecture:**

```python
# MCP Tools
@mcp.tool()
async def convert_to_text(uri: str) -> str:
    """Convert local document to text"""
    # 1. Validate file exists
    # 2. Call markitdown.convert(uri)
    # 3. Return text content

@mcp.tool()
async def convert_and_ingest(uri: str, collection: str = "default") -> dict:
    """Convert document and POST to Remote RAG API"""
    # 1. Convert to text (reuse convert_to_text logic)
    # 2. Prepare metadata (filename, source="local")
    # 3. POST to RAG_API_URL/api/v1/ingest
    # 4. Return {status, doc_id, chunks}
```

**Technology Stack:**
- **markitdown**: Document conversion (PDF, DOCX, XLSX, PPTX, images, HTML, CSV, JSON, XML)
- **httpx**: Async HTTP client for API calls
- **MCP SDK**: Anthropic's Python MCP SDK

**Configuration:**
- `RAG_API_URL`: Remote RAG API endpoint
- `RAG_API_KEY`: Authentication token

**Directory Structure:**
```
local-mcp-server/
├── pyproject.toml
├── src/
│   └── local_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP server entrypoint
│       ├── converter.py       # markitdown wrapper
│       └── ingest_client.py   # HTTP client for Remote RAG API
└── tests/
```

---

### Remote RAG API

**Purpose:** Core RAG business logic - chunking, embedding, storage, search

**Architecture:**

```python
# FastAPI Application Structure

# API Endpoints
@app.post("/api/v1/ingest")
async def ingest_text(request: IngestRequest):
    """
    1. Validate request (text, metadata)
    2. Chunk text using RecursiveCharacterTextSplitter
    3. Generate embeddings (batch to Azure OpenAI)
    4. Store in Qdrant with metadata
    5. Return {status, doc_id, chunks}
    """

@app.post("/api/v1/ingest_url")
async def ingest_url(request: IngestURLRequest):
    """
    1. Fetch URL using httpx
    2. Convert to text using markitdown
    3. Call ingest_text() logic
    """

@app.post("/api/v1/search")
async def search(request: SearchRequest):
    """
    1. Generate query embedding (Azure OpenAI)
    2. Search Qdrant collection
    3. Return top_k results with scores and metadata
    """

@app.get("/api/v1/collections")
async def list_collections():
    """Query Qdrant for all collections"""

@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str):
    """Retrieve all chunks for a document from Qdrant"""

@app.get("/health")
async def health():
    """Health check (no auth required)"""
```

**Technology Stack:**
- **FastAPI 0.119+**: Async web framework (latest stable: 0.119.0, Oct 2025)
- **LangChain 1.0+**: RecursiveCharacterTextSplitter (latest stable: 1.0.0, Oct 2025)
  - ⚠️ **Breaking Changes**: LangChain 1.0.0 is a major release - review migration guide during implementation
- **openai 2.5+**: Azure OpenAI client (async) (latest stable: 2.5.0, Oct 2025)
  - ⚠️ **Breaking Changes**: OpenAI v2.x has breaking changes from v1.x - verify Azure OpenAI compatibility
- **qdrant-client 1.15+**: Async Qdrant client (latest stable: 1.15.1, Jul 2025)
- **httpx 0.28+**: Async HTTP client for URL fetching (latest stable: 0.28.1)
- **markitdown 0.1.3**: Document conversion for URLs (Microsoft library, early release, Aug 2025)
- **pydantic**: Request/response validation (bundled with FastAPI)

**Configuration:**
- `QDRANT_URL`: Qdrant endpoint
- `QDRANT_API_KEY`: Qdrant authentication
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI key
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Deployment name (e.g., "text-embedding-3-small")
- `RAG_API_KEY`: API key for client authentication
- `CHUNK_SIZE`: Default 512 tokens
- `CHUNK_OVERLAP`: Default 50 tokens

**Directory Structure:**
```
remote-rag-server/
├── Dockerfile
├── pyproject.toml
├── src/
│   └── rag_server/
│       ├── __init__.py
│       ├── main.py              # FastAPI app + MCP server runner
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py        # API endpoints
│       │   ├── models.py        # Pydantic models
│       │   └── auth.py          # API key authentication
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py        # MCP tools (calls API via HTTP)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── chunker.py       # RecursiveCharacterTextSplitter
│       │   ├── embedder.py      # Azure OpenAI embedding service
│       │   ├── qdrant_service.py # Qdrant operations
│       │   └── converter.py     # markitdown for URLs
│       └── config.py            # Environment config
├── openshift/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── route.yaml
│   ├── configmap.yaml
│   └── secret.yaml
└── tests/
```

---

### Remote RAG MCP Server

**Purpose:** Expose Remote RAG API as MCP tools for AI assistants

**Architecture:**

```python
# MCP Tools (thin wrappers around HTTP API calls)

@mcp.tool()
async def search(query: str, collection: str = "default", top_k: int = 5):
    """Semantic search via Remote RAG API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RAG_API_URL}/api/v1/search",
            headers={"Authorization": f"Bearer {RAG_API_KEY}"},
            json={"query": query, "collection": collection, "top_k": top_k}
        )
        return response.json()

@mcp.tool()
async def ingest_url(uri: str, collection: str = "default"):
    """Ingest HTTPS document via Remote RAG API"""
    # Similar pattern: POST to /api/v1/ingest_url

@mcp.tool()
async def list_collections():
    """List all collections via Remote RAG API"""
    # GET /api/v1/collections

@mcp.tool()
async def get_document(doc_id: str):
    """Retrieve document by ID via Remote RAG API"""
    # GET /api/v1/documents/{doc_id}
```

**Technology Stack:**
- **MCP SDK**: Anthropic's Python MCP SDK
- **httpx**: Async HTTP client

**Configuration:**
- `RAG_API_URL`: `http://localhost:8000` (same container)
- `RAG_API_KEY`: Shared with Remote RAG API

**Integration:**
- Runs in same container as Remote RAG API
- Started via process manager (supervisord) or main.py script that starts both FastAPI and MCP server

---

# Runtime View

## Scenario 1: Local Document Ingestion

**User Action:** Developer uses AI assistant to ingest a local PDF

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────┐
│ AI       │      │ Local MCP    │      │ Remote RAG   │      │ Qdrant │
│ Assistant│      │ Server       │      │ API          │      │        │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬───┘
     │                   │                     │                   │
     │ convert_and_      │                     │                   │
     │ ingest()          │                     │                   │
     ├──────────────────>│                     │                   │
     │                   │                     │                   │
     │                   │ 1. Read file        │                   │
     │                   │ 2. markitdown       │                   │
     │                   │    convert()        │                   │
     │                   │                     │                   │
     │                   │ POST /api/v1/ingest │                   │
     │                   ├────────────────────>│                   │
     │                   │ {text, metadata}    │                   │
     │                   │                     │                   │
     │                   │                     │ 3. Chunk text     │
     │                   │                     │ 4. Generate       │
     │                   │                     │    embeddings     │
     │                   │                     │    (Azure OpenAI) │
     │                   │                     │                   │
     │                   │                     │ 5. Store vectors  │
     │                   │                     ├──────────────────>│
     │                   │                     │                   │
     │                   │                     │ 6. Return status  │
     │                   │ {doc_id, chunks}    │<──────────────────┤
     │                   │<────────────────────┤                   │
     │                   │                     │                   │
     │ Success response  │                     │                   │
     │<──────────────────┤                     │                   │
     │                   │                     │                   │
```

**Steps:**
1. AI assistant calls Local MCP `convert_and_ingest(uri="file:///docs/manual.pdf", collection="project-alpha")`
2. Local MCP reads file and converts to text using markitdown
3. Local MCP POSTs text to Remote RAG API `/api/v1/ingest`
4. Remote RAG API chunks text using RecursiveCharacterTextSplitter
5. Remote RAG API generates embeddings via Azure OpenAI (batch)
6. Remote RAG API stores vectors in Qdrant collection "project-alpha"
7. Remote RAG API returns `{status: "success", doc_id: "abc123", chunks: 15}`
8. Local MCP forwards response to AI assistant

---

## Scenario 2: Semantic Search

**User Action:** Developer asks AI assistant "What's the authentication approach?"

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────┐
│ AI       │      │ Remote RAG   │      │ Remote RAG   │      │ Qdrant │
│ Assistant│      │ MCP Server   │      │ API          │      │        │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬───┘
     │                   │                     │                   │
     │ search()          │                     │                   │
     ├──────────────────>│                     │                   │
     │                   │                     │                   │
     │                   │ POST /api/v1/search │                   │
     │                   ├────────────────────>│                   │
     │                   │ {query, collection} │                   │
     │                   │                     │                   │
     │                   │                     │ 1. Generate query │
     │                   │                     │    embedding      │
     │                   │                     │    (Azure OpenAI) │
     │                   │                     │                   │
     │                   │                     │ 2. Vector search  │
     │                   │                     ├──────────────────>│
     │                   │                     │                   │
     │                   │                     │ 3. Top-k results  │
     │                   │ {results}           │<──────────────────┤
     │                   │<────────────────────┤                   │
     │                   │                     │                   │
     │ Search results    │                     │                   │
     │<──────────────────┤                     │                   │
     │                   │                     │                   │
```

**Steps:**
1. AI assistant calls Remote RAG MCP `search(query="authentication approach", collection="default", top_k=5)`
2. Remote RAG MCP POSTs to Remote RAG API `/api/v1/search` (localhost HTTP)
3. Remote RAG API generates query embedding via Azure OpenAI
4. Remote RAG API searches Qdrant collection "default" with embedding vector
5. Qdrant returns top 5 similar chunks with scores
6. Remote RAG API formats results with text, scores, metadata
7. Remote RAG MCP forwards results to AI assistant
8. AI assistant synthesizes answer from search results

---

## Scenario 3: URL Document Ingestion

**User Action:** Developer asks AI assistant to ingest a web page

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────┐
│ AI       │      │ Remote RAG   │      │ Remote RAG   │      │ Qdrant │
│ Assistant│      │ MCP Server   │      │ API          │      │        │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬───┘
     │                   │                     │                   │
     │ ingest_url()      │                     │                   │
     ├──────────────────>│                     │                   │
     │                   │                     │                   │
     │                   │ POST /api/v1/       │                   │
     │                   │ ingest_url          │                   │
     │                   ├────────────────────>│                   │
     │                   │ {url, collection}   │                   │
     │                   │                     │                   │
     │                   │                     │ 1. Fetch URL      │
     │                   │                     │    (httpx)        │
     │                   │                     │ 2. Convert to text│
     │                   │                     │    (markitdown)   │
     │                   │                     │ 3. Chunk, embed   │
     │                   │                     │ 4. Store          │
     │                   │                     ├──────────────────>│
     │                   │                     │                   │
     │                   │ {doc_id, chunks}    │                   │
     │                   │<────────────────────┤                   │
     │                   │                     │                   │
     │ Success           │                     │                   │
     │<──────────────────┤                     │                   │
     │                   │                     │                   │
```

**Steps:**
1. AI assistant calls Remote RAG MCP `ingest_url(uri="https://docs.example.com/auth.html", collection="docs")`
2. Remote RAG MCP POSTs to Remote RAG API `/api/v1/ingest_url`
3. Remote RAG API fetches URL content using httpx
4. Remote RAG API converts HTML to text using markitdown
5. Remote RAG API follows standard ingestion pipeline (chunk, embed, store)
6. Returns `{status: "success", doc_id: "xyz789", chunks: 8}`

---

# Deployment View

## Infrastructure Level 1

### OpenShift Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      OpenShift Cluster                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Namespace: rag-system                                     │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Deployment: rag-server                              │ │ │
│  │  │  Replicas: 1 (can scale to 2-3 for HA)               │ │ │
│  │  │                                                      │ │ │
│  │  │  ┌────────────────────────────────────────────────┐ │ │ │
│  │  │  │  Pod: rag-server-xxxxx                         │ │ │ │
│  │  │  │                                                │ │ │ │
│  │  │  │  ┌──────────────────────────────────────────┐ │ │ │ │
│  │  │  │  │  Container: rag-server                   │ │ │ │ │
│  │  │  │  │  Image: rag-server:1.0                   │ │ │ │ │
│  │  │  │  │  Ports: 8000 (FastAPI), 8001 (MCP HTTP)  │ │ │ │ │
│  │  │  │  │                                          │ │ │ │ │
│  │  │  │  │  Process 1: FastAPI (port 8000)          │ │ │ │ │
│  │  │  │  │  Process 2: MCP Server (port 8001)       │ │ │ │ │
│  │  │  │  │                                          │ │ │ │ │
│  │  │  │  │  Resources:                              │ │ │ │ │
│  │  │  │  │    CPU: 500m-2000m                       │ │ │ │ │
│  │  │  │  │    Memory: 1Gi-4Gi                       │ │ │ │ │
│  │  │  │  └──────────────────────────────────────────┘ │ │ │ │
│  │  │  │                                                │ │ │ │
│  │  │  │  Environment (ConfigMap + Secret):             │ │ │ │
│  │  │  │  - QDRANT_URL                                  │ │ │ │
│  │  │  │  - QDRANT_API_KEY (secret)                     │ │ │ │
│  │  │  │  - AZURE_OPENAI_ENDPOINT                       │ │ │ │
│  │  │  │  - AZURE_OPENAI_KEY (secret)                   │ │ │ │
│  │  │  │  - AZURE_OPENAI_EMBEDDING_DEPLOYMENT           │ │ │ │
│  │  │  │  - RAG_API_KEY (secret)                        │ │ │ │
│  │  │  └────────────────────────────────────────────────┘ │ │ │
│  │  │                                                      │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Service: rag-server-service                         │ │ │
│  │  │  Type: ClusterIP                                     │ │ │
│  │  │  Ports:                                              │ │ │
│  │  │    - 8000 → FastAPI                                  │ │ │
│  │  │    - 8001 → MCP HTTP                                 │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Route: rag-api-route                                │ │ │
│  │  │  Host: rag-api.apps.openshift.example.com            │ │ │
│  │  │  Target: rag-server-service:8000                     │ │ │
│  │  │  TLS: Edge termination                               │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Route: rag-mcp-route                                │ │ │
│  │  │  Host: rag-mcp.apps.openshift.example.com            │ │ │
│  │  │  Target: rag-server-service:8001                     │ │ │
│  │  │  TLS: Edge termination                               │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Existing: Qdrant Service                                  │ │
│  │  Endpoint: qdrant.rag-system.svc.cluster.local:6333        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Dockerfile Structure

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# Copy application code
COPY src/ ./src/

# Expose ports
EXPOSE 8000 8001

# Start both FastAPI and MCP server
CMD ["python", "-m", "rag_server.main"]
```

### Main Entrypoint (`main.py`)

```python
import asyncio
import uvicorn
from fastapi import FastAPI
from mcp import Server as MCPServer

async def run_fastapi():
    """Run FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def run_mcp_server():
    """Run MCP server"""
    # MCP server initialization
    # Listen on HTTP port 8001 or stdio

async def main():
    """Run both servers concurrently"""
    await asyncio.gather(
        run_fastapi(),
        run_mcp_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

# Cross-cutting Concepts

## Document Chunking Strategy

**Approach:** LangChain RecursiveCharacterTextSplitter

**Configuration:**
- `chunk_size`: 512 tokens (~2000 characters)
- `chunk_overlap`: 50 tokens (~200 characters)
- Separators: `["\n\n", "\n", " ", ""]` (paragraph → sentence → word → character)

**Rationale:**
- Preserves semantic boundaries (paragraphs, sentences)
- Overlap ensures context is not lost at chunk boundaries
- Token-based sizing aligns with embedding model limits (text-embedding-3-small supports 8191 tokens)

**Future Extensibility:**
- **Graph RAG**: Chunks preserve document structure for entity extraction
- **Hybrid RAG**: Semantic chunks work well with BM25 keyword search

**Implementation:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,  # Can switch to token counter
    separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_text(document_text)
```

---

## Embedding and Vector Storage

**Embedding Model:** Azure OpenAI text-embedding-3-small
- **Dimensions:** 1536
- **Cost:** $0.02 per 1M tokens (very affordable)
- **Performance:** Fast, accurate for semantic search

**Batch Processing:**
- Embed chunks in batches of 16-32 to optimize API calls
- Async calls to Azure OpenAI for parallel processing

**Qdrant Schema:**

```python
# Collection Structure
collection_name = "project-alpha"  # User-defined or "default"

# Point Schema
{
    "id": "uuid",
    "vector": [1536 dimensions],
    "payload": {
        "doc_id": "abc123",          # Document identifier
        "chunk_index": 0,            # Chunk position in document
        "text": "chunk content...",  # Original text chunk
        "metadata": {
            "filename": "manual.pdf",
            "source": "local",       # "local" or "url"
            "collection": "project-alpha",
            "ingested_at": "2025-10-19T10:30:00Z",
            "page": 5,               # Optional: page number
            "url": null              # Original URL if source="url"
        }
    }
}
```

**Index Configuration:**
- **Distance Metric:** Cosine similarity (standard for text embeddings)
- **HNSW Parameters:** Default (can tune for performance)

---

## Authentication and Security

**API Key Authentication:**
- All Remote RAG API endpoints (except `/health`) require `Authorization: Bearer <API_KEY>`
- API key stored in OpenShift Secret
- FastAPI dependency injection for auth validation

**Implementation:**
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != RAG_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

@app.post("/api/v1/search", dependencies=[Depends(verify_api_key)])
async def search(request: SearchRequest):
    ...
```

**Future Enhancements (Out of Scope for MVP):**
- OAuth 2.0 / SSO integration
- Role-based access control (RBAC)
- Audit logging
- Rate limiting per API key

---

## Error Handling and Logging

**Error Response Format:**
```json
{
    "error": "DocumentConversionError",
    "detail": "Failed to convert PDF: file is encrypted",
    "status_code": 400,
    "timestamp": "2025-10-19T10:30:00Z"
}
```

**Logging Strategy:**
- **Format:** JSON-structured logs for OpenShift log aggregation
- **Levels:** DEBUG (development), INFO (production)
- **Content:**
  - Request ID (UUID for tracing)
  - Endpoint, method, status code
  - Latency (ms)
  - Error details (if applicable)

**Logged Events:**
- Document ingestion (doc_id, filename, collection, chunks, latency)
- Search queries (query text, collection, results count, latency)
- Authentication failures
- External service errors (Qdrant, Azure OpenAI)

**Implementation:**
```python
import logging
import structlog

logger = structlog.get_logger()

@app.post("/api/v1/ingest")
async def ingest_text(request: IngestRequest):
    request_id = str(uuid.uuid4())
    logger.info("ingest_request", request_id=request_id, collection=request.metadata.collection)

    try:
        # ... ingestion logic
        logger.info("ingest_success", request_id=request_id, doc_id=doc_id, chunks=len(chunks))
    except Exception as e:
        logger.error("ingest_failed", request_id=request_id, error=str(e))
        raise
```

---

## Configuration Management

**12-Factor App Principles:**
- All configuration via environment variables
- No hardcoded secrets
- Environment-specific configs (dev, staging, production)

**Environment Variables:**

| Variable | Component | Description | Example |
|----------|-----------|-------------|---------|
| `RAG_API_URL` | Local MCP, Remote MCP | Remote RAG API endpoint | `https://rag-api.example.com` |
| `RAG_API_KEY` | All | API key for authentication | `sk-abc123...` |
| `QDRANT_URL` | Remote RAG API | Qdrant endpoint | `http://qdrant:6333` |
| `QDRANT_API_KEY` | Remote RAG API | Qdrant authentication | `qdrant-key-xyz` |
| `AZURE_OPENAI_ENDPOINT` | Remote RAG API | Azure OpenAI endpoint | `https://example.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Remote RAG API | Azure OpenAI key | `azure-key-123` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Remote RAG API | Deployment name | `text-embedding-3-small` |
| `CHUNK_SIZE` | Remote RAG API | Chunking size (tokens) | `512` |
| `CHUNK_OVERLAP` | Remote RAG API | Chunking overlap (tokens) | `50` |
| `LOG_LEVEL` | All | Logging level | `INFO` |

**OpenShift ConfigMap & Secret:**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
data:
  QDRANT_URL: "http://qdrant.rag-system.svc.cluster.local:6333"
  AZURE_OPENAI_ENDPOINT: "https://example.openai.azure.com/"
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT: "text-embedding-3-small"
  CHUNK_SIZE: "512"
  CHUNK_OVERLAP: "50"
  LOG_LEVEL: "INFO"

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
type: Opaque
stringData:
  RAG_API_KEY: "sk-abc123..."
  QDRANT_API_KEY: "qdrant-key-xyz"
  AZURE_OPENAI_KEY: "azure-key-123"
```

---

# Architecture Decisions

## ADR-001: Async Python Stack

**Context:** Remote RAG API handles IO-bound workload (Qdrant, Azure OpenAI, HTTP)

**Decision:** Use async throughout (FastAPI, qdrant-client, openai, httpx)

**Status:** Accepted

**Consequences:**
- **Positive:** Better performance, scales to 1000 queries/day easily, efficient resource usage
- **Negative:** Slightly more complex code (async/await), requires Python 3.11+
- **Mitigation:** FastAPI and modern Python make async natural

---

## ADR-002: RecursiveCharacterTextSplitter for Chunking

**Context:** Need chunking strategy that balances quality and extensibility

**Decision:** Use LangChain RecursiveCharacterTextSplitter (512 tokens, 50 overlap)

**Status:** Accepted

**Alternatives Considered:**
- Fixed-size chunking: Rejected (breaks semantic boundaries)
- Advanced semantic chunking with LLM: Deferred (too expensive for MVP)

**Consequences:**
- **Positive:** Preserves semantic boundaries, proven in production, extensible to Graph/Hybrid RAG
- **Negative:** Slightly slower than fixed-size (negligible)

---

## ADR-003: Single Container Deployment (Remote Components)

**Context:** Remote RAG API and Remote RAG MCP can be deployed separately or together

**Decision:** Single Docker container running both FastAPI and MCP server

**Status:** Accepted

**Alternatives Considered:**
- Separate containers: Deferred (can split later if needed)

**Consequences:**
- **Positive:** Simpler deployment, no network overhead, easier debugging
- **Negative:** Cannot scale FastAPI and MCP independently
- **Mitigation:** 1000 queries/day doesn't require separate scaling; can refactor later

---

## ADR-004: Hybrid Collection Strategy

**Context:** How to organize documents in Qdrant

**Decision:** Support "default" collection + user-defined collections

**Status:** Accepted

**Alternatives Considered:**
- Single collection with metadata filtering: Rejected (less isolation, harder to manage)
- Only user-defined collections: Rejected (poor UX for simple use cases)

**Consequences:**
- **Positive:** Flexibility for users, simple default for beginners, scoped search
- **Negative:** More Qdrant collections to manage
- **Mitigation:** Collections are lightweight in Qdrant

---

## ADR-005: Build New Local MCP (Not Fork markitdown-mcp)

**Context:** Local MCP can fork existing markitdown-mcp or build from scratch

**Decision:** Build new MCP server using markitdown library

**Status:** Accepted

**Alternatives Considered:**
- Fork markitdown-mcp: Rejected (maintenance burden, our requirements differ)

**Consequences:**
- **Positive:** Full control, cleaner implementation, no upstream dependencies
- **Negative:** More initial work
- **Mitigation:** Local MCP is thin wrapper (~200 lines of code)

---

## ADR-006: Library Versions and Breaking Changes

**Context:** Need to specify library versions for reproducible builds

**Decision:** Use latest stable versions as of October 2025 with awareness of breaking changes

**Status:** Accepted

**Library Versions (Verified October 2025):**
- FastAPI 0.119+ (stable, minor updates)
- LangChain 1.0+ (MAJOR release - breaking changes)
- openai 2.5+ (MAJOR release - breaking changes from v1.x)
- qdrant-client 1.15+ (stable, minor updates)
- httpx 0.28+ (stable, minor updates)
- markitdown 0.1.3 (early release, Microsoft library)

**Breaking Changes to Address During Implementation:**

1. **LangChain 1.0.0** (Released Oct 17, 2025)
   - Major milestone release with breaking API changes
   - RecursiveCharacterTextSplitter may have updated import paths
   - Review migration guide: https://python.langchain.com/docs/versions/v0_2/migrating_chains/
   - **Action**: Test RecursiveCharacterTextSplitter compatibility during implementation

2. **OpenAI 2.5.0** (Released Oct 17, 2025)
   - Breaking changes from v1.x to v2.x
   - Azure OpenAI client may have different initialization
   - Async API patterns may have changed
   - **Action**: Verify Azure OpenAI embedding generation works with v2.x API
   - **Fallback**: Consider pinning to openai<2.0 if Azure compatibility issues arise

3. **markitdown 0.1.3** (Released Aug 26, 2025)
   - Early release (0.1.x) - API may not be stable
   - Limited production usage history
   - **Action**: Monitor for updates; be prepared for API changes
   - **Mitigation**: Thin wrapper around markitdown to isolate changes

**Consequences:**
- **Positive:** Use latest features, bug fixes, security patches
- **Negative:** Potential breaking changes require implementation testing
- **Mitigation:** Pin exact versions in requirements.txt/pyproject.toml during development

**Version Pinning Strategy:**
- Development: Pin exact versions (e.g., `langchain==1.0.0`)
- Production: Pin major.minor (e.g., `langchain>=1.0,<1.1`)
- Security: Regular dependency updates with testing

---

# Quality Requirements

## Quality Tree

```
Quality
├── Performance
│   ├── Search latency <3s (95th percentile)
│   └── Ingestion throughput: 100 docs/day
├── Reliability
│   ├── 99% uptime during business hours
│   └── Graceful degradation (Azure OpenAI outage → fallback)
├── Maintainability
│   ├── Clear separation of concerns (Local MCP, API, MCP wrapper)
│   ├── Comprehensive logging (request tracing)
│   └── Environment-based configuration
├── Extensibility
│   ├── Future: Graph RAG support
│   ├── Future: Hybrid RAG (BM25 + vector)
│   └── Future: Multi-modal (images)
├── Security
│   ├── API key authentication
│   └── TLS encryption (OpenShift Route)
└── Usability
    ├── Simple MCP interface (5 tools)
    └── Helpful error messages
```

## Quality Scenarios

### Performance: Search Latency

**Scenario:** Developer performs semantic search during active development

**Stimulus:** AI assistant calls `search(query="...", collection="default", top_k=5)`

**Response:** System returns results in <3 seconds (95th percentile)

**Measured by:**
- Latency logging in Remote RAG API
- OpenShift monitoring dashboards

**Architectural tactics:**
- Async Azure OpenAI calls (non-blocking)
- Qdrant HNSW index (fast approximate search)
- Batch embedding generation

---

### Extensibility: Graph RAG Support

**Scenario:** Team wants to add entity extraction for Graph RAG

**Stimulus:** New requirement to extract entities and relationships from chunks

**Response:** Add entity extraction service without major refactoring

**Architectural support:**
- RecursiveCharacterTextSplitter preserves document structure
- Qdrant payload stores full text chunks (can process retroactively)
- Modular services architecture (add `graph_service.py`)

---

### Reliability: Azure OpenAI Outage

**Scenario:** Azure OpenAI service is down (5-minute outage)

**Stimulus:** Embedding generation requests fail

**Response:** System returns clear error message; search queries fail gracefully; ingestion is queued for retry

**Architectural tactics:**
- Exponential backoff for Azure OpenAI calls
- Circuit breaker pattern (future enhancement)
- Health check endpoint reports degraded state

---

# Risks and Technical Debts

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **LangChain 1.0 Breaking Changes** | High | Medium | Test RecursiveCharacterTextSplitter during implementation; review migration guide; fallback to 0.3.x if needed |
| **OpenAI 2.x Azure Compatibility** | Medium | High | Verify Azure OpenAI embeddings work with v2.x; consider pinning to openai<2.0 if issues arise |
| **Azure OpenAI Rate Limits** | Medium | High | Implement exponential backoff, request batching; monitor TPM usage |
| **Qdrant Performance Degradation** | Low | Medium | Monitor query latency; tune HNSW parameters; consider sharding at 50k+ docs |
| **Single Container SPOF** | Medium | Medium | Deploy 2+ replicas in OpenShift; add health checks; implement graceful shutdown |
| **Large Document Memory Issues** | Low | Medium | Stream large documents instead of loading fully; set max file size limit (50MB) |
| **Embedding Cost Overrun** | Low | Low | Monitor Azure OpenAI usage; set budget alerts; text-embedding-3-small is very cheap |
| **markitdown API Instability** | Low | Low | Wrap markitdown in thin adapter layer to isolate changes; monitor for 0.2.x releases |

## Technical Debts

| Debt | Priority | Rationale | Remediation Plan |
|------|----------|-----------|------------------|
| **No Document Deletion API** | Low | Out of scope for MVP | Add `DELETE /api/v1/documents/{id}` in Phase 2 |
| **No Hybrid Search (BM25)** | Medium | Deferred for simplicity | Add BM25 index alongside vector search in Phase 2 |
| **Simple API Key Auth** | Medium | MVP security is minimal | Replace with OAuth 2.0 / SSO in Phase 2 |
| **No Circuit Breaker** | Medium | External service failures cascade | Add resilience4j or similar in Phase 2 |
| **No Rate Limiting** | Low | Internal users only | Add per-user rate limiting if needed in Phase 2 |

---

# Glossary

| Term | Definition |
|------|------------|
| **MCP (Model Context Protocol)** | Anthropic's protocol for AI assistants to interact with external tools and data sources via JSON-RPC |
| **RAG (Retrieval-Augmented Generation)** | Architecture pattern where LLMs retrieve relevant context from external knowledge base before generating responses |
| **Graph RAG** | Extension of RAG that extracts entities and relationships to build knowledge graphs for improved retrieval |
| **Hybrid RAG** | Combination of keyword search (BM25) and semantic search (vector embeddings) for better recall |
| **Embedding** | Dense vector representation of text (1536 dimensions for text-embedding-3-small) capturing semantic meaning |
| **Chunking** | Process of splitting long documents into smaller segments for embedding and retrieval |
| **Qdrant** | Open-source vector database optimized for similarity search and filtering |
| **HNSW** | Hierarchical Navigable Small World - graph-based algorithm for fast approximate nearest neighbor search |
| **Azure OpenAI** | Microsoft's managed service providing OpenAI models (GPT, embeddings) with enterprise security |
| **RecursiveCharacterTextSplitter** | LangChain component that splits text at semantic boundaries (paragraphs, sentences) |
| **Collection** | Isolated set of vectors in Qdrant (analogous to database table) |
| **Payload** | Metadata stored alongside vectors in Qdrant (text, filename, source, etc.) |
| **Cosine Similarity** | Distance metric measuring angle between vectors (1 = identical, 0 = orthogonal, -1 = opposite) |
| **Top-k Search** | Retrieve k most similar vectors to query vector |
| **markitdown** | Microsoft library for converting various document formats (PDF, DOCX, etc.) to Markdown |

---

*End of Architecture Documentation*
