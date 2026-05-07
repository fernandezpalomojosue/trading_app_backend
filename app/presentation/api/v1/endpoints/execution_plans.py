# app/presentation/api/v1/endpoints/execution_plans.py
"""
Execution Plans API Endpoints

REST API endpoints for managing execution plans.
Provides CRUD operations with authentication and ownership validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from uuid import UUID
from typing import List

from app.domain.use_cases.execution_plan_use_cases import ExecutionPlanUseCases
from app.application.dto.execution_plan_dto import (
    CreateExecutionPlanDTO, 
    UpdateExecutionPlanDTO, 
    ExecutionPlanResponseDTO
)
from app.infrastructure.security.auth_dependencies import get_current_user_dependency
from app.domain.entities.user import UserEntity
from app.infrastructure.database.execution_plan_repository import SQLExecutionPlanRepository
from app.infrastructure.database.strategy_repository import SQLStrategyRepository
from app.db.base import get_session

router = APIRouter()


def get_execution_plan_use_cases(db: Session = Depends(get_session)) -> ExecutionPlanUseCases:
    """
    Dependency injection for ExecutionPlanUseCases.
    
    Args:
        db: Database session
        
    Returns:
        Configured ExecutionPlanUseCases instance
    """
    execution_plan_repo = SQLExecutionPlanRepository(db)
    strategy_repo = SQLStrategyRepository(db)
    return ExecutionPlanUseCases(execution_plan_repo, strategy_repo)


@router.post("/execution-plans", response_model=ExecutionPlanResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_execution_plan(
    dto: CreateExecutionPlanDTO,
    current_user: UserEntity = Depends(get_current_user_dependency),
    use_cases: ExecutionPlanUseCases = Depends(get_execution_plan_use_cases)
):
    """
    Create a new execution plan.
    
    Args:
        dto: Execution plan creation data
        current_user: Authenticated user
        use_cases: Use cases for business logic
        
    Returns:
        Created execution plan
        
    Raises:
        HTTPException: If validation fails or strategy not found
    """
    try:
        plan = await use_cases.create_plan(dto, current_user.id)
        
        # Get strategy name for response
        strategy = await use_cases.strategy_repo.get_by_id(plan.strategy_id)
        strategy_name = strategy.name if strategy else "Unknown"
        
        return ExecutionPlanResponseDTO(
            id=plan.id,
            strategy_id=plan.strategy_id,
            strategy_name=strategy_name,
            stocks=plan.stocks,
            timeframe=plan.timeframe,
            is_active=plan.is_active,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )


@router.get("/execution-plans", response_model=List[ExecutionPlanResponseDTO])
async def list_execution_plans(
    current_user: UserEntity = Depends(get_current_user_dependency),
    use_cases: ExecutionPlanUseCases = Depends(get_execution_plan_use_cases)
):
    """
    List all execution plans for the current user.
    
    Args:
        current_user: Authenticated user
        use_cases: Use cases for business logic
        
    Returns:
        List of user's execution plans
        
    Raises:
        HTTPException: If server error occurs
    """
    try:
        plans_with_names = await use_cases.get_user_plans_with_strategy_names(current_user.id)
        
        return [
            ExecutionPlanResponseDTO(
                id=plan.id,
                strategy_id=plan.strategy_id,
                strategy_name=strategy_name,
                stocks=plan.stocks,
                timeframe=plan.timeframe,
                is_active=plan.is_active,
                created_at=plan.created_at.isoformat(),
                updated_at=plan.updated_at.isoformat()
            )
            for plan, strategy_name in plans_with_names
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )


@router.get("/execution-plans/{plan_id}", response_model=ExecutionPlanResponseDTO)
async def get_execution_plan(
    plan_id: UUID,
    current_user: UserEntity = Depends(get_current_user_dependency),
    use_cases: ExecutionPlanUseCases = Depends(get_execution_plan_use_cases)
):
    """
    Get a specific execution plan by ID.
    
    Args:
        plan_id: Execution plan ID
        current_user: Authenticated user
        use_cases: Use cases for business logic
        
    Returns:
        Execution plan details
        
    Raises:
        HTTPException: If plan not found or access denied
    """
    try:
        result = await use_cases.get_plan_with_strategy_name(plan_id, current_user.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        
        plan, strategy_name = result
        
        return ExecutionPlanResponseDTO(
            id=plan.id,
            strategy_id=plan.strategy_id,
            strategy_name=strategy_name,
            stocks=plan.stocks,
            timeframe=plan.timeframe,
            is_active=plan.is_active,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat()
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Plan not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )


@router.patch("/execution-plans/{plan_id}", response_model=ExecutionPlanResponseDTO)
async def update_execution_plan(
    plan_id: UUID,
    dto: UpdateExecutionPlanDTO,
    current_user: UserEntity = Depends(get_current_user_dependency),
    use_cases: ExecutionPlanUseCases = Depends(get_execution_plan_use_cases)
):
    """
    Update an existing execution plan.
    
    Args:
        plan_id: Execution plan ID
        dto: Update data
        current_user: Authenticated user
        use_cases: Use cases for business logic
        
    Returns:
        Updated execution plan
        
    Raises:
        HTTPException: If plan not found, access denied, or validation fails
    """
    try:
        plan = await use_cases.update_plan(plan_id, dto, current_user.id)
        
        # Get strategy name for response
        strategy = await use_cases.strategy_repo.get_by_id(plan.strategy_id)
        strategy_name = strategy.name if strategy else "Unknown"
        
        return ExecutionPlanResponseDTO(
            id=plan.id,
            strategy_id=plan.strategy_id,
            strategy_name=strategy_name,
            stocks=plan.stocks,
            timeframe=plan.timeframe,
            is_active=plan.is_active,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat()
        )
    except ValueError as e:
        if "not found or access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )


@router.delete("/execution-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution_plan(
    plan_id: UUID,
    current_user: UserEntity = Depends(get_current_user_dependency),
    use_cases: ExecutionPlanUseCases = Depends(get_execution_plan_use_cases)
):
    """
    Delete an execution plan.
    
    Args:
        plan_id: Execution plan ID
        current_user: Authenticated user
        use_cases: Use cases for business logic
        
    Returns:
        No content on success
        
    Raises:
        HTTPException: If plan not found or access denied
    """
    try:
        await use_cases.delete_plan(plan_id, current_user.id)
    except ValueError as e:
        if "not found or access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )
