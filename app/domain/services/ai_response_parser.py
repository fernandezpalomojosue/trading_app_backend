"""
AI Response Parser

Extracts JSON from AI responses with various formatting patterns.
Handles markdown code blocks, plain JSON, and common AI formatting issues.
"""

import json
import re
from typing import Dict, List, Optional, Tuple


class AIResponseParser:
    """
    Parse AI responses to extract valid JSON DSL definitions.
    
    Handles:
    - Plain JSON strings
    - Markdown code blocks (```json ... ```)
    - Unclosed code blocks
    - Multiple JSON objects in response
    """
    
    @staticmethod
    def parse(raw_response: str) -> Tuple[Optional[Dict], List[str]]:
        """
        Extract JSON from raw AI response.
        
        Args:
            raw_response: Raw string from AI provider
            
        Returns:
            Tuple of (parsed_json_dict, error_messages)
            - If successful: (dict, [])
            - If failed: (None, [error_message])
        """
        errors = []
        
        if not raw_response or not raw_response.strip():
            return None, ["Empty response from AI"]
        
        # Try direct JSON parse first
        try:
            return json.loads(raw_response.strip()), []
        except json.JSONDecodeError:
            pass
        
        # Extract from markdown code blocks
        extraction_strategies = [
            AIResponseParser._extract_json_block,
            AIResponseParser._extract_any_braces,
        ]
        
        for strategy in extraction_strategies:
            result, error = strategy(raw_response)
            if result is not None:
                return result, []
            if error:
                errors.append(error)
        
        # All strategies failed
        return None, errors if errors else ["Failed to extract valid JSON from AI response"]
    
    @staticmethod
    def _extract_json_block(text: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Extract JSON from markdown code blocks."""
        # Pattern for ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*\n?(.*?)\n?```',  # ```json ... ```
            r'```\s*\n?(.*?)\n?```',       # ``` ... ```
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    cleaned = match.strip()
                    if cleaned:
                        return json.loads(cleaned), None
                except json.JSONDecodeError:
                    continue
        
        return None, "No valid JSON found in code blocks"
    
    @staticmethod
    def _extract_any_braces(text: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Extract any JSON-like structure with braces."""
        # Find outermost JSON object
        # Look for balanced braces
        start = text.find('{')
        if start == -1:
            return None, "No opening brace found"
        
        # Find matching closing brace
        brace_count = 0
        end = start
        for i, char in enumerate(text[start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = start + i + 1
                    break
        
        if brace_count != 0:
            return None, "Unbalanced braces in response"
        
        json_str = text[start:end]
        try:
            return json.loads(json_str), None
        except json.JSONDecodeError as e:
            return None, f"JSON syntax error: {str(e)}"
    
    @staticmethod
    def _clean_response(text: str) -> str:
        """Clean common AI response artifacts."""
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove trailing commas before closing braces/brackets
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        return text
