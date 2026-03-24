# LNbits MCP Server

Give your AI assistant a Lightning wallet. The LNbits MCP Server connects any [MCP-compatible](https://modelcontextprotocol.io/) AI client to your [LNbits](https://lnbits.com/) instance - check balances, create invoices, send payments, and manage extensions, all through natural language.

<a href="https://rumble.com/v6vxr70-lnbits-mcp-server-lnbits-in-your-ai.html">
  <img src="https://github.com/lnbits/LNbits-MCP-Server/blob/main/LNbits_MCP.png" width="600" alt="Watch the LNbits MCP Server demo" />
</a>

> Click the image to watch the demo

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/lnbits/LNbits-MCP-Server.git
cd LNbits-MCP-Server
pip install -e .
```

### 2. Add to your AI client

Add the server to your MCP client config. For **Claude Desktop**:

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

Restart your client after saving.

### 3. Connect to your LNbits

Once your client is running, tell your AI assistant:

```
Configure lnbits.

URL: https://your-lnbits-instance.com
Key: your_api_key_here
Auth method: api_key_header
```

That's it. Your AI can now talk to your LNbits wallet.

> Get your API key from your LNbits instance sidebar under "Node URL, API keys and API docs". Admin key gives full access; Invoice key is read-only.

---

## What you can say

```
"Check my wallet balance"
"Create an invoice for 1000 sats with memo 'Coffee payment'"
"Pay this invoice: lnbc10u1p3..."
"Send 500 sats to alice@lnbits.com"
"Show me my recent payments"
"Decode this invoice: lnbc..."
```

---

## Available Tools

### Configuration

| Tool | Description |
|---|---|
| `configure_lnbits` | Set LNbits URL, API key, and auth method at runtime |
| `get_lnbits_configuration` | Show current connection settings |
| `test_lnbits_configuration` | Verify the connection works |

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

### Extensions (when enabled)

| Tool | Description |
|---|---|
| `create_lnurlp_link` / `get_lnurlp_links` | LNURLp pay links |
| `create_tpos` / `get_tpos_list` | TPoS terminals |
| `create_satspay_charge` / `get_satspay_charges` | SatsPay charges |
| `create_watchonly_wallet` / `get_watchonly_wallets` | Watch-only wallets |

### Admin (when admin access is available)

| Tool | Description |
|---|---|
| `get_node_info` | Lightning node information |
| `list_users` / `create_user` | User management |
| `get_system_stats` | System statistics |

---

## Configuration Reference

The server can be configured at runtime (recommended) or via environment variables.

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

At least one auth method (`API_KEY`, `BEARER_TOKEN`, or `OAUTH2_TOKEN`) is required.

---

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

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes and add tests
4. Submit a pull request

## Links

- [LNbits](https://lnbits.com/) - official site
- [LNbits Docs](https://docs.lnbits.com) - documentation
- [Issues](https://github.com/lnbits/LNbits-MCP-Server/issues) - report bugs or request features
- [Telegram](https://t.me/lnbits) - community chat

## License

MIT
