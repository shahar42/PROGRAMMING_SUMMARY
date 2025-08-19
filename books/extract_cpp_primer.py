#!/usr/bin/env python3
"""
C++ Primer Expert Concept Extraction Engine
Based on the working cpp_standard extraction script

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
from processors.concept_memory import ConceptMemoryManager


class CppPrimerChapterMapper:
    """Maps content to C++ Primer chapters"""
    
    CHAPTER_MAPPING = {
        "basics": ["variable", "type", "declaration", "initialization", "scope"],
        "strings": ["string", "vector", "iterator", "container"],
        "expressions": ["operator", "expression", "precedence", "evaluation"],
        "statements": ["if", "for", "while", "switch", "loop"],
        "functions": ["function", "parameter", "argument", "return", "overload"],
        "classes": ["class", "member", "constructor", "destructor", "this"],
        "io": ["iostream", "stream", "input", "output", "file"],
        "sequential": ["vector", "list", "deque", "array", "container"],
        "generic": ["template", "generic", "algorithm", "iterator"],
        "associative": ["map", "set", "unordered", "hash"],
        "dynamic": ["new", "delete", "smart", "pointer", "shared", "unique"],
        "copy": ["copy", "move", "assignment", "constructor"],
        "overloaded": ["operator", "overload", "conversion", "friend"],
        "oop": ["inheritance", "virtual", "abstract", "polymorphism"],
        "templates": ["template", "specialization", "instantiation"],
        "specialized": ["exception", "namespace", "multiple", "inheritance"]
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
        return "basics"


class MultiModelRotator:
    """Round-robin model management"""
    
    def __init__(self, config_file="config/config.env"):
        load_dotenv(config_file)
        
        self.processors = {}
        self.model_order = []
        
        # Initialize Grok
        grok_key = os.getenv("GROK_API_KEY")
        print(f"🔍 DEBUG: Raw GROK_API_KEY length: {len(grok_key) if grok_key else 0}")
        print(f"🔍 DEBUG: GROK_API_KEY first 15: {grok_key[:15] if grok_key else 'None'}")
        print(f"🔍 DEBUG: GROK_API_KEY last 15: {grok_key[-15:] if grok_key else 'None'}")
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
        
        print(f"🔄 Round-robin order: { ' → '.join(self.model_order)}")
    
    def get_processor_for_concept(self, concept_index):
        """Get processor using round-robin"""
        model_index = concept_index % len(self.model_order)
        selected_model = self.model_order[model_index]
        return self.processors[selected_model], selected_model


class CppPrimerExtractionEngine:
    """Main extraction engine for C++ Primer"""
    
    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        progress_file = self.output_dir / "progress.json"
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.model_rotator = MultiModelRotator()
        self.chapter_mapper = CppPrimerChapterMapper()
        
        # Initialize concept memory for deduplication
        self.concept_memory = ConceptMemoryManager()
        print("🧠 Concept memory system initialized for deduplication")
        
        print(f"📚 C++ Primer Expert Extraction Engine Initialized")
        print(f"📖 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
    
    def run_extraction_session(self, max_concepts=17):
        """Run extraction session"""
        session_start = datetime.now()
        print(f"\n🔍 Starting C++ Primer extraction session (max {max_concepts} concepts)...")
        print(f"📚 Focus: Practical C++ programming concepts and best practices")
        print(f"🔄 Round-robin: {len(self.model_rotator.model_order)} models rotating per concept")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []
        model_stats = {model: 0 for model in self.model_rotator.model_order}
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            print(f"📖 Extracting C++ Primer content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=40)
            
            if not content_blocks:
                print("🏁 No more content found.")
                return False
            
            # Detect concepts
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential C++ Primer concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing C++ Primer concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Get processor (round-robin)
                processor, model_name = self.model_rotator.get_processor_for_concept(i)
                print(f"🤖 Using {model_name.upper()} for concept {i + 1}")
                
                # Process concept
                processed_concept = self._process_concept(concept, processor, model_name)
                
                if processed_concept:
                    # CHECK FOR DUPLICATES BEFORE SAVING
                    is_duplicate, similar_concepts, similarity_scores = self.concept_memory.check_for_duplicates(processed_concept)
                    
                    if is_duplicate:
                        print(f"🚨 DUPLICATE DETECTED - Skipping concept: {processed_concept.get('topic', 'Unknown')}")
                        print(f"   Similar to: {similar_concepts[0]['concept_data'].get('topic', 'Unknown')}")
                        continue
                    
                    if similar_concepts:
                        print(f"⚠️  Similar concept found (score: {similarity_scores[0]:.2f})")
                        print(f"   Existing: {similar_concepts[0]['concept_data'].get('topic', 'Unknown')}")
                        print(f"   Proceeding with extraction...")
                    
                    # SAVE THE CONCEPT
                    chapter_prefix = self.chapter_mapper.get_chapter_prefix(concept["raw_content"])
                    filename = self._save_concept(processed_concept, concepts_extracted, chapter_prefix)
                    
                    # ADD TO MEMORY AFTER SAVING
                    file_path = self.output_dir / filename
                    self.concept_memory.add_concept_to_memory(processed_concept, str(file_path), "cpp_primer")
                    
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
                    
                    print(f"✅ Saved C++ Primer concept: {processed_concept.get('topic', 'Unknown')} [{chapter_prefix}]")
                else:
                    print(f"❌ Failed to process concept with {model_name}")
        
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
        
        print(f"\n📊 C++ Primer session complete: {concepts_extracted} concepts extracted")
        print(f"🔄 Model distribution: {model_stats}")
        print(f"📈 Total progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
        
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
                return processor.process_concept(concept, "cpp_primer")
                
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
        """Build expert-level prompt for C++ Primer concepts"""
        return f"""You are an expert C++ educator creating training data for practical C++ programming knowledge from C++ Primer.

Extract ONE practical C++ concept focusing on real-world programming techniques, best practices, and common patterns.

FOCUS ON:
- Practical programming techniques and patterns
- Best practices and idiomatic C++ code
- Common pitfalls and how to avoid them
- Real-world usage scenarios

Return valid JSON:
{{
  "topic": "Practical C++ Programming Concept",
  "explanation": "Clear explanation of the concept with practical context and best practices.",
  "syntax": "C++ syntax with practical usage notes",
  "code_example": [
    "#include <iostream>",
    "// Practical C++ example from C++ Primer"
  ],
  "example_explanation": "Practical analysis focusing on real-world usage and best practices."
}}

Content: {content[:2000]}

Extract practical C++ concept as JSON:"""
    
    def _parse_grok_response(self, response_text):
        """Parse Grok response"""
        try:
            # Use regex to find JSON block, robust against surrounding text
            match = re.search(r'{.*}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GROK extracted concept: {concept['topic']}")
                    return concept
            print("❌ Failed to find a valid JSON object in the Grok response.")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Grok: {e}")
            print(f"   Response Text: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during Grok response parsing: {e}")
            return None

    def _parse_gemini_response(self, response_text):
        """Parse Gemini response"""
        try:
            # Use regex to find JSON block, robust against surrounding text
            match = re.search(r'{.*}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GEMINI extracted concept: {concept['topic']}")
                    return concept
            print("❌ Failed to find a valid JSON object in the Gemini response.")
            print(f"🔍 GEMINI RAW RESPONSE:")
            print(f"{'='*50}")
            print(response_text[:1000])  # Show first 1000 chars
            print(f"{'='*50}")
            print(f"📏 Total length: {len(response_text)} characters")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Gemini: {e}")
            print(f"   Response Text: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during Gemini response parsing: {e}")
            return None
    
    def _save_concept(self, concept, concept_number, chapter_prefix):
        """Save concept with chapter-based naming"""
        concept_id = f"{chapter_prefix}_{concept_number + 1:03d}"
        safe_topic = self._safe_filename(concept.get('topic', 'unknown'))
        filename = f"cpp_primer_{concept_id}_{safe_topic}.json"
        
        # Add metadata
        if "extraction_metadata" not in concept:
            concept["extraction_metadata"] = {}
        
        concept["extraction_metadata"].update({
            "source": "C++ Primer (5th Edition)",
            "chapter": chapter_prefix,
            "extraction_type": "practical_programming",
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
        
        summary_filename = f"cpp_primer_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_path = self.output_dir / summary_filename
        
        summary_content = f"""# C++ Primer Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {session_duration.total_seconds():.1f} seconds
**Extraction Type:** Practical C++ Programming Concepts

## Model Statistics
"""
        
        for model, count in model_stats.items():
            summary_content += f"- **{model.upper()}**: {count} concepts\n"
        
        summary_content += f"\n## Extracted Concepts: {len(extracted_concepts)}\n\n"
        
        for concept in extracted_concepts:
            summary_content += f"### {concept['topic']}\n"
            summary_content += f"**Chapter:** {concept['chapter']} | **Processor:** {concept['processor'].upper()}\n"
            summary_content += f"**File:** `{concept['filename']}`\n\n"
        
        summary_content += "\n---\n*C++ Primer Practical Programming Analysis Complete*"
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 Summary saved: {summary_filename}")


def main():
    """Main execution"""
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/CPPPrimer.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/cpp_primer"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found")
        return
    
    # Run extraction
    engine = CppPrimerExtractionEngine(pdf_path, output_dir)
    
    # Run extraction session
    engine.run_extraction_session(max_concepts=17)


if __name__ == "__main__":
    main()