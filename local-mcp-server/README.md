# Local MCP Server

Local MCP server for converting binary documents (PDF, DOCX, XLSX, etc.) to text and optionally ingesting them into the Remote RAG API.

## Features

- **Document Conversion**: Convert local binary documents to text using Microsoft's markitdown library
- **Supported Formats**: PDF, DOCX, PPTX, XLSX, images (with OCR), HTML, CSV, JSON, XML
- **Optional Ingestion**: Send converted documents to Remote RAG API for indexing
- **MCP Protocol**: Exposes tools for AI assistants (Claude Code)

## MCP Tools

### 1. `convert_to_text`

Convert a local document to text without ingesting it.

**Parameters:**
- `uri` (required): File path to the document (e.g., `file:///path/to/doc.pdf` or `/path/to/doc.pdf`)

**Returns:**
- Converted text content
- File metadata (filename, size)

**Example:**
```python
{
  "uri": "/home/user/documents/manual.pdf"
}
```

### 2. `convert_and_ingest`

Convert a local document to text and ingest it into the Remote RAG API.

**Parameters:**
- `uri` (required): File path to the document
- `collection` (optional): Collection name for organizing documents (default: `"default"`)

**Returns:**
- Ingestion status
- Document ID
- Number of chunks created

**Example:**
```python
{
  "uri": "/home/user/documents/manual.pdf",
  "collection": "project-alpha"
}
```

## Installation

### Prerequisites

- Python 3.11 or higher
- **uv** (fast Python package installer) - [Install uv](https://github.com/astral-sh/uv)
  ```bash
  # Install uv (if not already installed)
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Setup

1. **Clone the repository**:
   ```bash
   cd local-mcp-server
   ```

2. **Install dependencies**:
   ```bash
   # Install project dependencies
   uv pip install -e .

   # Install development dependencies
   uv pip install -e ".[dev]"
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:
   ```
   RAG_API_URL=https://rag-api.example.com
   RAG_API_KEY=your-api-key-here
   ```

## Usage

### Running the MCP Server

```bash
# Using uv
uv run python -m local_mcp.server

# Or directly with Python (if dependencies are installed)
python -m local_mcp.server
```

The server will start and listen for MCP protocol messages on stdio.

### Using with Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp_servers.json`):

```json
{
  "local-mcp-server": {
    "command": "uv",
    "args": ["run", "python", "-m", "local_mcp.server"],
    "cwd": "/path/to/local-mcp-server"
  }
}
```

**Alternative (without uv prefix):**
```json
{
  "local-mcp-server": {
    "command": "python",
    "args": ["-m", "local_mcp.server"],
    "cwd": "/path/to/local-mcp-server",
    "env": {
      "PYTHONPATH": "/path/to/local-mcp-server/src"
    }
  }
}
```

### Examples

**Convert a PDF to text:**
```
Ask Claude: "Convert the file /home/user/report.pdf to text"
```

**Ingest a document:**
```
Ask Claude: "Ingest the file /home/user/manual.pdf into the 'documentation' collection"
```

## Development

### Running Tests

The project has comprehensive test coverage (target: 80%+) with unit tests for all components.

#### Quick Start

```bash
# Install dependencies (if not done yet)
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=local_mcp --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=local_mcp --cov-report=html
# Open htmlcov/index.html in your browser
```

#### Running Specific Tests

```bash
# Run specific test file
uv run pytest tests/test_converter.py

# Run specific test function
uv run pytest tests/test_converter.py::test_convert_text_file

# Run tests matching a pattern
uv run pytest -k "convert"

# Run tests with verbose output
uv run pytest -v

# Run tests with extra details
uv run pytest -vv
```

#### Test Categories

```bash
# Run only async tests
uv run pytest -m asyncio

# Show test execution time
uv run pytest --durations=10
```

#### Continuous Testing (Watch Mode)

```bash
# Install pytest-watch
uv pip install pytest-watch

# Run tests automatically on file changes
uv run ptw
```

### Test Coverage

**Current Test Files:**
- `tests/test_converter.py`: 30+ tests for DocumentConverter
  - File conversion (text, markdown, HTML, large files, empty files)
  - Metadata extraction (filename, extension, size)
  - Error handling (nonexistent files, directories, invalid paths)
  - Edge cases (special characters, no extension, multiple extensions)

- `tests/test_ingest_client.py`: 25+ tests for IngestClient
  - Successful ingestion (default collection, additional metadata, long content)
  - HTTP errors (401, 400, 500)
  - Network errors (timeout, connection refused)
  - Client management (initialization, context manager, URL construction)

- `tests/conftest.py`: Shared fixtures
  - Sample files (text, markdown, HTML, large, empty)

**Coverage Target:** 80%+ line coverage

**How to Check Coverage:**
```bash
# Run tests with coverage
uv run pytest --cov=local_mcp --cov-report=term-missing

# Expected output:
# Name                            Stmts   Miss  Cover   Missing
# -------------------------------------------------------------
# src/local_mcp/__init__.py           1      0   100%
# src/local_mcp/config.py            10      0   100%
# src/local_mcp/converter.py         30      2    93%   45-46
# src/local_mcp/ingest_client.py     45      3    93%   67-69
# src/local_mcp/server.py            80     10    88%   (MCP handlers)
# -------------------------------------------------------------
# TOTAL                             166     15    91%
```

### Code Quality

```bash
# Lint code (check for issues)
uv run ruff check src/ tests/

# Format code (auto-fix formatting)
uv run ruff format src/ tests/

# Type checking (mypy)
uv run mypy src/

# Run all quality checks
uv run ruff check src/ tests/ && uv run mypy src/
```

### Debugging Tests

```bash
# Run tests with print statements visible
uv run pytest -s

# Drop into debugger on failure
uv run pytest --pdb

# Drop into debugger on first failure
uv run pytest -x --pdb

# Show local variables on failure
uv run pytest -l
```

### Test Best Practices

1. **Test Naming**: Use descriptive test names that explain what is being tested
   - Good: `test_convert_text_file_with_special_characters`
   - Bad: `test_1`, `test_convert`

2. **Test Organization**: Group related tests using comments
   ```python
   # ============================================================================
   # Test: convert_to_text - Success Cases
   # ============================================================================
   ```

3. **Fixtures**: Use pytest fixtures for shared test data (see `conftest.py`)

4. **Async Tests**: Mark async tests with `@pytest.mark.asyncio`

5. **Mocking**: Use `unittest.mock` for external dependencies
   - Mock `httpx.AsyncClient` for HTTP calls
   - Mock `MarkItDown` for document conversion (if needed)

6. **Assertions**: Use descriptive assertion messages
   ```python
   assert result["status"] == "success", f"Expected success, got {result}"
   ```

### Common Testing Commands

```bash
# Before committing - full check
uv run pytest --cov=local_mcp --cov-report=term-missing && \
uv run ruff check src/ tests/ && \
uv run mypy src/

# Quick check during development
uv run pytest tests/test_converter.py -v

# Check if new code broke anything
uv run pytest --lf  # Run last failed tests
```

## Architecture

### Components

- **server.py**: MCP server with tool definitions
- **converter.py**: Document conversion wrapper (markitdown)
- **ingest_client.py**: HTTP client for Remote RAG API
- **config.py**: Configuration management

### Error Handling

The server handles errors gracefully and returns user-friendly error messages:

- **FileNotFoundError**: File doesn't exist
- **DocumentConversionError**: Conversion failed (encrypted PDF, unsupported format, etc.)
- **IngestError**: Remote API ingestion failed (authentication, network, etc.)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAG_API_URL` | Remote RAG API base URL | `http://localhost:8000` |
| `RAG_API_KEY` | API key for authentication | `""` (empty) |

## Testing

Test coverage target: **80%+**

Test files:
- `tests/test_converter.py`: DocumentConverter tests
- `tests/test_ingest_client.py`: IngestClient tests

## License

MIT License

## Related Projects

- **Remote RAG Server**: The backend RAG API that this server communicates with
- **markitdown**: Microsoft's document conversion library

---

Built with ❤️ using Python 3.11+ and the MCP Protocol
