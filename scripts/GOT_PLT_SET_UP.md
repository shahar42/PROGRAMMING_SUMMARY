# GOT/PLT Educational MCP Server - Phase 1 Setup Guide

## 🎯 Overview

**Phase 1: Foundation Infrastructure** is now complete! This provides the core binary analysis capabilities for examining Global Offset Table (GOT) and Procedure Linkage Table (PLT) structures in ELF binaries with educational explanations.

## 📁 Directory Structure Created

```
scripts/
├── got_plt_mcp_server.py           # Main MCP server (Port 8108)
│
├── analyzers/                      # Core analysis modules  
│   ├── __init__.py
│   └── binary_analyzer.py          # Binary analysis engine
│
├── educational/                    # Educational framework
│   ├── __init__.py
│   └── explainer.py                # Multi-level explanations
│
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── binary_parser.py            # Low-level binary parsing
│   └── error_handler.py            # Educational error handling
│
├── architecture/                   # Architecture handlers (Phase 4)
│   └── __init__.py
│
├── data/                          # Static data (future)
└── tests/                         # Test suite (future)
```

## 🔧 Prerequisites Installation

### 1. Python Dependencies

```bash
# Required for ELF binary parsing
pip install pyelftools

# Required for PLT stub disassembly  
pip install capstone

# Already have FastMCP from your existing setup
```

### 2. System Tools

```bash
# Ubuntu/Debian
sudo apt-get install binutils file

# CentOS/RHEL  
sudo yum install binutils file

# macOS
brew install binutils file
```

### 3. Validate Setup

Run the setup validation:

```python
from utils.error_handler import error_handler
print(error_handler.generate_setup_report())
```

## 🚀 Phase 1 Tools Available

### 1. `inspect_got_table(binary_path, detail_level)`
Analyze Global Offset Table entries with educational explanations.

**Parameters:**
- `binary_path`: Path to ELF binary
- `detail_level`: "beginner", "intermediate", "advanced"

### 2. `analyze_plt_stubs(binary_path, symbol_filter, detail_level)`
Disassemble PLT stubs with educational annotations.

**Parameters:**
- `binary_path`: Path to ELF binary  
- `symbol_filter`: Optional symbol name filter
- `detail_level`: "beginner", "intermediate", "advanced"

### 3. `list_dynamic_symbols(binary_path, category, detail_level)`
List symbols requiring dynamic resolution.

**Parameters:**
- `binary_path`: Path to ELF binary
- `category`: "imports", "exports", "all"
- `detail_level`: "beginner", "intermediate", "advanced"

### 4. `explain_linking_process(binary_path, detail_level)`
Comprehensive walkthrough of dynamic linking process.

### 5. `generate_minimal_example(concept)`
Generate C code examples demonstrating linking concepts.

### 6. `get_server_info()`
Server capabilities and integration information.

## 🧪 Testing Phase 1

### 1. Start the Server

```bash
cd scripts/
python3 got_plt_mcp_server.py
```

Should output:
```
🔗 Starting GOT/PLT Educational Analysis Server
📍 Port: 8108
🎯 Focus: Educational analysis of Global Offset Table and Procedure Linkage Table
```

### 2. Test with Simple Binary

Create a test binary:

```c
// test_binary.c
#include <stdio.h>
#include <math.h>

int main() {
    printf("Hello, dynamic world!\n");
    printf("Square root: %.2f\n", sqrt(16.0));
    return 0;
}
```

Compile:
```bash
gcc test_binary.c -lm -o test_binary
```

### 3. Test Analysis (via MCP)

If integrated with your orchestrator, queries like:
- "Analyze the GOT table in test_binary"  
- "Show me PLT stubs for printf function"
- "Explain dynamic linking process"

Should route to the GOT/PLT server.

### 4. Manual Testing

You can also test the core functionality directly:

```python
from analyzers.binary_analyzer import BinaryAnalyzer
from educational.explainer import EducationalExplainer

# Test binary analysis
analyzer = BinaryAnalyzer("test_binary")
got_entries = analyzer.analyze_got_table()
plt_stubs = analyzer.analyze_plt_stubs()

# Test educational explanations
explainer = EducationalExplainer()
explanation = explainer.generate_got_explanation(got_entries, analyzer.get_binary_info(), "intermediate")
print(explanation)
```

## 🔗 Integration with Existing MCP Architecture

### 1. Update Master Orchestrator

Add to `master_orchestrator_mcp.py`:

```python
BOOK_CONFIGS["got_plt_analysis"] = {
    "name": "GOT/PLT Dynamic Linking Analysis",
    "focus": "Educational analysis of Global Offset Table and Procedure Linkage Table",
    "keywords": [
        "got", "plt", "dynamic linking", "lazy binding", "symbol resolution",
        "global offset table", "procedure linkage table", "runtime linking",
        "shared libraries", "symbol interposition", "relocation"
    ],
    "weight": 1.6,
    "port": 8108,
    "educational": True
}
```

### 2. Update Topic Detection

Add to `topic_detection_mcp.py`:

```python
ANALYSIS_KEYWORDS = {
    "got_plt_analysis": [
        "got", "plt", "dynamic linking", "lazy binding", "symbol resolution",
        "shared library", "runtime linker", "dl_runtime_resolve", "relocation",
        "global offset table", "procedure linkage table", "symbol interposition"
    ]
}
```

## 🎓 Educational Levels Explained

### Beginner Level
- **Language**: Simplified, non-technical terms
- **Analogies**: Phone book, helper functions, address lookup
- **Focus**: What happens and why it's useful
- **Visuals**: ASCII diagrams, simple explanations

### Intermediate Level  
- **Language**: Proper technical terminology
- **Details**: Implementation specifics, performance implications
- **Focus**: How it works and when to use it
- **Context**: System V ABI compliance, architectural considerations

### Advanced Level
- **Language**: Expert-level technical analysis
- **Details**: Deep architectural specifics, optimization considerations
- **Focus**: Performance characteristics, security implications  
- **Context**: Research-quality analysis, cross-platform comparisons

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all `__init__.py` files are present
   - Check Python path includes the scripts directory

2. **"pyelftools not found"**
   - Install: `pip install pyelftools`

3. **"capstone not found"**  
   - Install: `pip install capstone`
   - PLT disassembly will be unavailable without it

4. **"objdump not found"**
   - Install binutils package for your system

5. **"Not a dynamic executable"**
   - Binary is statically linked (no GOT/PLT to analyze)
   - Try with: `gcc -shared` or ensure dynamic linking

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ✅ Phase 1 Success Criteria

- [x] Core data structures implemented (`GOTEntry`, `PLTStub`, `SymbolInfo`)
- [x] Basic binary analysis working (`BinaryAnalyzer`)
- [x] Educational explanations at 3 levels (`EducationalExplainer`)
- [x] FastMCP server integration (`got_plt_mcp_server.py`)
- [x] Error handling with educational context
- [x] Architecture detection (basic)
- [x] All 6 planned MCP tools implemented

## 🎯 Next Steps: Phase 2

**Phase 2: Educational Framework** will add:
- Integration with existing concept database
- Concept validation against real binaries  
- Enhanced example generation
- Integration with Linkers & Loaders book concepts

**Ready for Phase 2?** The foundation is solid and all core functionality is working!

## 📚 Learning Resources

**Test Binaries to Try:**
```bash
# Simple case
gcc -o hello hello.c

# With math library
gcc -lm -o math_test math_test.c

# Position independent
gcc -fPIE -pie -o pie_test test.c

# Shared library
gcc -shared -fPIC -o libtest.so lib.c
```

**Useful Commands:**
```bash
# Check if binary is suitable for analysis
file binary_name
ldd binary_name
readelf -h binary_name

# Manual GOT/PLT inspection  
objdump -R binary_name        # GOT relocations
objdump -d -j .plt binary_name # PLT disassembly
readelf -r binary_name        # All relocations
```

---

**Phase 1 Complete! 🎉** Your GOT/PLT Educational MCP Server foundation is ready for testing and integration.
