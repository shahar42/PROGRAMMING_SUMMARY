#!/usr/bin/env python3
"""
Educational Explainer for GOT/PLT Analysis

Generates educational explanations at different complexity levels for dynamic linking concepts.
Transforms technical binary analysis into accessible learning material.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("educational-explainer")


class EducationalExplainer:
    """
    Generates educational explanations for GOT/PLT analysis results
    
    Provides explanations at three levels:
    - Beginner: Simplified language, visual diagrams, basic concepts
    - Intermediate: Technical terminology, implementation details
    - Advanced: Deep technical analysis, optimization considerations
    """
    
    def __init__(self):
        """Initialize the educational explainer with explanation templates"""
        self.got_explanations = self._load_got_explanations()
        self.plt_explanations = self._load_plt_explanations()
        self.general_explanations = self._load_general_explanations()
    
    def _load_got_explanations(self) -> Dict[str, Dict[str, str]]:
        """Load GOT explanation templates for different levels"""
        return {
            "beginner": {
                "intro": """
🎯 **Global Offset Table (GOT) - Simple Explanation**

Think of the GOT like a phone book for your program. When your program wants to call a function from another library (like printf from the C library), it doesn't know where that function lives in memory until the program actually runs.

The GOT is a table that stores the addresses of these external functions. Initially, these addresses point to helper code that will find the real function the first time it's called.
""",
                "entry_format": "📍 **{symbol_name}** at {address}\n   Current value: {current_value}\n   Status: {'✅ Resolved' if resolved else '⏳ Not yet resolved'}\n   From library: {library_source}\n",
                "summary": """
🔑 **Key Points:**
- GOT stores addresses of external functions and data
- Addresses are filled in when the program runs (lazy binding)
- This allows programs to work even when libraries move around in memory
- Makes programs more flexible but slightly slower on first use
"""
            },
            "intermediate": {
                "intro": """
🔗 **Global Offset Table (GOT) Analysis**

The GOT is a critical component of position-independent code (PIC) and dynamic linking. It provides a level of indirection that allows the runtime linker to resolve symbol addresses without modifying the program's code sections.

This analysis shows the current state of GOT entries and their resolution status.
""",
                "entry_format": "🎯 **{symbol_name}** (Index: {entry_index})\n   Virtual Address: {address}\n   Current Value: {current_value}\n   Relocation Type: {relocation_type}\n   Binding: {binding_type}\n   Resolution Status: {'Resolved' if resolved else 'Pending'}\n   Source Library: {library_source}\n",
                "summary": """
📊 **Technical Summary:**
- GOT entries use R_*_JUMP_SLOT relocations for function calls
- R_*_GLOB_DAT relocations for global data access
- Lazy binding defers resolution until first use
- Position independence enables ASLR and shared library loading
"""
            },
            "advanced": {
                "intro": """
⚙️ **Global Offset Table (GOT) - Advanced Analysis**

The GOT implements the System V ABI's position-independent code mechanism. Each entry represents a runtime-patchable memory location that the dynamic linker (_dl_runtime_resolve) can modify to implement lazy symbol resolution.

Architecture-specific implementation details and performance characteristics are analyzed below.
""",
                "entry_format": "🔬 **{symbol_name}** (GOT[{entry_index}])\n   Virtual Address: {address} (Runtime patchable)\n   Current Content: {current_value}\n   Relocation: {relocation_type}\n   Binding Strategy: {binding_type}\n   Resolution State: {'Runtime-resolved' if resolved else 'Unresolved (stub target)'}\n   Provider: {library_source}\n   Memory Access Pattern: Indirect through GOT\n",
                "summary": """
🧠 **Advanced Considerations:**
- GOT entries incur one additional memory access per symbol reference
- Cache locality impact depends on GOT section layout and access patterns
- RELRO (Relocation Read-Only) can make GOT entries read-only after resolution
- Lazy binding trades startup time for runtime overhead on first access
- Symbol interposition requires GOT-based indirection even for internal calls
"""
            }
        }
    
    def _load_plt_explanations(self) -> Dict[str, Dict[str, str]]:
        """Load PLT explanation templates for different levels"""
        return {
            "beginner": {
                "intro": """
🎯 **Procedure Linkage Table (PLT) - Simple Explanation**

The PLT is like a bunch of small helper functions that work with the GOT. When your program tries to call an external function, it actually calls a PLT stub first.

The PLT stub looks up the real function address in the GOT and jumps to it. If it's the first time calling this function, the PLT stub helps figure out where the function really is.
""",
                "stub_format": "📞 **{symbol_name}** (PLT stub #{stub_index})\n   Location: {address}\n   Jumps to GOT entry: {got_reference}\n   Status: {'✅ Ready to call' if is_resolved else '⏳ Will resolve on first call'}\n",
                "disassembly_intro": "🔍 **What the computer actually does:**",
                "summary": """
🔑 **Key Points:**
- PLT stubs are small pieces of code that handle function calls
- They work together with the GOT to find external functions
- First call is slower (finds the function), later calls are fast
- This system lets programs use libraries without knowing exactly where they are
"""
            },
            "intermediate": {
                "intro": """
🔗 **Procedure Linkage Table (PLT) Analysis**

The PLT provides trampolines for external function calls, implementing lazy binding in conjunction with the GOT. Each PLT entry is a small stub that performs an indirect jump through the corresponding GOT entry.

The first call to a PLT stub triggers symbol resolution via _dl_runtime_resolve.
""",
                "stub_format": "🎯 **{symbol_name}** (PLT[{stub_index}])\n   Stub Address: {address}\n   Target GOT Entry: {got_reference}\n   Stub Type: {stub_type}\n   Resolution Status: {'Resolved' if is_resolved else 'Lazy (unresolved)'}\n   Final Target: {target_address}\n",
                "disassembly_intro": "🔍 **Assembly Analysis:**",
                "summary": """
📊 **Technical Details:**
- PLT stubs implement the lazy binding mechanism
- First call: stub → resolver → symbol lookup → GOT update → target function
- Subsequent calls: stub → GOT → target function (direct)
- PLT[0] contains the dynamic linker resolver code
- Each architecture has specific PLT stub formats and calling conventions
"""
            },
            "advanced": {
                "intro": """
⚙️ **Procedure Linkage Table (PLT) - Advanced Analysis**

The PLT implements the System V ABI's lazy binding protocol. Each entry is a precisely crafted instruction sequence that balances code size, performance, and flexibility. The implementation varies by architecture to optimize for instruction encoding efficiency and calling conventions.
""",
                "stub_format": "🔬 **{symbol_name}** (PLT[{stub_index}])\n   Stub VMA: {address} (Code segment)\n   GOT Reference: {got_reference} (Data segment)\n   Stub Implementation: {stub_type}\n   Binding State: {'Post-resolution direct jump' if is_resolved else 'Pre-resolution lazy stub'}\n   Target Symbol VMA: {target_address}\n   Performance: {'Resolved (single indirect jump)' if is_resolved else 'Unresolved (resolver overhead)'}\n",
                "disassembly_intro": "🔍 **Instruction-Level Analysis:**",
                "summary": """
🧠 **Advanced Performance Considerations:**
- PLT stubs add one level of indirection to all external calls
- Branch prediction effectiveness depends on call patterns and stub design
- Immediate binding (LD_BIND_NOW) eliminates runtime resolution overhead
- PLT stub cache footprint affects instruction cache performance
- Security implications: PLT stubs are executable and contain ROP gadgets
- Modern defenses: Intel CET, ARM Pointer Authentication affect PLT design
"""
            }
        }
    
    def _load_general_explanations(self) -> Dict[str, str]:
        """Load general dynamic linking explanations"""
        return {
            "linking_process_beginner": """
🔄 **How Dynamic Linking Works - Step by Step**

1. **Program Starts**: Your program begins running, but it doesn't know where library functions are yet
2. **First Function Call**: When you call printf() for the first time, the program goes to a PLT stub
3. **PLT Stub**: The stub looks in the GOT, but finds a "helper" address instead of printf
4. **Helper Does the Work**: The helper finds where printf really lives in memory
5. **GOT Gets Updated**: The helper puts printf's real address in the GOT
6. **Function Runs**: Now the program can call printf directly
7. **Future Calls**: Next time you call printf, it goes straight there (much faster!)

This system lets programs work with libraries that might be in different places in memory.
""",
            "linking_process_intermediate": """
🔄 **Dynamic Linking Process Overview**

**Load Time:**
- Program and dependencies loaded into memory
- GOT entries initialized with PLT resolver addresses
- Symbol tables prepared for runtime resolution

**Runtime Resolution (First Call):**
1. PLT stub performs indirect jump through GOT
2. GOT contains address of _dl_runtime_resolve
3. Resolver identifies symbol and searches libraries
4. Symbol address cached in GOT entry
5. Control transferred to resolved function

**Subsequent Calls:**
- PLT stub jumps directly through updated GOT entry
- No resolver overhead, single indirection penalty

**Key Components:**
- .got.plt: Runtime-patchable function addresses
- .plt: Lazy binding trampolines
- .rela.plt: Relocation information for resolver
- .dynsym: Dynamic symbol table for lookups
""",
            "linking_process_advanced": """
🔄 **Dynamic Linking: System V ABI Implementation**

**ELF Load-Time Processing:**
- ET_DYN objects loaded with ASLR offsets
- DT_NEEDED dependencies resolved via library search paths
- Relocation sections (.rela.plt, .rela.dyn) processed
- GOT entries initialized with PLT resolver entry points

**Lazy Binding Protocol:**
1. PLT[N] stub executes: push N; jmp PLT[0]
2. PLT[0] resolver: push linkmap; jmp _dl_runtime_resolve
3. _dl_runtime_resolve(linkmap, reloc_index):
   - Extract symbol from relocation table
   - Perform symbol lookup in loaded objects
   - Apply relocation to GOT entry
   - Transfer control to resolved symbol

**Performance Characteristics:**
- First call: ~100-1000 cycles (symbol resolution overhead)
- Subsequent calls: ~1-3 cycles (indirect jump penalty)
- Memory overhead: PLT + GOT + relocation metadata
- Cache impact: Additional memory accesses, potential TLB pressure

**Security Considerations:**
- PLT stubs in executable memory (ROP/JOP potential)
- GOT in writable memory (GOT overwrite attacks)
- Mitigations: RELRO, Intel CET, CFI implementations
"""
        }
    
    def generate_got_explanation(self, got_entries: List, binary_info: Dict[str, Any], detail_level: str) -> str:
        """
        Generate educational explanation for GOT analysis
        
        Args:
            got_entries: List of GOTEntry objects
            binary_info: Binary metadata
            detail_level: Explanation complexity level
            
        Returns:
            Formatted educational explanation
        """
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
        
        explanations = self.got_explanations[detail_level]
        
        # Build the explanation
        result = f"🔍 **GOT Analysis: {binary_info['file_path']}**\n\n"
        result += explanations["intro"] + "\n"
        
        # Add binary information
        arch = binary_info.get("architecture", "unknown")
        result += f"🏗️ **Binary Information:**\n"
        result += f"- Architecture: {arch}\n"
        result += f"- Entry Point: {binary_info.get('entry_point', 'unknown')}\n"
        result += f"- PIE/Dynamic: {binary_info.get('linking_info', {}).get('is_pie', False)}\n\n"
        
        if not got_entries:
            result += "⚠️ **No GOT entries found** - This binary may not use dynamic linking.\n"
            return result
        
        # Add GOT entries
        result += f"📊 **GOT Entries Found: {len(got_entries)}**\n\n"
        
        for entry in got_entries[:10]:  # Limit to first 10 for readability
            formatted_entry = explanations["entry_format"].format(
                symbol_name=entry.symbol_name or "unnamed",
                address=entry.address,
                current_value=entry.current_value,
                resolved=entry.resolved,
                library_source=entry.library_source or "unknown",
                entry_index=getattr(entry, 'entry_index', 0),
                relocation_type=getattr(entry, 'relocation_type', 'unknown'),
                binding_type=getattr(entry, 'binding_type', 'unknown')
            )
            result += formatted_entry + "\n"
        
        if len(got_entries) > 10:
            result += f"... and {len(got_entries) - 10} more entries\n\n"
        
        # Add summary
        result += explanations["summary"] + "\n"
        
        return result
    
    def generate_plt_explanation(self, plt_stubs: List, binary_info: Dict[str, Any], detail_level: str, symbol_filter: Optional[str] = None) -> str:
        """
        Generate educational explanation for PLT analysis
        
        Args:
            plt_stubs: List of PLTStub objects
            binary_info: Binary metadata
            detail_level: Explanation complexity level
            symbol_filter: Optional symbol filter
            
        Returns:
            Formatted educational explanation
        """
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
        
        explanations = self.plt_explanations[detail_level]
        
        # Build the explanation
        result = f"🔍 **PLT Analysis: {binary_info['file_path']}**\n\n"
        result += explanations["intro"] + "\n"
        
        # Add binary information
        arch = binary_info.get("architecture", "unknown")
        result += f"🏗️ **Binary Information:**\n"
        result += f"- Architecture: {arch}\n"
        result += f"- PLT Section: {'Present' if binary_info.get('linking_info', {}).get('has_plt', False) else 'Not found'}\n"
        
        if symbol_filter:
            result += f"- Filter: Showing entries for '{symbol_filter}'\n"
        
        result += "\n"
        
        if not plt_stubs:
            result += "⚠️ **No PLT stubs found** - This binary may not use dynamic function calls.\n"
            return result
        
        # Add PLT stubs
        display_stubs = plt_stubs
        if symbol_filter:
            display_stubs = [stub for stub in plt_stubs if symbol_filter.lower() in stub.symbol_name.lower()]
        
        result += f"📊 **PLT Stubs Found: {len(display_stubs)}**\n\n"
        
        for stub in display_stubs[:10]:  # Limit to first 10 for readability
            formatted_stub = explanations["stub_format"].format(
                symbol_name=stub.symbol_name or "unnamed",
                address=stub.address,
                got_reference=stub.got_reference,
                stub_index=getattr(stub, 'stub_index', 0),
                stub_type=getattr(stub, 'stub_type', 'unknown'),
                is_resolved=getattr(stub, 'is_resolved', False),
                target_address=getattr(stub, 'target_address', 'unknown')
            )
            result += formatted_stub + "\n"
            
            # Add disassembly if available
            if hasattr(stub, 'disassembly') and stub.disassembly:
                result += explanations["disassembly_intro"] + "\n"
                for instruction in stub.disassembly:
                    result += f"   {instruction}\n"
                result += "\n"
        
        if len(display_stubs) > 10:
            result += f"... and {len(display_stubs) - 10} more stubs\n\n"
        
        # Add summary
        result += explanations["summary"] + "\n"
        
        return result
    
    def generate_symbols_explanation(self, symbols: List, binary_info: Dict[str, Any], category: str, detail_level: str) -> str:
        """
        Generate educational explanation for dynamic symbols
        
        Args:
            symbols: List of SymbolInfo objects
            binary_info: Binary metadata
            category: Symbol category filter
            detail_level: Explanation complexity level
            
        Returns:
            Formatted educational explanation
        """
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
        
        # Build the explanation
        result = f"🔍 **Dynamic Symbols Analysis: {binary_info['file_path']}**\n\n"
        
        # Add category-specific introduction
        if category == "imports":
            result += "📥 **Imported Symbols** - Functions and data this program needs from other libraries\n\n"
        elif category == "exports":
            result += "📤 **Exported Symbols** - Functions and data this program provides to others\n\n"
        else:
            result += "🔄 **All Dynamic Symbols** - Both imported and exported symbols\n\n"
        
        if not symbols:
            result += f"⚠️ **No {category} symbols found**\n"
            return result
        
        # Categorize symbols
        imports = [s for s in symbols if getattr(s, 'is_import', False)]
        exports = [s for s in symbols if getattr(s, 'is_export', False)]
        
        result += f"📊 **Symbol Summary:**\n"
        result += f"- Total symbols: {len(symbols)}\n"
        result += f"- Imported: {len(imports)}\n"
        result += f"- Exported: {len(exports)}\n\n"
        
        # Display symbols based on detail level
        display_symbols = symbols[:20]  # Limit for readability
        
        if detail_level == "beginner":
            result += "🔍 **Symbol List:**\n"
            for symbol in display_symbols:
                symbol_type = "📥 Import" if getattr(symbol, 'is_import', False) else "📤 Export"
                result += f"{symbol_type}: **{symbol.name}** ({'Function' if symbol.symbol_type == 'FUNC' else 'Data'})\n"
        
        elif detail_level == "intermediate":
            result += "🔍 **Detailed Symbol Information:**\n"
            for symbol in display_symbols:
                direction = "📥 IMPORT" if getattr(symbol, 'is_import', False) else "📤 EXPORT"
                result += f"{direction}: **{symbol.name}**\n"
                result += f"   Type: {symbol.symbol_type}, Binding: {symbol.binding}\n"
                result += f"   Address: {symbol.address}, Size: {symbol.size} bytes\n\n"
        
        else:  # advanced
            result += "🔍 **Comprehensive Symbol Analysis:**\n"
            for symbol in display_symbols:
                direction = "📥 IMPORTED" if getattr(symbol, 'is_import', False) else "📤 EXPORTED"
                result += f"{direction}: **{symbol.name}**\n"
                result += f"   Symbol Type: {symbol.symbol_type}\n"
                result += f"   Binding: {symbol.binding}, Visibility: {symbol.visibility}\n"
                result += f"   Virtual Address: {symbol.address}\n"
                result += f"   Size: {symbol.size} bytes\n"
                result += f"   Section: {symbol.section}\n"
                if hasattr(symbol, 'library') and symbol.library:
                    result += f"   Library: {symbol.library}\n"
                result += "\n"
        
        if len(symbols) > 20:
            result += f"... and {len(symbols) - 20} more symbols\n\n"
        
        return result
    
    def generate_comprehensive_linking_explanation(self, got_entries: List, plt_stubs: List, symbols: List, binary_info: Dict[str, Any], detail_level: str) -> str:
        """
        Generate comprehensive educational explanation of the entire linking process
        
        Args:
            got_entries: List of GOT entries
            plt_stubs: List of PLT stubs
            symbols: List of dynamic symbols
            binary_info: Binary metadata
            detail_level: Explanation complexity level
            
        Returns:
            Comprehensive educational explanation
        """
        if detail_level not in ["beginner", "intermediate", "advanced"]:
            detail_level = "intermediate"
        
        # Build comprehensive explanation
        result = f"🔗 **Complete Dynamic Linking Analysis: {binary_info['file_path']}**\n\n"
        
        # Add process explanation
        process_key = f"linking_process_{detail_level}"
        if process_key in self.general_explanations:
            result += self.general_explanations[process_key] + "\n\n"
        
        # Add statistics
        result += "📊 **Analysis Summary:**\n"
        result += f"- Architecture: {binary_info.get('architecture', 'unknown')}\n"
        result += f"- GOT Entries: {len(got_entries)}\n"
        result += f"- PLT Stubs: {len(plt_stubs)}\n"
        result += f"- Dynamic Symbols: {len(symbols)}\n"
        result += f"- Position Independent: {binary_info.get('linking_info', {}).get('is_pie', False)}\n\n"
        
        # Add detailed analysis for each component (abbreviated)
        if got_entries:
            result += "🎯 **GOT Analysis Summary:**\n"
            for entry in got_entries[:3]:
                result += f"- {entry.symbol_name}: {entry.address} → {entry.current_value}\n"
            if len(got_entries) > 3:
                result += f"- ... and {len(got_entries) - 3} more entries\n"
            result += "\n"
        
        if plt_stubs:
            result += "📞 **PLT Stubs Summary:**\n"
            for stub in plt_stubs[:3]:
                result += f"- {stub.symbol_name}: {stub.address} → {stub.got_reference}\n"
            if len(plt_stubs) > 3:
                result += f"- ... and {len(plt_stubs) - 3} more stubs\n"
            result += "\n"
        
        # Add educational conclusion
        if detail_level == "beginner":
            result += """
🎓 **What This Means:**
This binary uses dynamic linking, which means it relies on other programs (libraries) to provide some of its functionality. The GOT and PLT work together to make this possible, allowing your program to call functions from libraries even when those libraries might be in different places in memory each time the program runs.
"""
        elif detail_level == "intermediate":
            result += """
🎓 **Technical Implications:**
This binary implements lazy binding through the PLT/GOT mechanism, providing runtime flexibility at the cost of indirection overhead. The first call to each external function incurs resolution costs, while subsequent calls have minimal overhead. This design enables position-independent execution and efficient memory sharing of libraries.
"""
        else:  # advanced
            result += """
🎓 **Advanced Analysis:**
The binary demonstrates standard System V ABI compliance with architecture-specific PLT stub implementations. Performance characteristics depend on call patterns, with cold-start resolution overhead amortized across program execution. Security implications include executable PLT sections and writable GOT entries, mitigated by modern defenses like RELRO and control flow integrity.
"""
        
        return result
    
    def generate_code_example(self, concept: str) -> str:
        """
        Generate minimal C code example demonstrating linking concept
        
        Args:
            concept: Linking concept to demonstrate
            
        Returns:
            C code example with explanation
        """
        examples = {
            "got": """
🔍 **GOT Demonstration Example**

```c
// file: got_demo.c
#include <stdio.h>

extern int global_var;  // External variable (will use GOT)

int main() {
    printf("Global var: %d\\n", global_var);  // printf via PLT/GOT
    return 0;
}
```

```c
// file: global_var.c  
int global_var = 42;
```

**Compilation & Analysis:**
```bash
# Compile as shared library
gcc -fPIC -shared global_var.c -o libglobal.so

# Compile main program
gcc -L. -lglobal got_demo.c -o got_demo

# Analyze GOT entries
objdump -R got_demo
readelf -r got_demo
```

**What happens:**
1. `global_var` access goes through GOT entry
2. `printf` call uses PLT stub that references GOT
3. Runtime linker resolves addresses in GOT entries
""",
            "plt": """
🔍 **PLT Demonstration Example**

```c
// file: plt_demo.c
#include <stdio.h>
#include <math.h>

int main() {
    printf("Hello from PLT!\\n");     // First external call
    printf("Square root: %.2f\\n", sqrt(16.0));  // Second external call
    return 0;
}
```

**Compilation & Analysis:**
```bash
# Compile with dynamic linking
gcc plt_demo.c -lm -o plt_demo

# Examine PLT section
objdump -d -j .plt plt_demo

# Show PLT entries
readelf -r plt_demo | grep JUMP_SLOT
```

**What the PLT does:**
1. Each external function gets a PLT stub
2. First call: PLT → resolver → library → update GOT → function
3. Later calls: PLT → GOT → function (direct jump)
""",
            "lazy_binding": """
🔍 **Lazy Binding Demonstration**

```c
// file: lazy_demo.c
#include <stdio.h>
#include <dlfcn.h>
#include <unistd.h>

void show_got_entry() {
    // This function will be resolved on first call
    printf("Function resolved!\\n");
}

int main() {
    printf("Program started - functions not yet resolved\\n");
    sleep(1);  // Pause to allow inspection
    
    printf("About to call external function...\\n");
    show_got_entry();  // First call - resolution happens here
    
    printf("Calling again - should be faster\\n");
    show_got_entry();  // Second call - direct through GOT
    
    return 0;
}
```

**Analysis with GDB:**
```bash
# Compile with debug info
gcc -g lazy_demo.c -o lazy_demo

# Debug session
gdb lazy_demo
(gdb) break main
(gdb) run
(gdb) x/i printf@plt     # Show PLT stub before resolution
(gdb) continue
(gdb) x/i printf@plt     # Show GOT entry after resolution
```
""",
            "symbol_resolution": """
🔍 **Symbol Resolution Example**

```c
// file: symbol_demo.c
#include <stdio.h>

// Override a library function
int puts(const char *s) {
    printf("[INTERCEPTED] %s\\n", s);
    return 0;
}

int main() {
    puts("This will be intercepted!");
    printf("This goes to real printf\\n");
    return 0;
}
```

**Compilation & Analysis:**
```bash
# Compile and run
gcc symbol_demo.c -o symbol_demo
./symbol_demo

# Examine symbol resolution order
LD_DEBUG=symbols ./symbol_demo 2>&1 | grep puts

# Show symbol table
nm -D symbol_demo | grep puts
```

**What this demonstrates:**
- Symbol resolution searches program first, then libraries
- Global symbols can be interposed (overridden)
- Dynamic linker resolves symbols at runtime
"""
        }
        
        concept_lower = concept.lower()
        for key, example in examples.items():
            if key in concept_lower:
                return example
        
        # Default example
        return f"""
🔍 **General Dynamic Linking Example**

```c
// file: basic_demo.c
#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("Hello, dynamic world!\\n");
    void *ptr = malloc(100);
    free(ptr);
    return 0;
}
```

**Analysis Commands:**
```bash
# Compile
gcc basic_demo.c -o basic_demo

# Show dynamic dependencies
ldd basic_demo

# Examine GOT/PLT
objdump -d -j .plt basic_demo
readelf -r basic_demo
```

This example shows basic dynamic linking with external function calls.
"""
