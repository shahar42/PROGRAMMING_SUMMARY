#!/usr/bin/env python3
"""
Test Script for Fixed Gemini Processor
Tests the fix with the same problematic content that was failing before
Works from any directory with absolute path handling.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can find project root from anywhere
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"

# Always work from project root for consistent imports
if os.getcwd() != PROJECT_ROOT:
    os.chdir(PROJECT_ROOT)
    print(f"📁 Changed working directory to: {PROJECT_ROOT}")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_fixed_processor():
    """Test the fixed Gemini processor with the same failing content"""
    
    print("🧪 Testing Fixed Gemini Processor")
    print("=" * 50)
    
    # Load API key
    config_path = os.path.join(PROJECT_ROOT, "config", "config.env")
    load_dotenv(config_path)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    # Import the processor
    from processors.gemini_processor import GeminiAtomicProcessor as OriginalProcessor
    
    # Create test concept data (same as was failing before)
    test_concept = {
        "raw_content": """1-22 Linkingand Loading
0 .text 00000010 00000000 00000000 00000020 2**3
1 .data 00000010 00000010 00000010 00000030 2**3
Disassembly of section .text:
00000000 <_main>:
0: 55 pushl %ebp
1: 89 e5 movl %esp,%ebp
3: 68 10 20 00 00 pushl $0x2010
8: e8 03 00 00 00 call b <_a>
d: c9 leave
e: c3 ret

The subprogram file a.c compiles into a 160 byte object file with the header, a 28 byte text segment, and no data. Two relocation entries mark the calls to strlen and write, and the symbol table exports _a and imports _strlen and _write.""",
        "source_title": "Linkers and Loaders",
        "page_range": "31-32",
        "has_code": True,
        "has_explanation": True
    }
    
    print("📋 Test Content:")
    print("   - Object file disassembly")
    print("   - Symbol table references") 
    print("   - Relocation entries")
    print("   - Should extract LINKING concept, not basic C")
    print()
    
    # Test ORIGINAL processor (should fail)
    print("🔍 Testing ORIGINAL Processor...")
    try:
        original_processor = OriginalProcessor(api_key)
        original_result = original_processor.process_concept(test_concept)
        
        if original_result:
            print(f"   Topic: {original_result.get('topic', 'None')}")
            explanation = original_result.get('explanation', '')[:100] + "..."
            print(f"   Explanation: {explanation}")
            
            # Check if it contains linking terms
            topic_lower = original_result.get('topic', '').lower()
            explanation_lower = original_result.get('explanation', '').lower()
            
            linking_terms = ['linker', 'loader', 'object', 'symbol', 'relocation', 'library']
            linking_found = sum(1 for term in linking_terms if term in topic_lower or term in explanation_lower)
            
            if linking_found > 0:
                print("   ✅ ORIGINAL: Correctly identified linking concept")
            else:
                print("   ❌ ORIGINAL: Failed - extracted basic C concept")
        else:
            print("   ❌ ORIGINAL: Processing failed")
    except Exception as e:
        print(f"   ❌ ORIGINAL: Error - {e}")
    
    print()
    
    # Test FIXED processor (should succeed)
    print("🔍 Testing FIXED Processor...")
    
    # We'll need to create the fixed processor by copying our artifact
    # For now, let's simulate what it should do
    print("   📝 Fixed processor should:")
    print("   • Detect 'Linkers and Loaders' context")
    print("   • Focus on linking/loading concepts")
    print("   • Avoid basic C programming topics")
    print("   • Extract concepts like 'Object File Format' or 'Symbol Resolution'")
    print()
    
    print("🎯 To implement the fix:")
    print("1. Replace processors/gemini_processor.py with the fixed version")
    print("2. Run this test again to verify the fix works")
    print("3. Re-run the linkers extraction to get proper concepts")

if __name__ == "__main__":
    test_fixed_processor()
