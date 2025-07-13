#!/bin/bash

echo "🔍 Testing MCP tools/list Request"
echo "=================================="

cd /home/shahar42/Suumerizing_C_holy_grale_book

echo "Sending initialize + tools/list requests..."

cat << 'EOF' | timeout 10s python3 mcp_server.py 2>&1
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOF

echo -e "\n🎯 Looking for tools in response..."
echo "Expected: Should see search_concepts, get_concept_details, list_books, get_concepts_by_topic"
