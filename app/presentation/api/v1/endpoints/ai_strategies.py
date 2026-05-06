"""
AI Strategy Generation API Endpoints

Natural language → Strategy DSL via AI generation.
Features rate limiting at endpoint level.
"""

import uuid
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from app.core.logging_config import get_logger, get_request_logger

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
    
    Raises HTTPException 503 if AI service cannot be configured.
    """
    use_cases = StrategyUseCases(repository)
    
    logger = get_logger(__name__)
    
    # Configure AI service via factory (extensible)
    try:
        logger.info(
            "AI provider configuration started",
            component="ai_strategies",
            provider=settings.AI_PROVIDER
        )
        provider = AIProviderFactory.create()
        ai_service = StrategyAIService(
            provider=provider,
            max_retries=settings.AI_MAX_RETRIES
        )
        use_cases.set_ai_service(ai_service)
        logger.info(
            "AI service configured successfully",
            component="ai_strategies",
            provider=settings.AI_PROVIDER,
            max_retries=settings.AI_MAX_RETRIES
        )
    except ValueError as e:
        # Provider not registered or unknown
        available = AIProviderFactory.list_providers()
        logger.error(
            "AI provider configuration failed - unknown provider",
            component="ai_strategies",
            provider=settings.AI_PROVIDER,
            available_providers=available,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_type": "ai_configuration_error",
                "message": f"AI provider '{settings.AI_PROVIDER}' not available",
                "details": {
                    "provider": settings.AI_PROVIDER,
                    "available_providers": available,
                    "error": str(e)
                }
            }
        )
    except Exception as e:
        # Other configuration errors (missing API keys, etc.)
        logger.error(
            "AI service configuration failed - general error",
            component="ai_strategies",
            provider=settings.AI_PROVIDER,
            error_type=type(e).__name__,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_type": "ai_configuration_error",
                "message": "AI service configuration failed",
                "details": {
                    "provider": settings.AI_PROVIDER,
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            }
        )
    
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
    request_logger = get_request_logger()
    request_id = str(uuid.uuid4())
    request_logger.set_request_context(
        request_id=request_id,
        user_id=str(current_user.id),
        endpoint="ai_strategies_generate"
    )
    
    request_logger.info(
        "AI strategy generation request received",
        component="ai_strategies",
        user_id=current_user.id,
        prompt_preview=request.prompt[:50],
        prompt_length=len(request.prompt)
    )
    
    # Rate limiting at ENDPOINT level (not inside service)
    remaining = await rate_limiter.check_rate_limit(current_user.id)
    
    request_logger.info(
        "Rate limit check completed",
        component="ai_strategies",
        remaining_requests=remaining
    )
    
    if not remaining:
        retry_after = rate_limiter.get_retry_after(current_user.id)
        request_logger.warning(
            "Rate limit exceeded",
            component="ai_strategies",
            user_id=current_user.id,
            retry_after_seconds=retry_after,
            limit_per_minute=settings.AI_RATE_LIMIT_PER_MINUTE
        )
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
    
    request_logger.info(
        "Rate limit request recorded",
        component="ai_strategies",
        user_id=current_user.id
    )
    
    # Delegate to use cases (which delegates to AI service)
    request_logger.info(
        "Delegating to strategy generation use case",
        component="ai_strategies",
        user_id=current_user.id
    )
    
    result = await use_cases.generate_strategy_from_ai(
        user_id=current_user.id,
        prompt=request.prompt
    )
    
    # Handle error response
    if isinstance(result, StrategyGenerationError):
        request_logger.error(
            "Strategy generation failed",
            component="ai_strategies",
            user_id=current_user.id,
            error_type=result.error_type,
            error_message=result.message
        )
        # Map error types to status codes
        status_code_map = {
            "rate_limit": status.HTTP_429_TOO_MANY_REQUESTS,
            "ai_error": status.HTTP_503_SERVICE_UNAVAILABLE,
            "validation_error": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "unknown_error": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        status_code = status_code_map.get(result.error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error_type": result.error_type,
                "message": result.message,
                "details": result.details if hasattr(result, 'details') else {}
            }
        )
    
    # Return successful response
    request_logger.info(
        "Strategy generation completed successfully",
        component="ai_strategies",
        user_id=current_user.id,
        strategy_name=result.name,
        attempts_made=result.attempts_made,
        strategy_saved=result.saved
    )
    
    # Clear request context
    request_logger.clear_context()
    
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
