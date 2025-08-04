#!/usr/bin/env python3
"""
Assembly Analyzer - Core Analysis Engine
Part of GOT/PLT Educational MCP Server

Place this file at: scripts/analyzers/assembly_analyzer.py

Correlates C source code with assembly output, analyzes calling conventions,
and provides educational explanations with performance metrics and visualizations.
"""

import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("assembly-analyzer")

class Architecture(Enum):
    X86_64 = "x86_64"
    ARM64 = "arm64"
    RISCV = "riscv"

class CallingConvention(Enum):
    SYSTEM_V_AMD64 = "system_v_amd64"
    MICROSOFT_X64 = "microsoft_x64"
    ARM_AAPCS = "arm_aapcs"
    RISCV_ABI = "riscv_abi"

@dataclass
class CFunction:
    """Represents a function parsed from C source"""
    name: str
    line_start: int
    line_end: int
    parameters: List[str]
    return_type: str
    local_variables: List[str]
    function_calls: List[str]

@dataclass
class AssemblyFunction:
    """Represents a function parsed from assembly"""
    name: str
    line_start: int
    line_end: int
    instructions: List[str]
    labels: List[str]
    calls: List[str]
    registers_used: List[str]

@dataclass
class CorrelationMapping:
    """Maps C constructs to assembly instructions"""
    c_line: int
    c_construct: str
    asm_lines: List[int]
    asm_instructions: List[str]
    explanation: str

@dataclass
class CallingConventionAnalysis:
    """Analysis of calling convention usage"""
    convention: CallingConvention
    parameter_registers: List[str]
    return_register: str
    callee_saved: List[str]
    caller_saved: List[str]
    stack_operations: List[str]
    violations: List[str]

class AssemblyAnalyzer:
    """Main assembly analysis engine"""
    
    def __init__(self):
        self.architecture = None
        self.calling_convention = None
        
    def analyze_files(self, c_file: str, assembly_file: str) -> Dict:
        """
        Main entry point: analyze C and assembly files
        
        Args:
            c_file: Path to C source file
            assembly_file: Path to assembly file
            
        Returns:
            Complete analysis results
        """
        try:
            # Read and parse files
            c_content = self._read_file(c_file)
            asm_content = self._read_file(assembly_file)
            
            # Detect architecture from assembly
            self.architecture = self._detect_architecture(asm_content)
            self.calling_convention = self._detect_calling_convention(asm_content)
            
            # Parse C functions
            c_functions = self._parse_c_functions(c_content)
            
            # Parse assembly functions
            asm_functions = self._parse_assembly_functions(asm_content)
            
            # Create correlations
            correlations = self._correlate_c_to_assembly(c_functions, asm_functions, c_content, asm_content)
            
            # Analyze calling convention
            calling_analysis = self._analyze_calling_convention(asm_functions)
            
            return {
                'success': True,
                'architecture': self.architecture.value if self.architecture else 'unknown',
                'calling_convention': calling_analysis,
                'c_functions': c_functions,
                'asm_functions': asm_functions,
                'correlations': correlations,
                'files': {
                    'c_file': c_file,
                    'assembly_file': assembly_file
                }
            }
            
        except Exception as e:
            logger.error(f"Assembly analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': {
                    'c_file': c_file,
                    'assembly_file': assembly_file
                }
            }
    
    def _read_file(self, filepath: str) -> str:
        """Read file content with error handling"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        except Exception as e:
            raise Exception(f"Failed to read {filepath}: {e}")
    
    def _detect_architecture(self, asm_content: str) -> Architecture:
        """Detect target architecture from assembly code"""
        asm_lower = asm_content.lower()
        
        # x86-64 indicators
        if any(reg in asm_lower for reg in ['%rax', '%rbx', '%rcx', '%rdx', '%rsp', '%rbp']):
            return Architecture.X86_64
        
        # ARM64 indicators
        if any(reg in asm_lower for reg in ['x0', 'x1', 'w0', 'w1', 'sp', 'lr']):
            return Architecture.ARM64
        
        # RISC-V indicators
        if any(reg in asm_lower for reg in ['x1', 'x2', 'ra', 'sp']) and 'risc' in asm_lower:
            return Architecture.RISCV
        
        # Default to x86-64 if unclear
        return Architecture.X86_64
    
    def _detect_calling_convention(self, asm_content: str) -> CallingConvention:
        """Detect calling convention from assembly patterns"""
        if self.architecture == Architecture.X86_64:
            # Look for System V AMD64 patterns (Linux/Unix)
            if re.search(r'%rdi.*%rsi.*%rdx.*%rcx.*%r8.*%r9', asm_content):
                return CallingConvention.SYSTEM_V_AMD64
            # Microsoft x64 uses different register order
            elif re.search(r'%rcx.*%rdx.*%r8.*%r9', asm_content):
                return CallingConvention.MICROSOFT_X64
            else:
                return CallingConvention.SYSTEM_V_AMD64  # Default for x86-64
                
        elif self.architecture == Architecture.ARM64:
            return CallingConvention.ARM_AAPCS
            
        elif self.architecture == Architecture.RISCV:
            return CallingConvention.RISCV_ABI
            
        return CallingConvention.SYSTEM_V_AMD64
    
    def _parse_c_functions(self, c_content: str) -> List[CFunction]:
        """Parse C source to extract function information"""
        functions = []
        lines = c_content.split('\n')
        
        # Simple function detection pattern
        func_pattern = r'^\s*(\w+(?:\s*\*)?)\s+(\w+)\s*\([^)]*\)\s*\{'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip comments and preprocessor directives
            if line.startswith('//') or line.startswith('#') or line.startswith('/*'):
                i += 1
                continue
            
            match = re.search(func_pattern, line)
            if match:
                return_type = match.group(1).strip()
                func_name = match.group(2)
                
                # Find function end
                brace_count = 0
                func_start = i
                func_end = i
                
                for j in range(i, len(lines)):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count == 0 and j > i:
                        func_end = j
                        break
                
                # Extract function info
                func_body = '\n'.join(lines[func_start:func_end+1])
                
                # Parse parameters
                param_match = re.search(r'\(([^)]*)\)', line)
                parameters = []
                if param_match and param_match.group(1).strip():
                    param_str = param_match.group(1)
                    parameters = [p.strip() for p in param_str.split(',')]
                
                # Find local variables (simple heuristic)
                local_vars = []
                var_pattern = r'^\s*(\w+(?:\s*\*)?)\s+(\w+)(?:\s*=|\s*;)'
                for line_num in range(func_start, func_end):
                    var_match = re.search(var_pattern, lines[line_num])
                    if var_match and not lines[line_num].strip().startswith('//'):
                        local_vars.append(var_match.group(2))
                
                # Find function calls
                func_calls = []
                call_pattern = r'(\w+)\s*\('
                for line_num in range(func_start, func_end):
                    calls = re.findall(call_pattern, lines[line_num])
                    func_calls.extend([call for call in calls if call not in ['if', 'while', 'for', 'switch']])
                
                functions.append(CFunction(
                    name=func_name,
                    line_start=func_start + 1,  # 1-indexed
                    line_end=func_end + 1,
                    parameters=parameters,
                    return_type=return_type,
                    local_variables=list(set(local_vars)),
                    function_calls=list(set(func_calls))
                ))
                
                i = func_end + 1
            else:
                i += 1
        
        return functions
    
    def _parse_assembly_functions(self, asm_content: str) -> List[AssemblyFunction]:
        """Parse assembly code to extract function information"""
        functions = []
        lines = asm_content.split('\n')
        
        # Function label patterns
        func_patterns = [
            r'^(\w+):$',  # Standard label
            r'^\s*\.globl\s+(\w+)',  # Global symbol declaration
            r'^\s*\.type\s+(\w+),\s*@function'  # Function type declaration
        ]
        
        current_func = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for function start
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    
                    # Skip if this looks like a data label
                    if any(keyword in line.lower() for keyword in ['.data', '.bss', '.rodata']):
                        break
                    
                    # End previous function if exists
                    if current_func:
                        current_func['line_end'] = i
                        functions.append(self._create_asm_function(current_func, lines))
                    
                    # Start new function
                    current_func = {
                        'name': func_name,
                        'line_start': i,
                        'line_end': len(lines) - 1,  # Will be updated
                        'instructions': [],
                        'labels': [],
                        'calls': [],
                        'registers': set()
                    }
                    break
            
            # If we're inside a function, parse the line
            if current_func:
                # Extract instruction
                if re.match(r'^\s*[a-zA-Z]', line) and ':' not in line:
                    current_func['instructions'].append(line)
                    
                    # Extract registers
                    registers = re.findall(r'%[a-z0-9]+', line)
                    current_func['registers'].update(registers)
                    
                    # Extract function calls
                    call_match = re.search(r'call\s+(\w+)', line)
                    if call_match:
                        current_func['calls'].append(call_match.group(1))
                
                # Extract labels
                if ':' in line and not line.startswith('#'):
                    label_match = re.search(r'^(\w+):', line)
                    if label_match:
                        current_func['labels'].append(label_match.group(1))
                        
                # Check for function end indicators
                if 'ret' in line.lower() or '.size' in line:
                    # Look ahead for next function
                    for j in range(i + 1, min(i + 10, len(lines))):
                        next_line = lines[j].strip()
                        if any(re.search(pat, next_line) for pat in func_patterns):
                            current_func['line_end'] = j - 1
                            break
            
            i += 1
        
        # Don't forget the last function
        if current_func:
            functions.append(self._create_asm_function(current_func, lines))
        
        return functions
    
    def _create_asm_function(self, func_data: Dict, lines: List[str]) -> AssemblyFunction:
        """Create AssemblyFunction object from parsed data"""
        return AssemblyFunction(
            name=func_data['name'],
            line_start=func_data['line_start'] + 1,  # 1-indexed
            line_end=func_data['line_end'] + 1,
            instructions=func_data['instructions'],
            labels=func_data['labels'],
            calls=func_data['calls'],
            registers_used=list(func_data['registers'])
        )
    
    def _correlate_c_to_assembly(self, c_functions: List[CFunction], 
                                asm_functions: List[AssemblyFunction],
                                c_content: str, asm_content: str) -> List[CorrelationMapping]:
        """Create correlations between C code and assembly instructions"""
        correlations = []
        
        # Match functions by name
        for c_func in c_functions:
            asm_func = next((af for af in asm_functions if af.name == c_func.name), None)
            
            if asm_func:
                # Create high-level correlation for the function
                correlations.append(CorrelationMapping(
                    c_line=c_func.line_start,
                    c_construct=f"Function {c_func.name}({', '.join(c_func.parameters)})",
                    asm_lines=list(range(asm_func.line_start, asm_func.line_end + 1)),
                    asm_instructions=asm_func.instructions[:5],  # First 5 instructions
                    explanation=f"Function {c_func.name} compiles to {len(asm_func.instructions)} assembly instructions"
                ))
                
                # Correlate function calls
                for call in c_func.function_calls:
                    if call in asm_func.calls:
                        correlations.append(CorrelationMapping(
                            c_line=c_func.line_start,  # Simplified - would need better parsing
                            c_construct=f"Function call: {call}()",
                            asm_lines=[],  # Would need to find specific call instruction
                            asm_instructions=[f"call {call}"],
                            explanation=f"C function call {call}() translates to assembly call instruction"
                        ))
        
        return correlations
    
    def _analyze_calling_convention(self, asm_functions: List[AssemblyFunction]) -> CallingConventionAnalysis:
        """Analyze calling convention usage in assembly functions"""
        
        # Define calling convention details based on detected convention
        if self.calling_convention == CallingConvention.SYSTEM_V_AMD64:
            param_regs = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']
            return_reg = '%rax'
            callee_saved = ['%rbx', '%rbp', '%r12', '%r13', '%r14', '%r15']
            caller_saved = ['%rax', '%rcx', '%rdx', '%rsi', '%rdi', '%r8', '%r9', '%r10', '%r11']
        elif self.calling_convention == CallingConvention.ARM_AAPCS:
            param_regs = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7']
            return_reg = 'x0'
            callee_saved = ['x19', 'x20', 'x21', 'x22', 'x23', 'x24', 'x25', 'x26', 'x27', 'x28']
            caller_saved = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9']
        else:
            # Default x86-64
            param_regs = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']
            return_reg = '%rax'
            callee_saved = ['%rbx', '%rbp', '%r12', '%r13', '%r14', '%r15']
            caller_saved = ['%rax', '%rcx', '%rdx', '%rsi', '%rdi', '%r8', '%r9', '%r10', '%r11']
        
        # Analyze stack operations
        stack_ops = []
        violations = []
        
        for func in asm_functions:
            for instruction in func.instructions:
                # Look for stack operations
                if re.search(r'push|pop|sub.*%rsp|add.*%rsp', instruction.lower()):
                    stack_ops.append(instruction.strip())
        
        return CallingConventionAnalysis(
            convention=self.calling_convention,
            parameter_registers=param_regs,
            return_register=return_reg,
            callee_saved=callee_saved,
            caller_saved=caller_saved,
            stack_operations=list(set(stack_ops)),
            violations=violations
        )
