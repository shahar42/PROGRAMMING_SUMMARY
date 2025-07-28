#!/usr/bin/env python3
"""
Error Handler for GOT/PLT Educational MCP Server

Provides comprehensive error handling with educational context.
Transforms technical errors into learning opportunities.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger("got-plt-error-handler")


class GOTPLTError(Exception):
    """Base exception for GOT/PLT analysis errors"""
    
    def __init__(self, message: str, educational_context: Optional[str] = None):
        super().__init__(message)
        self.educational_context = educational_context


class BinaryAnalysisError(GOTPLTError):
    """Errors related to binary analysis"""
    pass


class ArchitectureNotSupportedError(GOTPLTError):
    """Errors for unsupported architectures"""
    pass


class EducationalErrorHandler:
    """
    Provides educational error handling that turns technical errors
    into learning opportunities
    """
    
    def __init__(self):
        self.error_explanations = self._load_error_explanations()
    
    def _load_error_explanations(self) -> Dict[str, str]:
        """Load educational explanations for common errors"""
        return {
            "file_not_found": """
🚫 **File Not Found Error**

**What happened:** The binary file you specified doesn't exist at the given path.

**Common causes:**
- Typo in the file path
- File was moved or deleted
- Incorrect working directory

**How to fix:**
1. Check the file path: `ls -la /path/to/your/binary`
2. Verify you're in the right directory: `pwd`
3. Use absolute paths to avoid confusion

**Learning opportunity:** File path resolution is important in systems programming!
""",
            "not_elf_binary": """
🚫 **Not an ELF Binary Error**

**What happened:** The file exists but it's not a valid ELF (Executable and Linkable Format) binary.

**Common causes:**
- Trying to analyze a text file, script, or other non-binary file
- File is corrupted
- File is a different binary format (PE, Mach-O, etc.)

**How to check:**
```bash
file your_binary_name
readelf -h your_binary_name
```

**Learning opportunity:** ELF is the standard binary format on Linux. Other systems use different formats!
""",
            "not_dynamically_linked": """
🚫 **Not Dynamically Linked Error**

**What happened:** The binary is statically linked, so it doesn't have GOT/PLT sections to analyze.

**What this means:**
- All library code is compiled directly into the binary
- No external dependencies at runtime
- No dynamic symbol resolution needed

**How to check:**
```bash
ldd your_binary_name
# Static binaries will show "not a dynamic executable"
```

**Learning opportunity:** Static vs dynamic linking is a fundamental concept in systems programming!
""",
            "missing_dependencies": """
🚫 **Missing Dependencies Error**

**What happened:** The analysis tools (like `objdump`, `readelf`) are not installed on your system.

**How to fix:**
```bash
# On Ubuntu/Debian:
sudo apt-get install binutils

# On CentOS/RHEL:
sudo yum install binutils

# On macOS:
brew install binutils
```

**Learning opportunity:** Binary analysis requires specialized tools that understand file formats!
""",
            "architecture_not_supported": """
🚫 **Architecture Not Supported Error**

**What happened:** The binary's architecture is not yet supported by this educational tool.

**Currently supported:**
- x86-64 (Intel/AMD 64-bit) - Full support
- AArch64 (ARM 64-bit) - Partial support
- RISC-V 64-bit - Planned

**Learning opportunity:** Different CPU architectures have different calling conventions, instruction sets, and PLT implementations!
""",
            "capstone_missing": """
🚫 **Disassembler Not Available Error**

**What happened:** The Capstone disassembly engine is not installed, so PLT stub disassembly is not available.

**How to fix:**
```bash
pip install capstone
```

**Workaround:** You can still analyze GOT entries and symbol information without disassembly.

**Learning opportunity:** Disassemblers translate machine code back to human-readable assembly language!
""",
            "pyelftools_missing": """
🚫 **ELF Parser Not Available Error**

**What happened:** The pyelftools library is not installed, which is required for ELF binary parsing.

**How to fix:**
```bash
pip install pyelftools
```

**Learning opportunity:** Parsing binary file formats requires specialized libraries that understand the format specifications!
"""
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle error with educational context
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            Educational error message
        """
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Determine error category and provide educational response
        if "no such file or directory" in error_message or "file not found" in error_message:
            return self._format_error_response("file_not_found", error, context)
        
        elif "not a valid elf binary" in error_message or "bad magic number" in error_message:
            return self._format_error_response("not_elf_binary", error, context)
        
        elif "not dynamically linked" in error_message or "no got section" in error_message:
            return self._format_error_response("not_dynamically_linked", error, context)
        
        elif "objdump" in error_message or "readelf" in error_message:
            return self._format_error_response("missing_dependencies", error, context)
        
        elif "architecture" in error_message and "not supported" in error_message:
            return self._format_error_response("architecture_not_supported", error, context)
        
        elif "capstone" in error_message:
            return self._format_error_response("capstone_missing", error, context)
        
        elif "pyelftools" in error_message or "elftools" in error_message:
            return self._format_error_response("pyelftools_missing", error, context)
        
        else:
            # Generic error handling
            return self._format_generic_error(error, context)
    
    def _format_error_response(self, error_key: str, error: Exception, context: Optional[Dict[str, Any]]) -> str:
        """Format educational error response"""
        explanation = self.error_explanations.get(error_key, "")
        
        result = f"❌ **Analysis Error**\n\n"
        result += explanation + "\n"
        
        if context:
            result += f"\n🔍 **Context:**\n"
            for key, value in context.items():
                result += f"- {key}: {value}\n"
        
        result += f"\n🔧 **Technical Details:**\n"
        result += f"Error Type: {type(error).__name__}\n"
        result += f"Error Message: {str(error)}\n"
        
        return result
    
    def _format_generic_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> str:
        """Format generic error with educational guidance"""
        result = f"❌ **Unexpected Analysis Error**\n\n"
        
        result += f"🔧 **Technical Details:**\n"
        result += f"Error Type: {type(error).__name__}\n"
        result += f"Error Message: {str(error)}\n\n"
        
        if context:
            result += f"🔍 **Context:**\n"
            for key, value in context.items():
                result += f"- {key}: {value}\n"
            result += "\n"
        
        result += f"📚 **Troubleshooting Steps:**\n"
        result += f"1. Verify the binary file exists and is readable\n"
        result += f"2. Check that it's a valid ELF binary: `file your_binary`\n"
        result += f"3. Ensure it's dynamically linked: `ldd your_binary`\n"
        result += f"4. Try with a simple test binary first\n"
        result += f"5. Check the server logs for more detailed error information\n\n"
        
        result += f"🐛 **Debug Information:**\n"
        result += f"```\n{traceback.format_exc()}```\n"
        
        return result
    
    def validate_prerequisites(self) -> Dict[str, bool]:
        """
        Validate that all prerequisites are available
        
        Returns:
            Dictionary of prerequisite availability
        """
        checks = {
            "pyelftools": False,
            "capstone": False,
            "objdump": False,
            "readelf": False,
            "ldd": False,
            "file": False
        }
        
        # Check Python libraries
        try:
            import elftools
            checks["pyelftools"] = True
        except ImportError:
            pass
        
        try:
            import capstone
            checks["capstone"] = True
        except ImportError:
            pass
        
        # Check system tools
        import subprocess
        for tool in ["objdump", "readelf", "ldd", "file"]:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                checks[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return checks
    
    def generate_setup_report(self) -> str:
        """Generate setup validation report"""
        checks = self.validate_prerequisites()
        
        result = "🔧 **GOT/PLT Analysis Setup Report**\n\n"
        
        result += "📋 **Prerequisites Status:**\n"
        for requirement, available in checks.items():
            status = "✅" if available else "❌"
            result += f"{status} {requirement}: {'Available' if available else 'Missing'}\n"
        
        result += "\n"
        
        # Provide installation instructions for missing items
        missing = [req for req, avail in checks.items() if not avail]
        if missing:
            result += "🚀 **Installation Instructions:**\n\n"
            
            if "pyelftools" in missing:
                result += "**Python Libraries:**\n"
                result += "```bash\npip install pyelftools capstone\n```\n\n"
            
            if any(tool in missing for tool in ["objdump", "readelf", "ldd", "file"]):
                result += "**System Tools:**\n"
                result += "```bash\n"
                result += "# Ubuntu/Debian:\nsudo apt-get install binutils file\n\n"
                result += "# CentOS/RHEL:\nsudo yum install binutils file\n\n"
                result += "# macOS:\nbrew install binutils file\n"
                result += "```\n"
        else:
            result += "🎉 **All prerequisites are available!**\n"
            result += "Your system is ready for GOT/PLT analysis.\n"
        
        return result


# Global error handler instance
error_handler = EducationalErrorHandler()


def handle_analysis_error(func):
    """Decorator for handling analysis errors with educational context"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Analysis error in {func.__name__}: {e}")
            return error_handler.handle_error(e, {
                "function": func.__name__,
                "args": str(args)[:100],  # Truncate for safety
                "kwargs": str(kwargs)[:100]
            })
    return wrapper
