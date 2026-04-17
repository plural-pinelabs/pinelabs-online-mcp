# Pine Labs MCP Tool Generator

Generate complete MCP tool implementations from Pine Labs API documentation, curl commands, or request/response examples.

## Input Formats

The user may provide any of:

1. **Pine Labs docs URL** — fetch and extract endpoint details
2. **curl command** — parse method, path, headers, body, and response
3. **Request/response JSON** — infer params and types
4. **API specification** — method, path, parameters

If the **tool name** is not provided or cannot be inferred, **ask the user** before proceeding.

## Workflow

```
- [ ] Step 1: Parse input and extract API contract
- [ ] Step 2: Determine tool name and resource file
- [ ] Step 3: Implement tool function
- [ ] Step 4: Register tool in tools.py
- [ ] Step 5: Add Pydantic models (if needed)
- [ ] Step 6: Write unit tests
- [ ] Step 7: Run linter — fix errors
- [ ] Step 8: Run tests — fix errors
```

## Step 1: Parse Input

Extract: HTTP method, endpoint path, required/optional parameters with types, and example response.

Map parameters:
- `str` → `validate_resource_id()` or raw string param
- `int` / `float` → typed parameter
- `dict` → Pydantic model
- `list` → typed list parameter
- `bool` → boolean parameter

## Step 2: Determine Tool Name and File

Naming conventions:
- Fetch single: `get_{resource}` or `get_{resource}_by_{field}`
- Fetch list: `get_{resources}` or `list_{resources}`
- Create: `create_{resource}`
- Update: `update_{resource}`
- Delete: `delete_{resource}` or `cancel_{resource}`

Place in `pkg/pinelabs/{resource_type}.py`. Create new file only if needed.

## Step 3: Implement Tool

```python
import json
import logging

from fastmcp import FastMCP

from pkg.pinelabs.client import PineLabsClient, PineLabsAPIError
from pkg.pinelabs.utils.errors import (
    api_error_response,
    validation_error_response,
    unexpected_error_response,
)
from pkg.pinelabs.utils.validators import validate_resource_id

logger = logging.getLogger("pinelabs-mcp-server.{resource}")


def register_{resource}_tools(
    mcp: FastMCP, client: PineLabsClient
) -> None:

    @mcp.tool(
        name="tool_name",
        description=(
            "Action verb + what it does. "
            "When to use / prerequisites. "
            "Constraints or return format."
        ),
    )
    async def tool_name(required_param: str) -> str:
        rid = validate_resource_id(required_param, "param_name")

        try:
            result = await client.get(f"/path/{rid}")
            return json.dumps(result, indent=2)
        except PineLabsAPIError as e:
            return api_error_response(
                e.message, e.code, e.status_code
            )
        except Exception as e:
            return unexpected_error_response(e, "context")
```

## Step 4: Register in tools.py

In `pkg/pinelabs/tools.py`:
1. Import `register_{resource}_tools`
2. Create a `Toolset` with `add_read_tools()` / `add_write_tools()`
3. Add to `group` via `group.add_toolset()`
4. Call `register_{resource}_tools(mcp, client)` at the bottom

## Step 5: Add Models (if needed)

Create `pkg/pinelabs/models/{resource}.py` with Pydantic v2 models.

## Step 6: Write Tests

Create `tests/test_{resource}_tool.py`:

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
        mock_client.get.return_value = {"id": "123", "status": "ACTIVE"}
        result = await tool(required_param="123")
        data = json.loads(result)
        assert data["id"] == "123"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_error(self, tool, mock_client):
        result = await tool(required_param="")
        data = json.loads(result)
        assert data["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_api_error(self, tool, mock_client):
        mock_client.get.side_effect = PineLabsAPIError(
            404, "NOT_FOUND", "Resource not found"
        )
        result = await tool(required_param="valid-id")
        data = json.loads(result)
        assert data["code"] == "NOT_FOUND"
        assert data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_unexpected_error(self, tool, mock_client):
        mock_client.get.side_effect = RuntimeError("boom")
        result = await tool(required_param="valid-id")
        data = json.loads(result)
        assert data["code"] == "INTERNAL_ERROR"
```

## Step 7 & 8: Verify

```bash
make lint   # fix any issues
make test   # all tests must pass
```

## Completion Checklist

- [ ] Tool function in `pkg/pinelabs/{resource}.py`
- [ ] Tool registered in `pkg/pinelabs/tools.py`
- [ ] Pydantic models in `pkg/pinelabs/models/{resource}.py` (if needed)
- [ ] Tests in `tests/test_{resource}_tool.py` (success + validation + API error + unexpected)
- [ ] Lint passes (`make lint`)
- [ ] Tests pass (`make test`)
