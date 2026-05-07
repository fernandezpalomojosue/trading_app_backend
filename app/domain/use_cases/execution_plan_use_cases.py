# app/domain/use_cases/execution_plan_use_cases.py
"""
Execution Plan Use Cases

Business logic for execution plan management.
Handles validation, ownership, and business rules.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.execution_plan import ExecutionPlan
from app.application.repositories.execution_plan_repository import ExecutionPlanRepository
from app.application.repositories.strategy_repository import StrategyRepository
from app.application.dto.execution_plan_dto import CreateExecutionPlanDTO, UpdateExecutionPlanDTO


class ExecutionPlanUseCases:
    """
    Use case layer for execution plan management.
    
    Contains business logic, validation, and ownership enforcement.
    Completely decoupled from runtime execution.
    """
    
    def __init__(
        self,
        execution_plan_repo: ExecutionPlanRepository,
        strategy_repo: StrategyRepository
    ):
        self.execution_plan_repo = execution_plan_repo
        self.strategy_repo = strategy_repo
    
    async def create_plan(self, dto: CreateExecutionPlanDTO, user_id: UUID) -> ExecutionPlan:
        """
        Create a new execution plan.
        
        Args:
            dto: Create execution plan DTO
            user_id: ID of the user creating the plan
            
        Returns:
            Created ExecutionPlan entity
            
        Raises:
            ValueError: If strategy doesn't exist or validation fails
        """
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        logger.debug(
            "ExecutionPlanUseCases.create_plan started",
            component="execution_plan_use_cases",
            user_id=str(user_id),
            strategy_id=str(dto.strategy_id),
            strategy_repo_is_none=self.strategy_repo is None,
            strategy_repo_type=type(self.strategy_repo).__name__ if self.strategy_repo else "None"
        )
        
        # Validate strategy exists (skip ownership validation per requirement)
        logger.debug(
            "Validating strategy exists",
            component="execution_plan_use_cases",
            strategy_id=str(dto.strategy_id)
        )
        
        strategy = self.strategy_repo.get_by_id(dto.strategy_id)
        logger.debug(
            "Strategy validation result",
            component="execution_plan_use_cases",
            strategy_is_none=strategy is None,
            strategy_type=type(strategy).__name__ if strategy else "None"
        )
        
        if not strategy:
            logger.error(
                "Strategy not found during validation",
                component="execution_plan_use_cases",
                strategy_id=str(dto.strategy_id)
            )
            raise ValueError("Strategy not found")
        
        # Create execution plan
        plan = ExecutionPlan(
            user_id=user_id,
            strategy_id=dto.strategy_id,
            stocks=dto.stocks,
            timeframe=dto.timeframe.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.execution_plan_repo.create(plan)
    
    async def get_user_plans(self, user_id: UUID) -> List[ExecutionPlan]:
        """
        Get all execution plans for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of ExecutionPlan entities owned by the user
        """
        return await self.execution_plan_repo.get_by_user_id(user_id)
    
    async def get_plan_by_id(self, plan_id: UUID, user_id: UUID) -> Optional[ExecutionPlan]:
        """
        Get execution plan by ID with ownership validation.
        
        Args:
            plan_id: ID of the execution plan
            user_id: ID of the user requesting the plan
            
        Returns:
            ExecutionPlan entity if found and owned by user, None otherwise
        """
        plan = await self.execution_plan_repo.get_by_id(plan_id)
        if not plan or plan.user_id != user_id:
            return None
        return plan
    
    async def update_plan(self, plan_id: UUID, dto: UpdateExecutionPlanDTO, user_id: UUID) -> ExecutionPlan:
        """
        Update an existing execution plan with ownership validation.
        
        Args:
            plan_id: ID of the execution plan
            dto: Update execution plan DTO
            user_id: ID of the user updating the plan
            
        Returns:
            Updated ExecutionPlan entity
            
        Raises:
            ValueError: If plan not found, access denied, or validation fails
        """
        # Get existing plan and validate ownership
        plan = await self.execution_plan_repo.get_by_id(plan_id)
        if not plan or plan.user_id != user_id:
            raise ValueError("Plan not found or access denied")
        
        # Update allowed fields only (strategy_id and user_id are immutable)
        updated_at = datetime.now(timezone.utc)
        needs_update = False
        
        if dto.stocks is not None:
            plan.stocks = dto.stocks
            needs_update = True
        
        if dto.timeframe is not None:
            plan.timeframe = dto.timeframe.value
            needs_update = True
        
        if dto.is_active is not None:
            plan.is_active = dto.is_active
            needs_update = True
        
        if needs_update:
            plan.updated_at = updated_at
            plan = await self.execution_plan_repo.update(plan)
        
        return plan
    
    async def delete_plan(self, plan_id: UUID, user_id: UUID) -> bool:
        """
        Delete an execution plan with ownership validation.
        
        Args:
            plan_id: ID of the execution plan
            user_id: ID of the user deleting the plan
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If plan not found or access denied
        """
        # Validate ownership before deletion
        plan = await self.execution_plan_repo.get_by_id(plan_id)
        if not plan or plan.user_id != user_id:
            raise ValueError("Plan not found or access denied")
        
        return await self.execution_plan_repo.delete(plan_id)
    
    async def get_plan_with_strategy_name(self, plan_id: UUID, user_id: UUID) -> Optional[tuple]:
        """
        Get execution plan with strategy name for response enrichment.
        
        Args:
            plan_id: ID of the execution plan
            user_id: ID of the user requesting the plan
            
        Returns:
            Tuple of (ExecutionPlan, strategy_name) if found and owned, None otherwise
        """
        plan = await self.execution_plan_repo.get_by_id(plan_id)
        if not plan or plan.user_id != user_id:
            return None
        
        # Get strategy name for response enrichment
        strategy = self.strategy_repo.get_by_id(plan.strategy_id)
        strategy_name = strategy.name if strategy else "Unknown"
        
        return plan, strategy_name
    
    async def get_user_plans_with_strategy_names(self, user_id: UUID) -> List[tuple]:
        """
        Get all execution plans for user with strategy names for response enrichment.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of tuples (ExecutionPlan, strategy_name)
        """
        plans = await self.execution_plan_repo.get_by_user_id(user_id)
        
        result = []
        for plan in plans:
            # Get strategy name for each plan
            strategy = self.strategy_repo.get_by_id(plan.strategy_id)
            strategy_name = strategy.name if strategy else "Unknown"
            result.append((plan, strategy_name))
        
        return result
