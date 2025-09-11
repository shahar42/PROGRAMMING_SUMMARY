#!/usr/bin/env python3
"""
Quick test script to verify the Topology Analyzer is working.
Run after starting the server:
    python scripts/topology_analyzer_mcp.py &
    python scripts/test_topology_analyzer.py
"""

import asyncio
import httpx
import json
from pathlib import Path


async def test_analyzer_tools():
    """Test each analyzer tool with sample inputs."""
    
    base_url = "http://localhost:8109"
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code != 200:
                print("❌ Server not responding on port 8109")
                print("   Start it with: python scripts/topology_analyzer_mcp.py")
                return
    except:
        print("❌ Cannot connect to server on port 8109")
        print("   Start it with: python scripts/topology_analyzer_mcp.py")
        return
    
    print("✅ Server is running on port 8109")
    print("\nTesting analyzer tools...\n")
    
    # Test 1: Analyze complexity of a specific file
    print("1. Testing analyze_code_complexity...")
    test_file = "agent/graph.py"
    
    if Path(test_file).exists():
        response = await call_tool("analyze_code_complexity", {"path": test_file})
        if response and response.get('success'):
            summary = response.get('summary', {})
            print(f"   ✅ Analyzed {test_file}")
            print(f"      - Complexity: {summary.get('complexity', 'N/A')}")
            print(f"      - Issues: {summary.get('issues', 0)}")
        else:
            print(f"   ❌ Failed to analyze {test_file}")
    else:
        print(f"   ⚠️  {test_file} not found, skipping")
    
    # Test 2: Map dependencies
    print("\n2. Testing map_function_dependencies...")
    response = await call_tool("map_function_dependencies", {"path": "."})
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        print(f"   ✅ Mapped dependencies")
        print(f"      - Total modules: {summary.get('total_modules', 0)}")
        print(f"      - Circular deps: {summary.get('circular_dependencies_found', False)}")
        print(f"      - Missing modules: {summary.get('missing_modules_count', 0)}")
    else:
        print("   ❌ Failed to map dependencies")
    
    # Test 3: Check architecture
    print("\n3. Testing detect_architecture_violations...")
    response = await call_tool("detect_architecture_violations", {"path": "."})
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        print(f"   ✅ Architecture analyzed")
        print(f"      - Violations: {summary.get('violation_count', 0)}")
        print(f"      - Critical: {summary.get('critical_violations', 0)}")
        print(f"      - Layers: {summary.get('layer_count', 0)}")
    else:
        print("   ❌ Failed to analyze architecture")
    
    # Test 4: Find hotspots
    print("\n4. Testing find_maintenance_hotspots...")
    response = await call_tool("find_maintenance_hotspots", {"path": "."})
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        hotspots = response.get('hotspots', [])
        print(f"   ✅ Found hotspots")
        print(f"      - Total: {summary.get('total_hotspots', 0)}")
        print(f"      - High risk: {summary.get('high_risk_files', 0)}")
        
        if hotspots:
            print(f"      - Top hotspot: {Path(hotspots[0]['file']).name} (risk: {hotspots[0]['risk_score']})")
    else:
        print("   ❌ Failed to find hotspots")
    
    # Test 5: Analyze integration points
    print("\n5. Testing analyze_integration_points...")
    response = await call_tool("analyze_integration_points", {
        "path": ".",
        "focus_module": "mcp_integration.client"
    })
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        analysis = response.get('analysis', {})
        print(f"   ✅ Integration analyzed")
        print(f"      - Missing: {summary.get('missing_count', 0)}")
        print(f"      - Integration points: {summary.get('integration_points', 0)}")
        print(f"      - Critical issues: {summary.get('critical_issues', 0)}")
        
        # Check for GOT/PLT issues
        issues = analysis.get('issues', [])
        got_plt_issues = [i for i in issues if i.get('type') == 'got_plt_missing']
        if got_plt_issues:
            print(f"      - ⚠️  GOT/PLT issue detected: {got_plt_issues[0].get('suggestion', '')}")
    else:
        print("   ❌ Failed to analyze integration")
    
    # Test 6: Generate suggestions
    print("\n6. Testing generate_refactor_suggestions...")
    response = await call_tool("generate_refactor_suggestions", {"path": "."})
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        suggestions = response.get('suggestions', [])
        print(f"   ✅ Generated suggestions")
        print(f"      - Total: {summary.get('total_suggestions', 0)}")
        print(f"      - High priority: {summary.get('high_priority', 0)}")
        
        if suggestions:
            print(f"      - Top issue: {suggestions[0].get('issue', 'N/A')}")
    else:
        print("   ❌ Failed to generate suggestions")
    
    # Test 7: Assess health
    print("\n7. Testing assess_code_health...")
    response = await call_tool("assess_code_health", {"path": "."})
    
    if response and response.get('success'):
        report = response.get('report', {})
        print(f"   ✅ Health assessed")
        print(f"      - Score: {report.get('health_score', 0)}/100")
        print(f"      - Status: {report.get('status', 'Unknown')}")
        
        metrics = report.get('metrics', {})
        print(f"      - Avg complexity: {metrics.get('avg_complexity', 0)}")
        print(f"      - Doc coverage: {metrics.get('doc_coverage', 0)}%")
    else:
        print("   ❌ Failed to assess health")
    
    # Test 8: Create graph
    print("\n8. Testing create_dependency_graph...")
    response = await call_tool("create_dependency_graph", {
        "path": ".",
        "output_format": "summary"
    })
    
    if response and response.get('success'):
        summary = response.get('summary', {})
        print(f"   ✅ Graph created")
        print(f"      - Nodes: {summary.get('total_nodes', 0)}")
        print(f"      - Edges: {summary.get('total_edges', 0)}")
        print(f"      - Has cycles: {summary.get('has_cycles', False)}")
        print(f"      - Longest chain: {summary.get('longest_chain', 0)}")
    else:
        print("   ❌ Failed to create graph")
    
    print("\n" + "="*50)
    print("Testing complete!")
    print("\nUse these tools through your chat interface to analyze specific issues.")


async def call_tool(tool_name: str, params: dict) -> dict:
    """Call a tool via HTTP (simulating MCP call)."""
    try:
        # In real usage, this would go through the MCP client
        # For testing, we'll import and call directly
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from scripts import topology_analyzer_mcp as analyzer
        
        tool_func = getattr(analyzer, tool_name)
        result = await tool_func(**params)
        return result
    except Exception as e:
        print(f"   Error calling {tool_name}: {e}")
        return None


if __name__ == "__main__":
    print("="*50)
    print("TOPOLOGY ANALYZER TEST SUITE")
    print("="*50)
    print()
    
    asyncio.run(test_analyzer_tools())
