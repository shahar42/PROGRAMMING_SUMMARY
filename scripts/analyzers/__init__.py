# analyzers/__init__.py
"""
Binary Analysis Module for GOT/PLT Educational MCP Server

Provides core data structures and analysis capabilities for examining
Global Offset Table (GOT) and Procedure Linkage Table (PLT) in ELF binaries.
"""

from .binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub, SymbolInfo

__all__ = ['BinaryAnalyzer', 'GOTEntry', 'PLTStub', 'SymbolInfo']

# educational/__init__.py
"""
Educational Framework for GOT/PLT Analysis

Provides multi-level educational explanations for dynamic linking concepts.
Transforms technical binary analysis into accessible learning material.
"""


__all__ = ['EducationalExplainer', 'ConceptValidator', 'EnhancedExampleGenerator']

# utils/__init__.py
"""
Utility Modules for GOT/PLT Analysis

Provides low-level binary parsing utilities, error handling, and helper functions
for ELF analysis with educational focus.
"""


__all__ = ['BinaryParser', 'ArchitectureDetector']

# architecture/__init__.py
"""
Architecture-Specific Handlers for GOT/PLT Analysis

Provides architecture-specific implementations for different platforms.
Currently supports x86-64, with AArch64 and RISC-V planned.
"""

# This will be implemented in Phase 4
__all__ = []
