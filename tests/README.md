# Tests

This directory contains the test suite for the trading app backend.

## Test Structure

```
tests/
├── conftest.py              # Shared test fixtures and configuration
├── fixtures/                 # Test data fixtures
│   ├── user_fixtures.py
│   ├── market_fixtures.py
│   └── portfolio_fixtures.py
├── integration/              # Integration tests
│   ├── test_integration.py    # End-to-end workflow tests
│   └── test_health.py       # Health check endpoints
└── unit/                    # Unit tests
    ├── domain/              # Domain layer tests
    │   ├── test_domain_entities.py
    │   └── test_market_data_processor.py
    ├── presentation/        # Presentation layer tests
    │   ├── test_auth.py     # Authentication endpoints
    │   ├── test_portfolio.py # Portfolio endpoints
    │   └── test_data_validation.py
    ├── use_cases/          # Use cases tests
    │   └── test_portfolio_use_cases.py
    └── infrastructure/      # Infrastructure layer tests
        └── test_models.py   # Database models
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/presentation/test_auth.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/presentation/test_auth.py::TestAuthEndpoints::test_register_user_success

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m auth
pytest -m portfolio
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Domain**: Business logic, entities, and domain services
- **Presentation**: API endpoints, validation, and HTTP responses
- **Use Cases**: Application business logic and workflows
- **Infrastructure**: Database models, external services, and utilities

### Integration Tests (`tests/integration/`)
- Complete API workflows
- Database operations
- Authentication flows
- Health checks
- Error handling across layers

## Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.auth`: Authentication related tests
- `@pytest.mark.portfolio`: Portfolio related tests
- `@pytest.mark.market`: Market related tests
- `@pytest.mark.user`: User related tests
- `@pytest.mark.slow`: Tests that take longer to run

## Test Fixtures

### Global Fixtures
- `client`: FastAPI test client with database session
- `db_session`: Database session for testing
- `engine`: Test database engine
- `authenticated_user`: User with valid authentication token

### Domain Fixtures (from `fixtures/`)
- `sample_user`: Sample user entity for testing
- `user_test_data`: Various user data scenarios
- `market_data`: Sample market data
- `portfolio_data`: Sample portfolio data

## Configuration

Test configuration is in:
- `conftest.py`: Global test setup and fixtures
- `pytest.ini`: Pytest configuration and markers

## Notes

- Tests use PostgreSQL for integration tests and SQLite for unit tests
- All tests are designed to be independent and repeatable
- Authentication tests handle both success and failure scenarios
- Market tests account for external API failures
- Database is cleaned between tests for isolation

## Best Practices

1. **Unit Tests**: Test single functions/classes in isolation
2. **Integration Tests**: Test complete workflows and API endpoints
3. **Fixtures**: Use fixtures for common test data
4. **Markers**: Use markers to categorize tests
5. **Isolation**: Each test should not depend on others
6. **Coverage**: Aim for high test coverage in critical paths
