#!/usr/bin/env python3
"""
C++ Standard Expert Concept Extraction Engine
Working version - rewritten from scratch to restore functionality

Features:
- Expert-level "under the hood" concept extraction
- Round-robin model rotation: Grok → GPT → Gemini → repeat
- Chapter-based concept naming
- Clean error handling
- Progress tracking
"""

import sys
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Add project root to Python path
sys.path.append('.')

# Import components
from core.progress_tracker import ProgressTracker
from core.pdf_extractor import PDFStructureExtractor
from core.concept_detector import ConceptBoundaryDetector
from processors.grok_processor import GrokAtomicProcessor
from processors.gpt4_nano_processor import GPT4NanoAtomicProcessor
from processors.gemini_processor import GeminiAtomicProcessor


class CppChapterMapper:
    """Maps content to C++ chapters"""
    
    CHAPTER_MAPPING = {
        "basic": ["declaration", "definition", "scope", "types", "lvalue", "rvalue"],
        "classes": ["class", "member", "constructor", "destructor", "virtual"],
        "templates": ["template", "generic", "specialization", "metaprogramming"],
        "exceptions": ["try", "catch", "throw", "exception", "RAII"],
        "special": ["copy", "move", "assignment", "destructor"],
        "overloading": ["operator", "overload", "function overload"],
        "statements": ["if", "for", "while", "switch"],
        "expressions": ["operator", "assignment", "conditional"],
        "declarators": ["pointer", "reference", "array"],
        "library": ["std", "algorithm", "container", "iterator"]
    }
    
    def get_chapter_prefix(self, content):
        """Get chapter prefix from content"""
        content_lower = content.lower()
        
        chapter_scores = {}
        for chapter, keywords in self.CHAPTER_MAPPING.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                chapter_scores[chapter] = score
        
        if chapter_scores:
            return max(chapter_scores, key=chapter_scores.get)
        return "basic"


class MultiModelRotator:
    """Round-robin model management"""
    
    def __init__(self, config_file="config/config.env"):
        load_dotenv(config_file)
        
        self.processors = {}
        self.model_order = []
        
        # Initialize Grok
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            self.processors["grok"] = GrokAtomicProcessor(grok_key)
            self.model_order.append("grok")
            print("✅ Grok processor initialized")
        
        # Initialize GPT
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.processors["gpt"] = GPT4NanoAtomicProcessor(openai_key)
            self.model_order.append("gpt")
            print("✅ GPT processor initialized")
        
        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.processors["gemini"] = GeminiAtomicProcessor(gemini_key)
            self.model_order.append("gemini")
            print("✅ Gemini processor initialized")
        
        if not self.processors:
            raise ValueError("No API keys found!")
        
        print(f"🔄 Round-robin order: {' → '.join(self.model_order)}")
    
    def get_processor_for_concept(self, concept_index):
        """Get processor using round-robin"""
        model_index = concept_index % len(self.model_order)
        selected_model = self.model_order[model_index]
        return self.processors[selected_model], selected_model


class CppExpertExtractionEngine:
    """Main extraction engine"""
    
    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        progress_file = self.output_dir / "progress.json"
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.model_rotator = MultiModelRotator()
        self.chapter_mapper = CppChapterMapper()
        
        print(f"🏛️  C++ Expert Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
    
    def run_extraction_session(self, max_concepts=6):
        """Run extraction session"""
        session_start = datetime.now()
        print(f"\n🔍 Starting C++ Expert extraction session (max {max_concepts} concepts)...")
        print(f"🧠 Focus: Implementation details, compiler behavior, and under-the-hood mechanics")
        print(f"🔄 Round-robin: {len(self.model_rotator.model_order)} models rotating per concept")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []
        model_stats = {model: 0 for model in self.model_rotator.model_order}
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            print(f"📖 Extracting C++ content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=40)
            
            if not content_blocks:
                print("🏁 No more content found.")
                return False
            
            # Detect concepts
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential C++ atomic concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing expert C++ concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Get processor (round-robin)
                processor, model_name = self.model_rotator.get_processor_for_concept(concepts_extracted)
                print(f"🤖 Using {model_name.upper()} for expert concept {concepts_extracted + 1}")
                
                # Process concept
                processed_concept = self._process_concept(concept, processor, model_name)
                
                if processed_concept:
                    # Determine chapter prefix
                    chapter_prefix = self.chapter_mapper.get_chapter_prefix(concept["raw_content"])
                    
                    # Save concept
                    filename = self._save_concept(processed_concept, concepts_extracted, chapter_prefix)
                    concepts_extracted += 1
                    model_stats[model_name] += 1
                    
                    # Track for summary
                    extracted_concepts.append({
                        "topic": processed_concept.get('topic', 'Unknown'),
                        "explanation": processed_concept.get('explanation', 'No explanation'),
                        "filename": filename,
                        "chapter": chapter_prefix,
                        "processor": model_name
                    })
                    
                    print(f"✅ Saved expert C++ concept: {processed_concept.get('topic', 'Unknown')} [{chapter_prefix}]")
                else:
                    print(f"❌ Failed to process expert C++ concept with {model_name}")
        
        # Update progress
        if concepts:
            last_page = max(block["page"] for concept in concepts for block in concept["blocks"])
            self.progress_tracker.progress["last_processed_page"] = last_page
            self.progress_tracker.progress["total_concepts_extracted"] = (
                self.progress_tracker.progress.get("total_concepts_extracted", 0) + concepts_extracted
            )
            self.progress_tracker.save_progress()
        
        # Generate summary
        self._generate_summary(session_start, extracted_concepts, model_stats)
        
        print(f"\n📊 Expert C++ session complete: {concepts_extracted} atomic concepts extracted")
        print(f"🔄 Model distribution: {model_stats}")
        print(f"📈 Total C++ progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
        
        return concepts_extracted > 0
    
    def _process_concept(self, concept, processor, model_name):
        """Process concept with selected model"""
        try:
            if model_name == "grok":
                # Build expert prompt for Grok
                prompt = self._build_expert_prompt(concept["raw_content"])
                response = processor._call_grok_api(prompt)
                return self._parse_grok_response(response)
                
            elif model_name == "gpt":
                # Use GPT's existing process_concept method
                return processor.process_concept(concept, "cpp_standard")
                
            elif model_name == "gemini":
                # Build expert prompt for Gemini
                prompt = self._build_expert_prompt(concept["raw_content"])
                response = processor.model.generate_content(prompt).text
                return self._parse_gemini_response(response)
                
            else:
                print(f"❌ Unknown processor: {model_name}")
                return None
                
        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")
            return None
    
    def _build_expert_prompt(self, content):
        """Build expert-level prompt"""
        return f"""You are an expert C++ architect creating training data for advanced C++ implementation knowledge.

Extract ONE expert-level C++ concept focusing on implementation details, compiler behavior, and under-the-hood mechanics.

FOCUS ON:
- How the compiler implements this feature
- Memory layout and performance implications
- Assembly-level behavior when relevant
- Runtime vs compile-time behavior

Return valid JSON:
{{
  "topic": "Expert C++ Implementation Concept",
  "explanation": "Deep technical explanation covering implementation details, compiler behavior, and performance characteristics.",
  "syntax": "C++ syntax with implementation notes",
  "code_example": [
    "#include <iostream>",
    "// Expert-level C++ example"
  ],
  "example_explanation": "Expert analysis of compiler behavior and implementation details."
}}

Content: {content[:2000]}

Extract expert C++ concept as JSON:"""
    
    def _parse_grok_response(self, response_text):
        """Parse Grok response"""
        try:
            # Simple JSON extraction
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GROK extracted expert concept: {concept['topic']}")
                    return concept
            return None
        except:
            return None
    
    def _parse_gemini_response(self, response_text):
        """Parse Gemini response"""
        try:
            # Simple JSON extraction
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GEMINI extracted expert concept: {concept['topic']}")
                    return concept
            return None
        except:
            return None
    
    def _save_concept(self, concept, concept_number, chapter_prefix):
        """Save concept with chapter-based naming"""
        concept_id = f"{chapter_prefix}_{concept_number + 1:03d}"
        safe_topic = self._safe_filename(concept.get('topic', 'unknown'))
        filename = f"cpp_{concept_id}_{safe_topic}.json"
        
        # Add metadata
        if "extraction_metadata" not in concept:
            concept["extraction_metadata"] = {}
        
        concept["extraction_metadata"].update({
            "source": "ISO/IEC 14882:2014 C++ Standard",
            "chapter": chapter_prefix,
            "extraction_type": "expert_level",
            "extraction_date": datetime.now().isoformat()
        })
        
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)
        
        return filename
    
    def _safe_filename(self, topic):
        """Create safe filename"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:25]
    
    def _generate_summary(self, session_start, extracted_concepts, model_stats):
        """Generate session summary"""
        session_duration = datetime.now() - session_start
        
        summary_filename = f"cpp_expert_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_path = self.output_dir / summary_filename
        
        summary_content = f"""# C++ Expert Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {session_duration.total_seconds():.1f} seconds
**Extraction Type:** Expert-Level Implementation Analysis

## Model Statistics
"""
        
        for model, count in model_stats.items():
            summary_content += f"- **{model.upper()}**: {count} expert concepts\n"
        
        summary_content += f"\n## Extracted Concepts: {len(extracted_concepts)}\n\n"
        
        for concept in extracted_concepts:
            summary_content += f"### {concept['topic']}\n"
            summary_content += f"**Chapter:** {concept['chapter']} | **Processor:** {concept['processor'].upper()}\n"
            summary_content += f"**File:** `{concept['filename']}`\n\n"
        
        summary_content += "\n---\n*Expert C++ Implementation Analysis Complete*"
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 Expert summary saved: {summary_filename}")


def main():
    """Main execution"""
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/cpp_standard_2014.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/cpp_standard"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found")
        return
    
    # Run extraction
    engine = CppExpertExtractionEngine(pdf_path, output_dir)
    engine.run_extraction_session(max_concepts=6)


if __name__ == "__main__":
    main()
