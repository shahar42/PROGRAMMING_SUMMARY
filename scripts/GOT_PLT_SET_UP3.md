# GOT/PLT Educational MCP Server - Phase 3 Setup Guide

## 🎯 Phase 3 Overview: Runtime Analysis

**Phase 3** adds sophisticated runtime analysis capabilities using GDB integration. This phase bridges the gap between static analysis and dynamic behavior, showing how lazy binding and symbol resolution actually work during program execution.

## 🆕 New Capabilities Added

### **1. Live Symbol Resolution Tracing**
- **Real-time tracing** - Observe symbol resolution as it happens
- **Step-by-step breakdown** - See each phase of the resolution process
- **Educational annotations** - Explanations of what each step means
- **Performance measurement** - Measure resolution overhead

### **2. Lazy Binding Analysis**
- **First call vs subsequent calls** - Compare performance and behavior
- **GOT state tracking** - Watch GOT entries change during resolution
- **Resolution confirmation** - Verify lazy binding is actually happening
- **Educational insights** - Theory validation against practice

### **3. Runtime GOT Snapshots**
- **Execution point snapshots** - Capture GOT state at any program point
- **Memory layout analysis** - Show register states and memory organization
- **Resolution statistics** - Track how many symbols are resolved
- **Educational context** - Explain what the snapshot reveals

### **4. Dynamic PLT Behavior**
- **PLT interaction monitoring** - Track all PLT stub executions
- **Call pattern analysis** - Understand how PLT stubs are used
- **Multi-symbol analysis** - Compare behavior across different symbols
- **Performance impact** - Measure PLT overhead in real programs

## 📁 Files Added in Phase 3

```
scripts/
├── utils/
│   └── gdb_interface.py             # NEW: GDB integration wrapper
│
├── analyzers/
│   ├── runtime_analyzer.py         # NEW: Runtime analysis engine
│   └── lazy_binding_analyzer.py    # NEW: Specialized lazy binding analysis
│
├── got_plt_mcp_server.py (updated)  # Updated with 6 new runtime tools
└── analyzers/__init__.py (updated)  # Updated imports
```

## 🛠️ Phase 3 Prerequisites

### **1. GDB Installation**

```bash
# Ubuntu/Debian
sudo apt-get install gdb

# CentOS/RHEL  
sudo yum install gdb

# Fedora
sudo dnf install gdb

# macOS
brew install gdb
# Note: macOS may require additional setup for code signing
```

### **2. Verify GDB Installation**

```bash
gdb --version
# Should show GDB version information
```

### **3. Test Permissions**

```bash
# Create simple test program
echo 'int main(){return 0;}' > test.c
gcc test.c -o test

# Test GDB can attach
gdb -batch -ex "run" -ex "quit" ./test
# Should run without permission errors
```

## 🚀 Phase 3 Tools Added

### **New Runtime Analysis MCP Tools:**

1. **`trace_symbol_resolution(binary_path, symbol_name)`**
   - Live trace of symbol resolution process
   - Shows step-by-step resolution with educational explanations
   - Measures total resolution time and resolver calls

2. **`analyze_lazy_binding(binary_path, symbol_name)`**
   - Analyzes lazy binding behavior for specific symbol
   - Compares first call vs subsequent calls
   - Shows GOT state changes and performance impact

3. **`runtime_got_snapshot(binary_path, execution_point="main")`**
   - Captures GOT state at specific execution point
   - Shows memory layout and register states
   - Provides statistics on resolved vs unresolved symbols

4. **`compare_binding_modes(binary_path, symbols="printf,malloc,free")`**
   - Compares lazy vs immediate binding behavior
   - Analyzes multiple symbols simultaneously
   - Provides educational comparison and recommendations

5. **`generate_lazy_binding_report(binary_path, symbols="printf,malloc,strlen")`**
   - Generates comprehensive analysis report
   - Includes performance metrics and educational insights
   - Professional-quality documentation of lazy binding behavior

6. **`analyze_plt_behavior(binary_path, symbols="printf,malloc,free")`**
   - Monitors PLT interactions during execution
   - Tracks call patterns and GOT value changes
   - Provides detailed PLT behavior analysis

## 🧪 Testing Phase 3

### **1. Verify Runtime Analysis Setup**

Start the server and check for Phase 3 capabilities:

```bash
cd scripts/
python3 got_plt_mcp_server.py
```

Look for log messages indicating Phase 3 is loaded:
```
Starting GOT/PLT Educational Analysis Server - Phase 3
Runtime analysis capabilities enabled
GDB interface initialized
```

### **2. Test Basic Runtime Analysis**

Create a simple test program:

```c
// runtime_test.c
#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("Testing lazy binding...\n");
    void *ptr = malloc(100);
    free(ptr);
    printf("Done!\n");
    return 0;
}
```

Compile:
```bash
gcc runtime_test.c -o runtime_test
```

### **3. Test Runtime Tools (via MCP)**

Try these queries through your MCP client:

```
"Trace symbol resolution for printf in runtime_test"
"Analyze lazy binding for malloc in runtime_test" 
"Take a GOT snapshot at main in runtime_test"
"Compare binding modes for printf,malloc,free in runtime_test"
```

### **4. Manual Testing**

You can also test Phase 3 components directly:

```python
from analyzers.runtime_analyzer import RuntimeAnalyzer
from analyzers.lazy_binding_analyzer import LazyBindingAnalyzer
from utils.gdb_interface import GDBInterface

# Test GDB interface
try:
    with GDBInterface("runtime_test") as gdb:
        gdb.run_program()
        print("✅ GDB interface working")
except Exception as e:
    print(f"❌ GDB interface failed: {e}")

# Test runtime analyzer
analyzer = RuntimeAnalyzer("runtime_test")
trace = analyzer.trace_symbol_resolution("printf")
print(f"Resolution successful: {trace.successful}")

# Test lazy binding analyzer
lazy_analyzer = LazyBindingAnalyzer("runtime_test")
analysis = lazy_analyzer.analyze_first_call_behavior("printf")
print(f"First call detected: {analysis['first_call_detected']}")
```

## 🔗 Integration with Existing Architecture

### **Seamless Integration**
- **No orchestrator changes needed** - Runtime analysis queries automatically route to GOT/PLT server
- **Compatible with Phase 1 & 2** - All existing functionality preserved
- **Educational consistency** - Same multi-level explanations (beginner/intermediate/advanced)

### **Query Examples That Now Work**
- "How does lazy binding work in practice with /bin/ls?"
- "Show me the GOT state when printf is first called"
- "Trace the symbol resolution process for malloc"
- "Compare the performance of first vs subsequent calls"

## 📊 Phase 3 Success Metrics

### **Runtime Analysis Capabilities**
- [x] GDB integration for dynamic analysis
- [x] Live symbol resolution tracing
- [x] Lazy binding behavior confirmation
- [x] Performance overhead measurement
- [x] GOT state monitoring during execution
- [x] PLT interaction tracking

### **Educational Features**
- [x] Step-by-step resolution explanations
- [x] Theory validation against runtime behavior
- [x] Performance impact analysis
- [x] Multi-symbol comparative analysis
- [x] Professional analysis reports

### **Practical Capabilities**
- [x] Real program analysis (not just toy examples)
- [x] Multiple architecture support
- [x] Educational error handling for runtime failures
- [x] Safe GDB process management

## 🎓 Educational Impact

### **Before Phase 3:**
- Static analysis showing potential behavior
- Theoretical explanations of lazy binding
- Examples demonstrating concepts

### **After Phase 3:**
- **Live observation** of dynamic linking in action
- **Performance measurement** of lazy binding overhead
- **Theory validation** - see if concepts match reality
- **Runtime debugging** - educational GDB scenarios
- **Real-world analysis** - analyze actual programs like /bin/ls

## 🚀 Advanced Usage Scenarios

### **Scenario 1: Understanding Lazy Binding Performance**
```
1. analyze_lazy_binding("/bin/ls", "printf")
   → Shows first call resolution overhead

2. runtime_got_snapshot("/bin/ls", "main")  
   → Captures initial GOT state

3. trace_symbol_resolution("/bin/ls", "printf")
   → Step-by-step resolution process

4. generate_lazy_binding_report("/bin/ls", "printf,malloc,strlen")
   → Comprehensive performance analysis
```

### **Scenario 2: Comparing Different Programs**
```
1. compare_binding_modes("/bin/ls", "printf,malloc,free")
   → Analyze system utility

2. compare_binding_modes("./my_program", "printf,malloc,free")  
   → Compare with your own program

3. Educational comparison of binding behaviors
```

### **Scenario 3: Debugging Linking Issues**
```
1. trace_symbol_resolution("problem_binary", "problematic_symbol")
   → See exactly what happens during resolution

2. runtime_got_snapshot("problem_binary", "crash_point")
   → Examine GOT state at crash

3. Identify if symbol resolution is the issue
```

## 🐛 Troubleshooting Phase 3

### **"GDB not available" errors**
- **Install GDB**: Follow installation instructions above
- **Check PATH**: Ensure `gdb` command is accessible
- **Test manually**: Run `gdb --version` to verify installation

### **"Permission denied" when debugging**
- **Linux**: May need to set `ptrace_scope`: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope`
- **macOS**: GDB may need code signing, consider LLDB alternative
- **User permissions**: Ensure user can debug processes

### **"Breakpoint not set" warnings**
- **Check binary format**: Use `file binary_name` to verify ELF format
- **Debug symbols**: While not required, debug symbols improve analysis
- **Dynamic linking**: Static binaries cannot use runtime analysis

### **Analysis timeouts**
- **Complex programs**: Large programs may take longer to analyze
- **Increase timeout**: Modify timeout parameters in GDBInterface
- **Simplify analysis**: Use fewer symbols or simpler test programs

### **"Symbol not found" in tracing**
- **Check symbol exists**: Use `nm -D binary_name | grep symbol`
- **Try common symbols**: printf, malloc, free are usually available
- **Check dynamic linking**: Use `ldd binary_name` to verify

## 🔧 Performance Optimization

### **For Better Analysis Performance:**

1. **Use simple test programs** when learning
2. **Limit symbol count** in multi-symbol analysis
3. **Set appropriate timeouts** for complex binaries
4. **Clean up GDB processes** between analyses

### **Recommended Test Programs:**

```c
// Simple lazy binding test
#include <stdio.h>
int main() {
    printf("Hello\n");
    printf("World\n");
    return 0;
}
```

```c
// Multi-symbol test
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main() {
    printf("Testing multiple symbols\n");
    void *p = malloc(100);
    strcpy((char*)p, "test");
    free(p);
    return 0;
}
```

## ✅ Phase 3 Complete!

Your GOT/PLT Educational MCP Server now includes:

**✅ Phase 1 (Foundation)**: Binary analysis, educational explanations, multi-level complexity
**✅ Phase 2 (Educational Framework)**: Concept validation, knowledge base integration, theory vs practice
**✅ Phase 3 (Runtime Analysis)**: Live tracing, lazy binding analysis, performance measurement, GDB integration

## 🎯 What's Next?

**Phase 3 Achievement Unlocked! 🏆** Your server now provides the most comprehensive educational analysis of GOT/PLT behavior available, bridging theory, static analysis, and runtime behavior.

**Future Enhancement Possibilities:**
- **Phase 4**: Multi-architecture support (ARM64, RISC-V)
- **Security Analysis**: ROP gadget detection in PLT stubs
- **Performance Optimization**: Cache analysis and optimization suggestions
- **Advanced Visualization**: Interactive diagrams of linking process

## 📈 Total Capabilities

**18 MCP Tools Total:**
- 5 from Phase 1 (Binary Analysis)
- 7 from Phase 2 (Concept Validation)  
- 6 from Phase 3 (Runtime Analysis)

**Complete Educational Pipeline:**
1. **Static Analysis** → Understand binary structure
2. **Concept Validation** → Test theory against binaries
3. **Runtime Analysis** → Observe dynamic behavior
4. **Educational Synthesis** → Learn through practice

---

**Phase 3 Achievement Unlocked! 🚀** Your GOT/PLT Educational MCP Server is now a comprehensive dynamic linking analysis and education platform!
