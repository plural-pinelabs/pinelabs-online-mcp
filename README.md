# Pine Labs Online Payments MCP Server (Official)

<!-- mcp-name: io.github.plural-pinelabs/pinelabs-online-mcp -->

[![npm package](https://img.shields.io/npm/v/pinelabs-mcp.svg)](https://www.npmjs.com/package/pinelabs-mcp)

MCP client for Pine Labs Online Payments gateway -- connect Claude Desktop, Cursor, VS Code, and other AI assistants to Pine Labs Online Payments APIs using your client credentials.

[Full Documentation](#available-tools) | [Available Tools](#available-tools) | [Use Cases](#use-cases) | [FAQs](#faq)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Supported AI Clients](#supported-ai-clients)
- [Manual Configuration](#manual-configuration)
- [Available Tools](#available-tools)
- [Use Cases](#use-cases)
- [Remote MCP Server](#remote-mcp-server)
- [Authentication](#authentication)
- [Local MCP Server](#local-mcp-server)
- [Configuration](#configuration)
- [Debugging](#debugging-the-server)
- [FAQ](#faq)
- [Keywords](#keywords)
- [License](#license)

---

## Prerequisites

- **Node.js 18+** -- [Download](https://nodejs.org/) or install npm i pinelabs-mcp
- **Pine Labs Online Payments Client Credentials** -- Get your Client ID and Client Secret from the [Pine Labs developer portal](https://www.pinelabs.com/docs/online-payments/ai/mcp-server)

---

## Quick Start

### Getting Your Credentials

1. Sign up or log in to the Pine Labs Online Payments <a href="https://dashboardv2.pluralonline.com/signup" target="_blank">merchant dashboard</a> provided with your account.
2. Navigate to your account settings to locate your **Client ID** and **Client Secret**.
3. Use these credentials in the MCP server configuration as shown in the setup instructions above.

### Configure and Connect

```bash
# 1. Configure your credentials
npx pinelabs-mcp configure --client-id=YOUR_ID --client-secret=YOUR_SECRET

# 2. Test your connection
npx pinelabs-mcp test

# 3. Auto-configure your AI client
npx pinelabs-mcp setup cursor       # or: claude-desktop, vscode, windsurf, opencode, copilot, codex
```

Then restart your AI client and start using Pine Labs Online Payments tools.

---

## CLI Commands

```
pinelabs-mcp start                             Start MCP server (stdio mode)
pinelabs-mcp configure                         Interactive credential setup
pinelabs-mcp configure --client-id=X --client-secret=Y [--env=uat|prod]
pinelabs-mcp test                              Test connectivity and credentials
pinelabs-mcp setup <client>                    Auto-configure an AI client
pinelabs-mcp setup <client> --local            Use local path (dev mode)
pinelabs-mcp setup <client> --print            Preview config without writing
pinelabs-mcp status                            Show current configuration
pinelabs-mcp help                              Show help message
pinelabs-mcp --version                         Show version
```

---

## Supported AI Clients

| Client | Command | Config Path |
|:-------|:--------|:------------|
| Claude Desktop | `setup claude-desktop` | Platform-specific Claude config |
| Cursor | `setup cursor` | `~/.cursor/mcp.json` |
| VS Code | `setup vscode` | `.vscode/mcp.json` (project) |
| Windsurf | `setup windsurf` | `~/.codeium/windsurf/mcp_config.json` |
| OpenCode | `setup opencode` | `.opencode/config.json` (project) |
| GitHub Copilot | `setup copilot` | `~/.copilot/mcp-config.json` |
| OpenAI Codex | `setup codex` | `.codex/config.toml` |

---

## Manual Configuration

If you prefer to configure manually instead of using `npx pinelabs-mcp setup`, add the following to your AI client's MCP config:

```json
{
  "mcpServers": {
    "pinelabs": {
      "command": "npx",
      "args": ["-y", "pinelabs-mcp"],
      "env": {
        "PINELABS_CLIENT_ID": "your_client_id",
        "PINELABS_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

> **Note:** VS Code uses `"servers"` instead of `"mcpServers"` as the top-level key. For production environment, add `"PINELABS_ENV": "prod"` to the `env` block.

---

## Available Tools

The Pine Labs Online Payments MCP Server exposes 50+ tools across multiple categories. Each tool maps to a specific Pine Labs Online Payments API endpoint.

### Tool Type Legend

Each tool below is tagged with a **Type** indicating its access pattern and operational risk. This helps you reason about which tools are safe in read-only deployments and which require explicit user confirmation in autonomous (agentic) flows.

| Type | Meaning | Examples |
|:-----|:--------|:---------|
| **Read** | Safe, side-effect-free. Fetches or queries data only. Allowed in read-only mode. | `get_order_by_order_id`, `get_all_settlements`, `list_plural_apis` |
| **Write** | Creates or modifies resources. Not destructive but mutates server state. Skipped in read-only mode. | `create_payment_link`, `create_order`, `update_plan` |
| **Destructive** | Cancels, deletes, refunds, or moves money. Irreversible or financially impactful. **Should require explicit user confirmation in agent flows.** | `cancel_order`, `create_refund`, `create_payout`, `delete_plan` |

> **Read-only mode:** Run the server with `--read-only` (or set the equivalent config) to register only `Read` tools and skip all `Write` / `Destructive` toolsets. Useful for analytics, monitoring, or untrusted agent contexts.

### Payment Links


| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_payment_link` | Write | Create a new payment link for collecting payments | [Payment Link - Create](https://www.pinelabs.com/docs/online-payments/api/payment-links/create-payment-link) |
| `get_payment_link_by_id` | Read | Fetch a payment link by its payment link ID | [Payment Link - Get by ID](https://www.pinelabs.com/docs/online-payments/api/payment-links/get-payment-link-by-id) |
| `get_payment_link_by_merchant_reference` | Read | Fetch a payment link by its merchant payment link reference | [Payment Link - Get by Reference](https://www.pinelabs.com/docs/online-payments/api/payment-links/get-payment-link-by-merchant-reference) |
| `cancel_payment_link` | Destructive | Cancel an active payment link | [Payment Link - Cancel](https://www.pinelabs.com/docs/online-payments/api/payment-links/cancel-payment-link) |
| `resend_payment_link_notification` | Write | Resend a payment link notification to the customer | [Payment Link - Resend](https://www.pinelabs.com/docs/online-payments/api/payment-links/resend-payment-link-notification) |

### Orders

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `get_order_by_order_id` | Read | Retrieve order details by order ID | [Order - Get by ID](https://www.pinelabs.com/docs/online-payments/api/orders/get-order-by-id) |
| `get_order_by_merchant_order_reference` | Read | Retrieve order details by merchant order reference | [Order - Get by Merchant Reference](https://www.pinelabs.com/docs/online-payments/api/orders/get-order-by-merchant-reference) |
| `capture_order` | Write | Capture a previously authorized payment against an order | [Order - Capture](https://www.pinelabs.com/docs/online-payments/api/orders/capture-order) |
| `cancel_order` | Destructive | Cancel a pre-authorized payment against an order | [Order - Cancel](https://www.pinelabs.com/docs/online-payments/api/orders/cancel-order) |
| `fetch_order_payments` | Read | Fetch all payment attempts associated with an order | [Order - Get Payments](https://www.pinelabs.com/docs/online-payments/api/orders/get-order-by-id) |

### Checkout Orders

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_order` | Write | Create a new checkout order and generate a checkout link | [Order - Create](https://www.pinelabs.com/docs/online-payments/api/checkout/generate-checkout-link) |

### Card Payments

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_card_payment` | Write | Create a server-to-server card payment against an order | [Card Payment - Create](https://www.pinelabs.com/docs/online-payments/api/card-payments/create-payment) |
| `get_card_details` | Read | Retrieve card details (BIN, network, type) for a card number | [Card Details - Get](https://www.pinelabs.com/docs/online-payments/api/card-payments/get-card-details) |

### OTP

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `generate_otp` | Write | Generate an OTP for a card payment authentication flow | [OTP - Generate](https://www.pinelabs.com/docs/online-payments/api/card-payments/generate-otp) |
| `submit_otp` | Write | Submit an OTP to complete a card payment authentication | [OTP - Submit](https://www.pinelabs.com/docs/online-payments/api/card-payments/submit-otp) |
| `resend_otp` | Write | Resend an OTP for a card payment authentication | [OTP - Resend](https://www.pinelabs.com/docs/online-payments/api/card-payments/resend-otp) |

### Refunds

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_refund` | Destructive | Initiate a full or partial refund against a captured payment | [Refund - Create](https://www.pinelabs.com/docs/online-payments/api/refunds/create-refund) |

### Settlements

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `get_all_settlements` | Read | Retrieve all settlements for the merchant within a date range | [Settlements - Get All](https://www.pinelabs.com/docs/online-payments/api/settlements/get-all-settlements) |
| `get_settlement_by_utr` | Read | Retrieve a specific settlement by its UTR (Unique Transaction Reference) | [Settlement - Get by UTR](https://www.pinelabs.com/docs/online-payments/api/settlements/get-settlements-by-utr) |

### Payouts

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_payout` | Destructive | Create a payout to disburse funds to a beneficiary (moves money) | [Payout - Create](https://www.pinelabs.com/docs/online-payments/api/payouts/create-payout) |
| `get_payout_details` | Read | Retrieve details of a payout by payout ID | [Payout - Get](https://www.pinelabs.com/docs/online-payments/api/payouts/list-payouts) |
| `get_payout_payments` | Read | List payments associated with a payout | [Payout - Get Payments](https://www.pinelabs.com/docs/online-payments/api/payouts/list-payouts) |
| `get_payout_balance` | Read | Retrieve the available payout balance for the merchant | [Payout - Get Balance](https://www.pinelabs.com/docs/online-payments/api/payouts/get-payout-balance) |
| `update_payout` | Write | Update an existing payout request | [Payout - Update](https://www.pinelabs.com/docs/online-payments/api/payouts/update-scheduled-payout) |
| `cancel_payout` | Destructive | Cancel a pending payout request | [Payout - Cancel](https://www.pinelabs.com/docs/online-payments/api/payouts/cancel-scheduled-payout) |

### Subscriptions

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_plan` | Write | Create a new subscription plan | [Plan - Create](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/create-plan) |
| `get_plans` | Read | Retrieve subscription plans | [Plan - Get All](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/list-plans) |
| `get_plan_by_id` | Read | Retrieve a subscription plan by plan ID | [Plan - Get Specific](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/get-plan-by-id) |
| `get_plan_by_merchant_reference` | Read | Retrieve a plan by merchant plan reference | [Plan - Get Specific](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/get-plan-by-merchant-reference) |
| `update_plan` | Write | Update an existing subscription plan | [Plan - Update](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/update-plan) |
| `delete_plan` | Destructive | Delete a subscription plan | [Plan - Delete](https://www.pinelabs.com/docs/online-payments/api/subscriptions-plans/delete-plan) |
| `create_subscription` | Write | Create a new subscription against a plan | [Subscription - Create](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/create-subscription) |
| `get_subscriptions` | Read | Retrieve subscriptions | [Subscription - Get All](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/list-subscriptions) |
| `get_subscription_by_id` | Read | Retrieve a subscription by subscription ID | [Subscription - Get Specific](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/get-subscription-by-id) |
| `get_subscription_by_merchant_reference` | Read | Retrieve a subscription by merchant reference | [Subscription - Get Specific](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/get-subscription-by-merchant-reference) |
| `pause_subscription` | Write | Pause an active subscription | [Subscription - Pause](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/pause-subscription) |
| `resume_subscription` | Write | Resume a paused subscription | [Subscription - Resume](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/resume-subscription) |
| `cancel_subscription` | Destructive | Cancel an active subscription | [Subscription - Cancel](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/cancel-subscription) |
| `update_subscription` | Write | Update an existing subscription | [Subscription - Update](https://www.pinelabs.com/docs/online-payments/api/subscriptions-subscriptions/update-subscription) |
| `create_presentation` | Write | Create a presentation (payment request) for a subscription | [Presentation - Create](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/create-presentation) |
| `get_presentation` | Read | Retrieve a presentation by presentation ID | [Presentation - Get](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/get-presentation-by-id) |
| `delete_presentation` | Destructive | Delete a presentation | [Presentation - Delete](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/delete-presentation) |
| `get_presentations_by_subscription_id` | Read | Retrieve all presentations for a subscription | [Presentation - Get by Subscription](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/list-presentations-by-subscription) |
| `get_presentation_by_merchant_reference` | Read | Retrieve a presentation by merchant reference | [Presentation - Get](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/get-presentation-by-merchant-reference) |
| `send_subscription_notification` | Write | Send a pre-debit notification for a subscription | [Presentation - Create](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/send-subscription-notification) |
| `create_debit` | Destructive | Execute a debit (payment collection) against a subscription | [Presentation - Create](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/create-debit) |
| `create_merchant_retry` | Write | Retry mandate execution for a failed debit (max 3 retries) | [Merchant Retry](https://www.pinelabs.com/docs/online-payments/api/subscriptions-presentations/create-merchant-retry) |

### UPI Payments

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `create_upi_intent_payment_with_qr` | Write | Create a UPI intent payment with QR code for instant collection | [UPI Intent QR](https://www.pinelabs.com/docs/online-payments/api/upi-payments/create-payment) |

### Reports and Transaction Search

| Tool | Type | Description | API Reference |
|:-----|:-----|:------------|:--------------|
| `get_payment_link_details` | Read | Fetch payment link details within a date range | [API Docs](https://www.pinelabs.com/docs/online-payments/ai/mcp-server) |
| `get_order_details` | Read | Fetch order details within a date range | [API Docs](https://www.pinelabs.com/docs/online-payments/ai/mcp-server) |
| `get_refund_order_details` | Read | Fetch refund order details within a date range | [API Docs](https://www.pinelabs.com/docs/online-payments/ai/mcp-server) |
| `search_transaction` | Read | Search for a transaction by transaction ID | [API Docs](https://www.pinelabs.com/docs/online-payments/ai/mcp-server) |

### Developer Tools

| Tool | Type | Description |
|:-----|:-----|:------------|
| `get_api_documentation` | Read | Fetch Pine Labs API documentation for a specific API |
| `list_plural_apis` | Read | List all available Pine Labs Online Payments APIs with descriptions |
| `detect_stack` | Read | Detect the technology stack of the current project to tailor integration guidance |
| `integrate_pinelabs_checkout` | Read | Generate stack-aware code snippets and integration guidance for Pine Labs Checkout |

### Merchant Analytics

| Tool | Type | Description |
|:-----|:-----|:------------|
| `get_merchant_success_rate` | Read | Fetch transaction success rate for the merchant over a date range |

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

## Remote MCP Server

The Remote MCP Server is hosted and maintained by Pine Labs Online Payments. Use this approach if you prefer to configure your AI client manually with the remote endpoint instead of using the [npm CLI](#quick-start).

### Benefits

- **Zero Setup**: No Python, Docker, or local infrastructure to manage
- **Always Updated**: Automatic updates with the latest payment API features and security patches
- **High Availability**: Hosted on Pine Labs Online Payments production infrastructure
- **Secure Authentication**: Client credential authentication over HTTPS

If you are connecting to a self-hosted remote deployment instead of the
Pine Labs Online Payments service, replace the remote URL below with
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

The MCP server authenticates using **Client ID** and **Client Secret** credentials issued by Pine Labs Online Payments.

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

Use the official Pine Labs Online Payments Docker image directly. No build step required.

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
A: Visit the [Pine Labs Online Payments Developer Documentation](https://www.pinelabs.com/docs/online-payments/ai/mcp-server) for the complete API reference.

---

## Keywords

Pine Labs Online Payments, Pine Labs, payment gateway, online payment gateway, checkout gateway, payment checkout, online checkout, hosted checkout, payment page, payments, online payments, digital payments, payment processing, accept payments, collect payments, payment integration, gateway integration, payments API, payment API, checkout API, gateway API, UPI, cards, credit card, debit card, netbanking, wallet, EMI, cardless EMI, subscriptions, recurring payments, orders, order payments, create payment, initiate payment, process payment, payment links, MCP server, Model Context Protocol, AI payment automation, agentic payments, QR code payments, payment orchestration, merchant API, transaction reporting, fintech, SDK

---

## License

This project is licensed under the Apache 2.0 license. See [LICENSE](./LICENSE) for the full terms.
