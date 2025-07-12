#!/usr/bin/env python3
"""
PDF Structure Extractor Core Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Intelligently extracts and classifies content from PDF documents.
"""

import re
import pdfplumber


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
