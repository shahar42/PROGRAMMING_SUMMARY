#!/bin/bash

echo "🔍 Test 1: FastMCP tools/list Request Variations"
echo "================================================"

cd /home/shahar42/Suumerizing_C_holy_grale_book

echo "Testing different tools/list request formats..."

# Test 1a: Empty params
echo -e "\n📋 Test 1a: tools/list with empty params {}"
cat << 'EOF' | timeout 5s python3 mcp_server.py 2>&1 | grep -A5 -B5 "tools"
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOF

# Test 1b: No params at all
echo -e "\n📋 Test 1b: tools/list with no params field"
cat << 'EOF' | timeout 5s python3 mcp_server.py 2>&1 | grep -A5 -B5 "tools"
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
EOF

# Test 1c: Different method name
echo -e "\n📋 Test 1c: Try 'list_tools' instead of 'tools/list'"
cat << 'EOF' | timeout 5s python3 mcp_server.py 2>&1 | grep -A5 -B5 "tools\|list"
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "list_tools", "params": {}}
EOF

# Test 1d: Check what methods FastMCP actually supports
echo -e "\n📋 Test 1d: Check FastMCP supported methods"
python3 -c "
import asyncio
import sys
sys.path.append('.')

async def test_methods():
    from mcp_server import mcp
    print('FastMCP available methods:')
    methods = [m for m in dir(mcp) if not m.startswith('_')]
    for method in sorted(methods):
        print(f'  - {method}')
    
    print('\nChecking internal protocol handlers...')
    if hasattr(mcp, 'app') and hasattr(mcp.app, 'routes'):
        print('Routes available:')
        for route in mcp.app.routes:
            print(f'  - {route}')
    elif hasattr(mcp, '_handlers'):
        print('Handlers:')
        for handler in mcp._handlers:
            print(f'  - {handler}')

asyncio.run(test_methods())
"

echo -e "\n🎯 Summary: Looking for the correct method name and parameters that FastMCP expects"
