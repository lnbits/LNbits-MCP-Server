# 🚀 LNbits MCP Server - Quick Start

## ✅ Server Status: READY TO USE!

The LNbits MCP server has been successfully installed and tested.

## 🔌 How to Connect

### Step 1: Get Your LNbits Credentials

1. **Open your LNbits instance** (e.g., `https://your-lnbits-instance.com`)
2. **Go to your wallet**
3. **Click "API Info" or "Wallet Details"**
4. **Copy your API key** (Admin key for full access, Invoice key for read-only)

### Step 2: Configure the Server

Choose one of these methods:

#### Option A: Environment Variables
```bash
export LNBITS_URL="https://your-lnbits-instance.com"
export LNBITS_API_KEY="your_api_key_here"
```

#### Option B: Create .env file
```bash
# Edit /Users/mark/Desktop/lnbits-mcp-server/.env
LNBITS_URL=https://your-lnbits-instance.com
LNBITS_API_KEY=your_api_key_here
LNBITS_AUTH_METHOD=api_key_header
```

### Step 3: Connect to Claude Desktop

1. **Find your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add this configuration:**
```json
{
  "mcpServers": {
    "lnbits": {
      "command": "/Users/mark/Desktop/lnbits-mcp-server/venv/bin/lnbits-mcp-server",
      "env": {
        "LNBITS_URL": "https://your-lnbits-instance.com",
        "LNBITS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### Step 4: Test the Connection

In Claude Desktop, you can now use commands like:

- "Check my LNbits wallet balance"
- "Get my recent payments"
- "Create an invoice for 1000 sats"
- "Pay this lightning invoice: lnbc..."

## 🛠️ Available Tools

- `check_connection` - Test LNbits connection
- `get_wallet_details` - Get wallet info
- `get_wallet_balance` - Check balance
- `get_payments` - View payment history
- `create_invoice` - Create Lightning invoices
- `pay_invoice` - Pay Lightning invoices
- `decode_invoice` - Analyze invoice details

## 🔧 Manual Testing

```bash
# Activate the environment
source /Users/mark/Desktop/lnbits-mcp-server/venv/bin/activate

# Set your credentials
export LNBITS_URL="https://your-lnbits-instance.com"
export LNBITS_API_KEY="your_api_key_here"

# Run the server
lnbits-mcp-server
```

## 🆘 Troubleshooting

**Server won't start:**
- Check that your LNbits URL is correct and accessible
- Verify your API key is valid
- Make sure you have internet connection

**Connection fails:**
- Check the structured JSON logs for specific error messages
- Verify your LNbits instance is running
- Ensure your API key has the required permissions

**In Claude Desktop:**
- Make sure the server path is correct in the config
- Restart Claude Desktop after making changes
- Check Claude Desktop's logs for connection errors

## 🎉 You're Ready!

The server is now fully functional and ready to integrate with Claude Desktop or any other MCP client. Enjoy lightning-fast Bitcoin payments through AI! ⚡️