#!/usr/bin/env python3
"""
Improve V7 validation set with strategic examples:
1. Critical test cases (V6 failures)
2. Edge cases (complex structs, unusual patterns)
3. Harder examples (multi-step reasoning)
4. Out-of-distribution (ambiguous, calibration tests)
5. Adversarial examples (contradictory-sounding)
"""

import json
import random
from typing import List, Dict

def load_datasets():
    """Load current train and val datasets"""
    with open('fine_tuning_llama_v7_sizeof/train.json', 'r') as f:
        train_data = json.load(f)
    with open('fine_tuning_llama_v7_sizeof/val.json', 'r') as f:
        val_data = json.load(f)
    return train_data, val_data

def create_system_message():
    """Standard system message"""
    return {
        "role": "system",
        "content": "You are a C/C++ systems programming expert. Provide precise, technically accurate explanations based on authoritative sources (K&R C, C++ Standard, C++ Primer, CSAPP). Focus on implementation details, compiler behavior, and standard-defined semantics. Avoid speculation or creative interpretation."
    }

def find_critical_examples(train_data: List[Dict]) -> List[Dict]:
    """Find V6's critical failure cases in training data"""
    critical_patterns = [
        'sizeof(struct { char a; int b; })',
        'sizeof(int[3])',
        'sizeof(struct { int a; char b; })',
        'sizeof(struct { char a; long b; })',
        'sizeof(struct { char a; double b; })',
    ]

    critical_examples = []
    for pattern in critical_patterns:
        for ex in train_data:
            for msg in ex.get('messages', []):
                if msg['role'] == 'user' and pattern in msg['content']:
                    critical_examples.append(ex)
                    print(f"  ✅ Found: {pattern}")
                    break
            if len([e for e in critical_examples if pattern in str(e)]) > 0:
                break

    return critical_examples

def find_edge_case_examples(train_data: List[Dict]) -> List[Dict]:
    """Find edge cases: complex structs, nested types, unusual patterns"""
    edge_patterns = [
        'void (*[',  # Array of function pointers
        '***',       # Triple pointers
        'union',     # Unions
        'nested',    # Nested structures
        'alignment', # Alignment issues
        'padding',   # Struct padding
        'volatile',  # Volatile keyword
        'restrict',  # Restrict keyword
        'bit field', # Bit fields
        'flexible array', # Flexible array members
        'errno',     # Error handling
        'EINVAL',    # Specific error codes
        'signal',    # Signal handling
        'fork',      # Process control
        'mmap',      # Memory mapping
    ]

    edge_examples = []
    seen_patterns = set()

    for ex in train_data:
        for msg in ex.get('messages', []):
            if msg['role'] == 'user':
                user_msg = msg['content'].lower()
                for pattern in edge_patterns:
                    if pattern in user_msg and pattern not in seen_patterns:
                        edge_examples.append(ex)
                        seen_patterns.add(pattern)
                        print(f"  ✅ Found edge case: {pattern}")
                        break
                if len(edge_examples) >= 30:  # Limit edge cases
                    break
        if len(edge_examples) >= 30:
            break

    return edge_examples

def find_hard_examples(train_data: List[Dict]) -> List[Dict]:
    """Find harder examples: multi-step reasoning, complex explanations"""
    hard_examples = []

    for ex in train_data:
        for msg in ex.get('messages', []):
            if msg['role'] == 'assistant':
                content = msg['content']
                # Heuristics for complexity:
                # 1. Long answers (detailed explanations)
                # 2. Code examples
                # 3. Multiple sections
                if (len(content) > 2500 and
                    '```' in content and
                    content.count('\n\n') > 4):
                    hard_examples.append(ex)
                    break

        if len(hard_examples) >= 50:
            break

    print(f"  ✅ Found {len(hard_examples)} hard examples (long, detailed)")
    return hard_examples

def create_calibration_examples() -> List[Dict]:
    """Create out-of-distribution calibration examples"""
    system = create_system_message()

    calibration_examples = [
        # Ambiguous questions
        {
            "messages": [
                system,
                {"role": "user", "content": "What is the type of int arr[]?"},
                {"role": "assistant", "content": "I need more context to provide a precise answer. The type of `int arr[]` depends on where it appears:\n\n1. **In a function parameter**: `void foo(int arr[])` - `arr` is actually `int*` (pointer to int), not an array. Array-to-pointer decay occurs.\n\n2. **As an incomplete type**: If declared without size and no initializer (e.g., `extern int arr[];`), it's an incomplete array type that must be defined elsewhere.\n\n3. **With an initializer**: If `int arr[] = {1, 2, 3};`, the compiler deduces the size, making it `int[3]`.\n\nCould you clarify the context where `int arr[]` appears?"}
            ]
        },
        # Out-of-scope questions
        {
            "messages": [
                system,
                {"role": "user", "content": "How do I center a div in CSS?"},
                {"role": "assistant", "content": "That's a CSS/web development question, which is outside my area of expertise. I specialize in C/C++ systems programming, compiler behavior, and low-level implementation details.\n\nFor CSS questions, I'd recommend consulting CSS documentation or web development resources."}
            ]
        },
        # Future standards
        {
            "messages": [
                system,
                {"role": "user", "content": "What are the new features in C++26?"},
                {"role": "assistant", "content": "C++26 is still under development, and I don't have verified information about finalized features. My knowledge is based on established standards (C++98 through C++23) and authoritative sources.\n\nFor up-to-date information on C++26 proposals, I recommend checking:\n- https://isocpp.org/ (ISO C++ Standards Committee)\n- https://en.cppreference.com/w/cpp/compiler_support\n\nIf you have questions about C++23 or earlier standards, I'd be happy to help with those."}
            ]
        },
        # Platform-specific ambiguity
        {
            "messages": [
                system,
                {"role": "user", "content": "What is sizeof(long)?"},
                {"role": "assistant", "content": "**The answer depends on the platform:**\n\n- **On x86-64 Linux (LP64)**: sizeof(long) = **8 bytes**\n- **On x86-64 Windows (LLP64)**: sizeof(long) = **4 bytes**\n- **On 32-bit systems (ILP32)**: sizeof(long) = **4 bytes**\n\nThe C standard only guarantees:\n- sizeof(char) ≤ sizeof(short) ≤ sizeof(int) ≤ sizeof(long) ≤ sizeof(long long)\n- sizeof(long) ≥ 4 bytes\n\n**To verify on your platform:**\n```c\n#include <stdio.h>\nint main() {\n    printf(\"%zu\\n\", sizeof(long));\n    return 0;\n}\n```\n\nIf you're assuming a specific platform, please let me know which one."}
            ]
        },
        # Contradictory-sounding pattern
        {
            "messages": [
                system,
                {"role": "user", "content": "Is `const int* p` a pointer to const or a const pointer?"},
                {"role": "assistant", "content": "**`const int* p` is a pointer to const int** (the pointer itself is NOT const).\n\n**WHAT:**\n- You can modify `p` (point it to a different int)\n- You CANNOT modify `*p` (the int it points to)\n\n**Read it right-to-left:** \"p is a pointer to int that is const\"\n\n**Example:**\n```c\nint x = 10, y = 20;\nconst int* p = &x;\np = &y;   // ✅ OK - changing what p points to\n*p = 30;  // ❌ ERROR - cannot modify through const pointer\n```\n\n**Common confusion:**\n- `const int* p` = pointer to const int (pointer is mutable)\n- `int* const p` = const pointer to int (pointed-to data is mutable)\n- `const int* const p` = const pointer to const int (both immutable)"}
            ]
        },
    ]

    print(f"  ✅ Created {len(calibration_examples)} calibration examples")
    return calibration_examples

def create_adversarial_examples() -> List[Dict]:
    """Create adversarial examples that test common misconceptions"""
    system = create_system_message()

    adversarial = [
        # Common beginner mistakes
        {
            "messages": [
                system,
                {"role": "user", "content": "Does `char* p = \"hello\";` allocate memory on the heap?"},
                {"role": "assistant", "content": "**No, it does NOT allocate on the heap.**\n\n**WHAT:**\nThe string literal `\"hello\"` is stored in **read-only data segment** (.rodata), not on the heap or stack. The pointer `p` points to this static string.\n\n**WHY this matters:**\n```c\nchar* p = \"hello\";\np[0] = 'H';  // ❌ UNDEFINED BEHAVIOR - modifying read-only memory\n```\n\n**Correct alternatives:**\n1. **For read-only:** `const char* p = \"hello\";` (preferred)\n2. **For mutable:** `char p[] = \"hello\";` (copies to stack array)\n3. **For heap:** `char* p = malloc(6); strcpy(p, \"hello\");`\n\n**Common mistake:** Beginners think string literals are on the heap because they use pointers, but string literals have **static storage duration** (exist for program lifetime)."}
            ]
        },
        # Operator precedence trap
        {
            "messages": [
                system,
                {"role": "user", "content": "What is the type of `int *p[10]`?"},
                {"role": "assistant", "content": "**`int *p[10]` is an array of 10 pointers to int** (NOT a pointer to an array).\n\n**WHAT:**\n- Type: `int*[10]` (array of 10 int pointers)\n- Size: `sizeof(p) = 10 * sizeof(int*) = 80 bytes` on x86-64\n\n**WHY (operator precedence):**\n`[]` binds tighter than `*`, so:\n- `int *p[10]` = `int *(p[10])` = array of pointers\n- `int (*p)[10]` = pointer to array (note the parentheses!)\n\n**Example:**\n```c\nint *p[10];     // Array of 10 pointers\np[0] = &x;      // OK - p[0] is an int*\nint (*q)[10];   // Pointer to array of 10 ints\nq = &arr;       // OK - q points to entire array\n```\n\n**Common mistake:** Confusing `int *p[10]` with `int (*p)[10]` due to operator precedence."}
            ]
        },
    ]

    print(f"  ✅ Created {len(adversarial)} adversarial examples")
    return adversarial

def stratified_sample(train_data: List[Dict], current_val: List[Dict], target_size: int) -> List[Dict]:
    """Sample remaining validation examples with topic diversity"""
    # Categories to ensure coverage
    categories = {
        'pointers': ['pointer', '*', 'dereference', 'address'],
        'memory': ['malloc', 'free', 'new', 'delete', 'heap', 'stack'],
        'classes': ['class', 'struct', 'member', 'constructor', 'destructor'],
        'templates': ['template', 'generic', 'typename'],
        'inheritance': ['virtual', 'override', 'polymorphism', 'base class'],
        'concurrency': ['thread', 'mutex', 'atomic', 'race condition'],
        'io': ['iostream', 'printf', 'scanf', 'file'],
        'stl': ['vector', 'map', 'set', 'algorithm', 'iterator'],
    }

    category_samples = {cat: [] for cat in categories}
    uncategorized = []

    # Exclude already selected examples
    current_val_set = set(json.dumps(ex, sort_keys=True) for ex in current_val)

    for ex in train_data:
        if json.dumps(ex, sort_keys=True) in current_val_set:
            continue

        for msg in ex.get('messages', []):
            if msg['role'] == 'user':
                user_msg = msg['content'].lower()
                categorized = False

                for cat, keywords in categories.items():
                    if any(kw in user_msg for kw in keywords):
                        category_samples[cat].append(ex)
                        categorized = True
                        break

                if not categorized:
                    uncategorized.append(ex)
                break

    # Sample proportionally from each category
    samples_per_cat = target_size // len(categories)
    stratified = []

    for cat, examples in category_samples.items():
        if examples:
            sample_size = min(samples_per_cat, len(examples))
            stratified.extend(random.sample(examples, sample_size))
            print(f"  ✅ Sampled {sample_size} from '{cat}' category")

    # Fill remaining with uncategorized
    remaining = target_size - len(stratified)
    if remaining > 0 and uncategorized:
        stratified.extend(random.sample(uncategorized, min(remaining, len(uncategorized))))

    return stratified

def main():
    print("🔧 IMPROVING V7 VALIDATION SET")
    print("="*80)

    # Load datasets
    print("\n📂 Loading datasets...")
    train_data, val_data = load_datasets()
    print(f"  Current train: {len(train_data)}")
    print(f"  Current val: {len(val_data)}")

    # Backup original validation
    print("\n💾 Backing up original validation set...")
    with open('fine_tuning_llama_v7_sizeof/val_original.json', 'w') as f:
        json.dump(val_data, f, indent=2)
    print("  ✅ Saved to val_original.json")

    # Build improved validation set
    new_val = []

    # 1. Critical test cases (V6 failures)
    print("\n🎯 Finding critical test cases...")
    critical = find_critical_examples(train_data)
    new_val.extend(critical)
    print(f"  Added {len(critical)} critical examples")

    # 2. Edge cases
    print("\n⚠️  Finding edge cases...")
    edge = find_edge_case_examples(train_data)
    new_val.extend(edge)
    print(f"  Added {len(edge)} edge case examples")

    # 3. Hard examples
    print("\n🧠 Finding hard examples...")
    hard = find_hard_examples(train_data)
    new_val.extend(hard)
    print(f"  Added {len(hard)} hard examples")

    # 4. Calibration examples
    print("\n🎓 Creating calibration examples...")
    calibration = create_calibration_examples()
    new_val.extend(calibration)
    print(f"  Added {len(calibration)} calibration examples")

    # 5. Adversarial examples
    print("\n🥊 Creating adversarial examples...")
    adversarial = create_adversarial_examples()
    new_val.extend(adversarial)
    print(f"  Added {len(adversarial)} adversarial examples")

    # 6. Stratified sample for diversity
    print("\n🎨 Stratified sampling for topic diversity...")
    current_val_size = len(new_val)
    target_remaining = 1144 - current_val_size  # Keep same total size

    if target_remaining > 0:
        stratified = stratified_sample(train_data, new_val, target_remaining)
        new_val.extend(stratified)
        print(f"  Added {len(stratified)} stratified examples")

    # Remove duplicates
    print("\n🔍 Removing duplicates...")
    seen = set()
    unique_val = []
    for ex in new_val:
        key = json.dumps(ex, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique_val.append(ex)

    print(f"  Removed {len(new_val) - len(unique_val)} duplicates")
    new_val = unique_val

    # Save improved validation set
    print(f"\n💾 Saving improved validation set...")
    with open('fine_tuning_llama_v7_sizeof/val.json', 'w') as f:
        json.dump(new_val, f, indent=2)

    print(f"\n{'='*80}")
    print("✅ VALIDATION SET IMPROVED!")
    print(f"{'='*80}")
    print(f"Original size: {len(val_data)}")
    print(f"New size: {len(new_val)}")
    print(f"\nBreakdown:")
    print(f"  Critical test cases: {len(critical)}")
    print(f"  Edge cases: {len(edge)}")
    print(f"  Hard examples: {len(hard)}")
    print(f"  Calibration: {len(calibration)}")
    print(f"  Adversarial: {len(adversarial)}")
    print(f"  Stratified samples: {len(new_val) - len(critical) - len(edge) - len(hard) - len(calibration) - len(adversarial)}")
    print(f"\n📊 Split ratio: {len(train_data)/(len(train_data)+len(new_val)):.1%} train / {len(new_val)/(len(train_data)+len(new_val)):.1%} val")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    random.seed(42)  # Reproducibility
    main()
