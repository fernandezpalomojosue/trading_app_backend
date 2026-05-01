"""
AI Strategy Generation API Endpoints

Natural language → Strategy DSL via AI generation.
Features rate limiting at endpoint level.
"""

import uuid
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.infrastructure.external.openrouter_provider import OpenRouterProvider
from app.infrastructure.rate_limiter.ai_rate_limiter import AIRateLimiter
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.infrastructure.database.strategy_repository import SQLStrategyRepository

router = APIRouter(prefix="/ai-strategies", tags=["ai-strategies"])


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
    
    Only configures AI service if OPENROUTER_API_KEY is set.
    """
    use_cases = StrategyUseCases(repository)
    
    # Configure AI service if API key available
    if settings.OPENROUTER_API_KEY:
        provider = OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.OPENROUTER_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS
        )
        ai_service = StrategyAIService(
            provider=provider,
            max_retries=settings.AI_MAX_RETRIES
        )
        use_cases.set_ai_service(ai_service)
    
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
    # Rate limiting at ENDPOINT level (not inside service)
    if not await rate_limiter.check_rate_limit(current_user.id):
        retry_after = rate_limiter.get_retry_after(current_user.id)
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
    
    # Delegate to use cases (which delegates to AI service)
    result = await use_cases.generate_strategy_from_ai(
        user_id=current_user.id,
        prompt=request.prompt
    )
    
    # Handle error response
    if isinstance(result, StrategyGenerationError):
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
