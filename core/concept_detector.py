#!/usr/bin/env python3
"""
Concept Boundary Detector Core Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Detects natural atomic concept boundaries in structured content.
"""


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
