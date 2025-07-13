#!/usr/bin/env python3
"""
Integration Validation Script for Expert C Programming + GPT-4.1 Nano
Verifies all components integrate seamlessly
"""

import sys
import os
from pathlib import Path

def validate_integration():
    print("🔍 VALIDATING EXPERT C PROGRAMMING + GPT-4.1 NANO INTEGRATION")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: Processor import
    try:
        from processors.gpt4_nano_processor import GPT4NanoAtomicProcessor
        print("✅ GPT-4.1 Nano processor imports successfully")
        checks_passed += 1
    except Exception as e:
        print(f"❌ GPT-4.1 Nano processor import failed: {e}")
    
    # Check 2: Book extractor import
    try:
        from books.extract_expert_c_programming import ExpertCExtractionEngine
        print("✅ Expert C Programming extractor imports successfully")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Expert C Programming extractor import failed: {e}")
    
    # Check 3: Configuration file exists
    if Path("config/books_config.json").exists():
        print("✅ Books configuration file exists")
        checks_passed += 1
    else:
        print("❌ Books configuration file missing")
    
    # Check 4: Output directory structure
    if Path("outputs/expert_c_programming").exists():
        print("✅ Output directory structure created")
        checks_passed += 1
    else:
        print("❌ Output directory structure missing")
    
    # Check 5: Environment template
    if Path("config/config.env").exists() or Path("config/config_template.env").exists():
        print("✅ Environment configuration template available")
        checks_passed += 1
    else:
        print("❌ Environment configuration template missing")
    
    # Check 6: Core dependencies
    try:
        from core.progress_tracker import ProgressTracker
        from core.pdf_extractor import PDFStructureExtractor
        from core.concept_detector import ConceptBoundaryDetector
        print("✅ Core dependencies available")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Core dependencies missing: {e}")
    
    print("\n" + "=" * 60)
    print(f"INTEGRATION VALIDATION: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 INTEGRATION COMPLETE - Expert C Programming ready for production!")
        return True
    else:
        print("⚠️  INTEGRATION INCOMPLETE - Please address failing checks")
        return False

if __name__ == "__main__":
    success = validate_integration()
    sys.exit(0 if success else 1)
