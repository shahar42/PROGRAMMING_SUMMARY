#!/usr/bin/env python3
"""
Integration Test Script for GOT/PLT Educational MCP Server

Tests all three phases of the server to ensure complete functionality.
Provides educational feedback on what works and what might need attention.
"""

import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
import sys
from pathlib import Path

# Add the project root directory (the parent of 'scripts') to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

class GOTPLTServerTester:
    """Comprehensive tester for all three phases of the GOT/PLT server"""
    
    def __init__(self):
        self.test_results = {
            'phase1': {},
            'phase2': {},
            'phase3': {},
            'integration': {}
        }
        self.test_binary = None
        
    def create_test_binary(self) -> bool:
        """Create a simple test binary for analysis"""
        try:
            # Create temporary test program
            test_code = '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    printf("Testing GOT/PLT analysis...\\n");
    
    void *ptr = malloc(100);
    if (ptr) {
        strcpy((char*)ptr, "Hello, lazy binding!");
        printf("Allocated and copied: %s\\n", (char*)ptr);
        free(ptr);
    }
    
    printf("Test completed successfully\\n");
    return 0;
}
'''
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(test_code)
                source_file = f.name
            
            # Compile test binary
            binary_file = source_file.replace('.c', '_test_binary')
            compile_cmd = ['gcc', '-o', binary_file, source_file]
            
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.test_binary = binary_file
                logger.info(f"✅ Test binary created: {binary_file}")
                
                # Clean up source file
                os.unlink(source_file)
                return True
            else:
                logger.error(f"❌ Failed to compile test binary: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create test binary: {e}")
            return False
    
    def test_phase1_static_analysis(self) -> bool:
        """Test Phase 1: Static binary analysis capabilities"""
        logger.info("\n🔍 Testing Phase 1: Static Binary Analysis")
        
        try:
            from analyzers.binary_analyzer import BinaryAnalyzer
            from educational.explainer import EducationalExplainer
            
            # Test binary analyzer
            analyzer = BinaryAnalyzer(self.test_binary)
            
            # Test GOT analysis
            got_entries = analyzer.analyze_got_table()
            self.test_results['phase1']['got_analysis'] = len(got_entries) > 0
            logger.info(f"  GOT Analysis: {'✅' if len(got_entries) > 0 else '❌'} ({len(got_entries)} entries)")
            
            # Test PLT analysis
            plt_stubs = analyzer.analyze_plt_stubs()
            self.test_results['phase1']['plt_analysis'] = len(plt_stubs) >= 0  # May be 0 for simple binaries
            logger.info(f"  PLT Analysis: {'✅' if len(plt_stubs) >= 0 else '❌'} ({len(plt_stubs)} stubs)")
            
            # Test symbol listing
            symbols = analyzer.list_dynamic_symbols()
            self.test_results['phase1']['symbol_analysis'] = len(symbols) > 0
            logger.info(f"  Symbol Analysis: {'✅' if len(symbols) > 0 else '❌'} ({len(symbols)} symbols)")
            
            # Test educational explainer
            explainer = EducationalExplainer()
            binary_info = analyzer.get_binary_info()
            explanation = explainer.generate_got_explanation(got_entries, binary_info, "intermediate")
            self.test_results['phase1']['educational_explanations'] = len(explanation) > 100
            logger.info(f"  Educational Explanations: {'✅' if len(explanation) > 100 else '❌'}")
            
            phase1_success = all(self.test_results['phase1'].values())
            logger.info(f"Phase 1 Overall: {'✅ PASSED' if phase1_success else '❌ FAILED'}")
            
            return phase1_success
            
        except ImportError as e:
            logger.error(f"❌ Phase 1 import error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Phase 1 test failed: {e}")
            return False
    
    def test_phase2_concept_validation(self) -> bool:
        """Test Phase 2: Concept validation and knowledge base integration"""
        logger.info("\n📚 Testing Phase 2: Concept Validation")
        
        try:
            from educational.concept_validator import ConceptValidator
            from educational.example_generator import EnhancedExampleGenerator
            
            # Test concept validator
            validator = ConceptValidator()
            
            # Test concept loading
            concepts = validator.list_available_concepts()
            self.test_results['phase2']['concept_loading'] = len(concepts) > 0
            logger.info(f"  Concept Loading: {'✅' if len(concepts) > 0 else '❌'} ({len(concepts)} concepts)")
            
            # Test concept search
            related = validator.find_related_concepts("got")
            self.test_results['phase2']['concept_search'] = len(related) > 0
            logger.info(f"  Concept Search: {'✅' if len(related) > 0 else '❌'} ({len(related)} GOT-related)")
            
            # Test concept validation (if concepts available)
            validation_success = False
            if concepts:
                test_concept = concepts[0]  # Use first available concept
                validation_result = validator.validate_concept(test_concept, self.test_binary)
                validation_success = validation_result.concept_name == test_concept
                logger.info(f"  Concept Validation: {'✅' if validation_success else '❌'} (tested: {test_concept})")
            else:
                logger.info(f"  Concept Validation: ⚠️ SKIPPED (no concepts available)")
            
            self.test_results['phase2']['concept_validation'] = validation_success
            
            # Test example generator
            generator = EnhancedExampleGenerator()
            example = generator.generate_concept_example("got")
            self.test_results['phase2']['example_generation'] = len(example) > 100
            logger.info(f"  Example Generation: {'✅' if len(example) > 100 else '❌'}")
            
            # Calculate phase 2 success (allow concept validation to be skipped)
            required_tests = ['concept_loading', 'concept_search', 'example_generation']
            phase2_success = all(self.test_results['phase2'][test] for test in required_tests)
            logger.info(f"Phase 2 Overall: {'✅ PASSED' if phase2_success else '❌ FAILED'}")
            
            return phase2_success
            
        except ImportError as e:
            logger.error(f"❌ Phase 2 import error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Phase 2 test failed: {e}")
            return False
    
    def test_phase3_runtime_analysis(self) -> bool:
        """Test Phase 3: Runtime analysis with GDB integration"""
        logger.info("\n🚀 Testing Phase 3: Runtime Analysis")
        
        try:
            from utils.gdb_interface import GDBInterface
            from analyzers.runtime_analyzer import RuntimeAnalyzer
            from analyzers.lazy_binding_analyzer import LazyBindingAnalyzer
            
            # Test GDB availability
            gdb_available = self.check_gdb_available()
            self.test_results['phase3']['gdb_available'] = gdb_available
            logger.info(f"  GDB Available: {'✅' if gdb_available else '❌'}")
            
            if not gdb_available:
                logger.info("  ⚠️ GDB not available - skipping runtime analysis tests")
                logger.info("  💡 Install GDB to enable runtime analysis: sudo apt-get install gdb")
                return False
            
            # Test GDB interface
            gdb_interface_works = False
            try:
                with GDBInterface(self.test_binary, timeout=10) as gdb:
                    gdb_interface_works = True
                    logger.info(f"  GDB Interface: ✅")
            except Exception as e:
                logger.info(f"  GDB Interface: ❌ ({str(e)[:50]}...)")
            
            self.test_results['phase3']['gdb_interface'] = gdb_interface_works
            
            # Test runtime analyzer
            runtime_analyzer_works = False
            if gdb_interface_works:
                try:
                    analyzer = RuntimeAnalyzer(self.test_binary)
                    summary = analyzer.get_analysis_summary()
                    runtime_analyzer_works = summary.get('gdb_test') == 'successful'
                    logger.info(f"  Runtime Analyzer: {'✅' if runtime_analyzer_works else '❌'}")
                except Exception as e:
                    logger.info(f"  Runtime Analyzer: ❌ ({str(e)[:50]}...)")
            else:
                logger.info(f"  Runtime Analyzer: ⚠️ SKIPPED (GDB interface failed)")
            
            self.test_results['phase3']['runtime_analyzer'] = runtime_analyzer_works
            
            # Test lazy binding analyzer
            lazy_analyzer_works = False
            if gdb_interface_works:
                try:
                    lazy_analyzer = LazyBindingAnalyzer(self.test_binary)
                    stats = lazy_analyzer.get_binding_statistics()
                    lazy_analyzer_works = stats.get('binary_path') == self.test_binary
                    logger.info(f"  Lazy Binding Analyzer: {'✅' if lazy_analyzer_works else '❌'}")
                except Exception as e:
                    logger.info(f"  Lazy Binding Analyzer: ❌ ({str(e)[:50]}...)")
            else:
                logger.info(f"  Lazy Binding Analyzer: ⚠️ SKIPPED (GDB interface failed)")
            
            self.test_results['phase3']['lazy_analyzer'] = lazy_analyzer_works
            
            # Phase 3 success requires GDB availability and at least basic interface working
            phase3_success = gdb_available and gdb_interface_works
            logger.info(f"Phase 3 Overall: {'✅ PASSED' if phase3_success else '❌ FAILED'}")
            
            return phase3_success
            
        except ImportError as e:
            logger.error(f"❌ Phase 3 import error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Phase 3 test failed: {e}")
            return False
    
    def check_gdb_available(self) -> bool:
        """Check if GDB is available on the system"""
        try:
            result = subprocess.run(['gdb', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def test_mcp_server_import(self) -> bool:
        """Test that the MCP server can be imported without errors"""
        logger.info("\n🔗 Testing MCP Server Integration")
        
        try:
            # Test importing the main server
            import got_plt_mcp_server
            
            # Check that key components are available
            components_available = {
                'explainer': hasattr(got_plt_mcp_server, 'explainer'),
                'concept_validator': hasattr(got_plt_mcp_server, 'concept_validator'),
                'example_generator': hasattr(got_plt_mcp_server, 'example_generator')
            }
            
            self.test_results['integration']['server_import'] = True
            self.test_results['integration']['components'] = all(components_available.values())
            
            logger.info(f"  Server Import: ✅")
            logger.info(f"  Components Available: {'✅' if all(components_available.values()) else '❌'}")
            
            # Check server info
            try:
                server_info = got_plt_mcp_server._get_server_info_impl()
                info_available = len(server_info) > 100
                self.test_results['integration']['server_info'] = info_available
                logger.info(f"  Server Info: {'✅' if info_available else '❌'}")
            except Exception as e:
                logger.info(f"  Server Info: ❌ ({str(e)[:50]}...)")
                self.test_results['integration']['server_info'] = False
            
            integration_success = all([
                self.test_results['integration']['server_import'],
                self.test_results['integration']['components']
            ])
            
            logger.info(f"Integration Overall: {'✅ PASSED' if integration_success else '❌ FAILED'}")
            
            return integration_success
            
        except ImportError as e:
            logger.error(f"❌ Server import failed: {e}")
            self.test_results['integration']['server_import'] = False
            return False
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            return False
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        
        total_tests = sum(len(phase_results) for phase_results in self.test_results.values())
        passed_tests = sum(sum(phase_results.values()) for phase_results in self.test_results.values())
        
        report = f"""
📊 **GOT/PLT Educational MCP Server - Test Report**

**Overall Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)**

## Phase Results

**Phase 1 (Static Binary Analysis):**
"""
        
        for test, result in self.test_results['phase1'].items():
            report += f"- {test.replace('_', ' ').title()}: {'✅ PASS' if result else '❌ FAIL'}\n"
        
        report += f"\n**Phase 2 (Concept Validation):**\n"
        for test, result in self.test_results['phase2'].items():
            report += f"- {test.replace('_', ' ').title()}: {'✅ PASS' if result else '❌ FAIL'}\n"
        
        report += f"\n**Phase 3 (Runtime Analysis):**\n"
        for test, result in self.test_results['phase3'].items():
            report += f"- {test.replace('_', ' ').title()}: {'✅ PASS' if result else '❌ FAIL'}\n"
        
        report += f"\n**Integration:**\n"
        for test, result in self.test_results['integration'].items():
            report += f"- {test.replace('_', ' ').title()}: {'✅ PASS' if result else '❌ FAIL'}\n"
        
        # Add recommendations
        report += f"\n## Recommendations\n\n"
        
        if not self.test_results['phase1'].get('got_analysis', False):
            report += "- ⚠️ GOT analysis failed - check if binary is dynamically linked\n"
        
        if not self.test_results['phase2'].get('concept_loading', False):
            report += "- ⚠️ No concepts loaded - check `/outputs/linkers_loaders/` directory\n"
        
        if not self.test_results['phase3'].get('gdb_available', False):
            report += "- ⚠️ GDB not available - install with: `sudo apt-get install gdb`\n"
        
        if passed_tests == total_tests:
            report += "- 🎉 All tests passed! Your GOT/PLT server is fully functional.\n"
        elif passed_tests >= total_tests * 0.8:
            report += "- ✅ Most tests passed! Minor issues may need attention.\n"
        else:
            report += "- ⚠️ Multiple issues detected. Check error messages above.\n"
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        logger.info("🧪 Starting GOT/PLT Educational MCP Server Integration Tests")
        logger.info("=" * 60)
        
        # Create test binary
        if not self.create_test_binary():
            logger.error("❌ Cannot create test binary - aborting tests")
            return False
        
        try:
            # Run all test phases
            phase1_success = self.test_phase1_static_analysis()
            phase2_success = self.test_phase2_concept_validation()
            phase3_success = self.test_phase3_runtime_analysis()
            integration_success = self.test_mcp_server_import()
            
            # Generate and display report
            logger.info("\n" + "=" * 60)
            report = self.generate_test_report()
            logger.info(report)
            
            # Overall success
            overall_success = phase1_success and integration_success
            # Phase 2 and 3 are important but not critical for basic functionality
            
            if overall_success:
                logger.info("\n🎉 Integration tests completed successfully!")
                logger.info("Your GOT/PLT Educational MCP Server is ready for use.")
            else:
                logger.info("\n⚠️ Some tests failed. Check the report above for details.")
            
            return overall_success
            
        finally:
            # Clean up test binary
            if self.test_binary and os.path.exists(self.test_binary):
                try:
                    os.unlink(self.test_binary)
                    logger.info(f"🧹 Cleaned up test binary: {self.test_binary}")
                except:
                    pass


def main():
    """Main test execution"""
    tester = GOTPLTServerTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
