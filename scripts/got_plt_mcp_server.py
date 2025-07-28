#!/usr/bin/env python3
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback
import functools

sys.path.append('.')

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("FastMCP not found. Please install: pip install fastmcp")

from analyzers.binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub, SymbolInfo
from educational.explainer import EducationalExplainer

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
def trace_plt_ant_trail(binary_path: str, symbol_name: str, detail_level: str = "intermediate") -> str:
    """
    Trace the PLT 'ant trail' for a specific symbol - shows the discovery vs optimized paths
    
    Args:
        binary_path: Path to ELF binary to analyze
        symbol_name: Symbol to trace the ant trail for (e.g., 'printf')
        detail_level: Explanation complexity ("beginner", "intermediate", "advanced")
    
    Returns:
        Step-by-step ant trail narrative explaining lazy binding for this symbol
    """
    try:
        logger.info(f"Tracing ant trail for {symbol_name} in {binary_path}")
        
        if detail_level not in VALID_DETAIL_LEVELS:
            detail_level = DEFAULT_DETAIL_LEVEL
        
        analyzer = get_analyzer(binary_path)
        plt_stubs = analyzer.analyze_plt_stubs()
        binary_info = analyzer.get_binary_info()
        
        # Find the specific PLT stub for this symbol
        target_stub = None
        for stub in plt_stubs:
            if symbol_name.lower() in stub.symbol_name.lower():
                target_stub = stub
                break
        
        if not target_stub:
            available_symbols = [stub.symbol_name for stub in plt_stubs if stub.symbol_name != "unknown"]
            if available_symbols:
                return f"❌ Symbol '{symbol_name}' not found in PLT.\n\n🐜 Available ant trails: {', '.join(available_symbols[:10])}"
            else:
                return f"❌ No recognizable symbols found in PLT. Binary may be stripped or statically linked."
        
        # Generate the ant trail story
        result = f"""🐜 **Ant Trail Analysis: {symbol_name}**

**Binary:** {binary_path}
**PLT Entry:** {target_stub.address}
**GOT Reference:** {target_stub.got_reference}

"""
        
        if detail_level == "beginner":
            result += f"""📖 **The Ant Trail Story:**

🐜 **First Call (Discovery Journey):**
1. First ant reaches the trail marker at {target_stub.address}
2. Trail marker says "Go ask the scout!" (jumps to resolver)
3. Scout ant searches through all the libraries to find {symbol_name}
4. Scout finds {symbol_name} and writes the direct path in the trail guide
5. First ant finally reaches {symbol_name} and completes its task

🐜 **All Future Calls (Following the Trail):**
1. Ant reaches the same trail marker at {target_stub.address}
2. Trail guide now has the direct path written down
3. Ant jumps directly to {symbol_name} - no scout needed!
4. Much faster journey for all future ants

💡 **Why This Matters:**
The first ant does extra work so all future ants can be lazy!
"""

        elif detail_level == "intermediate":
            result += f"""📖 **The Ant Trail Process:**

🐜 **First Call - Discovery Phase:**
1. CPU calls {symbol_name}@plt ({target_stub.address})
2. PLT stub jumps to GOT entry (initially points back to PLT+6)
3. PLT pushes relocation index and jumps to PLT[0] (resolver)
4. Dynamic linker (_dl_runtime_resolve) searches for {symbol_name}
5. Linker updates GOT entry with real {symbol_name} address
6. Linker jumps to the resolved function

🐜 **Subsequent Calls - Optimized Trail:**
1. CPU calls {symbol_name}@plt ({target_stub.address})
2. PLT stub jumps to GOT entry (now contains real address)
3. Direct jump to {symbol_name} - no resolver overhead

⚡ **Performance Impact:**
- First call: ~100-1000x slower (symbol resolution)
- Later calls: Nearly identical to direct call
"""

        else:  # advanced
            result += f"""📖 **Detailed Ant Trail Architecture:**

🐜 **First Call - Resolution Mechanics:**
PLT Stub Instructions:
"""
            for i, instruction in enumerate(target_stub.disassembly[:3]):
                result += f"  {i+1}. {instruction}\n"
            
            result += f"""
Resolution Flow:
1. jmp *GOT[{symbol_name}] → Initially points to PLT+6
2. push $reloc_index → Identifies which symbol to resolve  
3. jmp PLT[0] → Calls _dl_runtime_resolve
4. Resolver searches symbol tables in dependency order
5. Updates GOT[{symbol_name}] = resolved_address
6. Transfers control to resolved function

🐜 **Optimized Path Analysis:**
After resolution, the same jmp *GOT[{symbol_name}] becomes a direct jump.
The push/jmp instructions become dead code - never executed again.

🏗️ **Architecture Details:**
- GOT Entry: {target_stub.got_reference}
- Relocation Type: R_X86_64_JUMP_SLOT (typical)
- Binding: {"Lazy" if not binary_info.get('immediate_binding', False) else "Immediate"}
"""

        # Add educational insights
        result += f"""
🎓 **Educational Insights:**
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
        
        return explainer.generate_symbol_explanation(
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
