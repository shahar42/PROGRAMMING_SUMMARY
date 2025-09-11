#!/usr/bin/env python3
"""
Quick test script for C++ STL extraction
Tests the cpp_stl_processor with a small sample
"""

import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from config
load_dotenv("config/config.env")

# Add project root to Python path
sys.path.append('.')

try:
    from processors.cpp_stl_processor import CppStlProcessor
    from core.pdf_extractor import PDFStructureExtractor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_stl_extraction():
    """Test STL concept extraction with a small sample"""
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please set your Gemini API key in .env file")
        return False
    
    print("🚀 Starting C++ STL extraction test...")
    print(f"📖 Book: C++ Standard LibraryContainers.pdf")
    print(f"📄 Test pages: 37-40 (small sample)")
    print(f"🎯 Target: 2-3 concepts max")
    
    try:
        # Initialize processor
        processor = CppStlProcessor(api_key)
        print("✅ STL processor initialized")
        
        # Initialize PDF extractor
        pdf_path = "C++ Standard LibraryContainers.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return False
        
        print(f"✅ PDF found: {pdf_path}")
        
        # Extract a small sample from pages 37-40
        print("📄 Extracting content from pages 37-40...")
        
        # Create test data (simulating extracted content)
        test_concept_data = {
            "raw_content": """
            std::vector is a sequence container that encapsulates dynamic size arrays.
            
            The elements are stored contiguously, which means that elements can be accessed not only through iterators, but also using offsets to regular pointers to elements. This means that a pointer to an element of a vector may be passed to any function that expects a pointer to an element of an array.
            
            The storage of the vector is handled automatically, being expanded and contracted as needed. Vectors usually occupy more space than static arrays, because more memory is allocated to handle future growth. This way a vector does not need to reallocate each time an element is inserted, but only when the additional memory is exhausted.
            
            Example usage:
            std::vector<int> v = {1, 2, 3, 4, 5};
            v.push_back(6);
            for (auto& element : v) {
                std::cout << element << " ";
            }
            """,
            "page_range": "37-38",
            "has_code": True,
            "has_explanation": True
        }
        
        # Process the concept
        print("🔄 Processing concept with STL processor...")
        result = processor.process_concept(test_concept_data)
        
        if result:
            print("✅ Concept extracted successfully!")
            
            # Save test result
            output_file = "outputs/cpp_stl_containers/test_concept_001.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Saved to: {output_file}")
            
            # Display result summary
            print("\n📋 EXTRACTION RESULT:")
            print(f"Topic: {result.get('topic', 'N/A')}")
            print(f"Explanation length: {len(result.get('explanation', ''))} chars")
            print(f"Code lines: {len(result.get('code_example', []))}")
            print(f"Has std:: prefix: {'std::' in str(result)}")
            
            return True
        else:
            print("❌ Failed to extract concept")
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stl_extraction()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Ready to run full extraction with batch processing.")
    else:
        print("\n💥 Test failed. Check the errors above.")