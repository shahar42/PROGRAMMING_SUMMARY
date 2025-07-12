#!/usr/bin/env python3
"""
Content-Intelligent C Concept Extraction Engine
Archaeologically extracts atomic programming concepts from K&R C book
"""

import os
import json
import re
import pdfplumber
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

class ProgressTracker:
    """Tracks extraction progress for resumable operations"""
    
    def __init__(self, progress_file="progress.json"):
        self.progress_file = progress_file
        self.progress = self.load_progress()
    
    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Only parse if file has content
                        return json.loads(content)
                    else:
                        print("📝 Found empty progress file, initializing fresh...")
            except (json.JSONDecodeError, Exception) as e:
                print(f"📝 Progress file corrupted ({e}), initializing fresh...")
        
        # Return fresh progress structure
        return {
            "last_processed_page": 0,
            "total_concepts_extracted": 0,
            "extraction_sessions": [],
            "current_chapter": 1
        }
    
    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def update_progress(self, page_num, concepts_count, session_info):
        self.progress["last_processed_page"] = page_num
        self.progress["total_concepts_extracted"] += concepts_count
        self.progress["extraction_sessions"].append({
            "date": datetime.now().isoformat(),
            "concepts_extracted": concepts_count,
            "page_range": session_info.get("page_range", ""),
            "chapter": session_info.get("chapter", "")
        })
        self.save_progress()

class PDFStructureExtractor:
    """Intelligently extracts and classifies content from PDF"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pdf = None
    
    def __enter__(self):
        self.pdf = pdfplumber.open(self.pdf_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf:
            self.pdf.close()
    
    def extract_structured_content(self, start_page=0, max_pages=20):
        """Extract content with structure awareness"""
        content_blocks = []
        
        for page_num in range(start_page, min(len(self.pdf.pages), start_page + max_pages)):
            page = self.pdf.pages[page_num]
            text = page.extract_text()
            
            if not text or len(text.strip()) < 50:  # Skip sparse pages
                continue
            
            # Classify content types
            classified_content = self._classify_content(text, page_num + 1)
            content_blocks.extend(classified_content)
        
        return content_blocks
    
    def _classify_content(self, text, page_num):
        """Classify text into headers, explanations, code blocks, etc."""
        blocks = []
        lines = text.split('\n')
        current_block = {"type": "unknown", "content": [], "page": page_num}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect headers (chapter/section markers)
            if self._is_header(line):
                if current_block["content"]:
                    blocks.append(current_block)
                current_block = {"type": "header", "content": [line], "page": page_num}
            
            # Detect code blocks
            elif self._is_code_line(line):
                if current_block["type"] != "code":
                    if current_block["content"]:
                        blocks.append(current_block)
                    current_block = {"type": "code", "content": [line], "page": page_num}
                else:
                    current_block["content"].append(line)
            
            # Regular explanatory text
            else:
                if current_block["type"] not in ["text", "unknown"]:
                    if current_block["content"]:
                        blocks.append(current_block)
                    current_block = {"type": "text", "content": [line], "page": page_num}
                else:
                    current_block["content"].append(line)
        
        if current_block["content"]:
            blocks.append(current_block)
        
        return blocks
    
    def _is_header(self, line):
        """Detect if line is a chapter/section header"""
        # K&R patterns: "Chapter 1", "1.1", "2.3 The For Statement"
        header_patterns = [
            r'^Chapter\s+\d+',
            r'^\d+\.\d+\s+\w+',
            r'^[A-Z][A-Za-z\s]+$'  # All caps or title case standalone
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, line) and len(line) < 80:
                return True
        return False
    
    def _is_code_line(self, line):
        """Detect if line contains C code"""
        code_indicators = [
            r'#include\s*<',
            r'\bint\s+main\s*\(',
            r'\bprintf\s*\(',
            r'\bfor\s*\(',
            r'\bwhile\s*\(',
            r'\bif\s*\(',
            r'^\s*{',
            r'^\s*}',
            r';\s*$',
            r'/\*.*\*/',
            r'//.*'
        ]
        
        for indicator in code_indicators:
            if re.search(indicator, line):
                return True
        return False

class ConceptBoundaryDetector:
    """Detects natural atomic concept boundaries"""
    
    def detect_atomic_concepts(self, content_blocks):
        """Group content blocks into atomic concepts"""
        concepts = []
        current_concept = []
        
        for block in content_blocks:
            # Start new concept on headers
            if block["type"] == "header":
                if current_concept:
                    concepts.append(self._finalize_concept(current_concept))
                current_concept = [block]
            
            # Add to current concept
            else:
                current_concept.append(block)
                
                # Check if we have a complete atomic concept
                if self._is_complete_concept(current_concept):
                    concepts.append(self._finalize_concept(current_concept))
                    current_concept = []
        
        # Don't forget the last concept
        if current_concept:
            concepts.append(self._finalize_concept(current_concept))
        
        return concepts
    
    def _is_complete_concept(self, blocks):
        """Check if we have a complete atomic concept"""
        has_explanation = any(b["type"] == "text" for b in blocks)
        has_code = any(b["type"] == "code" for b in blocks)
        
        # A complete concept should have both explanation and code
        # Or be a substantial standalone explanation
        return (has_explanation and has_code) or len(blocks) > 3
    
    def _finalize_concept(self, blocks):
        """Convert block sequence into structured concept"""
        concept = {
            "blocks": blocks,
            "page_range": f"{blocks[0]['page']}-{blocks[-1]['page']}",
            "has_code": any(b["type"] == "code" for b in blocks),
            "has_explanation": any(b["type"] == "text" for b in blocks),
            "raw_content": self._extract_raw_content(blocks)
        }
        return concept
    
    def _extract_raw_content(self, blocks):
        """Extract clean text from blocks"""
        content = []
        for block in blocks:
            content.extend(block["content"])
        return "\n".join(content)

class GeminiAtomicProcessor:
    """Processes raw content into atomic training data using Gemini"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"🤖 Gemini 1.5 Flash initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            raise
    
    def process_concept(self, concept_data):
        """Transform raw concept into atomic training format"""
        
        prompt = self._build_atomic_extraction_prompt(concept_data["raw_content"])
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse Gemini's response into structured format
            parsed_concept = self._parse_gemini_response(response.text)
            
            # Add metadata
            parsed_concept["extraction_metadata"] = {
                "source": "The C Programming Language - Kernighan & Ritchie",
                "page_range": concept_data["page_range"],
                "extraction_date": datetime.now().isoformat(),
                "has_code": concept_data["has_code"],
                "has_explanation": concept_data["has_explanation"]
            }
            
            return parsed_concept
            
        except Exception as e:
            print(f"Error processing concept: {e}")
            return None
    
    def _build_atomic_extraction_prompt(self, raw_content):
        """Build surgical prompt for atomic concept extraction"""
        
        return f"""You are a pedagogical knowledge architect creating atomic training data for AI models learning C programming.

Your task: Extract this content into a SINGLE atomic concept following this EXACT structure.

An atomic concept contains:
1. **Concept Definition**: Clear explanation of what it is and why it's used
2. **Syntax**: The generalized code structure/pattern  
3. **Minimal Compilable Example**: Complete, runnable C program demonstrating ONLY this concept
4. **Example Explanation**: How the specific code demonstrates the concept

CRITICAL REQUIREMENTS:
- Extract only ONE atomic concept (the most prominent one)
- Example must be complete and compilable
- Focus on the core concept, avoid feature creep
- Use clear, pedagogical language

Return your response as valid JSON in this EXACT format:
{{
  "topic": "Concept Name",
  "explanation": "Clear definition of what this concept is and why it's used...",
  "syntax": "generalized code pattern",
  "code_example": [
    "line1 of complete program",
    "line2 of complete program",
    "..."
  ],
  "example_explanation": "Explanation of what this specific example does and how it demonstrates the concept..."
}}

CONTENT TO PROCESS:
{raw_content}

Extract the atomic concept as JSON:"""
    
    def _parse_gemini_response(self, response_text):
        """Parse Gemini's JSON response"""
        try:
            # Extract JSON from response (handle potential markdown wrapping)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response was: {response_text[:500]}...")
            return None

class QualityValidator:
    """Validates extracted concepts meet training data standards"""
    
    def validate_concept(self, concept):
        """Check if concept meets quality standards"""
        required_fields = ["topic", "explanation", "syntax", "code_example", "example_explanation"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in concept:
                return False, f"Missing required field: {field}"
        
        # Check code example is substantial
        if not concept["code_example"] or len(concept["code_example"]) < 3:
            return False, "Code example too short"
        
        # Check for C programming signatures
        code_text = "\n".join(concept["code_example"])
        if "#include" not in code_text or "main" not in code_text:
            return False, "Code example doesn't appear to be complete C program"
        
        return True, "Valid"

class ExtractionEngine:
    """Main orchestrator for the content-intelligent extraction process"""
    
    def __init__(self, pdf_path, output_dir, config_file="config.env"):
        load_dotenv(config_file)
        
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Verify API key is loaded
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(f"❌ GEMINI_API_KEY not found in {config_file}")
            print(f"📝 Please ensure config.env contains: GEMINI_API_KEY=your_actual_api_key")
            raise ValueError("Missing GEMINI_API_KEY")
        
        print(f"✅ API key loaded successfully (length: {len(api_key)} chars)")
        
        # Initialize components
        self.progress_tracker = ProgressTracker()
        self.processor = GeminiAtomicProcessor(api_key)
        self.validator = QualityValidator()
        
        print(f"🏛️  Archaeological C Extraction Engine Initialized")
        print(f"📚 Source: {pdf_path}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Previous progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts extracted")
    
    def run_extraction_session(self, max_concepts=5):
        """Run one extraction session with daily summary generation"""
        session_start = datetime.now()
        print(f"\n🔍 Starting extraction session...")
        
        start_page = self.progress_tracker.progress["last_processed_page"]
        concepts_extracted = 0
        extracted_concepts = []  # Track what we extracted for summary
        
        with PDFStructureExtractor(self.pdf_path) as extractor:
            # Extract structured content
            print(f"📖 Extracting content from page {start_page + 1}...")
            content_blocks = extractor.extract_structured_content(start_page, max_pages=15)
            
            if not content_blocks:
                print("🏁 No more content found. Extraction complete!")
                self._generate_completion_summary(session_start)
                return False
            
            # Detect atomic concept boundaries
            detector = ConceptBoundaryDetector()
            concepts = detector.detect_atomic_concepts(content_blocks)
            
            print(f"🧠 Detected {len(concepts)} potential atomic concepts")
            
            # Process each concept
            for i, concept in enumerate(concepts[:max_concepts]):
                print(f"\n⚡ Processing concept {i+1}/{min(len(concepts), max_concepts)}...")
                
                # Generate atomic training data
                processed_concept = self.processor.process_concept(concept)
                
                if processed_concept:
                    # Validate quality
                    is_valid, message = self.validator.validate_concept(processed_concept)
                    
                    if is_valid:
                        # Save to file
                        filename = self._save_concept(processed_concept, concepts_extracted)
                        concepts_extracted += 1
                        
                        # Track for summary
                        extracted_concepts.append({
                            "topic": processed_concept.get('topic', 'Unknown'),
                            "explanation": processed_concept.get('explanation', 'No explanation available'),
                            "filename": filename,
                            "page_range": processed_concept["extraction_metadata"]["page_range"]
                        })
                        
                        print(f"✅ Saved atomic concept: {processed_concept.get('topic', 'Unknown')}")
                    else:
                        print(f"❌ Quality check failed: {message}")
                else:
                    print(f"❌ Failed to process concept")
        
        # Update progress
        last_page = max(block["page"] for concept in concepts for block in concept["blocks"])
        session_info = {"page_range": f"{start_page + 1}-{last_page}", "chapter": "Auto-detected"}
        
        self.progress_tracker.update_progress(
            last_page,
            concepts_extracted,
            session_info
        )
        
        # Generate daily summary
        self._generate_daily_summary(session_start, extracted_concepts, session_info)
        
        print(f"\n📊 Session complete: {concepts_extracted} atomic concepts extracted")
        print(f"📈 Total progress: {self.progress_tracker.progress['total_concepts_extracted']} concepts")
        
        return concepts_extracted > 0
    
    def _save_concept(self, concept, concept_number):
        """Save atomic concept to JSON file"""
        filename = f"concept_{self.progress_tracker.progress['total_concepts_extracted'] + concept_number + 1:03d}_{self._safe_filename(concept.get('topic', 'unknown'))}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(concept, f, indent=2)
        
        return filename
    
    def _generate_daily_summary(self, session_start, extracted_concepts, session_info):
        """Generate daily summary report"""
        session_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"daily_summary_{session_date}.md"
        summary_path = self.output_dir / summary_filename
        
        duration = datetime.now() - session_start
        
        summary_content = f"""# Daily C Concept Extraction Summary
**Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {duration.total_seconds():.1f} seconds
**Page Range:** {session_info['page_range']}

## Concepts Extracted Today: {len(extracted_concepts)}

"""
        
        for i, concept in enumerate(extracted_concepts, 1):
            summary_content += f"""### {i}. {concept['topic']}
**What it's about:** {concept['explanation'][:200]}{'...' if len(concept['explanation']) > 200 else ''}

- **File:** `{concept['filename']}`
- **Pages:** {concept['page_range']}

"""
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        summary_content += f"""## Progress Summary
- **Total Concepts Extracted:** {total_concepts}
- **Extraction Sessions Completed:** {len(self.progress_tracker.progress['extraction_sessions'])}
- **Last Processed Page:** {self.progress_tracker.progress['last_processed_page']}

## Next Session
Run the extraction script again tomorrow to continue processing the K&R C Programming book.

---
*Generated by Archaeological C Extraction Engine*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"📋 Daily summary saved: {summary_filename}")
    
    def _generate_completion_summary(self, session_start):
        """Generate final completion summary"""
        completion_date = session_start.strftime("%Y-%m-%d")
        summary_filename = f"extraction_complete_{completion_date}.md"
        summary_path = self.output_dir / summary_filename
        
        total_concepts = self.progress_tracker.progress['total_concepts_extracted']
        total_sessions = len(self.progress_tracker.progress['extraction_sessions'])
        
        summary_content = f"""# 🎉 K&R C Programming Book Extraction Complete!

**Completion Date:** {session_start.strftime("%Y-%m-%d %H:%M:%S")}

## Final Statistics
- **Total Atomic Concepts Extracted:** {total_concepts}
- **Total Extraction Sessions:** {total_sessions}
- **Total Pages Processed:** {self.progress_tracker.progress['last_processed_page']}

## All Extracted Concepts
Your complete C programming training dataset is now ready in the `summeries/` directory.

Each concept follows the atomic structure:
- ✅ Concept Definition
- ✅ Syntax Pattern  
- ✅ Compilable Example
- ✅ Example Explanation

## Training Data Usage
All `concept_*.json` files are now ready for machine learning model training or educational purposes.

---
*Archaeological excavation of "The C Programming Language" by Kernighan & Ritchie complete!*
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"🏆 Completion summary saved: {summary_filename}")
    
    def _safe_filename(self, topic):
        """Create safe filename from topic"""
        safe = re.sub(r'[^\w\s-]', '', topic)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:30]

def main():
    """Main execution"""
    # Configuration
    pdf_path = "/home/shahar42/Suumerizing_C_holy_grale_book/The C Programming Language (Kernighan Ritchie).pdf"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/summeries"
    
    # Verify files exist
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    if not os.path.exists("config.env"):
        print(f"❌ Config file not found. Please create config.env with GEMINI_API_KEY=your_key")
        return
    
    # Initialize and run extraction engine
    engine = ExtractionEngine(pdf_path, output_dir)
    
    # Run extraction session
    continue_extraction = engine.run_extraction_session(max_concepts=4)
    
    if not continue_extraction:
        print("\n🎉 Book extraction complete! All atomic concepts have been archaeologically excavated.")
    else:
        print(f"\n⏳ Run script again tomorrow to continue extraction...")

if __name__ == "__main__":
    main()
