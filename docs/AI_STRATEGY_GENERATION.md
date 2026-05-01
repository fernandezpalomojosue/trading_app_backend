# AI Strategy Generation

Natural language → Strategy DSL conversion using OpenRouter with Mistral/Mixtral models.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Endpoint  │────▶│ StrategyAIService│────▶│ AIProvider       │
│ (rate limit)│     │  (orchestration) │     │ (OpenRouter)     │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
     │                                               │
     │                                               ▼
     │                                        ┌──────────────┐
     │                                        │   AI Model   │
     │                                        │(Mistral/     │
     │                                        │ Mixtral)     │
     │                                        └──────┬───────┘
     │                                               │
     ▼                                               ▼
┌──────────────────────────────────────────────────────────┐
│                    StrategyAIService                       │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Prompts   │───▶│ AI Provider  │───▶│    Parser    │  │
│  │  (Jinja2)   │    │   .generate  │    │ (JSON ext)   │  │
│  └─────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                │          │
│                                                ▼          │
│                                         ┌──────────────┐  │
│                                         │ DSLValidator│  │
│                                         │ (validate)  │  │
│                                         └──────┬───────┘  │
│                                                │          │
│                    ┌───────────────────────────┴──────┐   │
│                    │ Valid                           │   │
│                    ▼                               │   │   │
│            ┌──────────┐                          │   │   │
│            │  Return  │◀─────────────────────────┘   │   │   │
│            │ Success  │                              │   │   │
│            └──────────┘                              │   │   │
│                                                      │   │   │
│                    │ Invalid                        │   │   │
│                    ▼                               │   │   │
│            ┌──────────────┐                        │   │   │
│            │ Build Retry  │                        │   │   │
│            │   Prompt     │────────────────────────┘   │   │
│            │ (with errors) │     (max 3 attempts)      │   │
│            └──────────────┘                            │   │
└────────────────────────────────────────────────────────┘
```

## API Endpoints

### POST /api/v1/ai-strategies/generate

Generate a trading strategy from natural language.

**Rate Limit:** 5 requests per minute per user

**Request:**
```json
{
  "prompt": "Create a strategy that buys when RSI is below 30 and price crosses above 20-day EMA"
}
```

**Success Response (200):**
```json
{
  "name": "RSI Oversold EMA Crossover",
  "description": "Buy signal when RSI indicates oversold conditions (<30) and price confirms uptrend by crossing above 20-day EMA",
  "action": "buy",
  "dsl_definition": {
    "version": 1,
    "root": {
      "type": "AND",
      "children": [
        {
          "type": "condition",
          "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
          "operator": "<",
          "right": {"type": "constant", "value": 30}
        },
        {
          "type": "condition",
          "left": {"type": "price", "field": "close"},
          "operator": "cross_above",
          "right": {"type": "indicator", "name": "EMA", "params": {"period": 20}}
        }
      ]
    }
  },
  "is_valid": true,
  "validation_errors": [],
  "attempts_made": 1
}
```

**Error Response (422):**
```json
{
  "error_type": "validation_failed",
  "message": "AI generated invalid DSL after 3 attempts",
  "details": {
    "validation_errors": ["AND node must have at least 2 children, got 1"],
    "attempts_made": 3
  }
}
```

### GET /api/v1/ai-strategies/health

Check AI service configuration status.

**Response:**
```json
{
  "configured": true,
  "provider": "openrouter",
  "model": "mistralai/mixtral-8x7b-instruct",
  "max_retries": 2,
  "timeout_seconds": 15
}
```

## Configuration

Add to your `.env`:

```bash
# Required for AI strategy generation
OPENROUTER_API_KEY=sk-or-v1-...

# Optional (defaults shown)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=mistralai/mixtral-8x7b-instruct
AI_MAX_RETRIES=2
AI_TIMEOUT_SECONDS=15
AI_RATE_LIMIT_PER_MINUTE=5
AI_MAX_OUTPUT_TOKENS=1200
```

## Retry Logic

The AI service implements intelligent retry with error feedback:

- **Initial Attempt:** Generate strategy from prompt
- **Retry (if needed):** Include validation errors in prompt for AI to fix
- **Max Attempts:** `max_retries + 1` = 3 total when `max_retries=2`

All validation uses the existing `DSLValidator` from Sprint 1.

## Separation of Concerns

| Component | Responsibility |
|-----------|---------------|
| `API Endpoint` | Rate limiting, auth, HTTP responses |
| `StrategyUseCases` | Simple delegation to AI service |
| `StrategyAIService` | ALL orchestration (prompts, AI calls, parse, validate, retry) |
| `AIProvider` | Abstract interface for AI providers |
| `OpenRouterProvider` | OpenAI-compatible HTTP client |
| `DSLValidator` | DSL structure validation (unchanged from Sprint 1) |

## Testing

```bash
# Unit tests
pytest tests/unit/domain/test_ai_response_parser.py -v
pytest tests/unit/domain/test_strategy_ai_service.py -v

# Integration tests
pytest tests/integration/test_ai_strategy_endpoint.py -v

# All AI tests
pytest tests/unit/domain/test_ai_response_parser.py tests/unit/domain/test_strategy_ai_service.py tests/integration/test_ai_strategy_endpoint.py -v
```

## Files Created/Modified

### New Files
- `app/application/services/ai_provider.py` - AIProvider Protocol
- `app/infrastructure/external/openrouter_provider.py` - OpenRouter implementation
- `app/domain/services/strategy_ai_service.py` - AI orchestration service
- `app/domain/services/ai_response_parser.py` - JSON extraction from AI responses
- `app/domain/services/ai_prompts.py` - Prompt templates
- `app/infrastructure/rate_limiter/ai_rate_limiter.py` - Per-user rate limiting
- `app/application/dto/ai_strategy_dto.py` - Request/response DTOs
- `app/presentation/api/v1/endpoints/ai_strategies.py` - API endpoint
- `tests/unit/domain/test_ai_response_parser.py` - Unit tests for parser
- `tests/unit/domain/test_strategy_ai_service.py` - Unit tests for AI service
- `tests/integration/test_ai_strategy_endpoint.py` - Integration tests

### Modified Files
- `app/core/config.py` - Added AI configuration settings
- `app/domain/use_cases/strategy_use_cases.py` - Added `generate_strategy_from_ai()` method
- `app/domain/services/strategy_registry.py` - Added `get_dsl_schema_json()` method
- `app/presentation/api/v1/endpoints/routers.py` - Registered AI strategies router
- `requirements.txt` - Added `openai>=1.0.0` dependency
