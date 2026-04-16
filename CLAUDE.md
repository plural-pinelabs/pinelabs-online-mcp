# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/code) and other AI agents working on this repository.

## Project

Pine Labs MCP Server — Python 3.10+ async MCP server wrapping Pine Labs payment APIs.
Uses FastMCP, httpx, Pydantic v2. Stdio transport only. No Redis, no metrics, no tracing.

## Build & Test

```bash
make test       # Run all tests (pytest, asyncio_mode=auto)
make fmt        # Format with ruff
make lint       # Lint with ruff
make local-run  # Run server via stdio
```

## Architecture

- **Entry point**: `cli/pinelabs_mcp_server/main.py` (argparse CLI → stdio)
- **Server factory**: `pkg/pinelabs/server.py` → `new_pinelabs_mcp_server(settings)`
- **Client**: `pkg/pinelabs/client.py` → `PineLabsClient` (httpx + in-memory token cache)
- **Config**: `pkg/pinelabs/config.py` → `Settings` (env vars + CLI overrides)
- **Tool registration**: `pkg/pinelabs/tools.py` → `register_all_tools(mcp, client)`
- **Tool modules**: `pkg/pinelabs/{resource}.py` → `register_{resource}_tools(mcp, client)`
- **Models**: `pkg/pinelabs/models/{resource}.py` (Pydantic v2)
- **Validators**: `pkg/pinelabs/utils/validators.py`
- **Errors**: `pkg/pinelabs/utils/errors.py`

## Coding Patterns

Import order: stdlib → third-party → pkg.* (separated by blank lines).

Error handling in tools:
```python
try:
    result = await client.get(f"/path/{rid}")
    return json.dumps(result, indent=2)
except PineLabsAPIError as e:
    return api_error_response(e.message, e.code, e.status_code)
except Exception as e:
    return unexpected_error_response(e, "context")
```

Input validation: `validate_resource_id(value, "field_name")` raises `ValueError`.

## Test Fixtures

Tests use `fake_mcp` (stub MCP capturing registrations) and `mock_client` (AsyncMock of PineLabsClient) from `tests/conftest.py`.
