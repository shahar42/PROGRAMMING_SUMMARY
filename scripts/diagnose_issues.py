#!/usr/bin/env python3
"""
Diagnostic script to analyze your three critical issues:
1. agent/graph.py returning None (500 errors)
2. GOT/PLT server missing module
3. Gemini authentication failure

Run this after starting the topology analyzer server:
    python scripts/topology_analyzer_mcp.py &
    python scripts/diagnose_issues.py
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the analyzer tools
from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.dependency_mapper import DependencyMapper
from analyzers.complexity_calculator import ComplexityCalculator
from analyzers.pattern_detector import PatternDetector


async def diagnose_agent_graph_issue():
    """Diagnose why agent/graph.py returns None."""
    print("\n" + "="*60)
    print("DIAGNOSING: agent/graph.py routing issue")
    print("="*60)
    
    filepath = "agent/graph.py"
    
    if not Path(filepath).exists():
        print(f"ERROR: {filepath} not found")
        return
    
    # Analyze complexity
    calculator = ComplexityCalculator()
    complexity_result = calculator.analyze_file(filepath)
    
    print("\n1. COMPLEXITY ANALYSIS:")
    print(f"   - Total functions: {len(complexity_result.get('functions', []))}")
    
    # Find complex functions
    complex_functions = []
    for func in complexity_result.get('functions', []):
        if func['cyclomatic_complexity'] > 10:
            complex_functions.append(func)
            print(f"   - {func['name']}: complexity={func['cyclomatic_complexity']} (HIGH)")
    
    # Look for routing functions
    routing_functions = []
    for func in complexity_result.get('functions', []):
        if 'route' in func['name'].lower() or 'router' in func['name'].lower():
            routing_functions.append(func)
            print(f"\n2. ROUTING FUNCTION FOUND: {func['name']}")
            print(f"   - Line: {func['line']}")
            print(f"   - Complexity: {func['cyclomatic_complexity']}")
            print(f"   - Return points: {func['return_points']}")
            print(f"   - Nesting depth: {func['nesting_depth']}")
    
    # Pattern detection
    detector = PatternDetector()
    pattern_result = detector.analyze_file(filepath)
    
    print("\n3. CODE ISSUES:")
    critical_issues = []
    for smell in pattern_result.get('code_smells', []):
        if smell['severity'] in ['high', 'critical']:
            critical_issues.append(smell)
            print(f"   - {smell['type']}: {smell['description']}")
    
    # Look for None returns
    analyzer = ASTAnalyzer()
    ast_result = analyzer.analyze_file(filepath)
    
    print("\n4. POTENTIAL NONE RETURN CAUSES:")
    
    # Check for functions without explicit returns
    for func in ast_result.get('functions', []):
        if func['returns'] is None and not func['name'].startswith('__'):
            print(f"   - {func['name']} has no return type annotation")
    
    # Recommendations
    print("\n5. RECOMMENDATIONS:")
    print("   - Add logging to track where None is being returned")
    print("   - Check all conditional branches have return statements")
    print("   - Verify router configuration and message handling")
    
    if complex_functions:
        print(f"   - Refactor complex functions: {', '.join(f['name'] for f in complex_functions)}")
    
    return {
        'complex_functions': complex_functions,
        'routing_functions': routing_functions,
        'critical_issues': critical_issues
    }


async def diagnose_got_plt_issue():
    """Diagnose missing GOT/PLT server module."""
    print("\n" + "="*60)
    print("DIAGNOSING: GOT/PLT server integration issue")
    print("="*60)
    
    # Map dependencies in mcp_integration
    mapper = DependencyMapper(".")
    
    print("\n1. SEARCHING FOR GOT/PLT REFERENCES...")
    
    # Check mcp_integration/client.py
    client_path = "langgraph_agent/mcp_integration/client.py"
    if Path(client_path).exists():
        mapper._analyze_file_imports(client_path)
        
        # Look for GOT/PLT imports
        for (from_module, to_module), details in mapper.import_details.items():
            if 'got' in to_module.lower() or 'plt' in to_module.lower():
                print(f"\n   Found import: {to_module}")
                print(f"   - Type: {details['type']}")
                print(f"   - Line: {details['line']}")
                print(f"   - From: {from_module}")
    
    # Check scripts directory for GOT/PLT server
    scripts_dir = Path("scripts")
    got_plt_files = []
    
    if scripts_dir.exists():
        for file in scripts_dir.glob("*got*"):
            got_plt_files.append(file)
            print(f"\n2. FOUND FILE: {file}")
        
        for file in scripts_dir.glob("*plt*"):
            got_plt_files.append(file)
            print(f"   FOUND FILE: {file}")
    
    if not got_plt_files:
        print("\n2. NO GOT/PLT SERVER FILES FOUND IN scripts/")
        print("   Expected: scripts/got_plt_server.py or similar")
    
    # Check for binary analysis tools
    print("\n3. CHECKING BINARY ANALYSIS TOOLS...")
    
    binary_tools = [
        "analyze_elf", "extract_got", "extract_plt", "analyze_binary",
        "disassemble", "find_gadgets", "check_protections", "dump_symbols"
    ]
    
    found_tools = []
    missing_tools = []
    
    # Search for tool definitions
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        for tool in binary_tools:
                            if f"def {tool}" in content or f"async def {tool}" in content:
                                found_tools.append((tool, filepath))
                                print(f"   Found tool: {tool} in {filepath}")
                except:
                    pass
    
    missing_tools = [t for t in binary_tools if t not in [f[0] for f in found_tools]]
    
    if missing_tools:
        print(f"\n4. MISSING TOOLS: {', '.join(missing_tools)}")
    
    print("\n5. RECOMMENDATIONS:")
    print("   - Create scripts/got_plt_server.py with binary analysis tools")
    print("   - Ensure the server implements all 18 binary analysis functions")
    print("   - Register the server in mcp_integration/client.py")
    print("   - Add configuration to config/mcp_endpoints.yaml")
    
    return {
        'got_plt_files': [str(f) for f in got_plt_files],
        'found_tools': found_tools,
        'missing_tools': missing_tools
    }


async def diagnose_gemini_auth_issue():
    """Diagnose Gemini authentication failure."""
    print("\n" + "="*60)
    print("DIAGNOSING: Gemini authentication issue")
    print("="*60)
    
    # Check for Gemini configuration
    config_files = [
        "config/config.yaml",
        "config/mcp_endpoints.yaml",
        "config/models.yaml",
        ".env"
    ]
    
    gemini_configs = []
    
    print("\n1. CHECKING CONFIGURATION FILES...")
    
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if 'gemini' in content.lower() or 'google' in content.lower():
                        gemini_configs.append(config_file)
                        print(f"   Found Gemini config in: {config_file}")
                        
                        # Look for API key references
                        if 'api_key' in content.lower() or 'apikey' in content.lower():
                            print(f"     - Contains API key reference")
                        if 'GEMINI' in content:
                            print(f"     - Contains GEMINI environment variable")
            except:
                pass
    
    # Check for authentication code
    print("\n2. CHECKING AUTHENTICATION CODE...")
    
    auth_patterns = [
        "genai.configure",
        "google.generativeai",
        "credentials",
        "authenticate",
        "api_key"
    ]
    
    auth_locations = []
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        for pattern in auth_patterns:
                            if pattern in content and 'gemini' in content.lower():
                                auth_locations.append((pattern, filepath))
                                print(f"   Found '{pattern}' in {filepath}")
                                break
                except:
                    pass
    
    # Check environment variables
    print("\n3. CHECKING ENVIRONMENT VARIABLES...")
    
    env_vars = os.environ
    gemini_vars = []
    
    for var in env_vars:
        if 'GEMINI' in var or 'GOOGLE' in var:
            gemini_vars.append(var)
            print(f"   Found: {var}=<set>")
    
    if not gemini_vars:
        print("   No GEMINI or GOOGLE environment variables found")
    
    print("\n4. RECOMMENDATIONS:")
    print("   - Set GEMINI_API_KEY environment variable")
    print("   - Verify API key is valid at https://makersuite.google.com/app/apikey")
    print("   - Check if using correct authentication method:")
    print("     import google.generativeai as genai")
    print("     genai.configure(api_key=os.getenv('GEMINI_API_KEY'))")
    print("   - Ensure proper error handling in Gemini initialization")
    
    return {
        'config_files': gemini_configs,
        'auth_locations': auth_locations,
        'env_vars': gemini_vars
    }


async def run_integration_analysis():
    """Run comprehensive integration analysis."""
    print("\n" + "="*60)
    print("COMPREHENSIVE INTEGRATION ANALYSIS")
    print("="*60)
    
    # Map all dependencies
    mapper = DependencyMapper(".")
    result = mapper.map_project(".")
    
    print(f"\n1. PROJECT OVERVIEW:")
    print(f"   - Total modules: {result['total_modules']}")
    print(f"   - Total dependencies: {result['total_dependencies']}")
    print(f"   - Missing modules: {len(result['missing_modules'])}")
    
    if result['missing_modules']:
        print(f"\n2. MISSING MODULES:")
        for module in result['missing_modules'][:10]:
            print(f"   - {module}")
        
        if len(result['missing_modules']) > 10:
            print(f"   ... and {len(result['missing_modules']) - 10} more")
    
    if result['circular_dependencies']:
        print(f"\n3. CIRCULAR DEPENDENCIES DETECTED:")
        for cycle in result['circular_dependencies']:
            print(f"   - {' -> '.join(cycle)}")
    
    print(f"\n4. TOP COUPLED MODULES:")
    for module, metrics in list(result['coupling_metrics'].items())[:5]:
        print(f"   - {module}:")
        print(f"     Depends on: {metrics['efferent_coupling']} modules")
        print(f"     Used by: {metrics['afferent_coupling']} modules")
    
    return result


async def main():
    """Run all diagnostics."""
    print("\n" + "="*70)
    print(" LANGGRAPH AGENT DIAGNOSTIC TOOL")
    print(" Analyzing your three critical issues...")
    print("="*70)
    
    results = {}
    
    # Issue 1: agent/graph.py
    try:
        results['agent_graph'] = await diagnose_agent_graph_issue()
    except Exception as e:
        print(f"\nError analyzing agent/graph.py: {e}")
        results['agent_graph'] = {'error': str(e)}
    
    # Issue 2: GOT/PLT
    try:
        results['got_plt'] = await diagnose_got_plt_issue()
    except Exception as e:
        print(f"\nError analyzing GOT/PLT: {e}")
        results['got_plt'] = {'error': str(e)}
    
    # Issue 3: Gemini Auth
    try:
        results['gemini'] = await diagnose_gemini_auth_issue()
    except Exception as e:
        print(f"\nError analyzing Gemini: {e}")
        results['gemini'] = {'error': str(e)}
    
    # Overall integration
    try:
        results['integration'] = await run_integration_analysis()
    except Exception as e:
        print(f"\nError in integration analysis: {e}")
        results['integration'] = {'error': str(e)}
    
    # Save results
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "="*70)
    print(" DIAGNOSTIC COMPLETE")
    print(" Results saved to: diagnostic_results.json")
    print("="*70)
    
    print("\n\nNEXT STEPS:")
    print("1. Review the diagnostic output above")
    print("2. Start the topology analyzer server:")
    print("   python scripts/topology_analyzer_mcp.py")
    print("3. Use the analyzer tools through your chat interface:")
    print("   - analyze_integration_points(\"langgraph_agent/mcp_integration\", \"client\")")
    print("   - analyze_code_complexity(\"langgraph_agent/agent/graph.py\")")
    print("   - find_maintenance_hotspots('.')")
    print("4. Fix identified issues based on recommendations")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
