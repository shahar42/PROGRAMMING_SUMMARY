#!/usr/bin/env python3
"""
GPT-4.1 Nano Atomic Processor Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Processes raw content into atomic training data using OpenAI's GPT-4.1 Nano.
Optimized for low-latency, cost-effective concept extraction.
"""

import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path
import requests
from processors.base_processor import BaseAtomicProcessor


# Ensure project root accessibility
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class GPT4NanoAtomicProcessor(BaseAtomicProcessor):
    """Processes raw content into atomic training data using GPT-4.1 Nano"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4.1-nano"
        
        try:
            # Test the API connection
            self._test_connection()
            print(f"🤖 GPT-4.1 Nano initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize GPT-4.1 Nano: {e}")
            raise
        super().__init__()

    def process_concept(self, concept_data, book_name="expert_c_programming"):
        """New main entry point that includes deduplication"""
        return self.process_concept_with_deduplication(concept_data, book_name)
    
    def _test_connection(self):
        """Test API connection with minimal request"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"API test failed: {response.status_code} - {response.text}")
    
    def _extract_with_ai(self, concept_data, book_name=None):
            """
            Transform raw concept into atomic training format
            
            This method signature matches other processors for seamless integration.
            Input: concept_data dict with keys: raw_content, page_range, has_code, has_explanation
            Output: structured concept dict with standardized format
            """
            
            # Use explicit book_name if provided, otherwise detect from content
            if book_name:
                book_context = book_name
            else:
                source_title = concept_data.get("source_title", "")
                book_context = self._detect_book_context(source_title, concept_data.get("raw_content", ""))
            
            # Build context-aware prompt
            prompt = self._build_atomic_extraction_prompt(
                concept_data["raw_content"], 
                book_context
            )
            
            try:
                response_text = self._call_gpt4_nano_api(prompt)
                
                # Parse response into structured format
                parsed_concept = self._parse_gpt4_response(response_text)
                
                # Add standardized metadata (REQUIRED for integration)
                parsed_concept["extraction_metadata"] = {
                    "source": concept_data.get("source_title", "Unknown Source"),
                    "page_range": concept_data["page_range"],
                    "extraction_date": datetime.now().isoformat(),
                    "has_code": concept_data["has_code"],
                    "has_explanation": concept_data["has_explanation"],
                    "book_context": book_context
                }
                
                return parsed_concept
                
            except Exception as e:
                print(f"Error processing concept: {e}")
                return None
    
    def _call_gpt4_nano_api(self, prompt):
        """Make API call to GPT-4.1 Nano - optimized for cost efficiency"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,  # Reduced for nano cost optimization
            "temperature": 0.1,  # Low temperature for consistent structured output
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30  # Reduced timeout for nano's low-latency benefit
        )
        
        if response.status_code != 200:
            raise Exception(f"GPT-4.1 Nano API call failed: {response.status_code} - {response.text}")
        
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    
    def _detect_book_context(self, source_title, raw_content):
        """
        Detect which book we're processing to provide proper context
        Extended to include Expert C Programming
        """
        source_lower = source_title.lower()
        content_lower = raw_content.lower()
        
        # Book detection patterns (Expert C Programming added)
        if "expert" in source_lower and "programming" in source_lower:
            return "expert_c_programming"
        elif "linkers" in source_lower or "loaders" in source_lower:
            return "linkers_loaders"
        elif "unix" in source_lower or "environment" in source_lower:
            return "unix_programming"
        elif "operating" in source_lower or "three easy pieces" in source_lower:
            return "operating_systems"
        elif "kernighan" in source_lower or "ritchie" in source_lower:
            return "c_programming"
        
        # Content-based detection for Expert C Programming
        expert_c_indicators = ["deep dive", "pitfalls", "gotchas", "advanced c", "tricky", "expert level"]
        if any(indicator in content_lower for indicator in expert_c_indicators):
            return "expert_c_programming"
        
        # Other content-based detection
        linking_indicators = ["linker", "loader", "object file", "symbol table", "relocation"]
        unix_indicators = ["system call", "unix", "posix", "file descriptor", "process"]
        os_indicators = ["scheduler", "virtual memory", "file system", "thread", "process"]
        
        if any(indicator in content_lower for indicator in linking_indicators):
            return "linkers_loaders"
        elif any(indicator in content_lower for indicator in unix_indicators):
            return "unix_programming"
        elif any(indicator in content_lower for indicator in os_indicators):
            return "operating_systems"
        
        # Default to Expert C Programming since that's what this processor handles
        return "expert_c_programming"
    
    def _build_atomic_extraction_prompt(self, raw_content, book_context):
        """Build context-aware prompt for atomic concept extraction"""
        
        context_info = self._get_book_context_info(book_context)
        
        return f"""You are a pedagogical knowledge architect creating atomic training data for AI models learning {context_info['subject']}.

**CRITICAL CONTEXT**: You are processing content from {context_info['book_title']}.

{context_info['focus_instruction']}

**Expected Concept Types for this book:**
{context_info['concept_examples']}

**What to AVOID extracting:**
{context_info['avoid_concepts']}

Your task: Extract this content into a SINGLE atomic concept following this EXACT structure.

An atomic concept contains:
1. **Concept Definition**: Clear explanation of what it is and why it's used IN THE CONTEXT OF {context_info['subject'].upper()}
2. **Syntax**: The generalized code structure/pattern or technical specification
3. **Minimal Example**: {context_info['example_type']}
4. **Example Explanation**: How the specific example demonstrates the {context_info['subject']} concept

CRITICAL REQUIREMENTS:
- Extract only ONE atomic concept (the most prominent one FOR {context_info['subject'].upper()})
- Focus on {context_info['level']} concepts, not basic programming
- Example must demonstrate the specific {context_info['subject']} concept
- Use clear, pedagogical language appropriate for {context_info['subject']}

Return your response as valid JSON in this EXACT format:
{{
  "topic": "Concept Name",
  "explanation": "Clear definition of what this {context_info['subject']} concept is and why it's used...",
  "syntax": "technical specification or code pattern",
  "code_example": [
    "line1 of complete example",
    "line2 of complete example",
    "..."
  ],
  "example_explanation": "Explanation of what this specific example does and how it demonstrates the {context_info['subject']} concept..."
}}

CONTENT TO PROCESS:
{raw_content}

Extract the {context_info['subject']} concept as JSON:"""
    
    def _get_book_context_info(self, book_context):
        """Get context-specific information for different books including C++ Standard"""
    
        contexts = {
            # ... existing contexts ...
            "expert_c_programming": {
                "subject": "advanced C programming techniques",
                "book_title": "Expert C Programming: Deep C Secrets",
                "level": "expert-level",
                "focus_instruction": "Focus EXCLUSIVELY on advanced C programming concepts, common pitfalls, expert techniques, and deep language insights. AVOID basic C syntax or elementary programming concepts.",
                "concept_examples": '''
- Advanced pointer techniques and pointer arithmetic
- C memory model and storage classes (auto, static, extern, register)
- Complex declaration parsing and precedence rules
- Function pointers and callback mechanisms
- Advanced struct and union usage patterns
- C preprocessor advanced techniques and gotchas
- Undefined behavior and implementation-defined behavior
- Advanced linking concepts (weak symbols, aliases)
- C runtime environment and startup code
- Expert debugging techniques and common pitfalls
- Performance optimization techniques in C
- Advanced array and string manipulation techniques''',
                "avoid_concepts": '''
- Basic C syntax (hello world, simple variables, basic loops)
- Elementary programming concepts (if/else basics, simple functions)
- Basic data types without advanced context
- Simple arithmetic or basic I/O operations
- Beginner-level programming tutorials
- Basic control structures without expert insights''',
                "example_type": "Advanced C code demonstrating expert techniques, pitfalls, or deep language features"
            },
            
            "linkers_loaders": {
                "subject": "linking and loading",
                "book_title": "Linkers and Loaders by John Levine",
                "level": "advanced system-level",
                "focus_instruction": "Focus on concepts related to program linking, loading, object files, symbol resolution, dynamic libraries, and binary formats.",
                "concept_examples": '''
- Object file formats (ELF, COFF, PE)
- Symbol tables and symbol resolution
- Relocation entries and address patching
- Dynamic vs static linking
- Shared libraries and DLLs
- Loader architecture and program loading''',
                "avoid_concepts": '''
- Basic C programming concepts (variables, functions, loops)
- Simple printf or scanf examples
- Basic data types or operators''',
                "example_type": "Code demonstrating linking/loading concepts, object file analysis, or system-level examples"
            },
            
            "unix_programming": {
                "subject": "UNIX system programming",
                "book_title": "Advanced Programming in the UNIX Environment",
                "level": "system programming",
                "focus_instruction": "Focus EXCLUSIVELY on UNIX system calls, APIs, process management, file operations, and system-level programming.",
                "concept_examples": '''
- System calls (open, read, write, fork, exec)
- Process management and IPC
- File descriptors and file operations
- Signal handling and process control''',
                "avoid_concepts": '''
- Basic C syntax or language features
- Simple hello world programs
- Elementary programming concepts''',
                "example_type": "Code demonstrating UNIX system calls, process operations, or system-level functionality"
            },
            
            "operating_systems": {
                "subject": "operating systems",
                "book_title": "Operating Systems: Three Easy Pieces",
                "level": "operating systems",
                "focus_instruction": "Focus EXCLUSIVELY on operating system algorithms, data structures, and mechanisms.",
                "concept_examples": '''
- Process and thread management
- Memory management and virtual memory
- File system implementation
- CPU scheduling algorithms''',
                "avoid_concepts": '''
- Basic C programming constructs
- Elementary programming examples''',
                "example_type": "Code demonstrating OS concepts, system calls, or theoretical examples of OS mechanisms"
            },
            
            "c_programming": {
                "subject": "C programming",
                "book_title": "The C Programming Language by Kernighan & Ritchie",
                "level": "programming language",
                "focus_instruction": "Focus on C language features, syntax, standard library, and programming techniques.",
                "concept_examples": '''
- C language syntax and features
- Standard library functions
- Memory management (malloc, free)
- Pointer operations and arrays''',
                "avoid_concepts": '''
- System-level concepts better suited for other books''',
                "example_type": "Complete, compilable C program demonstrating the language concept"
            },
        
            # NEW: C++ Standard context  
            "cpp_standard": {
                "subject": "C++ programming language",
                "book_title": "ISO/IEC 14882:2014 C++ Programming Language Standard",
                "level": "comprehensive and modern",
                "focus_instruction": "Focus EXCLUSIVELY on C++ language features, object-oriented programming, templates, STL, and modern C++ idioms (C++11/14 and beyond). AVOID basic C syntax.",
                "concept_examples": '''
- Object-oriented programming (classes, constructors, destructors, inheritance, virtual functions)
- Template programming (function templates, class templates, template specialization, SFINAE)
- Standard Template Library (std::vector, std::map, algorithms, iterators)
- Modern C++ features (auto keyword, lambda expressions, move semantics, smart pointers)
- Exception handling (try/catch blocks, RAII pattern)
- Operator overloading and function overloading
- Namespaces and scope resolution (std::, using declarations)
- Advanced features (constexpr, decltype, variadic templates, perfect forwarding)''',
                "avoid_concepts": '''
- Basic C syntax without C++ context
- Simple procedural programming
- Elementary concepts better suited for C books''',
                "example_type": "Complete, compilable C++ program using modern C++ features and best practices"
            },
            
            # NEW: Inside the C++ Object Model context
            "Inside_the_C++_Object_Model": {
                "subject": "C++ object model internals",
                "book_title": "Inside the C++ Object Model by Stanley Lippman",
                "level": "expert implementation details",
                "focus_instruction": "Focus EXCLUSIVELY on C++ object model internals, memory layout, vtable mechanisms, constructor/destructor implementation, and compiler behavior. AVOID surface-level language features.",
                "concept_examples": '''
- Object memory layout and data member arrangement
- Virtual function table (vtable) implementation and dispatch
- Constructor and destructor calling sequences and optimization
- Virtual base class implementation and memory management
- Member function call mechanisms (this pointer manipulation)
- Inheritance models (single, multiple, virtual inheritance)
- RTTI (Run-Time Type Information) implementation details
- Template instantiation and code generation
- Exception handling implementation mechanisms
- Copy constructor and assignment operator implementation
- Temporary object creation and optimization (RVO, NRVO)
- Name mangling and linkage considerations''',
                "avoid_concepts": '''
- Basic C++ syntax or language features without implementation details
- Surface-level OOP concepts without memory layout discussion
- Simple class examples without internals explanation
- Template syntax without instantiation mechanics''',
                "example_type": "C++ code with detailed analysis of memory layout, compiler behavior, or runtime mechanisms"
            }
        
            # ... rest of existing contexts ...
        }
    
        return contexts.get(book_context, contexts["expert_c_programming"])
    
    def _parse_gpt4_response(self, response_text):
        """Parse GPT-4's JSON response - handles both JSON and markdown-wrapped responses"""
        print(f"🐛 DEBUG - Raw GPT response ({len(response_text)} chars): {response_text}")
        try:
            # First try to find JSON wrapped in markdown code blocks
            markdown_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if markdown_match:
                json_str = markdown_match.group(1).strip()
                print(f"🐛 DEBUG - Extracted from markdown ({len(json_str)} chars): {json_str[:200]}...")
                return json.loads(json_str)
            
            # Try to find a complete JSON object starting with { and ending with }
            start_pos = response_text.find('{')
            if start_pos == -1:
                raise ValueError("No opening brace found in response")
            
            # Count braces to find matching closing brace
            brace_count = 0
            end_pos = -1
            for i, char in enumerate(response_text[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            if end_pos != -1:
                json_str = response_text[start_pos:end_pos + 1]
                print(f"🐛 DEBUG - Extracted JSON string ({len(json_str)} chars): {json_str[:200]}...")
                return json.loads(json_str)
            else:
                print("🐛 DEBUG - No matching closing brace found")
                raise ValueError("No complete JSON object found")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from GPT: {e}")
            print(f"🐛 DEBUG - Problematic JSON string: {json_str[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Error parsing GPT response: {e}")
            return None
