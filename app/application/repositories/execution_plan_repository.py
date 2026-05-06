# app/application/repositories/execution_plan_repository.py
"""
ExecutionPlan Repository Interface

Abstract interface for execution plan persistence.
Implementations can use PostgreSQL, Redis, or other storage.
"""

import uuid
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.execution_plan import ExecutionPlan


class ExecutionPlanRepository(ABC):
    """
    Abstract repository for ExecutionPlan entity.
    
    Provides CRUD operations for execution plans.
    """
    
    @abstractmethod
    async def get_active_plans(self) -> List[ExecutionPlan]:
        """
        Get all active execution plans.
        
        Returns:
            List of active ExecutionPlan entities
            
        Raises:
            DatabaseError: If query fails
        """
    
    @abstractmethod
    async def create(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Create a new execution plan.
        
        Args:
            plan: ExecutionPlan entity to create
            
        Returns:
            Created ExecutionPlan with generated ID
            
        Raises:
            DatabaseError: If creation fails
            ValidationError: If plan data is invalid
        """
    
    @abstractmethod
    async def update(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Update an existing execution plan.
        
        Args:
            plan: ExecutionPlan entity with updated fields
            
        Returns:
            Updated ExecutionPlan entity
            
        Raises:
            DatabaseError: If update fails
            NotFoundError: If plan doesn't exist
        """
    
    @abstractmethod
    async def get_by_id(self, plan_id: uuid.UUID) -> ExecutionPlan:
        """
        Get execution plan by ID.
        
        Args:
            plan_id: UUID of the execution plan
            
        Returns:
            ExecutionPlan entity
            
        Raises:
            NotFoundError: If plan doesn't exist
            DatabaseError: If query fails
        """
    
    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> List[ExecutionPlan]:
        """
        Get all execution plans for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of ExecutionPlan entities for the user
            
        Raises:
            DatabaseError: If query fails
        """
    
    @abstractmethod
    async def delete(self, plan_id: uuid.UUID) -> bool:
        """
        Delete an execution plan.
        
        Args:
            plan_id: UUID of the execution plan to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
