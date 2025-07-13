#!/usr/bin/env python3
"""
Problem Isolation Script for Linkers & Loaders Extraction
Tests each step of the pipeline independently to identify the failure point
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append('.')

# Import components to test
from core.pdf_extractor import PDFStructureExtractor
from core.concept_detector import ConceptBoundaryDetector
from processors.gemini_processor import GeminiAtomicProcessor

def test_step_1_pdf_extraction():
    """Test Step 1: PDF Content Extraction"""
    print("=" * 60)
    print("🔍 STEP 1: PDF CONTENT EXTRACTION")
    print("=" * 60)
    
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/LinkersAndLoaders (1).pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return None
    
    try:
        with PDFStructureExtractor(pdf_path) as extractor:
            # Extract content from pages 31-45 (where we know good content exists)
            content_blocks = extractor.extract_structured_content(30, max_pages=15)
            
            print(f"✅ Extracted {len(content_blocks)} content blocks")
            
            # Analyze content types
            content_types = {}
            for block in content_blocks:
                block_type = block["type"]
                content_types[block_type] = content_types.get(block_type, 0) + 1
            
            print(f"📊 Content types: {content_types}")
            
            # Show sample content from each type
            for content_type in content_types:
                sample_blocks = [b for b in content_blocks if b["type"] == content_type][:2]
                print(f"\n🔍 Sample {content_type.upper()} content:")
                for i, block in enumerate(sample_blocks):
                    content_preview = " ".join(block["content"])[:200] + "..."
                    print(f"  {i+1}. Page {block['page']}: {content_preview}")
            
            return content_blocks
            
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return None

def test_step_2_concept_detection(content_blocks):
    """Test Step 2: Concept Boundary Detection"""
    print("\n" + "=" * 60)
    print("🔍 STEP 2: CONCEPT BOUNDARY DETECTION")
    print("=" * 60)
    
    if not content_blocks:
        print("❌ No content blocks to process")
        return None
    
    try:
        detector = ConceptBoundaryDetector()
        concepts = detector.detect_atomic_concepts(content_blocks)
        
        print(f"✅ Detected {len(concepts)} potential concepts")
        
        # Analyze each concept
        for i, concept in enumerate(concepts):
            print(f"\n🔍 CONCEPT {i+1}:")
            print(f"  📄 Blocks: {len(concept['blocks'])}")
            print(f"  📝 Has text: {concept['has_explanation']}")
            print(f"  💻 Has code: {concept['has_code']}")
            print(f"  📖 Pages: {concept['page_range']}")
            
            # Show content preview
            content_preview = concept['raw_content'][:300] + "..."
            print(f"  📋 Content preview: {content_preview}")
        
        return concepts
        
    except Exception as e:
        print(f"❌ Concept detection failed: {e}")
        return None

def test_step_3_raw_content_analysis(concepts):
    """Test Step 3: Raw Content Analysis"""
    print("\n" + "=" * 60)
    print("🔍 STEP 3: RAW CONTENT ANALYSIS")
    print("=" * 60)
    
    if not concepts:
        print("❌ No concepts to analyze")
        return
    
    # Analyze what keywords are present in the raw content
    linking_keywords = [
        'linker', 'loader', 'object', 'symbol', 'relocation', 'segment',
        'library', 'dynamic', 'static', 'elf', 'executable', 'address',
        'binding', 'resolution', 'table', 'entry', 'section', 'header'
    ]
    
    basic_c_keywords = [
        'printf', 'main', 'function', 'call', 'variable', 'declaration',
        'initialization', 'loop', 'if', 'else', 'return'
    ]
    
    for i, concept in enumerate(concepts):
        raw_content = concept['raw_content'].lower()
        
        # Count keyword occurrences
        linking_count = sum(1 for kw in linking_keywords if kw in raw_content)
        basic_c_count = sum(1 for kw in basic_c_keywords if kw in raw_content)
        
        print(f"\n🔍 CONCEPT {i+1} KEYWORD ANALYSIS:")
        print(f"  🔗 Linking/Loading keywords: {linking_count}")
        print(f"  🔤 Basic C keywords: {basic_c_count}")
        
        # Show which linking keywords were found
        found_linking = [kw for kw in linking_keywords if kw in raw_content]
        found_basic = [kw for kw in basic_c_keywords if kw in raw_content]
        
        print(f"  📋 Linking terms found: {found_linking[:5]}")
        print(f"  📋 Basic C terms found: {found_basic[:5]}")
        
        # Verdict
        if linking_count > basic_c_count:
            print(f"  ✅ VERDICT: Advanced linking content")
        elif basic_c_count > linking_count:
            print(f"  ⚠️  VERDICT: Basic C content")
        else:
            print(f"  🤔 VERDICT: Mixed content")

def test_step_4_gemini_processing(concepts):
    """Test Step 4: Gemini AI Processing"""
    print("\n" + "=" * 60)
    print("🔍 STEP 4: GEMINI AI PROCESSING")
    print("=" * 60)
    
    if not concepts:
        print("❌ No concepts to process")
        return
    
    # Load API key
    load_dotenv("config/config.env")
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    try:
        processor = GeminiAtomicProcessor(api_key)
        
        # Test first concept only
        test_concept = concepts[0]
        test_concept["source_title"] = "Linkers and Loaders"
        
        print(f"🧪 Testing Gemini processing on concept 1...")
        print(f"📋 Raw content length: {len(test_concept['raw_content'])} chars")
        print(f"📋 Content preview: {test_concept['raw_content'][:200]}...")
        
        # Process with Gemini
        result = processor.process_concept(test_concept)
        
        if result:
            print(f"✅ Gemini processing successful")
            print(f"📝 Extracted topic: {result.get('topic', 'None')}")
            print(f"📝 Explanation preview: {result.get('explanation', 'None')[:150]}...")
            
            # Analyze the result
            topic_lower = result.get('topic', '').lower()
            explanation_lower = result.get('explanation', '').lower()
            
            linking_terms = ['linker', 'loader', 'object', 'symbol', 'relocation', 'library', 'dynamic', 'segment']
            basic_terms = ['function', 'call', 'variable', 'printf', 'main']
            
            linking_in_result = sum(1 for term in linking_terms if term in topic_lower or term in explanation_lower)
            basic_in_result = sum(1 for term in basic_terms if term in topic_lower or term in explanation_lower)
            
            print(f"🔍 RESULT ANALYSIS:")
            print(f"  🔗 Linking terms in result: {linking_in_result}")
            print(f"  🔤 Basic C terms in result: {basic_in_result}")
            
            if linking_in_result > basic_in_result:
                print(f"  ✅ VERDICT: Gemini correctly identified advanced content")
            else:
                print(f"  ❌ VERDICT: Gemini defaulted to basic C concepts")
                print(f"  🚨 PROBLEM ISOLATED: Gemini AI processing failure")
            
            return result
        else:
            print(f"❌ Gemini processing failed")
            return None
            
    except Exception as e:
        print(f"❌ Gemini processing error: {e}")
        return None

def test_step_5_prompt_analysis():
    """Test Step 5: Analyze the Gemini Prompt"""
    print("\n" + "=" * 60)
    print("🔍 STEP 5: GEMINI PROMPT ANALYSIS")
    print("=" * 60)
    
    try:
        # Load the processor to examine its prompt
        load_dotenv("config/config.env")
        api_key = os.getenv("GEMINI_API_KEY")
        processor = GeminiAtomicProcessor(api_key)
        
        # Create a dummy concept to see the prompt
        dummy_concept = {
            "raw_content": "Sample linker content about object files and symbol resolution",
            "source_title": "Linkers and Loaders"
        }
        
        # Get the prompt (we'll need to examine the _build_atomic_extraction_prompt method)
        prompt = processor._build_atomic_extraction_prompt(dummy_concept["raw_content"])
        
        print("🔍 CURRENT GEMINI PROMPT:")
        print("-" * 40)
        print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
        print("-" * 40)
        
        # Analyze prompt for context awareness
        prompt_lower = prompt.lower()
        
        context_indicators = ['linkers', 'loaders', 'linking', 'loading', 'advanced', 'system']
        book_context = sum(1 for indicator in context_indicators if indicator in prompt_lower)
        
        print(f"\n🔍 PROMPT ANALYSIS:")
        print(f"  📚 Book context indicators: {book_context}")
        print(f"  📝 Prompt length: {len(prompt)} chars")
        
        if book_context == 0:
            print(f"  ❌ PROBLEM: Prompt lacks book context")
            print(f"  🔧 FIX NEEDED: Add Linkers & Loaders context to prompt")
        else:
            print(f"  ✅ Prompt has some book context")
        
    except Exception as e:
        print(f"❌ Prompt analysis failed: {e}")

def main():
    """Run complete problem isolation"""
    print("🔍 LINKERS & LOADERS EXTRACTION PROBLEM ISOLATION")
    print("=" * 80)
    
    # Step 1: Test PDF extraction
    content_blocks = test_step_1_pdf_extraction()
    
    # Step 2: Test concept detection
    concepts = test_step_2_concept_detection(content_blocks)
    
    # Step 3: Analyze raw content
    test_step_3_raw_content_analysis(concepts)
    
    # Step 4: Test Gemini processing
    result = test_step_4_gemini_processing(concepts)
    
    # Step 5: Analyze the prompt
    test_step_5_prompt_analysis()
    
    print("\n" + "=" * 80)
    print("🎯 ISOLATION COMPLETE")
    print("=" * 80)
    print("Check the output above to identify exactly where the pipeline fails.")
    print("The problem will be in one of these steps:")
    print("1. PDF extraction (wrong content)")
    print("2. Concept detection (wrong grouping)")
    print("3. Raw content (wrong classification)")
    print("4. Gemini processing (AI failure)")
    print("5. Prompt engineering (missing context)")

if __name__ == "__main__":
    main()
