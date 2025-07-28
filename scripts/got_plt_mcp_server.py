#!/usr/bin/env python3
"""
GOT/PLT Educational MCP Server

A specialized Model Context Protocol server that provides educational and research-focused
analysis of the Global Offset Table (GOT) and Procedure Linkage Table (PLT) in dynamically
linked binaries. Integrates with the existing MCP multi-server architecture.

Port: 8108
Framework: FastMCP
Educational Focus: Makes complex dynamic linking concepts accessible to learners
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback

# Add current directory to Python path for local imports
sys.path.append('.')

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("FastMCP not found. Please install: pip install fastmcp")

# Import our analysis modules
from analyzers.binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub, SymbolInfo
from analyzers.runtime_analyzer import RuntimeAnalyzer
from analyzers.lazy_binding_analyzer import LazyBindingAnalyzer
from utils.binary_parser import BinaryParser
from educational.explainer import EducationalExplainer
from educational.concept_validator import ConceptValidator
from educational.example_generator import EnhancedExampleGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("got-plt-mcp")

# Initialize FastMCP server
mcp = FastMCP("GOT/PLT Educational Analysis Server")

# Global educational explainer, concept validator, and example generator
explainer = EducationalExplainer()
concept_validator = ConceptValidator()
example_generator = EnhancedExampleGenerator()

# Server metadata for integration
SERVER_INFO = {
    "name": "GOT/PLT Dynamic Linking Analysis",
    "port": 8108,
    "focus": "Educational analysis of Global Offset Table and Procedure Linkage Table",
    "keywords": [
        "got", "plt", "dynamic linking", "lazy binding", "symbol resolution",
        "global offset table", "procedure linkage table", "runtime linking",
        "shared libraries", "symbol interposition", "relocation"
    ],
    "educational": True,
    "complexity_levels": ["beginner", "intermediate", "advanced"]
}


@mcp.tool()
def inspect_got_table(binary_path: str, detail_level: str = "intermediate") -> str:
    """
    Analyze Global Offset Table entries with educational explanations
    
    Args:
        binary_path: Path to ELF binary to analyze
        detail_level: Explanation complexity ("beginner", "intermediate", "advanced")
    
    Returns:
        Formatted analysis of GOT entries with educational context
    """
    try:
        logger.info(f"Analyzing GOT table in {binary_path} at {detail_level} level")
        
        # Validate inputs
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
            
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize analyzer
        analyzer = BinaryAnalyzer(binary_path)
        got_entries = analyzer.analyze_got_table()
        binary_info = analyzer.get_binary_info()
        
        # Generate educational explanation
        result = explainer.generate_got_explanation(
            got_entries=got_entries,
            binary_info=binary_info,
            detail_level=detail_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"GOT analysis failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def analyze_plt_stubs(binary_path: str, symbol_filter: str = None, detail_level: str = "intermediate") -> str:
    """
    Disassemble PLT stubs with educational annotations
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbol_filter: Optional symbol name to focus analysis on
        detail_level: Explanation complexity ("beginner", "intermediate", "advanced")
    
    Returns:
        Annotated disassembly of PLT stubs with educational explanations
    """
    try:
        logger.info(f"Analyzing PLT stubs in {binary_path}")
        
        # Validate inputs
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
            
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize analyzer
        analyzer = BinaryAnalyzer(binary_path)
        plt_stubs = analyzer.analyze_plt_stubs()
        binary_info = analyzer.get_binary_info()
        
        # Filter by symbol if requested
        if symbol_filter:
            plt_stubs = [stub for stub in plt_stubs 
                        if symbol_filter.lower() in stub.symbol_name.lower()]
        
        # Generate educational explanation
        result = explainer.generate_plt_explanation(
            plt_stubs=plt_stubs,
            binary_info=binary_info,
            detail_level=detail_level,
            symbol_filter=symbol_filter
        )
        
        return result
        
    except Exception as e:
        logger.error(f"PLT analysis failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def list_dynamic_symbols(binary_path: str, category: str = "all", detail_level: str = "intermediate") -> str:
    """
    List symbols requiring dynamic resolution with educational context
    
    Args:
        binary_path: Path to ELF binary to analyze
        category: Symbol category ("imports", "exports", "all")
        detail_level: Explanation complexity ("beginner", "intermediate", "advanced")
    
    Returns:
        Categorized symbol listing with educational explanations
    """
    try:
        logger.info(f"Listing dynamic symbols in {binary_path}, category: {category}")
        
        # Validate inputs
        if category not in ["imports", "exports", "all"]:
            category = "all"
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
            
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize analyzer
        analyzer = BinaryAnalyzer(binary_path)
        symbols = analyzer.list_dynamic_symbols(category)
        binary_info = analyzer.get_binary_info()
        
        # Generate educational explanation
        result = explainer.generate_symbols_explanation(
            symbols=symbols,
            binary_info=binary_info,
            category=category,
            detail_level=detail_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Symbol listing failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def explain_linking_process(binary_path: str, detail_level: str = "intermediate") -> str:
    """
    Educational walkthrough of the entire dynamic linking process
    
    Args:
        binary_path: Path to ELF binary to analyze
        detail_level: Explanation complexity ("beginner", "intermediate", "advanced")
    
    Returns:
        Comprehensive step-by-step explanation of dynamic linking
    """
    try:
        logger.info(f"Explaining linking process for {binary_path}")
        
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
            
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize analyzer and gather all information
        analyzer = BinaryAnalyzer(binary_path)
        got_entries = analyzer.analyze_got_table()
        plt_stubs = analyzer.analyze_plt_stubs()
        symbols = analyzer.list_dynamic_symbols()
        binary_info = analyzer.get_binary_info()
        
        # Generate comprehensive educational explanation
        result = explainer.generate_comprehensive_linking_explanation(
            got_entries=got_entries,
            plt_stubs=plt_stubs,
            symbols=symbols,
            binary_info=binary_info,
            detail_level=detail_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Linking explanation failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def list_available_concepts() -> str:
    """
    List all available concepts for validation from the Linkers & Loaders knowledge base
    
    Returns:
        List of concept names that can be validated against binaries
    """
    try:
        concepts = concept_validator.list_available_concepts()
        
        if not concepts:
            return "⚠️ No concepts loaded from the knowledge base. Check if the linkers_loaders concepts directory exists."
        
        result = f"📚 **Available Linker Concepts for Validation ({len(concepts)})**\n\n"
        
        # Group concepts by category for better organization
        categories = {
            "GOT/PLT": [],
            "Symbol Resolution": [],
            "Dynamic Linking": [],
            "Relocations": [],
            "Other": []
        }
        
        for concept in concepts:
            concept_lower = concept.lower()
            if any(keyword in concept_lower for keyword in ['got', 'plt', 'offset', 'linkage']):
                categories["GOT/PLT"].append(concept)
            elif any(keyword in concept_lower for keyword in ['symbol', 'binding', 'resolution']):
                categories["Symbol Resolution"].append(concept)
            elif any(keyword in concept_lower for keyword in ['dynamic', 'lazy', 'runtime', 'shared']):
                categories["Dynamic Linking"].append(concept)
            elif any(keyword in concept_lower for keyword in ['reloc', 'patch', 'fixup']):
                categories["Relocations"].append(concept)
            else:
                categories["Other"].append(concept)
        
        for category, concept_list in categories.items():
            if concept_list:
                result += f"**{category}:**\n"
                for concept in sorted(concept_list):
                    result += f"- {concept}\n"
                result += "\n"
        
        result += "💡 **Usage:** Use `validate_concept(concept_name)` to test any of these concepts against real binaries.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list concepts: {e}")
        return f"❌ Failed to list concepts: {str(e)}"


@mcp.tool()
def find_related_concepts(search_term: str) -> str:
    """
    Find concepts related to a search term
    
    Args:
        search_term: Term to search for in concept names and descriptions
    
    Returns:
        List of related concepts from the knowledge base
    """
    try:
        if not search_term.strip():
            return "Please provide a search term to find related concepts."
        
        related_concepts = concept_validator.find_related_concepts(search_term)
        
        if not related_concepts:
            available = concept_validator.list_available_concepts()[:5]
            return f"🔍 No concepts found related to '{search_term}'.\n\nTry searching for: {', '.join(available)}"
        
        result = f"🔍 **Concepts Related to '{search_term}' ({len(related_concepts)})**\n\n"
        
        for i, concept in enumerate(related_concepts, 1):
            concept_info = concept_validator.get_concept_info(concept)
            if concept_info:
                description = concept_info['explanation'][:100] + "..." if len(concept_info['explanation']) > 100 else concept_info['explanation']
                result += f"{i}. **{concept}**\n   {description}\n\n"
        
        result += "💡 **Next steps:** Use `validate_concept()` to test any of these concepts, or `get_concept_info()` for detailed information.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to find related concepts: {e}")
        return f"❌ Search failed: {str(e)}"


@mcp.tool()
def get_concept_info(concept_name: str) -> str:
    """
    Get detailed information about a specific concept from the knowledge base
    
    Args:
        concept_name: Name of the concept to get information about
    
    Returns:
        Detailed concept information including theory, examples, and metadata
    """
    try:
        concept_info = concept_validator.get_concept_info(concept_name)
        
        if not concept_info:
            available = concept_validator.list_available_concepts()[:10]
            return f"❌ Concept '{concept_name}' not found.\n\nAvailable concepts: {', '.join(available)}"
        
        result = f"📖 **Concept: {concept_info['topic']}**\n\n"
        
        if concept_info['explanation']:
            result += f"**📚 Theory:**\n{concept_info['explanation']}\n\n"
        
        if concept_info['syntax']:
            result += f"**🔧 Syntax:**\n```c\n{concept_info['syntax']}\n```\n\n"
        
        if concept_info['code_example']:
            code = '\n'.join(concept_info['code_example']) if isinstance(concept_info['code_example'], list) else concept_info['code_example']
            result += f"**💻 Code Example:**\n```c\n{code}\n```\n\n"
        
        if concept_info['example_explanation']:
            result += f"**📝 Example Explanation:**\n{concept_info['example_explanation']}\n\n"
        
        # Add metadata
        metadata = concept_info.get('extraction_metadata', {})
        if metadata:
            result += f"**📄 Source Information:**\n"
            if 'page_range' in metadata:
                result += f"- Pages: {metadata['page_range']}\n"
            if 'extraction_date' in metadata:
                result += f"- Extracted: {metadata['extraction_date']}\n"
            result += f"- File: {concept_info['filename']}\n\n"
        
        result += f"🔬 **Validation:** Use `validate_concept('{concept_name}')` to test this theory against real binaries.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get concept info: {e}")
        return f"❌ Failed to get concept information: {str(e)}"


@mcp.tool()
def trace_symbol_resolution(binary_path: str, symbol_name: str) -> str:
    """
    Live trace of symbol resolution process during program execution
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbol_name: Symbol to trace during resolution
    
    Returns:
        Step-by-step trace of resolution process with educational explanations
    """
    try:
        logger.info(f"Tracing symbol resolution for {symbol_name} in {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize runtime analyzer
        runtime_analyzer = RuntimeAnalyzer(binary_path)
        trace_result = runtime_analyzer.trace_symbol_resolution(symbol_name)
        
        # Format educational response
        result = f"""
🔍 **Symbol Resolution Trace: {symbol_name}**

**Binary:** {binary_path}
**Symbol:** {symbol_name}
**Trace Status:** {'✅ Successful' if trace_result.successful else '❌ Failed'}
**Total Time:** {trace_result.total_time:.6f} seconds
**Resolver Calls:** {trace_result.resolver_calls}

"""
        
        if trace_result.resolution_steps:
            result += "**📋 Resolution Steps:**\n"
            for i, step in enumerate(trace_result.resolution_steps, 1):
                result += f"{i}. **{step.get('location', 'Unknown')}**\n"
                if 'got_value' in step:
                    result += f"   GOT Value: {step['got_value']}\n"
                if 'address' in step:
                    result += f"   Address: {step['address']}\n"
                if 'educational_note' in step:
                    result += f"   📝 {step['educational_note']}\n"
                result += "\n"
        
        result += f"**🎯 Final Address:** {trace_result.final_address}\n\n"
        
        result += "**📚 Educational Context:**\n"
        result += "- Symbol resolution occurs on first access (lazy binding)\n"
        result += "- _dl_runtime_resolve performs the actual symbol lookup\n"
        result += "- GOT entry is updated with resolved address\n"
        result += "- Subsequent calls use the resolved address directly\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Symbol resolution tracing failed: {e}")
        return f"❌ Tracing failed: {str(e)}"


@mcp.tool()
def analyze_lazy_binding(binary_path: str, symbol_name: str) -> str:
    """
    Analyze lazy binding behavior showing first call vs subsequent calls
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbol_name: Symbol to analyze lazy binding for
    
    Returns:
        Analysis of lazy binding behavior with performance comparison
    """
    try:
        logger.info(f"Analyzing lazy binding for {symbol_name} in {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize lazy binding analyzer
        lazy_analyzer = LazyBindingAnalyzer(binary_path)
        
        # Analyze first call behavior
        first_call_analysis = lazy_analyzer.analyze_first_call_behavior(symbol_name)
        
        # Compare call performance
        performance_comparison = lazy_analyzer.compare_call_performance(symbol_name)
        
        # Format comprehensive response
        result = f"""
🔄 **Lazy Binding Analysis: {symbol_name}**

**Binary:** {binary_path}
**Symbol:** {symbol_name}

## 🚀 First Call Analysis

**First Call Detected:** {'✅ Yes' if first_call_analysis['first_call_detected'] else '❌ No'}

"""
        
        # GOT state changes
        got_changes = first_call_analysis.get('got_state_changes', [])
        if got_changes:
            result += "**GOT State Changes:**\n"
            for change in got_changes:
                result += f"- **{change['phase'].replace('_', ' ').title()}:** {change['got_value']}\n"
                result += f"  {change['interpretation']}\n"
            result += "\n"
        
        # Performance metrics
        if performance_comparison.get('performance_analysis'):
            perf = performance_comparison['performance_analysis']
            result += "## ⚡ Performance Analysis\n\n"
            
            if 'time_between_calls' in perf:
                result += f"**Resolution Overhead:** {perf['time_between_calls']:.6f} seconds\n"
            
            result += f"**Performance Improvement:** {perf.get('performance_improvement', 'Not measured')}\n"
            
            if 'educational_interpretation' in perf:
                result += f"**Impact:** {perf['educational_interpretation']}\n"
            
            result += "\n"
        
        # Educational insights
        result += "## 📚 Educational Insights\n\n"
        
        all_insights = (first_call_analysis.get('educational_insights', []) + 
                       performance_comparison.get('educational_conclusions', []))
        
        for insight in all_insights:
            result += f"- {insight}\n"
        
        result += "\n"
        
        # Summary
        resolution_detected = any(change['phase'] == 'after_resolution' 
                                for change in got_changes)
        
        result += "## 📋 Summary\n\n"
        if resolution_detected:
            result += "✅ **Lazy binding behavior confirmed**\n"
            result += "- GOT entry was updated during first call\n"
            result += "- Symbol resolution overhead measured\n"
            result += "- Subsequent calls will be faster\n"
        else:
            result += "⚠️ **Lazy binding not clearly detected**\n"
            result += "- Symbol may already be resolved\n"
            result += "- Binary might use immediate binding\n"
            result += "- Try with different symbols or test programs\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Lazy binding analysis failed: {e}")
        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def runtime_got_snapshot(binary_path: str, execution_point: str = "main") -> str:
    """
    Capture GOT state snapshot at specific execution point
    
    Args:
        binary_path: Path to ELF binary to analyze
        execution_point: Function name to break at for snapshot
    
    Returns:
        GOT state snapshot with runtime analysis
    """
    try:
        logger.info(f"Capturing GOT snapshot at {execution_point} in {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Initialize runtime analyzer
        runtime_analyzer = RuntimeAnalyzer(binary_path)
        snapshot = runtime_analyzer.runtime_got_snapshot(execution_point)
        
        # Format response
        result = f"""
📸 **GOT Runtime Snapshot**

**Binary:** {binary_path}
**Execution Point:** {execution_point}
**Snapshot Time:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(snapshot['timestamp']))}

"""
        
        # Memory layout
        memory_layout = snapshot.get('memory_layout', {})
        if memory_layout:
            result += "## 🧠 Memory Layout\n\n"
            result += f"**Instruction Pointer (RIP):** {memory_layout.get('instruction_pointer', 'unknown')}\n"
            result += f"**Stack Pointer (RSP):** {memory_layout.get('stack_pointer', 'unknown')}\n"
            result += f"**Base Pointer (RBP):** {memory_layout.get('base_pointer', 'unknown')}\n\n"
        
        # GOT entries
        got_entries = snapshot.get('got_entries', {})
        if got_entries:
            result += "## 🎯 GOT Entries State\n\n"
            
            resolved_count = 0
            total_count = len(got_entries)
            
            for symbol, entry_info in list(got_entries.items())[:10]:  # Limit display
                status_icon = "✅" if entry_info['resolved_status'] == 'resolved' else "⏳"
                result += f"**{status_icon} {symbol}**\n"
                result += f"- Static Address: {entry_info['static_address']}\n"
                result += f"- Current Value: {entry_info['current_value']}\n"
                result += f"- Relocation Type: {entry_info['relocation_type']}\n"
                result += f"- Status: {entry_info['resolved_status'].title()}\n\n"
                
                if entry_info['resolved_status'] == 'resolved':
                    resolved_count += 1
            
            if len(got_entries) > 10:
                result += f"... and {len(got_entries) - 10} more entries\n\n"
            
            # Statistics
            result += f"**📊 Statistics:** {resolved_count}/{total_count} entries resolved ({resolved_count/total_count*100:.1f}%)\n\n"
        
        # Educational context
        result += "## 📚 Educational Context\n\n"
        for context in snapshot.get('educational_context', []):
            result += f"- {context}\n"
        
        result += "\n**💡 Runtime Analysis Notes:**\n"
        result += "- Resolved entries point to actual function addresses\n"
        result += "- Unresolved entries point to PLT resolver stubs\n"
        result += "- Resolution happens on first access (lazy binding)\n"
        result += "- Snapshot shows program state at specific execution point\n"
        
        return result
        
    except Exception as e:
        logger.error(f"GOT snapshot failed: {e}")
        return f"❌ Snapshot failed: {str(e)}"


@mcp.tool()
def compare_binding_modes(binary_path: str, symbols: str = "printf,malloc,free") -> str:
    """
    Compare lazy vs immediate binding behavior for specified symbols
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbols: Comma-separated list of symbols to analyze
    
    Returns:
        Comparison of binding modes with educational analysis
    """
    try:
        logger.info(f"Comparing binding modes in {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Parse symbols list
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        
        # Initialize runtime analyzer
        runtime_analyzer = RuntimeAnalyzer(binary_path)
        comparison = runtime_analyzer.compare_binding_modes(symbol_list)
        
        # Format response
        result = f"""
⚖️ **Binding Mode Comparison**

**Binary:** {binary_path}
**Symbols Analyzed:** {', '.join(symbol_list)}

## 🔄 Lazy Binding Analysis Results

"""
        
        # Results for each symbol
        lazy_results = comparison.get('lazy_binding_results', {})
        for symbol, analysis in lazy_results.items():
            result += f"### {symbol}\n"
            
            if analysis.get('first_call_analysis', {}).get('got_after_resolution'):
                got_before = analysis['first_call_analysis'].get('got_before_resolution', 'unknown')
                got_after = analysis['first_call_analysis'].get('got_after_resolution', 'unknown')
                
                if got_before != got_after:
                    result += f"- **Lazy Binding:** ✅ Confirmed (GOT: {got_before} → {got_after})\n"
                else:
                    result += f"- **Lazy Binding:** ⚠️ Not detected (GOT: {got_before})\n"
            else:
                result += f"- **Lazy Binding:** ❌ Analysis incomplete\n"
            
            # Educational insights
            insights = analysis.get('educational_insights', [])
            for insight in insights[:2]:  # Limit for readability
                result += f"- {insight}\n"
            
            result += "\n"
        
        # Performance analysis
        perf_analysis = comparison.get('performance_analysis', {})
        if perf_analysis:
            result += "## 📊 Performance Analysis\n\n"
            result += f"**Symbols Analyzed:** {perf_analysis.get('symbols_analyzed', 0)}\n"
            result += f"**Lazy Binding Detected:** {perf_analysis.get('symbols_showing_lazy_binding', 0)}\n"
            result += f"**Detection Rate:** {perf_analysis.get('binding_effectiveness', 0)*100:.1f}%\n\n"
        
        # Educational comparison
        result += "## 📚 Lazy vs Immediate Binding Comparison\n\n"
        
        educational_summary = comparison.get('educational_summary', [])
        for summary_point in educational_summary:
            result += f"- {summary_point}\n"
        
        result += "\n"
        
        # Immediate binding simulation
        immediate_sim = comparison.get('immediate_binding_simulation', {})
        if immediate_sim:
            result += "## 🚀 Immediate Binding (LD_BIND_NOW=1)\n\n"
            result += f"**Explanation:** {immediate_sim.get('explanation', '')}\n\n"
            
            characteristics = immediate_sim.get('characteristics', {})
            if characteristics:
                result += "**Characteristics:**\n"
                for aspect, description in characteristics.items():
                    result += f"- **{aspect.replace('_', ' ').title()}:** {description}\n"
                result += "\n"
        
        # Practical recommendations
        result += "## 🎯 Practical Recommendations\n\n"
        result += "**Use Lazy Binding (default) when:**\n"
        result += "- Fast startup time is important\n"
        result += "- Not all library functions are used\n"
        result += "- Memory usage should be minimized\n\n"
        
        result += "**Use Immediate Binding (LD_BIND_NOW=1) when:**\n"
        result += "- Predictable performance is required\n"
        result += "- Security is a primary concern\n"
        result += "- Real-time constraints exist\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Binding mode comparison failed: {e}")
        return f"❌ Comparison failed: {str(e)}"


@mcp.tool()
def generate_lazy_binding_report(binary_path: str, symbols: str = "printf,malloc,strlen") -> str:
    """
    Generate comprehensive lazy binding analysis report
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbols: Comma-separated list of symbols to include in report
    
    Returns:
        Comprehensive educational report on lazy binding behavior
    """
    try:
        logger.info(f"Generating lazy binding report for {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Parse symbols list
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        
        # Initialize lazy binding analyzer
        lazy_analyzer = LazyBindingAnalyzer(binary_path)
        
        # Generate comprehensive report
        report = lazy_analyzer.generate_lazy_binding_report(symbol_list)
        
        return report
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return f"❌ Report generation failed: {str(e)}"


@mcp.tool()
def analyze_plt_behavior(binary_path: str, symbols: str = "printf,malloc,free") -> str:
    """
    Analyze PLT behavior for multiple symbols during program execution
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbols: Comma-separated list of symbols to analyze PLT behavior for
    
    Returns:
        Analysis of PLT stub behavior during execution
    """
    try:
        logger.info(f"Analyzing PLT behavior in {binary_path}")
        
        if not Path(binary_path).exists():
            return f"❌ Error: Binary file not found: {binary_path}"
        
        # Parse symbols list
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        
        # Initialize runtime analyzer
        runtime_analyzer = RuntimeAnalyzer(binary_path)
        plt_analysis = runtime_analyzer.analyze_plt_behavior(symbol_list)
        
        # Format response
        result = f"""
📞 **PLT Behavior Analysis**

**Binary:** {binary_path}
**Symbols Analyzed:** {', '.join(symbol_list)}

"""
        
        # PLT interactions
        plt_interactions = plt_analysis.get('plt_interactions', {})
        if plt_interactions:
            result += "## 🔄 PLT Interactions Captured\n\n"
            
            for symbol, interactions in plt_interactions.items():
                result += f"### {symbol}\n"
                result += f"**Total Calls:** {len(interactions)}\n"
                
                for i, interaction in enumerate(interactions[:3], 1):  # Show first 3 calls
                    result += f"\n**Call #{interaction['call_number']}:**\n"
                    result += f"- GOT Value: {interaction['got_value']}\n"
                    result += f"- Instruction Pointer: {interaction['instruction_pointer']}\n"
                    if 'educational_note' in interaction:
                        result += f"- 📝 {interaction['educational_note']}\n"
                
                if len(interactions) > 3:
                    result += f"\n... and {len(interactions) - 3} more calls\n"
                
                result += "\n"
        
        # Call patterns analysis
        call_patterns = plt_analysis.get('call_patterns', {})
        if call_patterns:
            result += "## 📊 Call Pattern Analysis\n\n"
            
            for symbol, pattern in call_patterns.items():
                result += f"**{symbol}:**\n"
                result += f"- Total Calls: {pattern['total_calls']}\n"
                result += f"- First Call GOT: {pattern['first_call_got']}\n"
                result += f"- Last Call GOT: {pattern['last_call_got']}\n"
                result += f"- GOT Changed: {'✅ Yes' if pattern['got_changed'] else '❌ No'}\n\n"
        
        # Educational observations
        result += "## 📚 Educational Observations\n\n"
        
        observations = plt_analysis.get('educational_observations', [])
        for observation in observations:
            result += f"- {observation}\n"
        
        result += "\n**💡 PLT Analysis Insights:**\n"
        result += "- PLT stubs provide uniform entry points for external functions\n"
        result += "- Each PLT entry corresponds to one external symbol\n"
        result += "- PLT works with GOT to implement lazy binding\n"
        result += "- Multiple calls to same function use same PLT stub\n"
        result += "- GOT value changes indicate symbol resolution\n"
        
        return result
        
    except Exception as e:
        logger.error(f"PLT behavior analysis failed: {e}")
        return f"❌ Analysis failed: {str(e)}"
    """
    Detailed comparison between theoretical concept and binary implementation
    
    Args:
        concept_name: Name of concept to compare
        binary_path: Path to binary for practical analysis
    
    Returns:
        Side-by-side comparison of theory vs observed behavior
    """
    try:
        logger.info(f"Comparing theory vs practice for {concept_name} using {binary_path}")
        
        # Get theoretical information
        concept_info = concept_validator.get_concept_info(concept_name)
        if not concept_info:
            return f"❌ Concept '{concept_name}' not found in knowledge base."
        
        if not Path(binary_path).exists():
            return f"❌ Binary not found: {binary_path}"
        
        # Perform validation
        validation_result = concept_validator.validate_concept(concept_name, binary_path)
        
        # Generate side-by-side comparison
        result = f"⚖️ **Theory vs Practice Comparison: {concept_name}**\n\n"
        result += f"📄 **Binary Analyzed:** {binary_path}\n\n"
        
        result += "| 📚 **Theory** | 🔬 **Practice** |\n"
        result += "|---------------|----------------|\n"
        
        # Theory column
        theory_desc = concept_info['explanation'][:200] + "..." if len(concept_info['explanation']) > 200 else concept_info['explanation']
        theory_desc = theory_desc.replace('\n', ' ').replace('|', '\\|')
        
        # Practice column  
        if validation_result.evidence:
            practice_desc = " ".join(validation_result.evidence[:3])[:200] + "..."
        else:
            practice_desc = "No supporting evidence found"
        practice_desc = practice_desc.replace('\n', ' ').replace('|', '\\|')
        
        result += f"| {theory_desc} | {practice_desc} |\n\n"
        
        # Detailed comparison
        result += f"🎯 **Validation Status:** {validation_result.validation_status}\n"
        result += f"📊 **Match Confidence:** {validation_result.confidence_score:.1%}\n\n"
        
        if validation_result.evidence:
            result += "✅ **Supporting Evidence:**\n"
            for evidence in validation_result.evidence:
                result += f"- {evidence}\n"
            result += "\n"
        
        if validation_result.discrepancies:
            result += "❌ **Discrepancies:**\n"
            for discrepancy in validation_result.discrepancies:
                result += f"- {discrepancy}\n"
            result += "\n"
        
        if validation_result.educational_notes:
            result += "📝 **Educational Insights:**\n"
            for note in validation_result.educational_notes:
                result += f"- {note}\n"
            result += "\n"
        
        # Add educational conclusion
        if validation_result.confidence_score >= 0.8:
            result += "🎉 **Conclusion:** The theoretical concept closely matches observed binary behavior!\n"
        elif validation_result.confidence_score >= 0.5:
            result += "🤔 **Conclusion:** The concept is partially confirmed. Some aspects may be context-dependent.\n"
        else:
            result += "🔍 **Conclusion:** Significant differences found. This may reveal edge cases or implementation variations.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Theory vs practice comparison failed: {e}")
        return f"❌ Comparison failed: {str(e)}"
    """
    Validate extracted linker concept against real binary behavior
    
    Args:
        concept_name: Name of concept from knowledge base to validate
        binary_path: Optional specific binary to test against
    
    Returns:
        Validation results comparing theory vs practice
    """
    try:
        logger.info(f"Validating concept: {concept_name}")
        
        # Generate comprehensive validation report
        report = concept_validator.generate_validation_report(concept_name, binary_path)
        
        return report
        
    except Exception as e:
        logger.error(f"Concept validation failed: {e}")
        return f"❌ Validation failed: {str(e)}"


@mcp.tool()
def generate_minimal_example(concept: str) -> str:
    """
    Generate minimal C code demonstrating specific linking behavior
    
    Args:
        concept: Linking concept to demonstrate
    
    Returns:
        C code example with compilation and analysis instructions
    """
    try:
        logger.info(f"Generating example for concept: {concept}")
        
        # Use enhanced example generator that integrates with knowledge base
        result = example_generator.generate_concept_example(concept)
        
        return result
        
    except Exception as e:
        logger.error(f"Example generation failed: {e}")
        return f"❌ Example generation failed: {str(e)}"


@mcp.tool()
def create_interactive_example(concept_name: str, output_directory: str = None) -> str:
    """
    Create interactive example files that can be compiled and run
    
    Args:
        concept_name: Name of concept to create example for
        output_directory: Optional directory to create files in
    
    Returns:
        Path and instructions for the created interactive example
    """
    try:
        logger.info(f"Creating interactive example for: {concept_name}")
        
        result = example_generator.create_interactive_example(concept_name, output_directory)
        
        return result
        
    except Exception as e:
        logger.error(f"Interactive example creation failed: {e}")
        return f"❌ Interactive example creation failed: {str(e)}"


@mcp.tool()
def list_example_templates() -> str:
    """
    List all available example templates
    
    Returns:
        Available example templates and their descriptions
    """
    try:
        result = example_generator.list_available_examples()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list example templates: {e}")
        return f"❌ Failed to list templates: {str(e)}"


@mcp.tool()
def get_server_info() -> str:
    """
    Get information about this GOT/PLT analysis server
    
    Returns:
        Server capabilities and integration information
    """
    # Get concept statistics
    total_concepts = len(concept_validator.list_available_concepts())
    
    info = f"""
🔗 **GOT/PLT Educational Analysis Server - Phase 2**

**Server Information:**
- Name: {SERVER_INFO['name']}
- Port: {SERVER_INFO['port']}
- Framework: FastMCP
- Focus: {SERVER_INFO['focus']}
- Implementation: Phase 1 (Foundation) + Phase 2 (Educational Framework) ✅

**Phase 1 Tools (Binary Analysis):**
1. `inspect_got_table()` - Analyze Global Offset Table entries
2. `analyze_plt_stubs()` - Disassemble Procedure Linkage Table stubs  
3. `list_dynamic_symbols()` - List symbols requiring dynamic resolution
4. `explain_linking_process()` - Comprehensive linking walkthrough
5. `generate_minimal_example()` - Create demonstration code

**Phase 2 Tools (Concept Validation):**
6. `validate_concept()` - Test theory against real binary behavior
7. `list_available_concepts()` - Show all concepts available for validation
8. `find_related_concepts()` - Search concepts by keyword
9. `get_concept_info()` - Detailed concept information from knowledge base
10. `compare_theory_vs_practice()` - Side-by-side theory vs binary comparison
11. `create_interactive_example()` - Generate compilable example files
12. `list_example_templates()` - Show available example templates

**Phase 3 Tools (Runtime Analysis):**
13. `trace_symbol_resolution()` - Live trace of symbol resolution process
14. `analyze_lazy_binding()` - Analyze lazy binding behavior with performance comparison
15. `runtime_got_snapshot()` - Capture GOT state at execution points
16. `compare_binding_modes()` - Compare lazy vs immediate binding
17. `generate_lazy_binding_report()` - Comprehensive lazy binding analysis report
18. `analyze_plt_behavior()` - Analyze PLT behavior during execution

**Knowledge Base Integration:**
- **Concepts Loaded:** {total_concepts} from Linkers & Loaders book
- **Source:** `/outputs/linkers_loaders/` directory
- **Format:** Extracted atomic concepts with theory, examples, and metadata
- **Validation:** Real-time testing against ELF binaries

**Educational Levels:**
- **Beginner**: Simplified explanations with visual diagrams
- **Intermediate**: Technical details with proper terminology
- **Advanced**: Deep architectural analysis and optimization

**Supported Architectures:**
- x86-64 (Intel/AMD 64-bit) - Full support
- AArch64 (ARM 64-bit) - Partial support
- RISC-V 64-bit - Planned

**Integration:**
- Integrates with Master Orchestrator (port 8101)
- Routes dynamic linking questions automatically
- Validates concepts from existing knowledge extraction
- Bridges theory and practice with educational explanations

**Keywords for Routing:**
{', '.join(SERVER_INFO['keywords'])}

**Phase 2 Features:**
✅ Concept validation against real binaries
✅ Integration with existing concept database  
✅ Theory vs practice comparisons
✅ Educational error handling
✅ Searchable concept repository
✅ Detailed validation reports

**Phase 3 Features:**
✅ Runtime symbol resolution tracing
✅ Lazy binding behavior analysis
✅ Live GOT state snapshots
✅ Performance overhead measurement
✅ PLT interaction monitoring
✅ GDB-based dynamic analysis

**Runtime Analysis Capabilities:**
- Live symbol resolution tracing with educational explanations
- Lazy binding vs immediate binding comparisons
- Performance impact measurement (first call vs subsequent calls)
- GOT state changes during program execution
- PLT stub behavior analysis
- Educational runtime debugging scenarios

**Usage Examples:**
- `validate_concept("Global Offset Table")`
- `find_related_concepts("lazy binding")`
- `compare_theory_vs_practice("PLT", "/bin/ls")`
- `trace_symbol_resolution("/bin/ls", "printf")`
- `analyze_lazy_binding("/bin/cat", "malloc")`
- `runtime_got_snapshot("/bin/echo", "main")`

**Requirements:**
- **Phase 1:** pyelftools, capstone, objdump, readelf
- **Phase 2:** Existing concept database in `/outputs/linkers_loaders/`
- **Phase 3:** GDB installed, dynamically linked binaries, execution permissions
"""
    
    return info


# Server startup and integration
if __name__ == "__main__":
    logger.info("🔗 Starting GOT/PLT Educational Analysis Server")
    logger.info(f"📍 Port: {SERVER_INFO['port']}")
    logger.info(f"🎯 Focus: {SERVER_INFO['focus']}")
    logger.info(f"🔧 Available tools: {len([name for name in dir() if hasattr(globals()[name], '__call__') and name.startswith('mcp')])}")
    
    # Log supported features
    logger.info("📚 Educational levels: beginner, intermediate, advanced")
    logger.info("🏗️ Architectures: x86-64, AArch64 (partial), RISC-V (planned)")
    logger.info("🔍 Analysis types: static binary analysis, educational explanations")
    
    try:
        # Run the MCP server
        mcp.run()
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        logger.error(traceback.format_exc())
        raise
