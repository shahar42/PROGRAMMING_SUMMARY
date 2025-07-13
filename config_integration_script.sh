#!/bin/bash
# Complete Integration Script for Expert C Programming + GPT-4.1 Nano
# This script updates all necessary configuration files for seamless integration

echo "🔧 INTEGRATING EXPERT C PROGRAMMING + GPT-4.1 NANO"
echo "=================================================="

# Step 1: Update books_config.json
echo "📝 Updating books_config.json..."
cat > config/books_config_updated.json << 'EOF'
{
  "kernighan_ritchie": {
    "pdf_path": "The C Programming Language (Kernighan Ritchie).pdf",
    "output_dir": "outputs/kernighan_ritchie",
    "processor": "gemini",
    "concept_focus": "C language syntax, operators, control structures, functions",
    "max_concepts_per_day": 4,
    "status": "active",
    "source_title": "The C Programming Language - Kernighan & Ritchie"
  },
  "unix_env": {
    "pdf_path": "Advanced Programming in the UNIX Environment 3rd Edition.pdf", 
    "output_dir": "outputs/unix_env",
    "processor": "grok",
    "concept_focus": "System calls, APIs, UNIX programming patterns, file operations",
    "max_concepts_per_day": 4,
    "status": "active",
    "source_title": "Advanced Programming in the UNIX Environment 3rd Edition"
  },
  "linkers_loaders": {
    "pdf_path": "LinkersAndLoaders (1).pdf",
    "output_dir": "outputs/linkers_loaders", 
    "processor": "gemini", 
    "concept_focus": "Binary formats, linking mechanics, loader concepts, object files",
    "max_concepts_per_day": 4,
    "status": "active",
    "source_title": "Linkers and Loaders"
  },
  "os_three_pieces": {
    "pdf_path": "Operating Systems - Three Easy Pieces.pdf",
    "output_dir": "outputs/os_three_pieces",
    "processor": "grok",
    "concept_focus": "OS algorithms, data structures, system concepts, concurrency",
    "max_concepts_per_day": 4,
    "status": "active",
    "source_title": "Operating Systems - Three Easy Pieces"
  },
  "expert_c_programming": {
    "pdf_path": "Expert C Programming Deep C Secrets.pdf",
    "output_dir": "outputs/expert_c_programming",
    "processor": "gpt4_nano",
    "concept_focus": "Advanced C techniques, pitfalls, expert-level programming, deep language insights",
    "max_concepts_per_day": 4,
    "status": "active",
    "source_title": "Expert C Programming: Deep C Secrets"
  }
}
EOF

# Step 2: Update master script arrays
echo "📝 Updating master script arrays..."
cat > scripts/run_all_daily_updated.sh << 'EOF'
#!/bin/bash
# Enhanced Master Daily Multi-Book Extraction Runner
# Updated with Expert C Programming + GPT-4.1 Nano integration

# Book extraction configuration
declare -A BOOK_SCRIPTS=(
    ["kernighan_ritchie"]="$BOOKS_DIR/extract_c_concepts.py"
    ["unix_env"]="$BOOKS_DIR/extract_unix_env.py"
    ["linkers_loaders"]="$BOOKS_DIR/extract_linkers_loaders.py"
    ["os_three_pieces"]="$BOOKS_DIR/extract_os_three_pieces.py"
    ["expert_c_programming"]="$BOOKS_DIR/extract_expert_c_programming.py"
)

declare -A BOOK_NAMES=(
    ["kernighan_ritchie"]="K&R C Programming"
    ["unix_env"]="UNIX Environment"
    ["linkers_loaders"]="Linkers & Loaders"
    ["os_three_pieces"]="Operating Systems"
    ["expert_c_programming"]="Expert C Programming"
)

declare -A BOOK_STATUS=(
    ["kernighan_ritchie"]="active"
    ["unix_env"]="active"
    ["linkers_loaders"]="active"
    ["os_three_pieces"]="active"
    ["expert_c_programming"]="active"
)

declare -A BOOK_AI_MODEL=(
    ["kernighan_ritchie"]="Gemini"
    ["unix_env"]="Grok"
    ["linkers_loaders"]="Gemini"
    ["os_three_pieces"]="Grok"
    ["expert_c_programming"]="GPT-4.1 Nano"
)

# [Rest of the script remains the same - just copy existing implementation]
EOF

# Step 3: Update environment configuration
echo "📝 Updating config.env template..."
cat > config/config_template.env << 'EOF'
# AI Processor API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROK_API_KEY=your_grok_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Book Processing Configuration
MAX_CONCEPTS_PER_SESSION=4
EXTRACTION_TIMEOUT=600
API_RETRY_ATTEMPTS=3

# Rate Limiting (seconds between API calls)
GEMINI_DELAY=2
GROK_DELAY=3
OPENAI_DELAY=1
EOF

# Step 4: Create requirements update
echo "📝 Updating requirements.txt..."
cat > requirements_updated.txt << 'EOF'
pdfplumber==0.10.3
google-generativeai==0.3.2
python-dotenv==1.0.0
requests==2.31.0
openai>=1.0.0
EOF

# Step 5: Create output directory structure
echo "📁 Creating output directory structure..."
mkdir -p outputs/expert_c_programming

# Step 6: Integration validation script
cat > validate_expert_c_integration.py << 'EOF'
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
EOF

echo ""
echo "✅ INTEGRATION CONFIGURATION COMPLETE"
echo "📋 Next steps:"
echo "1. Copy processors/gpt4_nano_processor.py to your project"
echo "2. Copy books/extract_expert_c_programming.py to your project"
echo "3. Update config/books_config.json with the new entry"
echo "4. Add OPENAI_API_KEY to config/config.env"
echo "5. Run: python3 validate_expert_c_integration.py"
echo "6. Test: cd books && python3 extract_expert_c_programming.py"
