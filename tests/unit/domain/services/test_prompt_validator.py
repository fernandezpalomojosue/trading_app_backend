"""
Tests for Prompt Validator Service

Unit tests for prompt validation before DSL generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.domain.services.prompt_validator import PromptValidator
from app.application.dto.prompt_validation_dto import PromptValidationResponse


class TestPromptValidator:
    """Test cases for PromptValidator service."""
    
    @pytest.fixture
    def validator(self):
        """Create prompt validator instance with mocked dependencies."""
        validator = PromptValidator()
        # Mock AI provider to avoid actual API calls
        validator.ai_provider = Mock()
        return validator
    
    @pytest.mark.asyncio
    async def test_valid_prompt_with_rsi(self, validator):
        """Test validation of valid RSI-based prompt."""
        # Mock successful LLM response
        validator.ai_provider.generate_completion = AsyncMock(
            return_value='{"status": "VALID"}'
        )
        
        result = await validator.validate("buy when RSI is below 30")
        
        assert result.status == "VALID"
        assert result.reason is None
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_with_news_sentiment(self, validator):
        """Test rejection of prompt with unsupported news sentiment."""
        # Pattern matching should catch this first
        result = await validator.validate("buy based on news sentiment analysis")
        
        assert result.status == "INVALID"
        assert "Unsupported feature: news sentiment" in result.reason
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_with_contradictory_logic(self, validator):
        """Test rejection of prompt with contradictory RSI conditions."""
        # Pattern matching should catch this
        result = await validator.validate("buy when RSI > 90 and RSI < 20")
        
        assert result.status == "INVALID"
        assert "Contradictory logic" in result.reason
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_with_ambiguous_terms(self, validator):
        """Test rejection of prompt with ambiguous terms."""
        # Pattern matching should catch this
        result = await validator.validate("buy good stocks when market feels strong")
        
        assert result.status == "INVALID"
        assert "Ambiguous term: good stocks" in result.reason
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_with_unsupported_concepts(self, validator):
        """Test rejection of prompt with discretionary trading."""
        # Pattern matching should catch this
        result = await validator.validate("use discretionary trading based on psychology")
        
        assert result.status == "INVALID"
        assert "Unsupported concept: discretionary trading" in result.reason
    
    @pytest.mark.asyncio
    async def test_valid_prompt_with_multiple_indicators(self, validator):
        """Test validation of valid multi-indicator prompt."""
        validator.ai_provider.generate_completion = AsyncMock(
            return_value='{"status": "VALID"}'
        )
        
        result = await validator.validate(
            "buy when RSI < 30 and price crosses above 20-day EMA"
        )
        
        assert result.status == "VALID"
        assert result.reason is None
    
    @pytest.mark.asyncio
    async def test_llm_fallback_to_invalid(self, validator):
        """Test fallback behavior when LLM fails."""
        # Mock LLM failure
        validator.ai_provider.generate_completion = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )
        
        result = await validator.validate("any prompt")
        
        assert result.status == "INVALID"
        assert result.reason == "Validation service unavailable"
    
    @pytest.mark.asyncio
    async def test_prompt_too_short(self, validator):
        """Test rejection of extremely short prompt."""
        result = await validator.validate("buy")
        
        assert result.status == "INVALID"
    
    @pytest.mark.asyncio
    async def test_prompt_too_long(self, validator):
        """Test rejection of extremely long prompt."""
        long_prompt = "buy " * 200  # 800 characters
        result = await validator.validate(long_prompt)
        
        assert result.status == "INVALID"
    
    def test_pattern_check_unsupported_features(self, validator):
        """Test pattern matching for unsupported features."""
        prompt = "use news sentiment and social sentiment for trading"
        issues = validator._check_patterns(prompt)
        
        assert len(issues) >= 2
        assert any("news sentiment" in issue for issue in issues)
        assert any("social sentiment" in issue for issue in issues)
    
    def test_pattern_check_contradictory_logic(self, validator):
        """Test pattern matching for contradictory logic."""
        prompt = "buy when RSI > 90 and RSI < 20"
        issues = validator._check_patterns(prompt)
        
        assert len(issues) > 0
        assert any("Contradictory logic" in issue for issue in issues)
    
    def test_pattern_check_ambiguous_terms(self, validator):
        """Test pattern matching for ambiguous terms."""
        prompt = "buy good stocks from strong companies"
        issues = validator._check_patterns(prompt)
        
        assert len(issues) >= 2
        assert any("good stocks" in issue for issue in issues)
        assert any("strong companies" in issue for issue in issues)
    
    def test_build_system_prompt(self, validator):
        """Test system prompt construction."""
        prompt = validator._build_system_prompt()
        
        assert "SUPPORTED INDICATORS" in prompt
        assert "RSI" in prompt
        assert "EMA" in prompt
        assert "SUPPORTED OPERATORS" in prompt
        assert "UNSUPPORTED" in prompt
        assert "news sentiment" in prompt
        assert "VALID or INVALID" in prompt
