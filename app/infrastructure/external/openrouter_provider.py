"""
OpenRouter AI Provider Implementation

OpenAI-compatible provider for OpenRouter API.
"""

import logging
from openai import AsyncOpenAI, APITimeoutError

from app.application.services.ai_provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


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
        timeout: int = 15,
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
        logger.info(f"Sending request to OpenRouter with model={self.model}, max_tokens={self.max_tokens}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
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
            logger.info(f"OpenRouter response received: {len(content)} chars")
            logger.debug(f"Response content preview: {content[:200]}...")
            
            return content
            
        except APITimeoutError:
            logger.error(f"OpenRouter request timed out after {self.timeout}s")
            raise TimeoutError(f"AI request timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"OpenRouter API error: {type(e).__name__}: {str(e)}")
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

VALID VALUES:
- Indicators: RSI, SMA, EMA, MACD
- Operators: <, <=, >, >=, ==, !=, cross_above, cross_below
- Actions: buy, sell, hold
- Logical nodes: AND, OR, NOT (wrap all conditions)
- Max tree depth: 10 levels

Any deviation from these rules causes immediate rejection."""


# Type alias for protocol compatibility
OpenRouterProvider: AIProvider = OpenRouterProvider
