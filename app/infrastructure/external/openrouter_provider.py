"""
OpenRouter AI Provider Implementation

OpenAI-compatible provider for OpenRouter API.
"""

from openai import AsyncOpenAI, APITimeoutError

from app.application.services.ai_provider import AIProvider, AIProviderError


class OpenRouterProvider:
    """
    OpenRouter implementation using OpenAI-compatible API.
    
    Implements AIProvider protocol for strategy generation.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openrouter/free",
        timeout: int = 30,
        max_tokens: int = 1200
    ):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.system_prompt = self._build_system_prompt()
    
    async def generate(self, prompt: str) -> str:
        """
        Send prompt to OpenRouter and return response.
        
        Args:
            prompt: User prompt with strategy description
            
        Returns:
            Raw AI response string
            
        Raises:
            TimeoutError: If request times out
            AIProviderError: For API errors
        """
        print(f"[OPENROUTER] Request: model={self.model}, max_tokens={self.max_tokens}, prompt_len={len(prompt)}")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more deterministic JSON
            )
            
            content = response.choices[0].message.content
            print(f"[OPENROUTER] Response: {len(content)} chars, preview={content[:200]}...")
            
            return content
            
        except APITimeoutError:
            print(f"[OPENROUTER] TIMEOUT after {self.timeout}s")
            raise TimeoutError(f"AI request timed out after {self.timeout}s")
        except Exception as e:
            print(f"[OPENROUTER] ERROR: {type(e).__name__}: {str(e)}")
            raise AIProviderError(
                message=f"OpenRouter API error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def _build_system_prompt(self) -> str:
        """Build strict system prompt for JSON-only output."""
        return """You are an expert trading strategy designer. Convert natural language descriptions into valid JSON DSL definitions.

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
- indicator: {"type": "indicator", "name": "RSI|SMA|EMA|MACD", "params": {}, "offset": 0}
- constant: {"type": "constant", "value": 30}

EXAMPLE 1 - Single condition:
{"name": "RSI Oversold", "description": "Buy when RSI < 30", "action": "buy", "dsl_definition": {"version": 1, "root": {"type": "condition", "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}}, "operator": "<", "right": {"type": "constant", "value": 30}}}}

EXAMPLE 2 - AND with two conditions:
{"name": "RSI and EMA", "description": "Buy when RSI < 30 AND price > EMA20", "action": "buy", "dsl_definition": {"version": 1, "root": {"type": "AND", "children": [{"type": "condition", "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}}, "operator": "<", "right": {"type": "constant", "value": 30}}, {"type": "condition", "left": {"type": "price", "field": "close"}, "operator": ">", "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}}]} }}

COMMON MISTAKES TO AVOID:
- Use "children" array for AND/OR, NOT "conditions"
- Use "child" object for NOT, NOT "children"
- "condition" is the type for leaf conditions, NOT "indicator" or "CROSS"
- Indicators go inside expressions with type "indicator", NOT as node types

Actions: buy, sell, hold
Max tree depth: 10 levels

Any deviation from these rules causes immediate rejection."""


# Type alias for protocol compatibility
OpenRouterProvider: AIProvider = OpenRouterProvider
