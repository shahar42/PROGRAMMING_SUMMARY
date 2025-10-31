#!/usr/bin/env python3
"""
Inside the C++ Object Model - Advanced Implementation Extraction Engine
Specialized for deep C++ implementation internals and compiler behavior

Features:
- Focus on advanced constructor/destructor mechanics
- Virtual table and inheritance implementation details
- Memory layout and optimization analysis
- Expert-level compiler behavior insights
- Round-robin model rotation: Grok → GPT → Gemini → repeat
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


class CppObjectModelChapterMapper:
    """Maps content to C++ Object Model implementation topics"""

    CHAPTER_MAPPING = {
        "constructor": ["constructor", "initialization", "synthesis", "default constructor", "copy constructor"],
        "destructor": ["destructor", "destruction", "cleanup", "RAII", "object lifetime"],
        "inheritance": ["inheritance", "virtual", "base class", "derived", "multiple inheritance"],
        "function": ["virtual function", "vtable", "vptr", "dispatch", "polymorphism"],
        "object": ["object model", "memory layout", "object size", "alignment", "padding"],
        "template": ["template", "instantiation", "specialization", "generic programming"],
        "runtime": ["RTTI", "dynamic_cast", "typeid", "runtime type information"],
        "data": ["data member", "member function", "static", "access control"]
    }

    def get_chapter_prefix(self, content):
        """Get chapter prefix from content focusing on implementation aspects"""
        content_lower = content.lower()

        chapter_scores = {}
        for chapter, keywords in self.CHAPTER_MAPPING.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                chapter_scores[chapter] = score

        if chapter_scores:
            return max(chapter_scores, key=chapter_scores.get)
        return "object"


class MultiModelRotator:
    """Round-robin model management for C++ Object Model extraction"""

    def __init__(self, config_file="config/config.env"):
        load_dotenv(config_file)

        self.processors = {}
        self.model_order = []

        # Initialize Grok
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            self.processors["grok"] = GrokAtomicProcessor(grok_key)
            self.model_order.append("grok")
            print("✅ Grok processor initialized for C++ Object Model")

        # Initialize GPT
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.processors["gpt"] = GPT4NanoAtomicProcessor(openai_key)
            self.model_order.append("gpt")
            print("✅ GPT processor initialized for C++ Object Model")

        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.processors["gemini"] = GeminiAtomicProcessor(gemini_key)
            self.model_order.append("gemini")
            print("✅ Gemini processor initialized for C++ Object Model")

        if not self.processors:
            raise ValueError("No API keys found!")

        print(f"🔄 C++ Object Model round-robin: {' → '.join(self.model_order)}")

    def get_processor_for_concept(self, concept_index):
        """Get processor using round-robin"""
        model_index = concept_index % len(self.model_order)
        selected_model = self.model_order[model_index]
        return self.processors[selected_model], selected_model


class CppObjectModelExtractionEngine:
    """Main extraction engine for Inside the C++ Object Model"""

    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        progress_file = self.output_dir / "progress.json"
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.model_rotator = MultiModelRotator()
        self.chapter_mapper = CppObjectModelChapterMapper()

        # Initialize concept memory for deduplication
        self.concept_memory = ConceptMemoryManager()
        print("🧠 C++ Object Model concept memory initialized")

        print(f"🏛️  Inside the C++ Object Model Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")

    def run_extraction_session(self, max_concepts=8):
        """Run C++ Object Model extraction session"""
        session_start = datetime.now()
        print(f"\n🔍 Starting C++ Object Model extraction session (max {max_concepts} concepts)...")
        print(f"🧠 Focus: Implementation internals, compiler behavior, memory layout, virtual mechanisms")
        print(f"🔄 Round-robin: {len(self.model_rotator.model_order)} models rotating per concept")

        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []
        model_stats = {model: 0 for model in self.model_rotator.model_order}

        with PDFStructureExtractor(self.pdf_path) as extractor:
            print(f"📖 Extracting C++ Object Model content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=50)

            if not content_blocks:
                print("🏁 No more content found.")
                return False

            # Detect concepts with focus on implementation details
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)

            print(f"🧠 Detected {len(concepts)} potential C++ Object Model implementation concepts")

            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing C++ Object Model concept {i+1}/{min(len(concepts), max_concepts)}...")

                # Get processor (round-robin)
                processor, model_name = self.model_rotator.get_processor_for_concept(i)
                print(f"🤖 Using {model_name.upper()} for implementation concept {i + 1}")

                # Process concept
                processed_concept = self._process_concept(concept, processor, model_name)

                if processed_concept:
                    # Check for duplicates
                    is_duplicate, similar_concepts, similarity_scores = self.concept_memory.check_for_duplicates(processed_concept)

                    if is_duplicate:
                        print(f"🚨 DUPLICATE DETECTED - Skipping: {processed_concept.get('topic', 'Unknown')}")
                        continue

                    if similar_concepts:
                        print(f"⚠️  Similar concept found (score: {similarity_scores[0]:.2f})")
                        print(f"   Proceeding with extraction...")

                    # Save the concept
                    chapter_prefix = self.chapter_mapper.get_chapter_prefix(concept["raw_content"])
                    filename = self._save_concept(processed_concept, concepts_extracted, chapter_prefix)

                    # Add to memory after saving
                    file_path = self.output_dir / filename
                    self.concept_memory.add_concept_to_memory(processed_concept, str(file_path), "Inside_the_C++_Object_Model")

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

                    print(f"✅ Saved C++ Object Model concept: {processed_concept.get('topic', 'Unknown')} [{chapter_prefix}]")
                else:
                    print(f"❌ Failed to process C++ Object Model concept with {model_name}")

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

        print(f"\n📊 C++ Object Model session complete: {concepts_extracted} implementation concepts extracted")
        print(f"🔄 Model distribution: {model_stats}")
        print(f"📈 Total C++ Object Model progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")

        return concepts_extracted > 0

    def _process_concept(self, concept, processor, model_name):
        """Process concept with selected model using specialized C++ Object Model prompts"""
        try:
            if model_name == "grok":
                prompt = self._build_cpp_object_model_prompt(concept["raw_content"])
                response = processor._call_grok_api(prompt)
                return self._parse_grok_response(response)

            elif model_name == "gpt":
                # Use GPT's existing process_concept method but with custom prompt context
                return processor.process_concept(concept, "Inside_the_C++_Object_Model")

            elif model_name == "gemini":
                prompt = self._build_cpp_object_model_prompt(concept["raw_content"])
                response = processor.model.generate_content(prompt).text
                return self._parse_gemini_response(response)

            else:
                print(f"❌ Unknown processor: {model_name}")
                return None

        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")
            return None

    def _build_cpp_object_model_prompt(self, content):
        """Build specialized prompt for C++ Object Model implementation concepts"""
        return f"""You are an expert C++ compiler implementer and systems programmer creating training data for advanced C++ implementation knowledge from "Inside the C++ Object Model" by Stanley B. Lippman.

Extract ONE advanced C++ implementation concept focusing on:

PRIORITY TOPICS:
- Constructor/Destructor implementation mechanics and compiler synthesis
- Virtual function table layout, vptr placement, and dispatch mechanisms
- Multiple inheritance implementation, pointer adjustment, and vtable organization
- Virtual inheritance memory layout and virtual base class mechanisms
- Object memory layout, alignment, padding, and size optimization
- Template instantiation models and code generation strategies
- RTTI implementation details and runtime type checking
- Exception handling implementation and stack unwinding
- Compiler optimization strategies for C++ constructs

FOCUS ON IMPLEMENTATION DETAILS:
- How the compiler actually implements these features
- Memory layout diagrams and pointer manipulation
- Assembly-level behavior and performance implications
- Runtime vs compile-time behavior distinctions
- Specific compiler strategies and optimizations
- Cross-platform implementation differences

Return valid JSON:
{{
  "topic": "Advanced C++ Implementation Concept (Implementation-focused title)",
  "explanation": "Deep technical explanation covering compiler implementation, memory layout, runtime behavior, and performance characteristics. Include specific implementation details.",
  "syntax": "C++ syntax with detailed implementation notes",
  "code_example": [
    "#include <iostream>",
    "// Advanced C++ Object Model example showing implementation details"
  ],
  "example_explanation": "Detailed analysis of compiler behavior, memory layout, and implementation mechanics."
}}

Content: {content[:2500]}

Extract advanced C++ Object Model implementation concept as JSON:"""

    def _parse_grok_response(self, response_text):
        """Parse Grok response for C++ Object Model concepts"""
        try:
            match = re.search(r'{.*}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GROK extracted C++ Object Model concept: {concept['topic']}")
                    return concept
            print("❌ Failed to find valid JSON in Grok response")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Grok: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error parsing Grok response: {e}")
            return None

    def _parse_gemini_response(self, response_text):
        """Parse Gemini response for C++ Object Model concepts"""
        try:
            match = re.search(r'{.*}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GEMINI extracted C++ Object Model concept: {concept['topic']}")
                    return concept
            print("❌ Failed to find valid JSON in Gemini response")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Gemini: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error parsing Gemini response: {e}")
            return None

    def _save_concept(self, concept, concept_number, chapter_prefix):
        """Save concept with C++ Object Model specific naming"""
        concept_id = f"{chapter_prefix}_{concept_number + 1:03d}"
        safe_topic = self._safe_filename(concept.get('topic', 'unknown'))
        filename = f"objmdl_{concept_id}_{safe_topic}.json"

        # Add C++ Object Model specific metadata
        if "extraction_metadata" not in concept:
            concept["extraction_metadata"] = {}

        concept["extraction_metadata"].update({
            "source": "Inside the C++ Object Model by Stanley B. Lippman",
            "chapter": chapter_prefix,
            "extraction_type": "advanced_implementation",
            "focus": "compiler_internals_and_memory_layout",
            "extraction_date": datetime.now().isoformat()
        })

        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)

        return filename

    def _safe_filename(self, topic):
        """Create safe filename from topic"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:35]

    def _generate_summary(self, session_start, extracted_concepts, model_stats):
        """Generate C++ Object Model extraction summary"""
        session_duration = datetime.now() - session_start

        summary_filename = f"cpp_object_model_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_path = self.output_dir / summary_filename

        summary_content = f"""# Inside the C++ Object Model - Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {session_duration.total_seconds():.1f} seconds
**Extraction Type:** Advanced C++ Implementation Analysis
**Focus:** Compiler internals, memory layout, virtual mechanisms

## Model Statistics
"""

        for model, count in model_stats.items():
            summary_content += f"- **{model.upper()}**: {count} implementation concepts\n"

        summary_content += f"\n## Extracted Implementation Concepts: {len(extracted_concepts)}\n\n"

        for concept in extracted_concepts:
            summary_content += f"### {concept['topic']}\n"
            summary_content += f"**Chapter:** {concept['chapter']} | **Processor:** {concept['processor'].upper()}\n"
            summary_content += f"**File:** `{concept['filename']}`\n\n"

        summary_content += "\n---\n*Advanced C++ Object Model Implementation Analysis Complete*"

        with open(summary_path, 'w') as f:
            f.write(summary_content)

        print(f"📋 C++ Object Model summary saved: {summary_filename}")


def main():
    """Main execution for C++ Object Model extraction"""
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/Inside_the_C++_Object_Model.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/Inside_the_C++_Object_Model"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found")
        return

    # Run C++ Object Model extraction
    engine = CppObjectModelExtractionEngine(pdf_path, output_dir)

    # Run extraction session targeting ~0.5 concepts per page (goal: ~150 concepts from 304 pages)
    engine.run_extraction_session(max_concepts=15)


if __name__ == "__main__":
    main()