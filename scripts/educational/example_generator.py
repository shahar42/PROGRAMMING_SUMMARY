#!/usr/bin/env python3
"""
Enhanced Example Generator for GOT/PLT Educational MCP Server

Generates educational code examples that demonstrate linking concepts from the knowledge base.
Integrates with extracted Linkers & Loaders concepts to create targeted demonstrations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import subprocess

logger = logging.getLogger("example-generator")


class EnhancedExampleGenerator:
    """
    Generates code examples that demonstrate specific linking concepts
    
    Integrates with the existing concept database to create examples that
    directly validate theoretical knowledge from the Linkers & Loaders book.
    """
    
    def __init__(self, concepts_dir: Optional[str] = None):
        """
        Initialize example generator with concept database
        
        Args:
            concepts_dir: Path to linkers_loaders concepts directory
        """
        if concepts_dir is None:
            project_root = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
            self.concepts_dir = project_root / "outputs" / "linkers_loaders"
        else:
            self.concepts_dir = Path(concepts_dir)
        
        self.concepts_db = self._load_concepts()
        self.example_templates = self._load_example_templates()
        
    def _load_concepts(self) -> Dict[str, Any]:
        """Load concepts from the knowledge base"""
        concepts = {}
        
        if not self.concepts_dir.exists():
            logger.warning(f"Concepts directory not found: {self.concepts_dir}")
            return concepts
        
        for concept_file in self.concepts_dir.glob("*concept_*.json"):
            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept_data = json.load(f)
                
                concept_name = concept_data.get('topic', concept_file.stem)
                concepts[concept_name] = concept_data
                
            except Exception as e:
                logger.warning(f"Failed to load concept from {concept_file}: {e}")
        
        return concepts
    
    def _load_example_templates(self) -> Dict[str, Dict[str, str]]:
        """Load example templates for different concepts"""
        return {
            "got_basic": {
                "title": "Basic GOT Usage",
                "description": "Demonstrates how external variables are accessed through the GOT",
                "main_file": """
// main.c - Demonstrates GOT usage with external variables
#include <stdio.h>

// External variable that will require GOT entry
extern int shared_counter;
extern const char* shared_message;

int main() {
    printf("Accessing external variable through GOT...\\n");
    printf("Shared counter: %d\\n", shared_counter);
    printf("Shared message: %s\\n", shared_message);
    
    // Modify external variable
    shared_counter++;
    printf("Updated counter: %d\\n", shared_counter);
    
    return 0;
}
""",
                "lib_file": """
// shared.c - Provides external variables
int shared_counter = 42;
const char* shared_message = "Hello from shared library!";
""",
                "compile_commands": [
                    "gcc -fPIC -shared shared.c -o libshared.so",
                    "gcc -L. -lshared main.c -o got_demo",
                    "LD_LIBRARY_PATH=. ./got_demo"
                ],
                "analysis_commands": [
                    "readelf -r got_demo | grep shared",
                    "objdump -R got_demo",
                    "objdump -d -j .got.plt got_demo"
                ]
            },
            "plt_basic": {
                "title": "Basic PLT Usage",
                "description": "Demonstrates PLT stubs for external function calls",
                "main_file": """
// main.c - Demonstrates PLT usage with external functions
#include <stdio.h>
#include <math.h>
#include <string.h>

// Function that will use PLT
extern void library_function(const char* msg);

int main() {
    printf("Calling external functions via PLT...\\n");
    
    // Standard library functions (use PLT)
    printf("sqrt(16) = %.2f\\n", sqrt(16.0));
    
    // String function (uses PLT)
    char buffer[100];
    strcpy(buffer, "PLT demonstration");
    printf("String length: %zu\\n", strlen(buffer));
    
    // Custom library function (uses PLT)
    library_function("Hello from PLT!");
    
    return 0;
}
""",
                "lib_file": """
// library.c - Provides external function
#include <stdio.h>

void library_function(const char* msg) {
    printf("[LIBRARY] %s\\n", msg);
}
""",
                "compile_commands": [
                    "gcc -fPIC -shared library.c -o liblibrary.so",
                    "gcc -L. -llibrary -lm main.c -o plt_demo",
                    "LD_LIBRARY_PATH=. ./plt_demo"
                ],
                "analysis_commands": [
                    "objdump -d -j .plt plt_demo",
                    "readelf -r plt_demo | grep JUMP_SLOT",
                    "objdump -T plt_demo"
                ]
            },
            "lazy_binding": {
                "title": "Lazy Binding Demonstration",
                "description": "Shows the difference between first call and subsequent calls",
                "main_file": """
// main.c - Demonstrates lazy binding behavior
#include <stdio.h>
#include <unistd.h>
#include <dlfcn.h>

// Function that will demonstrate lazy binding
extern void slow_function(void);
extern void fast_function(void);

int main() {
    printf("=== Lazy Binding Demonstration ===\\n");
    
    printf("Program started - functions not yet resolved\\n");
    printf("Press Enter to make first call (slow - resolution overhead)...");
    getchar();
    
    printf("Making first call to slow_function...\\n");
    slow_function();  // First call - resolver overhead
    
    printf("Press Enter to make second call (fast - direct jump)...");
    getchar();
    
    printf("Making second call to slow_function...\\n");
    slow_function();  // Second call - direct through GOT
    
    printf("\\nCalling fast_function multiple times...\\n");
    for (int i = 0; i < 3; i++) {
        printf("Call %d: ", i + 1);
        fast_function();
    }
    
    return 0;
}
""",
                "lib_file": """
// timing_lib.c - Library functions with timing info
#include <stdio.h>
#include <time.h>
#include <unistd.h>

void slow_function(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    printf("slow_function called at %ld.%09ld\\n", ts.tv_sec, ts.tv_nsec);
    usleep(10000);  // 10ms delay to simulate work
}

void fast_function(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    printf("fast_function called at %ld.%09ld\\n", ts.tv_sec, ts.tv_nsec);
}
""",
                "compile_commands": [
                    "gcc -fPIC -shared timing_lib.c -o libtiming.so",
                    "gcc -L. -ltiming main.c -o lazy_demo",
                    "LD_LIBRARY_PATH=. ./lazy_demo"
                ],
                "analysis_commands": [
                    "# Run with immediate binding to compare:",
                    "LD_BIND_NOW=1 LD_LIBRARY_PATH=. ./lazy_demo",
                    "# Analyze PLT/GOT structure:",
                    "objdump -d -j .plt lazy_demo | head -20",
                    "readelf -r lazy_demo"
                ]
            },
            "symbol_resolution": {
                "title": "Symbol Resolution Order",
                "description": "Demonstrates symbol resolution and interposition",
                "main_file": """
// main.c - Symbol resolution demonstration
#include <stdio.h>

// Declare functions that exist in multiple places
void common_function(void);
void library_function(void);

// Override a library function (symbol interposition)
void puts(const char *s) {
    printf("[INTERCEPTED puts] %s\\n", s);
}

int main() {
    printf("=== Symbol Resolution Order Demo ===\\n");
    
    printf("Calling overridden puts function:\\n");
    puts("This should be intercepted!");
    
    printf("\\nCalling common_function (resolution order matters):\\n");
    common_function();
    
    printf("\\nCalling library_function:\\n");
    library_function();
    
    return 0;
}

// Local definition of common_function
void common_function(void) {
    printf("[MAIN] common_function from main program\\n");
}
""",
                "lib_file": """
// resolution_lib.c - Library with competing symbols
#include <stdio.h>

void common_function(void) {
    printf("[LIB] common_function from library (should not be called)\\n");
}

void library_function(void) {
    printf("[LIB] library_function - unique to library\\n");
}
""",
                "compile_commands": [
                    "gcc -fPIC -shared resolution_lib.c -o libresolution.so",
                    "gcc -L. -lresolution main.c -o symbol_demo",
                    "LD_LIBRARY_PATH=. ./symbol_demo"
                ],
                "analysis_commands": [
                    "# Show symbol resolution with debug output:",
                    "LD_DEBUG=symbols LD_LIBRARY_PATH=. ./symbol_demo 2>&1 | grep -E '(puts|common_function)'",
                    "# Show symbol tables:",
                    "nm -D symbol_demo | grep -E '(puts|common_function)'",
                    "nm -D libresolution.so | grep common_function"
                ]
            }
        }
    
    def generate_concept_example(self, concept_name: str) -> str:
        """
        Generate a code example for a specific concept from the knowledge base
        
        Args:
            concept_name: Name of concept to generate example for
            
        Returns:
            Complete code example with compilation and analysis instructions
        """
        # Check if concept exists in knowledge base
        concept_info = self.concepts_db.get(concept_name)
        if not concept_info:
            return self._generate_fallback_example(concept_name)
        
        # Try to find matching template
        concept_lower = concept_name.lower()
        
        if any(keyword in concept_lower for keyword in ['got', 'global offset table']):
            return self._generate_got_example(concept_info)
        elif any(keyword in concept_lower for keyword in ['plt', 'procedure linkage table']):
            return self._generate_plt_example(concept_info)
        elif any(keyword in concept_lower for keyword in ['lazy binding', 'dynamic linking']):
            return self._generate_lazy_binding_example(concept_info)
        elif any(keyword in concept_lower for keyword in ['symbol resolution', 'symbol table']):
            return self._generate_symbol_resolution_example(concept_info)
        else:
            return self._generate_custom_example(concept_info)
    
    def _generate_got_example(self, concept_info: Dict[str, Any]) -> str:
        """Generate GOT-specific example"""
        template = self.example_templates["got_basic"]
        
        result = f"""
🔍 **{template['title']} - Demonstrating: {concept_info['topic']}**

**Theoretical Background:**
{concept_info['explanation'][:300]}{'...' if len(concept_info['explanation']) > 300 else ''}

**What this example demonstrates:**
{template['description']}

{self._format_code_example(template)}

**Educational Notes:**
- The GOT entries will be created for `shared_counter` and `shared_message`
- At runtime, these entries will be filled with actual addresses
- This enables position-independent code and ASLR
- Use `readelf -r` to see the relocation entries that populate the GOT

**Connection to Theory:**
This example validates the concept from your knowledge base by showing how external variables require GOT entries for position-independent access.
"""
        
        return result
    
    def _generate_plt_example(self, concept_info: Dict[str, Any]) -> str:
        """Generate PLT-specific example"""
        template = self.example_templates["plt_basic"]
        
        result = f"""
🔍 **{template['title']} - Demonstrating: {concept_info['topic']}**

**Theoretical Background:**
{concept_info['explanation'][:300]}{'...' if len(concept_info['explanation']) > 300 else ''}

**What this example demonstrates:**
{template['description']}

{self._format_code_example(template)}

**Educational Notes:**
- Each external function call goes through a PLT stub
- PLT stubs are small pieces of code that jump through the GOT
- First call: PLT → resolver → symbol lookup → GOT update → function
- Later calls: PLT → GOT → function (direct)

**Connection to Theory:**
This example validates how PLT stubs implement the lazy binding mechanism described in your knowledge base.
"""
        
        return result
    
    def _generate_lazy_binding_example(self, concept_info: Dict[str, Any]) -> str:
        """Generate lazy binding example"""
        template = self.example_templates["lazy_binding"]
        
        result = f"""
🔍 **{template['title']} - Demonstrating: {concept_info['topic']}**

**Theoretical Background:**
{concept_info['explanation'][:300]}{'...' if len(concept_info['explanation']) > 300 else ''}

**What this example demonstrates:**
{template['description']}

{self._format_code_example(template)}

**Educational Notes:**
- Run the program and observe the pause between calls
- First call incurs symbol resolution overhead
- Subsequent calls are direct jumps through updated GOT entries
- Compare with LD_BIND_NOW=1 for immediate binding

**Connection to Theory:**
This example demonstrates the lazy binding process described in your knowledge base, showing the performance trade-off between startup time and runtime overhead.
"""
        
        return result
    
    def _generate_symbol_resolution_example(self, concept_info: Dict[str, Any]) -> str:
        """Generate symbol resolution example"""
        template = self.example_templates["symbol_resolution"]
        
        result = f"""
🔍 **{template['title']} - Demonstrating: {concept_info['topic']}**

**Theoretical Background:**
{concept_info['explanation'][:300]}{'...' if len(concept_info['explanation']) > 300 else ''}

**What this example demonstrates:**
{template['description']}

{self._format_code_example(template)}

**Educational Notes:**
- Symbol resolution searches program first, then libraries
- `puts` function is overridden in the main program
- `common_function` in main program shadows library version
- Use LD_DEBUG=symbols to see resolution process

**Connection to Theory:**
This example validates the symbol resolution order and interposition mechanisms described in your knowledge base.
"""
        
        return result
    
    def _generate_custom_example(self, concept_info: Dict[str, Any]) -> str:
        """Generate custom example based on concept information"""
        # Use existing code example from concept if available
        if concept_info.get('code_example'):
            code_lines = concept_info['code_example']
            if isinstance(code_lines, list):
                code = '\n'.join(code_lines)
            else:
                code = str(code_lines)
            
            result = f"""
🔍 **Custom Example - Demonstrating: {concept_info['topic']}**

**Theoretical Background:**
{concept_info['explanation']}

**Code Example from Knowledge Base:**
```c
{code}
```
"""
            
            if concept_info.get('example_explanation'):
                result += f"""
**Explanation:**
{concept_info['example_explanation']}
"""
            
            result += f"""
**How to test this concept:**
1. Save the code to a file (e.g., `concept_test.c`)
2. Compile with: `gcc concept_test.c -o concept_test`
3. Analyze with: `objdump -d concept_test` and `readelf -r concept_test`
4. Run with: `./concept_test`

**Educational Value:**
This example comes directly from your extracted knowledge base and demonstrates the theoretical concept in practice.
"""
            
            return result
        
        return self._generate_fallback_example(concept_info['topic'])
    
    def _format_code_example(self, template: Dict[str, str]) -> str:
        """Format a complete code example with files and commands"""
        result = ""
        
        # Main file
        result += "**📄 main.c:**\n```c\n" + template['main_file'].strip() + "\n```\n\n"
        
        # Library file (if present)
        if 'lib_file' in template:
            # Determine library filename from first compile command
            lib_filename = "library.c"  # default
            if template['compile_commands']:
                first_cmd = template['compile_commands'][0]
                if 'shared.c' in first_cmd:
                    lib_filename = "shared.c"
                elif 'library.c' in first_cmd:
                    lib_filename = "library.c"
                elif 'timing_lib.c' in first_cmd:
                    lib_filename = "timing_lib.c"
                elif 'resolution_lib.c' in first_cmd:
                    lib_filename = "resolution_lib.c"
            
            result += f"**📄 {lib_filename}:**\n```c\n" + template['lib_file'].strip() + "\n```\n\n"
        
        # Compilation commands
        if template['compile_commands']:
            result += "**🔨 Compilation:**\n```bash\n"
            for cmd in template['compile_commands']:
                result += cmd + "\n"
            result += "```\n\n"
        
        # Analysis commands  
        if template['analysis_commands']:
            result += "**🔍 Analysis:**\n```bash\n"
            for cmd in template['analysis_commands']:
                result += cmd + "\n"
            result += "```\n\n"
        
        return result
    
    def _generate_fallback_example(self, concept_name: str) -> str:
        """Generate a basic example when no specific template is available"""
        return f"""
🔍 **Basic Dynamic Linking Example - Related to: {concept_name}**

**Simple Demonstration:**
```c
// main.c
#include <stdio.h>

int main() {{
    printf("Dynamic linking example for: {concept_name}\\n");
    return 0;
}}
```

**Compilation and Analysis:**
```bash
# Compile
gcc main.c -o example

# Analyze dynamic linking aspects
ldd example
readelf -d example
objdump -R example
```

**Educational Note:**
This is a basic example. For more specific demonstrations of "{concept_name}", try using one of the available template concepts:
- GOT-related concepts
- PLT-related concepts  
- Lazy binding concepts
- Symbol resolution concepts
"""
    
    def create_interactive_example(self, concept_name: str, output_dir: str = None) -> str:
        """
        Create interactive example files that can be compiled and run
        
        Args:
            concept_name: Name of concept to create example for
            output_dir: Directory to create files in (default: temp directory)
            
        Returns:
            Path to created example directory and instructions
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix=f"got_plt_example_{concept_name.replace(' ', '_')}_")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        try:
            # Get concept info and determine example type
            concept_info = self.concepts_db.get(concept_name, {})
            concept_lower = concept_name.lower()
            
            # Select appropriate template
            template_name = "got_basic"  # default
            if any(keyword in concept_lower for keyword in ['plt', 'procedure linkage']):
                template_name = "plt_basic"
            elif any(keyword in concept_lower for keyword in ['lazy binding']):
                template_name = "lazy_binding"
            elif any(keyword in concept_lower for keyword in ['symbol resolution']):
                template_name = "symbol_resolution"
            
            template = self.example_templates[template_name]
            
            # Create main.c
            main_file = output_path / "main.c"
            with open(main_file, 'w') as f:
                f.write(template['main_file'])
            
            # Create library file if present
            if 'lib_file' in template:
                # Determine library filename
                lib_name = "library.c"
                if 'shared.c' in template['compile_commands'][0]:
                    lib_name = "shared.c"
                elif 'timing_lib.c' in template['compile_commands'][0]:
                    lib_name = "timing_lib.c"
                elif 'resolution_lib.c' in template['compile_commands'][0]:
                    lib_name = "resolution_lib.c"
                
                lib_file = output_path / lib_name
                with open(lib_file, 'w') as f:
                    f.write(template['lib_file'])
            
            # Create build script
            build_script = output_path / "build.sh"
            with open(build_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# Build script for {concept_name} example\n\n")
                f.write("set -e\n\n")
                for cmd in template['compile_commands']:
                    f.write(f"{cmd}\n")
            
            build_script.chmod(0o755)
            
            # Create analysis script
            analysis_script = output_path / "analyze.sh"
            with open(analysis_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# Analysis script for {concept_name} example\n\n")
                for cmd in template['analysis_commands']:
                    if cmd.startswith('#'):
                        f.write(f"{cmd}\n")
                    else:
                        f.write(f"echo '=== {cmd} ==='\n")
                        f.write(f"{cmd}\n")
                        f.write("echo\n")
            
            analysis_script.chmod(0o755)
            
            # Create README
            readme_file = output_path / "README.md"
            with open(readme_file, 'w') as f:
                f.write(f"# {template['title']} - {concept_name}\n\n")
                f.write(f"**Description:** {template['description']}\n\n")
                if concept_info.get('explanation'):
                    f.write(f"**Theoretical Background:**\n{concept_info['explanation']}\n\n")
                f.write("## Usage\n\n")
                f.write("1. Build the example: `./build.sh`\n")
                f.write("2. Run the analysis: `./analyze.sh`\n")
                f.write("3. Execute the program as instructed\n\n")
                f.write("## Files\n\n")
                f.write("- `main.c` - Main program\n")
                if 'lib_file' in template:
                    lib_name = next((cmd.split()[2] for cmd in template['compile_commands'] if cmd.startswith('gcc') and '.c' in cmd), 'library.c')
                    f.write(f"- `{lib_name}` - Shared library source\n")
                f.write("- `build.sh` - Compilation script\n")
                f.write("- `analyze.sh` - Analysis script\n")
            
            result = f"""
✅ **Interactive Example Created Successfully!**

**Location:** `{output_path}`

**Files Created:**
- `main.c` - Main program demonstrating {concept_name}
- Library source files (if applicable)
- `build.sh` - Automated build script
- `analyze.sh` - Analysis commands
- `README.md` - Complete documentation

**Quick Start:**
```bash
cd {output_path}
./build.sh      # Compile the example
./analyze.sh    # Analyze the binary
```

**Educational Value:**
This hands-on example lets you explore {concept_name} by:
1. Compiling and running real code
2. Analyzing the resulting binaries
3. Observing the concepts in action

The example is self-contained and includes all necessary instructions.
"""
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create interactive example: {e}")
            return f"❌ Failed to create interactive example: {str(e)}"
    
    def list_available_examples(self) -> str:
        """List all available example templates"""
        result = "📚 **Available Example Templates**\n\n"
        
        for template_name, template_info in self.example_templates.items():
            result += f"**{template_info['title']}**\n"
            result += f"- {template_info['description']}\n"
            result += f"- Template ID: `{template_name}`\n\n"
        
        result += "💡 **Usage:** Use `generate_minimal_example(concept_name)` to create examples based on your knowledge base concepts.\n"
        
        return result
