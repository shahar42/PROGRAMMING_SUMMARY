#!/bin/bash
# Create LangGraph Educational Agent structure

# Create main directory
mkdir -p langgraph_agent

# Create all subdirectories
mkdir -p langgraph_agent/{agent,mcp_integration,education,storage,config,utils,tests}

# Create all Python __init__.py files
touch langgraph_agent/agent/__init__.py
touch langgraph_agent/mcp_integration/__init__.py
touch langgraph_agent/education/__init__.py
touch langgraph_agent/storage/__init__.py
touch langgraph_agent/utils/__init__.py
touch langgraph_agent/tests/__init__.py

# Create main files
touch langgraph_agent/main.py
touch langgraph_agent/setup.py
touch langgraph_agent/README.md
touch langgraph_agent/.env.example

# Create agent module files
touch langgraph_agent/agent/state.py
touch langgraph_agent/agent/nodes.py
touch langgraph_agent/agent/graph.py
touch langgraph_agent/agent/workflows.py

# Create MCP integration files
touch langgraph_agent/mcp_integration/client.py
touch langgraph_agent/mcp_integration/tools.py
touch langgraph_agent/mcp_integration/topic_router.py

# Create education module files
touch langgraph_agent/education/learning_paths.py
touch langgraph_agent/education/concept_tracker.py
touch langgraph_agent/education/explanation_engine.py

# Create storage files
touch langgraph_agent/storage/checkpointer.py
touch langgraph_agent/storage/concept_memory.py

# Create config files (YAML)
touch langgraph_agent/config/agent_config.yaml
touch langgraph_agent/config/mcp_endpoints.yaml
touch langgraph_agent/config/learning_config.yaml

# Create utility files
touch langgraph_agent/utils/logger.py
touch langgraph_agent/utils/error_handler.py
touch langgraph_agent/utils/validators.py

# Create test files
touch langgraph_agent/tests/test_agent.py
touch langgraph_agent/tests/test_mcp_integration.py
touch langgraph_agent/tests/test_workflows.py

# Create requirements.txt with basic content
cat > langgraph_agent/requirements.txt << 'EOF'
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.2.0
langchain-core>=0.3.0
fastapi>=0.100.0
uvicorn>=0.20.0
httpx>=0.25.0
pydantic>=2.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
redis>=4.0.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
EOF

echo "✅ LangGraph Educational Agent structure created successfully!"
echo "📁 Directory: ./langgraph_agent/"
echo "📝 Files created: 22 Python files + configs"
echo ""
echo "Next steps:"
echo "1. cd langgraph_agent"
echo "2. pip install -r requirements.txt"
echo "3. Configure your MCP endpoints in config/mcp_endpoints.yaml"
echo "4. Start implementing the core files"
