"""
Unit tests for AI Response Parser

Tests JSON extraction from various AI response formats.
"""

import json
import pytest

from app.domain.services.ai_response_parser import AIResponseParser


class TestAIResponseParser:
    """Test AI response parsing with various formats."""
    
    def test_parse_plain_json(self):
        """Parse valid JSON string directly."""
        raw = '{"name": "Test", "action": "buy"}'
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"name": "Test", "action": "buy"}
        assert errors == []
    
    def test_parse_json_with_whitespace(self):
        """Parse JSON with leading/trailing whitespace."""
        raw = '  \n  {"name": "Test", "action": "buy"}  \n  '
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"name": "Test", "action": "buy"}
        assert errors == []
    
    def test_parse_json_code_block(self):
        """Extract JSON from markdown ```json code block."""
        raw = '''
        Here is the strategy:
        
        ```json
        {
          "name": "RSI Strategy",
          "action": "buy"
        }
        ```
        
        Hope this helps!
        '''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"name": "RSI Strategy", "action": "buy"}
        assert errors == []
    
    def test_parse_plain_code_block(self):
        """Extract JSON from markdown ``` code block without language."""
        raw = '''
        ```
        {"name": "Simple", "action": "sell"}
        ```
        '''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"name": "Simple", "action": "sell"}
        assert errors == []
    
    def test_parse_multiple_code_blocks(self):
        """Use first valid JSON when multiple code blocks present."""
        raw = '''
        ```json
        {"name": "First", "action": "buy"}
        ```
        
        ```json
        {"name": "Second", "action": "sell"}
        ```
        '''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"name": "First", "action": "buy"}
        assert errors == []
    
    def test_parse_invalid_json(self):
        """Return error for invalid JSON."""
        raw = '{"name": "Test", "action": "buy",}'  # Trailing comma
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result is None
        assert len(errors) > 0
    
    def test_parse_empty_response(self):
        """Return error for empty response."""
        raw = ''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result is None
        assert errors == ["Empty response from AI"]
    
    def test_parse_no_json(self):
        """Return error when no JSON found."""
        raw = 'This is just plain text with no JSON anywhere'
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result is None
        assert len(errors) > 0
    
    def test_parse_json_with_line_breaks(self):
        """Parse multi-line JSON."""
        raw = '''{
            "name": "Multi-line",
            "action": "buy",
            "dsl_definition": {
                "version": 1,
                "root": {"type": "condition"}
            }
        }'''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result["name"] == "Multi-line"
        assert errors == []


class TestAIResponseParserEdgeCases:
    """Edge case tests for response parsing."""
    
    def test_parse_nested_braces(self):
        """Handle nested JSON objects."""
        raw = '''
        Some text before
        {"outer": {"inner": {"deep": "value"}}}
        Some text after
        '''
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result == {"outer": {"inner": {"deep": "value"}}}
        assert errors == []
    
    def test_parse_json_with_arrays(self):
        """Parse JSON containing arrays."""
        raw = '{"items": [1, 2, 3], "name": "Array Test"}'
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result["items"] == [1, 2, 3]
        assert errors == []
    
    def test_parse_unclosed_code_block(self):
        """Handle unclosed markdown code block."""
        raw = '```json\n{"name": "Unclosed"}'
        
        result, errors = AIResponseParser.parse(raw)
        
        # Should extract from braces fallback
        assert result is not None
    
    def test_parse_partial_json(self):
        """Handle partial/incomplete JSON."""
        raw = '{"name": "Partial"'  # Missing closing brace
        
        result, errors = AIResponseParser.parse(raw)
        
        assert result is None
        assert len(errors) > 0
