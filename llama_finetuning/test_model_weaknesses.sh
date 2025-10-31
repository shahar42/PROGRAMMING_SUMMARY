#!/bin/bash
# Test V2 model for weak points across multiple categories

MODEL_CMD="feather"
OUTPUT_DIR="model_weakness_analysis"
mkdir -p "$OUTPUT_DIR"

echo "🔍 Testing V2 Model Weaknesses"
echo "================================"
echo ""

# Test categories with questions designed to expose weaknesses

# 1. Memory Layout & Alignment
echo "📦 Testing: Memory Layout & Alignment..."
cat > "$OUTPUT_DIR/01_memory_layout.txt" << 'EOF'
QUESTION: Why does sizeof(struct { char a; int b; }) equal 8 instead of 5?

EOF
$MODEL_CMD "Why does sizeof(struct { char a; int b; }) equal 8 instead of 5?" >> "$OUTPUT_DIR/01_memory_layout.txt" 2>&1
echo "✓ Saved to 01_memory_layout.txt"

# 2. Undefined Behavior Recognition
echo "⚠️  Testing: Undefined Behavior Recognition..."
cat > "$OUTPUT_DIR/02_undefined_behavior.txt" << 'EOF'
QUESTION: Is this code correct: int x = 5; int y = x++ + x++;

EOF
$MODEL_CMD "Is this code correct: int x = 5; int y = x++ + x++;" >> "$OUTPUT_DIR/02_undefined_behavior.txt" 2>&1
echo "✓ Saved to 02_undefined_behavior.txt"

# 3. Pointer Declarations (Classic confusion)
echo "🎯 Testing: Pointer Declarations..."
cat > "$OUTPUT_DIR/03_pointer_declarations.txt" << 'EOF'
QUESTION: What is the difference between int* ptr[10] and int (*ptr)[10]?

EOF
$MODEL_CMD "What is the difference between int* ptr[10] and int (*ptr)[10]?" >> "$OUTPUT_DIR/03_pointer_declarations.txt" 2>&1
echo "✓ Saved to 03_pointer_declarations.txt"

# 4. Const Correctness
echo "🔒 Testing: Const Correctness..."
cat > "$OUTPUT_DIR/04_const_correctness.txt" << 'EOF'
QUESTION: What's the difference between const int* p, int* const p, and const int* const p?

EOF
$MODEL_CMD "What's the difference between const int* p, int* const p, and const int* const p?" >> "$OUTPUT_DIR/04_const_correctness.txt" 2>&1
echo "✓ Saved to 04_const_correctness.txt"

# 5. Stack vs Heap (Dangling pointer)
echo "💾 Testing: Stack vs Heap Understanding..."
cat > "$OUTPUT_DIR/05_stack_heap.txt" << 'EOF'
QUESTION: Why does this code crash: int* f() { int x = 5; return &x; }

EOF
$MODEL_CMD "Why does this code crash: int* f() { int x = 5; return &x; }" >> "$OUTPUT_DIR/05_stack_heap.txt" 2>&1
echo "✓ Saved to 05_stack_heap.txt"

# 6. Linkage and ODR
echo "🔗 Testing: Linkage Understanding..."
cat > "$OUTPUT_DIR/06_linkage.txt" << 'EOF'
QUESTION: Why does defining a global variable in a header file cause multiple definition errors?

EOF
$MODEL_CMD "Why does defining a global variable in a header file cause multiple definition errors?" >> "$OUTPUT_DIR/06_linkage.txt" 2>&1
echo "✓ Saved to 06_linkage.txt"

# 7. Virtual Functions
echo "🎭 Testing: Virtual Function Mechanics..."
cat > "$OUTPUT_DIR/07_virtual_functions.txt" << 'EOF'
QUESTION: Why must base class destructors be virtual when using polymorphism?

EOF
$MODEL_CMD "Why must base class destructors be virtual when using polymorphism?" >> "$OUTPUT_DIR/07_virtual_functions.txt" 2>&1
echo "✓ Saved to 07_virtual_functions.txt"

# 8. Function Pointers
echo "🔧 Testing: Function Pointer Syntax..."
cat > "$OUTPUT_DIR/08_function_pointers.txt" << 'EOF'
QUESTION: How do I declare a pointer to a function that takes int and returns void?

EOF
$MODEL_CMD "How do I declare a pointer to a function that takes int and returns void?" >> "$OUTPUT_DIR/08_function_pointers.txt" 2>&1
echo "✓ Saved to 08_function_pointers.txt"

# 9. Rvalue References
echo "➡️  Testing: Move Semantics..."
cat > "$OUTPUT_DIR/09_move_semantics.txt" << 'EOF'
QUESTION: What's the difference between std::move and std::forward?

EOF
$MODEL_CMD "What's the difference between std::move and std::forward?" >> "$OUTPUT_DIR/09_move_semantics.txt" 2>&1
echo "✓ Saved to 09_move_semantics.txt"

# 10. Storage Duration
echo "⏱️  Testing: Storage Duration..."
cat > "$OUTPUT_DIR/10_storage_duration.txt" << 'EOF'
QUESTION: What happens to a static local variable between function calls?

EOF
$MODEL_CMD "What happens to a static local variable between function calls?" >> "$OUTPUT_DIR/10_storage_duration.txt" 2>&1
echo "✓ Saved to 10_storage_duration.txt"

# 11. Type Aliasing and Strict Aliasing
echo "🔀 Testing: Type Aliasing..."
cat > "$OUTPUT_DIR/11_type_aliasing.txt" << 'EOF'
QUESTION: What is strict aliasing and why does this break: int* p = (int*)&my_float;

EOF
$MODEL_CMD "What is strict aliasing and why does this break: int* p = (int*)&my_float;" >> "$OUTPUT_DIR/11_type_aliasing.txt" 2>&1
echo "✓ Saved to 11_type_aliasing.txt"

# 12. Calling Conventions
echo "📞 Testing: Calling Conventions..."
cat > "$OUTPUT_DIR/12_calling_conventions.txt" << 'EOF'
QUESTION: How are function arguments passed in x86-64 Linux?

EOF
$MODEL_CMD "How are function arguments passed in x86-64 Linux?" >> "$OUTPUT_DIR/12_calling_conventions.txt" 2>&1
echo "✓ Saved to 12_calling_conventions.txt"

# 13. Ambiguous Question (Should say "need more context")
echo "❓ Testing: Ambiguous Question Handling..."
cat > "$OUTPUT_DIR/13_ambiguous.txt" << 'EOF'
QUESTION: What is the exact type of int x[]?

EOF
$MODEL_CMD "What is the exact type of int x[]?" >> "$OUTPUT_DIR/13_ambiguous.txt" 2>&1
echo "✓ Saved to 13_ambiguous.txt"

# 14. Order of Evaluation
echo "⚡ Testing: Order of Evaluation..."
cat > "$OUTPUT_DIR/14_order_evaluation.txt" << 'EOF'
QUESTION: Is the order of evaluation guaranteed in: f(g(), h())?

EOF
$MODEL_CMD "Is the order of evaluation guaranteed in: f(g(), h())?" >> "$OUTPUT_DIR/14_order_evaluation.txt" 2>&1
echo "✓ Saved to 14_order_evaluation.txt"

# 15. Pass by Value vs Reference
echo "📤 Testing: Pass by Value vs Reference..."
cat > "$OUTPUT_DIR/15_pass_by.txt" << 'EOF'
QUESTION: When should I use pass by reference instead of pass by value?

EOF
$MODEL_CMD "When should I use pass by reference instead of pass by value?" >> "$OUTPUT_DIR/15_pass_by.txt" 2>&1
echo "✓ Saved to 15_pass_by.txt"

# 16. Reference vs Pointer
echo "🔗 Testing: Reference vs Pointer..."
cat > "$OUTPUT_DIR/16_ref_vs_ptr.txt" << 'EOF'
QUESTION: What's the fundamental difference between a reference and a pointer?

EOF
$MODEL_CMD "What's the fundamental difference between a reference and a pointer?" >> "$OUTPUT_DIR/16_ref_vs_ptr.txt" 2>&1
echo "✓ Saved to 16_ref_vs_ptr.txt"

# 17. Operator Precedence Pitfall
echo "🎲 Testing: Operator Precedence..."
cat > "$OUTPUT_DIR/17_operator_precedence.txt" << 'EOF'
QUESTION: What does *p++ do?

EOF
$MODEL_CMD "What does *p++ do?" >> "$OUTPUT_DIR/17_operator_precedence.txt" 2>&1
echo "✓ Saved to 17_operator_precedence.txt"

# 18. Multiple Inheritance Diamond
echo "💎 Testing: Multiple Inheritance..."
cat > "$OUTPUT_DIR/18_diamond_problem.txt" << 'EOF'
QUESTION: What is the diamond problem in C++ multiple inheritance?

EOF
$MODEL_CMD "What is the diamond problem in C++ multiple inheritance?" >> "$OUTPUT_DIR/18_diamond_problem.txt" 2>&1
echo "✓ Saved to 18_diamond_problem.txt"

# 19. Template Instantiation
echo "📋 Testing: Template Instantiation..."
cat > "$OUTPUT_DIR/19_templates.txt" << 'EOF'
QUESTION: Why can't I define template functions in .cpp files?

EOF
$MODEL_CMD "Why can't I define template functions in .cpp files?" >> "$OUTPUT_DIR/19_templates.txt" 2>&1
echo "✓ Saved to 19_templates.txt"

# 20. RAII and Resource Management
echo "🛡️  Testing: RAII..."
cat > "$OUTPUT_DIR/20_raii.txt" << 'EOF'
QUESTION: What is RAII and why is it important?

EOF
$MODEL_CMD "What is RAII and why is it important?" >> "$OUTPUT_DIR/20_raii.txt" 2>&1
echo "✓ Saved to 20_raii.txt"

echo ""
echo "================================"
echo "✅ Testing Complete!"
echo ""
echo "📁 Results saved to: $OUTPUT_DIR/"
echo ""
echo "To analyze results, run:"
echo "  cat $OUTPUT_DIR/*.txt | less"
echo ""
echo "Look for:"
echo "  ❌ Implementation-first answers (dumps assembly before explaining concept)"
echo "  ❌ Missing 'I need more context' on ambiguous questions"
echo "  ❌ Wrong or hallucinated information"
echo "  ❌ Overly verbose without structure"
echo "  ✅ Clear WHAT→WHY→HOW structure"
echo "  ✅ Working code examples"
echo "  ✅ Common mistakes sections"
