# Port 3454 Binding Issue - Comprehensive Analysis

**Date**: 2025-01-27
**Issue**: Address already in use error on port 3454 in combined mode
**Status**: INVESTIGATING

## Problem Summary

The MCP server starts successfully in combined mode but fails with:
```
[Errno 48] error while attempting to bind on address ('::1', 3454, 0, 0): [errno 48] address already in use
```

## Key Observations from Logs

1. **Successful Startup Messages**:
   - "Combined transport mode started successfully"
   - "HTTP server available at http://localhost:3454"
   - "WebSocket endpoint available at ws://localhost:3454/ws"
   - "stdio transport available for direct MCP client connections"

2. **MCP Protocol Working**:
   - Server initializes: "Initializing server 'mcp-jive-stdio'"
   - Handlers registered successfully
   - Tools listed successfully: "Got tools for mcp.config.usrlocalmcp.mcp-jive"

3. **Failure Point**:
   - Error occurs AFTER successful tool listing
   - IPv6 address binding fails: `('::1', 3454, 0, 0)`
   - Triggers complete server shutdown

## Investigation Plan

### Phase 1: Code Analysis
- [ ] Trace all port 3454 binding attempts in server.py
- [ ] Examine uvicorn.Config instances
- [ ] Analyze asyncio task creation in run_combined
- [ ] Check for IPv6 vs IPv4 binding conflicts

### Phase 2: Server Startup Sequence
- [ ] Map complete startup flow
- [ ] Identify timing of each binding attempt
- [ ] Check for race conditions

### Phase 3: Process Analysis
- [ ] Verify single server instance
- [ ] Check for orphaned processes
- [ ] Examine port usage patterns

## Findings

### Code Locations Using Port 3454

#### server.py References
- Line 681: Default port configuration
- Line 1239: uvicorn.Config setup
- Line 1836: Server configuration in run_combined

#### config.py References
- Line 21: Default server port constant
- Line 184: Configuration loading

### Analysis Progress

#### ✅ Completed
- Initial log analysis
- Port reference identification

#### 🔄 In Progress
- Line-by-line code analysis

#### ⏳ Pending
- Server startup sequence mapping
- IPv6 binding investigation
- Process verification

## Hypotheses

### Primary Hypothesis: Dual Binding Attempt
- Server successfully binds to IPv4 localhost:3454
- Later attempts to bind to IPv6 ::1:3454
- IPv6 binding fails because port already in use

### Secondary Hypotheses
- Race condition between asyncio tasks
- Duplicate server instance creation
- Configuration conflict between HTTP and WebSocket

## Next Steps

1. Examine run_combined method line by line
2. Trace all uvicorn.Server creation points
3. Check asyncio.create_task calls
4. Investigate IPv6 binding configuration

---

## Detailed Code Analysis

### CRITICAL FINDING: Duplicate HTTP Server Methods

**Root Cause Identified**: Two separate methods create uvicorn.Server instances on the same port:

#### Method 1: `run_http()` (Line 448)
- Creates FastAPI app
- Creates uvicorn.Server on port 3454 (Line 698)
- Used for HTTP-only transport mode

#### Method 2: `run_combined()` (Line 1184)
- Creates FastAPI app
- Creates uvicorn.Server on port 3454 (Line 1387)
- Used for combined transport mode (HTTP + stdio)

### Server Creation Analysis

#### run_http Method (Lines 448-720)
```python
# Line 448: Method definition
async def run_http(self) -> None:
    # ... FastAPI app creation ...
    
    # Lines 685-698: Server configuration
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,  # Default: 3454
        log_level="info",
        access_log=False,
        loop="asyncio",
        use_colors=False,
        log_config=None
    )
    
    server = uvicorn.Server(config)  # LINE 698: First server
```

#### run_combined Method (Lines 1184-1420)
```python
# Line 1184: Method definition
async def run_combined(self) -> None:
    # ... FastAPI app creation ...
    
    # Lines 1377-1387: Inline server function
    async def start_http_server():
        config = uvicorn.Config(
            app,
            host=host,
            port=port,  # Default: 3454
            log_level="info" if self.config.server.debug else "warning",
            access_log=self.config.server.debug,
            loop="asyncio",
            use_colors=False
        )
        server = uvicorn.Server(config)  # LINE 1387: Second server
        await server.serve()
```

### The Conflict Mechanism

1. **Combined Mode Startup**: `run_combined()` is called
2. **First Server Success**: HTTP server starts successfully on port 3454
3. **Stdio Server Starts**: MCP stdio transport initializes
4. **Tools Listed Successfully**: MCP protocol works correctly
5. **Second Binding Attempt**: Something triggers another port binding
6. **IPv6 Binding Fails**: `('::1', 3454, 0, 0)` fails with "address already in use"

### Key Questions to Investigate

1. **Why is there a second binding attempt?**
   - Is `run_http()` being called from somewhere?
   - Is there a race condition in task creation?
   - Is uvicorn trying to bind to both IPv4 and IPv6?

2. **What triggers the IPv6 binding?**
   - The error shows IPv6 address `::1` instead of IPv4 `localhost`
   - This suggests uvicorn is trying to bind to both interfaces

3. **Timing Analysis**:
   - Server starts successfully
   - Tools are listed (MCP protocol working)
   - Then binding fails - what happens between these events?

## BREAKTHROUGH: IPv6 Binding Issue Analysis

### Key Discovery
The error message shows: `[Errno 48] error while attempting to bind on address ('::1', 3454, 0, 0): [errno 48] address already in use`

**Critical Insight**: The address `('::1', 3454, 0, 0)` is IPv6 format, where:
- `::1` = IPv6 localhost equivalent
- `3454` = port number
- `0, 0` = flowinfo and scope_id (IPv6 specific)

### Hypothesis: Dual Stack Binding Issue

**Primary Theory**: When uvicorn binds to "localhost", it may attempt to bind to both:
1. **IPv4**: `127.0.0.1:3454` (succeeds first)
2. **IPv6**: `::1:3454` (fails because port already in use)

### Evidence Supporting This Theory

1. **Successful Initial Binding**: Server starts and works initially
2. **IPv6 Error Format**: Error shows IPv6 address format
3. **"localhost" Configuration**: Both servers use `host="localhost"`
4. **Timing**: Error occurs after successful startup

### Configuration Analysis

#### Both Methods Use Same Host Configuration:
```python
# Line 680 (run_http) and Line 1365 (run_combined)
host = self.config.server.host or "localhost"
```

#### Default Config (config.py):
```python
# Line 20 and 32
host: str = "localhost"
```

### Uvicorn Dual Stack Behavior

Uvicorn may be attempting to bind to both IPv4 and IPv6 when:
- Host is set to "localhost"
- System supports dual stack networking
- IPv6 is enabled

**Solution Hypothesis**: Change host from "localhost" to "127.0.0.1" to force IPv4-only binding.

## NEXT STEPS: Testing the IPv6 Dual-Stack Theory

### Test Plan
1. **Verify Current Behavior**: Confirm error occurs with "localhost"
2. **Test IPv4-Only**: Change host to "127.0.0.1" in both locations
3. **Monitor Binding**: Check if error disappears
4. **Validate Functionality**: Ensure all features work with IPv4-only

### Code Changes Required
```python
# In src/mcp_jive/server.py (lines 680 and 1365)
# BEFORE:
host = self.config.server.host or "localhost"

# AFTER:
host = self.config.server.host or "127.0.0.1"
```

### Alternative Solutions to Consider
1. **IPv4-Only Binding**: Force "127.0.0.1" instead of "localhost"
2. **Uvicorn IPv6 Disable**: Add uvicorn config to disable IPv6
3. **Socket Options**: Configure socket to IPv4-only
4. **Host Resolution**: Ensure localhost resolves to IPv4 only

### Risk Assessment
- **Low Risk**: IPv4-only binding is standard for local development
- **Compatibility**: Should work on all systems
- **Performance**: No impact expected
- **Security**: Actually more secure (no IPv6 exposure)

## ✅ RESOLUTION CONFIRMED

### Root Cause Identified
**Primary Issue**: Stale server process was already binding to port 3454
**Secondary Issue**: IPv6 dual-stack binding attempts with "localhost"

### Solution Applied
1. **Killed Stale Process**: `kill -9 85557` (PID found via `lsof -i :3454`)
2. **IPv4-Only Configuration**: Changed all "localhost" references to "127.0.0.1"

### Files Modified
- `src/mcp_jive/server.py`: Lines 680, 1365 (host configuration)
- `src/mcp_jive/config.py`: Lines 20, 32, 183, 192 (default configurations)

### Verification Results
✅ **Server Starts Successfully**: No binding errors
✅ **HTTP Endpoint Accessible**: `curl http://127.0.0.1:3454/` responds
✅ **Combined Mode Working**: stdio + HTTP + WebSocket all operational
✅ **No IPv6 Conflicts**: Using IPv4-only binding

### Key Learnings
1. **Process Management**: Always check for stale processes before debugging
2. **Dual-Stack Issues**: "localhost" can cause IPv6 binding conflicts
3. **IPv4-Only Safer**: "127.0.0.1" avoids dual-stack complications
4. **Diagnostic Tools**: `lsof -i :PORT` is essential for port debugging

### Prevention Measures
- Use IPv4-only binding by default
- Implement proper server shutdown handling
- Add port conflict detection in startup sequence
- Consider using different ports for development vs production