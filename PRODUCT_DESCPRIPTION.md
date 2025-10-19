[200~# Enterprise RAG Architecture: Two-MCP Design

## Overview

Production RAG system addressing MCP protocol's text-only limitation through local document processing + remote vector search.

**Core Challenge**: MCP protocol only supports text/JSON (no binary transfer).

**Solution**: Local MCP converts binaries → Remote MCP/API handles vector storage and retrieval.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Developer Machine │
│ │
│ ┌───────────────────────────────────────────────────┐ │
│ │ Extended markitdown-mcp (Local STDIO) │ │
│ │ │ │
│ │ - Accesses local files (file:// URIs) │ │
│ │ - Converts to markdown (MarkItDown library) │ │
│ │ - POSTs to remote RAG API OR saves locally │ │
│ └───────────────────────────────────────────────────┘ │
│ ↓ HTTPS │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Remote Server │
│ │
│ ┌──────────────────┐ ┌──────────────────┐ │
│ │ RAG MCP Server │ │ RAG REST API │ │
│ │ (HTTP/SSE) │ │ │ │
│ │ │ │ POST /ingest │ │
│ │ - search() │──┬───│ GET /docs │ │
│ │ - get_doc() │ │ │ DELETE /docs │ │
│ │ - list_colls() │ │ └──────────────────┘ │
│ └──────────────────┘ │ ↓ │
│ │ ┌──────────────────┐ │
│ │ │ MarkItDown Lib │ │
│ │ │ (Server-side │ │
│ │ │ processing) │ │
│ │ └──────────────────┘ │
│ │ ↓ │
│ │ ┌──────────────────┐ │
│ │ │ Azure OpenAI │ │
│ │ │ (Embeddings) │ │
│ │ └──────────────────┘ │
│ │ ↓ │
│ │ ┌──────────────────┐ │
│ └───│ Qdrant Vector │ │
│ │ Database │ │
│ └──────────────────┘ │
│ │
│ Authentication: API Key for all endpoints │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### Local MCP: Extended markitdown-mcp

**Base**: Microsoft MarkItDown MCP (81k stars, MIT license)

**Tool**:
```python
convert_to_markdown(
    uri: str, # file://, http://, https://
    target: str = "ingest", # "ingest" or local path
    collection: str = "default",
    metadata: dict = None
) -> dict
```

**Supported Formats**: PDF, DOCX, PPTX, XLSX, images (OCR), audio (transcription), HTML, CSV, JSON, XML, ZIP

**Extension**: Adds `target` parameter for direct RAG ingestion vs local save

### Remote MCP: rag-query-mcp

**Tools**:
```python
search(query: str, collection: str, top_k: int, filters: dict) -> dict
get_document(doc_id: str) -> dict
list_collections() -> dict
```

**Transport**: HTTP or SSE

**Authentication**: API key via header

### Remote REST API: rag-ingestion-api

**Endpoints**:
```
POST /api/ingest/text # From local MCP (text payload)
POST /api/ingest/file # From CI/CD (multipart binary)
GET /api/documents/{id}
DELETE /api/documents/{id}
```

**Processing Pipeline**:
1. Receive text or binary
2. Convert binary to markdown (MarkItDown library)
3. Chunk markdown (contextual chunking)
4. Generate embeddings (Azure OpenAI)
5. Store in Qdrant

**Authentication**: API key via Bearer token

## Data Flow

### Document Ingestion

```
User: "Index this PDF"
  ↓
Local MCP: convert_to_markdown("file:///report.pdf")
  ↓
MarkItDown converts PDF → markdown text
  ↓
POST to https://rag.company.com/api/ingest/text
  Headers: Authorization: Bearer {API_KEY}
  Body: {"text": "...", "metadata": {...}, "collection": "default"}
  ↓
Remote API:
  1. Validates API key
  2. Chunks markdown
  3. Calls Azure OpenAI for embeddings
  4. Stores vectors in Qdrant
  ↓
Returns: {"doc_id": "abc123", "chunks": 42}
```

### Document Search

```
User: "Find Q4 revenue info"
  ↓
Remote MCP: search("Q4 revenue", collection="default")
  Headers: Authorization: Bearer {API_KEY}
  ↓
Remote Server:
  1. Validates API key
  2. Generates query embedding (Azure OpenAI)
  3. Queries Qdrant vector database
  4. Returns top-k results
  ↓
Returns: [
  {"text": "...", "score": 0.89, "source": "report.pdf", "page": 12},
  ...
]
```

## Configuration

### Claude Code

`~/.config/claude/mcp.json`:
```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": ["-m", "markitdown_mcp"],
      "env": {
        "RAG_API_URL": "https://rag.company.com",
        "RAG_API_KEY": "${RAG_API_KEY}"
      }
    },
    "rag-search": {
      "transport": "http",
      "url": "https://rag.company.com/mcp",
      "headers": {
        "Authorization": "Bearer ${RAG_API_KEY}"
      }
    }
  }
}
```

### Environment Variables

**Local MCP**:
- `RAG_API_URL`: Remote RAG API endpoint
- `RAG_API_KEY`: API key for authentication

**Remote Server**:
- `QDRANT_URL`: Qdrant connection string
- `QDRANT_API_KEY`: Qdrant authentication
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Deployment name for embeddings

## Implementation

### Extending MarkItDown MCP

Clone and modify Microsoft's official MCP server:

```bash
git clone https://github.com/microsoft/markitdown.git
cd markitdown/packages/markitdown-mcp
```

Modify `src/markitdown_mcp/server.py`:

```python
import httpx
import os
import json
from pathlib import Path
from markitdown import MarkItDown

RAG_API_URL = os.getenv("RAG_API_URL")
RAG_API_KEY = os.getenv("RAG_API_KEY")

async def _ingest_to_rag(text: str, metadata: dict) -> dict:
    """Upload to remote RAG API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RAG_API_URL}/api/ingest/text",
            json={"text": text, "metadata": metadata},
            headers={"Authorization": f"Bearer {RAG_API_KEY}"},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

@server.tool()
async def convert_to_markdown(
    uri: str,
    target: str = "ingest",
    collection: str = "default",
    metadata: dict = None
) -> str:
    """Convert document to markdown and ingest or save"""
    
    # Convert using MarkItDown
    md = MarkItDown()
    result = md.convert(uri)
    markdown_text = result.text_content
    
    if target == "ingest":
        # Upload to RAG
        ingest_result = await _ingest_to_rag(
            markdown_text,
            {**(metadata or {}), "source": uri, "collection": collection}
        )
        return json.dumps({
            "status": "ingested",
            "doc_id": ingest_result["doc_id"],
            "chunks": ingest_result["chunks"],
            "collection": collection
        })
    else:
        # Save locally
        Path(target).write_text(markdown_text, encoding='utf-8')
        return json.dumps({
            "status": "saved",
            "path": target,
            "size_bytes": len(markdown_text.encode('utf-8'))
        })
```

Add `httpx` to dependencies in `pyproject.toml`:
```toml
dependencies = ["markitdown>=0.1.0", "mcp>=1.0.0", "httpx>=0.27.0"]
```

Install: `pip install -e .`

### Remote RAG Server

**Technology Stack**:
- **Vector Database**: Qdrant
- **Document Processing**: MarkItDown library
- **Embeddings**: Azure OpenAI (text-embedding-3-large or ada-002)
- **API Framework**: FastAPI or Flask

**Core Components**:

```python
# Ingestion endpoint
@app.post("/api/ingest/text")
async def ingest_text(
    request: IngestRequest,
    api_key: str = Depends(verify_api_key)
):
    # 1. Chunk text
    chunks = chunk_text(request.text)
    
    # 2. Generate embeddings via Azure OpenAI
    embeddings = await azure_openai_embed(chunks)
    
    # 3. Store in Qdrant
    doc_id = await qdrant_client.upsert(
        collection_name=request.metadata.get("collection", "default"),
        points=[{
            "id": generate_id(),
            "vector": emb,
            "payload": {"text": chunk, "metadata": request.metadata}
        } for chunk, emb in zip(chunks, embeddings)]
    )
    
    return {"doc_id": doc_id, "chunks": len(chunks)}

# Search via MCP
@mcp.tool()
async def search(
    query: str,
    collection: str = "default",
    top_k: int = 5
):
    # 1. Embed query via Azure OpenAI
    query_embedding = await azure_openai_embed([query])
    
    # 2. Search Qdrant
    results = await qdrant_client.search(
        collection_name=collection,
        query_vector=query_embedding[0],
        limit=top_k
    )
    
    return [{"text": r.payload["text"], "score": r.score, 
             "metadata": r.payload["metadata"]} for r in results]
```

## Usage Examples

**Basic ingestion**:
```
User: "Index product spec"
→ convert_to_markdown("file:///specs/product.pdf")
→ {"status": "ingested", "doc_id": "abc123", "chunks": 37}
```

**Review before ingestion**:
```
User: "Convert but let me review"
→ convert_to_markdown("file:///report.pdf", target="/tmp/report.md")
→ {"status": "saved", "path": "/tmp/report.md"}
[edit file]
→ convert_to_markdown("file:///tmp/report.md")
→ {"status": "ingested", ...}
```

**Remote URL**:
```
User: "Index this documentation"
→ convert_to_markdown("https://docs.example.com/api.html")
→ Converted and indexed
```

**Search**:
```
User: "Find authentication info"
→ search("authentication approach", collection="specs")
→ Returns relevant chunks with scores
```

## Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Local Processing | MarkItDown | Microsoft-backed, 81k stars, 10+ formats, CPU-only |
| Vector DB | Qdrant | Performance, ease of deployment, API key auth |
| Embeddings | Azure OpenAI | Enterprise support, high quality, easy integration |
| Server-side Processing | MarkItDown | Same library consistency, handles CI/CD uploads |

## Key Design Decisions

**Why Two MCP Servers?**
MCP protocol is text-only (JSON). Local MCP accesses binary files via filesystem, converts to text, then sends to remote server.

**Why `target` Parameter?**
Enables inspection workflow: convert → review → edit → ingest. Power users can audit before indexing.

**Why MarkItDown?**
- 10+ formats out-of-box
- Microsoft maintenance
- No GPU requirement
- Production-proven (81k stars)
- Plugin architecture for extensions

**Why API Key (not OAuth)?**
Simpler for service-to-service communication. Both MCP and REST use same API key for consistency.

**Why Azure OpenAI?**
Enterprise compliance, SLA guarantees, consistent API, no self-hosting complexity.

**Server-side MarkItDown?**
CI/CD pipelines and batch jobs can upload binaries directly to REST API. Server converts using same library for consistency.

## Security

**Authentication**: API key via Bearer token for all endpoints

**Authorization**: Collection-level access control via API key scoping

**Transport**: TLS for all communications

**Storage**: API keys in secure environment variables, never in code

## Monitoring

**Metrics**:
- Ingestion rate (docs/hour)
- Search latency (p50/p95/p99)
- Embedding API costs (Azure OpenAI)
- Vector database query performance
- API error rates by endpoint

**Logging**:
- Document ingestion events (doc_id, size, collection)
- Search queries (query text, results count, latency)
- API authentication failures
- Processing errors (conversion, embedding, storage)

## Future Enhancements

**Current Scope** (MVP):
- Binary document conversion (MarkItDown)
- Vector storage and retrieval (Qdrant)
- Basic semantic search
- API key authentication

**Future Additions**:
- Hybrid search (semantic + keyword BM25)
- Reranking (cross-encoder models)
- Multi-modal support (image captioning)
- GraphRAG (entity relationships)
- Advanced chunking strategies
- Usage analytics dashboard

