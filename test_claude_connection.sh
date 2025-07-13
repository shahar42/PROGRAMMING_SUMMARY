#!/bin/bash

echo "🔍 Test 4: Claude Code MCP Connection Test"
echo "=========================================="

cd /home/shahar42/Suumerizing_C_holy_grale_book

echo "Step 1: Create minimal working MCP server for Claude Code test"

cat > minimal_test_server.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
from mcp import stdio_server
from mcp.server import Server
from mcp.types import Tool

server = Server("minimal-test")

@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="hello",
            description="Say hello",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    return {"content": [{"type": "text", "text": "Hello from minimal MCP server!"}]}

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
EOF

echo "Step 2: Test if this minimal server works with protocol"
echo "📋 Testing minimal server protocol response:"

cat << 'EOF' | timeout 5s python3 minimal_test_server.py 2>&1
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOF

echo -e "\n🎯 Next Step Instructions:"
echo "If the minimal server shows tools properly:"
echo "1. Temporarily update ~/.claude.json to point to minimal_test_server.py"
echo "2. Test 'claude' and '/mcp' to see if it shows the 'hello' tool"
echo "3. If that works, we know standard MCP is the solution"
echo ""
echo "To test with Claude Code:"
echo "  - Backup current config: cp ~/.claude.json ~/.claude.json.backup"
echo "  - Edit ~/.claude.json and change the 'args' to point to minimal_test_server.py"
echo "  - Run 'claude' and try '/mcp'"
echo "  - Restore config: mv ~/.claude.json.backup ~/.claude.json"

# Cleanup 
rm -f minimal_test_server.py
