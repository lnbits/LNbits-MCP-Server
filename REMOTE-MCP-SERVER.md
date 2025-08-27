# Remote MCP Server for LNbits

This document describes how to run the LNbits MCP Server as a remote HTTP service, making it accessible to LLM APIs like OpenAI's MCP integration.

## What is this?

The LNbits MCP Server provides a bridge between AI assistants and LNbits Lightning Network wallets through the Model Context Protocol (MCP). This implementation allows the server to run as a web service rather than just locally via stdio.

### Key Features

- **🔒 Multi-User Security**: Session-based credential isolation prevents users from accessing each other's wallets
- **🌐 Remote Access**: Run as HTTP service accessible via URL  
- **🔌 MCP Protocol**: Proper MCP implementation over HTTP using FastMCP
- **⚡ All LNbits Functions**: Full access to wallet operations, payments, invoices
- **🔄 Runtime Configuration**: Configure LNbits connection without restart
- **🛡️ Production Ready**: Built with FastMCP for reliability and performance
- **📊 Session Management**: Automatic session cleanup and monitoring

## Security Architecture

### Session Isolation
Each user gets their own isolated session with separate:
- LNbits configuration and credentials
- Wallet connections and state
- Payment history and invoices
- Runtime configuration

### Multi-User Safety
- **No Credential Sharing**: User A cannot access User B's wallet
- **Session Expiry**: Automatic cleanup of inactive sessions (60min default)
- **Memory Isolation**: Each session runs in isolated tool instances
- **Secure Logging**: Session IDs tracked for debugging without exposing credentials

## Available Tools

The server exposes these MCP tools to AI assistants:

### Session Management Tools
- `create_session` - Create a new isolated session for credential separation
- `get_session_info` - Get information about your current session

### Configuration Tools  
- `configure_lnbits` - Configure LNbits connection parameters (session-isolated)
- `get_lnbits_configuration` - Get current configuration status for your session
- `test_lnbits_configuration` - Test configuration with API call

### Wallet Tools
- `get_wallet_details` - Get wallet information (your session only)
- `get_wallet_balance` - Get current balance in sats (your session only)
- `get_payments` - Get payment history (your session only)
- `check_connection` - Test LNbits connectivity for your session

### Payment Tools
- `pay_invoice` - Pay BOLT11 lightning invoices (from your wallet)
- `get_payment_status` - Check payment status by hash (your session only)
- `decode_invoice` - Decode BOLT11 invoice details
- `pay_lightning_address` - Pay lightning addresses (from your wallet)

### Invoice Tools
- `create_invoice` - Create new lightning invoices with QR codes (your wallet)

## Installation

### Prerequisites
- Python 3.9+
- LNbits instance (local or remote)
- API key from your LNbits wallet

### Install the Package
```bash
# Clone the repository
git clone <repository-url>
cd lnbits-mcp-server

# Install with dependencies
pip install -e .
```

## Running as Remote Server

### Secure Multi-User Server (Recommended)
```bash
# Start the secure HTTP server with session isolation
lnbits-mcp-secure --port 8001

# Or using Python module  
python -m lnbits_mcp_server.secure_fastmcp_server --port 8001
```

### Single-User Server (Legacy)
```bash
# Start the HTTP server (single user only - NOT secure for multi-user)
lnbits-mcp-http --port 8001

# Or using Python module
python -m lnbits_mcp_server.fastmcp_server --port 8001
```

⚠️ **Security Warning**: Only use `lnbits-mcp-http` for single-user deployments. For multi-user or public access, always use `lnbits-mcp-secure`.

### Command Line Options
```bash
lnbits-mcp-secure --help

Options:
  --host HOST      Host to bind to (default: 0.0.0.0)
  --port PORT      Port to bind to (default: 8000) 
  --debug         Enable debug mode
```

### Server Information
When started, the server provides:
- **MCP Endpoint**: `http://your-host:port/sse`
- **Transport**: Server-Sent Events (SSE)
- **Protocol**: MCP over HTTP

## Deployment Options

### 1. Local Testing with ngrok
Perfect for testing with OpenAI's MCP integration:

```bash
# Terminal 1: Start secure server  
lnbits-mcp-secure --port 8001

# Terminal 2: Expose via ngrok
ngrok http 8001
```

Use the ngrok URL with your LLM service. Each user will automatically get their own isolated session.

### 2. VPS/Cloud Server
Deploy to any cloud provider:

```bash
# Example systemd service
[Unit]
Description=LNbits Secure MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/lnbits-mcp-server
ExecStart=/path/to/venv/bin/lnbits-mcp-secure --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8001
CMD ["lnbits-mcp-secure", "--port", "8001", "--host", "0.0.0.0"]
```

## Configuration

### Environment Variables
```bash
export LNBITS_URL="https://your-lnbits-instance.com"
export LNBITS_API_KEY="your-api-key"
export LNBITS_AUTH_METHOD="api_key_header"
```

### Runtime Configuration (Session-Isolated)
Each session can be configured independently through MCP tools:

```python
# First, create a session for credential isolation
session_info = await mcp_client.call_tool("create_session")

# Configure this session's LNbits connection
await mcp_client.call_tool("configure_lnbits", {
    "__session_id": "your-session-id",
    "lnbits_url": "https://demo.lnbits.com", 
    "api_key": "your-api-key"
})
```

**Important**: Session IDs should be included in all tool calls to ensure credential isolation.

## Integration with LLM Services

### OpenAI MCP Integration
Use the server URL in your OpenAI MCP configuration:

```json
{
  "servers": {
    "lnbits": {
      "url": "https://your-ngrok-url.ngrok.io/sse"
    }
  }
}
```

### Other MCP Clients
Any MCP-compatible client can connect using the `/sse` endpoint with proper MCP protocol messages.

## Security Considerations

### API Key Protection
- Never expose API keys in URLs or logs
- Use environment variables or runtime configuration
- Rotate keys regularly

### Network Security
- Run behind HTTPS in production
- Use firewall rules to restrict access
- Consider VPN for sensitive deployments

### Authentication
The server currently supports LNbits authentication methods:
- API Key (Header or Query)
- Bearer Token
- OAuth2

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
lsof -i :8001

# Kill the process
kill -9 <PID>
```

**Connection Errors**
```bash
# Test configuration
curl -X POST http://localhost:8001/tools/test_lnbits_configuration \
  -H "Content-Type: application/json" \
  -d '{"name": "test_lnbits_configuration", "arguments": {}}'
```

**MCP Protocol Issues**
- Ensure using `/sse` endpoint
- Verify MCP client supports SSE transport
- Check server logs for detailed errors

### Debugging
```bash
# Run in debug mode
lnbits-mcp-http --port 8001 --debug

# Check server logs
tail -f /var/log/lnbits-mcp-server.log
```

## Development

### Local Development
```bash
# Install development dependencies  
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black src tests
isort src tests
```

### Adding New Tools
1. Add tool handler in `tools/` directory
2. Register in `fastmcp_server.py` 
3. Add proper MCP tool decorator
4. Update documentation

## Support

For issues and questions:
- Check the troubleshooting section above
- Review server logs for detailed errors
- Ensure LNbits connectivity and API key validity
- Test with the original stdio MCP server first

## Architecture

The secure remote server uses:
- **FastMCP**: Modern MCP framework for HTTP transport
- **SSE Protocol**: Server-Sent Events for MCP communication  
- **Session Isolation**: Each user gets isolated tool instances and credentials
- **Async Architecture**: Non-blocking operations for performance
- **Runtime Configuration**: Dynamic reconfiguration without restart per session
- **Automatic Cleanup**: Expired session cleanup (60min default)
- **Memory Safety**: No credential leakage between users

### Session Lifecycle
1. **Creation**: New session created automatically or via `create_session` tool
2. **Configuration**: Each session configured independently with `configure_lnbits`
3. **Usage**: All tools automatically use session-specific credentials  
4. **Expiry**: Sessions auto-expire after 60 minutes of inactivity
5. **Cleanup**: Resources automatically cleaned up on session end

This design maintains all functionality while ensuring complete credential isolation between users.