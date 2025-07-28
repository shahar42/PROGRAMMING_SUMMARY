#!/usr/bin/env python3
"""
Runtime Analyzer for GOT/PLT Educational MCP Server

Analyzes GOT/PLT behavior during program execution using GDB integration.
Provides educational insights into dynamic linking runtime behavior.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from utils.gdb_interface import GDBInterface, GDBAnalysisSession, MemorySnapshot
from analyzers.binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub

logger = logging.getLogger("runtime-analyzer")


@dataclass
class RuntimeGOTEntry:
    """Runtime state of a GOT entry"""
    symbol_name: str
    address: str
    initial_value: str
    current_value: str
    resolved: bool
    resolution_timestamp: Optional[float]
    access_count: int


@dataclass
class SymbolResolutionTrace:
    """Trace of symbol resolution process"""
    symbol_name: str
    resolution_steps: List[Dict[str, Any]]
    total_time: float
    resolver_calls: int
    final_address: str
    successful: bool


class RuntimeAnalyzer:
    """
    Analyzes GOT/PLT behavior during program execution
    
    This class provides educational runtime analysis capabilities that complement
    the static analysis from BinaryAnalyzer. It shows how dynamic linking
    actually works during program execution.
    """
    
    def __init__(self, binary_path: str):
        """
        Initialize runtime analyzer
        
        Args:
            binary_path: Path to ELF binary to analyze
        """
        self.binary_path = Path(binary_path)
        self.static_analyzer = None
        self.gdb_session = None
        self.runtime_got_entries = {}
        self.resolution_traces = {}
        self.breakpoints = {}
        
        # Validate binary exists
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {self.binary_path}")
        
        # Initialize static analyzer for comparison
        try:
            self.static_analyzer = BinaryAnalyzer(str(self.binary_path))
        except Exception as e:
            logger.warning(f"Static analysis failed: {e}")
    
    def get_runtime_got_state(self, symbols: List[str] = None) -> Dict[str, RuntimeGOTEntry]:
        """
        Capture runtime GOT state for specified symbols
        
        Args:
            symbols: List of symbols to analyze (None for all)
            
        Returns:
            Dictionary mapping symbol names to runtime GOT entries
        """
        runtime_entries = {}
        
        if not symbols and self.static_analyzer:
            # Get symbols from static analysis
            static_got = self.static_analyzer.analyze_got_table()
            symbols = [entry.symbol_name for entry in static_got if entry.symbol_name]
        
        if not symbols:
            logger.warning("No symbols specified for runtime GOT analysis")
            return runtime_entries
        
        try:
            with GDBInterface(str(self.binary_path)) as gdb:
                # Start program execution
                gdb.run_program()
                
                # Get initial GOT state
                initial_state = {}
                for symbol in symbols:
                    initial_value = gdb.get_got_entry_value(symbol)
                    initial_state[symbol] = initial_value
                
                # Continue execution to let some resolution happen
                hit = gdb.continue_execution()
                
                # Capture current GOT state
                for symbol in symbols:
                    current_value = gdb.get_got_entry_value(symbol)
                    initial_value = initial_state.get(symbol, "unknown")
                    
                    # Determine if resolved
                    resolved = False
                    if initial_value != "unknown" and current_value != "unknown":
                        resolved = initial_value != current_value
                    
                    runtime_entry = RuntimeGOTEntry(
                        symbol_name=symbol,
                        address="unknown",  # Would need additional GDB commands
                        initial_value=initial_value or "unknown",
                        current_value=current_value or "unknown",
                        resolved=resolved,
                        resolution_timestamp=time.time() if resolved else None,
                        access_count=1 if resolved else 0
                    )
                    
                    runtime_entries[symbol] = runtime_entry
        
        except Exception as e:
            logger.error(f"Runtime GOT state capture failed: {e}")
        
        return runtime_entries
    
    def trace_symbol_resolution(self, symbol_name: str) -> SymbolResolutionTrace:
        """
        Trace the complete symbol resolution process for a symbol
        
        Args:
            symbol_name: Symbol to trace during resolution
            
        Returns:
            Detailed trace of the resolution process
        """
        start_time = time.time()
        
        trace = SymbolResolutionTrace(
            symbol_name=symbol_name,
            resolution_steps=[],
            total_time=0.0,
            resolver_calls=0,
            final_address="unknown",
            successful=False
        )
        
        try:
            # Use high-level analysis session
            session = GDBAnalysisSession(str(self.binary_path))
            results = session.trace_symbol_resolution(symbol_name)
            
            # Convert results to our trace format
            trace.resolution_steps = results.get('resolution_steps', [])
            trace.resolver_calls = len(results.get('resolver_calls', []))
            trace.final_address = results.get('final_address', "unknown")
            trace.successful = len(trace.resolution_steps) > 0
            trace.total_time = time.time() - start_time
            
            # Add educational annotations
            for step in trace.resolution_steps:
                if step.get('location') == 'PLT':
                    step['educational_note'] = "PLT stub executed - lazy binding in progress"
                elif 'resolver' in step.get('location', '').lower():
                    step['educational_note'] = "Runtime resolver finding symbol address"
            
        except Exception as e:
            logger.error(f"Symbol resolution tracing failed for {symbol_name}: {e}")
            trace.resolution_steps.append({
                'error': f"Tracing failed: {str(e)}",
                'educational_note': "Runtime tracing requires GDB and may fail with complex binaries"
            })
        
        return trace
    
    def demonstrate_lazy_binding(self, symbol_name: str) -> Dict[str, Any]:
        """
        Demonstrate lazy binding behavior showing first vs subsequent calls
        
        Args:
            symbol_name: Symbol to demonstrate lazy binding for
            
        Returns:
            Analysis showing difference between first and subsequent calls
        """
        demonstration = {
            'symbol': symbol_name,
            'first_call_analysis': {},
            'subsequent_call_analysis': {},
            'performance_comparison': {},
            'educational_insights': []
        }
        
        try:
            # Use high-level analysis session
            session = GDBAnalysisSession(str(self.binary_path))
            results = session.analyze_lazy_binding(symbol_name)
            
            # Extract first call information
            first_call = results.get('first_call', {})
            if first_call:
                demonstration['first_call_analysis'] = {
                    'got_before_resolution': first_call.get('got_value_before', 'unknown'),
                    'got_after_resolution': first_call.get('got_value_after', 'unknown'),
                    'address': first_call.get('address', 'unknown'),
                    'registers': first_call.get('registers', {}),
                    'educational_note': "First call triggers symbol resolution via _dl_runtime_resolve"
                }
                
                # Check if resolution actually happened
                got_before = first_call.get('got_value_before', '')
                got_after = first_call.get('got_value_after', '')
                if got_before != got_after and got_after != 'unknown':
                    demonstration['educational_insights'].append(
                        f"✅ Lazy binding confirmed: GOT entry changed from {got_before} to {got_after}"
                    )
                else:
                    demonstration['educational_insights'].append(
                        "⚠️ GOT entry did not change - symbol may already be resolved or use immediate binding"
                    )
            
            # Extract subsequent call information
            second_call = results.get('second_call', {})
            if second_call:
                demonstration['subsequent_call_analysis'] = {
                    'got_value': second_call.get('got_value', 'unknown'),
                    'address': second_call.get('address', 'unknown'),
                    'registers': second_call.get('registers', {}),
                    'educational_note': "Subsequent calls jump directly through resolved GOT entry"
                }
                
                # Compare with first call
                if first_call and second_call:
                    first_time = first_call.get('timestamp', 0)
                    second_time = second_call.get('timestamp', 0)
                    
                    if second_time > first_time:
                        demonstration['performance_comparison'] = {
                            'time_difference': second_time - first_time,
                            'educational_note': "Time difference shows resolution overhead on first call"
                        }
            
            # Add analysis notes
            for note in results.get('analysis_notes', []):
                demonstration['educational_insights'].append(f"📝 {note}")
            
            # Add educational context
            if not demonstration['educational_insights']:
                demonstration['educational_insights'].append(
                    "🔍 Runtime tracing may require multiple function calls to observe lazy binding"
                )
        
        except Exception as e:
            logger.error(f"Lazy binding demonstration failed for {symbol_name}: {e}")
            demonstration['educational_insights'].append(
                f"❌ Analysis failed: {str(e)}"
            )
        
        return demonstration
    
    def compare_binding_modes(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Compare lazy vs immediate binding behavior
        
        Args:
            symbols: Symbols to analyze (None for default set)
            
        Returns:
            Comparison of binding modes with performance analysis
        """
        if symbols is None:
            symbols = ['printf', 'malloc', 'free']  # Common symbols
        
        comparison = {
            'lazy_binding_results': {},
            'immediate_binding_results': {},
            'performance_analysis': {},
            'educational_summary': []
        }
        
        try:
            # Test lazy binding (default)
            logger.info("Analyzing lazy binding behavior")
            for symbol in symbols:
                lazy_result = self.demonstrate_lazy_binding(symbol)
                comparison['lazy_binding_results'][symbol] = lazy_result
            
            # Note: Testing immediate binding would require running with LD_BIND_NOW=1
            # This is left as an educational exercise since it requires process control
            
            comparison['educational_summary'].extend([
                "🔍 Lazy binding analysis completed for specified symbols",
                "💡 To compare with immediate binding, run the same binary with LD_BIND_NOW=1",
                "📚 Immediate binding resolves all symbols at load time, eliminating PLT overhead",
                "⚖️ Trade-off: Faster function calls vs slower program startup"
            ])
            
            # Analyze results for educational insights
            lazy_symbols_with_resolution = 0
            for symbol, result in comparison['lazy_binding_results'].items():
                if result.get('first_call_analysis', {}).get('got_after_resolution', 'unknown') != 'unknown':
                    lazy_symbols_with_resolution += 1
            
            comparison['performance_analysis'] = {
                'symbols_analyzed': len(symbols),
                'symbols_showing_lazy_binding': lazy_symbols_with_resolution,
                'binding_effectiveness': lazy_symbols_with_resolution / len(symbols) if symbols else 0
            }
        
        except Exception as e:
            logger.error(f"Binding mode comparison failed: {e}")
            comparison['educational_summary'].append(f"❌ Analysis failed: {str(e)}")
        
        return comparison
    
    def runtime_got_snapshot(self, execution_point: str = "main") -> Dict[str, Any]:
        """
        Capture GOT state snapshot at specific execution point
        
        Args:
            execution_point: Function name to break at for snapshot
            
        Returns:
            GOT state snapshot with analysis
        """
        snapshot = {
            'execution_point': execution_point,
            'timestamp': time.time(),
            'got_entries': {},
            'memory_layout': {},
            'educational_context': []
        }
        
        try:
            with GDBInterface(str(self.binary_path)) as gdb:
                # Set breakpoint at execution point
                bp = gdb.set_breakpoint(execution_point)
                if not bp:
                    snapshot['educational_context'].append(
                        f"⚠️ Could not set breakpoint at {execution_point} - using program start"
                    )
                
                # Start program
                gdb.run_program()
                
                # Continue to breakpoint
                hit = gdb.continue_execution()
                
                if hit['status'] == 'breakpoint_hit':
                    snapshot['educational_context'].append(
                        f"✅ Stopped at {execution_point} - capturing GOT state"
                    )
                    
                    # Get symbols from static analysis
                    if self.static_analyzer:
                        static_got = self.static_analyzer.analyze_got_table()
                        
                        for entry in static_got[:10]:  # Limit for performance
                            if entry.symbol_name:
                                current_value = gdb.get_got_entry_value(entry.symbol_name)
                                
                                snapshot['got_entries'][entry.symbol_name] = {
                                    'static_address': entry.address,
                                    'current_value': current_value or 'unknown',
                                    'relocation_type': getattr(entry, 'relocation_type', 'unknown'),
                                    'resolved_status': 'resolved' if current_value and current_value != 'unknown' else 'unresolved'
                                }
                    
                    # Get memory layout information
                    registers = gdb.get_register_info(['rip', 'rsp', 'rbp'])
                    snapshot['memory_layout'] = {
                        'instruction_pointer': registers.get('rip', 'unknown'),
                        'stack_pointer': registers.get('rsp', 'unknown'),
                        'base_pointer': registers.get('rbp', 'unknown')
                    }
                    
                    # Educational context
                    resolved_count = sum(1 for entry in snapshot['got_entries'].values() 
                                       if entry['resolved_status'] == 'resolved')
                    total_count = len(snapshot['got_entries'])
                    
                    snapshot['educational_context'].extend([
                        f"📊 GOT Snapshot: {resolved_count}/{total_count} entries resolved",
                        f"🎯 Execution point: {execution_point} at {registers.get('rip', 'unknown')}",
                        "💡 Unresolved entries will be resolved on first access (lazy binding)"
                    ])
                
                else:
                    snapshot['educational_context'].append(
                        f"⚠️ Could not reach {execution_point} - program may have exited early"
                    )
        
        except Exception as e:
            logger.error(f"GOT snapshot failed: {e}")
            snapshot['educational_context'].append(f"❌ Snapshot failed: {str(e)}")
        
        return snapshot
    
    def measure_resolution_overhead(self, symbol_name: str, iterations: int = 5) -> Dict[str, Any]:
        """
        Measure performance impact of symbol resolution
        
        Args:
            symbol_name: Symbol to measure resolution overhead for
            iterations: Number of iterations for timing measurement
            
        Returns:
            Performance measurements and analysis
        """
        measurements = {
            'symbol': symbol_name,
            'iterations': iterations,
            'resolution_times': [],
            'call_times': [],
            'average_resolution_overhead': 0.0,
            'educational_analysis': []
        }
        
        try:
            # Note: Precise timing measurement requires more sophisticated GDB scripting
            # This implementation provides educational framework
            
            session = GDBAnalysisSession(str(self.binary_path))
            
            for i in range(iterations):
                logger.info(f"Measuring resolution overhead - iteration {i+1}/{iterations}")
                
                result = session.analyze_lazy_binding(symbol_name)
                
                # Extract timing information if available
                first_call = result.get('first_call', {})
                second_call = result.get('second_call', {})
                
                if first_call.get('timestamp') and second_call.get('timestamp'):
                    resolution_time = second_call['timestamp'] - first_call['timestamp']
                    measurements['resolution_times'].append(resolution_time)
            
            # Calculate averages
            if measurements['resolution_times']:
                measurements['average_resolution_overhead'] = sum(measurements['resolution_times']) / len(measurements['resolution_times'])
                
                measurements['educational_analysis'].extend([
                    f"📊 Measured {len(measurements['resolution_times'])} resolution cycles",
                    f"⏱️ Average resolution overhead: {measurements['average_resolution_overhead']:.6f} seconds",
                    "💡 Resolution overhead occurs only on first call to each symbol",
                    "🚀 Subsequent calls have minimal overhead (direct GOT jump)"
                ])
            else:
                measurements['educational_analysis'].extend([
                    "⚠️ Could not measure precise timing - this requires specialized profiling",
                    "💡 Resolution overhead is typically measured in microseconds",
                    "📚 Academic studies show 10-100x slower first call vs subsequent calls"
                ])
        
        except Exception as e:
            logger.error(f"Resolution overhead measurement failed: {e}")
            measurements['educational_analysis'].append(f"❌ Measurement failed: {str(e)}")
        
        return measurements
    
    def analyze_plt_behavior(self, symbol_names: List[str]) -> Dict[str, Any]:
        """
        Analyze PLT behavior for multiple symbols during execution
        
        Args:
            symbol_names: List of symbols to analyze PLT behavior for
            
        Returns:
            Analysis of PLT stub behavior during execution
        """
        analysis = {
            'symbols_analyzed': symbol_names,
            'plt_interactions': {},
            'call_patterns': {},
            'educational_observations': []
        }
        
        try:
            with GDBInterface(str(self.binary_path)) as gdb:
                # Set PLT breakpoints for all symbols
                plt_breakpoints = gdb.set_plt_breakpoints(symbol_names)
                
                analysis['educational_observations'].append(
                    f"🎯 Set PLT breakpoints for {len(plt_breakpoints)}/{len(symbol_names)} symbols"
                )
                
                # Start program
                gdb.run_program()
                
                # Track PLT interactions
                interaction_count = 0
                max_interactions = 20  # Limit for educational purposes
                
                while interaction_count < max_interactions:
                    hit = gdb.continue_execution()
                    
                    if hit['status'] == 'breakpoint_hit':
                        interaction_count += 1
                        
                        # Identify which symbol's PLT was hit
                        hit_symbol = None
                        for symbol, bp_info in plt_breakpoints.items():
                            if hit['breakpoint'] == bp_info.number:
                                hit_symbol = symbol
                                break
                        
                        if hit_symbol:
                            if hit_symbol not in analysis['plt_interactions']:
                                analysis['plt_interactions'][hit_symbol] = []
                            
                            # Capture interaction details
                            got_value = gdb.get_got_entry_value(hit_symbol)
                            registers = gdb.get_register_info(['rip', 'rsp'])
                            
                            interaction = {
                                'call_number': len(analysis['plt_interactions'][hit_symbol]) + 1,
                                'timestamp': time.time(),
                                'got_value': got_value,
                                'instruction_pointer': registers.get('rip', 'unknown'),
                                'stack_pointer': registers.get('rsp', 'unknown')
                            }
                            
                            analysis['plt_interactions'][hit_symbol].append(interaction)
                            
                            # Educational annotation
                            if interaction['call_number'] == 1:
                                interaction['educational_note'] = "First call - may trigger symbol resolution"
                            else:
                                interaction['educational_note'] = "Subsequent call - should use resolved address"
                    
                    elif hit['status'] in ['program_exited', 'program_terminated']:
                        break
                
                # Analyze call patterns
                for symbol, interactions in analysis['plt_interactions'].items():
                    analysis['call_patterns'][symbol] = {
                        'total_calls': len(interactions),
                        'first_call_got': interactions[0]['got_value'] if interactions else 'unknown',
                        'last_call_got': interactions[-1]['got_value'] if interactions else 'unknown',
                        'got_changed': False
                    }
                    
                    # Check if GOT value changed (indicating resolution)
                    if len(interactions) > 1:
                        first_got = interactions[0]['got_value']
                        last_got = interactions[-1]['got_value']
                        analysis['call_patterns'][symbol]['got_changed'] = first_got != last_got
                
                # Educational summary
                total_calls = sum(pattern['total_calls'] for pattern in analysis['call_patterns'].values())
                symbols_with_resolution = sum(1 for pattern in analysis['call_patterns'].values() if pattern['got_changed'])
                
                analysis['educational_observations'].extend([
                    f"📊 Captured {total_calls} PLT interactions across {len(analysis['plt_interactions'])} symbols",
                    f"🔄 {symbols_with_resolution} symbols showed GOT value changes (resolution)",
                    "💡 PLT stubs act as trampolines for all external function calls",
                    "🎯 Each PLT entry corresponds to one external symbol"
                ])
        
        except Exception as e:
            logger.error(f"PLT behavior analysis failed: {e}")
            analysis['educational_observations'].append(f"❌ Analysis failed: {str(e)}")
        
        return analysis
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of all runtime analysis capabilities
        
        Returns:
            Summary of runtime analysis features and current state
        """
        summary = {
            'binary_path': str(self.binary_path),
            'static_analysis_available': self.static_analyzer is not None,
            'gdb_available': True,  # Checked during GDBInterface init
            'analysis_capabilities': [
                'Runtime GOT state capture',
                'Symbol resolution tracing',
                'Lazy binding demonstration',
                'Binding mode comparison',
                'GOT snapshots at execution points',
                'Resolution overhead measurement',
                'PLT behavior analysis'
            ],
            'educational_features': [
                'Step-by-step resolution explanations',
                'Performance impact analysis',
                'Theory vs practice validation',
                'Interactive debugging scenarios'
            ],
            'requirements': [
                'GDB installed and accessible',
                'Binary with debug information (recommended)',
                'Dynamically linked executable',
                'Sufficient system permissions'
            ]
        }
        
        # Test GDB availability
        try:
            with GDBInterface(str(self.binary_path), timeout=5) as gdb:
                summary['gdb_test'] = 'successful'
        except Exception as e:
            summary['gdb_test'] = f'failed: {str(e)}'
        
        return summary
