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

from app.core.logging_config import get_logger
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
logger = get_logger(__name__)


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
    logger.info(
        "execution_plan_creation_started",
        component="execution_plans_api",
        user_id=str(current_user.id),
        strategy_id=str(dto.strategy_id),
        stock_count=len(dto.stocks),
        timeframe=dto.timeframe.value
    )
    
    try:
        plan = await use_cases.create_plan(dto, current_user.id)
        
        # Get strategy name for response
        strategy = await use_cases.strategy_repo.get_by_id(plan.strategy_id)
        strategy_name = strategy.name if strategy else "Unknown"
        
        logger.info(
            "execution_plan_created_successfully",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan.id),
            strategy_id=str(plan.strategy_id),
            strategy_name=strategy_name,
            stock_count=len(plan.stocks),
            timeframe=plan.timeframe
        )
        
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
        logger.warning(
            "execution_plan_creation_validation_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            strategy_id=str(dto.strategy_id),
            error_type="ValidationError",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "execution_plan_creation_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            strategy_id=str(dto.strategy_id),
            error_type=type(e).__name__,
            error_message=str(e)
        )
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
    logger.info(
        "execution_plans_list_requested",
        component="execution_plans_api",
        user_id=str(current_user.id)
    )
    
    try:
        plans_with_names = await use_cases.get_user_plans_with_strategy_names(current_user.id)
        
        logger.info(
            "execution_plans_list_retrieved_successfully",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_count=len(plans_with_names)
        )
        
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
        logger.error(
            "execution_plans_list_retrieval_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            error_type=type(e).__name__,
            error_message=str(e)
        )
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
    logger.info(
        "execution_plan_retrieval_requested",
        component="execution_plans_api",
        user_id=str(current_user.id),
        plan_id=str(plan_id)
    )
    
    try:
        result = await use_cases.get_plan_with_strategy_name(plan_id, current_user.id)
        if not result:
            logger.warning(
                "execution_plan_not_found",
                component="execution_plans_api",
                user_id=str(current_user.id),
                plan_id=str(plan_id),
                error_type="NotFound"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        
        plan, strategy_name = result
        
        logger.info(
            "execution_plan_retrieved_successfully",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan.id),
            strategy_id=str(plan.strategy_id),
            strategy_name=strategy_name,
            is_active=plan.is_active
        )
        
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
        logger.warning(
            "execution_plan_access_denied",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type="AccessDenied"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Plan not found"
        )
    except Exception as e:
        logger.error(
            "execution_plan_retrieval_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type=type(e).__name__,
            error_message=str(e)
        )
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
    logger.info(
        "execution_plan_update_started",
        component="execution_plans_api",
        user_id=str(current_user.id),
        plan_id=str(plan_id),
        update_fields=[k for k, v in dto.dict(exclude_unset=True).items() if v is not None]
    )
    
    try:
        plan = await use_cases.update_plan(plan_id, dto, current_user.id)
        
        # Get strategy name for response
        strategy = await use_cases.strategy_repo.get_by_id(plan.strategy_id)
        strategy_name = strategy.name if strategy else "Unknown"
        
        logger.info(
            "execution_plan_updated_successfully",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan.id),
            strategy_id=str(plan.strategy_id),
            strategy_name=strategy_name,
            stock_count=len(plan.stocks),
            timeframe=plan.timeframe,
            is_active=plan.is_active
        )
        
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
            logger.warning(
                "execution_plan_update_access_denied",
                component="execution_plans_api",
                user_id=str(current_user.id),
                plan_id=str(plan_id),
                error_type="AccessDenied",
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        logger.warning(
            "execution_plan_update_validation_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type="ValidationError",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "execution_plan_update_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type=type(e).__name__,
            error_message=str(e)
        )
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
    logger.info(
        "execution_plan_deletion_started",
        component="execution_plans_api",
        user_id=str(current_user.id),
        plan_id=str(plan_id)
    )
    
    try:
        await use_cases.delete_plan(plan_id, current_user.id)
        
        logger.info(
            "execution_plan_deleted_successfully",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id)
        )
    except ValueError as e:
        if "not found or access denied" in str(e):
            logger.warning(
                "execution_plan_deletion_access_denied",
                component="execution_plans_api",
                user_id=str(current_user.id),
                plan_id=str(plan_id),
                error_type="AccessDenied",
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Plan not found"
            )
        logger.warning(
            "execution_plan_deletion_validation_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type="ValidationError",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "execution_plan_deletion_failed",
            component="execution_plans_api",
            user_id=str(current_user.id),
            plan_id=str(plan_id),
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )
