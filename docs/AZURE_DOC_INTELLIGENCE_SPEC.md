# Azure Document Intelligence MCP Server Specification

**Version:** 2.0 (Revised - Standalone MVP)
**Date:** 2025-10-26
**Status:** Draft for Review

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Background](#background)
3. [Goals and Non-Goals](#goals-and-non-goals)
4. [Architecture Overview](#architecture-overview)
5. [Component Design](#component-design)
6. [Data Models](#data-models)
7. [MCP Tool Definitions](#mcp-tool-definitions)
8. [Configuration](#configuration)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Phases](#implementation-phases)
11. [Open Questions](#open-questions)

---

## 1. Executive Summary

This specification defines a **NEW standalone local MCP server** for reading and searching documents using **Azure Document Intelligence RAG**. This is a simple MVP that operates independently from the existing Qdrant-based MCP system.

### Key Principles
- **Standalone Server**: Completely separate from existing local-mcp-server and remote-rag-server
- **Local Only**: No remote API component - everything runs locally
- **Simple MVP**: Read-only search functionality (no ingestion in Phase 1)
- **Direct Azure Integration**: Direct calls to Azure Document Intelligence and Azure AI Search
- **Minimal Dependencies**: Only essential libraries for MVP

### What This Is
A lightweight local MCP server that:
1. Connects to **existing** Azure AI Search indexes (pre-populated with documents)
2. Performs hybrid search against those indexes
3. Retrieves document chunks with semantic understanding
4. Simple, focused, easy to use

### What This Is NOT
- Not an extension of existing MCP servers
- Not a replacement for Qdrant MCP
- Not a full document ingestion pipeline (MVP focuses on search/read)

---

## 2. Background

### Current System Architecture

The existing system has:

1. **Local MCP Server** (`local-mcp-server/`)
   - Document conversion using markitdown
   - Sends documents to Remote RAG API (Qdrant-based)

2. **Remote RAG Server** (`remote-rag-server/`)
   - FastAPI REST API
   - Uses Qdrant for vector storage
   - Character-based chunking (LangChain)
   - Azure OpenAI embeddings

### Why a Separate Azure Document Intelligence MCP?

The existing system uses Qdrant for vector search with character-based chunking. Azure Document Intelligence offers a **different approach** that warrants a separate, focused MCP server:

1. **Semantic Document Understanding**
   - Layout-aware parsing (tables, paragraphs, sections)
   - Preserves document structure
   - Better for complex documents (reports, forms, invoices)

2. **Hybrid Search**
   - Combines vector similarity + keyword matching + semantic ranking
   - More robust than pure vector search
   - Better handles specific terms and phrases

3. **Pre-Existing Indexes**
   - You already have Azure AI Search indexes populated
   - Need simple way to query them from AI assistants
   - No need for complex ingestion pipeline initially

4. **Independence**
   - Different use case than Qdrant (structured docs vs simple text)
   - Separate lifecycle and deployment
   - Simpler to understand and maintain

---

## 3. Goals and Non-Goals

### Goals (MVP)

1. **Create Simple Standalone MCP Server**
   - New directory: `docint-mcp-server/`
   - Direct Azure AI Search integration
   - Read-only operations (search, retrieve)
   - Fast startup, minimal dependencies

2. **Essential Search Capabilities**
   - Hybrid search in Azure AI Search indexes
   - List available indexes
   - Retrieve specific documents by ID
   - Simple, intuitive MCP tools

3. **MVP Focus**
   - Get it working quickly
   - Prove the concept
   - Enable AI assistants to query existing Azure AI Search indexes
   - Clean, maintainable code

### Non-Goals (MVP)

1. **No Document Ingestion** - Assume indexes are pre-populated (add later if needed)
2. **No Document Intelligence Analysis** - Just search existing indexed content (add later if needed)
3. **No Integration with Existing MCPs** - Completely standalone
4. **No REST API Layer** - Direct Azure SDK calls from MCP server
5. **No Complex Configuration** - Minimal settings, sensible defaults
6. **No Advanced Features** - No filters, facets, or complex queries (MVP only)

### Future Enhancements (Post-MVP)

- Document ingestion with Azure DI analysis
- Semantic chunking and indexing
- Advanced search filters and facets
- Document management operations

---

## 4. Architecture Overview

### 4.1 High-Level Architecture (Simplified MVP)

```
┌─────────────────────────────────────────┐
│         AI Assistant                     │
│      (Claude, GPT, etc.)                 │
└──────────────┬──────────────────────────┘
               │
               │ MCP Protocol
               │
┌──────────────▼───────────────────────────┐
│   Document Intelligence MCP Server       │
│   (docint-mcp-server/)                   │
│                                          │
│   MCP Tools:                             │
│   • search_documents                     │
│   • list_indexes                         │
│   • get_document                         │
│                                          │
│   Components:                            │
│   • AzureSearchClient (simple wrapper)   │
│   • MCP Server (tool handlers)           │
└──────────────┬───────────────────────────┘
               │
               │ Azure SDK (HTTPS)
               │
┌──────────────▼───────────────────────────┐
│   Azure AI Search                        │
│   (Pre-existing, pre-populated)          │
│                                          │
│   Indexes:                               │
│   • your-docs-index                      │
│   • technical-specs-index                │
│   • (other indexes...)                   │
└──────────────────────────────────────────┘
```

### 4.2 Key Design Decisions

1. **No Middle Layer** - MCP server directly calls Azure AI Search SDK
2. **No Document Ingestion** - Assumes indexes already have documents
3. **No Document Intelligence Analysis** - Just search (MVP scope)
4. **Stateless** - No local storage, no caching (keep it simple)
5. **Single Responsibility** - Only search and retrieval

### 4.3 Component Responsibilities

#### Document Intelligence MCP Server
- **Location:** `docint-mcp-server/` (new directory)
- **Purpose:** Provide MCP tools for searching Azure AI Search
- **Components:**
  - `server.py` - MCP server with tool handlers
  - `azure_search_client.py` - Thin wrapper around Azure SDK
  - `config.py` - Configuration management
  - `models.py` - Data classes for search results

#### Azure AI Search
- **Purpose:** Existing search indexes (pre-populated)
- **Responsibility:** Store and search documents
- **Interaction:** Direct SDK calls from MCP server

---

## 5. Component Design

### 5.1 Directory Structure (New Standalone MCP)

```
knowledge-mcp/
├── local-mcp-server/           # Existing (unchanged)
├── remote-rag-server/          # Existing (unchanged)
└── docint-mcp-server/          # NEW: Document Intelligence MCP
    ├── src/
    │   └── docint_mcp/
    │       ├── __init__.py
    │       ├── server.py                # MCP server with 3 tools
    │       ├── azure_search_client.py   # Azure Search wrapper
    │       ├── config.py                # Configuration
    │       └── models.py                # Data models
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py
    │   ├── test_azure_search_client.py  # 20+ tests
    │   └── test_server.py               # 15+ tests
    ├── pyproject.toml           # Dependencies
    ├── README.md                # Usage guide
    ├── .env.example             # Configuration template
    └── .gitignore
```

### 5.2 Core Components

#### 5.2.1 AzureSearchClient (Simple Wrapper)

**Purpose:** Thin wrapper around Azure Search SDK for common operations

**File:** `azure_search_client.py`

**Key Methods:**
```python
class AzureSearchClient:
    """Simple wrapper for Azure AI Search operations."""

    def __init__(self, endpoint: str, credential: str):
        """Initialize with Azure Search endpoint and API key."""
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential

        self.endpoint = endpoint
        self.credential = AzureKeyCredential(credential)

    async def search(
        self,
        index_name: str,
        query: str,
        top: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform simple hybrid search.

        Args:
            index_name: Name of the index to search
            query: Search query string
            top: Number of results to return (default: 5, max: 50)

        Returns:
            List of search results with score, content, and metadata
        """
        pass

    async def get_document(
        self,
        index_name: str,
        document_id: str
    ) -> dict[str, Any] | None:
        """
        Retrieve a specific document by ID.

        Args:
            index_name: Name of the index
            document_id: Document ID

        Returns:
            Document dict or None if not found
        """
        pass

    async def list_indexes(self) -> list[str]:
        """
        List all available indexes.

        Returns:
            List of index names
        """
        pass
```

#### 5.2.2 MCP Server

**Purpose:** MCP server with tool handlers

**File:** `server.py`

**Structure:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import settings
from .azure_search_client import AzureSearchClient

app = Server("docint-mcp-server")
search_client = AzureSearchClient(
    endpoint=settings.azure_search_endpoint,
    credential=settings.azure_search_key
)

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        # Tool definitions (see section 7)
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "search_documents":
        return await handle_search(arguments)
    elif name == "list_indexes":
        return await handle_list_indexes(arguments)
    elif name == "get_document":
        return await handle_get_document(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
```

#### 5.2.3 Configuration

**Purpose:** Simple configuration management

**File:** `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration for Document Intelligence MCP Server."""

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_key: str

    # Optional: Default settings
    default_index_name: str = "default"
    default_top_results: int = 5
    max_top_results: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

#### 5.2.4 Data Models

**Purpose:** Simple data classes for results

**File:** `models.py`

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class SearchResult:
    """Single search result."""
    document_id: str
    score: float
    content: str
    metadata: dict[str, Any]

@dataclass
class SearchResponse:
    """Search response with multiple results."""
    query: str
    results: list[SearchResult]
    total_count: int
    index_name: str
```

---

## 6. Data Models (Simplified)

### 6.1 Search Result

```python
@dataclass
class SearchResult:
    """Single search result from Azure AI Search."""
    document_id: str           # Unique document ID
    score: float              # Search relevance score (0.0-1.0)
    content: str              # Document content/chunk text
    metadata: dict[str, Any]  # Additional metadata (source, title, etc.)
```

### 6.2 Search Response

```python
@dataclass
class SearchResponse:
    """Complete search response."""
    query: str                     # Original search query
    results: list[SearchResult]    # List of results
    total_count: int              # Total results found
    index_name: str               # Index that was searched
```

### 6.3 Document

```python
@dataclass
class Document:
    """Retrieved document."""
    document_id: str
    content: str
    metadata: dict[str, Any]
    index_name: str
```

---

## 7. MCP Tool Definitions

### 7.1 search_documents

**Purpose:** Search for documents in Azure AI Search indexes using hybrid search

**Tool Definition:**
```python
Tool(
    name="search_documents",
    description=(
        "Search for relevant documents in Azure AI Search indexes. "
        "Uses hybrid search (combines keyword and semantic similarity) "
        "to find the most relevant document chunks for your query."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (natural language question or keywords)"
            },
            "index_name": {
                "type": "string",
                "description": "Name of the index to search (default: 'default')",
                "default": "default"
            },
            "top": {
                "type": "integer",
                "description": "Number of results to return (1-50, default: 5)",
                "default": 5,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }
)
```

**Example Usage:**
```json
{
  "query": "What are the security requirements for API access?",
  "index_name": "technical-docs",
  "top": 5
}
```

**Example Response:**
```
Found 5 relevant documents in 'technical-docs':

1. Score: 0.92
   Document ID: doc-1234
   Content: "API security requirements include authentication via API keys..."
   Source: security-policy.pdf

2. Score: 0.87
   Document ID: doc-5678
   Content: "All API endpoints must use HTTPS and require valid..."
   Source: api-guidelines.pdf

...
```

### 7.2 list_indexes

**Purpose:** List all available Azure AI Search indexes

**Tool Definition:**
```python
Tool(
    name="list_indexes",
    description=(
        "List all available Azure AI Search indexes that can be searched. "
        "Returns index names that can be used in search_documents."
    ),
    inputSchema={
        "type": "object",
        "properties": {}
    }
)
```

**Example Response:**
```
Available indexes:
  • default
  • technical-docs
  • product-manuals
  • company-policies
```

### 7.3 get_document

**Purpose:** Retrieve a specific document by ID

**Tool Definition:**
```python
Tool(
    name="get_document",
    description=(
        "Retrieve a specific document by its ID from an Azure AI Search index. "
        "Useful for getting full document details after finding it in search results."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The document ID to retrieve"
            },
            "index_name": {
                "type": "string",
                "description": "Name of the index containing the document (default: 'default')",
                "default": "default"
            }
        },
        "required": ["document_id"]
    }
)
```

**Example Usage:**
```json
{
  "document_id": "doc-1234",
  "index_name": "technical-docs"
}
```

**Example Response:**
```
Document ID: doc-1234
Index: technical-docs
Content: "API security requirements include authentication via API keys, HTTPS for all endpoints..."
Metadata:
  • source: security-policy.pdf
  • title: API Security Requirements
  • last_updated: 2025-01-15
```

---

## 8. Configuration

### 8.1 Environment Variables

**.env file:**
```bash
# Required: Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-admin-or-query-key

# Optional: Default Settings
DEFAULT_INDEX_NAME=default
DEFAULT_TOP_RESULTS=5
MAX_TOP_RESULTS=50
```

### 8.2 Configuration Class

**File:** `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration for Document Intelligence MCP Server."""

    # Required Azure AI Search settings
    azure_search_endpoint: str
    azure_search_key: str

    # Optional defaults
    default_index_name: str = "default"
    default_top_results: int = 5
    max_top_results: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 8.3 Setup Instructions

**Steps to configure:**

1. Create `.env` file in `docint-mcp-server/`:
```bash
cp .env.example .env
```

2. Edit `.env` with your Azure credentials:
   - Get endpoint from Azure Portal → Your Search Service → Overview
   - Get key from Azure Portal → Your Search Service → Keys

3. Verify configuration:
```bash
python -c "from docint_mcp.config import settings; print(settings.azure_search_endpoint)"
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**test_azure_search_client.py** (20+ tests)

**Test Coverage:**
- ✓ Client initialization with valid/invalid credentials
- ✓ Search with various parameters (query, top, index)
- ✓ Search error handling (network errors, invalid index, etc.)
- ✓ Get document by ID (success and not found)
- ✓ List indexes (empty, multiple indexes)
- ✓ Response parsing and data model validation
- ✓ Mock Azure SDK responses

**Target: 20+ tests, 80%+ coverage**

**test_server.py** (15+ tests)
**Test Coverage:**
- ✓ MCP tool registration (list_tools)
- ✓ search_documents tool handler
- ✓ list_indexes tool handler
- ✓ get_document tool handler
- ✓ Error handling for invalid tool names
- ✓ Error handling for missing parameters
- ✓ Response formatting (TextContent)

**Target: 15+ tests, 80%+ coverage**

### 9.2 Integration Tests

**Manual Testing with Real Azure Search:**
- Search actual indexes
- Verify results match expectations
- Test with different query types
- Test edge cases (empty results, large result sets)

### 9.3 Test Fixtures

**conftest.py:**
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_search_client():
    """Mock Azure Search client for testing."""
    client = AsyncMock()
    # Setup mock responses
    return client

@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        {
            "@search.score": 0.92,
            "id": "doc-1",
            "content": "Test content 1",
            "metadata": {"source": "test.pdf"}
        },
        {
            "@search.score": 0.85,
            "id": "doc-2",
            "content": "Test content 2",
            "metadata": {"source": "test2.pdf"}
        }
    ]
```

---

## 10. Implementation Phases

### Phase 1: Basic Setup and Azure Search Client (Week 1, Days 1-2)

**Goal:** Create project structure and implement Azure Search client

**Tasks:**
- [ ] Create `docint-mcp-server/` directory structure
- [ ] Setup `pyproject.toml` with minimal dependencies:
  - `mcp>=1.0.0`
  - `azure-search-documents>=11.4.0`
  - `azure-core>=1.30.0`
  - `pydantic>=2.9.0`
  - `pydantic-settings>=2.6.0`
  - `pytest>=8.3.0` (dev)
  - `pytest-asyncio>=0.24.0` (dev)
  - `pytest-mock>=3.14.0` (dev)
- [ ] Implement `config.py` (configuration management)
- [ ] Implement `models.py` (data classes)
- [ ] Implement `azure_search_client.py`:
  - `__init__` method (initialize Azure SDK)
  - `search()` method
  - `get_document()` method
  - `list_indexes()` method
- [ ] Write unit tests for `azure_search_client.py` (20+ tests)
- [ ] Create `.env.example` template
- [ ] Create basic `README.md`

**Deliverables:**
- Working Azure Search client with 3 methods
- 20+ unit tests passing
- 80%+ coverage on azure_search_client.py

---

### Phase 2: MCP Server Implementation (Week 1, Days 3-4)

**Goal:** Implement MCP server with 3 tools

**Tasks:**
- [ ] Implement `server.py`:
  - Initialize MCP server
  - Register 3 tools (search_documents, list_indexes, get_document)
  - Implement tool handlers
  - Format responses as TextContent
- [ ] Add error handling and user-friendly messages
- [ ] Write unit tests for `server.py` (15+ tests)
- [ ] Test MCP server manually with MCP inspector

**Deliverables:**
- Functional MCP server with 3 tools
- 15+ unit tests passing
- Can be called from AI assistants

---

### Phase 3: Documentation and Polish (Week 1, Day 5)

**Goal:** Complete documentation and prepare for release

**Tasks:**
- [ ] Write comprehensive `README.md`:
  - Quick start guide
  - Configuration instructions
  - Usage examples
  - Troubleshooting
- [ ] Add inline docstrings to all methods
- [ ] Create usage examples
- [ ] Test with real Azure Search indexes
- [ ] Update main project README with new MCP

**Deliverables:**
- Complete documentation
- Tested with real Azure Search
- Ready for use

---

### Phase 4 (Optional - Future): Document Ingestion

**Goal:** Add document ingestion capabilities

**Tasks:**
- [ ] Add Azure Document Intelligence SDK
- [ ] Implement document analysis
- [ ] Implement semantic chunking
- [ ] Add ingestion tool to MCP
- [ ] Write tests for new functionality

**This is OUT OF SCOPE for MVP**

---

## 11. Open Questions for Discussion

### 11.1 Azure Search Index Schema

**Question:** What fields does your Azure AI Search index have?

We need to know the schema to properly access:
- Document ID field name
- Content/text field name
- Metadata fields

**Example schemas:**
```python
# Option A: Simple schema
{
    "id": "document-id",
    "content": "document text...",
    "metadata": {...}
}

# Option B: Rich schema
{
    "id": "document-id",
    "content": "document text...",
    "title": "Document Title",
    "source": "file.pdf",
    "chunk_type": "paragraph",
    "page_number": 1,
    ...
}
```

**Impact:** Affects how we parse search results and display them

---

### 11.2 Search Mode

**Question:** What type of search should be default?

**Options:**
- **Hybrid search** (keyword + vector) - Best for most use cases
- **Keyword only** - Faster, good for exact matches
- **Vector only** - Best for semantic similarity

**Recommendation:** Hybrid search (combines best of both worlds)

---

### 11.3 Result Formatting

**Question:** How should search results be presented to the AI assistant?

**Options:**
- **Option A - Concise:** Just score, ID, and content snippet
- **Option B - Detailed:** Include all metadata, source, page numbers
- **Option C - Configurable:** Let user choose verbosity level

**Recommendation:** Option B (detailed) for MVP - AI can extract what it needs

---

### 11.4 Error Handling

**Question:** How should errors be reported?

**Options:**
- **Option A - Technical:** Full error details for debugging
- **Option B - User-friendly:** Simple messages, hide technical details
- **Option C - Hybrid:** User message + optional technical details

**Recommendation:** Option C (hybrid) - helpful for both users and debugging

---

### 11.5 Index Names

**Question:** What indexes exist in your Azure Search?

We need to know:
- Available index names
- Default index to use
- Whether new indexes will be created or all are pre-existing

**Impact:** Affects validation and default configuration

---

## Appendix A: Dependencies

### Python Package Requirements

**pyproject.toml:**
```toml
[project]
name = "docint-mcp-server"
version = "0.1.0"
description = "MCP server for Azure AI Search document retrieval"
requires-python = ">=3.11"

dependencies = [
    "mcp>=1.0.0",
    "azure-search-documents>=11.4.0",
    "azure-core>=1.30.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Why These Dependencies?

- **mcp**: MCP protocol implementation
- **azure-search-documents**: Official Azure AI Search SDK
- **azure-core**: Core Azure SDK functionality
- **pydantic**: Data validation and settings management
- **pytest ecosystem**: Comprehensive testing
- **ruff**: Fast Python linter
- **mypy**: Static type checking

---

## Appendix B: Quick Start Guide

### Installation

```bash
# Navigate to docint-mcp-server directory
cd docint-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your Azure credentials

# Run tests
pytest -v --cov=docint_mcp

# Start MCP server
python -m docint_mcp.server
```

### Usage with Claude Desktop

**Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "docint": {
      "command": "/path/to/docint-mcp-server/.venv/bin/python",
      "args": ["-m", "docint_mcp.server"],
      "env": {
        "AZURE_SEARCH_ENDPOINT": "https://your-search.search.windows.net",
        "AZURE_SEARCH_KEY": "your-key"
      }
    }
  }
}
```

---

## Appendix C: Comparison with Existing MCP

### Qdrant MCP vs Document Intelligence MCP

| Feature | Local/Remote Qdrant MCP | Document Intelligence MCP |
|---------|-------------------------|---------------------------|
| **Architecture** | Local + Remote API | Standalone local only |
| **Document Processing** | markitdown → LangChain chunking | N/A (reads pre-indexed docs) |
| **Storage** | Qdrant vector database | Azure AI Search indexes |
| **Search Type** | Vector similarity only | Hybrid (keyword + vector) |
| **Chunking** | Character-based (512 chars) | Semantic (pre-chunked in index) |
| **Ingestion** | Yes (via Remote API) | No (MVP - read only) |
| **Use Case** | Simple text documents | Complex structured documents |
| **Complexity** | Higher (multiple components) | Lower (single component) |
| **Setup** | Requires Remote API deployment | Just credentials |

### When to Use Each

**Use Qdrant MCP when:**
- You need to ingest new documents frequently
- Simple text documents
- You control the entire pipeline
- Want character-based chunking

**Use Document Intelligence MCP when:**
- Reading existing Azure AI Search indexes
- Complex documents (tables, forms, layouts)
- Want hybrid search (keyword + vector)
- Simpler setup (no API deployment)
- Documents already indexed in Azure Search

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-26 | Initial specification (unified approach) | AI Assistant |
| 2.0 | 2025-10-26 | Revised to standalone MVP approach | AI Assistant |

---

## Approval Checklist

- [ ] **User Review:** Standalone MVP approach approved
- [ ] **Scope Confirmed:** Read-only search operations (no ingestion in MVP)
- [ ] **Azure Resources:** Index names and schema provided
- [ ] **Open Questions:** All questions answered
- [ ] **Ready for Implementation:** User confirms go-ahead

---

## Next Steps

1. **Review this specification** - Discuss open questions
2. **Confirm approach** - Standalone MVP vs integrated approach
3. **Provide Azure details** - Index names, schema, credentials
4. **Start implementation** - Begin Phase 1 if approved
**Goal:** Implement core Azure Document Intelligence and Azure AI Search services

**Tasks:**
- [ ] Add Azure SDK dependencies to pyproject.toml
  - `azure-ai-documentintelligence==1.0.0b4`
  - `azure-search-documents==11.6.0b4`
- [ ] Extend config.py with Azure DI settings
- [ ] Implement DocIntelligenceService
  - Document analysis
  - Markdown extraction
  - Structured chunk extraction
- [ ] Implement AzureSearchService
  - Index management
  - Document indexing
  - Hybrid search
  - Document retrieval
- [ ] Implement DocIntChunkerService
  - Semantic chunking strategies
  - Table preservation
- [ ] Write unit tests (70+ tests target)
  - test_doc_intelligence.py (25+ tests)
  - test_azure_search.py (25+ tests)
  - test_docint_chunker.py (20+ tests)
- [ ] Verify 80%+ code coverage

**Deliverables:**
- New service modules in `services/`
- 70+ unit tests passing
- 80%+ coverage for new code

---

### Phase 2: REST API Endpoints (Week 2)
**Goal:** Add Azure DI HTTP endpoints to Remote RAG API

**Tasks:**
- [ ] Extend models.py with Azure DI request/response models
- [ ] Refactor existing routes into `routes/qdrant_routes.py`
- [ ] Create `routes/docint_routes.py` with new endpoints
  - POST /docint/analyze
  - POST /docint/ingest
  - POST /docint/ingest_url
  - POST /docint/search
  - GET /docint/indexes
  - GET /docint/documents/{id}
- [ ] Update app.py to include both route modules
- [ ] Add error handling for Azure DI specific errors
- [ ] Write integration tests (20+ tests)
  - test_docint_routes.py
  - Authentication tests
  - Error scenario tests
- [ ] Update API_DOCUMENTATION.md with new endpoints

**Deliverables:**
- 6 new REST endpoints
- 20+ integration tests passing
- Updated API documentation

---

### Phase 3: MCP Tool Integration (Week 3)
**Goal:** Extend unified MCP server with Azure DI tools

**Tasks:**
- [ ] Refactor existing MCP tools into `tools/qdrant_tools.py`
- [ ] Create `tools/docint_tools.py` with new tools
  - docint_analyze_document
  - docint_ingest_url
  - docint_search
  - docint_list_indexes
  - docint_get_document
- [ ] Update mcp/server.py to register all tools
- [ ] Rename existing tools with `qdrant_` prefix
  - Add aliases for backward compatibility
- [ ] Write MCP tool tests
- [ ] Update Remote MCP Server README

**Deliverables:**
- 5 new MCP tools
- Unified MCP server with 9+ tools total
- Tool tests passing
- Updated documentation

---

### Phase 4: Documentation and E2E Testing (Week 4)
**Goal:** Complete documentation and end-to-end validation

**Tasks:**
- [ ] Create AZURE_DI_GUIDE.md user guide
  - When to use Qdrant vs Azure DI
  - Chunking strategy comparison
  - Search mode comparison
  - Best practices
- [ ] Update main README.md with Azure DI architecture
- [ ] Create architecture diagrams (Azure DI flow)
- [ ] Write E2E tests
  - Full document ingestion flow (both backends)
  - Search comparison tests
  - Performance benchmarks
- [ ] Create migration guide (manual migration process)
- [ ] Update .env.example with all settings
- [ ] Record demo video (optional)

**Deliverables:**
- Comprehensive documentation
- E2E tests passing
- User guides
- Updated architecture docs

---

## 13. Open Questions

### 13.1 For User Decision

1. **Backend Selection Mechanism**
   - **Option A:** Prefix-based tool names (`qdrant_search` vs `docint_search`)
   - **Option B:** Single tools with `backend` parameter (`search(query, backend="qdrant")`)
   - **Recommendation:** Option A (clearer, no parameter confusion)

2. **Default Index/Collection Naming**
   - **Option A:** Shared naming (`default` for both)
   - **Option B:** Backend-specific (`qdrant-default`, `docint-default`)
   - **Recommendation:** Option A (simpler user experience)

3. **Chunking Strategy Default**
   - **Qdrant:** Character-based (512 chars, 50 overlap)
   - **Azure DI:** Paragraph-based semantic chunking
   - **Question:** Should both support both strategies?
   - **Recommendation:** Keep distinct (leverage each backend's strengths)

4. **Local MCP Routing**
   - **Option A:** Local MCP sends to both backends (user chooses in parameters)
   - **Option B:** Local MCP only sends to Qdrant (Azure DI via Remote MCP only)
   - **Recommendation:** Option B (clearer separation)

5. **Azure AI Search Index Schema**
   - **Option A:** Fixed schema for all indexes
   - **Option B:** Dynamic schema per index (user-defined)
   - **Recommendation:** Option A with extension points (consistent, predictable)

### 13.2 Technical Clarifications Needed

1. **Azure Document Intelligence Quota**
   - What are the rate limits for your Azure DI instance?
   - Do we need request throttling/queuing?

2. **Azure AI Search Tier**
   - What tier is your Azure AI Search instance?
   - Impacts: concurrent requests, index limits, semantic search availability

3. **Document Size Limits**
   - What's the max document size to support?
   - Azure DI has limits (varies by tier)

4. **Embedding Strategy for Azure AI Search**
   - Use Azure OpenAI embeddings for vector search?
   - Or rely on Azure AI Search built-in vectorization?
   - **Recommendation:** Use existing Azure OpenAI embeddings (consistent with Qdrant)

5. **Qdrant Tool Renaming**
   - Breaking change if we rename existing tools
   - Add aliases for backward compatibility?
   - **Recommendation:** Yes, provide aliases

---

## Appendix A: Azure Document Intelligence vs Qdrant RAG

### Feature Comparison

| Feature | Qdrant RAG | Azure DI RAG |
|---------|-----------|--------------|
| **Chunking** | Character-based (LangChain) | Semantic (paragraph/section/table) |
| **Search** | Vector similarity only | Hybrid (vector + keyword + semantic) |
| **Document Structure** | Lost | Preserved (tables, sections, layout) |
| **OCR** | Not included | Built-in |
| **Metadata** | Custom user metadata | Document structure + custom metadata |
| **Scalability** | Excellent (Qdrant) | Excellent (Azure AI Search) |
| **Cost** | Qdrant instance + OpenAI embeddings | DI + Search + OpenAI embeddings |
| **Setup Complexity** | Lower | Higher (multiple Azure services) |
| **Best For** | Simple docs, high-volume vectors | Complex docs, structure-aware search |

### When to Use Each Backend

**Use Qdrant RAG when:**
- Documents are simple text (no tables, minimal structure)
- High ingestion volume (thousands/day)
- Lower operational complexity desired
- Pure vector similarity search sufficient

**Use Azure DI RAG when:**
- Documents have rich structure (tables, forms, invoices)
- Need OCR for scanned documents
- Hybrid search important (keyword + vector)
- Want to preserve document layout information
- Semantic chunking critical (not arbitrary character splits)

---

## Appendix B: Dependencies

### New Python Packages

```toml
[project]
dependencies = [
    # Existing
    "fastapi>=0.115.0",
    "langchain>=0.3.0",
    "langchain-text-splitters>=0.3.0",
    "openai>=1.54.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "qdrant-client>=1.12.0",
    "structlog>=24.4.0",
    "uvicorn>=0.32.0",

    # NEW: Azure Document Intelligence
    "azure-ai-documentintelligence>=1.0.0b4",
    "azure-search-documents>=11.6.0b4",
    "azure-core>=1.30.0",
    "azure-identity>=1.18.0",  # If using managed identity
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "httpx>=0.28.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]
```

### Version Pinning Strategy

- Use `>=` for major versions (allow patches)
- Pin beta versions (Azure SDKs in preview)
- Verify compatibility with existing dependencies

---

## Appendix C: Error Handling

### Azure Document Intelligence Errors

```python
from azure.core.exceptions import (
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError
)

class DocIntelligenceError(Exception):
    """Base exception for Document Intelligence errors"""
    pass

class DocumentAnalysisError(DocIntelligenceError):
    """Document analysis failed"""
    pass

class UnsupportedDocumentError(DocIntelligenceError):
    """Document format not supported"""
    pass

# Error mapping
AZURE_ERROR_MAP = {
    401: "Invalid Azure Document Intelligence credentials",
    403: "Access denied to Document Intelligence resource",
    404: "Document not found or invalid URL",
    429: "Rate limit exceeded, retry after delay",
    500: "Azure Document Intelligence service error"
}
```

### Retry Strategy

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    retry=retry_if_exception_type(HttpResponseError),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(3)
)
async def analyze_with_retry(...):
    pass
```

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-26 | Initial specification | AI Assistant |

---

## Approval

- [ ] **User Review:** Specification reviewed and approved
- [ ] **Architecture Review:** Azure DI integration design approved
- [ ] **Technical Review:** Implementation plan approved
- [ ] **Ready for Implementation:** All open questions resolved
