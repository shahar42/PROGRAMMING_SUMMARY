#!/usr/bin/env python3
"""
C++ STL Container Processor
Enhanced processor specifically for extracting C++ Standard Library container concepts
from "C++ Standard LibraryContainers.pdf" (pages 37-407)

Based on cpp_stl_concept_guidelines.md
"""

import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from processors.base_processor import BaseAtomicProcessor

# Ensure project root access
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class CppStlProcessor(BaseAtomicProcessor):
    """Specialized processor for C++ STL container concepts"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"🤖 C++ STL Processor initialized with Gemini 1.5 Flash")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            raise
        super().__init__()

    def _extract_with_ai(self, concept_data, book_name="cpp_stl_containers"):
        """Extract concept using AI with STL-specific processing"""
        return self.process_concept(concept_data)

    def process_concept(self, concept_data):
        """Extract single STL concept using specialized prompt"""
        
        prompt = self._build_stl_extraction_prompt(concept_data["raw_content"])
        
        try:
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                print(f"❌ Empty response from Gemini")
                return None
                
            parsed_result = self._parse_gemini_response(response.text)
            if parsed_result:
                # Add extraction metadata
                parsed_result["extraction_metadata"] = {
                    "source": "C++ Standard Library Containers",
                    "page_range": concept_data.get("page_range", "unknown"),
                    "extraction_date": datetime.now().isoformat(),
                    "processor": "cpp_stl_processor",
                    "has_code": bool(parsed_result.get("code_example")),
                    "has_explanation": bool(parsed_result.get("explanation"))
                }
                return parsed_result
            return None
            
        except Exception as e:
            print(f"❌ Error during STL concept extraction: {e}")
            return None

    def _build_stl_extraction_prompt(self, raw_content):
        """Build specialized prompt for STL container concept extraction"""
        
        return f"""You are a C++ STL expert creating atomic training data for developers learning the Standard Template Library.

Your task: Extract this content into a SINGLE atomic STL concept following this EXACT structure.

An atomic STL concept contains:
1. **STL Concept Definition**: Clear explanation of what this container/algorithm/iterator feature is and why it's used IN MODERN C++ PROGRAMMING
2. **Syntax**: The generalized C++ STL syntax pattern
3. **Complete Example**: Compilable C++ program demonstrating ONLY this STL concept using modern C++ best practices
4. **Example Explanation**: How the specific STL code demonstrates the concept and its practical benefits

CRITICAL REQUIREMENTS FOR STL CONCEPTS:
- Extract only ONE atomic STL concept (most prominent container/algorithm/iterator feature)
- Focus on PRACTICAL STL usage, not basic C++ syntax
- Example must be complete, compilable C++ code with proper headers
- Use modern C++ style (auto, range-based loops, std:: prefix)
- Demonstrate REALISTIC use cases, not contrived examples

STL CONCEPT CATEGORIES TO FOCUS ON:
✅ Container operations (push_back, insert, erase, emplace)
✅ Iterator usage (begin/end, iterator arithmetic, range-based loops)  
✅ Algorithm applications (sort, find, transform, for_each)
✅ Smart pointer usage (unique_ptr, shared_ptr, RAII patterns)
✅ Container-specific features (vector growth, map lookups, set uniqueness)

❌ AVOID THESE (not STL-focused):
❌ Basic C++ syntax (variables, if/else, basic loops)
❌ Object-oriented concepts (inheritance, virtual functions)
❌ Template metaprogramming theory
❌ Low-level memory management without STL context

NAMING GUIDELINES:
- Use specific STL component names: "std::vector push_back", "std::sort with comparator"
- Focus on the operation/feature, not just the container type
- Be precise: "Range-based for loop with containers" not just "for loops"

RESPONSE FORMAT:
{{
  "topic": "std::vector push_back Operation",
  "explanation": "The push_back() method adds elements to the end of a std::vector, automatically managing memory reallocation when capacity is exceeded. This is the most common and efficient way to dynamically grow a vector during runtime.",
  "syntax": "vector.push_back(element);",
  "code_example": [
    "#include <iostream>",
    "#include <vector>",
    "",
    "int main() {{",
    "    std::vector<int> numbers;",
    "    numbers.push_back(10);",
    "    numbers.push_back(20);",
    "    ",
    "    for (const auto& num : numbers) {{",
    "        std::cout << num << \" \";",
    "    }}",
    "    return 0;",
    "}}"
  ],
  "example_explanation": "This program demonstrates push_back() by adding integers to an empty vector. The vector automatically reallocates memory as needed. The range-based for loop safely iterates through all elements without manual iterator management."
}}

CONTENT TO PROCESS:
{raw_content}

Extract the most prominent STL concept as JSON:"""

    def _parse_gemini_response(self, response_text):
        """Parse and validate Gemini's JSON response for STL concepts"""
        try:
            # Clean response text
            cleaned = response_text.replace('```json', '').replace('```', '').strip()
            
            # Handle potential markdown or extra text
            if '{' in cleaned and '}' in cleaned:
                start_idx = cleaned.find('{')
                end_idx = cleaned.rfind('}') + 1
                json_text = cleaned[start_idx:end_idx]
            else:
                json_text = cleaned
            
            # Parse JSON
            result = json.loads(json_text)
            
            # Validate required fields for STL concepts
            required_fields = ["topic", "explanation", "syntax", "code_example", "example_explanation"]
            for field in required_fields:
                if field not in result:
                    print(f"❌ Missing required field: {field}")
                    return None
            
            # Validate STL-specific requirements
            if not self._validate_stl_concept(result):
                return None
                
            print(f"✅ Successfully extracted STL concept: {result['topic']}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response preview: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return None

    def _validate_stl_concept(self, concept):
        """Validate that the concept is STL-focused and well-formed"""
        
        topic = concept.get("topic", "").lower()
        explanation = concept.get("explanation", "").lower()
        code_example = concept.get("code_example", [])
        
        # Check for STL indicators
        stl_indicators = [
            "std::", "vector", "map", "set", "list", "deque", "array",
            "iterator", "algorithm", "push_back", "insert", "erase",
            "begin", "end", "find", "sort", "unique_ptr", "shared_ptr"
        ]
        
        has_stl_focus = any(indicator in topic or indicator in explanation 
                           for indicator in stl_indicators)
        
        if not has_stl_focus:
            print(f"⚠️  Concept may not be STL-focused: {concept.get('topic')}")
            # Don't reject, but flag for review
        
        # Validate code example has proper includes
        code_text = "\n".join(code_example) if isinstance(code_example, list) else str(code_example)
        
        has_includes = "#include" in code_text
        has_main = "int main(" in code_text or "main()" in code_text
        
        if not has_includes or not has_main:
            print(f"⚠️  Code example may not be complete: missing includes or main function")
            return False
        
        return True

if __name__ == "__main__":
    print("C++ STL Container Processor - Use via extraction scripts")
    print("See cpp_stl_concept_guidelines.md for concept definitions")