#!/usr/bin/env python3
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback
import os
import functools

sys.path.append('.')

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("FastMCP not found. Please install: pip install fastmcp")

from analyzers.binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub, SymbolInfo
from educational.explainer import EducationalExplainer
from analyzers.assembly_analyzer import AssemblyAnalyzer
from utils.performance_estimator import PerformanceEstimator
from utils.ascii_visualizer import ASCIIVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("got-plt-mcp")

mcp = FastMCP("GOT/PLT Educational Analysis Server")
explainer = EducationalExplainer()

VALID_DETAIL_LEVELS = {"beginner", "intermediate", "advanced"}
DEFAULT_DETAIL_LEVEL = "intermediate"
VALID_CATEGORIES = {"imports", "exports", "all"}
DEFAULT_CATEGORY = "all"

SERVER_INFO = {
    "name": "GOT/PLT Dynamic Linking Analysis",
    "port": 8108,
    "focus": "Educational static analysis of Global Offset Table and Procedure Linkage Table",
    "keywords": [
        "got", "plt", "dynamic linking", "symbol resolution",
        "global offset table", "procedure linkage table",
        "shared libraries", "relocation", "binary analysis"
    ],
    "educational": True,
    "complexity_levels": ["beginner", "intermediate", "advanced"]
}

@functools.lru_cache(maxsize=32)
def get_analyzer(binary_path: str) -> BinaryAnalyzer:
    if not Path(binary_path).is_file():
        raise FileNotFoundError(f"Binary file not found: {binary_path}")
    return BinaryAnalyzer(binary_path)

@mcp.tool()
def inspect_got_table(binary_path: str, detail_level: str = "intermediate") -> str:
    try:
        logger.info(f"Analyzing GOT table in {binary_path} at {detail_level} level")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        analyzer = get_analyzer(binary_path)
        got_entries = analyzer.analyze_got_table()
        binary_info = analyzer.get_binary_info()
        
        return explainer.generate_got_explanation(
            got_entries=got_entries,
            binary_info=binary_info,
            detail_level=detail_level
        )
    except FileNotFoundError as e:
        logger.warning(f"GOT analysis failed for {binary_path}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"GOT analysis failed: {e}\n{traceback.format_exc()}")

        return f"❌ Analysis failed: {str(e)}"


@mcp.tool()
def assembly_analyzer(assembly_file: str, c_file: str, detail_level: str = "intermediate") -> str:
    """
    Analyze C-to-assembly correlation with performance metrics and visualizations
    
    Args:
        assembly_file: Path to .s assembly file  
        c_file: Path to .c source file
        detail_level: Analysis depth ("beginner", "intermediate", "advanced")
        
    Returns:
        Comprehensive analysis with performance metrics and ASCII visualizations
    """
    try:
        logger.info(f"Analyzing assembly correlation: {c_file} -> {assembly_file}")
        
        # Validate detail level
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        # Validate files exist
        if not os.path.exists(assembly_file):
            return f"❌ Error: Assembly file not found: {assembly_file}"
        
        if not os.path.exists(c_file):
            return f"❌ Error: C file not found: {c_file}"
        
        # Initialize analyzers
        analyzer = AssemblyAnalyzer()
        perf_estimator = PerformanceEstimator()
        visualizer = ASCIIVisualizer()
        
        # Perform main analysis
        analysis_result = analyzer.analyze_files(c_file, assembly_file)
        
        if not analysis_result['success']:
            return f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}"
        
        # Generate performance metrics
        function_performances = []
        for asm_func in analysis_result['asm_functions']:
            perf = perf_estimator.analyze_function_performance(
                asm_func.name, 
                asm_func.instructions
            )
            function_performances.append(perf)
        
        # Generate visualizations
        call_tree = visualizer.generate_function_call_tree(
            analysis_result['asm_functions']
        )
        
        data_flow = visualizer.generate_data_flow_diagram(
            analysis_result['asm_functions'],
            analysis_result['calling_convention'].__dict__ if analysis_result['calling_convention'] else {}
        )
        
        register_usage = visualizer.generate_register_usage_diagram(
            analysis_result['asm_functions']
        )
        
        # Build comprehensive result based on detail level
        result = _generate_assembly_analysis_report(
            analysis_result, 
            function_performances, 
            call_tree, 
            data_flow, 
            register_usage,
            detail_level
        )
        
        return result
        
    except FileNotFoundError as e:
        logger.warning(f"Assembly analysis failed for {c_file}/{assembly_file}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Assembly analysis failed: {e}\\n{traceback.format_exc()}")
        return f"❌ Analysis failed: {str(e)}"

def _generate_assembly_analysis_report(analysis_result, performances, call_tree, data_flow, register_usage, detail_level):
    """Generate comprehensive assembly analysis report"""
    
    # Performance table
    perf_estimator = PerformanceEstimator()
    performance_table = perf_estimator.generate_performance_table(performances)
    
    # Header based on detail level
    if detail_level == "beginner":
        result = "🔍 **Assembly Analysis - Beginner Guide**\\n\\n"
        result += "This analysis shows how your C code translates to assembly instructions.\\n\\n"
    elif detail_level == "advanced":
        result = "🔍 **Advanced Assembly Analysis & Optimization Report**\\n\\n"
        result += "Deep technical analysis with performance optimization opportunities.\\n\\n"
    else:
        result = "🔍 **Assembly Analysis Report**\\n\\n"
        result += "Comprehensive C-to-assembly correlation with performance insights.\\n\\n"
    
    # File information
    result += f"**📁 Files Analyzed:**\\n"
    result += f"- C Source: `{analysis_result['files']['c_file']}`\\n"
    result += f"- Assembly: `{analysis_result['files']['assembly_file']}`\\n"
    result += f"- Architecture: {analysis_result['architecture']}\\n\\n"
    
    # Function mapping
    result += "**🔗 C-to-Assembly Function Mapping:**\\n"
    c_functions = analysis_result['c_functions']
    asm_functions = analysis_result['asm_functions']
    
    for c_func in c_functions:
        asm_func = next((af for af in asm_functions if af.name == c_func.name), None)
        if asm_func:
            result += f"- **{c_func.name}()** (C lines {c_func.line_start}-{c_func.line_end}) "
            result += f"→ {len(asm_func.instructions)} assembly instructions\\n"
            
            if detail_level == "advanced" and c_func.function_calls:
                result += f"  - Calls: {', '.join(c_func.function_calls)}\\n"
        else:
            result += f"- **{c_func.name}()** → ⚠️ Not found in assembly\\n"
    
    result += "\\n"
    
    # Performance metrics
    result += performance_table
    result += "\\n"
    
    # Calling convention analysis
    calling_conv = analysis_result['calling_convention']
    if calling_conv:
        result += "**📋 Calling Convention Analysis:**\\n"
        result += f"- Convention: {calling_conv.convention.value}\\n"
        result += f"- Parameter Registers: {', '.join(calling_conv.parameter_registers[:4])}\\n"
        result += f"- Return Register: {calling_conv.return_register}\\n"
        
        if detail_level == "advanced":
            result += f"- Callee-Saved: {', '.join(calling_conv.callee_saved[:4])}\\n"
            result += f"- Caller-Saved: {', '.join(calling_conv.caller_saved[:4])}\\n"
        
        if calling_conv.violations:
            result += f"- ⚠️ Violations: {len(calling_conv.violations)} detected\\n"
        
        result += "\\n"
    
    # Show detailed performance breakdown for complex functions
    if detail_level == "advanced" and performances:
        complex_funcs = [p for p in performances if p.complexity.value in ["High", "Very High"]]
        if complex_funcs:
            result += "**🔍 Detailed Performance Analysis:**\\n"
            for perf in complex_funcs[:2]:  # Limit to 2 most complex
                detailed = perf_estimator.generate_detailed_breakdown(perf)
                result += detailed + "\\n"
    
    # Visualizations
    if detail_level != "beginner":  # Skip complex visuals for beginners
        result += call_tree + "\\n"
        result += data_flow + "\\n"
    
    if detail_level == "advanced":
        result += register_usage + "\\n"
    
    # Educational explanations based on correlations
    correlations = analysis_result.get('correlations', [])
    if correlations and detail_level in ["intermediate", "advanced"]:
        result += "**📚 C-to-Assembly Correlations:**\\n"
        for i, corr in enumerate(correlations[:3]):  # Show first 3
            result += f"{i+1}. **{corr.c_construct}** (Line {corr.c_line})\\n"
            result += f"   → {corr.explanation}\\n"
            if corr.asm_instructions:
                result += f"   → Assembly: `{corr.asm_instructions[0]}`\\n"
            result += "\\n"
    
    # Summary and recommendations
    result += "**💡 Summary & Recommendations:**\\n"
    
    total_instructions = sum(len(af.instructions) for af in asm_functions)
    total_cycles = sum(p.estimated_cycles for p in performances)
    
    result += f"- Total Assembly Instructions: {total_instructions}\\n"
    result += f"- Estimated Total Cycles: ~{total_cycles}\\n"
    
    # Generate recommendations based on analysis
    if any(p.complexity.value in ["High", "Very High"] for p in performances):
        result += "- ⚠️ Complex functions detected - consider optimization\\n"
    
    if total_instructions > 100:
        result += "- 📈 Large codebase - consider profiling hot paths\\n"
    
    # Beginner-friendly tips
    if detail_level == "beginner":
        result += "\\n**🎓 Learning Tips:**\\n"
        result += "- Each C statement typically becomes multiple assembly instructions\\n"
        result += "- Function calls have overhead (saving registers, jumping)\\n"
        result += "- Compilers optimize your code automatically\\n"
        result += "- Use `-O2` or `-O3` flags for optimized assembly\\n"
    
    return result

@mcp.tool()
def trace_plt_ant_trail(binary_path: str, symbol_name: str, detail_level: str = "intermediate") -> str:
    """
    Trace the PLT 'ant trail' for a specific symbol - shows the discovery vs optimized paths
    """
    try:
        logger.info(f"Tracing PLT ant trail for {symbol_name} in {binary_path}")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        analyzer = get_analyzer(binary_path)
        plt_stubs = analyzer.analyze_plt_stubs()
        binary_info = analyzer.get_binary_info()
        
        # Find the target stub - try exact match first, then partial match
        target_stub = None
        for stub in plt_stubs:
            if stub.symbol_name == symbol_name:
                target_stub = stub
                break
            # Try partial match (handles versioned symbols like printf@GLIBC_2.2.5)
            elif symbol_name in stub.symbol_name or stub.symbol_name in symbol_name:
                target_stub = stub
                break
        
        if not target_stub:
            # List available symbols for user reference
            available_symbols = [stub.symbol_name for stub in plt_stubs if stub.symbol_name]
            
            # Try to find similar symbols
            similar = [s for s in available_symbols if symbol_name.lower() in s.lower() or s.lower() in symbol_name.lower()]
            
            result = f"❌ Symbol '{symbol_name}' not found in PLT.\n\n"
            
            if similar:
                result += f"🔍 **Similar symbols found:**\n"
                for sym in similar:
                    result += f"- {sym}\n"
                result += f"\n💡 Try: `trace_plt_ant_trail(\"{binary_path}\", \"{similar[0]}\", \"{detail_level}\")`\n\n"
            
            if available_symbols:
                result += f"🐜 Available ant trails: {', '.join(available_symbols[:5])}"
                if len(available_symbols) > 5:
                    result += f" (+{len(available_symbols)-5} more)"
            else:
                result += "🐜 No PLT symbols found - this binary may not use dynamic linking"
            
            return result
        
        # Generate the ant trail analysis
        result = f"🐜 **PLT Ant Trail Analysis: {target_stub.symbol_name}**\n\n"
        
        # Rest of the existing trace logic...
        if target_stub.disassembly:
            result += "**🔍 PLT Stub Disassembly:**\n"
            for instruction in target_stub.disassembly:
                result += f"   {instruction}\n"
            
            result += f"""
**🐜 Trail Explanation:**
1. jmp *GOT[{target_stub.symbol_name}] → Initially points to PLT+6
2. push $reloc_index → Identifies which symbol to resolve  
3. jmp PLT[0] → Calls _dl_runtime_resolve
4. Resolver searches symbol tables in dependency order
5. Updates GOT[{target_stub.symbol_name}] = resolved_address
6. Transfers control to resolved function

**🏃 Optimized Path Analysis:**
After resolution, the same jmp *GOT[{target_stub.symbol_name}] becomes a direct jump.
The push/jmp instructions become dead code - never executed again.

**🏗️ Architecture Details:**
- GOT Entry: {target_stub.got_reference}
- PLT Address: {target_stub.address}
- Stub Index: {target_stub.stub_index}
"""

        # Add educational insights
        result += f"""
**🎓 Educational Insights:**
- The "ant trail" metaphor helps visualize why the first call is slow
- PLT/GOT work together: PLT provides the code, GOT stores the data
- This lazy binding saves startup time but costs on first use
- Modern security (ASLR) makes this mechanism essential
"""

        return result
        
    except FileNotFoundError as e:
        logger.warning(f"Ant trail analysis failed for {binary_path}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Ant trail analysis failed: {e}\n{traceback.format_exc()}")
        return f"❌ Analysis failed: {str(e)}"

@mcp.tool()
def analyze_plt_stubs(binary_path: str, symbol_filter: str = None, detail_level: str = "intermediate") -> str:
    try:
        logger.info(f"Analyzing PLT stubs in {binary_path}")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        analyzer = get_analyzer(binary_path)
        plt_stubs = analyzer.analyze_plt_stubs()
        binary_info = analyzer.get_binary_info()
        
        if symbol_filter:
            plt_stubs = [stub for stub in plt_stubs if symbol_filter.lower() in stub.symbol_name.lower()]
        
        return explainer.generate_plt_explanation(
            plt_stubs=plt_stubs,
            binary_info=binary_info,
            detail_level=detail_level,
            symbol_filter=symbol_filter
        )
    except FileNotFoundError as e:
        logger.warning(f"PLT analysis failed for {binary_path}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"PLT analysis failed: {e}\n{traceback.format_exc()}")
        return f"❌ Analysis failed: {str(e)}"

@mcp.tool()
def list_dynamic_symbols(binary_path: str, category: str = "all", detail_level: str = "intermediate") -> str:
    try:
        logger.info(f"Listing dynamic symbols in {binary_path}, category: {category}")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        if category not in VALID_CATEGORIES:
            category = DEFAULT_CATEGORY
        
        analyzer = get_analyzer(binary_path)
        symbols = analyzer.list_dynamic_symbols(category)
        binary_info = analyzer.get_binary_info()
        
        return explainer.generate_symbols_explanation(
            symbols=symbols,
            binary_info=binary_info,
            detail_level=detail_level,
            category=category
        )
    except FileNotFoundError as e:
        logger.warning(f"Symbol analysis failed for {binary_path}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Symbol analysis failed: {e}\n{traceback.format_exc()}")
        return f"❌ Analysis failed: {str(e)}"

@mcp.tool()
def explain_linking_process(binary_path: str, detail_level: str = "intermediate") -> str:
    try:
        logger.info(f"Explaining linking process for {binary_path}")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        analyzer = get_analyzer(binary_path)
        got_entries = analyzer.analyze_got_table()
        plt_stubs = analyzer.analyze_plt_stubs()
        symbols = analyzer.list_dynamic_symbols()
        binary_info = analyzer.get_binary_info()
        
        return explainer.generate_linking_walkthrough(
            got_entries=got_entries,
            plt_stubs=plt_stubs,
            symbols=symbols,
            binary_info=binary_info,
            detail_level=detail_level
        )
    except FileNotFoundError as e:
        logger.warning(f"Linking explanation failed for {binary_path}: {e}")
        return f"❌ Error: {e}"
    except Exception as e:
        logger.error(f"Linking explanation failed: {e}\n{traceback.format_exc()}")
        return f"❌ Analysis failed: {str(e)}"

@mcp.tool()
def get_server_info() -> str:
    return f"""
🔗 **GOT/PLT Educational Analysis Server - Clean Version**

**Server Information:**
- Name: {SERVER_INFO['name']}
- Port: {SERVER_INFO['port']}
- Framework: FastMCP
- Focus: {SERVER_INFO['focus']}
- Implementation: Phase 1 (Static Analysis) - Reliable Tools Only ✅

**Available Tools (5 Working Tools):**
1. `inspect_got_table()` - Analyze Global Offset Table entries
2. `analyze_plt_stubs()` - Disassemble Procedure Linkage Table stubs
3. `list_dynamic_symbols()` - List symbols requiring dynamic resolution
4. `explain_linking_process()` - Comprehensive linking walkthrough
5. `trace_plt_ant_trail()` - Follow the "ant trail" for symbol resolution
6. `assembly_analyzer()` - C-to-assembly correlation with performance metrics

** Assembly Analyzer Features:**
- 📊 Performance metrics with cycle estimation
- 🌳 ASCII function call trees
- 🔄 Data flow diagrams
- 📋 Calling convention analysis
- 💡 Optimization suggestions

**Educational Levels:**
- **Beginner**: Simplified explanations with visual diagrams
- **Intermediate**: Technical details with proper terminology
- **Advanced**: Deep architectural analysis and optimization

**Supported Architectures:**
- x86-64 (Intel/AMD 64-bit) - Full support
- AArch64 (ARM 64-bit) - Partial support
- RISC-V 64-bit - Basic support

**Integration:**
- Integrates with Master Orchestrator (port 8101)
- Routes dynamic linking questions automatically
- Provides reliable static binary analysis
- Educational explanations at multiple complexity levels

**Keywords for Routing:**
{', '.join(SERVER_INFO['keywords'])}

**Usage Examples:**
- `inspect_got_table("/bin/ls", "intermediate")`
- `analyze_plt_stubs("./my_program", None, "beginner")`
- `list_dynamic_symbols("/usr/bin/gcc", "imports", "advanced")`
- `explain_linking_process("./test_binary", "intermediate")`

**Requirements:**
- Python 3.8+
- pyelftools library
- capstone library
- objdump (binutils)
- readelf (binutils)

**Note:** This is the clean, reliable version with only proven static analysis tools.
Complex runtime analysis and concept validation features have been removed for stability.
"""

if __name__ == "__main__":
    logger.info("🔗 Starting GOT/PLT Educational Analysis Server (Clean Version)")
    logger.info(f"📍 Port: {SERVER_INFO['port']}")
    logger.info(f"🎯 Focus: {SERVER_INFO['focus']}")
    logger.info("🛠️ Available tools: 5 reliable static analysis tools")
    logger.info("📚 Educational levels: beginner, intermediate, advanced")
    logger.info("🏗️ Architectures: x86-64 (full), AArch64 (partial), RISC-V (basic)")
    logger.info("🔍 Analysis types: GOT, PLT, dynamic symbols, linking process")
    
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Server startup failed: {e}\n{traceback.format_exc()}")
        raise
