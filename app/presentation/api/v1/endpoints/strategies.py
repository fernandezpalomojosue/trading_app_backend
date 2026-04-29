# app/presentation/api/v1/endpoints/strategies.py
"""
Strategy API Endpoints

CRUD operations for trading strategies with DSL validation.
Requires authentication.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.db.base import get_session
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.application.repositories.strategy_repository import StrategyRepository
from app.application.dto.strategy_dto import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyListResponse,
    StrategyValidationResponse
)
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.infrastructure.database.strategy_repository import SQLStrategyRepository

router = APIRouter(prefix="/strategies", tags=["strategies"])


def get_strategy_repository(
    db: Session = Depends(get_session)
) -> StrategyRepository:
    """Dependency to get strategy repository instance"""
    return SQLStrategyRepository(db)


def get_strategy_use_cases(
    repository: StrategyRepository = Depends(get_strategy_repository)
) -> StrategyUseCases:
    """Dependency to get strategy use cases"""
    return StrategyUseCases(repository)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: StrategyCreateRequest,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """
    Create a new trading strategy.
    
    DSL definition is validated before creation.
    Returns 422 if DSL validation fails.
    """
    try:
        return await use_cases.create_strategy(
            user_id=current_user.id,
            request=request
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    active_only: bool = Query(False, description="Filter to active strategies only"),
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """List all strategies for the current user"""
    return await use_cases.list_strategies(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: uuid.UUID,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """Get a specific strategy by ID"""
    try:
        return await use_cases.get_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: uuid.UUID,
    request: StrategyUpdateRequest,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """
    Update an existing strategy.
    
    Only provided fields are updated.
    DSL is re-validated if dsl_definition is provided.
    """
    try:
        return await use_cases.update_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id,
            request=request
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: uuid.UUID,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """Delete a strategy"""
    try:
        deleted = await use_cases.delete_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{strategy_id}/activate", response_model=StrategyResponse)
async def activate_strategy(
    strategy_id: uuid.UUID,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """Activate a strategy"""
    try:
        return await use_cases.activate_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{strategy_id}/deactivate", response_model=StrategyResponse)
async def deactivate_strategy(
    strategy_id: uuid.UUID,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """Deactivate a strategy"""
    try:
        return await use_cases.deactivate_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/validate", response_model=StrategyValidationResponse)
async def validate_dsl(
    dsl_definition: dict,
    current_user = Depends(get_current_user_dependency),
    use_cases: StrategyUseCases = Depends(get_strategy_use_cases)
):
    """
    Validate a DSL definition without saving.
    
    Useful for:
    - Previewing DSL from AI generation
    - Debugging strategies
    - Validating before creation
    """
    return await use_cases.validate_dsl(dsl_definition)
