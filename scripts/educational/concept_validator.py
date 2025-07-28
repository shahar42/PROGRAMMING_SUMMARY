#!/usr/bin/env python3
"""
Concept Validator for GOT/PLT Educational MCP Server

Validates theoretical concepts from the Linkers & Loaders book against real binary behavior.
Bridges the gap between theory and practice with educational explanations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from analyzers.binary_analyzer import BinaryAnalyzer, GOTEntry, PLTStub, SymbolInfo

logger = logging.getLogger("concept-validator")


@dataclass
class ConceptValidationResult:
    """Results of validating a theoretical concept against binary reality"""
    concept_name: str
    theory_description: str
    validation_status: str  # "CONFIRMED", "PARTIAL", "CONTRADICTED", "UNTESTABLE"
    evidence: List[str]
    discrepancies: List[str]
    educational_notes: List[str]
    confidence_score: float  # 0.0 to 1.0
    test_binaries_used: List[str]


class ConceptValidator:
    """
    Validates extracted linker concepts against real binary behavior
    
    This class loads theoretical concepts from your existing knowledge base
    and tests them against actual ELF binaries to provide educational
    validation of theory vs practice.
    """
    
    def __init__(self, concepts_dir: Optional[str] = None):
        """
        Initialize concept validator
        
        Args:
            concepts_dir: Path to linkers_loaders concepts directory
        """
        if concepts_dir is None:
            # Use your existing project structure
            project_root = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
            self.concepts_dir = project_root / "outputs" / "linkers_loaders"
        else:
            self.concepts_dir = Path(concepts_dir)
        
        self.concepts_db = self._load_linker_concepts()
        self.test_binaries = self._prepare_test_binaries()
        
        logger.info(f"Loaded {len(self.concepts_db)} linker concepts for validation")
    
    def _load_linker_concepts(self) -> Dict[str, Any]:
        """Load concepts from your existing linkers_loaders directory"""
        concepts = {}
        
        if not self.concepts_dir.exists():
            logger.warning(f"Concepts directory not found: {self.concepts_dir}")
            return concepts
        
        # Load all concept JSON files
        for concept_file in self.concepts_dir.glob("*concept_*.json"):
            try:
                with open(concept_file, 'r', encoding='utf-8') as f:
                    concept_data = json.load(f)
                
                # Extract concept name from filename or topic
                concept_name = concept_data.get('topic', concept_file.stem)
                concepts[concept_name] = {
                    'filename': concept_file.name,
                    'topic': concept_data.get('topic', ''),
                    'explanation': concept_data.get('explanation', ''),
                    'syntax': concept_data.get('syntax', ''),
                    'code_example': concept_data.get('code_example', []),
                    'example_explanation': concept_data.get('example_explanation', ''),
                    'extraction_metadata': concept_data.get('extraction_metadata', {}),
                    'raw_data': concept_data
                }
                
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load concept from {concept_file}: {e}")
                continue
        
        logger.info(f"Loaded {len(concepts)} concepts from {self.concepts_dir}")
        return concepts
    
    def _prepare_test_binaries(self) -> Dict[str, str]:
        """Prepare test binaries for concept validation"""
        # These would be simple test binaries that demonstrate various linking concepts
        # For now, we'll use common system binaries and user-provided binaries
        test_binaries = {
            "simple_dynamic": "/bin/ls",  # Common dynamically linked binary
            "with_libs": "/usr/bin/gcc",  # Binary with many library dependencies
            "system_binary": "/bin/cat",  # Simple system binary
        }
        
        # Filter to only existing binaries
        existing_binaries = {}
        for name, path in test_binaries.items():
            if Path(path).exists():
                existing_binaries[name] = path
        
        return existing_binaries
    
    def list_available_concepts(self) -> List[str]:
        """List all available concepts for validation"""
        return list(self.concepts_db.keys())
    
    def get_concept_info(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific concept"""
        return self.concepts_db.get(concept_name)
    
    def validate_concept(self, concept_name: str, binary_path: str = None) -> ConceptValidationResult:
        """
        Validate a theoretical concept against actual binary behavior
        
        Args:
            concept_name: Name of concept to validate
            binary_path: Optional specific binary to test against
            
        Returns:
            Detailed validation results
        """
        # Get concept information
        concept_info = self.get_concept_info(concept_name)
        if not concept_info:
            return ConceptValidationResult(
                concept_name=concept_name,
                theory_description=f"Concept '{concept_name}' not found in knowledge base",
                validation_status="UNTESTABLE",
                evidence=[],
                discrepancies=[f"Concept '{concept_name}' not found"],
                educational_notes=["Available concepts: " + ", ".join(self.list_available_concepts()[:10])],
                confidence_score=0.0,
                test_binaries_used=[]
            )
        
        # Determine test binaries
        test_binaries = []
        if binary_path and Path(binary_path).exists():
            test_binaries = [binary_path]
        else:
            # Use default test binaries
            test_binaries = list(self.test_binaries.values())[:2]  # Limit to 2 for performance
        
        # Perform validation
        return self._validate_concept_against_binaries(concept_info, test_binaries)
    
    def _validate_concept_against_binaries(self, concept_info: Dict[str, Any], test_binaries: List[str]) -> ConceptValidationResult:
        """Validate concept against specific binaries"""
        concept_name = concept_info['topic']
        theory_description = concept_info['explanation']
        
        evidence = []
        discrepancies = []
        educational_notes = []
        successful_tests = 0
        total_tests = 0
        
        for binary_path in test_binaries:
            try:
                # Analyze binary
                analyzer = BinaryAnalyzer(binary_path)
                got_entries = analyzer.analyze_got_table()
                plt_stubs = analyzer.analyze_plt_stubs()
                symbols = analyzer.list_dynamic_symbols()
                binary_info = analyzer.get_binary_info()
                
                # Perform concept-specific validation
                validation_result = self._validate_specific_concept(
                    concept_info, analyzer, got_entries, plt_stubs, symbols, binary_info
                )
                
                evidence.extend(validation_result['evidence'])
                discrepancies.extend(validation_result['discrepancies'])
                educational_notes.extend(validation_result['educational_notes'])
                
                if validation_result['success']:
                    successful_tests += 1
                total_tests += 1
                
            except Exception as e:
                logger.warning(f"Failed to analyze {binary_path}: {e}")
                discrepancies.append(f"Could not analyze {binary_path}: {str(e)}")
                total_tests += 1
        
        # Determine overall validation status
        if total_tests == 0:
            validation_status = "UNTESTABLE"
            confidence_score = 0.0
        elif successful_tests == total_tests:
            validation_status = "CONFIRMED"
            confidence_score = 1.0
        elif successful_tests > 0:
            validation_status = "PARTIAL"
            confidence_score = successful_tests / total_tests
        else:
            validation_status = "CONTRADICTED"
            confidence_score = 0.0
        
        return ConceptValidationResult(
            concept_name=concept_name,
            theory_description=theory_description,
            validation_status=validation_status,
            evidence=evidence,
            discrepancies=discrepancies,
            educational_notes=educational_notes,
            confidence_score=confidence_score,
            test_binaries_used=test_binaries
        )
    
    def _validate_specific_concept(self, concept_info: Dict[str, Any], analyzer: BinaryAnalyzer, 
                                 got_entries: List[GOTEntry], plt_stubs: List[PLTStub], 
                                 symbols: List[SymbolInfo], binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specific concept against binary analysis results"""
        concept_name = concept_info['topic'].lower()
        explanation = concept_info['explanation'].lower()
        
        evidence = []
        discrepancies = []
        educational_notes = []
        success = False
        
        # Concept-specific validation logic
        if any(keyword in concept_name for keyword in ['got', 'global offset table']):
            return self._validate_got_concept(concept_info, got_entries, binary_info)
        
        elif any(keyword in concept_name for keyword in ['plt', 'procedure linkage table']):
            return self._validate_plt_concept(concept_info, plt_stubs, binary_info)
        
        elif any(keyword in concept_name for keyword in ['lazy binding', 'dynamic linking']):
            return self._validate_lazy_binding_concept(concept_info, got_entries, plt_stubs, binary_info)
        
        elif any(keyword in concept_name for keyword in ['symbol resolution', 'symbol table']):
            return self._validate_symbol_concept(concept_info, symbols, binary_info)
        
        elif any(keyword in concept_name for keyword in ['relocation', 'reloc']):
            return self._validate_relocation_concept(concept_info, got_entries, binary_info)
        
        elif any(keyword in concept_name for keyword in ['shared library', 'dynamic library']):
            return self._validate_shared_library_concept(concept_info, symbols, binary_info)
        
        else:
            # Generic validation
            return self._validate_generic_concept(concept_info, analyzer, binary_info)
    
    def _validate_got_concept(self, concept_info: Dict[str, Any], got_entries: List[GOTEntry], 
                            binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GOT-related concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        # Check if binary has GOT
        has_got = binary_info.get('linking_info', {}).get('has_got', False)
        
        if has_got and got_entries:
            evidence.append(f"✅ GOT section found with {len(got_entries)} entries")
            
            # Check for specific GOT characteristics mentioned in theory
            theory = concept_info['explanation'].lower()
            
            if 'position independent' in theory or 'pic' in theory:
                is_pie = binary_info.get('linking_info', {}).get('is_pie', False)
                if is_pie:
                    evidence.append("✅ Binary is position-independent, confirming GOT's role in PIC")
                else:
                    educational_notes.append("📝 Binary is not PIE, but GOT still used for dynamic linking")
            
            if 'lazy binding' in theory:
                lazy_entries = [e for e in got_entries if getattr(e, 'binding_type', '') == 'LAZY']
                if lazy_entries:
                    evidence.append(f"✅ Found {len(lazy_entries)} lazy binding GOT entries")
                else:
                    educational_notes.append("📝 No explicit lazy binding entries found (may use immediate binding)")
            
            success = True
        else:
            discrepancies.append("❌ No GOT entries found - binary may be statically linked")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_plt_concept(self, concept_info: Dict[str, Any], plt_stubs: List[PLTStub], 
                            binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PLT-related concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        has_plt = binary_info.get('linking_info', {}).get('has_plt', False)
        
        if has_plt and plt_stubs:
            evidence.append(f"✅ PLT section found with {len(plt_stubs)} stubs")
            
            # Check architecture-specific PLT characteristics
            arch = binary_info.get('architecture', 'unknown')
            theory = concept_info['explanation'].lower()
            
            if arch == 'x86_64' and 'x86' in theory:
                evidence.append("✅ x86-64 PLT stubs found, matching theoretical description")
            
            # Check for trampoline behavior mentioned in theory
            if 'trampoline' in theory or 'jump' in theory:
                stubs_with_jumps = [s for s in plt_stubs if any('jmp' in instr for instr in getattr(s, 'disassembly', []))]
                if stubs_with_jumps:
                    evidence.append(f"✅ Found {len(stubs_with_jumps)} PLT stubs with jump instructions (trampolines)")
            
            success = True
        else:
            discrepancies.append("❌ No PLT stubs found - binary may not use dynamic function calls")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_lazy_binding_concept(self, concept_info: Dict[str, Any], got_entries: List[GOTEntry], 
                                     plt_stubs: List[PLTStub], binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate lazy binding concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        theory = concept_info['explanation'].lower()
        
        # Check for lazy binding indicators
        if got_entries and plt_stubs:
            evidence.append("✅ Both GOT and PLT present - infrastructure for lazy binding exists")
            
            # Check for resolver-related content in theory vs practice
            if 'resolver' in theory or '_dl_runtime_resolve' in theory:
                educational_notes.append("📝 Theory mentions runtime resolver - this would be visible during execution, not static analysis")
            
            if 'first call' in theory and 'slow' in theory:
                educational_notes.append("📝 Theory describes first-call overhead - this is a runtime behavior")
            
            if 'subsequent calls' in theory and 'fast' in theory:
                educational_notes.append("📝 Theory describes subsequent call optimization - observable during execution")
            
            success = True
        else:
            discrepancies.append("❌ Missing GOT or PLT - lazy binding infrastructure not present")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_symbol_concept(self, concept_info: Dict[str, Any], symbols: List[SymbolInfo], 
                               binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate symbol resolution concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        if symbols:
            imports = [s for s in symbols if getattr(s, 'is_import', False)]
            exports = [s for s in symbols if getattr(s, 'is_export', False)]
            
            evidence.append(f"✅ Found {len(symbols)} dynamic symbols ({len(imports)} imports, {len(exports)} exports)")
            
            theory = concept_info['explanation'].lower()
            
            if 'binding' in theory:
                global_symbols = [s for s in symbols if s.binding == 'STB_GLOBAL']
                if global_symbols:
                    evidence.append(f"✅ Found {len(global_symbols)} globally bound symbols")
            
            if 'weak' in theory:
                weak_symbols = [s for s in symbols if s.binding == 'STB_WEAK']
                if weak_symbols:
                    evidence.append(f"✅ Found {len(weak_symbols)} weakly bound symbols")
                else:
                    educational_notes.append("📝 No weak symbols found in this binary")
            
            success = True
        else:
            discrepancies.append("❌ No dynamic symbols found - binary may be statically linked")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_relocation_concept(self, concept_info: Dict[str, Any], got_entries: List[GOTEntry], 
                                   binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate relocation concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        if got_entries:
            # Check relocation types
            reloc_types = [getattr(e, 'relocation_type', 'unknown') for e in got_entries]
            unique_types = set(reloc_types)
            
            evidence.append(f"✅ Found relocations with types: {', '.join(unique_types)}")
            
            theory = concept_info['explanation'].lower()
            arch = binary_info.get('architecture', 'unknown')
            
            if arch == 'x86_64' and 'x86' in theory:
                x86_relocs = [t for t in reloc_types if 'X86_64' in t]
                if x86_relocs:
                    evidence.append(f"✅ Found x86-64 specific relocations: {len(x86_relocs)} entries")
            
            if 'jump_slot' in theory.replace(' ', '_').lower():
                jump_slot_relocs = [t for t in reloc_types if 'JUMP_SLOT' in t]
                if jump_slot_relocs:
                    evidence.append(f"✅ Found JUMP_SLOT relocations: {len(jump_slot_relocs)} entries")
            
            success = True
        else:
            discrepancies.append("❌ No relocation entries found")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_shared_library_concept(self, concept_info: Dict[str, Any], symbols: List[SymbolInfo], 
                                       binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate shared library concepts"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        is_dynamic = binary_info.get('linking_info', {}).get('is_dynamically_linked', False)
        
        if is_dynamic:
            evidence.append("✅ Binary is dynamically linked - uses shared libraries")
            
            imports = [s for s in symbols if getattr(s, 'is_import', False)]
            if imports:
                evidence.append(f"✅ Found {len(imports)} imported symbols from shared libraries")
                
                # Try to identify common library functions
                common_libc = ['printf', 'malloc', 'free', 'strcpy', 'strlen']
                libc_symbols = [s for s in imports if s.name in common_libc]
                if libc_symbols:
                    evidence.append(f"✅ Found common libc functions: {[s.name for s in libc_symbols]}")
            
            success = True
        else:
            discrepancies.append("❌ Binary is not dynamically linked - does not use shared libraries")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def _validate_generic_concept(self, concept_info: Dict[str, Any], analyzer: BinaryAnalyzer, 
                                binary_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generic validation for concepts that don't fit specific categories"""
        evidence = []
        discrepancies = []
        educational_notes = []
        
        # Basic dynamic linking check
        is_dynamic = binary_info.get('linking_info', {}).get('is_dynamically_linked', False)
        
        if is_dynamic:
            evidence.append("✅ Binary uses dynamic linking - concept may be applicable")
            educational_notes.append(f"📝 Concept '{concept_info['topic']}' requires manual validation")
            educational_notes.append("📝 Theoretical description: " + concept_info['explanation'][:100] + "...")
            success = True
        else:
            discrepancies.append("❌ Binary is statically linked - dynamic linking concepts not applicable")
            success = False
        
        return {
            'evidence': evidence,
            'discrepancies': discrepancies,
            'educational_notes': educational_notes,
            'success': success
        }
    
    def generate_validation_report(self, concept_name: str, binary_path: str = None) -> str:
        """
        Generate comprehensive validation report for a concept
        
        Args:
            concept_name: Name of concept to validate
            binary_path: Optional specific binary to test
            
        Returns:
            Formatted validation report
        """
        result = self.validate_concept(concept_name, binary_path)
        
        # Format the report
        report = f"""
🔬 **Concept Validation Report: {result.concept_name}**

📚 **Theoretical Description:**
{result.theory_description[:200]}{'...' if len(result.theory_description) > 200 else ''}

🎯 **Validation Status:** {result.validation_status}
📊 **Confidence Score:** {result.confidence_score:.1%}

"""
        
        if result.evidence:
            report += "✅ **Supporting Evidence:**\n"
            for evidence in result.evidence:
                report += f"   {evidence}\n"
            report += "\n"
        
        if result.discrepancies:
            report += "❌ **Discrepancies Found:**\n"
            for discrepancy in result.discrepancies:
                report += f"   {discrepancy}\n"
            report += "\n"
        
        if result.educational_notes:
            report += "📝 **Educational Notes:**\n"
            for note in result.educational_notes:
                report += f"   {note}\n"
            report += "\n"
        
        if result.test_binaries_used:
            report += f"🔍 **Test Binaries:** {', '.join(result.test_binaries_used)}\n\n"
        
        # Add interpretation
        if result.validation_status == "CONFIRMED":
            report += "🎉 **Conclusion:** The theoretical concept is well-supported by binary evidence!\n"
        elif result.validation_status == "PARTIAL":
            report += "⚖️ **Conclusion:** The concept is partially confirmed. Some aspects may be runtime-dependent or context-specific.\n"
        elif result.validation_status == "CONTRADICTED":
            report += "🤔 **Conclusion:** The binary evidence contradicts the theoretical description. This may indicate edge cases or updated implementations.\n"
        else:
            report += "❓ **Conclusion:** Unable to test this concept with static analysis. Runtime or specialized tools may be needed.\n"
        
        return report
    
    def find_related_concepts(self, search_term: str) -> List[str]:
        """Find concepts related to a search term"""
        search_lower = search_term.lower()
        related = []
        
        for concept_name, concept_info in self.concepts_db.items():
            if (search_lower in concept_name.lower() or 
                search_lower in concept_info['explanation'].lower() or
                search_lower in concept_info.get('syntax', '').lower()):
                related.append(concept_name)
        
        return related[:10]  # Limit results
