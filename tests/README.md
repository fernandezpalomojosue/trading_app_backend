# Tests

This directory contains the test suite for the trading app backend.

## Test Structure

- `conftest.py` - Shared test fixtures and configuration
- `test_auth.py` - Authentication and user management tests
- `test_markets.py` - Market data endpoints tests
- `test_health.py` - Health check endpoints tests
- `test_integration.py` - Integration tests for complete workflows
- `test_models.py` - Domain and database model tests

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auth.py::TestAuthEndpoints::test_register_user_success
```

## Test Categories

### Unit Tests
- Model validation
- Business logic
- Entity behavior

### Integration Tests
- API endpoints
- Database operations
- Authentication flows

### End-to-End Tests
- Complete user workflows
- Error handling
- Concurrent requests

## Test Fixtures

- `client` - FastAPI test client with database session
- `db_session` - In-memory SQLite database session
- `sample_user` - Sample user entity for testing
- `authenticated_user` - User with valid authentication token

## Notes

- Tests use an in-memory SQLite database for isolation
- Authentication tests handle both success and failure scenarios
- Market tests account for external API failures
- All tests are designed to be independent and repeatable
