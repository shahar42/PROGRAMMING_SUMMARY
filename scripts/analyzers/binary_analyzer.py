#!/usr/bin/env python3
"""
Core Binary Analysis Module for GOT/PLT Educational MCP Server

Implements the foundational data structures and analysis logic for examining
Global Offset Table (GOT) and Procedure Linkage Table (PLT) in ELF binaries.

Educational Focus: Provides progressive complexity explanations for dynamic linking concepts.
"""

import struct
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import logging

try:
    from elftools.elf.elffile import ELFFile
    from elftools.elf.sections import SymbolTableSection
    from elftools.elf.relocation import RelocationSection
    from elftools.elf.descriptions import describe_reloc_type
    from elftools.elf.relocation import RelocationSection
except ImportError:
    raise ImportError("Please install pyelftools: pip install pyelftools")

try:
    import capstone
except ImportError:
    raise ImportError("Please install capstone: pip install capstone")

logger = logging.getLogger("got-plt-analyzer")

@dataclass
class GOTEntry:
    """
    Represents a Global Offset Table entry
    
    Educational Context: GOT entries store addresses of global symbols that are
    resolved at runtime. This enables position-independent code and lazy binding.
    """
    address: str          # Virtual address of GOT entry
    symbol_name: str      # Associated symbol name  
    current_value: str    # Current resolved address (or placeholder)
    resolved: bool        # Whether symbol is resolved
    library_source: str   # Which library provides this symbol
    entry_index: int      # Index within GOT
    relocation_type: str  # Type of relocation (R_X86_64_JUMP_SLOT, etc.)
    binding_type: str     # LAZY, IMMEDIATE, or UNKNOWN

@dataclass  
class PLTStub:
    """
    Represents a Procedure Linkage Table stub
    
    Educational Context: PLT stubs are small pieces of code that handle
    dynamic symbol resolution. They work with GOT entries to implement lazy binding.
    """
    address: str              # Virtual address of PLT stub
    symbol_name: str          # Symbol this stub resolves
    got_reference: str        # GOT entry this stub references
    disassembly: List[str]    # Assembly instructions with annotations
    stub_type: str           # Architecture-specific stub type
    stub_index: int          # Index within PLT
    is_resolved: bool        # Whether target symbol is resolved
    target_address: str      # Final resolved address (if known)

@dataclass
class SymbolInfo:
    """
    Comprehensive symbol information for dynamic linking analysis
    
    Educational Context: Understanding symbol attributes is crucial for
    comprehending how dynamic linking and symbol resolution work.
    """
    name: str
    address: str
    binding: str       # LOCAL, GLOBAL, WEAK
    visibility: str    # DEFAULT, HIDDEN, PROTECTED
    section: str       # Which section contains this symbol
    library: str       # Source library (for imports)
    symbol_type: str   # FUNC, OBJECT, NOTYPE
    size: int         # Symbol size in bytes
    is_import: bool   # Whether this is an imported symbol
    is_export: bool   # Whether this is an exported symbol


class BinaryAnalyzer:
    """
    Core binary analysis engine for GOT/PLT educational analysis
    
    This class provides the foundational analysis capabilities with educational
    explanations at different complexity levels.
    """
    
    def __init__(self, binary_path: str):
        """
        Initialize binary analyzer
        
        Args:
            binary_path: Path to ELF binary to analyze
        """
        self.binary_path = Path(binary_path)
        self.elffile = None
        self.architecture = None
        self.got_entries = []
        self.plt_stubs = []
        self.dynamic_symbols = []
        
        self._load_binary()
        self._detect_architecture()
        
    def _load_binary(self):
        """Load and validate ELF binary"""
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {self.binary_path}")
            
        try:
            self.file_handle = open(self.binary_path, 'rb')
            self.elffile = ELFFile(self.file_handle)
                
            # Validate it's an ELF file
            if not self.elffile.header['e_type'] in ['ET_EXEC', 'ET_DYN']:
                raise ValueError("File must be an executable or shared object")
                
        except Exception as e:
            raise ValueError(f"Failed to load ELF binary: {e}")
    
    def _detect_architecture(self):
        """Detect target architecture for arch-specific analysis"""
        machine = self.elffile.header['e_machine']
        if machine == 'EM_X86_64':
            self.architecture = 'x86_64'
        elif machine == 'EM_AARCH64':
            self.architecture = 'aarch64'
        elif machine == 'EM_RISCV':
            self.architecture = 'riscv64'
        else:
            self.architecture = 'unknown'
            logger.warning(f"Unsupported architecture: {machine}")
    
    def analyze_got_table(self) -> List[GOTEntry]:
        """
        Analyze Global Offset Table entries
        
        Returns:
            List of GOT entries with educational context
        """
        got_entries = []
        
        # Find .got.plt section
        got_plt_section = self.elffile.get_section_by_name('.got.plt')
        if not got_plt_section:
            # Try .got section as fallback
            got_plt_section = self.elffile.get_section_by_name('.got')
            
        if not got_plt_section:
            logger.warning("No GOT section found in binary")
            return got_entries
        
        # Find dynamic relocations
        reloc_sections = [s for s in self.elffile.iter_sections() 
                         if isinstance(s, RelocationSection)]
        
        # Find dynamic symbol table
        dynsym_section = self.elffile.get_section_by_name('.dynsym')
        if not dynsym_section:
            logger.warning("No dynamic symbol table found")
            return got_entries
        
        # Process relocations to build GOT entries
        entry_index = 0
        for reloc_section in reloc_sections:
            if reloc_section.name in ['.rela.plt', '.rel.plt']:
                for relocation in reloc_section.iter_relocations():
                    symbol = dynsym_section.get_symbol(relocation['r_info_sym'])
                    if symbol:
                        got_entry = GOTEntry(
                            address=f"0x{relocation['r_offset']:x}",
                            symbol_name=symbol.name,
                            current_value=f"0x{relocation['r_addend'] if 'r_addend' in relocation.entry else 0:x}",
                            resolved=False,  # Static analysis can't determine runtime state
                            library_source="unknown",  # Would need runtime analysis
                            entry_index=entry_index,
                            relocation_type=describe_reloc_type(relocation['r_info_type'], self.elffile),
                            binding_type="LAZY"  # Most PLT relocations are lazy
                        )
                        got_entries.append(got_entry)
                        entry_index += 1
        
        self.got_entries = got_entries
        return got_entries
    
    def analyze_plt_stubs(self) -> List[PLTStub]:
        """
        Analyze Procedure Linkage Table stubs
        
        Returns:
            List of PLT stubs with disassembly and educational context
        """
        plt_stubs = []
        
        # Find .plt section
        plt_section = self.elffile.get_section_by_name('.plt')
        if not plt_section:
            logger.warning("No PLT section found in binary")
            return plt_stubs
        
        # Get PLT section data
        plt_data = plt_section.data()
        plt_addr = plt_section['sh_addr']
        
        # Set up disassembler based on architecture
        if self.architecture == 'x86_64':
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        elif self.architecture == 'aarch64':
            md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
        else:
            logger.warning(f"Disassembly not supported for {self.architecture}")
            return plt_stubs
        
        md.detail = True
        
        # Disassemble PLT section
        disasm = list(md.disasm(plt_data, plt_addr))
        
        # Parse PLT stubs (architecture-specific logic)
        if self.architecture == 'x86_64':
            plt_stubs = self._parse_x86_64_plt_stubs(disasm, plt_addr)
        elif self.architecture == 'aarch64':
            plt_stubs = self._parse_aarch64_plt_stubs(disasm, plt_addr)
        
        self.plt_stubs = plt_stubs
        return plt_stubs
    
    def _parse_x86_64_plt_stubs(self, disasm: List, plt_base: int) -> List[PLTStub]:
        """Parse x86-64 specific PLT stubs with proper symbol resolution"""
        stubs = []
        
        # First, build a mapping of PLT relocations to symbol names
        plt_symbol_map = {}
        
        # Find PLT relocation section
        reloc_sections = [s for s in self.elffile.iter_sections() 
                         if isinstance(s, RelocationSection)]
        
        dynsym_section = self.elffile.get_section_by_name('.dynsym')
        
        if dynsym_section:
            for reloc_section in reloc_sections:
                if reloc_section.name in ['.rela.plt', '.rel.plt']:
                    for i, relocation in enumerate(reloc_section.iter_relocations()):
                        symbol = dynsym_section.get_symbol(relocation['r_info_sym'])
                        if symbol and symbol.name:
                            # Map PLT entry index to symbol name
                            # PLT[0] is resolver, so PLT[1] is first function
                            plt_symbol_map[i + 1] = symbol.name
        
        # Parse PLT stubs
        current_stub = []
        stub_start_addr = None
        stub_index = 0
        
        for insn in disasm:
            if len(current_stub) == 0:
                stub_start_addr = insn.address
                
            current_stub.append(f"{insn.mnemonic} {insn.op_str}")
            
            # x86-64 PLT stub is typically 3 instructions
            if len(current_stub) == 3:
                # Get symbol name from our mapping
                symbol_name = plt_symbol_map.get(stub_index + 1, f"unknown_symbol_{stub_index}")
                got_reference = "0x0"
                
                # Look for GOT reference in first instruction (usually jmp *addr(%rip))
                first_insn = current_stub[0]
                if "jmp" in first_insn and "*" in first_insn:
                    # Extract address from jmp instruction
                    parts = first_insn.split()
                    if len(parts) > 1:
                        addr_part = parts[1].replace("*", "").replace("(%rip)", "")
                        try:
                            got_reference = addr_part
                        except:
                            pass
                
                stub = PLTStub(
                    address=f"0x{stub_start_addr:x}",
                    symbol_name=symbol_name,
                    got_reference=got_reference,
                    disassembly=current_stub.copy(),
                    stub_type="x86_64_standard",
                    stub_index=stub_index,
                    is_resolved=False,
                    target_address="0x0"
                )
                stubs.append(stub)
                
                current_stub = []
                stub_index += 1
        
        return stubs

    def _parse_aarch64_plt_stubs(self, disasm: List, plt_base: int) -> List[PLTStub]:
        """Parse AArch64 specific PLT stubs"""
        # Implementation for ARM64 PLT parsing
        # ARM64 PLT stubs have different structure than x86-64
        stubs = []
        # TODO: Implement ARM64-specific PLT parsing
        logger.info("AArch64 PLT parsing not yet implemented")
        return stubs
    
    def list_dynamic_symbols(self, category: str = "all") -> List[SymbolInfo]:
        """
        List symbols requiring dynamic resolution
        
        Args:
            category: "imports", "exports", "all"
            
        Returns:
            List of dynamic symbols with comprehensive information
        """
        symbols = []
        
        # Get dynamic symbol table
        dynsym_section = self.elffile.get_section_by_name('.dynsym')
        if not dynsym_section:
            logger.warning("No dynamic symbol table found")
            return symbols
        
        for symbol in dynsym_section.iter_symbols():
            if symbol.name:  # Skip unnamed symbols
                symbol_info = SymbolInfo(
                    name=symbol.name,
                    address=f"0x{symbol['st_value']:x}",
                    binding=symbol['st_info']['bind'],
                    visibility=symbol['st_other']['visibility'],
                    section=symbol.entry.get('st_shndx', 'UNDEF'),
                    library="unknown",  # Would need to parse dependencies
                    symbol_type=symbol['st_info']['type'],
                    size=symbol['st_size'],
                    is_import=symbol['st_shndx'] == 'SHN_UNDEF',
                    is_export=symbol['st_shndx'] != 'SHN_UNDEF' and symbol['st_info']['bind'] != 'STB_LOCAL'
                )
                
                # Filter by category
                if category == "imports" and not symbol_info.is_import:
                    continue
                elif category == "exports" and not symbol_info.is_export:
                    continue
                    
                symbols.append(symbol_info)
        
        self.dynamic_symbols = symbols
        return symbols
    
    def get_binary_info(self) -> Dict[str, Any]:
        """
        Get comprehensive binary information for educational context
        
        Returns:
            Dictionary with binary metadata and linking information
        """
        info = {
            "file_path": str(self.binary_path),
            "architecture": self.architecture,
            "entry_point": f"0x{self.elffile.header['e_entry']:x}",
            "file_type": self.elffile.header['e_type'],
            "sections": {},
            "dynamic_info": {},
            "linking_info": {
                "has_got": self.elffile.get_section_by_name('.got') is not None,
                "has_plt": self.elffile.get_section_by_name('.plt') is not None,
                "has_got_plt": self.elffile.get_section_by_name('.got.plt') is not None,
                "is_dynamically_linked": self.elffile.get_section_by_name('.dynamic') is not None,
                "is_pie": self.elffile.header['e_type'] == 'ET_DYN'
            }
        }
        
        # Add section information
        for section in self.elffile.iter_sections():
            if section.name in ['.got', '.plt', '.got.plt', '.dynsym', '.dynstr', '.rela.plt']:
                info["sections"][section.name] = {
                    "address": f"0x{section['sh_addr']:x}",
                    "size": section['sh_size'],
                    "offset": section['sh_offset']
                }
        
        return info
