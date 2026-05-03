"""
AI Provider Factory

Extensible factory for creating AI providers based on configuration.
New providers can be registered without modifying existing code.
"""

from typing import Dict, Type, Callable, Any
from app.application.services.ai_provider import AIProvider
from app.core.config import settings


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    
    Supports extensible provider registration.
    New providers register themselves - no factory modification needed.
    """
    
    _providers: Dict[str, Callable[[], AIProvider]] = {}
    
    @classmethod
    def register(cls, name: str, factory_func: Callable[[], AIProvider]) -> None:
        """
        Register a provider factory function.
        
        Args:
            name: Provider identifier (e.g., "openrouter", "bedrock")
            factory_func: Function that creates and returns provider instance
        """
        cls._providers[name] = factory_func
        print(f"[AI_FACTORY] Registered provider: {name}")
    
    @classmethod
    def create(cls, provider_name: str = None) -> AIProvider:
        """
        Create provider instance by name.
        
        Args:
            provider_name: Provider to create (defaults to settings.AI_PROVIDER)
            
        Returns:
            Configured AIProvider instance
            
        Raises:
            ValueError: If provider not registered
        """
        name = provider_name or settings.AI_PROVIDER
        
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(
                f"Unknown AI provider: '{name}'. "
                f"Available providers: {available}"
            )
        
        print(f"[AI_FACTORY] Creating provider: {name}")
        return cls._providers[name]()
    
    @classmethod
    def list_providers(cls) -> list:
        """Return list of registered provider names."""
        return list(cls._providers.keys())


def register_openrouter() -> None:
    """Register OpenRouter provider factory."""
    from app.infrastructure.external.openrouter_provider import OpenRouterProvider
    
    def factory():
        return OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY or "",
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.OPENROUTER_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS
        )
    
    AIProviderFactory.register("openrouter", factory)


def register_bedrock() -> None:
    """Register Bedrock provider factory."""
    from app.infrastructure.external.bedrock_provider import BedrockProvider
    
    def factory():
        return BedrockProvider(
            base_url=settings.BEDROCK_BASE_URL,
            model=settings.BEDROCK_MODEL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS
        )
    
    AIProviderFactory.register("bedrock", factory)


# Auto-register built-in providers on module import
register_openrouter()
register_bedrock()
