#!/bin/bash

echo "🔍 MCP Server Diagnostic Script"
echo "================================"

# Test 1: Basic server startup
echo "📋 Test 1: Testing server startup..."
cd /home/shahar42/Suumerizing_C_holy_grale_book
timeout 10s python3 mcp_server.py &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server process started successfully"
    kill $SERVER_PID 2>/dev/null
else
    echo "❌ Server failed to start"
fi

# Test 2: Test MCP protocol communication
echo -e "\n📋 Test 2: Testing MCP protocol..."
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | python3 mcp_server.py | head -5

# Test 3: Check if database/content exists
echo -e "\n📋 Test 3: Checking for content files..."
find . -name "*.json" -type f | grep -E "(concepts|data|database)" | head -5

# Test 4: Check server logs
echo -e "\n📋 Test 4: Check recent server execution..."
python3 mcp_server.py --version 2>&1 | head -3 || echo "No version info available"

echo -e "\n🎯 Run this script to diagnose your MCP server issues"
