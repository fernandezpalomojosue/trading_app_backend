"""
OpenRouter AI Provider Implementation

OpenAI-compatible provider for OpenRouter API.
"""

from openai import AsyncOpenAI, APITimeoutError

from app.application.services.ai_provider import AIProvider, AIProviderError
from app.application.dto.ai_prompts_dto import AIPromptsDTO
from app.core.logging_config import get_logger


class BedrockProvider(AIProvider):
    """
    AWS Bedrock implementation using OpenAI-compatible API.
    
    Implements AIProvider protocol for strategy generation.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://bedrock-mantle.us-east-1.api.aws/v1",
        model: str = "openai.gpt-oss-120b",
        timeout: int = 30,
        max_tokens: int = 1200
    ):
        self.logger = get_logger(__name__)
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
        self.logger.info(
            "Bedrock API request initiated",
            component="bedrock_provider",
            model=self.model,
            max_tokens=self.max_tokens,
            prompt_length=len(prompt)
        )
        
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
            self.logger.info(
                "Bedrock API response received",
                component="bedrock_provider",
                response_length=len(content),
                response_preview=content[:200]
            )
            
            return content
            
        except APITimeoutError:
            self.logger.error(
                "Bedrock API request timeout",
                component="bedrock_provider",
                timeout_seconds=self.timeout
            )
            raise TimeoutError(f"AI request timed out after {self.timeout}s")
        except Exception as e:
            self.logger.error(
                "Bedrock API request failed",
                component="bedrock_provider",
                error_type=type(e).__name__,
                error_message=str(e),
                model=self.model
            )
            raise AIProviderError(
                message=f"Bedrock API error: {str(e)}",
                details={"error_type": type(e).__name__, "model": self.model}
            )
