#!/usr/bin/env python3
"""
Enhanced Gemini Atomic Processor Module
FIXED: Now includes book context awareness for proper concept extraction

Processes raw content into atomic training data using Google's Gemini AI.
Works from any directory with absolute path handling.
"""

import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

# Ensure we can find project root from anywhere
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class GeminiAtomicProcessor:
    """Processes raw content into atomic training data using Gemini"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"🤖 Gemini 1.5 Flash initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            raise
    
    def process_concept(self, concept_data):
        """Transform raw concept into atomic training format"""
        
        # Detect book context from metadata
        source_title = concept_data.get("source_title", "")
        book_context = self._detect_book_context(source_title, concept_data.get("raw_content", ""))
        
        prompt = self._build_atomic_extraction_prompt(
            concept_data["raw_content"], 
            book_context
        )
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse Gemini's response into structured format
            parsed_concept = self._parse_gemini_response(response.text)
            
            # Add metadata
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
    
    def _detect_book_context(self, source_title, raw_content):
        """Detect which book we're processing to provide proper context"""
        source_lower = source_title.lower()
        content_lower = raw_content.lower()
        
        # Book detection patterns
        if "linkers" in source_lower or "loaders" in source_lower:
            return "linkers_loaders"
        elif "unix" in source_lower or "environment" in source_lower:
            return "unix_programming"
        elif "operating" in source_lower or "three easy pieces" in source_lower:
            return "operating_systems"
        elif "kernighan" in source_lower or "ritchie" in source_lower:
            return "c_programming"
        
        # Content-based detection as fallback
        linking_indicators = ["linker", "loader", "object file", "symbol table", "relocation", "dynamic linking"]
        unix_indicators = ["system call", "unix", "posix", "file descriptor", "process"]
        os_indicators = ["scheduler", "virtual memory", "file system", "thread", "process"]
        
        if any(indicator in content_lower for indicator in linking_indicators):
            return "linkers_loaders"
        elif any(indicator in content_lower for indicator in unix_indicators):
            return "unix_programming"
        elif any(indicator in content_lower for indicator in os_indicators):
            return "operating_systems"
        
        # Default to C programming
        return "c_programming"
    
    def _build_atomic_extraction_prompt(self, raw_content, book_context):
        """Build context-aware prompt for atomic concept extraction"""
        
        # Get book-specific context
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
        """Get context-specific information for different books"""
        
        contexts = {
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
- Loader architecture and program loading
- Application Binary Interfaces (ABI)
- Position Independent Code (PIC)
- Global Offset Table (GOT)
- Procedure Linkage Table (PLT)""",
                "avoid_concepts": """
- Basic C programming concepts (variables, functions, loops)
- Simple printf or scanf examples
- Basic data types or operators
- Elementary control structures""",
                "example_type": "Code demonstrating linking/loading concepts, object file analysis, or system-level examples"
            },
            
            "unix_programming": {
                "subject": "UNIX system programming",
                "book_title": "Advanced Programming in the UNIX Environment",
                "level": "system programming",
                "focus_instruction": "Focus EXCLUSIVELY on UNIX system calls, APIs, process management, file operations, and system-level programming. AVOID basic C language tutorials or simple programming examples that don't involve system programming.",
                "concept_examples": """
- System calls (open, read, write, fork, exec)
- Process management and IPC
- File descriptors and file operations
- Signal handling and process control
- UNIX APIs and standards compliance
- Process groups and sessions
- File system operations
- Network programming concepts""",
                "avoid_concepts": """
- Basic C syntax or language features (variables, loops, functions)
- Simple hello world programs or basic printf examples
- Basic variable declarations and initialization
- Elementary programming concepts (#include, main function basics)
- Language tutorial concepts that don't use system calls
- Simple string manipulation without system interaction""",
                "example_type": "Code demonstrating UNIX system calls, process operations, or system-level functionality"
            },
            
            "operating_systems": {
                "subject": "operating systems",
                "book_title": "Operating Systems: Three Easy Pieces",
                "level": "operating systems",
                "focus_instruction": "Focus EXCLUSIVELY on operating system algorithms, data structures, and mechanisms. Extract concepts about how the OS works internally, NOT basic programming. Prioritize system-level concepts over language features.",
                "concept_examples": """
- Process and thread management (context switching, process control blocks)
- Memory management and virtual memory (page tables, TLB, paging algorithms)
- File system implementation (inodes, directory structures, journaling)
- CPU scheduling algorithms (round-robin, CFS, priority scheduling)
- Synchronization primitives (mutexes, semaphores, condition variables)
- Deadlock prevention and detection algorithms
- I/O systems and device management (device drivers, interrupt handling)
- Virtual memory systems (demand paging, page replacement algorithms)""",
                "avoid_concepts": """
- Basic C programming constructs (variables, arrays, strings, basic functions)
- Simple variable declarations and basic data types
- Basic control flow (if/else, loops) without OS context
- Elementary programming examples (hello world, simple calculations)
- Language syntax tutorials that don't demonstrate OS concepts
- String literals or basic I/O without system-level context""",
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
- Pointer operations and arrays
- String manipulation
- File I/O operations
- Data structures in C
- Function definitions and calls""",
                "avoid_concepts": """
- System-level concepts better suited for other books
- Operating system internals
- Linking and loading details""",
                "example_type": "Complete, compilable C program demonstrating the language concept"
            }
        }
        
        return contexts.get(book_context, contexts["c_programming"])
    
    def _parse_gemini_response(self, response_text):
        """Parse Gemini's JSON response"""
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
