<a href="https://lnbits.com" target="_blank" rel="noopener noreferrer">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/QE6SIrs.png">
    <img src="https://i.imgur.com/fyKPgVT.png" alt="LNbits" style="width:280px">
  </picture>
</a>

# LNbits MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-success?logo=open-source-initiative&logoColor=white)](./LICENSE)
[![Built for LNbits](https://img.shields.io/badge/Built%20for-LNbits-4D4DFF?logo=lightning&logoColor=white)](https://github.com/lnbits/lnbits)

Give your AI assistant a Lightning wallet. The LNbits MCP Server connects any [MCP-compatible](https://modelcontextprotocol.io/) AI client to your [LNbits](https://lnbits.com/) instance - check balances, create invoices, send payments, and manage extensions, all through natural language.

<a href="https://rumble.com/v6vxr70-lnbits-mcp-server-lnbits-in-your-ai.html">
  <img src="https://github.com/lnbits/LNbits-MCP-Server/blob/main/LNbits_MCP.png" width="600" alt="Watch the LNbits MCP Server demo" />
  <br/>
  <img src="https://img.shields.io/badge/%E2%96%B6%20Watch%20Demo-LNbits%20MCP%20in%20Action-7C3AED?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik04IDV2MTRsMTEtN3oiLz48L3N2Zz4=&logoColor=white" alt="Watch Demo" />
</a>

---

## Table of Contents

- [Quick Start](#quick-start)
- [What you can say](#what-you-can-say)
- [Available Tools](#available-tools)
- [Configuration Reference](#configuration-reference)
- [Development](#development)
- [Contributing](#contributing)
- [Powered by LNbits](#powered-by-lnbits)

---

## Quick Start

Three steps, takes about two minutes.

### 1. Install

```bash
git clone https://github.com/lnbits/LNbits-MCP-Server.git
cd LNbits-MCP-Server
pip install -e .
```

> You need Python 3.10+ installed. If you're unsure, run `python3 --version` first.

### 2. Add to your AI client

Tell your MCP client where the server lives. For **Claude Desktop**, edit the config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lnbits": {
      "command": "lnbits-mcp-server"
    }
  }
}
```

> Restart Claude Desktop after saving. The server only activates after a restart.

### 3. Connect to your LNbits

Now just talk to your AI. No extra config files needed - tell it your credentials in plain language:

```
Configure lnbits.

URL: https://your-lnbits-instance.com
Key: your_api_key_here
Auth method: api_key_header
```

That's it. Try asking "What's my wallet balance?" to confirm it works.

> **Where's my API key?** Open your LNbits instance, look in the sidebar under "Node URL, API keys and API docs". Use the **Admin key** if you want to send payments, or the **Invoice key** if you only need to check balances and create invoices.


## What you can say

Just talk naturally. The AI figures out which tool to call.

```
"Check my wallet balance"
"Create an invoice for 1000 sats with memo 'Coffee payment'"
"Pay this invoice: lnbc10u1p3..."
"Send 500 sats to alice@lnbits.com"
"Show me my recent payments"
"Decode this invoice and tell me what it's for"
```

> You can also chain requests: "Create a 5000 sat invoice and show me the QR code" or "Check if that last payment went through, and if so, what's my new balance?"


## Available Tools

These are the tools the AI uses behind the scenes. You don't need to call them directly - just describe what you want and the AI picks the right one.

### Configuration

| Tool | Description |
|---|---|
| `configure_lnbits` | Set LNbits URL, API key, and auth method at runtime |
| `get_lnbits_configuration` | Show current connection settings |
| `test_lnbits_configuration` | Verify the connection works |

> You only need to configure once per session. The server remembers your settings until you restart it.

### Wallet

| Tool | Description |
|---|---|
| `get_wallet_details` | Wallet info including balance and keys |
| `get_wallet_balance` | Current balance |
| `get_payments` | Payment history |
| `check_connection` | Test connection to LNbits |

### Payments

| Tool | Description |
|---|---|
| `pay_invoice` | Pay a BOLT11 Lightning invoice |
| `pay_lightning_address` | Pay a Lightning address (user@domain.com) |
| `get_payment_status` | Check status by payment hash |
| `decode_invoice` | Decode and inspect a Lightning invoice |
| `create_invoice` | Create a new Lightning invoice |

> **Tip:** You can pay Lightning addresses directly - just say "Send 1000 sats to user@domain.com". No need to create an invoice first.

### Extensions (when enabled)

These tools appear when you have the corresponding extensions installed on your LNbits instance.

| Tool | Description |
|---|---|
| `create_lnurlp_link` / `get_lnurlp_links` | LNURLp pay links |
| `create_tpos` / `get_tpos_list` | TPoS terminals |
| `create_satspay_charge` / `get_satspay_charges` | SatsPay charges |
| `create_watchonly_wallet` / `get_watchonly_wallets` | Watch-only wallets |

### Admin (requires admin key)

Only available when you connect with a Super User or admin-level API key.

| Tool | Description |
|---|---|
| `get_node_info` | Lightning node information |
| `list_users` / `create_user` | User management |
| `get_system_stats` | System statistics |


## Configuration Reference

Most people just use the runtime config (step 3 above). But if you prefer environment variables, these work too:

| Variable | Description | Default |
|---|---|---|
| `LNBITS_URL` | LNbits instance URL | `https://demo.lnbits.com` |
| `LNBITS_API_KEY` | API key | - |
| `LNBITS_BEARER_TOKEN` | Bearer token (alternative auth) | - |
| `LNBITS_OAUTH2_TOKEN` | OAuth2 token (alternative auth) | - |
| `LNBITS_AUTH_METHOD` | `api_key_header`, `api_key_query`, `http_bearer`, or `oauth2` | `api_key_header` |
| `LNBITS_TIMEOUT` | Request timeout (seconds) | `30` |
| `LNBITS_MAX_RETRIES` | Max retries on failure | `3` |
| `LNBITS_RATE_LIMIT_PER_MINUTE` | Rate limit | `60` |

> At least one auth method is required. For most setups, `LNBITS_API_KEY` with `api_key_header` is all you need.


## Development

```bash
git clone https://github.com/lnbits/LNbits-MCP-Server.git
cd LNbits-MCP-Server
pip install -e .[dev]

# Run tests
pytest

# Format
black src tests
isort src tests

# Type check
mypy src
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes and add tests
4. Submit a pull request

Questions? Drop by the [Telegram group](https://t.me/lnbits) first - a quick chat often saves a round-trip on the PR.

---

## Powered by LNbits

[LNbits](https://lnbits.com) is a free and open-source Lightning accounts system.

[![LNbits Docs](https://img.shields.io/badge/Read-LNbits%20Docs-10B981?logo=book&logoColor=white&labelColor=059669)](https://docs.lnbits.com)
[![Visit LNbits Shop](https://img.shields.io/badge/Visit-LNbits%20Shop-7C3AED?logo=shopping-cart&logoColor=white&labelColor=5B21B6)](https://shop.lnbits.com/)
[![Try myLNbits SaaS](https://img.shields.io/badge/Try-myLNbits%20SaaS-2563EB?logo=lightning&logoColor=white&labelColor=1E40AF)](https://my.lnbits.com/login)

## License

MIT
