---
name: pinelabs-mcp-local-setup
description: "Set up Pine Labs MCP server locally and generate config for any MCP client. Use when: the user wants to run the MCP server on their machine, connect it to VS Code Copilot, Claude Desktop, or Cursor, set up credentials, create .env files, configure Docker, or integrate the server into their development workflow. Covers first-time setup, config generation, environment selection (uat/prod), read-only mode, and toolset filtering."
argument-hint: "Specify client: vscode, claude-desktop, cursor (or 'all')"
---

# Pine Labs MCP Local Setup

Guide users through setting up the Pine Labs MCP server locally and generating configuration for their preferred MCP client.

## When to Use

- User wants to run Pine Labs MCP server locally (source or Docker)
- User needs config for VS Code, Claude Desktop, or Cursor
- User asks how to connect to the MCP server
- User needs to set up credentials or environment variables
- User wants to switch between UAT and production environments

## Prerequisites Check

Before starting, verify:

1. **Python 3.10+** is installed: `python3 --version`
2. **Project is cloned** and user is in the project root
3. **Credentials available**: User has Pine Labs `client_id` and `client_secret`

If Docker-based setup, only Docker is needed.

## Setup Methods

### Method 1: Source (Recommended for Development)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (optional — avoids passing CLI args)
cat > .env << 'EOF'
PINELABS_CLIENT_ID=<your-client-id>
PINELABS_CLIENT_SECRET=<your-client-secret>
PINELABS_ENV=uat
LOG_LEVEL=INFO
EOF

# 4. Test the server starts
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <your-client-id> \
  --client-secret <your-client-secret> \
  --env uat
```

### Method 2: Docker

```bash
# 1. Create .env file
cat > .env << 'EOF'
PINELABS_CLIENT_ID=<your-client-id>
PINELABS_CLIENT_SECRET=<your-client-secret>
PINELABS_ENV=uat
EOF

# 2. Build the image
docker build -t pinelabs-mcp-server .

# 3. Run via docker compose
cd examples && docker compose up
```

## Client Configuration Generation

Ask the user which client they need, then generate the appropriate config.

### VS Code (Copilot Chat)

**File**: `.vscode/mcp.json` (workspace) or user settings

```json
{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "pinelabs_client_id",
        "description": "Pine Labs Client ID"
      },
      {
        "type": "promptString",
        "id": "pinelabs_client_secret",
        "description": "Pine Labs Client Secret",
        "password": true
      }
    ],
    "servers": {
      "pinelabs": {
        "command": "python",
        "args": [
          "-m", "cli.pinelabs_mcp_server.main", "stdio",
          "--client-id", "${input:pinelabs_client_id}",
          "--client-secret", "${input:pinelabs_client_secret}"
        ]
      }
    }
  }
}
```

**With env and toolset options** (append to args array as needed):
- `"--env", "prod"` — use production environment
- `"--read-only"` — only register read tools
- `"--toolsets", "payment_links,orders"` — enable specific toolsets only

### Claude Desktop

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

Claude Desktop does not support input prompts — use the `env` key for credentials:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "python",
      "args": ["-m", "cli.pinelabs_mcp_server.main", "stdio"],
      "env": {
        "PINELABS_CLIENT_ID": "<your-client-id>",
        "PINELABS_CLIENT_SECRET": "<your-client-secret>",
        "PINELABS_ENV": "uat"
      }
    }
  }
}
```

### Cursor

**File**: `.cursor/mcp.json` (workspace) or `~/.cursor/mcp.json` (global)

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "python",
      "args": [
        "-m", "cli.pinelabs_mcp_server.main", "stdio",
        "--client-id", "<your-client-id>",
        "--client-secret", "<your-client-secret>"
      ]
    }
  }
}
```

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PINELABS_CLIENT_ID` | Yes | — | OAuth2 client ID |
| `PINELABS_CLIENT_SECRET` | Yes | — | OAuth2 client secret |
| `PINELABS_ENV` | No | `uat` | `uat` or `prod` |
| `PINELABS_BASE_URL` | No | auto | Override API base URL |
| `PINELABS_TOKEN_URL` | No | auto | Override token endpoint |
| `LOG_LEVEL` | No | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `LOG_FILE` | No | stderr | Log output path |
| `HTTP_TIMEOUT` | No | `30.0` | Request timeout in seconds |

### CLI Arguments

| Argument | Env equivalent | Description |
|----------|---------------|-------------|
| `--client-id` | `PINELABS_CLIENT_ID` | OAuth2 client ID |
| `--client-secret` | `PINELABS_CLIENT_SECRET` | OAuth2 client secret |
| `--env` | `PINELABS_ENV` | `uat` or `prod` |
| `--log-file` | `LOG_FILE` | Log output path |
| `--log-level` | `LOG_LEVEL` | Logging level |
| `--read-only` | — | Register only read tools |
| `--toolsets` | — | Comma-separated toolset list |

### Available Toolsets

| Toolset | Tools (count) | Type |
|---------|--------------|------|
| `payment_links` | 5 | Read + Write |
| `orders` | 2 | Read + Write |
| `checkout_orders` | 1 | Write |
| `subscriptions` | 22 | Read + Write |
| `upi_intent_qr` | 1 | Write |
| `mcp_api` | 4 | Read |
| `api_docs` | 2 | Read |
| `success_rate` | 1 | Read |

### API Endpoints

| Environment | Base URL | Token URL |
|-------------|----------|-----------|
| UAT | `https://pluraluat.v2.pinepg.in/api` | `https://pluraluat.v2.pinepg.in/api/auth/v1/token` |
| Production | `https://api.pluralpay.in/api` | `https://api.pluralpay.in/api/auth/v1/token` |

## Workflow

1. Ask which client(s) the user needs (VS Code, Claude Desktop, Cursor)
2. Ask whether they want source-based or Docker-based setup
3. Check if they have credentials ready
4. Generate the setup steps and config file(s)
5. Help them verify the server starts with: `make test` (source) or `docker build` + `docker compose up` (Docker)
6. Confirm the MCP client detects the server and tools are listed

## Security Notes

- Never commit credentials to version control
- Prefer environment variables or input prompts over hardcoded secrets
- Use `--read-only` in production-facing setups to prevent write operations
- Use `--toolsets` to limit tool surface area to what is needed
