#!/usr/bin/env python3
"""
Program Topology Analyzer MCP Server
Provides code structure and dependency analysis tools.
Port: 8109
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import analyzer modules
from analyzers.ast_analyzer import ASTAnalyzer, analyze_directory
from analyzers.dependency_mapper import DependencyMapper
from analyzers.complexity_calculator import ComplexityCalculator, analyze_complexity_batch
from analyzers.pattern_detector import PatternDetector
from analyzers.architecture_validator import ArchitectureValidator, validate_clean_architecture
from analyzers.graph_builder import GraphBuilder, build_complete_graph

# Import FastMCP
try:
    from fastmcp import FastMCP, Context
except ImportError:
    print("FastMCP not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastmcp"])
    from fastmcp import FastMCP, Context

# Initialize MCP server
mcp = FastMCP(
    name="topology_analyzer",
    version="1.0.0"
)

# Global state for analysis results
analysis_cache = {}


@mcp.tool()
async def analyze_code_complexity(path: str, recursive: bool = True) -> Dict[str, Any]:
    """
    Analyze code complexity metrics including cyclomatic complexity and nesting depth.
    
    Args:
        path: File or directory path to analyze
        recursive: Whether to analyze subdirectories (default: True)
    
    Returns:
        Dictionary containing complexity metrics, issues, and recommendations
    """
    try:
        path = Path(path).resolve()
        
        if path.is_file():
            calculator = ComplexityCalculator()
            result = calculator.analyze_file(str(path))
        else:
            # Find all Python files
            files = []
            if recursive:
                for root, dirs, filenames in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
                    for filename in filenames:
                        if filename.endswith('.py'):
                            files.append(os.path.join(root, filename))
            else:
                files = [f for f in path.glob('*.py')]
            
            result = analyze_complexity_batch([str(f) for f in files])
        
        # Cache results
        analysis_cache['complexity'] = result
        
        return {
            'success': True,
            'analysis': result,
            'summary': _generate_complexity_summary(result)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def map_function_dependencies(path: str) -> Dict[str, Any]:
    """
    Map function call graphs and module dependencies with coupling analysis.
    
    Args:
        path: Directory path to analyze
    
    Returns:
        Dependency map with import chains, circular dependencies, and coupling metrics
    """
    try:
        mapper = DependencyMapper(str(Path(path).resolve()))
        result = mapper.map_project(str(Path(path).resolve()))
        
        # Cache results
        analysis_cache['dependencies'] = result
        
        return {
            'success': True,
            'analysis': result,
            'summary': {
                'total_modules': result['total_modules'],
                'total_dependencies': result['total_dependencies'],
                'circular_dependencies_found': len(result['circular_dependencies']) > 0,
                'missing_modules_count': len(result['missing_modules']),
                'top_coupled_modules': list(result['coupling_metrics'].keys())[:3]
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def detect_architecture_violations(path: str) -> Dict[str, Any]:
    """
    Detect architectural violations including layering issues and circular dependencies.
    
    Args:
        path: Directory path to analyze
    
    Returns:
        Architecture analysis with violations, metrics, and recommendations
    """
    try:
        # First get dependency map
        mapper = DependencyMapper(str(Path(path).resolve()))
        dep_result = mapper.map_project(str(Path(path).resolve()))
        
        # Then validate architecture
        validator = ArchitectureValidator(str(Path(path).resolve()))
        result = validator.analyze_architecture(dep_result['dependency_graph'])
        
        # Also check clean architecture
        clean_result = validate_clean_architecture(
            str(Path(path).resolve()),
            dep_result['dependency_graph']
        )
        
        result['clean_architecture'] = clean_result.get('clean_architecture_violations', [])
        
        # Cache results
        analysis_cache['architecture'] = result
        
        return {
            'success': True,
            'analysis': result,
            'summary': {
                'violation_count': len(result['violations']),
                'critical_violations': sum(1 for v in result['violations'] if v['severity'] == 'critical'),
                'layer_count': len(result['layers']),
                'recommendations': result['recommendations'][:3]
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def find_maintenance_hotspots(path: str) -> Dict[str, Any]:
    """
    Identify high-risk areas that need refactoring based on complexity and coupling.
    
    Args:
        path: Directory path to analyze
    
    Returns:
        List of maintenance hotspots with risk scores and recommendations
    """
    try:
        hotspots = []
        
        # Analyze complexity
        files = []
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))
        
        calculator = ComplexityCalculator()
        
        for filepath in files:
            result = calculator.analyze_file(filepath)
            
            if 'error' not in result:
                # Calculate risk score
                risk_score = _calculate_risk_score(result)
                
                if risk_score > 5:  # Threshold for hotspot
                    hotspots.append({
                        'file': filepath,
                        'risk_score': risk_score,
                        'issues': result.get('issues', []),
                        'metrics': result.get('summary', {}),
                        'functions': [
                            f['name'] for f in result.get('functions', [])
                            if f['cyclomatic_complexity'] > 10
                        ]
                    })
        
        # Sort by risk score
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Cache results
        analysis_cache['hotspots'] = hotspots
        
        return {
            'success': True,
            'hotspots': hotspots[:10],  # Top 10 hotspots
            'summary': {
                'total_hotspots': len(hotspots),
                'high_risk_files': len([h for h in hotspots if h['risk_score'] > 10]),
                'total_issues': sum(len(h['issues']) for h in hotspots)
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def analyze_integration_points(path: str, focus_module: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze MCP tool integration points and identify missing connections.
    
    Args:
        path: Directory path to analyze
        focus_module: Optional specific module to focus on
    
    Returns:
        Integration analysis with missing imports, broken links, and connection map
    """
    try:
        mapper = DependencyMapper(str(Path(path).resolve()))
        dep_result = mapper.map_project(str(Path(path).resolve()))
        
        integration_analysis = {
            'missing_modules': dep_result['missing_modules'],
            'import_chains': dep_result['import_chains'],
            'integration_points': []
        }
        
        # Find MCP-specific integration points
        for module, deps in dep_result['dependency_graph'].items():
            if 'mcp' in module.lower() or 'integration' in module.lower():
                integration_analysis['integration_points'].append({
                    'module': module,
                    'dependencies': deps,
                    'missing': [d for d in deps if d in dep_result['missing_modules']]
                })
        
        # Focus on specific module if requested
        if focus_module:
            specific = mapper.find_module_dependencies(focus_module)
            integration_analysis['focused_analysis'] = specific
        
        # Look for common integration issues
        issues = []
        
        # Check for missing MCP servers
        mcp_imports = [m for m in dep_result['missing_modules'] if 'mcp' in m.lower()]
        if mcp_imports:
            issues.append({
                'type': 'missing_mcp_servers',
                'modules': mcp_imports,
                'suggestion': 'Check if MCP servers are in expected locations'
            })
        
        # Check for GOT/PLT specific issues
        got_plt_imports = [m for m in dep_result['missing_modules'] if 'got' in m.lower() or 'plt' in m.lower()]
        if got_plt_imports:
            issues.append({
                'type': 'got_plt_missing',
                'modules': got_plt_imports,
                'suggestion': 'GOT/PLT server module not found - check scripts directory'
            })
        
        integration_analysis['issues'] = issues
        
        # Cache results
        analysis_cache['integration'] = integration_analysis
        
        return {
            'success': True,
            'analysis': integration_analysis,
            'summary': {
                'missing_count': len(dep_result['missing_modules']),
                'integration_points': len(integration_analysis['integration_points']),
                'critical_issues': len([i for i in issues if i['type'] in ['missing_mcp_servers', 'got_plt_missing']])
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def generate_refactor_suggestions(path: str) -> Dict[str, Any]:
    """
    Generate actionable refactoring suggestions based on code analysis.
    
    Args:
        path: Directory path to analyze
    
    Returns:
        Prioritized list of refactoring suggestions with impact scores
    """
    try:
        suggestions = []
        
        # Run pattern detection
        detector = PatternDetector()
        files = []
        
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))
        
        for filepath in files[:20]:  # Limit to prevent timeout
            result = detector.analyze_file(filepath)
            
            if 'error' not in result:
                # Generate suggestions based on patterns
                for smell in result.get('code_smells', []):
                    suggestions.append({
                        'file': filepath,
                        'type': 'code_smell',
                        'issue': smell['type'],
                        'location': smell.get('location', 'unknown'),
                        'suggestion': smell.get('suggestion', 'Refactor needed'),
                        'priority': _severity_to_priority(smell.get('severity', 'low'))
                    })
                
                for anti in result.get('anti_patterns', []):
                    suggestions.append({
                        'file': filepath,
                        'type': 'anti_pattern',
                        'issue': anti['type'],
                        'location': anti.get('location', 'unknown'),
                        'suggestion': anti.get('suggestion', 'Consider refactoring'),
                        'priority': _severity_to_priority(anti.get('severity', 'medium'))
                    })
        
        # Sort by priority
        suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Group by type for summary
        grouped = {}
        for sugg in suggestions:
            issue_type = sugg['issue']
            if issue_type not in grouped:
                grouped[issue_type] = []
            grouped[issue_type].append(sugg)
        
        # Cache results
        analysis_cache['suggestions'] = suggestions
        
        return {
            'success': True,
            'suggestions': suggestions[:20],  # Top 20 suggestions
            'grouped': {k: v[:5] for k, v in grouped.items()},  # Top 5 per type
            'summary': {
                'total_suggestions': len(suggestions),
                'high_priority': len([s for s in suggestions if s['priority'] >= 8]),
                'most_common_issues': list(grouped.keys())[:5]
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def assess_code_health(path: str) -> Dict[str, Any]:
    """
    Provide overall code health metrics and quality assessment.
    
    Args:
        path: Directory path to analyze
    
    Returns:
        Comprehensive health report with scores and trend indicators
    """
    try:
        # Run comprehensive analysis
        analyzer = ASTAnalyzer()
        results = analyze_directory(str(Path(path).resolve()))
        
        # Calculate health metrics
        total_files = len(results)
        total_functions = sum(len(r.get('functions', [])) for r in results)
        total_classes = sum(len(r.get('classes', [])) for r in results)
        total_lines = sum(r.get('lines_of_code', 0) for r in results)
        
        # Calculate average complexity
        all_complexities = []
        for r in results:
            for f in r.get('functions', []):
                all_complexities.append(f.get('complexity', 0))
        
        avg_complexity = sum(all_complexities) / len(all_complexities) if all_complexities else 0
        
        # Calculate docstring coverage
        total_with_docs = sum(1 for r in results for f in r.get('functions', []) if f.get('docstring'))
        doc_coverage = (total_with_docs / total_functions * 100) if total_functions > 0 else 0
        
        # Calculate health score (0-100)
        health_score = _calculate_health_score(
            avg_complexity=avg_complexity,
            doc_coverage=doc_coverage,
            total_files=total_files
        )
        
        # Determine health status
        if health_score >= 80:
            status = "Excellent"
        elif health_score >= 60:
            status = "Good"
        elif health_score >= 40:
            status = "Fair"
        else:
            status = "Needs Attention"
        
        health_report = {
            'health_score': round(health_score, 1),
            'status': status,
            'metrics': {
                'total_files': total_files,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_lines': total_lines,
                'avg_complexity': round(avg_complexity, 2),
                'doc_coverage': round(doc_coverage, 1)
            },
            'areas_of_concern': [],
            'strengths': []
        }
        
        # Identify concerns and strengths
        if avg_complexity > 10:
            health_report['areas_of_concern'].append("High average complexity")
        else:
            health_report['strengths'].append("Low complexity code")
        
        if doc_coverage < 50:
            health_report['areas_of_concern'].append("Low documentation coverage")
        elif doc_coverage > 80:
            health_report['strengths'].append("Well documented code")
        
        # Cache results
        analysis_cache['health'] = health_report
        
        return {
            'success': True,
            'report': health_report,
            'recommendations': _generate_health_recommendations(health_report)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def create_dependency_graph(path: str, output_format: str = "ascii") -> Dict[str, Any]:
    """
    Create visual dependency graph and architecture mapping.
    
    Args:
        path: Directory path to analyze
        output_format: Format for output ('ascii', 'json', 'summary')
    
    Returns:
        Dependency graph visualization and relationship data
    """
    try:
        # Get dependency analysis
        mapper = DependencyMapper(str(Path(path).resolve()))
        dep_result = mapper.map_project(str(Path(path).resolve()))
        
        # Build graph
        builder = GraphBuilder()
        graph = builder.build_dependency_graph(dep_result['dependency_graph'])
        
        # Get architecture layers
        validator = ArchitectureValidator(str(Path(path).resolve()))
        arch_result = validator.analyze_architecture(dep_result['dependency_graph'])
        
        # Add layered view
        if arch_result['layers']:
            graph['layered_view'] = builder.create_layered_graph(
                arch_result['layers'],
                dep_result['dependency_graph']
            )
        
        # Format output based on request
        if output_format == "ascii":
            output = {
                'visualization': graph['ascii_visualization'],
                'layered_view': graph.get('layered_view', 'No layers detected')
            }
        elif output_format == "json":
            output = {
                'nodes': graph['nodes'],
                'edges': graph['edges'],
                'statistics': graph['statistics']
            }
        else:  # summary
            output = {
                'statistics': graph['statistics'],
                'critical_path': graph['critical_path'][:10] if graph['critical_path'] else [],
                'clusters': [list(c)[:5] for c in graph['clusters'][:3]] if graph['clusters'] else []
            }
        
        # Cache results
        analysis_cache['graph'] = graph
        
        return {
            'success': True,
            'graph': output,
            'summary': {
                'total_nodes': graph['statistics']['total_nodes'],
                'total_edges': graph['statistics']['total_edges'],
                'has_cycles': len(dep_result['circular_dependencies']) > 0,
                'longest_chain': len(graph['critical_path']) if graph['critical_path'] else 0
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Helper functions
def _generate_complexity_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary from complexity analysis."""
    if 'files_analyzed' in result:
        # Batch result
        return {
            'files_analyzed': result['files_analyzed'],
            'total_issues': result['total_issues'],
            'avg_complexity': round(result.get('avg_complexity', 0), 2),
            'high_complexity_files': len(result.get('high_complexity_files', []))
        }
    else:
        # Single file result
        return {
            'complexity': result.get('summary', {}).get('max_complexity', 0),
            'issues': len(result.get('issues', [])),
            'complex_functions': result.get('summary', {}).get('complex_functions', [])
        }


def _calculate_risk_score(analysis: Dict[str, Any]) -> float:
    """Calculate risk score for a file based on various metrics."""
    score = 0
    
    # Complexity factors
    summary = analysis.get('summary', {})
    score += summary.get('max_complexity', 0) * 0.5
    score += summary.get('avg_complexity', 0) * 0.3
    
    # Issue factors
    issues = analysis.get('issues', [])
    score += len(issues) * 0.5
    score += sum(1 for i in issues if i.get('severity') == 'warning') * 1
    score += sum(1 for i in issues if i.get('severity') == 'critical') * 2
    
    # Maintainability factor
    maintainability = summary.get('maintainability', 100)
    score += (100 - maintainability) / 10
    
    return round(score, 1)


def _severity_to_priority(severity: str) -> int:
    """Convert severity to priority score (0-10)."""
    mapping = {
        'critical': 10,
        'high': 8,
        'medium': 5,
        'low': 3,
        'info': 1
    }
    return mapping.get(severity, 3)


def _calculate_health_score(avg_complexity: float, doc_coverage: float, total_files: int) -> float:
    """Calculate overall health score (0-100)."""
    score = 100
    
    # Complexity penalty (up to -40 points)
    if avg_complexity > 5:
        score -= min(40, (avg_complexity - 5) * 4)
    
    # Documentation bonus/penalty (up to ±20 points)
    if doc_coverage < 50:
        score -= (50 - doc_coverage) * 0.4
    elif doc_coverage > 80:
        score += (doc_coverage - 80) * 0.2
    
    # Size penalty for very large codebases
    if total_files > 100:
        score -= min(10, total_files / 50)
    
    return max(0, min(100, score))


def _generate_health_recommendations(report: Dict[str, Any]) -> List[str]:
    """Generate health improvement recommendations."""
    recommendations = []
    
    metrics = report['metrics']
    
    if metrics['avg_complexity'] > 10:
        recommendations.append(
            "Reduce code complexity by breaking down complex functions into smaller, focused ones"
        )
    
    if metrics['doc_coverage'] < 50:
        recommendations.append(
            "Improve documentation coverage - aim for at least 70% of functions with docstrings"
        )
    
    if report['health_score'] < 60:
        recommendations.append(
            "Consider a focused refactoring sprint to address technical debt"
        )
    
    if not recommendations:
        recommendations.append(
            "Code health is good - maintain current practices and consider adding automated quality checks"
        )
    
    return recommendations


if __name__ == "__main__":
    import uvicorn
    print("Starting Topology Analyzer MCP Server on port 8109...")
    print("Available tools:")
    print("  - analyze_code_complexity")
    print("  - map_function_dependencies")
    print("  - detect_architecture_violations")
    print("  - find_maintenance_hotspots")
    print("  - analyze_integration_points")
    print("  - generate_refactor_suggestions")
    print("  - assess_code_health")
    print("  - create_dependency_graph")
    
    # Run the server
    uvicorn.run(
        "topology_analyzer_mcp:mcp",
        host="0.0.0.0",
        port=8109,
        reload=False,
        log_level="info"
    )
