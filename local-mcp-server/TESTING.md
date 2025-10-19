# Testing Guide - Local MCP Server

## Quick Start

```bash
# Navigate to project directory
cd local-mcp-server

# Install dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=local_mcp --cov-report=term-missing
```

## Test Coverage Summary

**Total Tests:** 55+ tests
**Coverage Target:** 80%+
**Test Files:** 3 files

### Test Breakdown

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_converter.py` | 30+ | DocumentConverter (conversion, metadata, errors) |
| `test_ingest_client.py` | 25+ | IngestClient (HTTP, errors, client management) |
| `conftest.py` | N/A | Shared fixtures |

## Running Tests

### Basic Commands

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=local_mcp

# HTML coverage report
uv run pytest --cov=local_mcp --cov-report=html
# Then open: htmlcov/index.html
```

### Specific Tests

```bash
# Single file
uv run pytest tests/test_converter.py

# Single test
uv run pytest tests/test_converter.py::test_convert_text_file

# Pattern matching
uv run pytest -k "convert_text"

# Verbose
uv run pytest -v
```

### Test Categories

```bash
# Async tests only
uv run pytest -m asyncio

# Show slowest tests
uv run pytest --durations=10

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf
```

## Expected Coverage Output

```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
src/local_mcp/__init__.py           1      0   100%
src/local_mcp/config.py            10      0   100%
src/local_mcp/converter.py         30      2    93%
src/local_mcp/ingest_client.py     45      3    93%
src/local_mcp/server.py            80     10    88%
-------------------------------------------------------------
TOTAL                             166     15    91%
```

## Test Files Overview

### test_converter.py

**Success Cases:**
- Convert text files
- Convert markdown files
- Convert HTML files
- Convert large files (10KB+)
- Convert empty files
- Handle special characters in filenames

**Error Cases:**
- Nonexistent files (FileNotFoundError)
- Directories (DocumentConversionError)
- Invalid paths

**Metadata Extraction:**
- Filename extraction
- Extension extraction (.txt, .md, .html)
- File size calculation
- No extension handling
- Multiple extensions (file.tar.gz)

### test_ingest_client.py

**Success Cases:**
- Basic ingestion
- Default collection
- Custom collection
- Additional metadata
- Long content (160KB+)

**HTTP Error Cases:**
- 401 Unauthorized
- 400 Bad Request
- 500 Server Error
- Network timeout
- Connection refused

**Client Management:**
- Initialization
- URL normalization (trailing slashes)
- Client creation and reuse
- Context manager usage
- Proper cleanup on close

## Code Quality Checks

```bash
# Linting
uv run ruff check src/ tests/

# Auto-format
uv run ruff format src/ tests/

# Type checking
uv run mypy src/

# All checks at once
uv run pytest --cov=local_mcp && \
uv run ruff check src/ tests/ && \
uv run mypy src/
```

## Debugging Tests

```bash
# Show print statements
uv run pytest -s

# Drop into debugger on failure
uv run pytest --pdb

# Show local variables
uv run pytest -l

# Verbose + local variables
uv run pytest -vl
```

## Continuous Testing

```bash
# Install watch tool
uv pip install pytest-watch

# Auto-run tests on file changes
uv run ptw
```

## Common Issues and Solutions

### Issue: Tests fail with "ModuleNotFoundError"

**Solution:**
```bash
# Ensure you're in the project directory
cd local-mcp-server

# Reinstall dependencies
uv pip install -e ".[dev]"
```

### Issue: Async tests don't run

**Solution:**
```bash
# Ensure pytest-asyncio is installed
uv pip install pytest-asyncio

# Check pytest.ini configuration
cat pyproject.toml | grep asyncio_mode
```

### Issue: Coverage report shows 0%

**Solution:**
```bash
# Use correct package name
uv run pytest --cov=local_mcp

# Not: --cov=src/local_mcp
```

### Issue: Tests pass locally but fail in CI

**Solution:**
- Check Python version (must be 3.11+)
- Verify all dev dependencies are installed
- Check for hardcoded paths in tests

## Test Writing Guidelines

### 1. Use Descriptive Names

```python
# Good
def test_convert_text_file_with_special_characters():
    pass

# Bad
def test_1():
    pass
```

### 2. Group Related Tests

```python
# ============================================================================
# Test: convert_to_text - Success Cases
# ============================================================================

def test_success_case_1():
    pass

def test_success_case_2():
    pass
```

### 3. Use Fixtures for Shared Data

```python
@pytest.fixture
def sample_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    return str(file_path)

def test_something(sample_file):
    # Use sample_file here
    pass
```

### 4. Mock External Dependencies

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    with patch.object(httpx.AsyncClient, "post") as mock:
        mock.return_value = AsyncMock(...)
        # Test code here
```

### 5. Test Both Success and Failure

```python
def test_success_case():
    result = function()
    assert result == expected

def test_error_case():
    with pytest.raises(CustomError):
        function_that_fails()
```

## Pre-Commit Checklist

Before committing code, run:

```bash
# 1. Run all tests
uv run pytest

# 2. Check coverage (should be ≥80%)
uv run pytest --cov=local_mcp --cov-report=term-missing

# 3. Lint code
uv run ruff check src/ tests/

# 4. Type check
uv run mypy src/

# 5. Format code
uv run ruff format src/ tests/
```

Or use this one-liner:

```bash
uv run pytest --cov=local_mcp --cov-report=term-missing && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
echo "All checks passed!"
```

## CI/CD Integration (Future)

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      - name: Run tests
        run: uv run pytest --cov=local_mcp --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

**For more details, see [README.md](README.md)**
