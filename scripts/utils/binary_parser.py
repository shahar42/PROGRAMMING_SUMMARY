#!/usr/bin/env python3
"""
Binary Parser Utilities for GOT/PLT Analysis

Provides low-level binary parsing utilities and helper functions for ELF analysis.
Focuses on educational clarity while maintaining technical accuracy.
"""

import struct
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger("binary-parser")


class BinaryParser:
    """
    Low-level binary parsing utilities
    
    Educational Focus: Provides clear, well-documented parsing functions that
    help users understand the binary format while extracting necessary information.
    """
    
    @staticmethod
    def is_elf_file(file_path: str) -> bool:
        """
        Check if file is a valid ELF binary
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is ELF format
        """
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x7fELF'
        except (IOError, OSError):
            return False
    
    @staticmethod
    def get_elf_header_info(file_path: str) -> Dict[str, Any]:
        """
        Extract basic ELF header information
        
        Args:
            file_path: Path to ELF file
            
        Returns:
            Dictionary with header information
        """
        if not BinaryParser.is_elf_file(file_path):
            raise ValueError("File is not a valid ELF binary")
        
        try:
            with open(file_path, 'rb') as f:
                # Read ELF header
                f.seek(0)
                e_ident = f.read(16)  # ELF identification
                
                # Determine architecture and endianness
                ei_class = e_ident[4]  # 32-bit (1) or 64-bit (2)
                ei_data = e_ident[5]   # Little (1) or big (2) endian
                
                # Architecture mapping
                arch_map = {1: "32-bit", 2: "64-bit"}
                endian_map = {1: "little-endian", 2: "big-endian"}
                
                return {
                    "class": arch_map.get(ei_class, "unknown"),
                    "endianness": endian_map.get(ei_data, "unknown"),
                    "version": e_ident[6],
                    "osabi": e_ident[7],
                    "is_64bit": ei_class == 2,
                    "is_little_endian": ei_data == 1
                }
                
        except Exception as e:
            raise ValueError(f"Failed to parse ELF header: {e}")
    
    @staticmethod
    def find_section_by_name(file_path: str, section_name: str) -> Optional[Dict[str, Any]]:
        """
        Find section by name using objdump (fallback method)
        
        Args:
            file_path: Path to ELF file
            section_name: Name of section to find
            
        Returns:
            Section information or None if not found
        """
        try:
            # Use objdump to get section information
            result = subprocess.run(
                ['objdump', '-h', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.split('\n')
            for line in lines:
                if section_name in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        return {
                            "name": section_name,
                            "size": int(parts[2], 16),
                            "vma": int(parts[3], 16),
                            "lma": int(parts[4], 16),
                            "file_offset": int(parts[5], 16)
                        }
            
            return None
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"objdump not available or failed for {file_path}")
            return None
    
    @staticmethod
    def extract_strings_from_section(file_path: str, section_name: str) -> List[str]:
        """
        Extract strings from a specific section
        
        Args:
            file_path: Path to ELF file
            section_name: Section to extract strings from
            
        Returns:
            List of strings found in section
        """
        try:
            # Use objdump to extract strings from section
            result = subprocess.run(
                ['objdump', '-s', '-j', section_name, file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            strings = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                # Parse objdump hex output
                if line.strip() and not line.startswith('Contents') and ':' in line:
                    # Extract hex bytes and convert to string
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        hex_data = parts[1].split()[:4]  # Max 4 hex groups per line
                        for hex_group in hex_data:
                            if len(hex_group) == 8:  # 4 bytes in hex
                                # Convert hex to bytes and extract printable chars
                                try:
                                    bytes_data = bytes.fromhex(hex_group)
                                    string_chars = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in bytes_data)
                                    if len(string_chars.replace('.', '')) > 2:
                                        strings.append(string_chars)
                                except ValueError:
                                    continue
            
            return strings
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"Failed to extract strings from {section_name}")
            return []
    
    @staticmethod
    def get_library_dependencies(file_path: str) -> List[str]:
        """
        Get shared library dependencies
        
        Args:
            file_path: Path to ELF file
            
        Returns:
            List of required shared libraries
        """
        try:
            # Use ldd to get library dependencies
            result = subprocess.run(
                ['ldd', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            dependencies = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if '=>' in line:
                    # Parse "libname.so => /path/to/lib"
                    parts = line.split('=>')
                    if len(parts) == 2:
                        lib_name = parts[0].strip()
                        lib_path = parts[1].strip().split()[0]  # Remove address info
                        dependencies.append({
                            "name": lib_name,
                            "path": lib_path if lib_path != "(0x" else "not found"
                        })
                elif line and not line.startswith('/') and not line.startswith('linux-vdso'):
                    # Handle cases like "libname.so (0xaddress)"
                    if '(' in line:
                        lib_name = line.split('(')[0].strip()
                        dependencies.append({
                            "name": lib_name,
                            "path": "virtual"
                        })
            
            return dependencies
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"ldd not available or failed for {file_path}")
            return []
    
    @staticmethod
    def check_binary_properties(file_path: str) -> Dict[str, bool]:
        """
        Check important binary properties for dynamic linking analysis
        
        Args:
            file_path: Path to ELF file
            
        Returns:
            Dictionary of binary properties
        """
        properties = {
            "is_elf": False,
            "is_64bit": False,
            "is_dynamically_linked": False,
            "is_pie": False,
            "has_got": False,
            "has_plt": False,
            "has_debug_info": False,
            "is_stripped": False
        }
        
        if not Path(file_path).exists():
            return properties
        
        try:
            # Basic ELF check
            properties["is_elf"] = BinaryParser.is_elf_file(file_path)
            if not properties["is_elf"]:
                return properties
            
            # Get header info
            header_info = BinaryParser.get_elf_header_info(file_path)
            properties["is_64bit"] = header_info["is_64bit"]
            
            # Use file command to get more info
            result = subprocess.run(
                ['file', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            file_output = result.stdout.lower()
            properties["is_dynamically_linked"] = "dynamically linked" in file_output
            properties["is_pie"] = "pie" in file_output or "position independent" in file_output
            properties["is_stripped"] = "stripped" in file_output
            
            # Check for specific sections using objdump
            try:
                objdump_result = subprocess.run(
                    ['objdump', '-h', file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                objdump_output = objdump_result.stdout
                properties["has_got"] = ".got" in objdump_output
                properties["has_plt"] = ".plt" in objdump_output
                properties["has_debug_info"] = ".debug" in objdump_output
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            return properties
            
        except Exception as e:
            logger.warning(f"Failed to check binary properties: {e}")
            return properties
    
    @staticmethod
    def format_address(address: int, is_64bit: bool = True) -> str:
        """
        Format address for display
        
        Args:
            address: Integer address
            is_64bit: Whether to format as 64-bit address
            
        Returns:
            Formatted address string
        """
        if is_64bit:
            return f"0x{address:016x}"
        else:
            return f"0x{address:08x}"
    
    @staticmethod
    def parse_hex_address(address_str: str) -> int:
        """
        Parse hex address string to integer
        
        Args:
            address_str: Address string (e.g., "0x1234" or "1234")
            
        Returns:
            Integer address
        """
        try:
            if address_str.startswith('0x') or address_str.startswith('0X'):
                return int(address_str, 16)
            else:
                return int(address_str, 16)
        except ValueError:
            return 0
    
    @staticmethod
    def validate_binary_for_analysis(file_path: str) -> Tuple[bool, str]:
        """
        Validate if binary is suitable for GOT/PLT analysis
        
        Args:
            file_path: Path to binary file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not Path(file_path).exists():
            return False, f"File not found: {file_path}"
        
        properties = BinaryParser.check_binary_properties(file_path)
        
        if not properties["is_elf"]:
            return False, "File is not a valid ELF binary"
        
        if not properties["is_dynamically_linked"]:
            return False, "Binary is not dynamically linked (no GOT/PLT to analyze)"
        
        if not properties["has_got"] and not properties["has_plt"]:
            return False, "Binary has no GOT or PLT sections"
        
        return True, "Binary is suitable for GOT/PLT analysis"


class ArchitectureDetector:
    """
    Architecture-specific detection and handling utilities
    """
    
    SUPPORTED_ARCHITECTURES = {
        'x86_64': {
            'name': 'Intel/AMD x86-64',
            'plt_entry_size': 16,
            'got_entry_size': 8,
            'instruction_set': 'x86_64'
        },
        'aarch64': {
            'name': 'ARM 64-bit',
            'plt_entry_size': 16,
            'got_entry_size': 8,
            'instruction_set': 'aarch64'
        },
        'riscv64': {
            'name': 'RISC-V 64-bit',
            'plt_entry_size': 16,
            'got_entry_size': 8,
            'instruction_set': 'riscv64'
        }
    }
    
    @staticmethod
    def detect_architecture(file_path: str) -> str:
        """
        Detect binary architecture
        
        Args:
            file_path: Path to ELF file
            
        Returns:
            Architecture string or 'unknown'
        """
        try:
            result = subprocess.run(
                ['file', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            file_output = result.stdout.lower()
            
            if 'x86-64' in file_output or 'x86_64' in file_output:
                return 'x86_64'
            elif 'aarch64' in file_output or 'arm64' in file_output:
                return 'aarch64'
            elif 'riscv' in file_output:
                return 'riscv64'
            else:
                return 'unknown'
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            return 'unknown'
    
    @staticmethod
    def get_architecture_info(architecture: str) -> Dict[str, Any]:
        """
        Get detailed architecture information
        
        Args:
            architecture: Architecture string
            
        Returns:
            Architecture details or empty dict if unknown
        """
        return ArchitectureDetector.SUPPORTED_ARCHITECTURES.get(architecture, {})
    
    @staticmethod
    def is_architecture_supported(architecture: str) -> bool:
        """
        Check if architecture is supported for analysis
        
        Args:
            architecture: Architecture string
            
        Returns:
            True if architecture is supported
        """
        return architecture in ArchitectureDetector.SUPPORTED_ARCHITECTURES
