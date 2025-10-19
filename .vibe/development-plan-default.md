# Development Plan: qdrant-full-mcp (default branch)

*Generated on 2025-10-19 by Vibe Feature MCP*
*Workflow: [greenfield](https://mrsimpson.github.io/responsible-vibe-mcp/workflows/greenfield)*

## Goal
Build an Enterprise RAG (Retrieval-Augmented Generation) Architecture with three components:

**Local Components:**
1. **Local MCP Server**: Extended markitdown-mcp for local binary document conversion
   - Single responsibility: Convert local documents (PDF, DOCX, XLSX, etc.) to text
   - Optional: Send converted text to Remote RAG API `/ingest` endpoint

**Remote Components (can be single artifact):**
2. **Remote RAG API** (HTTP REST API - FastAPI)
   - `/ingest`: Accepts text, performs chunking, embedding, stores in Qdrant
   - `/ingest_url`: Fetches HTTPS documents, converts to text, ingests
   - `/search`: Semantic search via Azure OpenAI embeddings + Qdrant
   - `/collections`, `/documents/{id}`: Utility endpoints
   - **Not directly accessible by AI assistants**

3. **Remote RAG MCP Server** (MCP protocol wrapper)
   - Exposes MCP tools (`search`, `ingest_url`, `list_collections`, `get_document`)
   - **Directly accessible by AI assistants via MCP protocol**
   - Internally calls Remote RAG API endpoints (HTTP REST calls)

This architecture addresses MCP protocol's text-only limitation by processing binaries locally and handling vector operations remotely.

## Ideation
### Tasks
- [x] Review and validate requirements with stakeholder

### Completed
- [x] Created development plan file
- [x] Defined target users (developers/technical staff)
- [x] Clarified deployment environment (OpenShift)
- [x] Established scale requirements (10k docs, 100/day, 10 users, 1000 queries/day)
- [x] Documented security approach (API key authentication for MVP)
- [x] Identified existing infrastructure (Qdrant already deployed)
- [x] Created comprehensive requirements document with 10 requirements (REQ-1 to REQ-10)
- [x] Defined out-of-scope features for MVP
- [x] Clarified three-component architecture:
  - Local MCP: Document-to-text conversion only (optionally calls Remote RAG API)
  - Remote RAG API: HTTP REST API (not accessible by AI, only by MCP servers)
  - Remote RAG MCP: MCP protocol wrapper (accessible by AI, calls Remote RAG API)

## Architecture

### Phase Entrance Criteria:
- [x] Requirements have been thoroughly defined and documented
- [x] Problem space is clearly understood (WHAT, WHO, WHY, SCOPE)
- [x] Key stakeholder needs are captured
- [x] Technology constraints and preferences are identified
- [x] Success criteria are defined

### Tasks
*All completed*

### Completed
- [x] Design Local MCP Server architecture (new build using markitdown library)
- [x] Design Remote RAG API architecture (FastAPI with async endpoints)
- [x] Design Remote RAG MCP Server architecture (MCP wrapper, same container)
- [x] Define document chunking strategy (RecursiveCharacterTextSplitter, 512 tokens, 50 overlap)
- [x] Define embedding and vector storage approach (Azure OpenAI text-embedding-3-small, Qdrant)
- [x] Design Qdrant collection schema and metadata structure (hybrid: default + user collections)
- [x] Design OpenShift deployment architecture (single container, ConfigMap, Secret, Routes)
- [x] Define error handling and logging strategy (JSON-structured logs, request tracing)
- [x] Create architecture.md document with all technical decisions (arc42 format)

## Plan

### Phase Entrance Criteria:
- [x] Technical architecture is complete and documented
- [x] Tech stack decisions are made and justified
- [x] Architectural patterns are defined (component structure, data flow, etc.)
- [x] Non-functional requirements are addressed (scalability, security, performance)
- [x] Alternative approaches have been evaluated

### Tasks
*All completed*

### Completed
- [x] Define project directory structure for both components
- [x] Create detailed implementation tasks with dependencies (6 phases documented)
- [x] Define implementation order (Phase 1: Local MCP → Phase 2-4: Remote → Phase 5-6: Deployment/Testing)
- [x] Design API contracts (Pydantic models documented in design.md)
- [x] Design MCP tool schemas for both MCP servers
- [x] Define test strategy (unit 80% coverage, integration, e2e, performance tests)
- [x] Document development workflow and setup instructions
- [x] Create comprehensive design.md document with naming conventions, design principles, component design, data modeling, implementation phases

## Code

### Phase Entrance Criteria:
- [x] Detailed implementation plan is complete
- [x] Work is broken down into specific, actionable tasks
- [x] Implementation order and dependencies are identified
- [x] Design document is complete with technical details
- [x] Risks and mitigation strategies are documented

### Tasks

**Phase 1: Local MCP Server (Week 1)** ✅ COMPLETED
- [x] Create project structure (local-mcp-server/)
- [x] Setup pyproject.toml with dependencies (markitdown 0.1.3, httpx 0.28+, mcp 1.0+)
- [x] Implement DocumentConverter (markitdown wrapper with error handling)
- [x] Implement IngestClient (HTTP client for Remote RAG API with retry logic)
- [x] Implement MCP Server with 2 tools (convert_to_text, convert_and_ingest)
- [x] Write unit tests (test_converter.py, test_ingest_client.py)
- [x] Create README with setup instructions and usage examples

**Phase 2: Remote RAG API - Core Services (Week 2)** ✅ COMPLETED
- [x] Create project structure (remote-rag-server/)
- [x] Setup pyproject.toml with dependencies
- [x] Implement configuration management (pydantic Settings)
- [x] Implement ChunkerService (LangChain RecursiveCharacterTextSplitter)
- [x] Implement EmbedderService (Azure OpenAI embeddings)
- [x] Implement QdrantService (async client)
- [x] Verify LangChain 1.0 and openai 2.5 compatibility
- [x] Write unit tests for all services

**Phase 3: Remote RAG API - HTTP Endpoints (Week 3)**
- [ ] Implement FastAPI application structure
- [ ] Implement Pydantic models (Request/Response)
- [ ] Implement API authentication (API key middleware)
- [ ] Implement 6 API endpoints
- [ ] Implement error handling and logging (structlog)
- [ ] Write API integration tests

**Phase 4: Remote RAG MCP Server (Week 3-4)**
- [ ] Implement MCP server in mcp/server.py
- [ ] Implement 4 MCP tools (search, ingest_url, list_collections, get_document)
- [ ] Implement main.py (run FastAPI + MCP concurrently)
- [ ] Write integration tests for MCP tools

**Phase 5: OpenShift Deployment (Week 4)**
- [ ] Create Dockerfile (multi-stage build)
- [ ] Create OpenShift manifests (deployment, service, route, configmap, secret)
- [ ] Test locally with Docker
- [ ] Deploy to OpenShift dev environment
- [ ] Run smoke tests

**Phase 6: Integration & E2E Testing (Week 5)**
- [ ] Write E2E tests (Local MCP → Remote API → Qdrant)
- [ ] Write E2E tests (Remote MCP → Remote API → Qdrant)
- [ ] Run performance tests (latency, throughput)
- [ ] Create user documentation (README, API docs)
- [ ] Final code review and cleanup

### Completed
- [x] **Phase 1: Local MCP Server** - Fully functional MCP server with document conversion and ingestion capabilities
  - 2 MCP tools implemented (convert_to_text, convert_and_ingest)
  - markitdown integration for document conversion
  - HTTP client for Remote RAG API communication
  - **55+ comprehensive unit tests** (test_converter.py: 30+, test_ingest_client.py: 25+)
  - **Shared test fixtures** (conftest.py with sample files)
  - **Expected coverage: 90%+** with pytest-cov
  - Complete documentation (README.md with detailed testing guide, TESTING.md, .env.example)

- [x] **Phase 2: Remote RAG API - Core Services** - All core services implemented and tested
  - Configuration management using pydantic Settings
  - ChunkerService with RecursiveCharacterTextSplitter (512 tokens, 50 overlap)
  - EmbedderService with Azure OpenAI async client (text-embedding-3-small, 1536 dimensions)
  - QdrantService with async client (create, upsert, search, get, list, delete operations)
  - **62 comprehensive unit tests** (test_chunker.py: 22, test_embedder.py: 18, test_qdrant.py: 22)
  - **93% code coverage** (exceeds 80% requirement)
  - **Verified compatibility**: LangChain 1.0.0, openai 2.5.0, qdrant-client 1.15.1

## Finalize

### Phase Entrance Criteria:
- [ ] Core implementation is complete
- [ ] All planned features are implemented
- [ ] Tests are passing
- [ ] Code meets quality standards (linting, type checking)
- [ ] Basic documentation exists

### Tasks
- [ ] *To be added when this phase becomes active*

### Completed
*None yet*

## Key Decisions

### Target Users
- **Decision**: Target users are technical staff (developers)
- **Impact**: No web UI needed, MCP-only interface, API key authentication sufficient, technical documentation focus
- **Date**: 2025-10-19

### Deployment Environment
- **Decision**: Deploy to OpenShift cluster
- **Constraints**: Create deployment scripts/manifests for OpenShift compatibility
- **Qdrant**: Already deployed in OpenShift with API key and URL available
- **Date**: 2025-10-19

### Scale Requirements (MVP/First Step)
- **Documents**: Max 10k total corpus, ~100 docs/day ingestion
- **Document Size**: Average 30-40 pages
- **Concurrent Users**: Max 10 developers
- **Query Volume**: Max 1000 queries/day
- **Performance Target**: Reasonable response times (no strict SLA for MVP)
- **Date**: 2025-10-19

### Security & Compliance
- **Decision**: Minimal security for first step (API key authentication only)
- **Rationale**: Internal technical users, can enhance later
- **Date**: 2025-10-19

### Technology Stack (Architecture Phase)
- **Decision**: Python 3.11+, Async-first (FastAPI, qdrant-client, openai)
- **Chunking**: RecursiveCharacterTextSplitter (512 tokens, 50 overlap)
- **Embeddings**: Azure OpenAI text-embedding-3-small (1536 dimensions)
- **Deployment**: Single container (FastAPI + MCP server)
- **Collections**: Hybrid strategy (default + user-defined collections)
- **Local MCP**: New build using markitdown library (not fork)
- **Date**: 2025-10-19
- **Rationale**: See ADR-001 through ADR-005 in [architecture.md](.vibe/docs/architecture.md)

## Notes
*Additional context and observations*

---
*This plan is maintained by the LLM. Tool responses provide guidance on which section to focus on and what tasks to work on.*
