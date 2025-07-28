# GOT/PLT Educational MCP Server - Phase 2 Setup Guide

## 🎯 Phase 2 Overview: Educational Framework

**Phase 2** adds advanced educational capabilities that integrate with your existing **Linkers & Loaders** concept database. This phase bridges the gap between theoretical knowledge and practical binary analysis.

## 🆕 New Capabilities Added

### **1. Concept Validation System**
- **Validates theory against practice** - Tests extracted concepts from your knowledge base against real ELF binaries
- **Educational reporting** - Provides detailed explanations when theory matches or differs from observed behavior
- **Confidence scoring** - Quantifies how well theory matches practice (0-100%)

### **2. Knowledge Base Integration**
- **Loads concepts from `/outputs/linkers_loaders/`** - Uses your existing extracted concepts
- **Searchable concept repository** - Find concepts by keywords or topics
- **Detailed concept information** - Access theory, examples, and metadata

### **3. Enhanced Example Generation**
- **Knowledge-driven examples** - Examples directly tied to concepts from your database
- **Interactive examples** - Generate complete, compilable projects
- **Template system** - Pre-built examples for common scenarios

### **4. Theory vs Practice Comparison**
- **Side-by-side analysis** - Compare theoretical descriptions with binary evidence
- **Educational insights** - Explanations of why differences occur
- **Learning opportunities** - Turn discrepancies into educational moments

## 📁 Files Added in Phase 2

```
scripts/
├── educational/
│   ├── concept_validator.py        # NEW: Validates concepts against binaries
│   ├── example_generator.py        # NEW: Enhanced example generation
│   └── __init__.py (updated)       # Updated imports
│
├── utils/
│   └── error_handler.py            # NEW: Educational error handling
│
└── got_plt_mcp_server.py (updated) # Updated with 7 new MCP tools
```

## 🛠️ Phase 2 Tools Added

### **New MCP Tools Available:**

1. **`validate_concept(concept_name, binary_path=None)`**
   - Tests theoretical concept against real binary
   - Returns detailed validation report with evidence and discrepancies

2. **`list_available_concepts()`**
   - Shows all concepts loaded from your knowledge base
   - Organizes by category (GOT/PLT, Symbol Resolution, etc.)

3. **`find_related_concepts(search_term)`**
   - Search concepts by keyword
   - Returns matching concepts with descriptions

4. **`get_concept_info(concept_name)`**
   - Detailed information about specific concept
   - Shows theory, examples, syntax, and metadata

5. **`compare_theory_vs_practice(concept_name, binary_path)`**
   - Side-by-side comparison of theory vs observed behavior
   - Educational analysis of matches and discrepancies

6. **`create_interactive_example(concept_name, output_directory=None)`**
   - Creates complete, compilable example project
   - Includes source files, build scripts, and analysis tools

7. **`list_example_templates()`**
   - Shows available example templates
   - Describes what each template demonstrates

## 🧪 Testing Phase 2

### **1. Verify Concept Database Loading**

Start the server and check concept loading:

```bash
cd scripts/
python3 got_plt_mcp_server.py
```

Look for log messages like:
```
Loaded 45 linker concepts for validation
Starting GOT/PLT Educational Analysis Server - Phase 2
```

### **2. Test Concept Validation (via MCP)**

Try these queries through your MCP client:

```
"List all available concepts for validation"
"Find concepts related to GOT"
"Validate the Global Offset Table concept"
"Compare theory vs practice for PLT using /bin/ls"
```

### **3. Test Interactive Examples**

```
"Create an interactive example for lazy binding"
"Generate a minimal example demonstrating GOT usage"
"List available example templates"
```

### **4. Manual Testing**

You can also test Phase 2 directly:

```python
from educational.concept_validator import ConceptValidator
from educational.example_generator import EnhancedExampleGenerator

# Test concept validator
validator = ConceptValidator()
concepts = validator.list_available_concepts()
print(f"Loaded {len(concepts)} concepts")

# Test validation
result = validator.validate_concept("Global Offset Table", "/bin/ls")
print(result.validation_status)

# Test example generator
generator = EnhancedExampleGenerator()
example = generator.generate_concept_example("PLT")
print(example)
```

## 🔗 Integration with Existing Architecture

### **Master Orchestrator Integration**

No changes needed! Your existing orchestrator will automatically route queries like:
- "How does the GOT work in practice?"
- "Validate the lazy binding concept"
- "Show me a PLT example"

These will be detected by your topic detection and routed to the GOT/PLT server.

### **Concept Database Integration**

Phase 2 automatically integrates with your existing extraction system:
- **Location**: `/outputs/linkers_loaders/*.json`
- **Format**: Uses your existing concept JSON structure
- **Updates**: Automatically picks up new extracted concepts

## 📊 Phase 2 Success Metrics

### **Validation Capabilities**
- [x] Loads concepts from existing knowledge base
- [x] Validates theory against binary evidence  
- [x] Provides educational explanations for discrepancies
- [x] Generates confidence scores for validation results

### **Educational Features**
- [x] Theory vs practice comparisons
- [x] Searchable concept repository
- [x] Interactive example generation
- [x] Knowledge-driven educational explanations

### **Integration**
- [x] Seamless integration with existing MCP architecture
- [x] No changes required to orchestrator or topic detection
- [x] Compatible with existing concept extraction system

## 🎓 Educational Impact

### **Before Phase 2:**
- Static binary analysis with generic explanations
- Basic example generation
- No connection to theoretical knowledge

### **After Phase 2:**
- **Theory-validated analysis** - Every analysis backed by theoretical knowledge
- **Concept-driven examples** - Examples directly tied to your knowledge base
- **Learning through validation** - Discover when theory matches/differs from practice
- **Knowledge exploration** - Search and explore your extracted concepts

## 🚀 Example Usage Scenarios

### **Scenario 1: Learning GOT Concepts**
```
User: "I want to understand how the Global Offset Table works"

1. find_related_concepts("GOT") 
   → Shows all GOT-related concepts from knowledge base

2. get_concept_info("Global Offset Table")
   → Detailed theory from Linkers & Loaders book

3. validate_concept("Global Offset Table", "/bin/ls")
   → Tests theory against real binary

4. create_interactive_example("Global Offset Table")  
   → Generates compilable example to explore
```

### **Scenario 2: Debugging Linking Issues**
```
User: "Why is my program's symbol resolution not working as expected?"

1. list_available_concepts()
   → Browse symbol resolution concepts

2. compare_theory_vs_practice("Symbol Resolution", "my_program")
   → Compare theory with actual binary behavior  

3. generate_minimal_example("symbol resolution")
   → Create test case to isolate the issue
```

### **Scenario 3: Teaching Dynamic Linking**
```
Instructor: "I need materials to teach lazy binding"

1. get_concept_info("Lazy Binding")
   → Get theoretical background

2. create_interactive_example("lazy binding", "/tmp/teaching_example")
   → Create complete teaching materials

3. validate_concept("Lazy Binding", "/bin/gcc")
   → Show real-world validation
```

## 🐛 Troubleshooting Phase 2

### **"No concepts loaded"**
- **Check**: Does `/outputs/linkers_loaders/` directory exist?
- **Check**: Are there `*concept_*.json` files in the directory?
- **Fix**: Run your linkers_loaders extraction script to populate concepts

### **"Concept not found" errors**
- **Check**: Use `list_available_concepts()` to see what's available
- **Note**: Concept names must match exactly (case-sensitive)
- **Tip**: Use `find_related_concepts()` to search for partial matches

### **Validation fails with "untestable"**
- **Check**: Is the binary dynamically linked? (`ldd binary_name`)
- **Check**: Does the binary have GOT/PLT sections? (`objdump -h binary_name`)
- **Note**: Static binaries can't be used to validate dynamic linking concepts

### **Interactive examples fail to compile**
- **Check**: Are required tools installed? (`gcc`, `objdump`, `readelf`)
- **Check**: File permissions on generated scripts
- **Fix**: Run `chmod +x build.sh analyze.sh` in example directory

## ✅ Phase 2 Complete!

Your GOT/PLT Educational MCP Server now includes:

**✅ Foundation (Phase 1)**: Binary analysis, educational explanations, multi-level complexity
**✅ Educational Framework (Phase 2)**: Concept validation, knowledge base integration, theory vs practice

## 🎯 Next: Phase 3 (Runtime Analysis)

**Phase 3** will add:
- GDB integration for runtime analysis
- Live symbol resolution tracing  
- Lazy binding behavior observation
- Dynamic GOT state inspection

**Ready for Phase 3?** Phase 2 provides the perfect foundation for adding runtime analysis capabilities!

---

**Phase 2 Achievement Unlocked! 🏆** Your server now bridges theory and practice with educational validation.
