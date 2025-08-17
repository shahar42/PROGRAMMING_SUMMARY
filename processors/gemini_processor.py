#!/usr/bin/env python3
"""
Enhanced Gemini Atomic Processor Module
UPDATED: Now includes CSAPP (Computer Systems) context awareness for proper concept extraction

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
from processors.base_processor import BaseAtomicProcessor

# Ensure we can find project root from anywhere
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class GeminiAtomicProcessor(BaseAtomicProcessor):
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
        super().__init__()

    def process_concept(self, concept_data, book_name="kernighan_ritchie"):
        """New main entry point that includes deduplication"""
        return self.process_concept_with_deduplication(concept_data, book_name)    
    
    def _extract_with_ai(self, concept_data):
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
        if "computer systems" in source_lower or "csapp" in source_lower:
            return "csapp_systems"
        elif "linkers" in source_lower or "loaders" in source_lower:
            return "linkers_loaders"
        elif "unix" in source_lower or "environment" in source_lower:
            return "unix_programming"
        elif "operating" in source_lower or "three easy pieces" in source_lower:
            return "operating_systems"
        elif "kernighan" in source_lower or "ritchie" in source_lower:
            return "c_programming"
        
        # Content-based detection as fallback
        systems_indicators = ["assembly", "processor", "cache", "virtual memory", "pipeline", "instruction set"]
        linking_indicators = ["linker", "loader", "object file", "symbol table", "relocation", "dynamic linking"]
        unix_indicators = ["system call", "unix", "posix", "file descriptor", "process"]
        os_indicators = ["scheduler", "virtual memory", "file system", "thread", "process"]
        
        if any(indicator in content_lower for indicator in systems_indicators):
            return "csapp_systems"
        elif any(indicator in content_lower for indicator in linking_indicators):
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
        """Get context-specific information for different books including C++ Standard"""
    
        contexts = {
            # ... existing contexts ...
            "csapp_systems": {
                "subject": "computer systems and architecture",
                "book_title": "Computer Systems: A Programmer's Perspective (CSAPP)",
                "level": "systems-level and performance-oriented",
                "focus_instruction": "Focus EXCLUSIVELY on systems programming concepts, computer architecture, memory hierarchy, performance optimization, and hardware-software interaction. AVOID information representation basics and linking details.",
                "example_type": "Complete assembly code, system calls, or architecture demonstrations",
                "concept_examples": [
                    "Machine-level programming with x86-64 assembly",
                    "Memory hierarchy and caching strategies", 
                    "Virtual memory and address translation",
                    "Processor pipelining and hazard handling",
                    "Concurrency and synchronization primitives",
                    "System call interfaces and exceptional control flow",
                    "Network programming with sockets",
                    "Performance optimization techniques"
                ],
                "avoid_concepts": [
                    "Basic C language syntax (covered in K&R)",
                    "Information representation and number systems",
                    "Linking and loading mechanics (covered in Linkers book)",
                    "High-level programming concepts",
                    "Basic data structures and algorithms"
                ]
            },
            
            "linkers_loaders": {
                "subject": "linking and loading",
                "book_title": "Linkers and Loaders by John Levine",
                "level": "advanced system-level",
                "focus_instruction": "Focus on concepts related to program linking, loading, object files, symbol resolution, dynamic libraries, and binary formats.",
                "example_type": "Complete linker scripts, object file analysis, or loading demonstrations",
                "concept_examples": [
                    "Symbol resolution across object files",
                    "Relocation entry processing",
                    "Dynamic library loading mechanisms",
                    "ELF file format structures",
                    "Position-independent code generation",
                    "Library interpositioning techniques"
                ],
                "avoid_concepts": [
                    "Basic C programming syntax",
                    "High-level application design",
                    "Operating system concepts not related to linking",
                    "Network programming basics"
                ]
            },
            
            "unix_programming": {
                "subject": "UNIX system programming",
                "book_title": "Advanced Programming in the UNIX Environment",
                "level": "system-level programming",
                "focus_instruction": "Focus on UNIX/POSIX system calls, APIs, and system programming patterns. Emphasize practical system programming techniques.",
                "example_type": "Complete system call examples with error handling",
                "concept_examples": [
                    "File I/O with system calls",
                    "Process creation and management",
                    "Signal handling mechanisms",
                    "Inter-process communication",
                    "File system operations",
                    "Network socket programming"
                ],
                "avoid_concepts": [
                    "Basic C language features",
                    "Hardware architecture details",
                    "High-level application frameworks",
                    "GUI programming concepts"
                ]
            },
            
            "operating_systems": {
                "subject": "operating systems principles",
                "book_title": "Operating Systems: Three Easy Pieces",
                "level": "conceptual and implementation-focused",
                "focus_instruction": "Focus on core OS concepts, algorithms, and data structures. Emphasize how operating systems manage resources.",
                "example_type": "Pseudocode algorithms or system implementation examples",
                "concept_examples": [
                    "Process scheduling algorithms",
                    "Memory management policies",
                    "File system implementations",
                    "Synchronization primitives",
                    "Virtual memory mechanisms",
                    "I/O subsystem design"
                ],
                "avoid_concepts": [
                    "Application-level programming",
                    "Specific hardware details",
                    "Network protocol implementations",
                    "Database concepts"
                ]
            },
            
            "c_programming": {
                "subject": "C programming language",
                "book_title": "The C Programming Language (K&R)",
                "level": "foundational programming",
                "focus_instruction": "Focus on C language syntax, semantics, and standard library usage. Emphasize proper C programming techniques.",
                "example_type": "Complete, compilable C programs demonstrating the concept",
                "concept_examples": [
                    "Variable declarations and scope",
                    "Control flow structures",
                    "Function definitions and calls",
                    "Pointer operations and arrays",
                    "Standard library functions",
                    "Memory management with malloc/free"
                ],
                "avoid_concepts": [
                    "System programming concepts",
                    "Hardware architecture details",
                    "Operating system internals",
                    "Network programming specifics"
                ]
            },
            # NEW: C++ Standard context
            "cpp_standard": {
                "subject": "C++ programming language",
                "book_title": "ISO/IEC 14882:2014 C++ Programming Language Standard",
                "level": "comprehensive language standard",
                "focus_instruction": "Focus EXCLUSIVELY on C++ language features, syntax, semantics, standard library, and modern C++ idioms. AVOID basic C concepts that are better covered in C-specific books.",
                "concept_examples": '''
- Classes and object-oriented programming (constructors, destructors, inheritance)
- Templates and generic programming (function templates, class templates, metaprogramming)
- Standard Template Library (containers, algorithms, iterators)
- Modern C++ features (auto, lambdas, move semantics, smart pointers)
- Exception handling (try/catch/throw, RAII)
- Operator overloading and function overloading
- Namespaces and scope resolution
- Advanced features (constexpr, decltype, variadic templates)''',
                "avoid_concepts": '''
- Basic C syntax already covered in K&R book
- Simple procedural programming concepts
- Basic pointer arithmetic without C++ context''',
                "example_type": "Complete, compilable C++ program demonstrating modern C++ features and best practices"
            }
            
            # ... rest of existing contexts ...
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
