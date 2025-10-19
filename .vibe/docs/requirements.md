<!--
INSTRUCTIONS FOR REQUIREMENTS (EARS FORMAT):
- Use EARS format
- Number requirements as REQ-1, REQ-2, etc.
- Keep user stories concise and focused on user value
- Make acceptance criteria specific and testable
- Reference requirements in tasks using: (_Requirements: REQ-1, REQ-3_)

EXAMPLE:
## REQ-1: User Authentication
**User Story:** As a website visitor, I want to create an account so that I can access personalized features.

**Acceptance Criteria:**
- WHEN user provides valid email and password THEN the system SHALL create new account
- WHEN user provides duplicate email THEN the system SHALL show "email already exists" error
- WHEN user provides weak password THEN the system SHALL show password strength requirements

FULL EARS SYNTAX:
While <optional pre-condition>, when <optional trigger>, the <system name> shall <system response>

The EARS ruleset states that a requirement must have: Zero or many preconditions; Zero or one trigger; One system name; One or many system responses.

The application of the EARS notation produces requirements in a small number of patterns, depending on the clauses that are used. The patterns are illustrated below.

Ubiquitous requirements
Ubiquitous requirements are always active (so there is no EARS keyword)

The <system name> shall <system response>

Example: The mobile phone shall have a mass of less than XX grams.

State driven requirements
State driven requirements are active as long as the specified state remains true and are denoted by the keyword While.

While <precondition(s)>, the <system name> shall <system response>

Example: While there is no card in the ATM, the ATM shall display “insert card to begin”.

Event driven requirements
Event driven requirements specify how a system must respond when a triggering event occurs and are denoted by the keyword When.

When <trigger>, the <system name> shall <system response>

Example: When “mute” is selected, the laptop shall suppress all audio output.

Optional feature requirements
Optional feature requirements apply in products or systems that include the specified feature and are denoted by the keyword Where.

Where <feature is included>, the <system name> shall <system response>

Example: Where the car has a sunroof, the car shall have a sunroof control panel on the driver door.

Unwanted behavior requirements
Unwanted behavior requirements are used to specify the required system response to undesired situations and are denoted by the keywords If and Then.

If <trigger>, then the <system name> shall <system response>

Example: If an invalid credit card number is entered, then the website shall display “please re-enter credit card details”.

Complex requirements
The simple building blocks of the EARS patterns described above can be combined to specify requirements for richer system behavior. Requirements that include more than one EARS keyword are called Complex requirements.

While <precondition(s)>, When <trigger>, the <system name> shall <system response>

Example: While the aircraft is on ground, when reverse thrust is commanded, the engine control system shall enable reverse thrust.

Complex requirements for unwanted behavior also include the If-Then keywords.
-->

# Requirements Document

## Project Overview

**System Name:** Enterprise RAG Architecture (Two-MCP Design)

**Target Users:** Technical staff (developers) using MCP-enabled AI assistants (Claude Code)

**Deployment:** OpenShift cluster

**Core Components:**

**Local Components:**
1. **Local MCP Server** (extended markitdown-mcp)
   - Converts local binary documents (PDF, DOCX, XLSX, etc.) to text
   - Optionally sends converted text to Remote RAG API endpoint

**Remote Components (can be single artifact):**
2. **Remote RAG API** (HTTP REST API - FastAPI)
   - `/ingest` endpoint: Accepts text/markdown, performs chunking, embedding, stores in Qdrant
   - `/ingest_url` endpoint: Fetches HTTPS documents, converts to text, ingests
   - Additional utility endpoints (health, collections, etc.)
   - **Not directly accessible by AI assistants** - called by MCP servers

3. **Remote RAG MCP Server** (MCP protocol wrapper)
   - Exposes MCP tools that AI assistants can call directly
   - `search()` tool: Semantic search functionality
   - `ingest_url()` tool: Trigger URL document ingestion via Remote RAG API
   - `list_collections()` tool: Collection management
   - `get_document()` tool: Document retrieval
   - **Directly accessible by AI assistants via MCP protocol**
   - Internally calls Remote RAG API endpoints

**Infrastructure:**
4. Qdrant Vector Database (existing, deployed in OpenShift)
5. Azure OpenAI (embeddings service)

**Scale (MVP):**
- Max 10k documents total corpus
- ~100 documents/day ingestion rate
- Average document size: 30-40 pages
- Max 10 concurrent developer users
- Max 1000 queries/day

---

## REQ-1: Local Document Conversion

**User Story:** As a developer, I want to convert local binary documents (PDF, DOCX, XLSX, etc.) to text using the local MCP server, so that I can process documents without uploading them externally.

**Acceptance Criteria:**

- WHEN developer calls `convert_to_text(uri="file:///path/to/doc.pdf")` THEN the local MCP SHALL convert the document to text using MarkItDown library
- WHEN document conversion succeeds THEN the local MCP SHALL return the text content
- WHEN document conversion fails THEN the local MCP SHALL return descriptive error message
- The local MCP SHALL support file formats: PDF, DOCX, PPTX, XLSX, images (with OCR), HTML, CSV, JSON, XML
- The local MCP SHALL only perform document-to-text conversion (no indexing, no search)

## REQ-1A: Local Document Ingestion (Optional)

**User Story:** As a developer, I want to optionally send converted text directly to the Remote RAG API for indexing, so that I can ingest local documents in one step.

**Acceptance Criteria:**

- WHEN developer calls local MCP `convert_and_ingest(uri="file:///path/to/doc.pdf", collection="default")` THEN the local MCP SHALL convert the document to text
- WHEN conversion succeeds THEN the local MCP SHALL POST the text to the Remote RAG API `/ingest` endpoint (HTTP REST call) with metadata
- WHEN remote ingestion succeeds THEN the local MCP SHALL return `{"status": "ingested", "doc_id": "<id>", "chunks": <count>}`
- WHEN remote ingestion fails THEN the local MCP SHALL return descriptive error message
- The local MCP SHALL read `RAG_API_URL` and `RAG_API_KEY` from environment variables for HTTP API access
- The local MCP does NOT communicate with the Remote RAG MCP Server (only with Remote RAG API)

## REQ-2: Remote Document Conversion and Ingestion

**User Story:** As a developer (via AI assistant), I want to fetch HTTPS-reachable documents and ingest them into the RAG system, so that I can index online documentation and web content.

**Acceptance Criteria:**

- WHEN AI assistant calls Remote RAG MCP `ingest_url(uri="https://example.com/doc.pdf", collection="default")` THEN the Remote RAG MCP SHALL call the Remote RAG API `/ingest_url` endpoint (HTTP REST call)
- WHEN Remote RAG API receives the request THEN it SHALL fetch the URL, convert to text, chunk, embed, and store in Qdrant
- WHEN ingestion completes THEN the Remote RAG MCP SHALL return `{"status": "ingested", "doc_id": "<id>", "chunks": <count>}` to the AI assistant
- WHEN URL is inaccessible (404, timeout) THEN the Remote RAG MCP SHALL return clear error message
- The Remote RAG API SHALL support the same formats as local MCP for HTTPS-reachable documents
- The Remote RAG MCP acts as an MCP protocol wrapper around the Remote RAG API

## REQ-3: Semantic Search via Remote RAG MCP

**User Story:** As a developer (via AI assistant), I want to perform semantic searches across ingested documents using natural language queries, so that I can find relevant information quickly.

**Acceptance Criteria:**

- WHEN AI assistant calls Remote RAG MCP `search(query="authentication approach", collection="default", top_k=5)` THEN the Remote RAG MCP SHALL call the Remote RAG API `/search` endpoint (HTTP REST call)
- WHEN Remote RAG API receives the request THEN it SHALL generate query embedding via Azure OpenAI and search Qdrant vector database
- WHEN search completes THEN the Remote RAG MCP SHALL return top_k results to AI assistant with text chunks, relevance scores, and metadata (source, page)
- The Remote RAG MCP SHALL support configurable `top_k` parameter (default: 5, max: 50)
- WHEN no results found THEN the Remote RAG MCP SHALL return empty results array
- The local MCP SHALL NOT provide search functionality (search is remote-only)
- The Remote RAG MCP acts as an MCP protocol wrapper around the Remote RAG API `/search` endpoint

## REQ-4: Collection Management

**User Story:** As a developer (via AI assistant), I want to organize documents into collections (projects, teams, domains), so that I can scope searches to relevant document sets.

**Acceptance Criteria:**

- WHEN document is ingested with `collection="project-alpha"` THEN the Remote RAG API SHALL store vectors in the specified Qdrant collection
- WHEN AI assistant calls Remote RAG MCP `list_collections()` THEN the Remote RAG MCP SHALL call Remote RAG API `/collections` endpoint and return all available collections with document counts
- WHEN search is performed with `collection="project-alpha"` THEN the Remote RAG API SHALL only search within that collection
- The Remote RAG API SHALL support "default" collection for uncategorized documents
- The Remote RAG MCP exposes collection management as MCP tools wrapping the Remote RAG API endpoints

## REQ-5: Document Retrieval

**User Story:** As a developer (via AI assistant), I want to retrieve full document details by ID, so that I can access the complete content and metadata of indexed documents.

**Acceptance Criteria:**

- WHEN AI assistant calls Remote RAG MCP `get_document(doc_id="abc123")` THEN the Remote RAG MCP SHALL call Remote RAG API `/documents/{doc_id}` endpoint
- WHEN Remote RAG API receives the request THEN it SHALL return the complete document with all chunks, metadata, and source information
- WHEN document ID does not exist THEN the Remote RAG MCP SHALL return "document not found" error
- The Remote RAG MCP acts as an MCP protocol wrapper around the Remote RAG API document retrieval endpoint

## REQ-6: API Authentication

**User Story:** As a system administrator, I want to secure the Remote RAG API with API key authentication, so that only authorized clients can access the system.

**Acceptance Criteria:**

- WHEN Remote RAG API receives request without API key THEN it SHALL return 401 Unauthorized
- WHEN Remote RAG API receives request with invalid API key THEN it SHALL return 403 Forbidden
- WHEN Remote RAG API receives request with valid API key THEN it SHALL process the request
- The local MCP SHALL read API key from environment variable `RAG_API_KEY` and send it in `Authorization: Bearer <key>` header when calling Remote RAG API
- The Remote RAG MCP SHALL read API key from environment variable `RAG_API_KEY` and send it in `Authorization: Bearer <key>` header when calling Remote RAG API
- Both the local MCP and Remote RAG MCP authenticate to the same Remote RAG API using the same authentication mechanism

## REQ-7: Document Chunking and Embedding

**User Story:** As a system, I want to chunk documents intelligently and generate high-quality embeddings, so that semantic search returns accurate results.

**Acceptance Criteria:**

- WHEN remote API receives markdown text THEN the system SHALL chunk the text into meaningful segments (contextual chunking)
- WHEN chunks are created THEN the system SHALL generate embeddings for each chunk using Azure OpenAI
- WHEN embeddings are generated THEN the system SHALL store vectors in Qdrant with chunk text and metadata as payload
- The system SHALL preserve source document metadata (filename, page number, collection) in each chunk

## REQ-8: OpenShift Deployment Readiness

**User Story:** As a DevOps engineer, I want OpenShift deployment manifests for all components, so that I can deploy the RAG system to our OpenShift cluster.

**Acceptance Criteria:**

- The system SHALL provide OpenShift DeploymentConfig or Deployment manifests for the remote RAG server
- The system SHALL provide Service and Route manifests for external access
- The system SHALL support configuration via ConfigMap (Qdrant URL, Azure OpenAI endpoints)
- The system SHALL support secrets via Secret (API keys, Qdrant API key, Azure OpenAI key)
- WHEN deployed to OpenShift THEN the system SHALL connect to existing Qdrant instance using provided URL and API key

## REQ-9: Error Handling and Logging

**User Story:** As a developer, I want clear error messages and proper logging, so that I can troubleshoot issues effectively.

**Acceptance Criteria:**

- WHEN any operation fails THEN the system SHALL return descriptive error message with failure reason
- The remote RAG server SHALL log document ingestion events (doc_id, size, collection, timestamp)
- The remote RAG server SHALL log search queries (query text, collection, results count, latency)
- The remote RAG server SHALL log API authentication failures
- The remote RAG server SHALL log processing errors (conversion, embedding, storage failures)

## REQ-10: Environment Configuration

**User Story:** As a system administrator, I want to configure the system via environment variables, so that I can adapt to different environments (dev, staging, production).

**Acceptance Criteria:**

- The local MCP SHALL read `RAG_API_URL` for Remote RAG API endpoint and `RAG_API_KEY` for authentication
- The Remote RAG MCP SHALL read `RAG_API_URL` for Remote RAG API endpoint and `RAG_API_KEY` for authentication
- The Remote RAG API SHALL read `QDRANT_URL` for Qdrant connection
- The Remote RAG API SHALL read `QDRANT_API_KEY` for Qdrant authentication
- The Remote RAG API SHALL read `AZURE_OPENAI_ENDPOINT` for Azure OpenAI service
- The Remote RAG API SHALL read `AZURE_OPENAI_KEY` for Azure OpenAI authentication
- The Remote RAG API SHALL read `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` for embedding model deployment name

## REQ-11: Remote RAG API Endpoints

**User Story:** As a system integrator, I want a well-defined HTTP REST API for the Remote RAG API, so that both the Local MCP and Remote RAG MCP can interact with it consistently.

**Acceptance Criteria:**

**Core Endpoints:**
- `POST /ingest`: Accepts `{text: string, metadata: {filename, collection, ...}}`, returns `{status, doc_id, chunks}`
- `POST /ingest_url`: Accepts `{url: string, collection: string}`, fetches URL, converts to text, ingests, returns `{status, doc_id, chunks}`
- `POST /search`: Accepts `{query: string, collection: string, top_k: int}`, returns `{results: [{text, score, metadata}]}`
- `GET /collections`: Returns `{collections: [{name, doc_count}]}`
- `GET /documents/{doc_id}`: Returns `{doc_id, chunks: [{text, metadata}], source, ...}`
- `GET /health`: Returns `{status: "healthy", version: "..."}`

**Authentication:**
- All endpoints (except `/health`) SHALL require `Authorization: Bearer <API_KEY>` header
- SHALL return 401/403 for missing/invalid API keys

**Error Handling:**
- SHALL return structured JSON errors: `{error: string, detail: string, status_code: int}`
- SHALL log all requests and errors for debugging

## Out of Scope (MVP)

The following features are explicitly out of scope for the first step:

- Web UI for document upload and search
- User management and role-based access control
- Advanced security (OAuth, 2FA, audit trails)
- GDPR/compliance features
- Hybrid search (BM25 + semantic)
- Reranking with cross-encoder models
- Multi-modal support (image embeddings, image captioning)
- GraphRAG (entity relationships)
- Advanced chunking strategies beyond contextual chunking
- Usage analytics dashboard
- Document deletion API (can be added later if needed)
- Multi-tenancy beyond collections
