"""
AI Prompt Templates for Strategy Generation

Jinja2-based prompt construction for:
- Initial strategy generation
- Retry with validation error feedback
"""

import json
from typing import Any, Dict, List

from app.domain.services.strategy_registry import StrategyRegistry


class StrategyGenerationPrompts:
    """
    Build prompts for AI strategy generation.
    
    Uses template strings (not Jinja2 dependency) for simplicity.
    """
    
    def __init__(self):
        self.dsl_schema = self._build_dsl_schema()
    
    def build_generation_prompt(self, user_prompt: str) -> str:
        """
        Build initial generation prompt with DSL schema.
        
        Args:
            user_prompt: User's natural language strategy description
            
        Returns:
            Complete prompt for AI
        """
        return f"""Convert this trading strategy description into a COMPLETE strategy object:

User Description: {user_prompt}

DSL Schema (for dsl_definition field):
{self.dsl_schema}

REQUIRED OUTPUT FORMAT:
{{
  "name": "Strategy name (max 50 chars)",
  "description": "Clear description (max 200 chars)",
  "action": "buy|sell|hold",
  "dsl_definition": {{
    "version": 1,
    "root": {{
      "type": "AND|OR|NOT|condition",
      // AST nodes per schema above
    }}
  }}
}}

⚠️ CRITICAL:
- Response must be VALID JSON (verified by json.loads)
- Include ALL 4 top-level fields
- dsl_definition contains only version and root (NOT action)
- Root can be: single condition, OR logical nodes (AND/OR/NOT) wrapping conditions
- Use logical nodes ONLY when combining multiple conditions
- Action is at strategy level, NOT inside dsl_definition

Valid indicators: {', '.join(StrategyRegistry.get_all_indicators())}
Valid operators: {', '.join(StrategyRegistry.get_all_operators())}"""
    
    def build_retry_prompt(
        self,
        user_prompt: str,
        previous_response: str,
        errors: List[str]
    ) -> str:
        """
        Build retry prompt with validation error feedback.
        
        Args:
            user_prompt: Original user request
            previous_response: The AI's previous (invalid) response
            errors: List of validation errors to fix
            
        Returns:
            Retry prompt with error context
        """
        errors_str = '\n'.join(f'- {error}' for error in errors)
        
        return f"""The previous generation FAILED validation. Fix ALL errors below.

Original Request: {user_prompt}

Your Previous Response:
{previous_response}

VALIDATION ERRORS (MUST FIX):
{errors_str}

REQUIRED OUTPUT FORMAT:
{{
  "name": "Strategy name (max 50 chars)",
  "description": "Clear description (max 200 chars)",
  "action": "buy|sell|hold",
  "dsl_definition": {{
    "version": 1,
    "root": {{ /* valid AST nodes */ }}
  }}
}}

CORRECTED OUTPUT (valid JSON only, no markdown, no explanations):"""
    
    def _build_dsl_schema(self) -> str:
        """Build DSL schema documentation for prompts."""
        schema = {
            "version": 1,
            "root": {
                "anyOf": [
                    {
                        "type": "condition",
                        "description": "Single condition (for simple strategies)",
                        "left": {"type": "indicator|price|constant"},
                        "operator": "<|<=|>|>=|==|!=|cross_above|cross_below",
                        "right": {"type": "indicator|price|constant"}
                    },
                    {
                        "type": "AND",
                        "description": "Logical AND (requires 2+ conditions)",
                        "children": [{"type": "condition"}]
                    },
                    {
                        "type": "OR",
                        "description": "Logical OR (requires 2+ conditions)",
                        "children": [{"type": "condition"}]
                    },
                    {
                        "type": "NOT",
                        "description": "Logical NOT (inverts one condition)",
                        "child": {"type": "condition"}
                    }
                ]
            }
        }
        return json.dumps(schema, indent=2)
