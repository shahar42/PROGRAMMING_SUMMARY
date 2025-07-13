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

# Ensure project root accessibility
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class GPT4NanoAtomicProcessor:
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
    
    def process_concept(self, concept_data):
        """
        Transform raw concept into atomic training format
        
        This method signature matches other processors for seamless integration.
        Input: concept_data dict with keys: raw_content, page_range, has_code, has_explanation
        Output: structured concept dict with standardized format
        """
        
        # Detect book context (inherit from existing system)
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
        """Get context-specific information for different books including Expert C Programming"""
        
        contexts = {
            # Expert C Programming context
            "expert_c_programming": {
                "subject": "advanced C programming techniques",
                "book_title": "Expert C Programming: Deep C Secrets",
                "level": "expert-level",
                "focus_instruction": "Focus EXCLUSIVELY on advanced C programming concepts, common pitfalls, expert techniques, and deep language insights. AVOID basic C syntax or elementary programming concepts.",
                "concept_examples": """
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
- Advanced array and string manipulation techniques""",
                "avoid_concepts": """
- Basic C syntax (hello world, simple variables, basic loops)
- Elementary programming concepts (if/else basics, simple functions)
- Basic data types without advanced context
- Simple arithmetic or basic I/O operations
- Beginner-level programming tutorials
- Basic control structures without expert insights""",
                "example_type": "Advanced C code demonstrating expert techniques, pitfalls, or deep language features"
            },
            
            # Other book contexts (copied from existing processors)
            "linkers_loaders": {
                "subject": "linking and loading",
                "book_title": "Linkers and Loaders by John Levine",
                "level": "advanced system-level",
                "focus_instruction": "Focus on concepts related to program linking, loading, object files, symbol resolution, dynamic libraries, and binary formats.",
                "concept_examples": """
- Object file formats (ELF, COFF, PE)
- Symbol tables and symbol resolution
- Relocation entries and address patching
- Dynamic vs static linking
- Shared libraries and DLLs
- Loader architecture and program loading""",
                "avoid_concepts": """
- Basic C programming concepts (variables, functions, loops)
- Simple printf or scanf examples
- Basic data types or operators""",
                "example_type": "Code demonstrating linking/loading concepts, object file analysis, or system-level examples"
            },
            
            "unix_programming": {
                "subject": "UNIX system programming",
                "book_title": "Advanced Programming in the UNIX Environment",
                "level": "system programming",
                "focus_instruction": "Focus EXCLUSIVELY on UNIX system calls, APIs, process management, file operations, and system-level programming.",
                "concept_examples": """
- System calls (open, read, write, fork, exec)
- Process management and IPC
- File descriptors and file operations
- Signal handling and process control""",
                "avoid_concepts": """
- Basic C syntax or language features
- Simple hello world programs
- Elementary programming concepts""",
                "example_type": "Code demonstrating UNIX system calls, process operations, or system-level functionality"
            },
            
            "operating_systems": {
                "subject": "operating systems",
                "book_title": "Operating Systems: Three Easy Pieces",
                "level": "operating systems",
                "focus_instruction": "Focus EXCLUSIVELY on operating system algorithms, data structures, and mechanisms.",
                "concept_examples": """
- Process and thread management
- Memory management and virtual memory
- File system implementation
- CPU scheduling algorithms""",
                "avoid_concepts": """
- Basic C programming constructs
- Elementary programming examples""",
                "example_type": "Code demonstrating OS concepts, system calls, or theoretical examples of OS mechanisms"
            },
            
            "c_programming": {
                "subject": "C programming",
                "book_title": "The C Programming Language by Kernighan & Ritchie",
                "level": "programming language",
                "focus_instruction": "Focus on C language features, syntax, standard library, and programming techniques.",
                "concept_examples": """
- C language syntax and features
- Standard library functions
- Memory management (malloc, free)
- Pointer operations and arrays""",
                "avoid_concepts": """
- System-level concepts better suited for other books""",
                "example_type": "Complete, compilable C program demonstrating the language concept"
            }
        }
        
        return contexts.get(book_context, contexts["expert_c_programming"])
    
    def _parse_gpt4_response(self, response_text):
        """Parse GPT-4's JSON response - handles both JSON and markdown-wrapped responses"""
        try:
            # Extract JSON from response (handle potential markdown wrapping)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response was: {response_text[:500]}...")
            return None
