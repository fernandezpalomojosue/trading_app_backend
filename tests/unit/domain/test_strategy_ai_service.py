"""
Unit tests for Strategy AI Service

Tests the orchestration layer: prompts → AI → parse → validate → retry.
"""

import json
import pytest
from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

from app.application.services.ai_provider import AIProvider
from app.domain.services.strategy_ai_service import (
    StrategyAIService,
    AIGenerationResult
)


class MockAIProvider:
    """Mock AI provider for testing."""
    
    def __init__(self, responses: List[str]):
        self.responses = iter(responses)
        self.call_count = 0
        self.last_prompt = None
    
    async def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.3) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        try:
            return next(self.responses)
        except StopIteration:
            return '{}'


# Valid strategy response
VALID_STRATEGY_RESPONSE = json.dumps({
    "name": "RSI Oversold",
    "description": "Buy when RSI < 30",
    "action": "buy",
    "dsl_definition": {
        "version": 1,
        "root": {
            "type": "condition",
            "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
            "operator": "<",
            "right": {"type": "constant", "value": 30}
        }
    }
})

# Invalid JSON response
INVALID_JSON_RESPONSE = "This is not JSON at all"

# Valid JSON but invalid DSL (missing required field)
VALID_JSON_INVALID_DSL = json.dumps({
    "name": "Invalid",
    "description": "Missing dsl_definition",
    "action": "buy"
    # Missing dsl_definition field
})


class TestStrategyAIService:
    """Test StrategyAIService orchestration."""
    
    @pytest.fixture
    def user_id(self) -> UUID:
        return uuid4()
    
    def test_init_with_provider(self):
        """Initialize with AIProvider."""
        provider = MockAIProvider([VALID_STRATEGY_RESPONSE])
        
        service = StrategyAIService(provider=provider, max_retries=2)
        
        assert service.provider == provider
        assert service.max_retries == 2
    
    @pytest.mark.asyncio
    async def test_generate_strategy_success_first_attempt(self, user_id):
        """Generate strategy successfully on first attempt."""
        provider = MockAIProvider([VALID_STRATEGY_RESPONSE])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Buy when RSI is below 30",
            user_id=user_id
        )
        
        assert result.is_valid is True
        assert result.name == "RSI Oversold"
        assert result.action == "buy"
        assert result.attempts_made == 1
        assert provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_strategy_invalid_json_then_success(self, user_id):
        """Retry on invalid JSON, succeed on second attempt."""
        provider = MockAIProvider([
            INVALID_JSON_RESPONSE,  # First attempt fails
            VALID_STRATEGY_RESPONSE   # Second attempt succeeds
        ])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Buy when RSI is below 30",
            user_id=user_id
        )
        
        assert result.is_valid is True
        assert result.attempts_made == 2
        assert provider.call_count == 2
        # Check retry prompt contains error feedback
        assert "FAILED" in provider.last_prompt or "error" in provider.last_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_strategy_invalid_dsl_then_success(self, user_id):
        """Retry on invalid DSL, succeed on second attempt."""
        provider = MockAIProvider([
            VALID_JSON_INVALID_DSL,     # First: valid JSON, invalid DSL
            VALID_STRATEGY_RESPONSE    # Second: valid
        ])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.is_valid is True
        assert result.attempts_made == 2
        assert provider.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self, user_id):
        """Fail after maximum attempts (max_retries + 1)."""
        provider = MockAIProvider([
            INVALID_JSON_RESPONSE,
            INVALID_JSON_RESPONSE,
            INVALID_JSON_RESPONSE
        ])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.is_valid is False
        assert result.attempts_made == 3  # max_retries + 1
        assert provider.call_count == 3
        assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_attempt_counting_with_zero_retries(self, user_id):
        """With max_retries=0, should make exactly 1 attempt."""
        provider = MockAIProvider([INVALID_JSON_RESPONSE])
        service = StrategyAIService(provider=provider, max_retries=0)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.attempts_made == 1  # max_retries(0) + 1
        assert provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_attempt_counting_with_one_retry(self, user_id):
        """With max_retries=1, should make up to 2 attempts."""
        provider = MockAIProvider([
            INVALID_JSON_RESPONSE,
            VALID_STRATEGY_RESPONSE
        ])
        service = StrategyAIService(provider=provider, max_retries=1)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.is_valid is True
        assert result.attempts_made == 2  # max_retries(1) + 1 initial
    
    @pytest.mark.asyncio
    async def test_dsl_definition_extraction(self, user_id):
        """Extract dsl_definition from response."""
        provider = MockAIProvider([VALID_STRATEGY_RESPONSE])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        # dsl_definition should be the extracted DSL (with version and root)
        assert "version" in result.dsl_definition
        assert "root" in result.dsl_definition
        assert result.dsl_definition["version"] == 1
        assert result.dsl_definition["root"]["type"] == "condition"
    
    @pytest.mark.asyncio
    async def test_error_response_includes_raw_response(self, user_id):
        """Failed results include raw response for debugging."""
        provider = MockAIProvider([INVALID_JSON_RESPONSE])
        service = StrategyAIService(provider=provider, max_retries=0)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.is_valid is False
        assert result.raw_response == INVALID_JSON_RESPONSE


class TestStrategyAIServiceValidation:
    """Test validation integration in retry loop."""
    
    @pytest.fixture
    def user_id(self) -> UUID:
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_validation_error_included_in_retry_prompt(self, user_id):
        """Validation errors are fed back to AI in retry prompt."""
        provider = MockAIProvider([
            VALID_JSON_INVALID_DSL,  # Missing dsl_definition
            VALID_STRATEGY_RESPONSE
        ])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        # Check second prompt includes error feedback
        assert provider.call_count == 2
        assert "FAILED" in provider.last_prompt or "error" in provider.last_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_all_validation_errors_collected(self, user_id):
        """All validation errors from final attempt returned."""
        invalid_dsl = json.dumps({
            "name": "Bad",
            "action": "invalid_action",  # Invalid action
            "dsl_definition": {
                "version": 1,
                "root": {
                    "type": "AND",
                    "children": []  # Empty children (invalid)
                }
            }
        })
        
        provider = MockAIProvider([invalid_dsl, invalid_dsl, invalid_dsl])
        service = StrategyAIService(provider=provider, max_retries=2)
        
        result = await service.generate_strategy(
            user_prompt="Sell when RSI is over 70",
            user_id=user_id
        )
        
        assert result.is_valid is False
        assert len(result.validation_errors) > 0
