# Trading App Backend (FastAPI)

Backend para una aplicación de trading, construido con **FastAPI** + **SQLModel** (PostgreSQL) y tests en CI con Docker. Incluye autenticación JWT, endpoints de mercado (stocks) y caché.

## Stack

- **API**: FastAPI
- **DB**: PostgreSQL (SQLModel / SQLAlchemy)
- **Migraciones**: Alembic
- **Auth**: JWT (`python-jose`) + `passlib`
- **HTTP clients**: `httpx` / `aiohttp`
- **CI**: GitHub Actions (Docker Compose)
- **Deploy**: Render (Postgres managed)

## Estructura

- `app/`: código de la API
- `tests/`: test suite
- `alembic/` + `alembic.ini`: migraciones
- `scripts/render_migrate.py`: migraciones contra Postgres de Render
- `docker-compose.yml`: desarrollo local (API + Postgres)
- `docker-compose.test.yml`: CI/testing (API + Postgres)
- `Dockerfile.prod`: imagen de producción

## Endpoints principales

Base URL: `http://localhost:8000`

- **Health**
  - `GET /health`
- **Auth** (prefijo `/api/v1/auth`)
  - `POST /register`
  - `POST /login` (OAuth2 password flow)
  - `GET /me`
- **Markets** (prefijo `/api/v1/markets`)
  - `GET /api/v1/markets`
  - `GET /api/v1/markets/{market_type}/overview` *(solo `stocks`)*
  - `GET /api/v1/markets/{market_type}/assets` *(solo `stocks`)*
  - `GET /api/v1/markets/assets/{symbol}`
  - `GET /api/v1/markets/{symbol}/candles`
  - Cache (requiere auth)
    - `GET /api/v1/markets/cache/stats`
    - `DELETE /api/v1/markets/cache`
    - `DELETE /api/v1/markets/cache/market-summary`

## Ejemplos (curl)

Base URL: `http://localhost:8000`

### Registrar usuario

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "testpassword123"
  }'
```

### Login (obtener token)

El login usa `OAuth2PasswordRequestForm` (form-urlencoded). El campo `username` corresponde al **email**.

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=testpassword123"
```

Respuesta esperada (ejemplo):

```json
{"access_token":"...","token_type":"bearer"}
```

### Usar el token (Bearer)

Guarda el token en una variable (requiere `jq`):

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=testpassword123" | jq -r '.access_token')
```

Probar endpoint protegido:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Ejemplo con cache (protegido):

```bash
curl -X GET "http://localhost:8000/api/v1/markets/cache/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## Configuración (variables de entorno)

Copia `.env.example` a `.env` y completa valores.

Variables relevantes:

- `ENVIRONMENT` (`development` | `testing` | `production`)
- `DATABASE_URL` (Postgres)
- `TEST_DATABASE_URL` (opcional, solo si `ENVIRONMENT=testing`)
- `SECRET_KEY`
- `POLYGON_API_KEY`

Nota: el cliente externo usa:

- **`MASSIVE_API_KEY`** si existe
- si no, hace fallback a **`POLYGON_API_KEY`**

## Desarrollo local (Docker)

Requisito: Docker + Docker Compose.

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Postgres expuesto por override en `localhost:5432`

## Desarrollo local (sin Docker)

```bash
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Tests

### En local (pytest)

```bash
python -m pytest
```

### En CI (igual que GitHub Actions)

GitHub Actions ejecuta tests con Docker Compose (`docker-compose.test.yml`). Para replicarlo local:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api
```

## Migraciones (Alembic)

En **development/testing**, la app crea tablas automáticamente al arrancar.

En **production**, **NO** se crean tablas automáticamente. Se deben ejecutar migraciones.

Comandos típicos:

```bash
alembic revision --autogenerate -m "Descripcion"
alembic upgrade head
alembic current
alembic history
```

Guía completa: ver `MIGRATIONS.md`.

## Producción (Render)

### 1) Variables en Render

Configura en Render:

- `DATABASE_URL` (la de Render Postgres)
- `SECRET_KEY`
- `POLYGON_API_KEY`
- `ENVIRONMENT=production`

### 2) Migraciones en el deploy

La forma recomendada es ejecutar migraciones como parte del **Build Command**.

**Build Command (Render):**

```bash
pip install -r requirements.txt
python scripts/render_migrate.py
```

**Start Command (Render):**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## CI/CD

Workflow (`.github/workflows/python-app.yml`):

- **test**: corre `docker compose -f docker-compose.test.yml up ...`
- **build-and-push** (solo en `master`): build + push de imagen a GHCR con `Dockerfile.prod`

---


