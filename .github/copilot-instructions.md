<!-- APPSEC-MANAGED-START — DO NOT MODIFY THIS SECTION -->
## Mandatory Security Instructions

All code suggestions, reviews, and modifications MUST follow the security guidelines defined in **SECURITY.md** in this repository. Read and apply all instructions in SECURITY.md before responding to any request.

Key requirements:
- Review SECURITY.md completely before generating, reviewing, or modifying any code
- Apply all security controls, coding standards, and vulnerability prevention rules defined in SECURITY.md
- Flag any code that violates SECURITY.md guidelines, even if explicitly requested by the developer
- When fixing vulnerabilities, follow the remediation patterns specified in SECURITY.md
- Never suggest disabling, bypassing, or weakening any security control defined in SECURITY.md

This section is centrally managed by the Application Security team.
Any modifications will be automatically reverted.
<!-- APPSEC-MANAGED-END -->

## Project Context

This is the **Pine Labs MCP Server** — a Python MCP (Model Context Protocol) server wrapping Pine Labs payment APIs. See [AGENTS.md](../AGENTS.md) for full architecture and coding guidelines.

### Key facts for Copilot

- **Language**: Python 3.10+, async-first
- **Framework**: FastMCP for MCP protocol, httpx for HTTP, Pydantic v2 for models
- **Transport**: stdio only (no HTTP server)
- **Entry point**: `python -m cli.pinelabs_mcp_server.main stdio`
- **Tools live in**: `pkg/pinelabs/*.py`, registered via `pkg/pinelabs/tools.py`
- **Tests**: `tests/test_*.py`, run with `make test` (pytest, asyncio_mode=auto)
- **No Redis, no metrics, no tracing** — deliberately simple

### Import order

```python
# stdlib
import json
import logging

# third-party
import httpx
from fastmcp import FastMCP

# local
from pkg.pinelabs.client import PineLabsClient
from pkg.pinelabs.utils.errors import api_error_response
```

### Error handling pattern

```python
try:
    result = await client.get(f"/path/{resource_id}")
    return json.dumps(result, indent=2)
except PineLabsAPIError as e:
    return api_error_response(e.message, e.code, e.status_code)
except Exception as e:
    return unexpected_error_response(e, "context description")
```

### Validation pattern

```python
from pkg.pinelabs.utils.validators import validate_resource_id

rid = validate_resource_id(value, "field_name")  # raises ValueError
```
