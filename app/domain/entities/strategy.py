# app/domain/entities/strategy.py
"""
Strategy Entity

Represents a trading strategy with DSL definition stored as JSONB.
Includes versioning for backward compatibility with AI-generated strategies.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """
    Trading Strategy entity with DSL definition.
    
    Fields:
    - id: Unique identifier
    - user_id: Owner of the strategy
    - name: Strategy name
    - description: Optional description
    - is_active: Whether the strategy is active
    - dsl_definition: JSONB storing the DSL AST
    - version: DSL version for backward compatibility
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    name: str = Field(
        min_length=1, 
        max_length=100, 
        description="Strategy name"
    )
    description: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Strategy description"
    )
    is_active: bool = Field(
        default=True, 
        description="Whether the strategy is active"
    )
    dsl_definition: Dict[str, Any] = Field(
        default_factory=dict,
        description="DSL definition as JSON object"
    )
    dsl_hash: Optional[str] = Field(
        default=None,
        description="Hash of DSL definition for change detection"
    )
    version: int = Field(
        default=1, 
        ge=1, 
        description="DSL version for backward compatibility"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    def activate(self) -> "Strategy":
        """Activate the strategy"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def deactivate(self) -> "Strategy":
        """Deactivate the strategy"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def update_name(self, name: str) -> "Strategy":
        """Update strategy name"""
        self.name = name
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def update_description(self, description: Optional[str]) -> "Strategy":
        """Update strategy description"""
        self.description = description
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def update_dsl(self, dsl_definition: Dict[str, Any], version: int) -> "Strategy":
        """
        Update DSL definition and version.
        
        Args:
            dsl_definition: New DSL JSON object
            version: DSL version number
        """
        self.dsl_definition = dsl_definition
        self.version = version
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def update(self, **kwargs) -> "Strategy":
        """
        Generic update method for multiple fields.
        
        Allowed fields: name, description, is_active, dsl_definition, version
        """
        allowed_fields = {"name", "description", "is_active", "dsl_definition", "dsl_hash", "version"}
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)
            else:
                raise ValueError(f"Cannot update field: {key}")
        
        self.updated_at = datetime.now(timezone.utc)
        return self
