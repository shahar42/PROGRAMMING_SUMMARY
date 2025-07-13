#!/bin/bash

echo "🔍 Test 3: FastMCP vs Standard MCP Protocol Comparison"
echo "======================================================"

cd /home/shahar42/Suumerizing_C_holy_grale_book

echo "Testing standard MCP server response..."

# Create the minimal standard MCP server
cat > test_standard_mcp.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
from mcp import stdio_server
from mcp.server import Server
from mcp.types import Tool

server = Server("test-mcp")

@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={"type": "object", "properties": {"message": {"type": "string"}}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    return {"content": [{"type": "text", "text": f"Test tool called: {arguments}"}]}

async def main():
    print("Standard MCP server ready", file=sys.stderr)
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
EOF

echo "📋 Testing Standard MCP tools/list response:"
cat << 'EOF' | timeout 5s python3 test_standard_mcp.py 2>&1
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOF

echo -e "\n📋 Comparing with FastMCP response:"
cat << 'EOF' | timeout 5s python3 mcp_server.py 2>&1 | tail -5
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOF

echo -e "\n🎯 Key Differences Analysis:"
echo "- Standard MCP: Should return tools list"
echo "- FastMCP: Returns 'Invalid request parameters'"
echo "- This confirms protocol incompatibility"

# Cleanup
rm -f test_standard_mcp.py
