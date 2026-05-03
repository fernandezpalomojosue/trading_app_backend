"""
AI Strategy Generation API Endpoints

Natural language → Strategy DSL via AI generation.
Features rate limiting at endpoint level.
"""

import uuid
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from app.application.dto.ai_strategy_dto import (
    StrategyGenerateRequest,
    StrategyGenerateResponse,
    StrategyGenerationError
)
from app.application.repositories.strategy_repository import StrategyRepository
from app.core.config import settings
from app.db.base import get_session
from app.domain.services.strategy_ai_service import StrategyAIService
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.infrastructure.external.ai_provider_factory import AIProviderFactory
from app.infrastructure.rate_limiter.ai_rate_limiter import AIRateLimiter
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.infrastructure.database.strategy_repository import SQLStrategyRepository

router = APIRouter()


def get_strategy_repository(
    db: Session = Depends(get_session)
) -> StrategyRepository:
    """Dependency to get strategy repository instance"""
    return SQLStrategyRepository(db)


def get_ai_rate_limiter() -> AIRateLimiter:
    """Dependency to get AI rate limiter instance"""
    return AIRateLimiter(
        max_requests=settings.AI_RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )


def get_strategy_use_cases(
    repository: StrategyRepository = Depends(get_strategy_repository)
) -> StrategyUseCases:
    """
    Dependency to get strategy use cases with AI service configured.
    
    Uses AIProviderFactory for extensible provider support.
    Available providers: openrouter, bedrock
    New providers can be added without modifying this code.
    """
    use_cases = StrategyUseCases(repository)
    
    # Configure AI service via factory (extensible)
    try:
        provider = AIProviderFactory.create()
        ai_service = StrategyAIService(
            provider=provider,
            max_retries=settings.AI_MAX_RETRIES
        )
        use_cases.set_ai_service(ai_service)
    except Exception as e:
        print(f"[AI_PROVIDER] Failed to configure AI service: {e}")
        print(f"[AI_PROVIDER] Available providers: {AIProviderFactory.list_providers()}")
    
    return use_cases


@router.post(
    "/generate",
    response_model=StrategyGenerateResponse,
    responses={
        422: {"model": StrategyGenerationError, "description": "Validation failed"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "AI service unavailable"}
    }
)
async def generate_strategy(
    request: StrategyGenerateRequest,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases),
    rate_limiter: AIRateLimiter = Depends(get_ai_rate_limiter)
):
    """
    Generate a trading strategy from natural language using AI.
    
    Features:
    - Rate limiting: 5 requests per minute per user
    - Retry logic: Up to 3 attempts with error feedback
    - Validation: All generated DSL passes through DSLValidator
    
    Args:
        request: Strategy generation request with natural language prompt
        
    Returns:
        StrategyGenerateResponse with generated DSL on success
        
    Raises:
        HTTPException 400: If AI service not configured
        HTTPException 422: If AI fails to generate valid DSL after retries
        HTTPException 429: If rate limit exceeded
    """
    print(f"[AI_ENDPOINT] Request from user={current_user.id}, prompt='{request.prompt[:50]}...'")
    
    # Rate limiting at ENDPOINT level (not inside service)
    remaining = await rate_limiter.check_rate_limit(current_user.id)
    print(f"[AI_ENDPOINT] Rate limit: remaining={remaining}")
    
    if not remaining:
        retry_after = rate_limiter.get_retry_after(current_user.id)
        print(f"[AI_ENDPOINT] Rate limit EXCEEDED for user={current_user.id}, retry_after={retry_after}s")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_type": "rate_limit",
                "message": f"Rate limit exceeded: {settings.AI_RATE_LIMIT_PER_MINUTE} requests per minute allowed",
                "retry_after_seconds": retry_after
            }
        )
    
    # Record request for rate limiting
    await rate_limiter.record_request(current_user.id)
    print(f"[AI_ENDPOINT] Rate limit recorded for user={current_user.id}")
    
    # Delegate to use cases (which delegates to AI service)
    print(f"[AI_ENDPOINT] Delegating to StrategyUseCases.generate_strategy_from_ai")
    result = await use_cases.generate_strategy_from_ai(
        user_id=current_user.id,
        prompt=request.prompt
    )
    
    # Handle error response
    if isinstance(result, StrategyGenerationError):
        print(f"[AI_ENDPOINT] FAILED: {result.error_type} - {result.message}")
        # Map error types to status codes
        status_code_map = {
            "rate_limit": status.HTTP_429_TOO_MANY_REQUESTS,
            "timeout": status.HTTP_504_GATEWAY_TIMEOUT,
            "invalid_json": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_failed": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "ai_error": status.HTTP_503_SERVICE_UNAVAILABLE
        }
        
        http_status = status_code_map.get(
            result.error_type,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        raise HTTPException(
            status_code=http_status,
            detail={
                "error_type": result.error_type,
                "message": result.message,
                "details": result.details
            }
        )
    
    # Return successful response
    print(f"[AI_ENDPOINT] SUCCESS: strategy='{result.name}', attempts={result.attempts_made}")
    return result


@router.get("/health")
async def ai_service_health():
    """Check AI service availability."""
    is_configured = bool(settings.OPENROUTER_API_KEY)
    
    return {
        "configured": is_configured,
        "provider": "openrouter" if is_configured else None,
        "model": settings.OPENROUTER_MODEL if is_configured else None,
        "max_retries": settings.AI_MAX_RETRIES,
        "timeout_seconds": settings.AI_TIMEOUT_SECONDS
    }
