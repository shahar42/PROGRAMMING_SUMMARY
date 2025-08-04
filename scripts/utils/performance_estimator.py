#!/usr/bin/env python3
"""
Performance Estimator - Instruction Counting and Cycle Estimation
Part of Assembly Analyzer for GOT/PLT Educational MCP Server

Place this file at: scripts/utils/performance_estimator.py

Provides heuristic-based performance analysis of assembly code with
instruction counting and cycle estimation.
"""

import re
import logging
from typing import Dict, List, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("performance-estimator")

class ComplexityLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"

@dataclass
class InstructionMetrics:
    """Metrics for a single instruction type"""
    count: int
    base_cycles: int
    total_cycles: int
    category: str

@dataclass
class FunctionPerformance:
    """Performance analysis for a single function"""
    name: str
    instruction_count: int
    estimated_cycles: int
    complexity: ComplexityLevel
    breakdown: Dict[str, InstructionMetrics]
    bottlenecks: List[str]

class PerformanceEstimator:
    """Estimates performance characteristics of assembly code"""
    
    def __init__(self, architecture: str = "x86_64"):
        self.architecture = architecture
        self.cycle_table = self._get_cycle_table(architecture)
        
    def _get_cycle_table(self, arch: str) -> Dict[str, Dict]:
        """Get cycle estimation table for specific architecture"""
        
        if arch == "x86_64":
            return {
                # ALU Operations (1-2 cycles)
                'alu': {
                    'cycles': 1,
                    'patterns': [r'\b(add|sub|and|or|xor|cmp|test|inc|dec|neg|not)\b'],
                    'category': 'ALU'
                },
                'alu_complex': {
                    'cycles': 2,
                    'patterns': [r'\b(imul|idiv|shl|shr|sar|rol|ror)\b'],
                    'category': 'ALU Complex'
                },
                
                # Move Operations (1 cycle)
                'move': {
                    'cycles': 1,
                    'patterns': [r'\b(mov|movl|movq|movb|movw)\b'],
                    'category': 'Move'
                },
                
                # Memory Operations (3-4 cycles)
                'load': {
                    'cycles': 3,
                    'patterns': [r'\bmov.*\([^)]+\).*%'],  # load from memory
                    'category': 'Memory Load'
                },
                'store': {
                    'cycles': 4,
                    'patterns': [r'\bmov.*%.*\([^)]+\)'],  # store to memory
                    'category': 'Memory Store'
                },
                
                # Branch Operations (1-20 cycles, depends on prediction)
                'branch_predicted': {
                    'cycles': 1,
                    'patterns': [r'\b(je|jne|jz|jnz|jl|jle|jg|jge)\b'],
                    'category': 'Branch (Predicted)'
                },
                'branch_mispredicted': {
                    'cycles': 15,
                    'patterns': [],  # Special handling needed
                    'category': 'Branch (Mispredicted)'
                },
                'unconditional_jump': {
                    'cycles': 1,
                    'patterns': [r'\b(jmp)\b'],
                    'category': 'Unconditional Jump'
                },
                
                # Function Calls (10-20 cycles)
                'call': {
                    'cycles': 12,
                    'patterns': [r'\b(call)\b'],
                    'category': 'Function Call'
                },
                'return': {
                    'cycles': 8,
                    'patterns': [r'\b(ret|retq)\b'],
                    'category': 'Function Return'
                },
                
                # Stack Operations (2-3 cycles)
                'stack': {
                    'cycles': 2,
                    'patterns': [r'\b(push|pop)\b'],
                    'category': 'Stack Operation'
                },
                
                # Floating Point (2-10 cycles)
                'fp_basic': {
                    'cycles': 3,
                    'patterns': [r'\b(addss|subss|mulss|addsd|subsd|mulsd)\b'],
                    'category': 'FP Basic'
                },
                'fp_complex': {
                    'cycles': 8,
                    'patterns': [r'\b(divss|divsd|sqrtss|sqrtsd)\b'],
                    'category': 'FP Complex'
                },
                
                # SIMD/Vector (1-5 cycles)
                'simd': {
                    'cycles': 2,
                    'patterns': [r'\b(paddd|psubd|pmull|movdqa|movdqu)\b'],
                    'category': 'SIMD'
                }
            }
            
        elif arch == "arm64":
            return {
                'alu': {
                    'cycles': 1,
                    'patterns': [r'\b(add|sub|and|orr|eor|cmp|tst)\b'],
                    'category': 'ALU'
                },
                'load': {
                    'cycles': 3,
                    'patterns': [r'\b(ldr|ldp)\b'],
                    'category': 'Memory Load'
                },
                'store': {
                    'cycles': 2,
                    'patterns': [r'\b(str|stp)\b'],
                    'category': 'Memory Store'
                },
                'branch': {
                    'cycles': 1,
                    'patterns': [r'\b(b\.eq|b\.ne|b\.lt|b\.ge)\b'],
                    'category': 'Branch'
                },
                'call': {
                    'cycles': 8,
                    'patterns': [r'\b(bl|blr)\b'],
                    'category': 'Function Call'
                }
            }
            
        else:  # Default/fallback
            return self._get_cycle_table("x86_64")
    
    def analyze_function_performance(self, func_name: str, instructions: List[str]) -> FunctionPerformance:
        """Analyze performance of a single function"""
        
        breakdown = {}
        total_cycles = 0
        bottlenecks = []
        
        # Count and categorize each instruction
        for instruction in instructions:
            inst_lower = instruction.lower().strip()
            
            # Skip empty lines and comments
            if not inst_lower or inst_lower.startswith('#') or inst_lower.startswith(';'):
                continue
            
            categorized = False
            
            # Match against cycle table patterns
            for category, info in self.cycle_table.items():
                for pattern in info['patterns']:
                    if re.search(pattern, inst_lower):
                        if category not in breakdown:
                            breakdown[category] = InstructionMetrics(
                                count=0,
                                base_cycles=info['cycles'],
                                total_cycles=0,
                                category=info['category']
                            )
                        
                        breakdown[category].count += 1
                        breakdown[category].total_cycles += info['cycles']
                        total_cycles += info['cycles']
                        categorized = True
                        break
                
                if categorized:
                    break
            
            # Handle uncategorized instructions
            if not categorized:
                if 'unknown' not in breakdown:
                    breakdown['unknown'] = InstructionMetrics(
                        count=0,
                        base_cycles=1,
                        total_cycles=0,
                        category='Unknown'
                    )
                breakdown['unknown'].count += 1
                breakdown['unknown'].total_cycles += 1
                total_cycles += 1
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(breakdown, instructions)
        
        # Determine complexity
        complexity = self._determine_complexity(len(instructions), total_cycles, bottlenecks)
        
        return FunctionPerformance(
            name=func_name,
            instruction_count=len([i for i in instructions if i.strip() and not i.strip().startswith('#')]),
            estimated_cycles=total_cycles,
            complexity=complexity,
            breakdown=breakdown,
            bottlenecks=bottlenecks
        )
    
    def _identify_bottlenecks(self, breakdown: Dict[str, InstructionMetrics], instructions: List[str]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Check for expensive operations
        for category, metrics in breakdown.items():
            if metrics.base_cycles >= 8:  # Expensive operations
                bottlenecks.append(f"High-latency {metrics.category} operations ({metrics.count} instances)")
        
        # Check for memory-intensive patterns
        total_memory_ops = sum(m.count for cat, m in breakdown.items() 
                              if 'Memory' in m.category)
        total_instructions = sum(m.count for m in breakdown.values())
        
        if total_instructions > 0 and total_memory_ops / total_instructions > 0.3:
            bottlenecks.append("Memory-intensive code (>30% memory operations)")
        
        # Check for branch-heavy code
        branch_ops = sum(m.count for cat, m in breakdown.items() 
                        if 'Branch' in m.category)
        
        if total_instructions > 0 and branch_ops / total_instructions > 0.2:
            bottlenecks.append("Branch-heavy code (>20% branches)")
        
        # Check for complex instruction patterns
        complex_patterns = [
            (r'div', "Division operations (very expensive)"),
            (r'sqrt', "Square root operations (expensive)"),
            (r'call.*call', "Nested function calls"),
            (r'loop|rep', "Loop/repeat instructions")
        ]
        
        for pattern, description in complex_patterns:
            if any(re.search(pattern, inst.lower()) for inst in instructions):
                bottlenecks.append(description)
        
        return bottlenecks
    
    def _determine_complexity(self, instruction_count: int, cycle_count: int, bottlenecks: List[str]) -> ComplexityLevel:
        """Determine overall complexity level"""
        
        # Base complexity on instruction count
        if instruction_count < 10:
            base_complexity = ComplexityLevel.LOW
        elif instruction_count < 25:
            base_complexity = ComplexityLevel.MEDIUM
        elif instruction_count < 50:
            base_complexity = ComplexityLevel.HIGH
        else:
            base_complexity = ComplexityLevel.VERY_HIGH
        
        # Adjust based on cycle density
        if instruction_count > 0:
            cycles_per_instruction = cycle_count / instruction_count
            
            if cycles_per_instruction > 5:  # High cycle density
                if base_complexity == ComplexityLevel.LOW:
                    base_complexity = ComplexityLevel.MEDIUM
                elif base_complexity == ComplexityLevel.MEDIUM:
                    base_complexity = ComplexityLevel.HIGH
        
        # Adjust based on bottlenecks
        if len(bottlenecks) > 2:
            if base_complexity != ComplexityLevel.VERY_HIGH:
                base_complexity = ComplexityLevel.HIGH
        
        return base_complexity
    
    def generate_performance_table(self, performances: List[FunctionPerformance]) -> str:
        """Generate formatted performance table"""
        
        if not performances:
            return "📊 No functions analyzed.\n"
        
        # Calculate column widths
        max_name_len = max(len(p.name) for p in performances)
        name_width = max(max_name_len, 15)
        
        # Header
        table = "📊 Performance Analysis:\n"
        table += "┌" + "─" * (name_width + 2) + "┬" + "─" * 14 + "┬" + "─" * 15 + "┬" + "─" * 13 + "┐\n"
        table += f"│ {'Function':<{name_width}} │ {'Instructions':<12} │ {'Est. Cycles':<13} │ {'Complexity':<11} │\n"
        table += "├" + "─" * (name_width + 2) + "┼" + "─" * 14 + "┼" + "─" * 15 + "┼" + "─" * 13 + "┤\n"
        
        # Data rows
        for perf in performances:
            # Format cycles with call overhead note
            cycles_str = f"~{perf.estimated_cycles}"
            if any('Call' in b for b in perf.breakdown.keys()):
                cycles_str += " (w/calls)"
            
            table += f"│ {perf.name:<{name_width}} │ {perf.instruction_count:<12} │ {cycles_str:<13} │ {perf.complexity.value:<11} │\n"
        
        table += "└" + "─" * (name_width + 2) + "┴" + "─" * 14 + "┴" + "─" * 15 + "┴" + "─" * 13 + "┘\n"
        
        return table
    
    def generate_detailed_breakdown(self, performance: FunctionPerformance) -> str:
        """Generate detailed breakdown for a single function"""
        
        result = f"\n🔍 Detailed Analysis: {performance.name}\n"
        result += "=" * 50 + "\n\n"
        
        # Summary
        result += f"**Summary:**\n"
        result += f"- Instructions: {performance.instruction_count}\n"
        result += f"- Estimated Cycles: ~{performance.estimated_cycles}\n"
        result += f"- Complexity: {performance.complexity.value}\n"
        result += f"- Avg Cycles/Instruction: {performance.estimated_cycles/max(performance.instruction_count, 1):.1f}\n\n"
        
        # Instruction breakdown
        if performance.breakdown:
            result += "**Instruction Breakdown:**\n"
            for category, metrics in sorted(performance.breakdown.items(), 
                                          key=lambda x: x[1].total_cycles, reverse=True):
                percentage = (metrics.total_cycles / performance.estimated_cycles) * 100
                result += f"- {metrics.category}: {metrics.count} instructions, {metrics.total_cycles} cycles ({percentage:.1f}%)\n"
            result += "\n"
        
        # Bottlenecks
        if performance.bottlenecks:
            result += "**⚠️ Performance Bottlenecks:**\n"
            for bottleneck in performance.bottlenecks:
                result += f"- {bottleneck}\n"
            result += "\n"
        
        # Optimization suggestions
        result += "**💡 Optimization Suggestions:**\n"
        suggestions = self._generate_optimization_suggestions(performance)
        for suggestion in suggestions:
            result += f"- {suggestion}\n"
        
        return result
    
    def _generate_optimization_suggestions(self, performance: FunctionPerformance) -> List[str]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []
        
        # Memory-related suggestions
        memory_ops = sum(m.count for cat, m in performance.breakdown.items() 
                        if 'Memory' in m.category)
        if memory_ops > performance.instruction_count * 0.3:
            suggestions.append("Consider reducing memory accesses through register reuse")
            suggestions.append("Look for opportunities to use cache-friendly access patterns")
        
        # Branch-related suggestions
        branch_ops = sum(m.count for cat, m in performance.breakdown.items() 
                        if 'Branch' in m.category)
        if branch_ops > performance.instruction_count * 0.2:
            suggestions.append("Consider reducing branches through predication or branchless techniques")
        
        # Function call suggestions
        if 'call' in performance.breakdown and performance.breakdown['call'].count > 3:
            suggestions.append("Consider inlining frequently called functions")
        
        # Complexity-based suggestions
        if performance.complexity in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]:
            suggestions.append("Consider breaking down into smaller functions")
            suggestions.append("Profile actual execution to identify hot paths")
        
        # Default suggestion if none specific
        if not suggestions:
            suggestions.append("Function appears well-optimized for its complexity level")
        
        return suggestions
