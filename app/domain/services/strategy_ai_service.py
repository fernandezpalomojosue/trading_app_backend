"""
Strategy AI Service

ALL AI orchestration logic lives here:
- Prompt construction
- AI provider calls (via AIProvider abstraction)
- Response parsing
- DSL validation
- Retry loop with error feedback

NO rate limiting here (handled at endpoint level).
NO database access (pure business logic).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.services.ai_provider import AIProvider, AIProviderError
from app.domain.services.ai_prompts import StrategyGenerationPrompts

from app.domain.services.ai_response_parser import AIResponseParser
from app.domain.services.strategy_validator import DSLValidator


@dataclass
class AIGenerationResult:
    """Result of AI strategy generation attempt."""
    name: str
    description: str
    action: str  # "buy", "sell", "hold"
    dsl_definition: Dict[str, Any]
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)
    attempts_made: int = 0
    raw_response: Optional[str] = None  # For debugging


class StrategyAIService:
    """
    AI-powered strategy generation with retry logic.
    
    Contains ALL orchestration:
    1. Build prompts with DSL schema
    2. Call AI provider (abstracted)
    3. Parse JSON response
    4. Validate with DSLValidator
    5. Retry with error feedback (max 3 attempts)
    
    Usage:
        provider = OpenRouterProvider(api_key=...)
        service = StrategyAIService(provider=provider, max_retries=2)
        result = await service.generate_strategy("Buy when RSI < 30", user_id)
    """
    
    def __init__(
        self,
        provider: AIProvider,
        max_retries: int = 2
    ):
        """
        Initialize with AI provider and retry configuration.
        
        Args:
            provider: AIProvider implementation (e.g., OpenRouterProvider)
            max_retries: Number of retry attempts AFTER initial (total = retries + 1)
        """
        self.provider = provider
        self.max_retries = max_retries
        self.prompts = StrategyGenerationPrompts()
    
    async def generate_strategy(
        self,
        user_prompt: str,
        user_id: UUID  # For logging/tracking only
    ) -> AIGenerationResult:
        """
        Generate strategy from natural language with retry loop.
        
        Key: max_attempts = max_retries + 1
        With max_retries=2 → 3 total attempts (1 initial + 2 retries)
        
        Args:
            user_prompt: Natural language strategy description
            user_id: User identifier for tracking
            
        Returns:
            AIGenerationResult with DSL or validation errors
            - If successful: is_valid=True, dsl_definition populated
            - If failed: is_valid=False, validation_errors populated
        """
        print(f"[AI_SERVICE] Starting generation for user={user_id}, prompt='{user_prompt[:50]}...'")
        
        # CORRECT calculation: initial + retries
        max_attempts = self.max_retries + 1
        print(f"[AI_SERVICE] Max attempts: {max_attempts} (retries={self.max_retries})")
        
        last_response: Optional[str] = None
        last_errors: List[str] = []
        
        for attempt in range(1, max_attempts + 1):
            print(f"[AI_SERVICE] Attempt {attempt}/{max_attempts}")
            
            # Build prompt (initial or retry with error feedback)
            if attempt == 1:
                prompt = self.prompts.build_generation_prompt(user_prompt)
                print(f"[AI_SERVICE] Built generation prompt ({len(prompt)} chars)")
            else:
                prompt = self.prompts.build_retry_prompt(
                    user_prompt=user_prompt,
                    previous_response=last_response or "",
                    errors=last_errors
                )
                print(f"[AI_SERVICE] Built retry prompt with {len(last_errors)} errors")
            
            try:
                # Call AI through provider abstraction
                print(f"[AI_SERVICE] Calling AI provider (attempt {attempt})...")
                raw_response = await self.provider.generate(prompt)
                last_response = raw_response
                print(f"[AI_SERVICE] AI response received: {len(raw_response)} chars")
                
                # Parse JSON from response
                dsl_json, parse_errors = AIResponseParser.parse(raw_response)
                
                if parse_errors:
                    print(f"[AI_SERVICE] JSON parse failed: {parse_errors}")
                    last_errors = parse_errors
                    continue
                
                print(f"[AI_SERVICE] JSON parsed. Keys: {list(dsl_json.keys())}")
                
                # Extract dsl_definition for validation
                dsl_definition = dsl_json.get("dsl_definition")
                
                if not dsl_definition:
                    print(f"[AI_SERVICE] Missing 'dsl_definition' field in AI response")
                    last_errors = ["Missing required field: 'dsl_definition'"]
                    continue
                
                print(f"[AI_SERVICE] dsl_definition keys: {list(dsl_definition.keys())}")
                
                # Validate DSL structure (expects {version, root})
                print(f"[AI_SERVICE] Validating DSL structure...")
                validation = DSLValidator.validate_json(dsl_definition)
                
                if validation.is_valid:
                    print(f"[AI_SERVICE] DSL validation PASSED on attempt {attempt}")
                    # SUCCESS - extract strategy fields
                    return AIGenerationResult(
                        name=dsl_json.get("name", "Generated Strategy"),
                        description=dsl_json.get("description", ""),
                        action=dsl_json.get("action", "hold"),
                        dsl_definition=dsl_definition,
                        is_valid=True,
                        validation_errors=[],
                        attempts_made=attempt,
                        raw_response=raw_response if attempt > 1 else None  # Only keep if retried
                    )
                else:
                    print(f"[AI_SERVICE] DSL validation FAILED on attempt {attempt}: {validation.errors}")
                    print(f"[AI_SERVICE] Raw AI response that failed:\n{raw_response}")
                    last_errors = validation.errors
                    continue
                    
            except TimeoutError:
                print(f"[AI_SERVICE] Timeout on attempt {attempt}")
                last_errors = ["AI request timed out"]
                continue
            except AIProviderError as e:
                print(f"[AI_SERVICE] AIProviderError on attempt {attempt}: {e.message}")
                last_errors = [f"AI provider error: {e.message}"]
                continue
            except Exception as e:
                print(f"[AI_SERVICE] Unexpected error on attempt {attempt}: {type(e).__name__}: {str(e)}")
                last_errors = [f"Unexpected error: {str(e)}"]
                continue
        
        # MAX ATTEMPTS EXCEEDED - return failure (don't raise)
        # This allows the API to return a proper error response
        return AIGenerationResult(
            name="",
            description="",
            action="hold",
            dsl_definition={},
            is_valid=False,
            validation_errors=last_errors,
            attempts_made=max_attempts,
            raw_response=last_response
        )
