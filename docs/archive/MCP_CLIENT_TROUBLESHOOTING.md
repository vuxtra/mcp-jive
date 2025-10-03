# MCP Client Troubleshooting Guide

## Issue: "fetch failed" Error

If you're getting a "fetch failed" error when listing tools for `mcp.config.usrlocalmcp.mcp-jive`, this guide will help you resolve it.

## Root Cause

The MCP HTTP transport requires a proper initialization flow:
1. First call `initialize` method to get a session ID
2. Use that session ID in subsequent requests

Most MCP clients handle this automatically, but configuration issues can cause problems.

## Verified Working Configuration

### For VSCode/Cursor with MCP Extension

Add this to your MCP client configuration (`.vscode/settings.json` or `.cursor/settings.json`):

```json
{
  "mcp.servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp"
      }
    }
  }
}
```

### For Other MCP Clients

**HTTP Transport (Recommended):**
- Transport Type: `http`
- URL: `http://localhost:3454/mcp`
- Headers: `Content-Type: application/json`

**WebSocket Transport (Alternative):**
- Transport Type: `websocket`
- URL: `ws://localhost:3454/mcp`

**Stdio Transport (Legacy):**
- Command: `/path/to/mcp-jive/bin/mcp-jive`
- Args: `["server", "start", "--mode", "stdio"]`

## Troubleshooting Steps

### 1. Verify Server is Running

```bash
# Check if server is running
curl http://localhost:3454/health
# Should return: {"status": "healthy", "version": "0.1.0"}
```

### 2. Test HTTP Transport Manually

```bash
# Test initialization
curl -X POST http://localhost:3454/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0"},"capabilities":{}}}'

# Should return session ID in Mcp-Session-Id header
```

### 3. Run Automated Test

```bash
# Run the test script to verify everything works
python test_mcp_client.py
```

### 4. Check Server Logs

Look at the server terminal for any error messages when the client tries to connect.

## Common Issues and Solutions

### Issue: "Invalid session" Error
**Cause:** Client not sending session ID or using expired session
**Solution:** Ensure client calls `initialize` first and includes `Mcp-Session-Id` header

### Issue: "Connection refused"
**Cause:** Server not running or wrong port
**Solution:** 
- Start server: `./bin/mcp-jive server start`
- Check port: Server runs on port 3454 by default

### Issue: "Method not found"
**Cause:** Client sending unsupported method
**Solution:** Use supported methods: `initialize`, `tools/list`, `tools/call`

### Issue: Client hangs or times out
**Cause:** Network issues or server overload
**Solution:**
- Restart server
- Check firewall settings
- Try WebSocket transport instead

## Transport Comparison

| Transport | Pros | Cons | Use Case |
|-----------|------|------|----------|
| HTTP | Simple, widely supported | Requires session management | Most clients |
| WebSocket | Real-time, bidirectional | More complex setup | Advanced clients |
| Stdio | Direct process communication | One client per server | Legacy/isolated |

## Server Status Verification

The server provides these endpoints for verification:

- `GET /health` - Health check
- `POST /mcp` - MCP HTTP transport
- `GET /mcp` - MCP SSE transport (streaming)
- `WS /mcp` - MCP WebSocket transport
- `WS /ws` - General WebSocket endpoint

## Need Help?

If you're still experiencing issues:

1. Check server logs for error messages
2. Verify your MCP client supports HTTP transport
3. Try the WebSocket transport as an alternative
4. Run the test script to isolate the issue

## Test Results

As of the last test run, the server is working correctly:
- ✅ HTTP transport functional
- ✅ Session management working
- ✅ All 8 tools available
- ✅ Proper JSON-RPC 2.0 responses

The issue is likely in the client configuration or initialization flow.