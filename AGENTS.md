# Agent Instructions

This file provides instructions for AI coding agents working on this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that wraps Pine Labs payment APIs. It uses **FastMCP** for the MCP protocol, **httpx** for async HTTP, and **Pydantic** for request/response validation. Transport is stdio-only (no HTTP server).

## Directory Layout

```
cli/pinelabs_mcp_server/     # CLI entry point (argparse + stdio runner)
pkg/
  log/                       # Logging setup (LogConfig, setup_logging)
  observability/              # Observability stubs
  toolsets/                   # Toolset/ToolsetGroup for read/write grouping
  pinelabs/
    client.py                 # PineLabsClient — async httpx + in-memory token cache
    config.py                 # Settings from env vars / CLI overrides
    server.py                 # MCP server factory (new_pinelabs_mcp_server)
    tools.py                  # Central tool registration (register_all_tools)
    models/                   # Pydantic request/response models
    utils/                    # Shared validators, errors, API docs config
    *.py                      # One file per resource (payment_links, orders, …)
tests/                        # pytest tests — one test file per source module
```

## Key Commands

```bash
make test       # Run all tests (pytest)
make fmt        # Format code (ruff format)
make lint       # Lint code (ruff check)
make build      # Build Docker image
make local-run  # Run locally via stdio
make clean      # Remove __pycache__ and caches
```

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <ID> --client-secret <SECRET> \
  --env uat
```

## Code Conventions

- **Python 3.10+** (uses `from __future__ import annotations` where needed)
- **Async-first**: all tool handlers and client methods are `async`
- **No Redis, no metrics, no tracing** — kept deliberately simple
- **In-memory token cache** with TTL in `PineLabsClient`
- **Pydantic v2** for all request models
- **Error handling**: use `pkg.pinelabs.utils.errors` helpers (`error_response`, `api_error_response`, `validation_error_response`, `unexpected_error_response`) — they return JSON strings
- **Input validation**: use `validate_resource_id()` and `validate_path_param()` from `pkg.pinelabs.utils.validators`
- **Imports**: stdlib → third-party → `pkg.*` (local), separated by blank lines

## Adding a New Tool

### Step 1: Create the tool file

Add `pkg/pinelabs/{resource}.py` with a `register_{resource}_tools(mcp, client)` function:

```python
from fastmcp import FastMCP
from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id

def register_{resource}_tools(mcp: FastMCP, client: PineLabsClient) -> None:

    @mcp.tool(
        name="tool_name",
        description=(
            "Action verb + what it does + key context. "
            "When to use / prerequisites. "
            "Constraints, units, or return format."
        ),
    )
    async def tool_name(required_param: str, optional_param: str = "") -> str:
        # Validate inputs
        rid = validate_resource_id(required_param, "param_name")

        try:
            result = await client.get(f"/path/{rid}")
            return json.dumps(result, indent=2)
        except PineLabsAPIError as e:
            return api_error_response(e.message, e.code, e.status_code)
        except Exception as e:
            return unexpected_error_response(e, "doing the thing")
```

### Step 2: Register in tools.py

In `pkg/pinelabs/tools.py`:
1. Import `register_{resource}_tools`
2. Add a `Toolset` with read/write tool names
3. Call `register_{resource}_tools(mcp, client)` at the bottom

### Step 3: Add Pydantic models (if needed)

Add to `pkg/pinelabs/models/{resource}.py`. Import in the tool file.

### Step 4: Write tests

Create `tests/test_{resource}_tool.py`. Use the `fake_mcp` and `mock_client` fixtures from `conftest.py`:

```python
import json
from unittest.mock import AsyncMock
import pytest
from pkg.pinelabs.client import PineLabsAPIError
from pkg.pinelabs.{resource} import register_{resource}_tools

@pytest.fixture
def tool(fake_mcp, mock_client):
    register_{resource}_tools(fake_mcp, mock_client)
    return fake_mcp.tools["tool_name"]

class TestToolName:
    @pytest.mark.asyncio
    async def test_success(self, tool, mock_client):
        mock_client.get.return_value = {"id": "123"}
        result = await tool(required_param="123")
        data = json.loads(result)
        assert data["id"] == "123"

    @pytest.mark.asyncio
    async def test_api_error(self, tool, mock_client):
        mock_client.get.side_effect = PineLabsAPIError(404, "NOT_FOUND", "Not found")
        result = await tool(required_param="123")
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"
```

### Step 5: Verify

```bash
make test   # all tests pass
make lint   # no lint errors
```

## Tool Description Guidelines

Tool descriptions are what LLMs read to decide which tool to call. Every description must answer:
1. **What** does this tool do?
2. **When** should an LLM pick this tool?
3. **What** constraints or gotchas exist? (units, required states, return format)

Start with an action verb. Keep to 2-4 sentences. If similar tools exist, explain when to pick THIS one.

## Registered Tools (37 total)

| Toolset | Tools |
|---------|-------|
| payment_links | `create_payment_link`, `get_payment_link_by_id`, `get_payment_link_by_merchant_reference`, `cancel_payment_link`, `resend_payment_link_notification` |
| orders | `get_order_by_order_id`, `cancel_order` |
| checkout_orders | `create_order` |
| subscriptions | `create_plan`, `update_plan`, `delete_plan`, `get_plans`, `get_plan_by_id`, `get_plan_by_merchant_reference`, `create_subscription`, `pause_subscription`, `resume_subscription`, `cancel_subscription`, `update_subscription`, `get_subscriptions`, `get_subscription_by_id`, `get_subscription_by_merchant_reference`, `create_presentation`, `delete_presentation`, `get_presentation`, `get_presentations_by_subscription_id`, `get_presentation_by_merchant_reference`, `send_subscription_notification`, `create_debit`, `create_merchant_retry` |
| upi_intent_qr | `create_upi_intent_payment_with_qr` |
| mcp_api | `get_payment_link_details`, `get_order_details`, `get_refund_order_details`, `search_transaction` |
| api_docs | `get_api_documentation`, `list_pinelabs_apis` |
| success_rate | `get_merchant_success_rate` |

## Architecture Notes

- **PineLabsClient** (`pkg/pinelabs/client.py`): handles OAuth2 client-credentials flow with in-memory token cache, retry with exponential backoff, and structured error responses via `PineLabsAPIError`.
- **Settings** (`pkg/pinelabs/config.py`): reads from env vars (`PINELABS_CLIENT_ID`, `PINELABS_CLIENT_SECRET`, `PINELABS_ENV`) with constructor `**overrides` for CLI args.
- **Server factory** (`pkg/pinelabs/server.py`): `new_pinelabs_mcp_server(settings, read_only, enabled_toolsets)` creates the FastMCP instance.
- **Toolsets** (`pkg/toolsets/toolsets.py`): `Toolset` groups tools as read/write; `ToolsetGroup` manages enable/disable.
