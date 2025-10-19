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
- [ ] Design Local MCP Server architecture (extended markitdown-mcp)
- [ ] Design Remote RAG API architecture (FastAPI with endpoints)
- [ ] Design Remote RAG MCP Server architecture (MCP wrapper)
- [ ] Define document chunking strategy
- [ ] Define embedding and vector storage approach
- [ ] Design Qdrant collection schema and metadata structure
- [ ] Design OpenShift deployment architecture (manifests, services, routes)
- [ ] Define error handling and logging strategy
- [ ] Create architecture.md document with all technical decisions

### Completed
*None yet*

## Plan

### Phase Entrance Criteria:
- [ ] Technical architecture is complete and documented
- [ ] Tech stack decisions are made and justified
- [ ] Architectural patterns are defined (component structure, data flow, etc.)
- [ ] Non-functional requirements are addressed (scalability, security, performance)
- [ ] Alternative approaches have been evaluated

### Tasks
- [ ] *To be added when this phase becomes active*

### Completed
*None yet*

## Code

### Phase Entrance Criteria:
- [ ] Detailed implementation plan is complete
- [ ] Work is broken down into specific, actionable tasks
- [ ] Implementation order and dependencies are identified
- [ ] Design document is complete with technical details
- [ ] Risks and mitigation strategies are documented

### Tasks
- [ ] *To be added when this phase becomes active*

### Completed
*None yet*

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

## Notes
*Additional context and observations*

---
*This plan is maintained by the LLM. Tool responses provide guidance on which section to focus on and what tasks to work on.*
