#!/usr/bin/env python3

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can find project root from anywhere
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Always work from project root for consistent imports
if os.getcwd() != PROJECT_ROOT:
    os.chdir(PROJECT_ROOT)

# Import core modules
from core.pdf_extractor import PDFStructureExtractor
from core.concept_detector import ConceptBoundaryDetector
from core.progress_tracker import ProgressTracker
from processors.gemini_processor import GeminiAtomicProcessor
from books.semantic_deduplication import SemanticDeduplicator

class CSAPPConceptExtractor:
    """
    CSAPP-specific concept extractor focusing on systems programming
    and computer architecture concepts starting from page 14
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv(os.path.join(PROJECT_ROOT, "config", "config.env"))
        
        # Book configuration
        self.book_config = {
            "pdf_path": "CSAPP_2016.pdf",
            "output_dir": "outputs/csapp_2016",
            "processor": "gemini",
            "start_page": 14,  # Skip early chapters
            "source_title": "Computer Systems: A Programmer's Perspective (3rd Edition)",
            "book_name": "csapp_2016"
        }
        
        # Create output directory
        self.output_dir = Path(self.book_config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress tracker
        progress_file = self.output_dir / "progress.json"
        self.progress_tracker = ProgressTracker(str(progress_file))
        
        # Initialize processors
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.ai_processor = GeminiAtomicProcessor(gemini_api_key)
        
        # Initialize deduplicator for CSAPP concepts
        self.deduplicator = SemanticDeduplicator(
            str(self.output_dir),
            similarity_threshold=0.7  # Slightly lower for systems concepts
        )
        
        print("🖥️  CSAPP Systems Architecture Concept Extractor Initialized")
        print(f"📖 Book: {self.book_config['source_title']}")
        print(f"🎯 Focus: Computer systems and architecture")
        print(f"📄 Starting from page: {self.book_config['start_page']}")
        print(f"📁 Output: {self.output_dir}")
        print(f"⚡ Processor: Gemini (systems-aware)")

    def is_valid_systems_concept(self, raw_content):
        """
        Validate if content contains valid CSAPP systems programming concepts
        Based on our atomic concept definition
        """
        # Handle different input types properly
        if isinstance(raw_content, list):
            content_text = "\n".join(str(item) for item in raw_content)
        elif isinstance(raw_content, dict):
            content_text = str(raw_content.get('content', raw_content.get('raw_content', '')))
        else:
            content_text = str(raw_content)
            
        content_lower = content_text.lower()
        
        # EXCLUSION patterns (what we DON'T want)
        exclusion_patterns = [
            "binary representation",
            "two's complement arithmetic", 
            "ieee floating point",
            "hexadecimal notation",
            "bit manipulation",
            "printf", "scanf", "main function",
            "variable declaration", "if statement", "for loop",
            "hello world",
            "static linking", "dynamic linking",
            "object files", "symbol table",
            "linker", "loader"
        ]
        
        for pattern in exclusion_patterns:
            if pattern in content_lower:
                return False, f"Excluded: {pattern}"
        
        # INCLUSION indicators (what we DO want)
        systems_indicators = [
            "assembly", "instruction", "register", "stack frame",
            "calling convention", "x86", "mov", "push", "pop",
            "pipeline", "hazard", "branch prediction", "superscalar",
            "out of order", "instruction set", "cpu",
            "cache", "memory hierarchy", "locality", "cache miss",
            "cache hit", "cache line", "associativity",
            "virtual memory", "virtual address", "physical address",
            "page table", "tlb", "address translation", "page fault",
            "thread", "synchronization", "mutex", "semaphore",
            "race condition", "deadlock", "atomic", "critical section",
            "system call", "exception", "interrupt", "context switch",
            "process", "signal", "exceptional control flow",
            "socket", "tcp", "udp", "client", "server", "protocol",
            "network", "connection",
            "performance", "optimization", "bottleneck", "profiling",
            "throughput", "latency", "scalability"
        ]
        
        indicator_count = 0
        found_indicators = []
        
        for indicator in systems_indicators:
            if indicator in content_lower:
                indicator_count += 1
                found_indicators.append(indicator)
        
        if indicator_count >= 2:
            return True, f"Systems concept: {', '.join(found_indicators[:3])}"
        elif indicator_count == 1:
            return True, f"Potential systems concept: {found_indicators[0]}"
        else:
            return False, "No systems programming indicators found"

    def detect_code_content(self, content):
        """Detect if content contains code examples"""
        code_indicators = [
            "int main", "void", "return", "#include",
            "printf", "malloc", "free", "{", "}",
            "mov", "push", "pop", "call", "ret",  # Assembly
            "socket(", "connect(", "bind(", "listen(",  # System calls
            "fork(", "exec", "pthread_", "mutex_"
        ]
        
        content_lower = str(content).lower()
        return any(indicator in content_lower for indicator in code_indicators)

    def extract_daily_concepts(self, max_concepts=4):
        """Extract daily batch of CSAPP systems concepts"""
        print(f"\n🚀 Starting CSAPP Daily Extraction (max {max_concepts} concepts)")
        
        # Get current progress - FIXED: proper calculation
        last_page = self.progress_tracker.progress.get("last_processed_page", self.book_config["start_page"] - 1)
        start_page = max(last_page + 1, self.book_config["start_page"])
        
        print(f"📄 Resuming from page {start_page}")
        
        extracted_concepts = []
        actual_last_page = start_page  # FIXED: properly initialize this variable
        
        # PDF extraction with systems focus
        try:
            with PDFStructureExtractor(self.book_config["pdf_path"]) as extractor:
                content_blocks = extractor.extract_structured_content(
                    start_page=start_page - 1,  # PDF pages are 0-indexed
                    max_pages=15  # Process 15 pages per session
                )
                
                print(f"📖 Extracted {len(content_blocks)} content blocks from CSAPP")
                
                # PROPER APPROACH: Use ConceptBoundaryDetector as intended
                concept_detector = ConceptBoundaryDetector()
                atomic_concepts = concept_detector.detect_atomic_concepts(content_blocks)
                
                print(f"🎯 Identified {len(atomic_concepts)} potential atomic concepts")
                
                # Process each atomic concept for systems content
                for concept_data in atomic_concepts:
                    if len(extracted_concepts) >= max_concepts:
                        break
                    
                    # FIXED: Validate concept data structure before using
                    if not isinstance(concept_data, dict) or 'raw_content' not in concept_data:
                        print(f"⚠️  Invalid concept data structure, skipping...")
                        continue
                    
                    # Validate systems content first
                    is_valid, reason = self.is_valid_systems_concept(concept_data['raw_content'])
                    
                    if not is_valid:
                        print(f"⏭️  Skipping concept: {reason}")
                        continue
                    
                    print(f"✅ Valid systems concept: {reason}")
                    
                    # Add source title to concept data
                    concept_data["source_title"] = self.book_config["source_title"]
                    
                    # Process with Gemini (systems-aware)
                    processed_concept = self.ai_processor.process_concept(
                        concept_data, 
                        book_name=self.book_config["book_name"]
                    )
                    
                    if processed_concept:
                        # Deduplication handled automatically by GeminiAtomicProcessor
                        concept_number = self.progress_tracker.progress['total_concepts_extracted'] + len(extracted_concepts) + 1
                        self.save_concept(processed_concept, concept_number)
                        extracted_concepts.append(processed_concept)
                        print(f"💾 Saved CSAPP concept #{concept_number}: {processed_concept.get('topic', 'Unknown')}")
                        
                        # Track actual last page from concept data
                        if 'page_range' in concept_data:
                            try:
                                page_parts = str(concept_data['page_range']).split('-')
                                if page_parts:
                                    page_end = int(page_parts[-1])
                                    actual_last_page = max(actual_last_page, page_end)
                            except (ValueError, IndexError):
                                pass
                                    
                # FIXED: Update progress with actual last processed page
                final_page = max(actual_last_page, start_page + 14)  # At least process the intended pages
                session_info = {
                    "page_range": f"{start_page}-{final_page}",
                    "chapter": "Auto-detected"
                }
                
                self.progress_tracker.update_progress(
                    final_page,
                    len(extracted_concepts),
                    session_info
                )
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            import traceback
            traceback.print_exc()  # Show full error for debugging
            return []
        
        print(f"\n📊 CSAPP Extraction Complete:")
        print(f"   Systems concepts extracted: {len(extracted_concepts)}")
        print(f"   Total CSAPP concepts: {self.progress_tracker.progress['total_concepts_extracted']}")
        
        return extracted_concepts

    def save_concept(self, concept, concept_number):
        """Save CSAPP concept with systems-specific naming"""
        # FIXED: Sanitize topic for safe filename
        topic = concept.get('topic', 'unknown')
        safe_topic = re.sub(r'[^a-zA-Z0-9_]', '_', topic.lower())[:30]
        
        filename = f"csapp_concept_{concept_number:03d}_{safe_topic}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(concept, f, indent=2, ensure_ascii=False)

    def generate_daily_summary(self, extracted_concepts):
        """Generate CSAPP-specific daily summary"""
        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.output_dir / f"csapp_daily_summary_{today}.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Daily CSAPP Systems Extraction Summary\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Book:** Computer Systems: A Programmer's Perspective (3rd Edition)\n")
            f.write(f"**Focus:** Computer architecture and systems programming\n\n")
            
            f.write(f"## Systems Concepts Extracted Today: {len(extracted_concepts)}\n\n")
            
            for i, concept in enumerate(extracted_concepts, 1):
                f.write(f"### {i}. {concept.get('topic', 'Unknown Topic')}\n")
                explanation = concept.get('explanation', '')[:200]
                f.write(f"**Systems concept:** {explanation}...\n\n")
            
            f.write(f"## CSAPP Progress Summary\n")
            f.write(f"- **Total Systems Concepts:** {self.progress_tracker.progress['total_concepts_extracted']}\n")
            f.write(f"- **Extraction Sessions:** {len(self.progress_tracker.progress['extraction_sessions'])}\n")
            f.write(f"- **Last Processed Page:** {self.progress_tracker.progress['last_processed_page']}\n\n")
            
            f.write(f"## Next Session\n")
            f.write(f"Continue CSAPP systems extraction to explore more computer architecture concepts.\n\n")
            f.write(f"---\n*Generated by CSAPP Systems Architecture Extraction Engine*\n")

def main():
    """Main extraction function for CSAPP systems concepts"""
    try:
        extractor = CSAPPConceptExtractor()
        
        # Extract daily concepts (max 4 systems concepts)
        concepts = extractor.extract_daily_concepts(max_concepts=4)
        
        # Generate summary
        extractor.generate_daily_summary(concepts)
        
        print(f"\n🎉 CSAPP systems extraction completed successfully!")
        print(f"📈 Progress: {extractor.progress_tracker.progress['total_concepts_extracted']} total systems concepts")
        
    except Exception as e:
        print(f"💥 CSAPP extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
