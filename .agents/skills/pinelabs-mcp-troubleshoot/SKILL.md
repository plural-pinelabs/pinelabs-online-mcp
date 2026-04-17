---
name: pinelabs-mcp-troubleshoot
description: "Diagnose and fix Pine Labs MCP server issues. Use when: the server won't start, tools aren't showing up, authentication fails, API calls return errors, the MCP client can't connect, or tests fail. Covers connection problems, credential issues, environment mismatches, timeout errors, token cache problems, and Docker runtime issues."
---

# Pine Labs MCP Troubleshoot

Diagnose and resolve issues with the Pine Labs MCP server running locally.

## When to Use

- Server won't start or crashes immediately
- MCP client shows "server disconnected" or "failed to connect"
- Authentication errors (401, invalid credentials, token failures)
- Tools don't appear in the MCP client
- API calls return unexpected errors
- Tests fail after setup
- Docker container exits or won't build

## Diagnostic Procedure

Follow this sequence — each step narrows the problem category.

### Step 1: Verify Python Environment

```bash
# Check Python version (need 3.10+)
python3 --version

# Check virtual environment is active
which python
# Should point to .venv/bin/python, NOT system Python

# If not active:
source .venv/bin/activate

# Check dependencies installed
pip list | grep -E "fastmcp|httpx|pydantic"
# All three must be present
```

**Common fix**: `pip install -r requirements.txt`

### Step 2: Verify Server Starts

```bash
# Start with debug logging
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <ID> --client-secret <SECRET> \
  --env uat --log-level DEBUG --log-file /tmp/mcp-debug.log
```

Check the log file for errors:
```bash
cat /tmp/mcp-debug.log
```

**Common errors**:

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: cli` | Wrong working directory | `cd` to project root |
| `ModuleNotFoundError: fastmcp` | Dependencies not installed | `pip install -r requirements.txt` |
| `ImportError` | Python version too old | Upgrade to 3.10+ |
| `Address already in use` | Port conflict (HTTP mode) | Use different `--port` or kill existing process |

### Step 3: Verify Credentials

```bash
# Test authentication directly
python -c "
import asyncio
from pkg.pinelabs.client import PineLabsClient

async def test():
    client = PineLabsClient(
        client_id='<ID>',
        client_secret='<SECRET>',
        base_url='https://pluraluat.v2.pinepg.in/api',
        token_url='https://pluraluat.v2.pinepg.in/api/auth/v1/token',
    )
    token = await client._get_token()
    print(f'Token obtained: {token[:20]}...')
    await client.close()

asyncio.run(test())
"
```

**Common errors**:

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Wrong client ID or secret | Verify credentials with Pine Labs dashboard |
| `ConnectionError` | Network/firewall blocking | Check internet, VPN, proxy settings |
| `TimeoutError` | API unreachable | Check `PINELABS_BASE_URL` matches environment |
| `SSL certificate error` | Corporate proxy/MITM | Set `SSL_CERT_FILE` env var or check proxy config |

### Step 4: Verify MCP Client Config

#### VS Code

1. Open Command Palette → `MCP: List Servers`
2. Check if "pinelabs" appears
3. If not, verify `.vscode/mcp.json` exists and has correct syntax
4. Check Output panel → "MCP" channel for errors
5. Verify `python` command resolves to the correct interpreter (venv)

**Fix for wrong Python path**: Use absolute path in config:
```json
"command": "/path/to/project/.venv/bin/python"
```

#### Claude Desktop

1. Check config at `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Verify JSON is valid (no trailing commas)
3. Restart Claude Desktop after config changes
4. Check Console.app for `claude` process errors (macOS)

#### Cursor

1. Check `.cursor/mcp.json` in project root
2. Verify JSON syntax
3. Restart Cursor after changes
4. Check Developer Console (Help → Toggle Developer Tools)

### Step 5: Verify Tools Are Registered

```bash
# Run tests to confirm tool registration works
make test
```

If only some tools are missing, check:
- `--toolsets` flag — may be limiting which toolsets load
- `--read-only` flag — hides write tools
- Check `pkg/pinelabs/tools.py` for registration order

### Step 6: Check Docker Issues

```bash
# Verify image builds
docker build -t pinelabs-mcp-server .

# Run with debug logging
docker run --rm \
  -e PINELABS_CLIENT_ID=<ID> \
  -e PINELABS_CLIENT_SECRET=<SECRET> \
  -e PINELABS_ENV=uat \
  -e LOG_LEVEL=DEBUG \
  pinelabs-mcp-server

# Check for permission issues (non-root user)
docker run --rm --entrypoint sh pinelabs-mcp-server -c "whoami && ls -la /app"
```

**Common Docker issues**:

| Issue | Cause | Fix |
|-------|-------|-----|
| Build fails at pip install | Network in build context | Use `--network host` or configure proxy |
| Container exits immediately | Missing env vars | Pass all required env vars via `-e` or `.env` |
| Permission denied | Non-root user can't access files | Check file ownership in Dockerfile |
| Can't connect from host | stdio transport needs special handling | Use `docker compose` from `examples/` |

## Error Pattern Reference

### API Errors (from tool responses)

| Response Code | Meaning | Action |
|---------------|---------|--------|
| `VALIDATION_ERROR` | Invalid input to tool | Check parameter format (IDs, amounts) |
| `NOT_FOUND` | Resource doesn't exist | Verify ID, check environment (uat vs prod data) |
| `UNAUTHORIZED` | Token expired or invalid | Restart server to refresh token cache |
| `RATE_LIMITED` | Too many requests | Wait and retry; reduce request frequency |
| `INTERNAL_ERROR` | Unexpected server-side error | Check logs, report if persistent |

### Environment Mismatches

| Symptom | Likely cause |
|---------|-------------|
| Resources exist in dashboard but API returns 404 | Wrong `--env` (uat vs prod) |
| Auth works but no data | Credentials are for different environment |
| Amounts look wrong | Pine Labs uses paisa (100 paisa = ₹1) |

## Quick Fixes Checklist

- [ ] Python 3.10+ and venv activated?
- [ ] `pip install -r requirements.txt` done?
- [ ] Running from project root directory?
- [ ] Credentials correct for the target environment?
- [ ] Network access to `pluraluat.v2.pinepg.in` or `api.pluralpay.in`?
- [ ] MCP client config has valid JSON?
- [ ] MCP client restarted after config change?
- [ ] `make test` passes?
- [ ] Log file shows successful token acquisition?
