#!/usr/bin/env python3
"""
Grok Atomic Processor Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Processes raw content into atomic training data using X.AI's Grok AI.
"""

import json
import re
from datetime import datetime
import requests
from processors.base_processor import BaseAtomicProcessor



class GrokAtomicProcessor(BaseAtomicProcessor):
    """Processes raw content into atomic training data using Grok"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-3-mini"
        
        try:
            # Test the API key with a simple request
            self._test_connection()
            print(f"🤖 Grok AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Grok: {e}")
            raise
        super().__init__()


    def process_concept(self, concept_data, book_name="unix_env"):
        """New main entry point that includes deduplication"""
        self.current_book_name = book_name
        return self.process_concept_with_deduplication(concept_data, book_name)
    
    def _test_connection(self):
        """Test API connection"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        test_payload = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "model": self.model,
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API test failed: {response.status_code} - {response.text}")
    
    def _extract_with_ai(self, concept_data, book_name=None):
        """Transform raw concept into atomic training format"""
        
        book_context = book_name if book_name else getattr(self, 'current_book_name', 'c_programming')
        prompt = self._build_atomic_extraction_prompt(concept_data["raw_content"], book_context)
        
        try:
            response_text = self._call_grok_api(prompt)
            
            # Parse Grok's response into structured format
            parsed_concept = self._parse_grok_response(response_text)
            
            # Add metadata
            parsed_concept["extraction_metadata"] = {
                "source": "The C Programming Language - Kernighan & Ritchie",
                "page_range": concept_data["page_range"],
                "extraction_date": datetime.now().isoformat(),
                "has_code": concept_data["has_code"],
                "has_explanation": concept_data["has_explanation"]
            }
            
            return parsed_concept
            
        except Exception as e:
            print(f"Error processing concept: {e}")
            return None
    
    def _call_grok_api(self, prompt):
        """Make API call to Grok with retry logic for truncated responses"""
        import time
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0.1,
            "stream": False
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔄 GROK: Attempt {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=110
                )
                
                if response.status_code != 200:
                    raise Exception(f"Grok API call failed: {response.status_code} - {response.text}")
                
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                
                # Check if response looks complete (basic truncation detection)
                if len(content) > 100 and (content.strip().endswith('}') or content.strip().endswith('}')):
                    print(f"✅ GROK: Response looks complete ({len(content)} chars)")
                    return content
                else:
                    print(f"⚠️ GROK: Response appears truncated ({len(content)} chars), retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        continue
                        
            except Exception as e:
                print(f"❌ GROK: Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        
        # If we get here, all retries failed
        print(f"💥 GROK: All {max_retries} attempts failed")
        return content  # Return the last attempt even if truncated
    
    def _build_atomic_extraction_prompt(self, raw_content, book_context="c_programming"):
        """Build context-aware prompt for atomic concept extraction"""
    
        if book_context == "cpp_standard":
            return f"""You are a pedagogical knowledge architect creating atomic training data for AI models learning modern C++ programming.

**CRITICAL CONTEXT**: You are processing content from the ISO/IEC 14882:2014 C++ Programming Language Standard.

Focus EXCLUSIVELY on C++ language features, object-oriented programming, templates, STL, and modern C++ idioms. AVOID basic C syntax that would be better covered in C-specific resources.

**Expected C++ Concept Types:**
- Object-oriented programming (classes, inheritance, polymorphism, encapsulation)
- Template programming (function templates, class templates, specialization, metaprogramming)
- Standard Template Library (containers, algorithms, iterators, function objects)
- Modern C++ features (auto, lambdas, move semantics, smart pointers, range-based for)
- Exception handling and RAII
- Operator and function overloading
- Advanced language features (constexpr, decltype, variadic templates, concepts)

**What to AVOID extracting:**
- Basic C syntax already covered in other books
- Elementary programming concepts without C++ context
- Simple procedural programming examples

Your task: Extract this content into a SINGLE atomic C++ concept following this EXACT structure.

An atomic C++ concept contains:
1. **Concept Definition**: Clear explanation of what this C++ feature is and why it's used IN MODERN C++ PROGRAMMING
2. **Syntax**: The generalized C++ code structure/pattern
3. **Minimal Compilable Example**: Complete, runnable C++ program demonstrating ONLY this concept using modern C++ best practices
4. **Example Explanation**: How the specific C++ code demonstrates the concept and its benefits

CRITICAL REQUIREMENTS:
- Extract only ONE atomic C++ concept (the most prominent one)
- Example must be complete, compilable C++ code
- Focus on C++ features, not basic C syntax
- Use modern C++ style and best practices
- Include relevant headers and namespace usage

Return your response as valid JSON in this EXACT format:
{{
  "topic": "C++ Concept Name",
  "explanation": "Clear definition of what this C++ concept is and why it's used in modern C++ programming...",
  "syntax": "C++ syntax pattern - use modern C++ style",
  "code_example": [
    "#include <iostream>",
    "#include <vector>",
    "// modern C++ code lines...",
    "..."
  ],
  "example_explanation": "Explanation of what this specific C++ example does and how it demonstrates the concept..."
}}

CONTENT TO PROCESS:
{raw_content}

Extract the C++ concept as JSON:"""
    
        else:
            # Existing C programming prompt logic
            return f"""You are a pedagogical knowledge architect creating atomic training data for AI models learning C programming.

Your task: Extract this content into a SINGLE atomic concept following this EXACT structure.

An atomic concept contains:
1. **Concept Definition**: Clear explanation of what it is and why it's used
2. **Syntax**: The generalized code structure/pattern  
3. **Minimal Compilable Example**: Complete, runnable C program demonstrating ONLY this concept
4. **Example Explanation**: How the specific code demonstrates the concept

CRITICAL REQUIREMENTS:
- Extract only ONE atomic concept (the most prominent one)
- Example must be complete and compilable
- Focus on the core concept, avoid feature creep
- Use clear, pedagogical language

Return your response as valid JSON in this EXACT format:
{{
  "topic": "Concept Name",
  "explanation": "Clear definition of what this concept is and why it's used...",
  "syntax": "simple function signature only - no newlines or code blocks",
  "code_example": [
    "line1 of complete program",
    "line2 of complete program",
    "..."
  ],
  "example_explanation": "Explanation of what this specific example does and how it demonstrates the concept..."
}}

CONTENT TO PROCESS:
{raw_content}

Extract the atomic concept as JSON:"""
    
    def _try_complete_json(self, partial_json):
        """Try to salvage partial JSON responses"""
        print(f"🔧 GROK JSON COMPLETION: Attempting to fix partial JSON...")
        try:
            # Remove any markdown formatting
            cleaned = partial_json.replace('```json', '').replace('```', '').strip()
            
            # Try to find where it was cut off and add closing braces
            if cleaned.strip().endswith(','):
                cleaned = cleaned.strip()[:-1]  # Remove trailing comma
            
            # Count missing closing braces
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            missing_braces = open_braces - close_braces
            
            if missing_braces > 0:
                completed_json = cleaned + '}' * missing_braces
                
                # Try to parse it
                concept = json.loads(completed_json)
                
                if concept.get('topic') and concept.get('explanation'):
                    print(f"🔧 ✅ Successfully completed partial JSON from Grok")
                    return concept
                    
        except Exception as e:
            print(f"⚠️ Failed to complete Grok JSON: {type(e).__name__}: {e}")
        
        return None

    def _parse_grok_response(self, response_text):
        """Parse Grok's JSON response"""
        print(f"Full Grok response: {response_text}")
        print(f"Response length: {len(response_text)}")
        try:
            # Extract JSON from response (handle potential markdown wrapping)
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # Try to complete partial JSON
            print("⚠️ No complete JSON found, trying to complete partial...")
            completed = self._try_complete_json(response_text)
            if completed:
                return completed
                
            raise ValueError("No JSON found in response")
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            
            # Try to complete partial JSON on decode error
            print("⚠️ Trying to complete partial GROK JSON after decode error...")
            if 'json_match' in locals() and json_match:
                completed = self._try_complete_json(json_match.group())
                if completed:
                    return completed
            
            # Try the whole response
            completed = self._try_complete_json(response_text)
            if completed:
                return completed
                
            print(f"Response was: {response_text[:500]}...")
            return None