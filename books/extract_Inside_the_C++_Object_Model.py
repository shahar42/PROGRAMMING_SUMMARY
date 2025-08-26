#!/usr/bin/env python3
"""
Inside the C++ Object Model Concept Extraction Engine
Adapted from C++ Standard extraction script for Inside the C++ Object Model book

Features:
- Expert-level "under the hood" concept extraction
- Round-robin model rotation: Grok → GPT → Gemini → repeat
- Object model-focused concept naming  
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


class ContentFilter:
    """Filters content to prioritize explanatory text over code for better concept extraction"""
    
    def filter_for_concept_extraction(self, content):
        """Filter content to prioritize explanatory text over code"""
        if not content or len(content.strip()) < 50:
            return content
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        
        filtered_paragraphs = []
        total_original_length = len(content)
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check if this paragraph is code-heavy
            if self._is_code_heavy(para):
                # Keep a brief summary instead of full code
                code_summary = f"[CODE: {para[:80].replace(chr(10), ' ')}...]"
                filtered_paragraphs.append(code_summary)
                current_length += len(code_summary)
            else:
                # Keep explanatory text in full
                filtered_paragraphs.append(para)
                current_length += len(para)
            
            # Stop if we're approaching reasonable length
            if current_length > 2500:  # Leave room for more content
                break
        
        filtered_content = '\n\n'.join(filtered_paragraphs)
        
        # Debug info
        compression_ratio = len(filtered_content) / total_original_length if total_original_length > 0 else 1
        print(f"🔍 Content filtered: {total_original_length} → {len(filtered_content)} chars (ratio: {compression_ratio:.2f})")
        
        return filtered_content
    
    def _is_code_heavy(self, text):
        """Heuristic to detect code vs explanatory text"""
        if len(text.strip()) < 20:  # Too short to analyze
            return False
            
        # Count code indicators
        code_indicators = {
            '{': 2, '}': 2, ';': 1, 
            '#include': 3, 'class ': 2, 'void ': 2, 'int ': 1,
            '->': 1, '::': 1, 'public:': 3, 'private:': 3,
            'virtual ': 2, 'const ': 1, 'return ': 1,
            '++': 1, '--': 1, '==': 1, '!=': 1,
            'cout': 2, 'endl': 2, 'std:': 2
        }
        
        # Assembly/compiler output indicators
        assembly_indicators = {
            'mov ': 3, 'push ': 3, 'pop ': 3, 'call ': 3,
            'jmp ': 3, 'cmp ': 3, 'lea ': 3, 'ret': 3,
            '%eax': 3, '%ebx': 3, '%ecx': 3, '%edx': 3,
            'asm': 3, '.text': 3, '.data': 3
        }
        
        # Combine indicators
        all_indicators = {**code_indicators, **assembly_indicators}
        
        # Calculate weighted score
        total_score = 0
        for indicator, weight in all_indicators.items():
            count = text.lower().count(indicator.lower())
            total_score += count * weight
        
        # Check ratio of code indicators to words
        word_count = len(text.split())
        if word_count == 0:
            return True  # Likely pure symbols
        
        # Threshold: if code score is high relative to word count
        code_ratio = total_score / word_count
        
        # Also check for high symbol-to-letter ratio (another code indicator)
        symbol_count = sum(text.count(c) for c in '{}();[]<>=+-*/')
        letter_count = sum(c.isalpha() for c in text)
        symbol_ratio = symbol_count / max(letter_count, 1)
        
        is_code = code_ratio > 0.3 or symbol_ratio > 0.2
        
        if is_code:
            print(f"📝 Detected code block (score: {code_ratio:.2f}, symbols: {symbol_ratio:.2f}): {text[:60]}...")
        
        return is_code


class ObjectModelChapterMapper:
    """Maps content to Inside the C++ Object Model chapters"""
    
    CHAPTER_MAPPING = {
        "object": ["object", "layout", "structure", "representation"],
        "constructor": ["constructor", "initialization", "ctor", "default constructor"],
        "data": ["data member", "member", "static member", "non-static"],
        "function": ["member function", "virtual", "inline", "static function"],
        "semantics": ["copy semantics", "assignment", "construction", "semantics"],
        "runtime": ["runtime", "virtual", "dynamic", "type identification", "rtti"],
        "efficiency": ["efficiency", "optimization", "performance", "compile time"],
        "memory": ["memory", "allocation", "placement", "pool", "heap"],
        "inheritance": ["inheritance", "base class", "derived", "virtual base"],
        "virtual": ["virtual function", "vtable", "vptr", "virtual dispatch"],
        "template": ["template", "instantiation", "generic", "specialization"]
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
        return "object"


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
        
        print(f"🔄 Round-robin order: { ' → '.join(self.model_order)}")
    
    def get_processor_for_concept(self, concept_index):
        """Get processor using round-robin"""
        model_index = concept_index % len(self.model_order)
        selected_model = self.model_order[model_index]
        return self.processors[selected_model], selected_model


class InsideObjectModelExtractionEngine:
    """Main extraction engine for Inside the C++ Object Model"""
    
    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.content_filter = ContentFilter()
        progress_file = self.output_dir / "progress.json"
        
        # Validate progress file exists and has correct format
        if not progress_file.exists():
            print(f"📝 Creating new progress file: {progress_file}")
        else:
            try:
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                    if "last_processed_page" not in progress_data or "total_concepts_extracted" not in progress_data:
                        print("⚠️  Progress file missing required fields, will be reset")
                        progress_file.unlink()  # Delete invalid progress file
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Invalid progress file format: {e}, creating new one")
                progress_file.unlink()  # Delete corrupted progress file
        
        self.progress_tracker = ProgressTracker(str(progress_file))
        self.model_rotator = MultiModelRotator()
        self.chapter_mapper = ObjectModelChapterMapper()
        
        # Initialize concept memory for deduplication
        self.concept_memory = ConceptMemoryManager()
        print("🧠 Concept memory system initialized for deduplication")
        
        print(f"🏛️  Inside the C++ Object Model Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
    
    def run_extraction_session(self, max_concepts=20):
        """Run extraction session"""
        session_start = datetime.now()
        print(f"\n🔍 Starting Inside the C++ Object Model extraction session (max {max_concepts} concepts)...")
        print(f"🧠 Focus: Object model internals, memory layout, and compiler implementation")
        print(f"🔄 Round-robin: {len(self.model_rotator.model_order)} models rotating per concept")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []
        model_stats = {model: 0 for model in self.model_rotator.model_order}
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            print(f"📖 Extracting C++ Object Model content from page {start_page + 1}...")
            # Start from the next page after the last processed one
            content_blocks = extractor.extract_structured_content(start_page + 1, max_pages=40)
            
            if not content_blocks:
                print("🏁 No more content found.")
                return False
            
            # Detect concepts
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential C++ Object Model concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing C++ Object Model concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Get processor (round-robin)
                processor, model_name = self.model_rotator.get_processor_for_concept(i)
                print(f"🤖 Using {model_name.upper()} for concept {i + 1}")
                
                # Process concept
                processed_concept = self._process_concept(concept, processor, model_name)
                
                if processed_concept:
                    # Check for duplicates before saving
                    is_duplicate, similar_concepts, similarity_scores = self.concept_memory.check_for_duplicates(processed_concept)
                    
                    if is_duplicate:
                        print(f"🚨 DUPLICATE DETECTED - Skipping concept: {processed_concept.get('topic', 'Unknown')}")
                        print(f"   Similar to: {similar_concepts[0]['concept_data'].get('topic', 'Unknown')}")
                        continue
                    
                    if similar_concepts:
                        print(f"⚠️  Similar concept found (score: {similarity_scores[0]:.2f})")
                        print(f"   Existing: {similar_concepts[0]['concept_data'].get('topic', 'Unknown')}")
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
                    print(f"❌ Failed to process concept with {model_name}")
        
        # Update progress
        if content_blocks:
            # Calculate the last page processed based on content blocks
            last_page = max(block["page"] for block in content_blocks)
            self.progress_tracker.progress["last_processed_page"] = last_page
            self.progress_tracker.progress["total_concepts_extracted"] = (
                self.progress_tracker.progress.get("total_concepts_extracted", 0) + concepts_extracted
            )
            self.progress_tracker.save_progress()
            print(f"📊 Progress updated: Last processed page {last_page}, Total concepts: {self.progress_tracker.progress['total_concepts_extracted']}")
        else:
            print("⚠️  No content blocks processed, progress not updated")
        
        # Generate summary
        self._generate_summary(session_start, extracted_concepts, model_stats)
        
        print(f"\n📊 Inside the C++ Object Model session complete: {concepts_extracted} concepts extracted")
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
                # Build expert prompt for GPT
                prompt = self._build_expert_prompt(concept["raw_content"])
                response = processor._call_gpt4_nano_api(prompt)
                return self._parse_gpt_response(response)
                
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
        """Build expert-level prompt for Inside the C++ Object Model with intelligent content filtering"""
        
        # Filter content to prioritize explanatory text over code
        filtered_content = self.content_filter.filter_for_concept_extraction(content)
        
        return f"""You are an expert C++ systems architect creating training data for advanced C++ object model knowledge.

Extract ONE expert-level C++ Object Model concept focusing on internal implementation, memory layout, and compiler behavior.

FOCUS ON:
- How objects are laid out in memory
- Virtual function table mechanisms
- Constructor/destructor implementation details
- Inheritance and polymorphism internals
- Compiler optimization strategies

Return valid JSON using this format with naming convention {{"book_code"}}_{{category}}_{{normalized_topic}}_{{uniqueid}}.json:
{{
  "topic": "C++ Object Model Implementation Concept",
  "explanation": "Deep technical explanation covering memory layout, vtables, compiler behavior, and performance characteristics.",
  "syntax": "C++ syntax with implementation notes",
  "code_example": [
    "#include <iostream>",
    "// Expert-level C++ Object Model example"
  ],
  "example_explanation": "Expert analysis of object model behavior and implementation details."
}}

Content: {filtered_content}

Extract C++ Object Model concept as JSON:"""
    
    def _parse_grok_response(self, response_text):
        """Parse Grok response with enhanced error handling"""
        try:
            print(f"🐛 DEBUG - Raw GROK response ({len(response_text)} chars): {response_text[:800]}...")
            
            # Check if response looks truncated (ends mid-sentence/mid-word)
            if len(response_text) > 100 and not response_text.strip().endswith(('}', '"', ']')):
                print(f"⚠️  GROK response appears truncated (ends with: '{response_text[-50:]}')")
            
            # Look for JSON with quoted property names (real JSON, not C++ code)
            match = re.search(r'\{[^{}]*"[^"]+"\s*:[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if not match:
                # Fallback: find any JSON object that contains "topic"
                match = re.search(r'\{[^{}]*"topic"[^{}]*\}', response_text, re.DOTALL)
            
            if match:
                json_str = match.group(0).strip()
                print(f"🐛 DEBUG - Extracted JSON string ({len(json_str)} chars): {json_str[:400]}...")
                
                # Validate JSON completeness before parsing
                if not self._is_json_complete(json_str):
                    print(f"❌ JSON appears incomplete, skipping")
                    return None
                
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GROK extracted concept: {concept['topic']}")
                    return concept
                else:
                    print(f"❌ JSON missing required 'topic' field")
                    
            print("❌ Failed to find a valid JSON object in the Grok response.")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Grok: {e}")
            if 'json_str' in locals():
                print(f"🐛 DEBUG - Problematic JSON string: {json_str[:200]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during Grok response parsing: {e}")
            return None

    def _parse_gemini_response(self, response_text):
        """Parse Gemini response with enhanced error handling"""
        try:
            print(f"🐛 DEBUG - Raw GEMINI response ({len(response_text)} chars): {response_text[:800]}...")
            
            # Remove markdown code blocks if present
            cleaned_response = re.sub(r'```json\s*', '', response_text)
            cleaned_response = re.sub(r'\s*```', '', cleaned_response)
            
            # Check if response looks truncated
            if len(cleaned_response) > 100 and not cleaned_response.strip().endswith(('}', '"', ']')):
                print(f"⚠️  GEMINI response appears truncated (ends with: '{cleaned_response[-50:]}')")
            
            # Look for JSON with quoted property names (real JSON, not C++ code)
            match = re.search(r'\{[^{}]*"[^"]+"\s*:[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_response, re.DOTALL)
            if not match:
                # Fallback: find any JSON object that contains "topic"
                match = re.search(r'\{[^{}]*"topic"[^{}]*\}', cleaned_response, re.DOTALL)
            
            if match:
                json_str = match.group(0).strip()
                print(f"🐛 DEBUG - Extracted JSON string ({len(json_str)} chars): {json_str[:400]}...")
                
                # Validate JSON completeness before parsing
                if not self._is_json_complete(json_str):
                    print(f"❌ JSON appears incomplete, skipping")
                    return None
                
                concept = json.loads(json_str)
                if 'topic' in concept:
                    print(f"✅ GEMINI extracted concept: {concept['topic']}")
                    return concept
                else:
                    print(f"❌ JSON missing required 'topic' field")
                    
            print("❌ Failed to find a valid JSON object in the Gemini response.")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from Gemini: {e}")
            if 'json_str' in locals():
                print(f"🐛 DEBUG - Problematic JSON string: {json_str[:200]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during Gemini response parsing: {e}")
            return None
    
    def _parse_gpt_response(self, response_text):
        """Parse GPT response with enhanced error handling"""
        try:
            print(f"🐛 DEBUG - Raw GPT response ({len(response_text)} chars): {response_text[:800]}...")
            
            # Check if response looks truncated
            if len(response_text) > 100 and not response_text.strip().endswith(('}', '"', ']')):
                print(f"⚠️  GPT response appears truncated (ends with: '{response_text[-50:]}')")
            
            # Look for JSON with quoted property names (real JSON, not C++ code)
            match = re.search(r'\{[^{}]*"[^"]+"\s*:[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if not match:
                # Fallback: find any JSON object that contains "topic"
                match = re.search(r'\{[^{}]*"topic"[^{}]*\}', response_text, re.DOTALL)
                
            if match:
                json_str = match.group(0).strip()
                print(f"🐛 DEBUG - Extracted JSON string ({len(json_str)} chars): {json_str[:400]}...")
                
                # Validate JSON completeness before parsing
                if not self._is_json_complete(json_str):
                    print(f"❌ JSON appears incomplete, skipping")
                    return None
                
                concept = json.loads(json_str)
                
                # Handle nested structure where GPT returns {filename: {actual_concept}}
                if 'topic' not in concept and len(concept) == 1:
                    # Extract the nested concept
                    nested_key = next(iter(concept.keys()))
                    if isinstance(concept[nested_key], dict) and 'topic' in concept[nested_key]:
                        concept = concept[nested_key]
                        print(f"📋 GPT used nested structure, extracted inner concept")
                
                if 'topic' in concept:
                    print(f"✅ GPT extracted concept: {concept['topic']}")
                    return concept
                else:
                    print(f"❌ JSON missing required 'topic' field")
                    
            print("❌ Failed to find a valid JSON object in the GPT response.")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON from GPT: {e}")
            if 'json_str' in locals():
                print(f"🐛 DEBUG - Problematic JSON string: {json_str[:200]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during GPT response parsing: {e}")
            return None
    
    def _is_json_complete(self, json_str):
        """Check if JSON string appears complete by validating bracket/brace balance"""
        if not json_str.strip():
            return False
            
        # Count brackets and braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Check basic balance
        if open_braces != close_braces or open_brackets != close_brackets:
            print(f"🔍 Brace/bracket mismatch: {{:{open_braces}→{close_braces}, [:{open_brackets}→{close_brackets}")
            return False
        
        # Check if it ends properly (should end with } or ] or ")
        if not json_str.strip().endswith(('}', ']', '"')):
            print(f"🔍 JSON doesn't end properly: '{json_str[-20:]}'")
            return False
            
        return True
    
    def _save_concept(self, concept, concept_number, chapter_prefix):
        """Save concept with chapter-based naming using recommended convention"""
        # Create a unique ID (6-character hash)
        import hashlib
        content_hash = hashlib.md5(str(concept).encode()).hexdigest()[:6]
        
        # Format: {book_code}_{category}_{normalized_topic}_{uniqueid}.json
        safe_topic = self._safe_filename(concept.get('topic', 'unknown'))[:40]  # Up to 40 characters
        filename = f"objmdl_{chapter_prefix}_{safe_topic}_{content_hash}.json"
        
        # Add metadata
        if "extraction_metadata" not in concept:
            concept["extraction_metadata"] = {}
        
        concept["extraction_metadata"].update({
            "source": "Inside the C++ Object Model",
            "chapter": chapter_prefix,
            "extraction_type": "object_model_internals",
            "extraction_date": datetime.now().isoformat(),
            "book_code": "objmdl"
        })
        
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)
        
        return filename
    
    def _safe_filename(self, topic):
        """Create safe filename"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()
    
    def _generate_summary(self, session_start, extracted_concepts, model_stats):
        """Generate session summary"""
        session_duration = datetime.now() - session_start
        
        summary_filename = f"inside_cpp_object_model_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_path = self.output_dir / summary_filename
        
        summary_content = f"""# Inside the C++ Object Model Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {session_duration.total_seconds():.1f} seconds
**Extraction Type:** C++ Object Model Internals Analysis

## Model Statistics
"""
        
        for model, count in model_stats.items():
            summary_content += f"- **{model.upper()}**: {count} concepts\n"
        
        summary_content += f"\n## Extracted Concepts: {len(extracted_concepts)}\n\n"
        
        for concept in extracted_concepts:
            summary_content += f"### {concept['topic']}\n"
            summary_content += f"**Chapter:** {concept['chapter']} | **Processor:** {concept['processor'].upper()}\n"
            summary_content += f"**File:** `{concept['filename']}`\n\n"
        
        summary_content += "\n---\n*Inside the C++ Object Model Analysis Complete*"
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 Summary saved: {summary_filename}")


def main():
    """Main execution"""
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/Inside_the_C++_Object_Model.pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/Inside_the_C++_Object_Model"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config/config.env"):
        print(f"❌ Config file not found")
        return
    
    # Run extraction
    engine = InsideObjectModelExtractionEngine(pdf_path, output_dir)
    
    # Run normal extraction
    engine.run_extraction_session(max_concepts=20)


if __name__ == "__main__":
    main()