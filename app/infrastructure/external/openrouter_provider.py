"""
OpenRouter AI Provider Implementation

OpenAI-compatible provider for OpenRouter API.
"""

from openai import AsyncOpenAI, APITimeoutError

from app.application.services.ai_provider import AIProvider, AIProviderError
from app.application.dto.ai_prompts_dto import AIPromptsDTO


class OpenRouterProvider(AIProvider):
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
        self.prompts = AIPromptsDTO.default()
    
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
                    {"role": "system", "content": self.prompts.system_prompt},
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
    
