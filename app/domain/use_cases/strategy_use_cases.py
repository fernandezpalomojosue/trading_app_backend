# app/domain/use_cases/strategy_use_cases.py
"""
Strategy Use Cases

Business logic for strategy CRUD operations.
Integrates DSLValidator for validation before persistence.
"""

import uuid
from typing import Any, Dict, List, Union

from app.domain.entities.strategy import Strategy
from app.application.dto.ai_strategy_dto import (
    StrategyGenerateResponse,
    StrategyGenerationError
)
from app.domain.entities.strategy_dsl import StrategyDSL
from app.domain.services.strategy_validator import DSLValidator, ValidationResult
from app.application.repositories.strategy_repository import StrategyRepository
from app.application.dto.strategy_dto import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyListResponse,
    StrategyValidationResponse
)


class StrategyUseCases:
    """
    Business logic for trading strategies.
    
    Integrates DSL validation before persistence.
    Provides CRUD operations with validation.
    """
    
    def __init__(self, repository: StrategyRepository):
        self._repository = repository
        self._strategy_ai_service = None  # Set via set_ai_service() for AI generation
    
    async def create_strategy(
        self, 
        user_id: uuid.UUID, 
        request: StrategyCreateRequest
    ) -> StrategyResponse:
        """
        Create a new strategy with DSL validation.
        
        Args:
            user_id: Owner of the strategy
            request: Create request with DSL definition
            
        Returns:
            Created strategy response
            
        Raises:
            ValueError: If DSL validation fails
        """
        # Validate DSL before creating
        validation_result = self._validate_dsl(request.dsl_definition)
        if not validation_result.is_valid:
            raise ValueError(
                f"DSL validation failed: {'; '.join(validation_result.errors)}"
            )
        
        # Create entity
        strategy = Strategy(
            user_id=user_id,
            name=request.name,
            description=request.description,
            dsl_definition=request.dsl_definition,
            version=request.version,
            is_active=request.is_active
        )
        
        # Persist
        created = await self._repository.create(strategy)
        
        return self._to_response(created)
    
    async def update_strategy(
        self,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID,
        request: StrategyUpdateRequest
    ) -> StrategyResponse:
        """
        Update an existing strategy with DSL validation.
        
        Args:
            user_id: Owner of the strategy (for verification)
            strategy_id: Strategy to update
            request: Update request
            
        Returns:
            Updated strategy response
            
        Raises:
            ValueError: If strategy not found or DSL validation fails
            PermissionError: If user doesn't own the strategy
        """
        # Get existing strategy
        existing = await self._repository.get_by_id(strategy_id)
        if not existing:
            raise ValueError(f"Strategy not found: {strategy_id}")
        
        # Verify ownership
        if existing.user_id != user_id:
            raise PermissionError("Cannot update strategy owned by another user")
        
        # Validate DSL if provided
        if request.dsl_definition is not None:
            # Use provided version or existing version
            version = request.version if request.version is not None else existing.version
            dsl_to_validate = request.dsl_definition.copy()
            dsl_to_validate["version"] = version
            
            validation_result = self._validate_dsl(dsl_to_validate)
            if not validation_result.is_valid:
                raise ValueError(
                    f"DSL validation failed: {'; '.join(validation_result.errors)}"
                )
        
        # Update fields
        update_data: Dict[str, Any] = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.dsl_definition is not None:
            update_data["dsl_definition"] = request.dsl_definition
        if request.version is not None:
            update_data["version"] = request.version
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        existing.update(**update_data)
        
        # Persist
        updated = await self._repository.update(existing)
        
        return self._to_response(updated)
    
    async def delete_strategy(
        self,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID
    ) -> bool:
        """
        Delete a strategy.
        
        Args:
            user_id: Owner of the strategy (for verification)
            strategy_id: Strategy to delete
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If strategy not found
            PermissionError: If user doesn't own the strategy
        """
        # Get existing strategy
        existing = await self._repository.get_by_id(strategy_id)
        if not existing:
            raise ValueError(f"Strategy not found: {strategy_id}")
        
        # Verify ownership
        if existing.user_id != user_id:
            raise PermissionError("Cannot delete strategy owned by another user")
        
        return await self._repository.delete(strategy_id)
    
    async def get_strategy(
        self,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID
    ) -> StrategyResponse:
        """
        Get a strategy by ID.
        
        Args:
            user_id: Owner of the strategy (for verification)
            strategy_id: Strategy to retrieve
            
        Returns:
            Strategy response
            
        Raises:
            ValueError: If strategy not found
            PermissionError: If user doesn't own the strategy
        """
        strategy = await self._repository.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy not found: {strategy_id}")
        
        # Verify ownership
        if strategy.user_id != user_id:
            raise PermissionError("Cannot access strategy owned by another user")
        
        return self._to_response(strategy)
    
    async def list_strategies(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> StrategyListResponse:
        """
        List all strategies for a user.
        
        Args:
            user_id: Owner of the strategies
            skip: Pagination offset
            limit: Pagination limit
            active_only: If True, filter to active strategies only
            
        Returns:
            List of strategy responses
        """
        strategies = await self._repository.get_by_user(user_id, skip=skip, limit=limit)
        
        # Filter by active status if requested
        if active_only:
            strategies = [s for s in strategies if s.is_active]
        
        # Calculate total from the filtered results (no count query available)
        total = len(strategies)
        
        return StrategyListResponse(
            items=[self._to_response(s) for s in strategies],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        )
    
    async def validate_dsl(
        self,
        dsl_definition: Dict[str, Any]
    ) -> StrategyValidationResponse:
        """
        Validate a DSL definition without persisting.
        
        Args:
            dsl_definition: DSL JSON object to validate
            
        Returns:
            Validation response with errors and warnings
        """
        result = self._validate_dsl(dsl_definition)
        
        return StrategyValidationResponse(
            is_valid=result.is_valid,
            depth=result.depth,
            errors=result.errors,
            warnings=result.warnings
        )
    
    async def activate_strategy(
        self,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID
    ) -> StrategyResponse:
        """Activate a strategy"""
        strategy = await self.get_strategy(user_id, strategy_id)
        
        # Get full entity
        entity = await self._repository.get_by_id(strategy_id)
        entity.activate()
        
        updated = await self._repository.update(entity)
        return self._to_response(updated)
    
    async def deactivate_strategy(
        self,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID
    ) -> StrategyResponse:
        """Deactivate a strategy"""
        strategy = await self.get_strategy(user_id, strategy_id)
        
        # Get full entity
        entity = await self._repository.get_by_id(strategy_id)
        entity.deactivate()
        
        updated = await self._repository.update(entity)
        return self._to_response(updated)
    
    async def get_user_active_strategies(self, user_id: uuid.UUID) -> List[Strategy]:
        """
        Get all active strategies for a user.
        
        Args:
            user_id: User ID to fetch strategies for
            
        Returns:
            List of active Strategy entities
        """
        # Fetch user's strategies with active filter
        strategies = await self._repository.list_by_user(
            user_id=user_id,
            skip=0,
            limit=1000,
            active_only=True
        )
        return strategies
    
    async def get_default_strategy(self) -> Strategy:
        """
        Get the system default strategy.
        
        Returns:
            Default Strategy entity (DSL-based, not hardcoded)
            
        Note:
            This is used when a user has no custom strategies defined.
            The default strategy is a DSL-based equivalent to the old hardcoded rules.
        """
        from app.infrastructure.database.default_strategy_seed import get_default_strategy_entity
        return get_default_strategy_entity()
    
    async def generate_strategy_from_ai(
        self,
        user_id: uuid.UUID,
        prompt: str
    ) -> Union["StrategyGenerateResponse", "StrategyGenerationError"]:
        """
        Generate a strategy from natural language using AI.
        
        This is a SIMPLE DELEGATION to StrategyAIService.
        All orchestration (retry, parse, validate) lives in the AI service.
        
        Args:
            user_id: User requesting the generation
            prompt: Natural language strategy description
            
        Returns:
            StrategyGenerateResponse on success
            StrategyGenerationError on failure
            
        Raises:
            RuntimeError: If StrategyAIService not configured
        """
        from app.domain.services.strategy_ai_service import StrategyAIService
        
        # Check if AI service is configured
        if self._strategy_ai_service is None:
            return StrategyGenerationError(
                error_type="ai_error",
                message="AI strategy generation not configured"
            )
        
        # Delegate to AI service - NO orchestration logic here
        result = await self._strategy_ai_service.generate_strategy(
            user_prompt=prompt,
            user_id=user_id
        )
        
        if result.is_valid:
            # Create and save the strategy to database
            from app.application.dto.strategy_dto import StrategyCreateRequest
            
            create_request = StrategyCreateRequest(
                name=result.name,
                description=result.description,
                dsl_definition=result.dsl_definition
            )
            
            try:
                saved_strategy = await self.create_strategy(user_id, create_request)
                print(f"[AI_GENERATION] Strategy saved: id={saved_strategy.id}, name={saved_strategy.name}")
                
                return StrategyGenerateResponse(
                    id=saved_strategy.id,
                    name=result.name,
                    description=result.description,
                    action=result.action,
                    dsl_definition=result.dsl_definition,
                    is_active=True,
                    is_valid=True,
                    validation_errors=[],
                    attempts_made=result.attempts_made,
                    saved=True
                )
            except Exception as e:
                print(f"[AI_GENERATION] WARNING: Strategy generated but failed to save: {e}")
                # Return generated strategy even if save failed
                return StrategyGenerateResponse(
                    name=result.name,
                    description=result.description,
                    action=result.action,
                    dsl_definition=result.dsl_definition,
                    is_active=False,
                    is_valid=True,
                    validation_errors=[],
                    attempts_made=result.attempts_made,
                    saved=False
                )
        else:
            return StrategyGenerationError(
                error_type="validation_failed",
                message=f"Failed to generate valid DSL after {result.attempts_made} attempts",
                details={
                    "validation_errors": result.validation_errors,
                    "attempts_made": result.attempts_made,
                    "raw_response_preview": result.raw_response[:500] if result.raw_response else None
                }
            )
    
    def set_ai_service(self, ai_service: 'StrategyAIService') -> None:
        """
        Set the AI service for strategy generation.
        
        Args:
            ai_service: StrategyAIService instance with configured AIProvider
        """
        self._strategy_ai_service = ai_service
    
    def _validate_dsl(self, dsl_definition: Dict[str, Any]) -> ValidationResult:
        """Validate DSL definition using DSLValidator"""
        return DSLValidator.validate_json(dsl_definition)
    
    def _to_response(self, strategy: Strategy) -> StrategyResponse:
        """Convert Strategy entity to StrategyResponse DTO"""
        return StrategyResponse(
            id=strategy.id,
            user_id=strategy.user_id,
            name=strategy.name,
            description=strategy.description,
            is_active=strategy.is_active,
            dsl_definition=strategy.dsl_definition,
            version=strategy.version,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
