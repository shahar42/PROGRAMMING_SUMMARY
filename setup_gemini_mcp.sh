#!/bin/bash
# Setup Gemini CLI with your existing MCP servers

echo "🔧 Setting up Gemini CLI with your MCP servers..."
echo ""

# Create Gemini config directory
echo "📁 Creating Gemini CLI config directory..."
mkdir -p ~/.gemini
echo "✅ Created ~/.gemini directory"

# Backup existing settings if they exist
if [[ -f ~/.gemini/settings.json ]]; then
    echo "💾 Backing up existing settings..."
    cp ~/.gemini/settings.json ~/.gemini/settings.json.backup.$(date +%s)
    echo "✅ Backup created"
fi

# Create the settings.json file
echo "📝 Creating Gemini CLI settings.json..."
cat > ~/.gemini/settings.json << 'EOF'
{
  "mcpServers": {
    "programming-concepts": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book",
      "env": {},
      "description": "Main programming concepts from K&R, UNIX, Linkers books"
    },
    "topic-detection": {
      "command": "python3", 
      "args": ["scripts/topic_detection_mcp.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book",
      "env": {},
      "description": "Intelligent question analysis and topic routing"
    },
    "master-orchestrator": {
      "command": "python3",
      "args": ["scripts/master_orchestrator_mcp.py"], 
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book",
      "env": {},
      "description": "Main routing and server management orchestrator"
    },
    "got-plt-server": {
      "command": "python3",
      "args": ["scripts/got_plt_mcp_server.py"],
      "cwd": "/home/shahar42/Suumerizing_C_holy_grale_book", 
      "env": {},
      "description": "GOT/PLT binary analysis and education server"
    }
  },
  "httpMcpServers": {
    "master-orchestrator-http": {
      "url": "http://localhost:8100",
      "description": "HTTP-based master orchestrator",
      "tools": ["analyze_and_route_question", "spawn_specific_server", "get_orchestrator_status"]
    },
    "got-plt-http": {
      "url": "http://localhost:8108", 
      "description": "HTTP-based GOT/PLT server",
      "tools": ["inspect_got_table", "analyze_plt_stubs", "validate_concept", "trace_symbol_resolution"]
    },
    "kernighan-ritchie": {
      "url": "http://localhost:8101",
      "description": "K&R C Programming concepts",
      "tools": ["search_concepts", "get_concept_details"]
    },
    "unix-environment": {
      "url": "http://localhost:8102",
      "description": "UNIX Environment programming",
      "tools": ["search_concepts", "get_concept_details"] 
    },
    "linkers-loaders": {
      "url": "http://localhost:8103",
      "description": "Linkers & Loaders concepts", 
      "tools": ["search_concepts", "get_concept_details"]
    }
  },
  "preferences": {
    "defaultTemperature": 0.1,
    "maxTokens": 4096,
    "enableMcpLogging": true,
    "mcpTimeout": 30000
  }
}
EOF

echo "✅ Created ~/.gemini/settings.json"
echo ""

# Verify the setup
echo "🔍 Verifying setup..."
if [[ -f ~/.gemini/settings.json ]]; then
    echo "✅ Settings file exists"
    echo "📊 Configuration summary:"
    echo "   - Stdio MCP Servers: 4 configured"
    echo "   - HTTP MCP Servers: 5 configured" 
    echo "   - Base directory: /home/shahar42/Suumerizing_C_holy_grale_book"
else
    echo "❌ Settings file not created"
    exit 1
fi

echo ""
echo "🎯 Setup Complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start your HTTP servers (if not running):"
echo "   cd /home/shahar42/Suumerizing_C_holy_grale_book"
echo "   python3 scripts/master_orchestrator_mcp.py &"
echo "   python3 scripts/got_plt_mcp_server.py &"
echo ""
echo "2. Test Gemini CLI:"
echo "   gemini /MCP"
echo ""
echo "3. Try using a tool:"
echo "   gemini 'search for malloc concepts using programming-concepts'"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check server logs in your project directory"
echo "   - Verify all Python dependencies are installed"
echo "   - Ensure correct file paths in configuration"
