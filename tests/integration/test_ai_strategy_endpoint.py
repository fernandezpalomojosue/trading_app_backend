"""
Integration tests for AI Strategy Endpoint

Full flow tests with mocked AI responses.
Tests rate limiting, validation, and error handling at API level.
"""

import json
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.domain.services.strategy_ai_service import StrategyAIService
from app.domain.use_cases.strategy_use_cases import StrategyUseCases
from app.infrastructure.rate_limiter.ai_rate_limiter import AIRateLimiter


# Mock AI responses
VALID_AI_RESPONSE = json.dumps({
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

INVALID_JSON_RESPONSE = "Not valid JSON"

VALID_JSON_INVALID_DSL = json.dumps({
    "name": "Invalid",
    "description": "Missing fields",
    "action": "buy"
    # Missing dsl_definition
})


class MockAIProvider:
    """Mock provider for integration tests."""
    def __init__(self, responses):
        self.responses = iter(responses)
        self.call_count = 0
    
    async def generate(self, prompt: str) -> str:
        self.call_count += 1
        try:
            return next(self.responses)
        except StopIteration:
            return '{}'


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock auth headers (would need valid token in real tests)."""
    # In real tests, you'd get a valid JWT token
    return {"Authorization": "Bearer test-token"}


@pytest.mark.skip("Requires auth setup")
class TestAIEndpointSuccess:
    """Test successful strategy generation flow."""
    
    @pytest.mark.asyncio
    async def test_endpoint_success_200(self, client, auth_headers, monkeypatch):
        """Full valid flow returns 200 with generated strategy."""
        # Mock AI service to return valid response immediately
        from app.presentation.api.v1.endpoints.ai_strategies import get_strategy_use_cases
        
        mock_provider = MockAIProvider([VALID_AI_RESPONSE])
        mock_ai_service = StrategyAIService(provider=mock_provider, max_retries=2)
        
        def mock_get_use_cases():
            use_cases = StrategyUseCases(repository=None)
            use_cases.set_ai_service(mock_ai_service)
            return use_cases
        
        app.dependency_overrides[get_strategy_use_cases] = mock_get_use_cases
        
        try:
            response = client.post(
                "/api/v1/ai-strategies/generate",
                json={"prompt": "Create RSI strategy"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "RSI Oversold"
            assert data["action"] == "buy"
            assert data["is_valid"] is True
            assert data["attempts_made"] == 1
            assert "dsl_definition" in data
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_endpoint_retry_then_success(self, client, auth_headers):
        """Retry on first failure, succeed on second."""
        pass  # Implement with proper auth mocking


@pytest.mark.skip("Requires auth setup")
class TestAIEndpointErrors:
    """Test error handling at endpoint level."""
    
    @pytest.mark.asyncio
    async def test_endpoint_validation_failed_422(self, client, auth_headers):
        """AI fails all retries, return 422 with validation errors."""
        pass  # Implement with proper auth mocking
    
    @pytest.mark.asyncio
    async def test_endpoint_unauthorized_401(self, client):
        """No auth token returns 401."""
        response = client.post(
            "/api/v1/ai-strategies/generate",
            json={"prompt": "Create strategy"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_endpoint_invalid_prompt_400(self, client, auth_headers):
        """Invalid prompt (too short) returns 400."""
        response = client.post(
            "/api/v1/ai-strategies/generate",
            json={"prompt": "Hi"},  # Too short (min 10)
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestAIRateLimiter:
    """Test rate limiting in isolation."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_under_quota(self):
        """Allow requests under rate limit."""
        limiter = AIRateLimiter(max_requests=5, window_seconds=60)
        user_id = "test-user-1"
        
        # 5 requests should be allowed
        for _ in range(5):
            allowed = await limiter.check_rate_limit(user_id)
            assert allowed is True
            await limiter.record_request(user_id)
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_quota(self):
        """Block requests over rate limit."""
        limiter = AIRateLimiter(max_requests=5, window_seconds=60)
        user_id = "test-user-2"
        
        # Use up all requests
        for _ in range(5):
            await limiter.record_request(user_id)
        
        # 6th request should be blocked
        allowed = await limiter.check_rate_limit(user_id)
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_resets(self):
        """Rate limit window resets after expiration."""
        import time
        
        limiter = AIRateLimiter(max_requests=1, window_seconds=0.1)
        user_id = "test-user-3"
        
        # Use up request
        await limiter.record_request(user_id)
        
        # Should be blocked
        assert await limiter.check_rate_limit(user_id) is False
        
        # Wait for window to expire
        time.sleep(0.15)
        
        # Should be allowed again
        assert await limiter.check_rate_limit(user_id) is True
    
    @pytest.mark.asyncio
    async def test_remaining_quota(self):
        """Track remaining quota per user."""
        limiter = AIRateLimiter(max_requests=5, window_seconds=60)
        user_id = "test-user-4"
        
        assert limiter.get_remaining_quota(user_id) == 5
        
        await limiter.record_request(user_id)
        assert limiter.get_remaining_quota(user_id) == 4
        
        await limiter.record_request(user_id)
        assert limiter.get_remaining_quota(user_id) == 3
    
    @pytest.mark.asyncio
    async def test_retry_after_calculation(self):
        """Calculate seconds until rate limit reset."""
        import time
        
        limiter = AIRateLimiter(max_requests=5, window_seconds=60)
        user_id = "test-user-5"
        
        # Record request to start window
        await limiter.record_request(user_id)
        
        # Should be around 60 seconds (allow for test execution time)
        retry_after = limiter.get_retry_after(user_id)
        assert 55 <= retry_after <= 60, f"Expected 55-60, got {retry_after}"
        
        # Wait a bit
        time.sleep(0.15)
        
        # Should be less now (or at least not more)
        retry_after2 = limiter.get_retry_after(user_id)
        assert retry_after2 <= retry_after, f"Expected {retry_after2} <= {retry_after}"


class TestAIServiceHealth:
    """Test AI service health endpoint."""
    
    def test_health_endpoint_unconfigured(self, client):
        """Health check when AI not configured."""
        response = client.get("/api/v1/ai-strategies/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # When OPENROUTER_API_KEY not set
        assert data["configured"] is False
        assert data["provider"] is None
