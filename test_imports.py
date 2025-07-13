#!/usr/bin/env python3
print("Testing MCP imports...")

try:
    print("1. Testing basic mcp import...")
    import mcp
    print("✅ mcp imported successfully")
    print("   Available:", dir(mcp))
except ImportError as e:
    print("❌ mcp import failed:", e)

try:
    print("\n2. Testing fastmcp (your original)...")
    from mcp.server.fastmcp import FastMCP
    print("✅ FastMCP available - maybe we should stick with it!")
except ImportError as e:
    print("❌ FastMCP not available:", e)

print("\nDone testing.")
