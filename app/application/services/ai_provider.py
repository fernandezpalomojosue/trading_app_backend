"""
AI Provider Protocol

Defines the interface for AI providers, enabling true provider-agnostic design.
Implementations: OpenRouterProvider, AnthropicProvider, LocalModelProvider, etc.
"""

from typing import Protocol


class AIProvider(Protocol):
    """
    Protocol for AI providers - enables true swapability.
    
    Usage:
        provider: AIProvider = OpenRouterProvider(...)
        response = await provider.generate("Generate a buy strategy...")
    
    Implementations must handle:
    - HTTP timeouts
    - Authentication
    - Error propagation (raise on failure)
    """
    
    async def generate(self, prompt: str) -> str:
        """
        Send prompt to AI and return raw response string.
        
        Args:
            prompt: The complete prompt to send to the AI model
            
        Returns:
            Raw response string from the AI (may contain markdown, JSON, etc.)
            
        Raises:
            TimeoutError: If request exceeds configured timeout
            AIProviderError: For API errors, rate limits, auth failures
        """
        ...


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
