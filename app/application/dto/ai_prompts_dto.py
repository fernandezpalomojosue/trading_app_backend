"""
AI Prompts DTO

Reusable prompt templates for AI strategy generation.
Centralized prompts to ensure consistency across providers.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class AIPromptsDTO:
    """
    Data Transfer Object for AI prompts.
    
    Contains system prompts and user prompt templates
    for strategy generation across all AI providers.
    """
    
    # DSL Schema for strategy generation
    dsl_schema: str = field(default="""{
  "version": 1,
  "root": {
    "oneOf": [
      {
        "type": "AND",
        "children": [{"type": "condition"}]
      },
      {
        "type": "OR", 
        "children": [{"type": "condition"}]
      },
      {
        "type": "NOT",
        "child": {"type": "condition"}
      },
      {
        "type": "condition",
        "description": "Single condition (for simple strategies)",
        "left": {"type": "indicator|price|constant"},
        "operator": "<|<=|>|>=|==|!=|cross_above|cross_below",
        "right": {"type": "indicator|price|constant"}
      }
    ]
  },
  "expression_types": {
    "constant": {"type": "number", "example": {"type": "constant", "value": 30}},
    "price": {
      "type": "price field with optional historical offset",
      "example": {"type": "price", "field": "close", "offset": 0},
      "fields": ["open", "high", "low", "close", "volume"],
      "offset": "0=current, 1=previous candle, 2=two candles ago, etc."
    },
    "indicator": {
      "type": "technical indicator with optional historical offset",
      "example": {"type": "indicator", "name": "RSI", "params": {"period": 14}, "offset": 0},
      "offset": "0=current, -1=previous candle's value, -2=two candles ago, etc."
    }
  }
}""")
    
    # System prompt for strategy DSL generation
    system_prompt: str = """You are an expert trading strategy designer. Convert natural language descriptions into valid JSON DSL definitions.

CRITICAL RULES:
- Output ONLY valid JSON, no markdown, no code blocks, no explanations
- If output is not valid JSON, it will be REJECTED
- Do not include comments, trailing commas, or any non-JSON content
- All required fields MUST be present: name, description, action, dsl_definition
- dsl_definition MUST contain: version (number), root (object)

VALID NODE TYPES AND EXACT FIELD NAMES:
- Condition node: {"type": "condition", "left": {...}, "operator": "<|<=|>|>=|==|!=|cross_above|cross_below", "right": {...}}
- AND node: {"type": "AND", "children": [{...}, {...}]}  
- OR node: {"type": "OR", "children": [{...}, {...}]}
- NOT node: {"type": "NOT", "child": {...}}

EXPRESSION TYPES:
- price: {"type": "price", "field": "close|open|high|low|volume", "offset": 0}
- indicator: {"type": "indicator", "name": "RSI|SMA|EMA|MACD|price_change|price_percentage_change", "params": {}, "offset": 0}
- constant: {"type": "constant", "value": 30}

EXAMPLE 1 - Single condition:
{"name": "RSI Oversold", "description": "Buy when RSI < 30", "action": "buy", "dsl_definition": {"version": 1, "root": {"type": "condition", "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}}, "operator": "<", "right": {"type": "constant", "value": 30}}}}

EXAMPLE 2 - AND with two conditions:
{"name": "RSI and EMA", "description": "Buy when RSI < 30 AND price > EMA20", "action": "buy", "dsl_definition": {"version": 1, "root": {"type": "AND", "children": [{"type": "condition", "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}}, "operator": "<", "right": {"type": "constant", "value": 30}}, {"type": "condition", "left": {"type": "price", "field": "close"}, "operator": ">", "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}}]} }}

EXAMPLE 3 - Price change indicator:
{"name": "Price Rising", "description": "Buy when price increased from previous candle", "action": "buy", "dsl_definition": {"version": 1, "root": {"type": "condition", "left": {"type": "indicator", "name": "price_change", "params": {"period": 1}}, "operator": ">", "right": {"type": "constant", "value": 0}}}}

COMMON MISTAKES TO AVOID:
- Use "children" array for AND/OR, NOT "conditions"
- Use "child" object for NOT, NOT "children"
- "condition" is the type for leaf conditions, NOT "indicator" or "CROSS"
- Indicators go inside expressions with type "indicator", NOT as node types"""

    # System prompt for prompt validation
    def get_validation_system_prompt() -> str:
        """Get validation system prompt dynamically."""
        return """You are a trading strategy prompt validator.

Your ONLY job is to determine if a prompt can safely become executable DSL.

SUPPORTED INDICATORS: RSI, EMA, SMA, MACD
SUPPORTED OPERATORS: <, <=, >, >=, ==, !=, cross_above, cross_below
SUPPORTED ACTIONS: buy, sell, hold

UNSUPPORTED: news sentiment, social sentiment, discretionary trading, psychology-based trading, fundamental analysis, chart patterns

Return ONLY this JSON format:
{"status": "VALID"} or {"status": "INVALID", "reason": "specific reason"}

Do not explain. Do not suggest improvements. Do not ask questions. Only VALID or INVALID.

Actions: buy, sell, hold
Max tree depth: 10 levels

Any deviation from these rules causes immediate rejection."""

    def build_generation_prompt(self, user_prompt: str) -> str:
        """Build initial generation prompt with DSL schema."""
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
- Action is at strategy level, NOT inside dsl_definition"""
    
    def build_retry_prompt(self, user_prompt: str, errors: list, previous_response: str = "") -> str:
        """Build retry prompt with error feedback."""
        error_text = "\n".join(f"- {e}" for e in errors)
        return f"""Previous attempt was INVALID. Fix these errors and regenerate:

Validation Errors:
{error_text}

Original Description: {user_prompt}

Previous Response (failed):
{previous_response[:500] if previous_response else "N/A"}

DSL Schema:
{self.dsl_schema}

⚠️ OUTPUT ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS, NO EXPLANATIONS"""
    
    @classmethod
    def default(cls) -> "AIPromptsDTO":
        """Get default prompts instance."""
        return cls()
