"""
Prompt Validator Service

Lightweight validation layer for strategy prompts before DSL generation.
Validates prompts against supported features, concepts, and logical consistency.
"""

import json
import re
from typing import Dict, List, Optional

from app.application.dto.prompt_validation_dto import (
    PromptValidationRequest,
    PromptValidationResponse
)
from app.domain.services.strategy_registry import StrategyRegistry
from app.infrastructure.external.ai_provider_factory import AIProviderFactory
from app.core.config import settings


class PromptValidator:
    """
    Validates strategy prompts before DSL generation.
    
    Simple, deterministic validation that returns VALID/INVALID status.
    No DSL generation, no prompt rewriting, no clarification loops.
    """
    
    def __init__(self):
        self.registry = StrategyRegistry()
        self.ai_provider = AIProviderFactory.create()
    
    async def validate(self, prompt: str) -> PromptValidationResponse:
        """
        Validate a strategy prompt.
        
        Args:
            prompt: Natural language strategy description
            
        Returns:
            PromptValidationResponse with VALID or INVALID status
        """
        # First check for obvious issues using pattern matching
        pattern_issues = self._check_patterns(prompt)
        if pattern_issues:
            return PromptValidationResponse(
                status="INVALID",
                reason="; ".join(pattern_issues)
            )
        
        # Use LLM for nuanced validation with low temperature
        llm_result = await self._validate_with_llm(prompt)
        
        return PromptValidationResponse(**llm_result)
    
    def _check_patterns(self, prompt: str) -> List[str]:
        """Check for obvious issues using pattern matching."""
        issues = []
        
        # Check unsupported features
        unsupported_features = self.registry.has_unsupported_features(prompt)
        issues.extend(unsupported_features)
        
        # Check unsupported concepts
        unsupported_concepts = self.registry.has_unsupported_concepts(prompt)
        issues.extend(unsupported_concepts)
        
        # Check ambiguous terms
        ambiguous_terms = self.registry.has_ambiguous_terms(prompt)
        issues.extend(ambiguous_terms)
        
        # Check contradictory logic
        contradictions = self.registry.has_contradictory_logic(prompt)
        issues.extend(contradictions)
        
        return issues
    
    async def _validate_with_llm(self, prompt: str) -> Dict[str, str]:
        """
        Use LLM for nuanced validation with deterministic output.
        
        Low temperature for consistency, constrained JSON output.
        """
        system_prompt = self._build_system_prompt()
        
        try:
            response = await self.ai_provider.generate(
                prompt=f"Validate this trading strategy prompt: '{prompt}'",
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for deterministic output
                max_tokens=100   # Short responses
            )
            
            # Parse JSON response
            return json.loads(response.strip())
            
        except Exception as e:
            # Fallback to conservative rejection
            return {
                "status": "INVALID",
                "reason": "Validation service unavailable"
            }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM validation."""
        from app.application.dto.ai_prompts_dto import AIPromptsDTO
        
        return AIPromptsDTO.get_validation_system_prompt()
    
    def _is_too_short(self, prompt: str) -> bool:
        """Check if prompt is too short to be meaningful."""
        return len(prompt.strip()) < 10
    
    def _is_too_long(self, prompt: str) -> bool:
        """Check if prompt exceeds reasonable length."""
        return len(prompt.strip()) > 500
