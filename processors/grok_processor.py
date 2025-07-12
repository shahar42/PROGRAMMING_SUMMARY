#!/usr/bin/env python3
"""
Grok Atomic Processor Module
Extracted from the Content-Intelligent C Concept Extraction Engine

Processes raw content into atomic training data using X.AI's Grok AI.
"""

import json
import re
from datetime import datetime
import requests


class GrokAtomicProcessor:
    """Processes raw content into atomic training data using Grok"""
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-beta"
        
        try:
            # Test the API key with a simple request
            self._test_connection()
            print(f"🤖 Grok AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Grok: {e}")
            raise
    
    def _test_connection(self):
        """Test API connection"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        test_payload = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "model": self.model,
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"API test failed: {response.status_code} - {response.text}")
    
    def process_concept(self, concept_data):
        """Transform raw concept into atomic training format"""
        
        prompt = self._build_atomic_extraction_prompt(concept_data["raw_content"])
        
        try:
            response_text = self._call_grok_api(prompt)
            
            # Parse Grok's response into structured format
            parsed_concept = self._parse_grok_response(response_text)
            
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
    
    def _call_grok_api(self, prompt):
        """Make API call to Grok"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "max_tokens": 2000,
            "temperature": 0.1,  # Low temperature for consistent structured output
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Grok API call failed: {response.status_code} - {response.text}")
        
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    
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
    
    def _parse_grok_response(self, response_text):
        """Parse Grok's JSON response"""
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
