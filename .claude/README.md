# Pine Labs MCP Server

## Overview

Python 3.10+ async MCP server wrapping Pine Labs payment APIs.
Uses FastMCP for protocol, httpx for HTTP, Pydantic v2 for models. Stdio transport only.

See AGENTS.md for full architecture, tool inventory, and contribution workflow.

## Structure

```
cli/pinelabs_mcp_server/     → CLI entry point
pkg/pinelabs/                → Tools, client, config, server factory
pkg/pinelabs/models/         → Pydantic request models
pkg/pinelabs/utils/          → Validators, errors, api docs config
pkg/toolsets/                → Toolset grouping abstraction
tests/                       → pytest async tests
```

## Key Commands

```bash
make test       # pytest
make fmt        # ruff format
make lint       # ruff check
make local-run  # stdio server
```

## Conventions

- Async tool handlers returning JSON strings
- `validate_resource_id()` for input validation
- `api_error_response()` / `unexpected_error_response()` for errors
- Import order: stdlib → third-party → pkg.*
- One file per resource: `pkg/pinelabs/{resource}.py`
- Registration: `register_{resource}_tools(mcp, client)` called from `tools.py`
- Tests: `fake_mcp` + `mock_client` fixtures from `conftest.py`
- No Redis, no metrics, no tracing

## Security

Follow SECURITY.md. Never log credentials. Validate all inputs.
