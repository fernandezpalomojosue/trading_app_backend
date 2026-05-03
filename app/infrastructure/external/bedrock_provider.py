"""
Amazon Bedrock AI Provider Implementation

AWS Bedrock provider for strategy generation using OpenAI-compatible API.
"""

from openai import AsyncOpenAI, APITimeoutError

from app.application.services.ai_provider import AIProvider, AIProviderError


class BedrockProvider(AIProvider):
    """
    Amazon Bedrock implementation using OpenAI-compatible API.
    
    Implements AIProvider protocol for strategy generation.
    Uses the OpenAI SDK to connect to Bedrock's OpenAI-compatible endpoint.
    """
    
    def __init__(
        self,
        base_url: str = "https://bedrock-mantle.us-east-1.api.aws/v1",
        model: str = "openai.gpt-oss-120b",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        timeout: int = 30,
        max_tokens: int = 1200
    ):
        """
        Initialize Bedrock provider using OpenAI-compatible API.
        
        Args:
            base_url: Bedrock runtime endpoint with model path
            model: Model identifier (e.g., openai.gpt-oss-120b, anthropic.claude-3-5-sonnet)
            aws_access_key_id: AWS access key for authentication
            aws_secret_access_key: AWS secret key for authentication
            aws_session_token: AWS session token (optional, for temporary credentials)
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.system_prompt = self._build_system_prompt()
        
        # Build API key from AWS credentials if provided
        # Bedrock OpenAI-compatible API uses AWS SigV4 authentication
        api_key = None
        if aws_access_key_id and aws_secret_access_key:
            # Format: access_key:secret_key or with session token
            if aws_session_token:
                api_key = f"{aws_access_key_id}:{aws_secret_access_key}:{aws_session_token}"
            else:
                api_key = f"{aws_access_key_id}:{aws_secret_access_key}"
        
        self.client = AsyncOpenAI()
    
    async def generate(self, prompt: str) -> str:
        """
        Send prompt to Bedrock and return response.
        
        Args:
            prompt: User prompt with strategy description
            
        Returns:
            Raw AI response string
            
        Raises:
            TimeoutError: If request times out
            AIProviderError: For API errors
        """
        print(f"[BEDROCK] Request: model={self.model}, max_tokens={self.max_tokens}, prompt_len={len(prompt)}")
        
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more deterministic JSON
            )
            
            content = response.output_text
            print(f"[BEDROCK] Response: {len(content)} chars, preview={content[:200]}...")
            
            return content
            
        except APITimeoutError:
            print(f"[BEDROCK] TIMEOUT after {self.timeout}s")
            raise TimeoutError(f"Bedrock request timed out after {self.timeout}s")
        except Exception as e:
            print(f"[BEDROCK] ERROR: {type(e).__name__}: {str(e)}")
            raise AIProviderError(
                message=f"Bedrock API error: {str(e)}",
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
