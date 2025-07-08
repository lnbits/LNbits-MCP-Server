# LNbits MCP Server

A Model Context Protocol (MCP) server for [LNbits](https://lnbits.com/) Lightning Network wallet integration. This server allows AI assistants to interact with LNbits through a comprehensive set of tools for wallet management, payments, invoices, and extensions.

## 💡 Examples

### Basic Usage with an AI Assistant

Once configured, you can interact with your LNbits wallet through your favorite AI assistant.

```
"Check my wallet balance"
"Create an invoice for 1000 sats with memo 'Coffee payment'"
"Pay this invoice: lnbc10u1p3..."
"Send 500 sats to bc@sats.pw"
"Pay Lightning address alice@lnbits.com 1000 sats with comment 'Thanks for the coffee!'"
"Show me my recent payments"
"What's the status of payment hash abc123..."
```

## 🚀 Features

- **⚡ Core Wallet Operations**: Get wallet details, balance, and transaction history
- **💸 Payment Management**: Send Lightning payments and check payment status
- **🧾 Invoice Creation**: Create and manage Lightning invoices
- **🔌 Extension Support**: Integrate with popular LNbits extensions (LNURLp, TPoS, SatsPay, etc.)
- **🔧 Admin Tools**: User and node management capabilities
- **🔒 Secure Authentication**: Support for API keys, Bearer tokens, and OAuth2
- **📝 Type Safety**: Full type hints and Pydantic models
- **📊 Structured Logging**: Comprehensive logging with structlog
- **🚦 Rate Limiting**: Built-in request throttling

## 📦 Installation

### From Source

```bash
git clone https://github.com/your-repo/lnbits-mcp-server
cd lnbits-mcp-server
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/your-repo/lnbits-mcp-server
cd lnbits-mcp-server
pip install -e .[dev]
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# LNbits instance URL
LNBITS_URL=https://your-lnbits-instance.com

# Authentication (choose one method)
LNBITS_API_KEY=your_api_key_here
LNBITS_BEARER_TOKEN=your_bearer_token
LNBITS_OAUTH2_TOKEN=your_oauth2_token

# Authentication method (optional, defaults to api_key_header)
LNBITS_AUTH_METHOD=api_key_header  # or api_key_query, http_bearer, oauth2

# Request settings (optional)
LNBITS_TIMEOUT=30
LNBITS_MAX_RETRIES=3
LNBITS_RATE_LIMIT_PER_MINUTE=60
```

### Configuration Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LNBITS_URL` | Base URL for LNbits instance | `https://demo.lnbits.com` | No |
| `LNBITS_API_KEY` | API key for authentication | `None` | Yes* |
| `LNBITS_BEARER_TOKEN` | Bearer token for authentication | `None` | Yes* |
| `LNBITS_OAUTH2_TOKEN` | OAuth2 token for authentication | `None` | Yes* |
| `LNBITS_AUTH_METHOD` | Authentication method | `api_key_header` | No |
| `LNBITS_TIMEOUT` | Request timeout in seconds | `30` | No |
| `LNBITS_MAX_RETRIES` | Maximum request retries | `3` | No |
| `LNBITS_RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `60` | No |

*At least one authentication method must be provided.

## 🚀 Usage

### Running the Server

```bash
# Using the installed command
lnbits-mcp-server

# Or run directly with Python
python -m lnbits_mcp_server.server
```

### Claude Desktop Integration

For Claude Desktop, add to your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\\Claude\\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lnbits": {
      "command": "lnbits-mcp-server",
      "env": {
        "LNBITS_URL": "https://your-lnbits-instance.com",
        "LNBITS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Other MCP Clients

Add the server to your MCP client configuration:

```json
{
  "mcpServers": {
    "lnbits": {
      "command": "lnbits-mcp-server",
      "env": {
        "LNBITS_URL": "https://your-lnbits-instance.com",
        "LNBITS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 🛠️ Available Tools

### Core Wallet Tools

- `get_wallet_details` - Get wallet information including balance and keys
- `get_wallet_balance` - Get current wallet balance
- `get_payments` - Get payment history
- `check_connection` - Test connection to LNbits instance

### Payment Tools

- `pay_invoice` - Pay a Lightning invoice (BOLT11)
- `pay_lightning_address` - Pay a Lightning address (e.g., user@domain.com)
- `get_payment_status` - Check payment status by hash
- `decode_invoice` - Decode and analyze a Lightning invoice

### Invoice Tools

- `create_invoice` - Create a new Lightning invoice

### Extension Tools (if extensions are enabled)

- `create_lnurlp_link` - Create LNURLp pay links
- `get_lnurlp_links` - List LNURLp pay links
- `create_tpos` - Create TPoS terminals
- `get_tpos_list` - List TPoS terminals
- `create_satspay_charge` - Create SatsPay charges
- `get_satspay_charges` - List SatsPay charges
- `create_watchonly_wallet` - Create watch-only wallets
- `get_watchonly_wallets` - List watch-only wallets

### Admin Tools (if admin access is available)

- `get_node_info` - Get Lightning node information
- `list_users` - List all users
- `create_user` - Create new users
- `get_system_stats` - Get system statistics

### API Usage

```python
from lnbits_mcp_server.client import LNbitsClient

async def example():
    client = LNbitsClient()
    
    # Get wallet balance
    balance = await client.get_wallet_balance()
    print(f"Current balance: {balance['balance']} msats")
    
    # Create an invoice
    invoice = await client.create_invoice(
        amount=1000,  # 1000 sats
        memo="Test payment"
    )
    print(f"Invoice: {invoice['bolt11']}")
    
    # Pay an invoice
    payment = await client.pay_invoice("lnbc1...")
    print(f"Payment hash: {payment['payment_hash']}")
    
    # Pay a Lightning address
    lightning_payment = await client.pay_lightning_address(
        lightning_address="edward@sats.pw",
        amount_sats=1000,
        comment="Payment via Lightning address"
    )
    print(f"Lightning address payment hash: {lightning_payment['payment_hash']}")
```

## 🔧 Development

### Setting up Development Environment

```bash
git clone https://github.com/your-repo/lnbits-mcp-server
cd lnbits-mcp-server
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src
```

### Testing with Claude Desktop

1. Configure the server in your Claude Desktop config
2. Restart Claude Desktop
3. Test with commands like:
   - "Check my LNbits connection"
   - "What's my wallet balance?"
   - "Create a 100 sat invoice"
   - "Send 21 sats to edward@sats.pw"
   - "Pay Lightning address alice@getalby.com 500 sats"

## 🏗️ Architecture

The server follows a modular architecture:

- **`server.py`**: Main MCP server implementation
- **`client.py`**: HTTP client for LNbits API
- **`tools/`**: Tool implementations organized by functionality
  - `core.py`: Wallet operations
  - `payments.py`: Payment processing
  - `invoices.py`: Invoice management
  - `extensions.py`: Extension integrations
  - `admin.py`: Administrative tools
- **`models/`**: Pydantic data models
- **`utils/`**: Utility functions and authentication

## 🔒 Security Considerations

- **API Keys**: Store API keys securely using environment variables
- **Network Security**: Use HTTPS for production LNbits instances
- **Access Control**: Limit API key permissions to required operations only
- **Rate Limiting**: Built-in rate limiting prevents API abuse
- **Logging**: Sensitive information is not logged

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/lnbits-mcp-server/issues)
- **Documentation**: [GitHub Wiki](https://github.com/your-repo/lnbits-mcp-server/wiki)
- **LNbits**: [Official Documentation](https://lnbits.com/)

## 📝 Changelog

### v0.1.0

- ✅ Initial release
- ✅ Core wallet operations (balance, details, payments)
- ✅ Payment processing (pay invoices, check status)
- ✅ Lightning address payments (pay user@domain.com addresses)
- ✅ Invoice creation and management
- ✅ Comprehensive error handling and structured logging
- ✅ Claude Desktop integration
- ✅ Type safety with Pydantic models
- ✅ Rate limiting and authentication support

## 🎯 Quick Start

1. **Install**: `pip install -e .`
2. **Configure**: Set `LNBITS_URL` and `LNBITS_API_KEY` environment variables
3. **Add to Claude**: Update your `claude_desktop_config.json`
4. **Test**: Ask Claude to check your wallet balance
5. **Enjoy**: Lightning-fast Bitcoin payments through AI! ⚡

---

*Built with ❤️ for the Bitcoin Lightning Network community*