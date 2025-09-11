#!/bin/bash
# Startup script for Topology Analyzer MCP Server

echo "=================================="
echo "Starting Topology Analyzer Server"
echo "=================================="

# Check if port 8109 is already in use
if lsof -Pi :8109 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 8109 is already in use. Stopping existing process..."
    kill $(lsof -Pi :8109 -sTCP:LISTEN -t)
    sleep 2
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install fastmcp uvicorn 2>/dev/null

# Start the server in background
echo "Starting server on port 8109..."
python topology_analyzer_mcp.py &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"
echo ""
echo "Available analysis tools:"
echo "  • analyze_code_complexity - Cyclomatic complexity analysis"
echo "  • map_function_dependencies - Dependency mapping"
echo "  • detect_architecture_violations - Architecture issues"
echo "  • find_maintenance_hotspots - High-risk areas"
echo "  • analyze_integration_points - Integration issues"
echo "  • generate_refactor_suggestions - Refactoring advice"
echo "  • assess_code_health - Overall health metrics"
echo "  • create_dependency_graph - Dependency visualization"
echo ""
echo "To run diagnostics: python diagnose_issues.py"
echo "To stop server: kill $SERVER_PID"
echo ""
echo "Server log:"
echo "----------"

# Keep script running to show logs
tail -f /dev/null
