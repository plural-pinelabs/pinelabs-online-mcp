# Pine Labs Payment Gateway MCP Server (Official)

<!-- mcp-name: io.github.plural-pinelabs/pinelabs-online-mcp -->

Pine Labs MCP Server is a production-grade [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) server that connects AI assistants and agentic applications to the Pine Labs payment gateway. It exposes Pine Labs' online payment APIs -- payment links, checkout orders, UPI intent payments, subscriptions, and transaction reporting -- as structured MCP tools that any compatible AI client can invoke.

Built for fintech developers integrating payment gateway capabilities into AI-driven workflows, this server enables programmatic access to the full Pine Labs payment API surface through natural-language AI interfaces such as VS Code Copilot, Claude Desktop, and Cursor.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Available Tools](#available-tools)
- [Use Cases](#use-cases)
- [Remote MCP Server (Recommended)](#remote-mcp-server-recommended)
- [Authentication](#authentication)
- [Local MCP Server](#local-mcp-server)
- [Configuration](#configuration)
- [Debugging](#debugging-the-server)
- [FAQ](#faq)
- [Keywords](#keywords)
- [License](#license)

---

## Quick Start

Choose your preferred deployment method:

- **[Remote MCP Server](#remote-mcp-server-recommended)** -- Hosted by Pine Labs. No local setup required.
- **[Local MCP Server](#local-mcp-server)** -- Self-hosted via Docker or source. Full control over your infrastructure.

---

## Available Tools

The Pine Labs MCP Server exposes 50+ tools across multiple categories. Each tool maps to a specific Pine Labs payment API endpoint.

### Payment Links

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
| `create_payment_link` | Create a new payment link for collecting payments | [Payment Link - Create](https://developer.pinelabsonline.com/reference/payment-link-create) |
| `get_payment_link_by_id` | Fetch a payment link by its payment link ID | [Payment Link - Get by ID](https://developer.pinelabsonline.com/reference/payment-link-get-by-payment-link-id) |
| `get_payment_link_by_merchant_reference` | Fetch a payment link by its merchant payment link reference | [Payment Link - Get by Reference](https://developer.pinelabsonline.com/reference/payment-link-get-by-merchant-payment-link-reference) |
| `cancel_payment_link` | Cancel an active payment link | [Payment Link - Cancel](https://developer.pinelabsonline.com/reference/payment-link-cancel) |
| `resend_payment_link_notification` | Resend a payment link notification to the customer | [Payment Link - Resend](https://developer.pinelabsonline.com/reference/payment-link-resend) |

### Orders

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
| `get_order_by_order_id` | Retrieve order details by order ID | [Order - Get by ID](https://developer.pinelabsonline.com/reference/orders-get-by-order-id) |
| `cancel_order` | Cancel a pre-authorized payment against an order | [Order - Cancel](https://developer.pinelabsonline.com/reference/orders-cancel) |

### Checkout Orders

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
| `create_order` | Create a new checkout order and generate a checkout link | [Order - Create](https://developer.pinelabsonline.com/reference/orders-create) |

### Subscriptions

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
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

### UPI Payments

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
| `create_upi_intent_payment_with_qr` | Create a UPI intent payment with QR code for instant collection | [UPI Intent QR](https://developer.pinelabsonline.com/reference/create-intent-payment-with-qr-image) |

### Reports and Transaction Search

| Tool | Description | API Reference |
|:-----|:------------|:--------------|
| `get_payment_link_details` | Fetch payment link details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `get_order_details` | Fetch order details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `get_refund_order_details` | Fetch refund order details within a date range | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |
| `search_transaction` | Search for a transaction by transaction ID | [API Docs](https://developer.pinelabsonline.com/docs/mcp-server-overview) |

### API Documentation

| Tool | Description |
|:-----|:------------|
| `get_api_documentation` | Fetch Pine Labs API documentation for a specific API |
| `list_pinelabs_apis` | List all available Pine Labs APIs with descriptions |

### Merchant Analytics

| Tool | Description |
|:-----|:------------|
| `get_merchant_success_rate` | Fetch transaction success rate for the merchant over a date range |

---

## Use Cases

- **Payment Gateway Integration**: Connect your AI application to the Pine Labs payment gateway to create checkout orders, generate payment links, and process transactions programmatically.
- **AI-Powered Checkout Flows**: Build conversational checkout experiences where AI assistants create orders, generate payment links, and track payment status in real time.
- **UPI Payment Automation**: Generate UPI intent QR codes and process UPI payments through AI-driven interfaces for in-app or point-of-sale collection.
- **Subscription Lifecycle Management**: Automate recurring payment plan creation, subscription activation, pause/resume cycles, debit presentations, and pre-debit notifications.
- **Agentic Payment Workflows**: Build autonomous AI agents that manage end-to-end payment operations -- from order creation through reconciliation -- without manual intervention.
- **Order Tracking and Reconciliation**: Query order details, search transactions by ID, and reconcile payments to verify statuses and resolve disputes.
- **Payment Analytics and Reporting**: Retrieve payment link reports, order summaries, refund details, and merchant success rates over custom date ranges.
- **Customer Support Automation**: Enable support agents or chatbots to look up transactions, check payment statuses, cancel orders, and resend payment notifications.

---

## Remote MCP Server (Recommended)

The Remote MCP Server is hosted and maintained by Pine Labs. It provides instant access to all payment gateway APIs with no local infrastructure required.

### Benefits

- **Zero Setup**: No Python, Docker, or local infrastructure to manage
- **Always Updated**: Automatic updates with the latest payment API features and security patches
- **High Availability**: Hosted on Pine Labs production infrastructure
- **Secure Authentication**: Client credential authentication over HTTPS

If you are connecting to a self-hosted remote deployment instead of the
Pine Labs hosted service, replace the remote URL below with
`<your-mcp-server-url>`.

### Prerequisites

`npx` is required to proxy the remote MCP connection.
Install Node.js (which includes `npm` and `npx`):

#### macOS
```bash
brew install node
```

#### Windows
```bash
choco install nodejs
```

Alternatively, download from [https://nodejs.org/](https://nodejs.org/).

#### Verify Installation
```bash
npx --version
```

### Usage with Cursor

Add the following to your Cursor MCP settings:

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

- Configure MCP servers in Claude Desktop: [MCP Quickstart Guide](https://modelcontextprotocol.io/quickstart/user)
- Install Claude Desktop: [Download](https://claude.ai/download)

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

---

## Authentication

The MCP server authenticates using **Client ID** and **Client Secret** credentials issued by Pine Labs.

### Getting Your Credentials

1. Sign up or log in to the Pine Labs merchant dashboard provided with your account.
2. Navigate to your account settings to locate your **Client ID** and **Client Secret**.
3. Use these credentials in the MCP server configuration as shown in the setup instructions above.

> **Note:** For local deployments, credentials can be passed via CLI arguments or environment variables. For the remote server, credentials are passed as HTTP headers.

---

## Local MCP Server

Deploy the MCP server on your own infrastructure for full control over the runtime environment.

### Prerequisites

- Python 3.12+
- Docker (optional, for containerized deployment)
- Git

### Install on Windows (Chocolatey)

The fastest way to get the MCP server on a Windows machine is via [Chocolatey](https://chocolatey.org/). The package is a thin wrapper that installs Python 3.10+ as a dependency and then installs `pinelabs-mcp-server` from PyPI, registering a `pinelabs-mcp` shim on `PATH`.

```powershell
choco install pinelabs-mcp
```

Verify the install:

```powershell
pinelabs-mcp --help
```

Run the server over stdio:

```powershell
pinelabs-mcp stdio --client-id <your-client-id> --client-secret <your-client-secret> --env uat
```

#### MCP client configuration (Claude Desktop / Cursor / VS Code)

After `choco install`, point your MCP client at the `pinelabs-mcp` shim:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "pinelabs-mcp",
      "args": ["stdio", "--env", "uat"],
      "env": {
        "PINELABS_CLIENT_ID": "<your-client-id>",
        "PINELABS_CLIENT_SECRET": "<your-client-secret>"
      }
    }
  }
}
```

To uninstall:

```powershell
choco uninstall pinelabs-mcp
```

### Using Public Docker Image (Recommended)

Use the official Pine Labs Docker image directly. No build step required.

> **Note:** To pin a specific version, replace `pinelabs/mcp:latest` with `pinelabs/mcp:<version-tag>` (e.g., `pinelabs/mcp:v1.0.0`) in the configurations below.

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
        "pinelabs/mcp:latest"
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

- Configure MCP servers in Claude Desktop: [MCP Quickstart Guide](https://modelcontextprotocol.io/quickstart/user)
- Install Claude Desktop: [Download](https://claude.ai/download)

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
          "pinelabs/mcp:latest"
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
        "pinelabs/mcp:latest"
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

Clone the repository and build the Docker image locally:

```bash
git clone https://github.com/plural-pinelabs/pinelabs-online-mcp.git
cd pinelabs-online-mcp
docker build -t pinelabs-mcp-server:latest .
```

Once built, replace `pinelabs/mcp:latest` with `pinelabs-mcp-server:latest` in the configurations above.

### Build from Source

Run the server directly from source without Docker:

```bash
# Clone the repository
git clone https://github.com/plural-pinelabs/pinelabs-online-mcp.git
cd pinelabs-online-mcp

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

Once running, configure your MCP client to connect to the local process. Example for VS Code:

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

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `PINELABS_CLIENT_ID` | Yes | -- | Pine Labs client ID for API authentication |
| `PINELABS_CLIENT_SECRET` | Yes | -- | Pine Labs client secret for API authentication |
| `PINELABS_ENV` | No | `uat` | Target environment: `uat` or `prod` |
| `LOG_LEVEL` | No | `INFO` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | No | stderr | Path to log output file |
| `READ_ONLY` | No | `false` | Restrict to read-only tools (disables write operations) |
| `TOOLSETS` | No | all | Comma-separated list of toolsets to enable |

### Command Line Flags

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
  --toolsets            Comma-separated list of toolsets to enable

HTTP-only options:
  --host                Host to bind to (default: 0.0.0.0)
  --port                Port to listen on (default: 8000)
```

---

## Debugging the Server

Use the `--log-level DEBUG` flag and optionally `--log-file` to write detailed logs for troubleshooting:

```bash
python -m cli.pinelabs_mcp_server.main stdio \
  --client-id <ID> --client-secret <SECRET> \
  --log-level DEBUG --log-file ./debug.log
```

---

## FAQ

**Q: Do I need to provide amounts in paisa?**
A: No. Amounts are specified in rupees (e.g., `500` for INR 500). No conversion to paisa is required.

**Q: What environments are supported?**
A: The server supports `uat` (default) and `prod` environments. Set via `PINELABS_ENV` or `--env`.

**Q: Can I restrict which tools are available?**
A: Yes. Use the `--read-only` flag to disable write operations, or use `--toolsets` to enable specific toolsets (e.g., `--toolsets payment_links,orders`).

**Q: Where can I find the full API reference?**
A: Visit the [Pine Labs Developer Documentation](https://developer.pinelabsonline.com/docs/mcp-server-overview) for the complete API reference.

---

## Keywords

Pine Labs, Pine Labs Online, Plural, Plural Online, payment gateway, online payment gateway, checkout gateway, payment checkout, online checkout, hosted checkout, payment page, payments, online payments, digital payments, payment processing, accept payments, collect payments, payment integration, gateway integration, payments API, payment API, checkout API, gateway API, UPI, cards, credit card, debit card, netbanking, wallet, EMI, cardless EMI, subscriptions, recurring payments, orders, order payments, create payment, initiate payment, process payment, payment links, MCP server, Model Context Protocol, AI payment automation, agentic payments, QR code payments, payment orchestration, merchant API, transaction reporting, fintech, SDK

---

## License

This project is licensed under the Apache 2.0 license. See [LICENSE](./LICENSE) for the full terms.
