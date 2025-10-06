# MCP Jive Build Scripts

## Building the PyPI Package

### Quick Start

```bash
# Option 1: Using the build script (recommended)
python3 scripts/build_package.py

# Option 2: Direct build command
pip install build
python3 -m build
```

### What Gets Created

Both methods create the `dist/` directory with:
- `mcp_jive-1.4.0-py3-none-any.whl` (286 KB) - Installable wheel
- `mcp_jive-1.4.0.tar.gz` (280 KB) - Source distribution

### First Time Setup

If you get an error about the `build` module not being found:

```bash
pip install build twine
```

Then run the build again.

### Testing Locally

```bash
# Install from the wheel
pip install dist/mcp_jive-1.4.0-py3-none-any.whl

# Test it works
mcp-jive --help
```

### Publishing to PyPI

```bash
# Upload to PyPI (requires PyPI account)
python -m twine upload dist/*
```

### After Publishing

Users can install with:
```bash
# Using uvx (no installation)
uvx mcp-jive --port 3454

# Using pip
pip install mcp-jive
mcp-jive --port 3454
```

## Troubleshooting

### "No module named build"

**Solution:**
```bash
pip install build
```

### "Permission denied" when running scripts

**Solution:**
```bash
chmod +x scripts/build_package.py
```

### Build warnings about license

These are deprecation warnings and can be ignored. The package builds successfully despite them.
