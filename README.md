# Trading App Backend

Backend for a trading application, built with **FastAPI** + **SQLModel** (PostgreSQL) and CI testing with Docker. Includes JWT authentication, market endpoints (stocks), and caching.

## 🚀 Features

- ✅ **Clean Architecture**: Clear separation between domain, application, and infrastructure
- ✅ **JWT Authentication**: Secure user login and registration system
- ✅ **Trading API**: Endpoints for market data (stocks, candles)
- ✅ **Smart Caching**: Caching system to optimize responses
- ✅ **Complete Testing**: Test suite with pytest and CI/CD
- ✅ **Migrations**: Schema management with Alembic
- ✅ **Docker Ready**: Containerization for development and production
- ✅ **Automatic Deploy**: Configuration for Render and GitHub Actions

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI 0.109.0 |
| **Database** | PostgreSQL + SQLModel |
| **Migrations** | Alembic |
| **Authentication** | JWT (python-jose) + passlib + bcrypt |
| **HTTP Clients** | httpx 0.27.0 + aiohttp 3.9.1 |
| **Market Data** | Massive API |
| **Testing** | pytest 8.0.2 + pytest-asyncio |
| **CI/CD** | GitHub Actions + Docker |
| **Deploy** | Render (Postgres managed) |
| **Cache** | Memory Cache (local implementation) |

## 📁 Project Structure

```
trading-app-backend/
├── app/                          # API source code
│   ├── application/              # Application layer
│   │   ├── dto/                  # Data Transfer Objects
│   │   └── services/             # Application services
│   ├── core/                     # Core configuration and utilities
│   │   ├── config.py             # Project configuration
│   │   ├── database/             # Database configuration and models
│   │   ├── security.py           # Security utilities
│   │   └── utils/                # Various utilities
│   ├── domain/                   # Domain entities and business logic
│   │   ├── entities/             # Domain entities
│   │   └── use_cases/            # Domain use cases
│   ├── infrastructure/           # Infrastructure layer
│   │   ├── cache/                # Caching system
│   │   ├── dependencies.py       # Application dependencies
│   │   ├── external/              # External HTTP clients
│   │   ├── repositories.py       # Database repositories
│   │   └── security/             # Security utilities
│   ├── presentation/             # Presentation layer (API endpoints)
│   │   ├── api/                  # API routes
│   │   │   └── v1/               # API version 1
│   │   │       └── endpoints/    # Implemented endpoints
│   │   └── schemas/              # Pydantic schemas
│   └── main.py                   # FastAPI entry point
├── tests/                        # Test suite
│   ├── fixtures/                 # Test fixtures
│   ├── unit/                     # Unit tests
│   ├── conftest.py               # pytest configuration
│   ├── test_auth.py              # Authentication tests
│   ├── test_health.py            # Health check tests
│   ├── test_integration.py       # Integration tests
│   ├── test_models.py            # Model tests
│   └── README.md                 # Test documentation
├── alembic/                      # Database migrations
├── scripts/                      # Utility scripts
│   ├── init_db.py                # DB initialization
│   ├── migrate.py                # Migration script
│   └── render_migrate.py         # Render migrations
├── docker-compose.yml            # Local development
├── docker-compose.test.yml       # Testing/CI
├── docker-compose.prod.yml       # Production
├── docker-compose.override.yml   # Local development override
├── Dockerfile.prod               # Production
├── Dockerfile.test               # Testing
├── .dockerignore                 # Docker exclusions
├── .env.example                   # Environment variables template
├── .gitignore                     # Git exclusions
├── .flake8                        # Linting configuration
├── .python-version.txt            # Python version
├── alembic.ini                    # Alembic configuration
├── pyproject.toml                # pytest configuration
└── .github/workflows/            # CI/CD pipelines
```

## 🌐 API Endpoints

**Base URL**: `http://localhost:8000`

### 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user (requires email, username, password, optional full_name) |
| POST | `/login` | Login (OAuth2 - uses username as email) |
| GET | `/me` | Get user profile (requires token) |

### 📈 Markets (`/api/v1/markets`)
| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|---------------|
| GET | `/{market_type}/overview` | Market overview | ✅ Required |
| GET | `/{market_type}/assets` | Asset list (with query params) | ✅ Required |
| GET | `/assets/{symbol}` | Asset details | ✅ Required |
| GET | `/{symbol}/candles` | Candle data for charts (OHLCV) | ✅ Required |
| GET | `/search` | Search assets by query | ✅ Required |

**Query Parameters for `/{market_type}/assets`:**
- `limit` (optional): 1-100 (default: 50)
- `offset` (optional): 0+ (default: 0) - for pagination

**Query Parameters for `/{symbol}/candles`:**
- `timespan` (optional): "minute", "hour", "day", "week", "month", "quarter", "year" (default: "day")
- `multiplier` (optional): integer to combine with timespan (default: 1)
- `limit` (optional): 1-5000 (default: 100)
- `start_date` (optional): "YYYY-MM-DD" - custom start date
- `end_date` (optional): "YYYY-MM-DD" - custom end date (default: last trading day)

**Query Parameters for `/search`:**
- `q` (required): Search query (minimum 2 characters)
- `market_type` (optional): `stocks` (default: all)
- `limit` (optional): 1-50 (default: 20)

### ❤️ Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | General API status |

## Examples (curl)

Base URL: `http://localhost:8000`

### Register user

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### Login (get token)

Login uses `OAuth2PasswordRequestForm` (form-urlencoded). The `username` field corresponds to the **email**.

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=testpassword123"
```

Expected response (example):

```json
{"access_token":"...","token_type":"bearer"}
```

### Use the token (Bearer)

Save the token in a variable (requires `jq`):

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=testpassword123" | jq -r '.access_token')
```

Test protected endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Examples with market endpoints (require authentication):

```bash
# Get market overview
curl -X GET "http://localhost:8000/api/v1/markets/stocks/overview" \
  -H "Authorization: Bearer $TOKEN"

# List assets (first 10)
curl -X GET "http://localhost:8000/api/v1/markets/stocks/assets?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# List assets with pagination (skip first 100, show next 50)
curl -X GET "http://localhost:8000/api/v1/markets/stocks/assets?limit=50&offset=100" \
  -H "Authorization: Bearer $TOKEN"

# Daily candle data (last 100 days) - uses last trading date as endDate
curl -X GET "http://localhost:8000/api/v1/markets/AAPL/candles?timespan=day&multiplier=1&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Intraday candle data (last 50 1-hour candles)
curl -X GET "http://localhost:8000/api/v1/markets/AAPL/candles?timespan=hour&multiplier=1&limit=50" \
  -H "Authorization: Bearer $TOKEN"

# 5-minute candle data (last 200 candles)
# Note: Requires plan with intraday data access from Massive API. May not be available for all symbols.
curl -X GET "http://localhost:8000/api/v1/markets/AAPL/candles?timespan=minute&multiplier=5&limit=200" \
  -H "Authorization: Bearer $TOKEN"

# Candle data with custom date range
curl -X GET "http://localhost:8000/api/v1/markets/AAPL/candles?timespan=day&multiplier=1&start_date=2026-01-17&end_date=2026-01-25&limit=5000" \
  -H "Authorization: Bearer $TOKEN"

# Weekly candle data (last 20 weeks)
curl -X GET "http://localhost:8000/api/v1/markets/AAPL/candles?timespan=week&multiplier=1&limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Search assets (minimum 2 characters, maximum 50 results by default)
curl -X GET "http://localhost:8000/api/v1/markets/search?q=AAPL&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Search assets filtering by market type
curl -X GET "http://localhost:8000/api/v1/markets/search?q=AAPL&market_type=stocks&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Asset details
curl -X GET "http://localhost:8000/api/v1/markets/assets/AAPL" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Environment Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
# Environment
cp .env.example .env
```

**Required variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Execution environment | `development`/`testing`/`production` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Key for JWT | `your-super-secret-key-here` |
| `MASSIVE_API_KEY` | Massive API API Key | `your-massive-api-key-here` |

**Notes about the API Key:**
- `MASSIVE_API_KEY` is required to get market data
- Intraday data (minute candles) may require a paid plan from Massive API
- Some symbols may not have high-frequency historical data available

**Optional variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `TEST_DATABASE_URL` | DB for testing | `postgresql://postgres:postgres@localhost/test_trading_app` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration (minutes) | `1440` |
| `ECHO_SQL` | Show SQL queries | `false` |
| `DEBUG` | Debug mode | `false` |
| `RELOAD` | Auto-reload in development | `false` |
| `PROJECT_NAME` | Project name | `Trading App API` |
| `PROJECT_DESCRIPTION` | Project description | `API for the trading application` |
| `PROJECT_VERSION` | Project version | `0.1.0` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `*` |
| `CORS_ALLOW_CREDENTIALS` | Allow CORS credentials | `true` |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | `*` |
| `CORS_ALLOW_HEADERS` | Allowed headers | `*` |

### 2. External API Priority

The system uses only **Massive API** to get market data.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

**Requirements:** Docker + Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd trading-app-backend

# Configure environment variables
cp .env.example .env
# Edit .env with your values

# Start services
docker compose up --build
```

**Access:**
- API: `http://localhost:8000`
- Postgres: `localhost:5432`
- API Docs: `http://localhost:8000/docs`

### Option 2: Local Development

**Requirements:** Python 3.9+

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your values

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Access:**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 🧪 Testing

### Local Tests

```bash
# Run all tests
python -m pytest

# With coverage
python -m pytest --cov=app --cov-report=html

# Specific tests
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_models.py -v
python -m pytest tests/test_integration.py -v
```

### CI/CD Tests

To replicate the GitHub Actions environment locally:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api
```

**Test Structure:**
- `conftest.py`: pytest configuration and fixtures
- `test_auth.py`: Authentication and registration tests
- `test_health.py`: Health check tests
- `test_integration.py`: Integration tests
- `test_models.py`: Data model tests
- `fixtures/`: Reusable test fixtures
- `unit/`: Unit tests of isolated components
- `README.md`: Test documentation

## 🗄️ Database Migrations

### Environments

- **Development/Testing**: Tables are created automatically on startup
- **Production**: **DO NOT** create tables automatically. Migrations are required

### Main Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description of change"

# Apply migrations
alembic upgrade head

# Check current status
alembic current

# View complete history
alembic history

# Revert last migration
alembic downgrade -1
```

### Troubleshooting

**Common error:** `No module named 'app.models'`

**Solution:** Make sure `alembic/env.py` imports from the correct path:
```python
from app.infrastructure.database.models import UserSQLModel
```

📖 **Complete guide:** See `MIGRATIONS.md` for more details.

## 🚀 Production (Render)

### 1. Render Configuration

**Required Environment Variables:**
- `DATABASE_URL` (Render PostgreSQL URL)
- `SECRET_KEY` (secure key for JWT)
- `MASSIVE_API_KEY` (API key for market data from Massive API)
- `ENVIRONMENT=production`

### 2. Deploy Commands

**Build Command:**
```bash
pip install -r requirements.txt
python scripts/render_migrate.py
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. Deploy Flow

1. **Push to master** → GitHub Actions creates Docker image
2. **Automatic deploy** → Render executes build and start commands
3. **Migrations** → Applied automatically during build
4. **API Live** → Available at Render URL

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/python-app.yml`

**Jobs:**

| Job | Trigger | Description |
|-----|---------|-------------|
| `test` | Push/PR to master | Run tests with Docker Compose using docker-compose.test.yml |
| `build-and-push` | Push to master | Build and push image to GitHub Container Registry (GHCR) |

### CI/CD Flow

1. **Development:**
   - Pull Request to master → Automatic tests with Docker
   - Push to master → Tests + Build Docker image

2. **Production:**
   - Merge to `master` → Tests + Build image + Push to GHCR
   - Manual or automatic deploy to Render using GHCR image

### Docker Image

**Registry:** GitHub Container Registry (GHCR)
**Tags:** 
- `latest` for latest build of `master`
- `{commit_sha}` for each specific commit

---

## 📚 Additional Documentation

- [📖 Migration Guide](MIGRATIONS.md)
- [🔧 API Documentation](http://localhost:8000/docs) (when running)
- [🐳 Docker Configuration](docker-compose.yml)

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🆘 Support

If you encounter any issues:

1. Check [existing issues](../../issues)
2. Create a new issue with detailed description
3. Include logs and steps to reproduce
