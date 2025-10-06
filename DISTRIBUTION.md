# MCP Jive Distribution Guide

This guide covers how MCP Jive is distributed and how developers can install it without cloning the repository.

## 📦 Distribution Methods

MCP Jive supports multiple distribution methods to make installation as easy as possible:

### 1. PyPI (Recommended) ⭐

**Installation with `uvx` (Single Command)**
```bash
# Run MCP Jive directly without installation
uvx mcp-jive

# Or with custom port
uvx mcp-jive --port 8080
```

**Installation with `pip`**
```bash
# Install globally
pip install mcp-jive

# Or in a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp-jive

# Start the server
mcp-jive --port 3454
```

**Benefits:**
- ✅ No git clone required
- ✅ No manual dependency installation
- ✅ Automatic updates with `uvx`
- ✅ Works on all platforms (Windows/Mac/Linux)
- ✅ Single command to run

---

### 2. Docker 🐳

**Using Docker Run**
```bash
# Pull and run the latest image
docker run -d \
  --name mcp-jive \
  -p 3454:3454 \
  -v mcp-jive-data:/app/data \
  mcpjive/mcp-jive:latest

# Check it's running
curl http://localhost:3454/health
```

**Using Docker Compose**
```bash
# Create docker-compose.yml
curl -O https://raw.githubusercontent.com/mcpjive/mcp-jive/main/docker-compose.yml

# Start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

**Benefits:**
- ✅ No Python/Node.js installation required
- ✅ Sandboxed environment (security)
- ✅ Easy updates (`docker pull`)
- ✅ Data persistence with volumes
- ✅ Cross-platform consistency

---

### 3. From Source (Development)

**For contributors and developers**
```bash
# Clone the repository
git clone https://github.com/mcpjive/mcp-jive.git
cd mcp-jive

# Install dependencies
./bin/mcp-jive setup environment

# Start the server
./bin/mcp-jive --port 3454
```

**Benefits:**
- ✅ Latest development features
- ✅ Ability to modify code
- ✅ Contribute back to the project

---

## 🎯 Which Method Should You Use?

| Method | Best For | Setup Time | Tech Skills |
|--------|----------|------------|-------------|
| **uvx** | Quick start, trying it out | 10 seconds | Basic terminal |
| **pip** | Long-term use, production | 2 minutes | Python basics |
| **Docker** | Isolated environments, servers | 1 minute | Docker basics |
| **From Source** | Development, contribution | 5 minutes | Git + Python |

---

## 📋 Quick Start Comparison

### Using uvx (Fastest)
```bash
# One command to run everything
uvx mcp-jive
```

### Using Docker (Easiest)
```bash
# One command for complete setup
docker run -dp 3454:3454 -v mcp-jive-data:/app/data mcpjive/mcp-jive:latest
```

### Using pip
```bash
# Install once
pip install mcp-jive

# Run anytime
mcp-jive --port 3454
```

---

## 🔧 IDE Configuration

After installation via any method, configure your IDE to connect to MCP Jive:

### VSCode
Create `.vscode/mcp.json`:
```json
{
  "servers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project"
    }
  }
}
```

### Cursor
Create `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project"
    }
  }
}
```

### Claude Code
```bash
claude mcp add mcp-jive --scope project --type http --url http://localhost:3454/mcp/my-project
```

---

## 🚀 Updating MCP Jive

### PyPI/uvx
```bash
# uvx automatically uses latest version
uvx mcp-jive

# Or force upgrade with pip
pip install --upgrade mcp-jive
```

### Docker
```bash
# Pull latest image
docker pull mcpjive/mcp-jive:latest

# Restart container
docker-compose down && docker-compose up -d
```

### From Source
```bash
git pull origin main
./bin/mcp-jive setup environment
```

---

## 📊 System Requirements

**Minimum:**
- Python 3.9+ (for PyPI/source installation)
- Docker 20.10+ (for Docker installation)
- 2GB RAM
- 1GB disk space

**Recommended:**
- Python 3.11+
- 4GB RAM
- 2GB disk space
- SSD storage for LanceDB performance

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port 3454 is in use
lsof -i :3454

# Try a different port
mcp-jive --port 8080
```

### Docker Container Issues
```bash
# Check container logs
docker logs mcp-jive

# Restart container
docker restart mcp-jive

# Remove and recreate
docker rm -f mcp-jive
docker run -dp 3454:3454 mcpjive/mcp-jive:latest
```

### IDE Can't Connect
```bash
# Verify server is running
curl http://localhost:3454/health

# Check MCP endpoint
curl -X POST http://localhost:3454/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## 📖 More Information

- [Main README](README.md) - Full documentation
- [Development Guide](docs/guides/claude-instructions.md) - For contributors
- [Architecture Docs](docs/architecture/) - Technical details
- [GitHub Issues](https://github.com/mcpjive/mcp-jive/issues) - Bug reports & features

---

## 🤝 Support

Need help? We're here:
- 📖 [Documentation](docs/README.md)
- 🐛 [GitHub Issues](https://github.com/mcpjive/mcp-jive/issues)
- 💬 [Discussions](https://github.com/mcpjive/mcp-jive/discussions)
