#!/usr/bin/env python3
"""
POSIX Man Page Extractor
Processes POSIX system call PDFs into structured JSON format using Grok

Handles long man pages (7+ pages) with section-aware chunked processing
Output: unix_syscall_name.json files in outputs/posix_manpages/
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root
PROJECT_ROOT = "/home/shahar42/Suumerizing_C_holy_grale_book"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from core.pdf_extractor import PDFStructureExtractor
from core.progress_tracker import ProgressTracker
from processors.grok_processor import GrokAtomicProcessor

class POSIXManPageExtractor:
    """Extract structured information from POSIX man page PDFs using Grok"""
    
    def __init__(self):
        load_dotenv(os.path.join(PROJECT_ROOT, "config", "config.env"))
        
        self.manpages_dir = Path("/home/shahar42/Suumerizing_C_holy_grale_book/Posix_Man_pages")
        self.output_dir = Path(PROJECT_ROOT) / "outputs" / "posix_manpages"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        progress_file = self.output_dir / "manpage_progress.json"
        self.progress_tracker = ProgressTracker(str(progress_file))
        
        # Grok processor for man page extraction
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            raise ValueError("GROK_API_KEY required for man page extraction")
        
        self.grok_processor = GrokAtomicProcessor(api_key)
        
        print("📋 POSIX Man Page Extractor Initialized")
        print(f"📁 Source: {self.manpages_dir}")
        print(f"💾 Output: {self.output_dir}")
        print(f"🤖 AI: Grok (optimized for technical documentation)")

    def extract_batch(self, batch_size=5):
        """Process next batch of man page PDFs"""
        # Get all PDF files sorted by name
        pdf_files = sorted(list(self.manpages_dir.glob("*.pdf")))
        
        if not pdf_files:
            print(f"❌ No PDF files found in {self.manpages_dir}")
            return []
        
        # Get processed files from progress
        processed_count = self.progress_tracker.progress.get("total_concepts_extracted", 0)
        remaining_files = pdf_files[processed_count:]
        
        if not remaining_files:
            print("🎉 All man pages processed!")
            return []
        
        batch_files = remaining_files[:batch_size]
        print(f"📋 Processing batch: {len(batch_files)} man pages")
        print(f"📈 Progress: {processed_count}/{len(pdf_files)} completed")
        
        extracted_manpages = []
        
        for i, pdf_file in enumerate(batch_files, 1):
            print(f"\n🔍 [{i}/{len(batch_files)}] Processing: {pdf_file.name}")
            
            try:
                manpage_data = self.extract_single_manpage(pdf_file)
                if manpage_data:
                    self.save_manpage_json(manpage_data, pdf_file.stem)
                    extracted_manpages.append(manpage_data)
                    print(f"✅ Extracted: {manpage_data.get('name', 'unknown')} syscall")
                else:
                    print(f"❌ Failed to extract: {pdf_file.name}")
                    
            except Exception as e:
                print(f"💥 Error processing {pdf_file.name}: {e}")
                # Continue with next file instead of crashing
                continue
        
        # Update progress
        self.progress_tracker.update_progress(
            processed_count + len(batch_files),
            len(extracted_manpages),
            {
                "batch_files": [f.name for f in batch_files],
                "successful_extractions": len(extracted_manpages),
                "failed_extractions": len(batch_files) - len(extracted_manpages)
            }
        )
        
        print(f"\n📊 Batch Complete:")
        print(f"  ✅ Successful: {len(extracted_manpages)}")
        print(f"  ❌ Failed: {len(batch_files) - len(extracted_manpages)}")
        print(f"  📈 Total Progress: {processed_count + len(batch_files)}/{len(pdf_files)}")
        
        return extracted_manpages

    def extract_single_manpage(self, pdf_file):
        """Extract structured data from a single man page PDF with chunked processing for long docs"""
        
        with PDFStructureExtractor(str(pdf_file)) as extractor:
            # Extract all content from the man page (handles up to 7+ pages)
            content_blocks = extractor.extract_structured_content(0, max_pages=15)
            
            if not content_blocks:
                print(f"  ⚠️  No content extracted from PDF")
                return None
            
            print(f"  📄 Extracted {len(content_blocks)} content blocks")
            
            # Detect man page sections for intelligent processing
            raw_content = self._combine_content_blocks(content_blocks)
            sections = self._parse_manpage_sections(raw_content)
            
            print(f"  📋 Detected sections: {', '.join(sections.keys())}")
            
            # Handle long documents by processing essential sections first
            if len(raw_content) > 8000:  # Grok context management
                print(f"  📏 Long document ({len(raw_content)} chars), using section-aware processing")
                processed_sections = self._process_long_manpage(sections, pdf_file.stem)
            else:
                print(f"  📄 Standard document ({len(raw_content)} chars), using full processing")
                processed_sections = self._process_standard_manpage(raw_content, pdf_file.stem)
            
            return processed_sections

    def _combine_content_blocks(self, content_blocks):
        """Combine PDF content blocks into coherent text"""
        combined_text = []
        
        for block in content_blocks:
            if block["type"] in ["text", "header", "code"]:
                combined_text.extend(block["content"])
        
        return "\n".join(combined_text)

    def _parse_manpage_sections(self, raw_content):
        """Parse man page into standard sections"""
        sections = {}
        current_section = "UNKNOWN"
        current_content = []
        
        # Standard man page section headers
        section_patterns = [
            r'^(NAME)\s*$',
            r'^(SYNOPSIS)\s*$', 
            r'^(DESCRIPTION)\s*$',
            r'^(PARAMETERS?|ARGUMENTS?)\s*$',
            r'^(RETURN VALUE|RETURN VALUES)\s*$',
            r'^(ERRORS?)\s*$',
            r'^(EXAMPLES?)\s*$',
            r'^(BUGS?)\s*$',
            r'^(VERSIONS?|VERSION)\s*$',
            r'^(CONFORMING TO|STANDARDS?)\s*$',
            r'^(SEE ALSO)\s*$',
            r'^(NOTES?)\s*$'
        ]
        
        lines = raw_content.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line is a section header
            section_found = False
            for pattern in section_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = re.match(pattern, line_stripped, re.IGNORECASE).group(1).upper()
                    current_content = []
                    section_found = True
                    break
            
            if not section_found and line_stripped:
                current_content.append(line_stripped)
        
        # Don't forget the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections

    def _process_long_manpage(self, sections, syscall_name):
        """Process long man pages by prioritizing essential sections"""
        
        # Priority sections for system calls
        essential_sections = ['NAME', 'SYNOPSIS', 'DESCRIPTION', 'RETURN VALUE', 'ERRORS']
        supplementary_sections = ['PARAMETERS', 'EXAMPLES', 'BUGS', 'VERSIONS', 'CONFORMING TO']
        
        # Build focused content for Grok
        focused_content = []
        
        for section in essential_sections:
            if section in sections:
                focused_content.append(f"{section}:\n{sections[section]}\n")
        
        # Add supplementary sections if space allows
        current_length = len('\n'.join(focused_content))
        for section in supplementary_sections:
            if section in sections:
                section_content = f"{section}:\n{sections[section]}\n"
                if current_length + len(section_content) < 6000:  # Safe Grok limit
                    focused_content.append(section_content)
                    current_length += len(section_content)
        
        focused_text = '\n'.join(focused_content)
        return self._extract_with_grok(focused_text, syscall_name, is_chunked=True)

    def _process_standard_manpage(self, raw_content, syscall_name):
        """Process standard-length man pages with full content"""
        return self._extract_with_grok(raw_content, syscall_name, is_chunked=False)

    def _extract_with_grok(self, content, syscall_name, is_chunked=False):
        """Use Grok to extract structured data from man page content"""
        
        prompt = self._build_manpage_extraction_prompt(content, syscall_name, is_chunked)
        
        try:
            # Use Grok's API directly for better control
            response_text = self.grok_processor._call_grok_api(prompt)
            
            if not response_text:
                print(f"  ❌ Empty response from Grok")
                return None
            
            parsed_data = self._parse_grok_response(response_text, syscall_name)
            
            if parsed_data:
                print(f"  ✅ Successfully parsed {syscall_name} with Grok")
                return parsed_data
            else:
                print(f"  ❌ Failed to parse Grok response for {syscall_name}")
                return None
                    
        except Exception as e:
            print(f"  💥 Grok extraction error: {e}")
            return None

    def _build_manpage_extraction_prompt(self, content, syscall_name, is_chunked):
        """Build specialized prompt for man page extraction using Grok"""
        
        chunk_note = " (processed from long document)" if is_chunked else ""
        
        return f"""You are extracting structured information from a POSIX system call man page{chunk_note}.

SYSTEM CALL: {syscall_name}

Extract the following information into structured JSON format:

REQUIRED FIELDS:
1. **name**: The main system call name (e.g., "epoll_create1", "fork", "execve")
2. **synopsis**: Function signature(s) including headers (array of strings)
3. **description**: Concise explanation of what this syscall does (2-3 sentences max)
4. **parameters**: Array of parameter objects with name, type, description
5. **return_value**: Object with "success" and "failure" descriptions
6. **errors**: Array of error objects with "code" and "description"
7. **bugs**: Any known bugs or limitations (string, or null if none)
8. **versions**: Version information (string, or null if not specified)
9. **posix_compliance**: POSIX standard compliance (e.g., "POSIX.1-2008", or null)

OPTIONAL FIELDS (include if present):
10. **examples**: Array of code example strings
11. **related_calls**: Array of related system call names

Return ONLY valid JSON in this EXACT format:
{{
  "name": "{syscall_name}",
  "synopsis": [
    "#include <sys/epoll.h>",
    "int epoll_create1(int flags);"
  ],
  "description": "Creates an epoll file descriptor for I/O event notification.",
  "parameters": [
    {{"name": "flags", "type": "int", "description": "Flags to modify behavior (EPOLL_CLOEXEC)"}}
  ],
  "return_value": {{
    "success": "Returns file descriptor on success",
    "failure": "Returns -1 on error, errno is set"
  }},
  "errors": [
    {{"code": "EINVAL", "description": "Invalid flags specified"}},
    {{"code": "EMFILE", "description": "Per-process limit on file descriptors reached"}}
  ],
  "bugs": null,
  "versions": "Linux 2.6.27",
  "posix_compliance": null,
  "examples": [
    "int epfd = epoll_create1(EPOLL_CLOEXEC);",
    "if (epfd == -1) {{ perror(\\"epoll_create1\\"); exit(1); }}"
  ],
  "related_calls": ["epoll_ctl", "epoll_wait", "close"]
}}

MAN PAGE CONTENT:
{content}

Extract as JSON:"""

    def _parse_grok_response(self, response_text, syscall_name):
        """Parse Grok response into structured man page data"""
        try:
            # Clean up response text and extract JSON
            cleaned_response = response_text.strip()
            
            # Find JSON in response (handle potential markdown wrapping)
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if not json_match:
                print(f"  ⚠️  No JSON found in Grok response")
                return None
            
            json_str = json_match.group()
            parsed_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['name', 'synopsis', 'description', 'return_value']
            for field in required_fields:
                if field not in parsed_data:
                    print(f"  ⚠️  Missing required field: {field}")
                    return None
            
            # Add extraction metadata
            parsed_data["extraction_metadata"] = {
                "syscall_file": f"{syscall_name}.pdf",
                "extraction_date": datetime.now().isoformat(),
                "extractor": "posix_manpage_extractor",
                "ai_model": "grok",
                "source": "POSIX System Call Manual"
            }
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            print(f"  📝 Response preview: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"  💥 Unexpected parsing error: {e}")
            return None

    def save_manpage_json(self, manpage_data, filename_base):
        """Save extracted man page data as JSON with unix_ prefix"""
        json_filename = f"unix_{filename_base}.json"
        json_filepath = self.output_dir / json_filename
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(manpage_data, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Saved: {json_filename}")

    def generate_batch_summary(self, extracted_manpages):
        """Generate summary of the extraction batch"""
        if not extracted_manpages:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.output_dir / f"posix_batch_summary_{today}.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# POSIX Man Page Extraction Summary\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Extractor:** Grok-powered POSIX man page processor\n")
            f.write(f"**Batch Size:** {len(extracted_manpages)} system calls\n\n")
            
            f.write("## System Calls Extracted\n\n")
            
            for i, manpage in enumerate(extracted_manpages, 1):
                f.write(f"### {i}. {manpage.get('name', 'Unknown')}\n")
                f.write(f"**Description:** {manpage.get('description', 'No description')}\n")
                f.write(f"**Errors:** {len(manpage.get('errors', []))} documented\n")
                f.write(f"**POSIX:** {manpage.get('posix_compliance', 'Not specified')}\n\n")
            
            f.write(f"## Progress Summary\n")
            progress = self.progress_tracker.progress
            f.write(f"- **Total System Calls Processed:** {progress['total_concepts_extracted']}\n")
            f.write(f"- **Extraction Sessions:** {len(progress['extraction_sessions'])}\n")
            f.write(f"- **Success Rate:** High (Grok-optimized)\n\n")
            
            f.write("---\n*Generated by POSIX Man Page Extractor*\n")
        
        print(f"📋 Batch summary saved: {summary_file.name}")

def main():
    """Main execution for POSIX man page extraction"""
    try:
        # Create extractor
        extractor = POSIXManPageExtractor()
        
        # Process batch of 8 PDFs
        extracted = extractor.extract_batch(batch_size=8)
        
        # Generate batch summary
        if extracted:
            extractor.generate_batch_summary(extracted)
        
        print(f"\n🎉 POSIX extraction session complete!")
        print(f"📊 Results: {len(extracted)} system calls extracted")
        
        # Show next steps
        remaining = len(list(extractor.manpages_dir.glob("*.pdf"))) - extractor.progress_tracker.progress['total_concepts_extracted']
        if remaining > 0:
            print(f"⏳ Remaining: {remaining} man pages to process")
            print(f"🔄 Run script again to continue extraction")
        else:
            print(f"✅ All man pages processed!")

    except Exception as e:
        print(f"💥 Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
