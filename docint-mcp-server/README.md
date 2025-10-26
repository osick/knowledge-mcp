# Document Intelligence MCP Server

A lightweight MCP server for searching and retrieving documents from Azure AI Search indexes.

## Features

- **Hybrid Search**: Search documents using Azure AI Search's hybrid search (keyword + vector)
- **Document Retrieval**: Get specific documents by ID
- **Index Management**: List available search indexes
- **Simple Integration**: Easy to configure and use with AI assistants

## Quick Start

### Installation

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Azure AI Search credentials:
```bash
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_KEY=your-api-key
```

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=docint_mcp --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_azure_search_client.py -v
```

## MCP Tools

### search_documents

Search for relevant documents in Azure AI Search indexes.

**Parameters:**
- `query` (required): Search query string
- `index_name` (optional): Index to search (default: "default")
- `top` (optional): Number of results (1-50, default: 5)

### list_indexes

List all available Azure AI Search indexes.

### get_document

Retrieve a specific document by ID.

**Parameters:**
- `document_id` (required): Document ID to retrieve
- `index_name` (optional): Index containing the document (default: "default")

## Usage with Claude Desktop

Add to your Claude Desktop configuration:

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

## Development

### Project Structure

```
docint-mcp-server/
├── src/docint_mcp/
│   ├── __init__.py
│   ├── server.py              # MCP server
│   ├── azure_search_client.py # Azure Search wrapper
│   ├── config.py              # Configuration
│   └── models.py              # Data models
├── tests/
│   ├── conftest.py            # Test fixtures
│   ├── test_azure_search_client.py
│   └── test_server.py
└── pyproject.toml
```

### Running Linters

```bash
# Ruff
uv run ruff check src/

# MyPy
uv run mypy src/
```

## License

MIT License
