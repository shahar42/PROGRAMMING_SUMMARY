#!/usr/bin/env python3
"""
GDB Interface for GOT/PLT Runtime Analysis

Provides a controlled interface to GDB for runtime analysis of dynamic linking behavior.
Focuses on educational clarity while maintaining debugging capabilities.
"""

import subprocess
import tempfile
import time
import signal
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import threading
import queue
import re

logger = logging.getLogger("gdb-interface")


@dataclass
class BreakpointInfo:
    """Information about a GDB breakpoint"""
    number: int
    address: str
    symbol_name: str
    enabled: bool
    hit_count: int


@dataclass
class MemorySnapshot:
    """Snapshot of memory contents at a specific time"""
    address: str
    value: str
    timestamp: float
    context: str  # e.g., "before_call", "after_resolution"


class GDBInterface:
    """
    Educational GDB interface for dynamic linking analysis
    
    This class provides a controlled way to use GDB for runtime analysis
    while maintaining educational focus and safety.
    """
    
    def __init__(self, binary_path: str, timeout: int = 30):
        """
        Initialize GDB interface
        
        Args:
            binary_path: Path to binary to debug
            timeout: Maximum time for GDB operations
        """
        self.binary_path = Path(binary_path)
        self.timeout = timeout
        self.gdb_process = None
        self.gdb_stdin = None
        self.gdb_stdout = None
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.breakpoints = {}
        self.memory_snapshots = []
        self.is_running = False
        
        # Validate binary
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {self.binary_path}")
        
        # Check if GDB is available
        if not self._check_gdb_available():
            raise RuntimeError("GDB not available. Please install gdb package.")
    
    def _check_gdb_available(self) -> bool:
        """Check if GDB is available on the system"""
        try:
            result = subprocess.run(['gdb', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_session(self) -> bool:
        """
        Start GDB debugging session
        
        Returns:
            True if session started successfully
        """
        try:
            # Start GDB process
            self.gdb_process = subprocess.Popen(
                ['gdb', '--interpreter=mi2', '--quiet', str(self.binary_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0
            )
            
            self.gdb_stdin = self.gdb_process.stdin
            self.gdb_stdout = self.gdb_process.stdout
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_gdb_output, daemon=True)
            self.reader_thread.start()
            
            # Initialize GDB settings for educational analysis
            self._send_command("set confirm off")
            self._send_command("set pagination off")
            self._send_command("set print address on")
            self._send_command("set print symbol-filename on")
            
            self.is_running = True
            logger.info(f"GDB session started for {self.binary_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start GDB session: {e}")
            self.cleanup()
            return False
    
    def _read_gdb_output(self):
        """Background thread to read GDB output"""
        try:
            while self.is_running and self.gdb_process:
                line = self.gdb_stdout.readline()
                if line:
                    self.response_queue.put(line.strip())
                else:
                    break
        except Exception as e:
            logger.error(f"GDB output reader error: {e}")
    
    def _send_command(self, command: str, wait_for_response: bool = True) -> List[str]:
        """
        Send command to GDB and optionally wait for response
        
        Args:
            command: GDB command to send
            wait_for_response: Whether to wait for command completion
            
        Returns:
            List of response lines
        """
        if not self.is_running or not self.gdb_stdin:
            return []
        
        try:
            self.gdb_stdin.write(command + '\n')
            self.gdb_stdin.flush()
            
            if wait_for_response:
                return self._get_command_response(timeout=5)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to send GDB command '{command}': {e}")
            return []
    
    def _get_command_response(self, timeout: int = 5) -> List[str]:
        """Get response from GDB command"""
        responses = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.response_queue.get(timeout=0.1)
                responses.append(response)
                
                # Check for command completion indicators
                if '(gdb)' in response or '^done' in response or '^error' in response:
                    break
                    
            except queue.Empty:
                continue
        
        return responses
    
    def set_breakpoint(self, location: str, condition: str = None) -> Optional[BreakpointInfo]:
        """
        Set breakpoint at specified location
        
        Args:
            location: Breakpoint location (function name, address, etc.)
            condition: Optional breakpoint condition
            
        Returns:
            Breakpoint information if successful
        """
        try:
            # Construct breakpoint command
            cmd = f"break {location}"
            if condition:
                cmd += f" if {condition}"
            
            response = self._send_command(cmd)
            
            # Parse breakpoint number from response
            bp_number = None
            for line in response:
                if "Breakpoint" in line and "at" in line:
                    match = re.search(r'Breakpoint (\d+)', line)
                    if match:
                        bp_number = int(match.group(1))
                        break
            
            if bp_number:
                bp_info = BreakpointInfo(
                    number=bp_number,
                    address="unknown",  # Will be filled when hit
                    symbol_name=location,
                    enabled=True,
                    hit_count=0
                )
                self.breakpoints[bp_number] = bp_info
                logger.info(f"Breakpoint {bp_number} set at {location}")
                return bp_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to set breakpoint at {location}: {e}")
            return None
    
    def set_plt_breakpoints(self, symbol_names: List[str]) -> Dict[str, BreakpointInfo]:
        """
        Set breakpoints on PLT entries for specified symbols
        
        Args:
            symbol_names: List of symbol names to set PLT breakpoints for
            
        Returns:
            Dictionary mapping symbol names to breakpoint info
        """
        plt_breakpoints = {}
        
        for symbol in symbol_names:
            # Try to set breakpoint on PLT entry
            plt_symbol = f"{symbol}@plt"
            bp_info = self.set_breakpoint(plt_symbol)
            
            if bp_info:
                plt_breakpoints[symbol] = bp_info
            else:
                # Fallback: try the symbol directly
                bp_info = self.set_breakpoint(symbol)
                if bp_info:
                    plt_breakpoints[symbol] = bp_info
        
        return plt_breakpoints
    
    def run_program(self, args: List[str] = None) -> bool:
        """
        Run the program under GDB
        
        Args:
            args: Optional program arguments
            
        Returns:
            True if program started successfully
        """
        try:
            if args:
                cmd = f"run {' '.join(args)}"
            else:
                cmd = "run"
            
            response = self._send_command(cmd, wait_for_response=False)
            logger.info(f"Started program execution")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run program: {e}")
            return False
    
    def continue_execution(self) -> Dict[str, Any]:
        """
        Continue program execution until next breakpoint
        
        Returns:
            Information about breakpoint hit or program termination
        """
        try:
            response = self._send_command("continue")
            
            # Parse response for breakpoint hits
            result = {
                'status': 'unknown',
                'breakpoint': None,
                'address': None,
                'function': None,
                'stopped_reason': None
            }
            
            for line in response:
                if "Breakpoint" in line and "hit" in line:
                    result['status'] = 'breakpoint_hit'
                    # Extract breakpoint number
                    match = re.search(r'Breakpoint (\d+)', line)
                    if match:
                        bp_num = int(match.group(1))
                        result['breakpoint'] = bp_num
                        if bp_num in self.breakpoints:
                            self.breakpoints[bp_num].hit_count += 1
                
                elif "at 0x" in line:
                    # Extract address and function info
                    match = re.search(r'0x[0-9a-fA-F]+', line)
                    if match:
                        result['address'] = match.group(0)
                
                elif "in " in line and "from" in line:
                    # Extract function name
                    match = re.search(r'in ([^()]+)', line)
                    if match:
                        result['function'] = match.group(1).strip()
                
                elif "exited normally" in line or "exited with code" in line or "Program exited" in line:
                    result['status'] = 'program_exited'

                elif "Program terminated" in line or "terminated" in line:
                    result['status'] = 'program_terminated'
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to continue execution: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def examine_memory(self, address: str, format_spec: str = "x") -> Optional[MemorySnapshot]:
        """
        Examine memory at specified address
        
        Args:
            address: Memory address to examine
            format_spec: GDB format specification (x=hex, d=decimal, etc.)
            
        Returns:
            Memory snapshot information
        """
        try:
            cmd = f"x/{format_spec} {address}"
            response = self._send_command(cmd)
            
            # Parse memory value from response
            value = "unknown"
            for line in response:
                if ":" in line and "0x" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        value = parts[1].strip()
                        break
            
            snapshot = MemorySnapshot(
                address=address,
                value=value,
                timestamp=time.time(),
                context="examine_memory"
            )
            
            self.memory_snapshots.append(snapshot)
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to examine memory at {address}: {e}")
            return None
    
    def get_got_entry_value(self, symbol_name: str) -> Optional[str]:
        """
        Get current value of GOT entry for specified symbol
        
        Args:
            symbol_name: Symbol to look up in GOT
            
        Returns:
            Current GOT entry value
        """
        try:
            # Try to find GOT entry address
            info_response = self._send_command(f"info address {symbol_name}")
            
            got_address = None
            for line in info_response:
                if "Symbol" in line and "is at" in line:
                    match = re.search(r'0x[0-9a-fA-F]+', line)
                    if match:
                        got_address = match.group(0)
                        break
            
            if got_address:
                snapshot = self.examine_memory(got_address, "gx")
                return snapshot.value if snapshot else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get GOT entry for {symbol_name}: {e}")
            return None
    
    def get_backtrace(self) -> List[str]:
        """
        Get current call stack backtrace
        
        Returns:
            List of backtrace frames
        """
        try:
            response = self._send_command("backtrace")
            
            frames = []
            for line in response:
                if line.startswith("#"):
                    frames.append(line)
            
            return frames
            
        except Exception as e:
            logger.error(f"Failed to get backtrace: {e}")
            return []
    
    def get_register_info(self, register_names: List[str] = None) -> Dict[str, str]:
        """
        Get current register values
        
        Args:
            register_names: Specific registers to query (default: common ones)
            
        Returns:
            Dictionary mapping register names to values
        """
        if register_names is None:
            register_names = ['rip', 'rsp', 'rbp', 'rax', 'rdi', 'rsi']
        
        registers = {}
        
        try:
            for reg in register_names:
                response = self._send_command(f"info register {reg}")
                
                for line in response:
                    if reg in line and "0x" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            registers[reg] = parts[1]
                        break
            
            return registers
            
        except Exception as e:
            logger.error(f"Failed to get register info: {e}")
            return {}
    
    def single_step(self) -> Dict[str, Any]:
        """
        Execute single instruction step
        
        Returns:
            Information about the step
        """
        try:
            response = self._send_command("stepi")
            
            result = {
                'status': 'stepped',
                'address': None,
                'instruction': None
            }
            
            for line in response:
                if "0x" in line:
                    match = re.search(r'0x[0-9a-fA-F]+', line)
                    if match:
                        result['address'] = match.group(0)
                
                if ":" in line and ("mov" in line or "jmp" in line or "call" in line):
                    result['instruction'] = line.split(":", 1)[1].strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to single step: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def cleanup(self):
        """Clean up GDB session and resources"""
        try:
            self.is_running = False
            
            if self.gdb_process:
                # Send quit command
                if self.gdb_stdin:
                    try:
                        self.gdb_stdin.write("quit\n")
                        self.gdb_stdin.flush()
                    except:
                        pass
                
                # Give GDB time to exit gracefully
                try:
                    self.gdb_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Force termination
                    self.gdb_process.kill()
                    self.gdb_process.wait()
                
                self.gdb_process = None
            
            logger.info("GDB session cleaned up")
            
        except Exception as e:
            logger.error(f"Error during GDB cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.start_session():
            raise RuntimeError("Failed to start GDB session")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


class GDBAnalysisSession:
    """
    High-level interface for educational GDB analysis sessions
    
    Provides pre-configured analysis workflows for common dynamic linking scenarios.
    """
    
    def __init__(self, binary_path: str):
        """
        Initialize analysis session
        
        Args:
            binary_path: Path to binary to analyze
        """
        self.binary_path = binary_path
        self.gdb = None
        self.analysis_results = {}
    
    def analyze_lazy_binding(self, symbol_name: str) -> Dict[str, Any]:
        """
        Analyze lazy binding behavior for a specific symbol
        
        Args:
            symbol_name: Symbol to analyze (e.g., 'printf')
            
        Returns:
            Analysis results showing first call vs subsequent calls
        """
        results = {
            'symbol': symbol_name,
            'first_call': {},
            'second_call': {},
            'got_states': [],
            'analysis_notes': []
        }
        
        try:
            with GDBInterface(self.binary_path) as gdb:
                # Set breakpoint on PLT entry
                plt_bp = gdb.set_breakpoint(f"{symbol_name}@plt")
                if not plt_bp:
                    results['analysis_notes'].append(f"Failed to set PLT breakpoint for {symbol_name}")
                    return results
                
                # Start program
                gdb.run_program()
                
                # Wait for first PLT call
                first_hit = gdb.continue_execution()
                if first_hit['status'] == 'breakpoint_hit':
                    # Capture state before resolution
                    got_before = gdb.get_got_entry_value(symbol_name)
                    registers_before = gdb.get_register_info()
                    
                    results['first_call'] = {
                        'got_value_before': got_before,
                        'registers': registers_before,
                        'address': first_hit.get('address'),
                        'timestamp': time.time()
                    }
                    
                    # Continue execution (resolution happens)
                    second_hit = gdb.continue_execution()
                    
                    # Capture state after resolution
                    got_after = gdb.get_got_entry_value(symbol_name)
                    
                    results['first_call']['got_value_after'] = got_after
                    results['analysis_notes'].append(f"First call resolved {symbol_name}")
                
                # Wait for second PLT call
                third_hit = gdb.continue_execution()
                if third_hit['status'] == 'breakpoint_hit':
                    got_value = gdb.get_got_entry_value(symbol_name)
                    registers = gdb.get_register_info()
                    
                    results['second_call'] = {
                        'got_value': got_value,
                        'registers': registers,
                        'address': third_hit.get('address'),
                        'timestamp': time.time()
                    }
                    
                    results['analysis_notes'].append(f"Second call used resolved address")
                
                return results
                
        except Exception as e:
            results['analysis_notes'].append(f"Analysis failed: {str(e)}")
            return results
    
    def trace_symbol_resolution(self, symbol_name: str) -> Dict[str, Any]:
        """
        Trace the complete symbol resolution process
        
        Args:
            symbol_name: Symbol to trace
            
        Returns:
            Step-by-step resolution trace
        """
        results = {
            'symbol': symbol_name,
            'resolution_steps': [],
            'final_address': None,
            'resolver_calls': []
        }
        
        try:
            with GDBInterface(self.binary_path) as gdb:
                # Set breakpoint on resolver
                resolver_bp = gdb.set_breakpoint("_dl_runtime_resolve")
                plt_bp = gdb.set_breakpoint(f"{symbol_name}@plt")
                
                gdb.run_program()
                
                # Trace resolution process
                step = 1
                while True:
                    hit = gdb.continue_execution()
                    
                    if hit['status'] == 'breakpoint_hit':
                        if hit['breakpoint'] == resolver_bp.number:
                            # In resolver
                            backtrace = gdb.get_backtrace()
                            registers = gdb.get_register_info()
                            
                            results['resolver_calls'].append({
                                'step': step,
                                'backtrace': backtrace[:5],  # Top 5 frames
                                'registers': registers,
                                'timestamp': time.time()
                            })
                            
                        elif hit['breakpoint'] == plt_bp.number:
                            # In PLT
                            got_value = gdb.get_got_entry_value(symbol_name)
                            
                            results['resolution_steps'].append({
                                'step': step,
                                'location': 'PLT',
                                'got_value': got_value,
                                'address': hit.get('address'),
                                'timestamp': time.time()
                            })
                        
                        step += 1
                        
                        if step > 10:  # Safety limit
                            break
                    
                    elif hit['status'] in ['program_exited', 'program_terminated']:
                        break
                
                return results
                
        except Exception as e:
            results['resolution_steps'].append({
                'error': f"Tracing failed: {str(e)}"
            })
            return results
