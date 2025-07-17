#!/bin/bash
# Setup Master Orchestrator (Part 2)
# Run this from ~/Suumerizing_C_holy_grale_book directory

echo "🎛️ Setting up Master Orchestrator (Part 2)..."
echo ""

# Check current directory
if [[ ! -f "mcp_server.py" ]]; then
    echo "❌ Please run this from the Suumerizing_C_holy_grale_book directory"
    exit 1
fi

# Create scripts directory if it doesn't exist
mkdir -p scripts/book_servers

echo "📁 Created directory structure:"
echo "  scripts/"
echo "  scripts/book_servers/ (for micro servers)"

# Update .mcp.json to include master orchestrator
if [[ -f ".mcp.json" ]]; then
    echo "📝 Updating .mcp.json to include master-orchestrator..."
    
    # Backup existing config
    cp .mcp.json .mcp.json.backup
    echo "💾 Backed up existing .mcp.json"
    
    # Create updated config
    cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "topic-detection": {
      "command": "python3",
      "args": ["scripts/topic_detection_mcp.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book"
    },
    "master-orchestrator": {
      "command": "python3",
      "args": ["scripts/master_orchestrator_mcp.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book"
    },
    "programming-concepts": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book"
    }
  }
}
EOF
    echo "✅ Updated .mcp.json with master-orchestrator"
else
    echo "❌ .mcp.json not found. Please create it first."
    exit 1
fi

echo ""
echo "🎯 Part 2 Setup Complete!"
echo ""
echo "📋 What was installed:"
echo "  ✅ Master Orchestrator MCP Server"
echo "  ✅ Updated .mcp.json configuration"
echo "  ✅ Directory structure for book servers"
echo "  ✅ Test script for verification"
echo ""
echo "🧪 Test the setup:"
echo "  cd scripts && python3 test_orchestrator_part2.py"
echo ""
echo "🚀 Ready for Claude Code!"
echo "Try: analyze_and_route_question('How do I fix a malloc memory leak?')"
echo ""
echo "📊 Next: Part 3 will connect real book concepts to the spawned servers"
