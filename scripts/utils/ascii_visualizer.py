#!/usr/bin/env python3
"""
ASCII Visualizer - Text-based Visualization Generator
Part of Assembly Analyzer for GOT/PLT Educational MCP Server

Place this file at: scripts/utils/ascii_visualizer.py

Creates ASCII art visualizations for function call trees, data flow diagrams,
and register usage patterns.
"""

import re
import logging
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger("ascii-visualizer")

@dataclass
class CallNode:
    """Node in function call tree"""
    name: str
    children: List['CallNode']
    depth: int = 0
    call_count: int = 1

@dataclass
class DataFlowNode:
    """Node in data flow diagram"""
    name: str
    type: str  # 'register', 'memory', 'function', 'operation'
    connections: List[str]

class ASCIIVisualizer:
    """Creates ASCII art visualizations for assembly analysis"""
    
    def __init__(self):
        self.box_chars = {
            'horizontal': '─',
            'vertical': '│',
            'top_left': '┌',
            'top_right': '┐',
            'bottom_left': '└',
            'bottom_right': '┘',
            'cross': '┼',
            'tee_down': '┬',
            'tee_up': '┴',
            'tee_right': '├',
            'tee_left': '┤'
        }
    
    def generate_function_call_tree(self, functions: List, main_function: str = "main") -> str:
        """Generate ASCII function call tree"""
        
        # Build call graph
        call_graph = self._build_call_graph(functions)
        
        # Find root function (main or first function)
        root_name = main_function if main_function in call_graph else list(call_graph.keys())[0] if call_graph else "unknown"
        
        if root_name not in call_graph:
            return f"🌳 Function Call Tree:\nNo function calls found or '{root_name}' not found.\n"
        
        # Build tree starting from root
        root_node = self._build_call_tree(root_name, call_graph, set())
        
        # Generate ASCII representation
        result = "🌳 Function Call Tree:\n"
        result += self._render_call_tree(root_node, "", True, set())
        
        return result
    
    def generate_data_flow_diagram(self, functions: List, calling_convention: Dict) -> str:
        """Generate ASCII data flow diagram showing register usage"""
        
        if not functions:
            return "🔄 Data Flow Diagram:\nNo functions to analyze.\n"
        
        # Analyze register usage patterns
        flow_data = self._analyze_data_flow(functions, calling_convention)
        
        result = "🔄 Data Flow (Register Usage):\n"
        
        # Show parameter passing
        if 'parameter_flow' in flow_data:
            result += self._render_parameter_flow(flow_data['parameter_flow'])
        
        # Show register reuse patterns
        if 'register_reuse' in flow_data:
            result += self._render_register_reuse(flow_data['register_reuse'])
        
        # Show return value flow
        if 'return_flow' in flow_data:
            result += self._render_return_flow(flow_data['return_flow'])
        
        return result
    
    def generate_register_usage_diagram(self, functions: List) -> str:
        """Generate diagram showing register usage across functions"""
        
        if not functions:
            return "📊 Register Usage:\nNo functions to analyze.\n"
        
        # Collect all registers used
        all_registers = set()
        func_registers = {}
        
        for func in functions:
            if hasattr(func, 'registers_used'):
                registers = set(func.registers_used)
                all_registers.update(registers)
                func_registers[func.name] = registers
        
        if not all_registers:
            return "📊 Register Usage:\nNo register usage detected.\n"
        
        # Sort registers for consistent display
        sorted_registers = sorted(all_registers)
        
        result = "📊 Register Usage Matrix:\n"
        result += self._render_register_matrix(func_registers, sorted_registers)
        
        return result
    
    def generate_instruction_flow_diagram(self, function_name: str, instructions: List[str]) -> str:
        """Generate control flow diagram for a single function"""
        
        if not instructions:
            return f"🔀 Control Flow ({function_name}):\nNo instructions to analyze.\n"
        
        # Analyze control flow
        flow_blocks = self._analyze_control_flow(instructions)
        
        result = f"🔀 Control Flow ({function_name}):\n"
        result += self._render_control_flow(flow_blocks)
        
        return result
    
    def _build_call_graph(self, functions: List) -> Dict[str, List[str]]:
        """Build function call graph from function list"""
        call_graph = {}
        
        for func in functions:
            if hasattr(func, 'name') and hasattr(func, 'function_calls'):
                call_graph[func.name] = func.function_calls
            elif hasattr(func, 'name') and hasattr(func, 'calls'):
                call_graph[func.name] = func.calls
        
        return call_graph
    
    def _build_call_tree(self, func_name: str, call_graph: Dict[str, List[str]], visited: Set[str]) -> CallNode:
        """Build call tree recursively"""
        
        if func_name in visited:
            # Circular reference
            return CallNode(name=f"{func_name} (circular)", children=[])
        
        visited.add(func_name)
        
        children = []
        if func_name in call_graph:
            for called_func in call_graph[func_name]:
                if called_func != func_name:  # Avoid self-recursion in display
                    child_node = self._build_call_tree(called_func, call_graph, visited.copy())
                    children.append(child_node)
        
        return CallNode(name=func_name, children=children)
    
    def _render_call_tree(self, node: CallNode, prefix: str, is_last: bool, visited_in_path: Set[str]) -> str:
        """Render call tree as ASCII art"""
        
        result = ""
        
        # Prevent infinite recursion in display
        if node.name in visited_in_path:
            connector = self.box_chars['bottom_right'] if is_last else self.box_chars['tee_right']
            result += f"{prefix}{connector}{self.box_chars['horizontal']} {node.name} (recursive)\n"
            return result
        
        # Add current node
        connector = self.box_chars['bottom_right'] if is_last else self.box_chars['tee_right']
        result += f"{prefix}{connector}{self.box_chars['horizontal']} {node.name}()\n"
        
        # Add children
        if node.children:
            visited_in_path.add(node.name)
            
            for i, child in enumerate(node.children):
                is_child_last = (i == len(node.children) - 1)
                
                if is_last:
                    child_prefix = prefix + "    "
                else:
                    child_prefix = prefix + self.box_chars['vertical'] + "   "
                
                result += self._render_call_tree(child, child_prefix, is_child_last, visited_in_path.copy())
        
        return result
    
    def _analyze_data_flow(self, functions: List, calling_convention: Dict) -> Dict:
        """Analyze data flow patterns in functions"""
        
        flow_data = {}
        
        # Analyze parameter passing
        param_registers = calling_convention.get('parameter_registers', [])
        return_register = calling_convention.get('return_register', '')
        
        if param_registers:
            flow_data['parameter_flow'] = {
                'registers': param_registers,
                'pattern': 'sequential'
            }
        
        if return_register:
            flow_data['return_flow'] = {
                'register': return_register,
                'functions': [f.name for f in functions if hasattr(f, 'name')]
            }
        
        # Analyze register reuse
        register_usage = defaultdict(list)
        for func in functions:
            if hasattr(func, 'registers_used') and hasattr(func, 'name'):
                for reg in func.registers_used:
                    register_usage[reg].append(func.name)
        
        flow_data['register_reuse'] = dict(register_usage)
        
        return flow_data
    
    def _render_parameter_flow(self, param_flow: Dict) -> str:
        """Render parameter passing flow"""
        
        result = "\n**Parameter Passing:**\n"
        
        registers = param_flow.get('registers', [])
        if len(registers) >= 3:
            # Show first few parameter registers
            result += f"{registers[0]} ──→ [arg1]\n"
            result += f"{registers[1]} ──→ [arg2] ──┐\n"
            result += f"{registers[2]} ──→ [arg3] ──┼──→ Function\n"
            
            if len(registers) > 3:
                result += f"{'...':<6} ──→ [...] ──┘\n"
        elif registers:
            for i, reg in enumerate(registers[:3]):
                arrow = "──→"
                result += f"{reg} {arrow} [arg{i+1}]\n"
        
        return result
    
    def _render_register_reuse(self, register_reuse: Dict) -> str:
        """Render register reuse patterns"""
        
        result = "\n**Register Reuse Patterns:**\n"
        
        # Show most commonly used registers
        common_registers = sorted(register_reuse.items(), 
                                key=lambda x: len(x[1]), reverse=True)[:5]
        
        for reg, functions in common_registers:
            if len(functions) > 1:
                result += f"{reg}: {' → '.join(functions[:3])}"
                if len(functions) > 3:
                    result += f" (+{len(functions)-3} more)"
                result += "\n"
        
        return result
    
    def _render_return_flow(self, return_flow: Dict) -> str:
        """Render return value flow"""
        
        result = "\n**Return Value Flow:**\n"
        
        return_reg = return_flow.get('register', '')
        functions = return_flow.get('functions', [])
        
        if return_reg and functions:
            result += f"Functions ──→ {return_reg} ──→ [return value]\n"
            
            # Show which functions use return register
            if len(functions) <= 3:
                func_list = ', '.join(functions)
            else:
                func_list = f"{', '.join(functions[:3])} (+{len(functions)-3} more)"
            
            result += f"Used by: {func_list}\n"
        
        return result
    
    def _render_register_matrix(self, func_registers: Dict[str, Set[str]], sorted_registers: List[str]) -> str:
        """Render register usage matrix"""
        
        if not func_registers or not sorted_registers:
            return "No register usage data available.\n"
        
        # Limit display to avoid overwhelming output
        max_functions = 8
        max_registers = 10
        
        functions = list(func_registers.keys())[:max_functions]
        registers = sorted_registers[:max_registers]
        
        # Calculate column widths
        max_func_len = max(len(name) for name in functions) if functions else 8
        func_width = min(max_func_len, 12)
        
        # Header
        result = f"{'Function':<{func_width}} │ "
        for reg in registers:
            result += f"{reg:<6}"
        result += "\n"
        
        # Separator
        result += "─" * func_width + "─┼─"
        result += "─" * (6 * len(registers)) + "\n"
        
        # Data rows
        for func_name in functions:
            func_regs = func_registers.get(func_name, set())
            
            # Truncate function name if too long
            display_name = func_name[:func_width-1] + "…" if len(func_name) > func_width else func_name
            
            result += f"{display_name:<{func_width}} │ "
            
            for reg in registers:
                marker = "●" if reg in func_regs else "○"
                result += f"{marker:<6}"
            
            result += "\n"
        
        # Legend
        result += "\nLegend: ● = Used, ○ = Not used\n"
        
        if len(sorted_registers) > max_registers:
            result += f"(Showing {max_registers} of {len(sorted_registers)} registers)\n"
        
        if len(func_registers) > max_functions:
            result += f"(Showing {max_functions} of {len(func_registers)} functions)\n"
        
        return result
    
    def _analyze_control_flow(self, instructions: List[str]) -> List[Dict]:
        """Analyze control flow in instructions"""
        
        blocks = []
        current_block = {
            'start': 0,
            'instructions': [],
            'type': 'sequential',
            'targets': []
        }
        
        for i, instruction in enumerate(instructions):
            inst_lower = instruction.lower().strip()
            
            if not inst_lower or inst_lower.startswith('#'):
                continue
            
            current_block['instructions'].append(instruction.strip())
            
            # Check for control flow changes
            if re.search(r'\b(ret|retq)\b', inst_lower):
                current_block['type'] = 'return'
                blocks.append(current_block)
                current_block = {
                    'start': i + 1,
                    'instructions': [],
                    'type': 'sequential',
                    'targets': []
                }
            elif re.search(r'\b(call)\b', inst_lower):
                current_block['type'] = 'call'
                # Extract call target
                call_match = re.search(r'call\s+(\w+)', inst_lower)
                if call_match:
                    current_block['targets'].append(call_match.group(1))
            elif re.search(r'\b(j[a-z]*)\b', inst_lower):
                current_block['type'] = 'branch'
                # Extract branch target
                branch_match = re.search(r'j[a-z]*\s+(\w+)', inst_lower)
                if branch_match:
                    current_block['targets'].append(branch_match.group(1))
        
        # Add final block if it has instructions
        if current_block['instructions']:
            blocks.append(current_block)
        
        return blocks
    
    def _render_control_flow(self, flow_blocks: List[Dict]) -> str:
        """Render control flow as ASCII diagram"""
        
        if not flow_blocks:
            return "No control flow to display.\n"
        
        result = ""
        
        for i, block in enumerate(flow_blocks):
            # Block header
            block_type = block['type']
            inst_count = len(block['instructions'])
            
            if block_type == 'sequential':
                icon = "□"
            elif block_type == 'call':
                icon = "📞"
            elif block_type == 'branch':
                icon = "◇"
            elif block_type == 'return':
                icon = "↩"
            else:
                icon = "○"
            
            result += f"{icon} Block {i+1} ({block_type}, {inst_count} instructions)\n"
            
            # Show first few instructions
            for j, inst in enumerate(block['instructions'][:3]):
                result += f"   {inst}\n"
            
            if len(block['instructions']) > 3:
                result += f"   ... ({len(block['instructions'])-3} more)\n"
            
            # Show targets
            if block['targets']:
                target_str = ", ".join(block['targets'])
                result += f"   → {target_str}\n"
            
            # Connection to next block
            if i < len(flow_blocks) - 1:
                result += "   ↓\n"
            
            result += "\n"
        
        return result
