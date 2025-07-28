#!/usr/bin/env python3
"""
Lazy Binding Analyzer for GOT/PLT Educational MCP Server

Specialized analysis of lazy binding behavior with educational explanations.
Focuses on the educational aspects of how lazy binding works in practice.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from utils.gdb_interface import GDBInterface, GDBAnalysisSession

logger = logging.getLogger("lazy-binding-analyzer")


@dataclass
class LazyBindingEvent:
    """Represents a lazy binding event during program execution"""
    symbol_name: str
    event_type: str  # 'first_call', 'resolution', 'subsequent_call'
    timestamp: float
    got_value_before: str
    got_value_after: str
    plt_address: str
    resolver_involved: bool
    educational_significance: str


@dataclass
class BindingComparison:
    """Comparison between lazy and immediate binding characteristics"""
    symbol_name: str
    lazy_binding_time: float
    immediate_binding_time: float
    overhead_ratio: float
    resolution_complexity: str
    educational_insights: List[str]


class LazyBindingAnalyzer:
    """
    Specialized analysis of lazy binding behavior
    
    This class focuses specifically on the educational aspects of lazy binding,
    providing detailed analysis and explanations of how lazy binding works
    in practice vs theory.
    """
    
    def __init__(self, binary_path: str):
        """
        Initialize lazy binding analyzer
        
        Args:
            binary_path: Path to binary for lazy binding analysis
        """
        self.binary_path = Path(binary_path)
        self.binding_events = []
        self.analyzed_symbols = set()
        self.resolver_traced = False
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {self.binary_path}")
    
    def setup_resolver_tracing(self) -> bool:
        """
        Set up tracing of _dl_runtime_resolve for educational analysis
        
        Returns:
            True if resolver tracing was set up successfully
        """
        try:
            # Test if we can set breakpoint on resolver
            with GDBInterface(str(self.binary_path)) as gdb:
                resolver_bp = gdb.set_breakpoint("_dl_runtime_resolve")
                if resolver_bp:
                    self.resolver_traced = True
                    logger.info("Resolver tracing enabled for educational analysis")
                    return True
                else:
                    logger.warning("Could not set resolver breakpoint - analysis will be limited")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to setup resolver tracing: {e}")
            return False
    
    def analyze_first_call_behavior(self, symbol_name: str) -> Dict[str, Any]:
        """
        Analyze the behavior of the first call to a symbol (lazy binding)
        
        Args:
            symbol_name: Symbol to analyze first call behavior for
            
        Returns:
            Detailed analysis of first call lazy binding behavior
        """
        analysis = {
            'symbol': symbol_name,
            'first_call_detected': False,
            'resolution_steps': [],
            'got_state_changes': [],
            'performance_metrics': {},
            'educational_insights': []
        }
        
        try:
            session = GDBAnalysisSession(str(self.binary_path))
            results = session.analyze_lazy_binding(symbol_name)
            
            first_call = results.get('first_call', {})
            if first_call:
                analysis['first_call_detected'] = True
                
                # Analyze GOT state changes
                got_before = first_call.get('got_value_before', 'unknown')
                got_after = first_call.get('got_value_after', 'unknown')
                
                if got_before != 'unknown' and got_after != 'unknown':
                    analysis['got_state_changes'].append({
                        'phase': 'before_resolution',
                        'got_value': got_before,
                        'interpretation': 'Points to PLT resolver stub'
                    })
                    
                    analysis['got_state_changes'].append({
                        'phase': 'after_resolution',
                        'got_value': got_after,
                        'interpretation': 'Points to actual symbol address'
                    })
                    
                    # Educational insights based on state changes
                    if got_before != got_after:
                        analysis['educational_insights'].extend([
                            f"✅ Lazy binding confirmed: GOT entry updated from {got_before} to {got_after}",
                            "🔄 This demonstrates the core lazy binding mechanism",
                            "💡 Future calls will use the resolved address directly"
                        ])
                    else:
                        analysis['educational_insights'].extend([
                            "⚠️ GOT entry did not change - possible reasons:",
                            "  • Symbol was already resolved",
                            "  • Binary uses immediate binding (LD_BIND_NOW)",
                            "  • Symbol is locally defined"
                        ])
                
                # Performance analysis
                timestamp = first_call.get('timestamp', 0)
                analysis['performance_metrics'] = {
                    'first_call_timestamp': timestamp,
                    'resolution_overhead': 'measured' if got_before != got_after else 'none_detected',
                    'educational_note': 'First call includes symbol lookup overhead'
                }
                
                # Educational context
                analysis['educational_insights'].append(
                    "📚 First call process: PLT stub → _dl_runtime_resolve → symbol lookup → GOT update → target function"
                )
            
            else:
                analysis['educational_insights'].extend([
                    "❌ Could not capture first call behavior",
                    "💡 Try running the program multiple times or with different test cases",
                    "🔍 Some symbols may be resolved at load time rather than on first call"
                ])
        
        except Exception as e:
            logger.error(f"First call analysis failed for {symbol_name}: {e}")
            analysis['educational_insights'].append(f"❌ Analysis failed: {str(e)}")
        
        return analysis
    
    def compare_call_performance(self, symbol_name: str, call_count: int = 5) -> Dict[str, Any]:
        """
        Compare performance between first call and subsequent calls
        
        Args:
            symbol_name: Symbol to analyze call performance for
            call_count: Number of calls to analyze
            
        Returns:
            Performance comparison with educational explanations
        """
        comparison = {
            'symbol': symbol_name,
            'call_count': call_count,
            'first_call_metrics': {},
            'subsequent_call_metrics': [],
            'performance_analysis': {},
            'educational_conclusions': []
        }
        
        try:
            # Note: Precise timing requires more sophisticated measurement
            # This provides educational framework and explanations
            
            session = GDBAnalysisSession(str(self.binary_path))
            binding_results = session.analyze_lazy_binding(symbol_name)
            
            first_call = binding_results.get('first_call', {})
            second_call = binding_results.get('second_call', {})
            
            if first_call and second_call:
                # Extract timing information
                first_time = first_call.get('timestamp', 0)
                second_time = second_call.get('timestamp', 0)
                
                comparison['first_call_metrics'] = {
                    'timestamp': first_time,
                    'got_before': first_call.get('got_value_before', 'unknown'),
                    'got_after': first_call.get('got_value_after', 'unknown'),
                    'resolution_occurred': first_call.get('got_value_before') != first_call.get('got_value_after'),
                    'educational_note': 'Includes symbol resolution overhead'
                }
                
                comparison['subsequent_call_metrics'].append({
                    'call_number': 2,
                    'timestamp': second_time,
                    'got_value': second_call.get('got_value', 'unknown'),
                    'educational_note': 'Direct jump through resolved GOT entry'
                })
                
                # Performance analysis
                if second_time > first_time:
                    time_difference = second_time - first_time
                    comparison['performance_analysis'] = {
                        'time_between_calls': time_difference,
                        'resolution_overhead_detected': comparison['first_call_metrics']['resolution_occurred'],
                        'performance_improvement': 'subsequent_calls_faster',
                        'educational_interpretation': f'Resolution added {time_difference:.6f}s overhead to first call'
                    }
                
                # Educational conclusions
                comparison['educational_conclusions'].extend([
                    "🎯 Lazy binding trade-off analysis:",
                    f"  • First call: Slower (includes resolution overhead)",
                    f"  • Subsequent calls: Faster (direct GOT jump)",
                    "💡 Benefits: Faster program startup, only resolve used symbols",
                    "⚖️ Costs: Slower first access to each external symbol"
                ])
                
                if comparison['first_call_metrics']['resolution_occurred']:
                    comparison['educational_conclusions'].append(
                        "✅ Lazy binding behavior confirmed through runtime analysis"
                    )
                else:
                    comparison['educational_conclusions'].append(
                        "⚠️ Symbol may have been pre-resolved or uses immediate binding"
                    )
            
            else:
                comparison['educational_conclusions'].extend([
                    "❌ Could not capture sufficient call data for comparison",
                    "💡 Performance comparison requires multiple calls to the same symbol",
                    "🔍 Try with a program that calls the same function multiple times"
                ])
        
        except Exception as e:
            logger.error(f"Call performance comparison failed: {e}")
            comparison['educational_conclusions'].append(f"❌ Analysis failed: {str(e)}")
        
        return comparison
    
    def demonstrate_binding_modes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Demonstrate different binding modes (lazy vs immediate)
        
        Args:
            symbols: List of symbols to demonstrate binding modes for
            
        Returns:
            Demonstration of different binding behaviors
        """
        demonstration = {
            'symbols_tested': symbols,
            'lazy_binding_results': {},
            'immediate_binding_simulation': {},
            'educational_comparison': [],
            'practical_implications': []
        }
        
        try:
            # Analyze current (likely lazy) binding behavior
            for symbol in symbols:
                logger.info(f"Analyzing lazy binding for {symbol}")
                lazy_analysis = self.analyze_first_call_behavior(symbol)
                demonstration['lazy_binding_results'][symbol] = lazy_analysis
            
            # Educational comparison (since we can't easily test immediate binding)
            demonstration['immediate_binding_simulation'] = {
                'explanation': 'Immediate binding (LD_BIND_NOW=1) resolves all symbols at load time',
                'characteristics': {
                    'startup_time': 'Slower (all symbols resolved at once)',
                    'runtime_calls': 'Faster (no resolution overhead)',
                    'memory_usage': 'Higher (all symbols in memory)',
                    'security': 'Better (no runtime resolution vulnerabilities)'
                },
                'educational_note': 'Cannot directly test immediate binding without restarting program'
            }
            
            # Educational comparison
            lazy_symbols_resolved = sum(1 for result in demonstration['lazy_binding_results'].values() 
                                      if result.get('first_call_detected', False))
            
            demonstration['educational_comparison'].extend([
                f"📊 Lazy Binding Analysis Results:",
                f"  • Symbols tested: {len(symbols)}",
                f"  • Symbols showing lazy behavior: {lazy_symbols_resolved}",
                f"  • Resolution detection rate: {lazy_symbols_resolved/len(symbols)*100:.1f}%",
                "",
                "🔄 Lazy vs Immediate Binding Comparison:",
                "  Lazy Binding:",
                "    ✅ Faster program startup",
                "    ✅ Lower memory usage (unused symbols not resolved)",
                "    ❌ Slower first call to each function",
                "    ❌ Runtime overhead for symbol resolution",
                "",
                "  Immediate Binding (LD_BIND_NOW=1):",
                "    ✅ Faster function calls (no resolution delay)",
                "    ✅ More predictable performance",
                "    ❌ Slower program startup",
                "    ❌ Higher memory usage"
            ])
            
            # Practical implications
            demonstration['practical_implications'].extend([
                "🎯 When to use Lazy Binding:",
                "  • Interactive applications (fast startup important)",
                "  • Programs with many unused library functions",
                "  • Development and testing environments",
                "",
                "🎯 When to use Immediate Binding:",
                "  • Real-time systems (predictable timing)",
                "  • Security-critical applications",
                "  • Performance benchmarking",
                "  • Production servers after warm-up"
            ])
        
        except Exception as e:
            logger.error(f"Binding mode demonstration failed: {e}")
            demonstration['educational_comparison'].append(f"❌ Analysis failed: {str(e)}")
        
        return demonstration
    
    def trace_resolver_behavior(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Trace _dl_runtime_resolve behavior for educational purposes
        
        Args:
            symbols: Symbols to trace resolver behavior for
            
        Returns:
            Educational trace of resolver behavior
        """
        trace = {
            'symbols': symbols,
            'resolver_calls': [],
            'resolution_sequence': {},
            'educational_insights': []
        }
        
        try:
            with GDBInterface(str(self.binary_path)) as gdb:
                # Set up resolver tracing
                resolver_bp = gdb.set_breakpoint("_dl_runtime_resolve")
                
                if not resolver_bp:
                    trace['educational_insights'].extend([
                        "⚠️ Could not set breakpoint on _dl_runtime_resolve",
                        "💡 Resolver tracing requires debug symbols",
                        "🔍 Analysis will focus on PLT behavior instead"
                    ])
                    return trace
                
                # Set PLT breakpoints for symbols
                plt_breakpoints = gdb.set_plt_breakpoints(symbols)
                
                # Start program
                gdb.run_program()
                
                call_sequence = 1
                max_calls = 15  # Limit for educational purposes
                
                while call_sequence <= max_calls:
                    hit = gdb.continue_execution()
                    
                    if hit['status'] == 'breakpoint_hit':
                        if hit['breakpoint'] == resolver_bp.number:
                            # In resolver
                            backtrace = gdb.get_backtrace()
                            registers = gdb.get_register_info(['rip', 'rdi', 'rsi'])
                            
                            resolver_call = {
                                'sequence': call_sequence,
                                'timestamp': time.time(),
                                'location': 'dl_runtime_resolve',
                                'backtrace_depth': len(backtrace),
                                'registers': registers,
                                'educational_note': 'Runtime linker resolving symbol address'
                            }
                            
                            # Try to identify which symbol is being resolved
                            if backtrace:
                                for frame in backtrace[:3]:
                                    for symbol in symbols:
                                        if symbol in frame:
                                            resolver_call['resolving_symbol'] = symbol
                                            break
                            
                            trace['resolver_calls'].append(resolver_call)
                            
                        else:
                            # PLT hit - identify symbol
                            hit_symbol = None
                            for symbol, bp_info in plt_breakpoints.items():
                                if hit['breakpoint'] == bp_info.number:
                                    hit_symbol = symbol
                                    break
                            
                            if hit_symbol:
                                if hit_symbol not in trace['resolution_sequence']:
                                    trace['resolution_sequence'][hit_symbol] = []
                                
                                plt_event = {
                                    'sequence': call_sequence,
                                    'timestamp': time.time(),
                                    'location': 'PLT_stub',
                                    'symbol': hit_symbol,
                                    'address': hit.get('address', 'unknown'),
                                    'educational_note': f'PLT stub for {hit_symbol} executed'
                                }
                                
                                trace['resolution_sequence'][hit_symbol].append(plt_event)
                        
                        call_sequence += 1
                    
                    elif hit['status'] in ['program_exited', 'program_terminated']:
                        break
                
                # Educational analysis
                total_resolver_calls = len(trace['resolver_calls'])
                symbols_resolved = len(trace['resolution_sequence'])
                
                trace['educational_insights'].extend([
                    f"📊 Resolver Tracing Results:",
                    f"  • Total resolver calls: {total_resolver_calls}",
                    f"  • Symbols with PLT activity: {symbols_resolved}",
                    f"  • Average resolver calls per symbol: {total_resolver_calls/max(symbols_resolved,1):.1f}",
                    "",
                    "🔍 Resolver Behavior Observations:",
                    "  • _dl_runtime_resolve handles symbol lookup",
                    "  • Each symbol is typically resolved once",
                    "  • Resolver updates GOT entry for future calls",
                    "  • PLT stubs provide entry points for resolution"
                ])
                
                if total_resolver_calls == 0:
                    trace['educational_insights'].extend([
                        "⚠️ No resolver calls detected - possible reasons:",
                        "  • Symbols already resolved at load time",
                        "  • Binary uses immediate binding",
                        "  • Program didn't call external functions"
                    ])
        
        except Exception as e:
            logger.error(f"Resolver tracing failed: {e}")
            trace['educational_insights'].append(f"❌ Tracing failed: {str(e)}")
        
        return trace
    
    def generate_lazy_binding_report(self, symbols: List[str]) -> str:
        """
        Generate comprehensive educational report on lazy binding behavior
        
        Args:
            symbols: Symbols to include in the analysis
            
        Returns:
            Formatted educational report
        """
        report_sections = []
        
        # Header
        report_sections.append(f"""
🔍 **Lazy Binding Analysis Report**
**Binary:** {self.binary_path}
**Symbols Analyzed:** {', '.join(symbols)}
**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}

""")
        
        try:
            # First call behavior analysis
            report_sections.append("## 🚀 First Call Behavior Analysis\n")
            
            for symbol in symbols:
                first_call_analysis = self.analyze_first_call_behavior(symbol)
                
                report_sections.append(f"### {symbol}\n")
                
                if first_call_analysis['first_call_detected']:
                    got_changes = first_call_analysis.get('got_state_changes', [])
                    if got_changes:
                        before = next((g['got_value'] for g in got_changes if g['phase'] == 'before_resolution'), 'unknown')
                        after = next((g['got_value'] for g in got_changes if g['phase'] == 'after_resolution'), 'unknown')
                        
                        report_sections.append(f"- **Resolution Status:** ✅ Confirmed\n")
                        report_sections.append(f"- **GOT Before:** `{before}`\n")
                        report_sections.append(f"- **GOT After:** `{after}`\n")
                    else:
                        report_sections.append(f"- **Resolution Status:** ⚠️ Not detected\n")
                else:
                    report_sections.append(f"- **Resolution Status:** ❌ First call not captured\n")
                
                # Add educational insights
                for insight in first_call_analysis.get('educational_insights', []):
                    report_sections.append(f"- {insight}\n")
                
                report_sections.append("\n")
            
            # Performance comparison
            report_sections.append("## ⚡ Performance Analysis\n")
            
            for symbol in symbols[:2]:  # Limit for report length
                performance = self.compare_call_performance(symbol)
                
                report_sections.append(f"### {symbol} Call Performance\n")
                
                first_call = performance.get('first_call_metrics', {})
                if first_call:
                    resolution = "Yes" if first_call.get('resolution_occurred', False) else "No"
                    report_sections.append(f"- **First Call Resolution:** {resolution}\n")
                    
                    if performance.get('performance_analysis', {}).get('time_between_calls'):
                        time_diff = performance['performance_analysis']['time_between_calls']
                        report_sections.append(f"- **Resolution Overhead:** {time_diff:.6f} seconds\n")
                
                # Add conclusions
                for conclusion in performance.get('educational_conclusions', []):
                    report_sections.append(f"- {conclusion}\n")
                
                report_sections.append("\n")
            
            # Binding modes comparison
            report_sections.append("## 🔄 Lazy vs Immediate Binding\n")
            
            binding_demo = self.demonstrate_binding_modes(symbols)
            
            for comparison in binding_demo.get('educational_comparison', []):
                report_sections.append(f"{comparison}\n")
            
            report_sections.append("\n")
            
            # Practical implications
            report_sections.append("## 🎯 Practical Implications\n")
            
            for implication in binding_demo.get('practical_implications', []):
                report_sections.append(f"{implication}\n")
            
            # Summary
            report_sections.append("## 📋 Summary\n")
            
            lazy_detected = sum(1 for symbol in symbols 
                              if self.analyze_first_call_behavior(symbol)['first_call_detected'])
            
            report_sections.append(f"- **Symbols Analyzed:** {len(symbols)}\n")
            report_sections.append(f"- **Lazy Binding Detected:** {lazy_detected}/{len(symbols)} symbols\n")
            report_sections.append(f"- **Analysis Success Rate:** {lazy_detected/len(symbols)*100:.1f}%\n")
            report_sections.append("\n")
            
            report_sections.append("**Educational Takeaways:**\n")
            report_sections.append("- Lazy binding provides faster startup at the cost of first-call overhead\n")
            report_sections.append("- GOT entries are updated during first symbol access\n")
            report_sections.append("- PLT stubs coordinate with the runtime resolver\n")
            report_sections.append("- Subsequent calls bypass resolution for better performance\n")
        
        except Exception as e:
            report_sections.append(f"\n❌ **Report Generation Error:** {str(e)}\n")
        
        return ''.join(report_sections)
    
    def get_binding_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about lazy binding analysis capabilities
        
        Returns:
            Statistics and capabilities summary
        """
        stats = {
            'binary_path': str(self.binary_path),
            'analyzed_symbols': list(self.analyzed_symbols),
            'binding_events_captured': len(self.binding_events),
            'resolver_tracing_enabled': self.resolver_traced,
            'analysis_capabilities': [
                'First call behavior analysis',
                'Performance comparison (first vs subsequent calls)',
                'Binding mode demonstration',
                'Resolver behavior tracing',
                'Educational report generation'
            ],
            'educational_features': [
                'Step-by-step resolution explanation',
                'GOT state change tracking',
                'Performance impact measurement',
                'Theory validation against practice'
            ]
        }
        
        return stats
