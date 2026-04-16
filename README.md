# Pine Labs MCP Server (Official)

The Pine Labs Online MCP Server implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) to enable seamless integration between Pine Labs' online payment APIs and AI tools. It allows AI assistants to perform Pine Labs Online API operations, empowering developers to build intelligent, AI-driven payment applications with ease.

## Quick Start

Choose your preferred setup method:
- **[Remote MCP Server](#remote-mcp-server-recommended)** - Hosted by Pine Labs, no setup required
- **[Local MCP Server](#local-mcp-server)** - Run on your own infrastructure

## Available Tools

Currently, the Pine Labs MCP Server provides the following tools:

### Payment Links

| Tool | Description | API |
|:-----|:------------|:----|
| `create_payment_link` | Create a new Pine Labs payment link | [Payment Link - Create](https://developer.pinelabsonline.com/reference/payment-link-create) |
| `get_payment_link_by_id` | Fetch a payment link by its payment link ID | [Payment Link - Get by ID](https://developer.pinelabsonline.com/reference/payment-link-get-by-payment-link-id) |
| `get_payment_link_by_merchant_reference` | Fetch a payment link by its merchant payment link reference | [Payment Link - Get by Reference](https://developer.pinelabsonline.com/reference/payment-link-get-by-merchant-payment-link-reference) |
| `cancel_payment_link` | Cancel a payment link | [Payment Link - Cancel](https://developer.pinelabsonline.com/reference/payment-link-cancel) |
| `resend_payment_link_notification` | Resend a payment link notification to the customer | [Payment Link - Resend](https://developer.pinelabsonline.com/reference/payment-link-resend) |

### Orders

| Tool | Description | API |
|:-----|:------------|:----|
| `get_order_by_order_id` | Retrieve order details by order ID | [Order - Get by ID](https://developer.pinelabsonline.com/reference/orders-get-by-order-id) |
| `cancel_order` | Cancel a pre-authorized payment against an order | [Order - Cancel](https://developer.pinelabsonline.com/reference/orders-cancel) |

### Checkout Orders

| Tool | Description | API |
|:-----|:------------|:----|
| `create_order` | Create a new checkout order and generate a checkout link | [Order - Create](https://developer.pinelabsonline.com/reference/orders-create) |

### Subscriptions

| Tool | Description | API |
|:-----|:------------|:----|
| `create_plan` | Create a new subscription plan | [Plan - Create](https://developer.pinelabsonline.com/reference/create-plan) |
| `get_plans` | Retrieve subscription plans | [Plan - Get All](https://developer.pinelabsonline.com/reference/get-all-plans) |
| `get_plan_by_id` | Retrieve a subscription plan by plan ID | [Plan - Get Specific](https://developer.pinelabsonline.com/reference/get-specific-plan) |
| `get_plan_by_merchant_reference` | Retrieve a plan by merchant plan reference | [Plan - Get Specific](https://developer.pinelabsonline.com/reference/get-specific-plan) |
| `update_plan` | Update an existing subscription plan | [Plan - Update](https://developer.pinelabsonline.com/reference/update-plan) |
| `delete_plan` | Delete a subscription plan | [Plan - Delete](https://developer.pinelabsonline.com/reference/delete-plan) |
| `create_subscription` | Create a new subscription against a plan | [Subscription - Create](https://developer.pinelabsonline.com/reference/create-subscription) |
| `get_subscriptions` | Retrieve subscriptions | [Subscription - Get All](https://developer.pinelabsonline.com/reference/get-all-subscriptions) |
| `get_subscription_by_id` | Retrieve a subscription by subscription ID | [Subscription - Get Specific](https://developer.pinelabsonline.com/reference/get-specific-subscription) |
| `get_subscription_by_merchant_reference` | Retrieve a subscription by merchant reference | [Subscription - Get Specific](https://developer.pinelabsonline.com/reference/get-specific-subscription) |
| `pause_subscription` | Pause an active subscription | [Subscription - Pause](https://developer.pinelabsonline.com/reference/pause-subscription) |
| `resume_subscription` | Resume a paused subscription | [Subscription - Resume](https://developer.pinelabsonline.com/reference/resume-subscription) |
| `cancel_subscription` | Cancel an active subscription | [Subscription - Cancel](https://developer.pinelabsonline.com/reference/cancel-subscription) |
| `update_subscription` | Update an existing subscription | [Subscription - Update](https://developer.pinelabsonline.com/reference/update-subscription) |
| `create_presentation` | Create a presentation (payment request) for a subscription | [Presentation - Create](https://developer.pinelabsonline.com/reference/create-presentation) |
| `get_presentation` | Retrieve a presentation by presentation ID | [Presentation - Get](https://developer.pinelabsonline.com/reference/get-presentation) |
| `delete_presentation` | Delete a presentation | [Presentation - Delete](https://developer.pinelabsonline.com/reference/delete-presentation) |
| `get_presentations_by_subscription_id` | Retrieve all presentations for a subscription | [Presentation - Get by Subscription](https://developer.pinelabsonline.com/reference/get-presentation-by-subscription-id) |
| `get_presentation_by_merchant_reference` | Retrieve a presentation by merchant reference | [Presentation - Get](https://developer.pinelabsonline.com/reference/get-presentation) |
| `send_subscription_notification` | Send a pre-debit notification for a subscription | [Presentation - Create](https://developer.pinelabsonline.com/reference/create-presentation) |
| `create_debit` | Execute a debit (payment collection) against a subscription | [Presentation - Create](https://developer.pinelabsonline.com/reference/create-presentation) |
| `create_merchant_retry` | Retry mandate execution for a failed debit (max 3 retries) | [Merchant Retry](https://developer.pinelabsonline.com/reference/create-merchant-retry) |

### UPI

| Tool | Description | API |
|:-----|:------------|:----|
| `create_upi_intent_payment_with_qr` | Create a UPI intent payment with QR code | [UPI Intent QR](https://developer.pinelabsonline.com/reference/create-intent-payment-with-qr-image) |

### Reports

| Tool | Description | API |
|:-----|:------------|:----|
| `get_payment_link_details` | Fetch payment link details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `get_order_details` | Fetch order details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `get_refund_order_details` | Fetch refund order details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `search_transaction` | Search for a transaction by transaction ID | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |

### API Documentation

| Tool | Description |
|:-----|:------------|
| `get_api_documentation` | Fetch Pine Labs API documentation for a specific API |
| `list_pinelabs_apis` | List all available Pine Labs APIs with descriptions |

### Success Rate

| Tool | Description |
|:-----|:------------|
| `get_merchant_success_rate` | Fetch transaction success rate for the merchant over a date range |

## Use Cases

- **Workflow Automation**: Automate day-to-day payment operations — create payment links, manage subscriptions, track orders — using AI assistants.
- **Agentic Applications**: Build AI-powered tools that interact with Pine Labs' payment ecosystem for intelligent, automated payment workflows.
- **Subscription Management**: Automate recurring payment plan creation, subscription lifecycle management, and debit presentations.
- **Payment Link Generation**: Dynamically create, send, and manage payment links through conversational AI interfaces.
- **Order Tracking & Reconciliation**: Query order details and transaction history to reconcile payments, verify statuses, and resolve disputes.
- **UPI QR Payments**: Generate UPI intent QR codes on the fly for in-app or in-store payment collection.
- **Analytics & Reporting**: Fetch payment link details, order reports, and merchant success rates over custom date ranges for business insights.
- **Customer Support Automation**: Enable support agents or chatbots to look up transactions, check payment statuses, and resend payment notifications instantly.

## Remote MCP Server (Recommended)

The Remote MCP Server is hosted by Pine Labs and provides instant access to Pine Labs APIs without any local setup.

### Benefits

- **Zero Setup**: No need to install Python, Docker, or manage local infrastructure
- **Always Updated**: Automatically stays updated with the latest features and security patches
- **High Availability**: Backed by Pine Labs' robust infrastructure
- **Enhanced Security**: Secure authentication with client credentials

If you are connecting to a self-hosted remote deployment instead of the
Pine Labs hosted service, replace the remote URL below with
`<your-mcp-server-url>`.

### Prerequisites

`npx` is needed to use the remote MCP server.
You need to have Node.js installed on your system, which includes both `npm` and `npx` by default:

#### macOS
```bash
# Install Node.js using Homebrew
brew install node

# Alternatively, download from https://nodejs.org/
```

#### Windows
```bash
# Install Node.js using Chocolatey
choco install nodejs

# Alternatively, download from https://nodejs.org/
```

#### Verify Installation
```bash
npx --version
```

### Usage with Cursor

Add this to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.pinelabs.com/mcp",
        "--header",
        "X-Client-Id:<your-client-id>",
        "--header",
        "X-Client-Secret:<your-client-secret>"
      ]
    }
  }
}
```

Replace `<your-client-id>` and `<your-client-secret>` with your Pine Labs credentials. See [Authentication](#authentication) for details.

### Usage with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.pinelabs.com/mcp",
        "--header",
        "X-Client-Id:<your-client-id>",
        "--header",
        "X-Client-Secret:<your-client-secret>"
      ]
    }
  }
}
```

Replace `<your-client-id>` and `<your-client-secret>` with your Pine Labs credentials.

- Learn about how to configure MCP servers in Claude Desktop: [Link](https://modelcontextprotocol.io/quickstart/user)
- How to install Claude Desktop: [Link](https://claude.ai/download)

### Usage with VS Code

Add the following to your VS Code settings (JSON):

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
        "command": "npx",
        "args": [
          "mcp-remote",
          "https://mcp.pinelabs.com/mcp",
          "--header",
          "X-Client-Id:${input:pinelabs_client_id}",
          "--header",
          "X-Client-Secret:${input:pinelabs_client_secret}"
        ]
      }
    }
  }
}
```

Learn more about MCP servers in VS Code's [agent mode documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

## Authentication

The MCP server uses **Client ID** and **Client Secret** credentials for authentication.

### Getting Your Credentials

1. Sign up or log in to the Pine Labs merchant dashboard provided with your account.
2. Navigate to your account settings to locate your **Client ID** and **Client Secret**
3. Use these credentials in the MCP server configuration as shown in the setup instructions above

> **Note:** For local MCP server deployment, you can pass credentials directly via CLI arguments or environment variables. For the remote server, credentials are passed as HTTP headers.

## Local MCP Server

For users who prefer to run the MCP server on their own infrastructure, you can deploy the server locally.

### Prerequisites

- Python 3.12+
- Docker (optional)
- Git

### Using Public Docker Image (Recommended)

You can use the public Pine Labs image directly. No need to build anything yourself — just copy-paste the configurations below and make sure Docker is already installed.

> **Note:** To use a specific version instead of the latest, replace `pinelabs/mcp-server` with `pinelabs/mcp-server:v1.0.0` (or your desired version tag) in the configurations below.

#### Usage with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "PINELABS_CLIENT_ID",
        "-e",
        "PINELABS_CLIENT_SECRET",
        "-e",
        "PINELABS_ENV",
        "pinelabs/mcp-server"
      ],
      "env": {
        "PINELABS_CLIENT_ID": "<your-client-id>",
        "PINELABS_CLIENT_SECRET": "<your-client-secret>",
        "PINELABS_ENV": "prod"
      }
    }
  }
}
```

Replace `<your-client-id>` and `<your-client-secret>` with your Pine Labs credentials.

- Learn about how to configure MCP servers in Claude Desktop: [Link](https://modelcontextprotocol.io/quickstart/user)
- How to install Claude Desktop: [Link](https://claude.ai/download)

#### Usage with VS Code

Add the following to your VS Code settings (JSON):

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
        "command": "docker",
        "args": [
          "run",
          "--rm",
          "-i",
          "-e",
          "PINELABS_CLIENT_ID",
          "-e",
          "PINELABS_CLIENT_SECRET",
          "-e",
          "PINELABS_ENV=prod",
          "pinelabs/mcp-server"
        ],
        "env": {
          "PINELABS_CLIENT_ID": "${input:pinelabs_client_id}",
          "PINELABS_CLIENT_SECRET": "${input:pinelabs_client_secret}"
        }
      }
    }
  }
}
```

Learn more about MCP servers in VS Code's [agent mode documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

#### Usage with Cursor

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "PINELABS_CLIENT_ID",
        "-e",
        "PINELABS_CLIENT_SECRET",
        "-e",
        "PINELABS_ENV=prod",
        "pinelabs/mcp-server"
      ],
      "env": {
        "PINELABS_CLIENT_ID": "<your-client-id>",
        "PINELABS_CLIENT_SECRET": "<your-client-secret>"
      }
    }
  }
}
```

Replace `<your-client-id>` and `<your-client-secret>` with your Pine Labs credentials.

### Build from Docker (Alternative)

Clone the repo and build the Docker image locally:

```bash
git clone https://github.com/pinelabs/pinelabs-mcp-server.git
cd pinelabs-mcp-server
docker build -t pinelabs-mcp-server:latest .
```

Once built, replace `pinelabs/mcp-server` with `pinelabs-mcp-server:latest` in the above configurations.

### Build from Source

You can directly run the server from source without Docker:

```bash
# Clone the repository
git clone https://github.com/pinelabs/pinelabs-mcp-server.git
cd pinelabs-mcp-server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server (stdio mode)
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <your-client-id> \
  --client-secret <your-client-secret> \
  --env prod
```

Once running, configure your MCP client to point to the local binary. Here's an example for VS Code:

```json
{
  "mcp": {
    "servers": {
      "pinelabs": {
        "command": "python",
        "args": [
          "-m",
          "cli.pinelabs_mcp_server.main",
          "stdio"
        ],
        "env": {
          "PINELABS_CLIENT_ID": "<your-client-id>",
          "PINELABS_CLIENT_SECRET": "<your-client-secret>",
          "PINELABS_ENV": "prod"
        }
      }
    }
  }
}
```

## Configuration

The server requires the following configuration:

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `PINELABS_CLIENT_ID` | Yes | — | Your Pine Labs client ID |
| `PINELABS_CLIENT_SECRET` | Yes | — | Your Pine Labs client secret |
| `PINELABS_ENV` | No | `uat` | Environment: `uat` or `prod` |
| `LOG_LEVEL` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | No | stderr | Path to log file |
| `READ_ONLY` | No | `false` | Run server in read-only mode |
| `TOOLSETS` | No | all | Comma-separated list of toolsets to enable |

### Command Line Flags

The server supports the following command line flags:

```
python -m cli.pinelabs_mcp_server.main <transport> [options]

Transports:
  stdio                 Standard I/O transport (for MCP clients)
  http                  HTTP transport (for web-based access)

Options:
  --client-id           Pine Labs client ID
  --client-secret       Pine Labs client secret
  --env                 Environment: uat, prod (default: uat)
  --log-file            Path to log file
  --log-level           Log level: DEBUG, INFO, WARNING, ERROR
  --read-only           Only register read-only tools
  --toolsets             Comma-separated list of toolsets to enable

HTTP-only options:
  --host                Host to bind to (default: 0.0.0.0)
  --port                Port to listen on (default: 8000)
```

## Debugging the Server

Use the `--log-level DEBUG` flag and optionally `--log-file` to write logs to a file for troubleshooting:

```bash
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <ID> --client-secret <SECRET> \
  --log-level DEBUG --log-file ./debug.log
```

## FAQ

**Q: Do I need to provide amounts in paisa?**
A: No. Amounts can be provided in rupees (e.g., `500` for ₹500). You do not need to convert to paisa.

**Q: What environments are supported?**
A: The server supports `uat` (default) and `prod` environments. Set via `PINELABS_ENV` or `--env`.

**Q: Can I restrict which tools are available?**
A: Yes. Use the `--read-only` flag to disable write operations, or use `--toolsets` to enable only specific toolsets (e.g., `--toolsets payment_links,orders`).

**Q: Where can I find the full API reference?**
A: Visit the [Pine Labs Developer Documentation](https://developer.pinelabsonline.com/docs/mcp-server-overview) for the complete API reference and available tools.

## License

This project is licensed under the terms of the Apache 2.0 license. Please refer to [LICENSE](./LICENSE) for the full terms.
