# Remote RAG Server API Documentation

Complete API reference for the Remote RAG Server REST API.

## Base URL

```
http://localhost:8000
```

For production, replace with your actual server URL.

## Authentication

All endpoints except `/health` require API key authentication using the `X-API-Key` header.

### Authentication Header

```http
X-API-Key: your-api-key-here
```

### Authentication Errors

**401 Unauthorized** - Missing API key
```json
{
  "success": false,
  "error": "HTTPException",
  "message": "Missing API key. Provide X-API-Key header.",
  "details": null
}
```

**403 Forbidden** - Invalid API key
```json
{
  "success": false,
  "error": "HTTPException",
  "message": "Invalid API key",
  "details": null
}
```

## Endpoints

### 1. Health Check

Check the health status of the server and its dependencies.

**Endpoint**: `GET /health`

**Authentication**: Not required

**Request**: None

**Response**: `200 OK`
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

**Response Fields**:
- `status` (string): Overall health status ("healthy" or "degraded")
- `version` (string): API version
- `services` (object): Status of each service component

**Example**:
```bash
curl http://localhost:8000/health
```

---

### 2. Ingest Text

Ingest text content for semantic search. The text will be chunked, embedded, and stored in the specified collection.

**Endpoint**: `POST /ingest`

**Authentication**: Required

**Request Body**:
```json
{
  "text": "string (required, min length: 1)",
  "collection_name": "string (optional, default: 'default')",
  "metadata": {
    "key": "value",
    "...": "..."
  }
}
```

**Request Fields**:
- `text` (string, required): The text content to ingest. Cannot be empty.
- `collection_name` (string, optional): Name of the collection to store in. Defaults to "default".
- `metadata` (object, optional): Arbitrary metadata to attach to each chunk.

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Successfully ingested 5 chunks",
  "collection_name": "my-collection",
  "chunks_created": 5,
  "chunk_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "..."
  ],
  "chunks": [
    {
      "chunk_index": 0,
      "chunk_text": "First portion of text...",
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "chunk_index": 1,
      "chunk_text": "Second portion of text...",
      "chunk_id": "550e8400-e29b-41d4-a716-446655440001"
    }
  ]
}
```

**Response Fields**:
- `success` (boolean): Whether the operation succeeded
- `message` (string): Human-readable status message
- `collection_name` (string): Collection where data was stored
- `chunks_created` (integer): Number of chunks created
- `chunk_ids` (array): List of generated chunk IDs in Qdrant
- `chunks` (array): Detailed information about each chunk

**Error Responses**:

**400 Bad Request** - Empty or whitespace-only text
```json
{
  "success": false,
  "error": "HTTPException",
  "message": "Chunking error: Cannot chunk empty or whitespace-only text",
  "details": null
}
```

**422 Unprocessable Entity** - Validation error
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**500 Internal Server Error** - Processing error
```json
{
  "success": false,
  "error": "EmbeddingError",
  "message": "Embedding error: Failed to generate embedding",
  "details": {
    "error": "API connection failed"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "text": "This is a sample document about artificial intelligence and machine learning.",
    "collection_name": "ai-docs",
    "metadata": {
      "source": "sample.txt",
      "author": "John Doe"
    }
  }'
```

---

### 3. Ingest from URL

Fetch a document from an HTTPS URL, convert it to text, and ingest it.

**Endpoint**: `POST /ingest_url`

**Authentication**: Required

**Request Body**:
```json
{
  "url": "https://example.com/document.pdf",
  "collection_name": "string (optional, default: 'default')",
  "metadata": {
    "key": "value",
    "...": "..."
  }
}
```

**Request Fields**:
- `url` (string, required): HTTPS URL of the document. Must be a valid URL.
- `collection_name` (string, optional): Name of the collection. Defaults to "default".
- `metadata` (object, optional): Metadata to attach to chunks. `source_url` is automatically added.

**Supported Formats**:
- PDF documents
- Microsoft Office (DOCX, XLSX, PPTX)
- HTML pages
- Text files
- Any format supported by markitdown library

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Successfully ingested document from https://example.com/document.pdf",
  "url": "https://example.com/document.pdf",
  "collection_name": "documents",
  "chunks_created": 12,
  "chunk_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "..."
  ],
  "document_length": 8450
}
```

**Response Fields**:
- `success` (boolean): Operation success status
- `message` (string): Status message
- `url` (string): The URL that was processed
- `collection_name` (string): Collection where data was stored
- `chunks_created` (integer): Number of chunks created
- `chunk_ids` (array): Generated chunk IDs
- `document_length` (integer): Length of converted text in characters

**Error Responses**:

**400 Bad Request** - Failed to fetch URL
```json
{
  "success": false,
  "error": "HTTPException",
  "message": "Failed to fetch URL: Connection timeout",
  "details": null
}
```

**422 Unprocessable Entity** - Invalid URL
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/ingest_url \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "url": "https://example.com/research-paper.pdf",
    "collection_name": "research",
    "metadata": {
      "category": "AI",
      "year": 2025
    }
  }'
```

---

### 4. Semantic Search

Perform semantic search across ingested documents using natural language queries.

**Endpoint**: `POST /search`

**Authentication**: Required

**Request Body**:
```json
{
  "query": "string (required, min length: 1)",
  "collection_name": "string (optional, default: 'default')",
  "limit": 5,
  "score_threshold": 0.7,
  "filter": {
    "key": "value"
  }
}
```

**Request Fields**:
- `query` (string, required): Natural language search query. Cannot be empty.
- `collection_name` (string, optional): Collection to search. Defaults to "default".
- `limit` (integer, optional): Maximum number of results (1-100). Default: 5.
- `score_threshold` (float, optional): Minimum similarity score (0.0-1.0). Default: 0.0.
- `filter` (object, optional): Metadata filters to apply. Only exact matches supported.

**Response**: `200 OK`
```json
{
  "success": true,
  "query": "What is machine learning?",
  "collection_name": "ai-docs",
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "score": 0.92,
      "text": "Machine learning is a subset of artificial intelligence...",
      "metadata": {
        "source": "ml-guide.pdf",
        "author": "Jane Smith",
        "chunk_index": 3,
        "total_chunks": 10
      }
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "score": 0.87,
      "text": "Deep learning models use neural networks...",
      "metadata": {
        "source": "dl-intro.pdf",
        "chunk_index": 0,
        "total_chunks": 5
      }
    }
  ],
  "count": 2
}
```

**Response Fields**:
- `success` (boolean): Operation success status
- `query` (string): The search query
- `collection_name` (string): Collection that was searched
- `results` (array): Array of search results, sorted by relevance score (descending)
  - `id` (string): Document/chunk ID in Qdrant
  - `score` (float): Similarity score (0.0-1.0, higher is more similar)
  - `text` (string): The matched text content
  - `metadata` (object): Associated metadata
- `count` (integer): Number of results returned

**Error Responses**:

**422 Unprocessable Entity** - Empty query
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**422 Unprocessable Entity** - Invalid limit
```json
{
  "detail": [
    {
      "loc": ["body", "limit"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**500 Internal Server Error** - Collection not found
```json
{
  "success": false,
  "error": "QdrantError",
  "message": "Search error: Collection 'invalid-name' not found",
  "details": {
    "error": "Collection does not exist"
  }
}
```

**Examples**:

Basic search:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "What is machine learning?"
  }'
```

Search with filters:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "neural networks",
    "collection_name": "ai-docs",
    "limit": 10,
    "score_threshold": 0.8,
    "filter": {
      "author": "Jane Smith",
      "year": 2025
    }
  }'
```

---

### 5. List Collections

List all available Qdrant collections.

**Endpoint**: `GET /collections`

**Authentication**: Required

**Request**: None

**Response**: `200 OK`
```json
{
  "success": true,
  "collections": [
    "default",
    "ai-docs",
    "research",
    "customer-support"
  ],
  "count": 4
}
```

**Response Fields**:
- `success` (boolean): Operation success status
- `collections` (array): List of collection names
- `count` (integer): Number of collections

**Error Responses**:

**500 Internal Server Error** - Qdrant connection error
```json
{
  "success": false,
  "error": "QdrantError",
  "message": "Failed to list collections: Connection refused",
  "details": {
    "error": "Cannot connect to Qdrant server"
  }
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/collections \
  -H "X-API-Key: your-api-key"
```

---

### 6. Get Document by ID

Retrieve a specific document/chunk by its ID from a collection.

**Endpoint**: `GET /documents/{document_id}`

**Authentication**: Required

**Path Parameters**:
- `document_id` (string, required): The UUID of the document/chunk

**Query Parameters**:
- `collection_name` (string, optional): Collection name. Defaults to "default".

**Response (Document Found)**: `200 OK`
```json
{
  "success": true,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection_name": "ai-docs",
  "text": "Machine learning is a subset of artificial intelligence that focuses on...",
  "metadata": {
    "source": "ml-guide.pdf",
    "author": "Jane Smith",
    "chunk_index": 3,
    "total_chunks": 10,
    "source_url": "https://example.com/ml-guide.pdf"
  },
  "found": true
}
```

**Response (Document Not Found)**: `200 OK`
```json
{
  "success": true,
  "document_id": "550e8400-e29b-41d4-a716-999999999999",
  "collection_name": "ai-docs",
  "text": null,
  "metadata": null,
  "found": false
}
```

**Response Fields**:
- `success` (boolean): Operation success status
- `document_id` (string): The requested document ID
- `collection_name` (string): Collection that was queried
- `text` (string | null): The document text content
- `metadata` (object | null): Associated metadata
- `found` (boolean): Whether the document was found

**Error Responses**:

**500 Internal Server Error** - Retrieval error
```json
{
  "success": false,
  "error": "QdrantError",
  "message": "Failed to get document: Collection not found",
  "details": {
    "error": "Collection 'invalid' does not exist"
  }
}
```

**Examples**:

Default collection:
```bash
curl -X GET "http://localhost:8000/documents/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key"
```

Specific collection:
```bash
curl -X GET "http://localhost:8000/documents/550e8400-e29b-41d4-a716-446655440000?collection_name=ai-docs" \
  -H "X-API-Key: your-api-key"
```

---

## Common HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid request data or parameters |
| 401 | Unauthorized | Missing API key |
| 403 | Forbidden | Invalid API key |
| 404 | Not Found | Endpoint not found |
| 405 | Method Not Allowed | Wrong HTTP method for endpoint |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Internal Server Error | Server or processing error |

## Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "error": "Additional technical details",
    "field": "context-specific-information"
  }
}
```

## Rate Limiting

Currently, the API does not implement rate limiting. For production deployments, consider adding rate limiting middleware or using a reverse proxy with rate limiting capabilities.

## CORS

The API includes CORS middleware configured to allow all origins. For production, configure the `allow_origins` parameter in the CORS middleware to restrict access to specific domains.

## Pagination

The API does not currently support pagination for search results. Use the `limit` parameter in the `/search` endpoint to control the number of results returned (maximum: 100).

## Versioning

API version: 0.1.0

Future versions may introduce breaking changes. Version information is available in the `/health` endpoint response.

## Best Practices

### Ingestion

1. **Batch large documents**: Use `/ingest` endpoint for bulk text rather than multiple small requests
2. **Metadata strategy**: Include searchable metadata like source, author, date for better filtering
3. **Collection organization**: Use separate collections for different document types or use cases
4. **Error handling**: Implement retry logic with exponential backoff for 500-series errors

### Search

1. **Query optimization**: Use specific, relevant queries for better results
2. **Score threshold**: Set appropriate `score_threshold` to filter low-relevance results
3. **Result limits**: Start with smaller limits (5-10) and increase if needed
4. **Metadata filters**: Use filters to narrow search scope and improve performance

### Security

1. **API key management**: Rotate keys regularly, store securely
2. **HTTPS**: Always use HTTPS in production
3. **Input validation**: The API validates all inputs, but sanitize data on client side too
4. **Error handling**: Don't expose sensitive information in error messages

## Code Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Ingest text
response = requests.post(
    f"{API_URL}/ingest",
    headers=headers,
    json={
        "text": "Sample document content...",
        "collection_name": "my-docs",
        "metadata": {"source": "api-example"}
    }
)
print(response.json())

# Search
response = requests.post(
    f"{API_URL}/search",
    headers=headers,
    json={
        "query": "sample query",
        "collection_name": "my-docs",
        "limit": 5
    }
)
results = response.json()
for result in results["results"]:
    print(f"Score: {result['score']}, Text: {result['text'][:100]}...")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Ingest text
async function ingestText() {
  const response = await axios.post(
    `${API_URL}/ingest`,
    {
      text: 'Sample document content...',
      collection_name: 'my-docs',
      metadata: { source: 'api-example' }
    },
    { headers }
  );
  console.log(response.data);
}

// Search
async function search() {
  const response = await axios.post(
    `${API_URL}/search`,
    {
      query: 'sample query',
      collection_name: 'my-docs',
      limit: 5
    },
    { headers }
  );

  response.data.results.forEach(result => {
    console.log(`Score: ${result.score}, Text: ${result.text.substring(0, 100)}...`);
  });
}
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Ingest text
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample text", "collection_name": "my-docs"}'

# Search
curl -X POST http://localhost:8000/search \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample query", "limit": 5}'

# List collections
curl http://localhost:8000/collections \
  -H "X-API-Key: your-api-key"
```

## Support

For API issues or questions:
- Review this documentation and the main README.md
- Check server logs for detailed error information
- Verify configuration in .env file
- Test with the `/health` endpoint to ensure all services are operational
