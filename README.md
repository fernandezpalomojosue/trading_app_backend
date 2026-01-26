# Trading App Backend

Backend para una aplicación de trading, construido con **FastAPI** + **SQLModel** (PostgreSQL) y tests en CI con Docker. Incluye autenticación JWT, endpoints de mercado (stocks) y caché.

## 🚀 Características

- ✅ **Arquitectura Limpia**: Separación clara entre dominio, aplicación e infraestructura
- ✅ **Autenticación JWT**: Sistema seguro de login y registro de usuarios
- ✅ **API de Trading**: Endpoints para obtener datos de mercado (stocks, candles)
- ✅ **Caché Inteligente**: Sistema de caché para optimizar respuestas
- ✅ **Testing Completo**: Suite de tests con pytest y CI/CD
- ✅ **Migraciones**: Gestión de esquema con Alembic
- ✅ **Docker Ready**: Contenerización para desarrollo y producción
- ✅ **Deploy Automático**: Configuración para Render y GitHub Actions

## 🛠️ Tech Stack

| Componente | Tecnología |
|------------|------------|
| **API Framework** | FastAPI |
| **Base de Datos** | PostgreSQL + SQLModel |
| **Migraciones** | Alembic |
| **Autenticación** | JWT (python-jose) + passlib |
| **HTTP Clients** | httpx / aiohttp |
| **Testing** | pytest + TestClient |
| **CI/CD** | GitHub Actions + Docker |
| **Deploy** | Render (Postgres managed) |
| **Caché** | Redis (opcional) |

## 📁 Estructura del Proyecto

```
trading-app-backend/
├── app/                          # Código fuente de la API
│   ├── application/              # Capa de aplicación
│   │   ├── dto/                  # Data Transfer Objects
│   │   └── services/             # Servicios de aplicación
│   ├── core/                     # Configuración y utilidades core
│   ├── crud/                     # Operaciones CRUD (vacío por ahora)
│   ├── db/                       # Configuración de base de datos
│   ├── domain/                   # Entidades de dominio y lógica de negocio
│   │   ├── entities/             # Entidades del dominio
│   │   └── use_cases/            # Casos de uso del dominio
│   ├── infrastructure/           # Capa de infraestructura
│   │   ├── cache/                # Sistema de caché
│   │   ├── database/             # Modelos y configuración DB
│   │   ├── external/              # Clientes HTTP externos
│   │   └── security/             # Utilidades de seguridad
│   ├── presentation/             # Capa de presentación (API endpoints)
│   │   └── api/                  # Rutas de la API
│   ├── schemas/                  # Pydantic schemas
│   ├── utils/                    # Utilidades varias
│   └── main.py                   # Punto de entrada de FastAPI
├── tests/                        # Suite de tests
│   ├── conftest.py               # Configuración de pytest
│   ├── test_auth.py              # Tests de autenticación
│   ├── test_health.py            # Tests de health check
│   ├── test_integration.py       # Tests de integración
│   ├── test_markets.py           # Tests de mercados
│   ├── test_models.py            # Tests de modelos
│   └── README.md                 # Documentación de tests
├── alembic/                      # Migraciones de base de datos
├── scripts/                      # Scripts de utilidad
│   ├── init_db.py                # Inicialización de DB
│   ├── migrate.py                # Script de migraciones
│   └── render_migrate.py         # Migraciones para Render
├── docker-compose.yml            # Desarrollo local
├── docker-compose.test.yml       # Testing/CI
├── Dockerfile.prod               # Producción
└── .github/workflows/            # CI/CD pipelines
```

## 🌐 API Endpoints

**Base URL**: `http://localhost:8000`

### 🔐 Autenticación (`/api/v1/auth`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registrar nuevo usuario |
| POST | `/login` | Iniciar sesión (OAuth2) |
| GET | `/me` | Obtener perfil de usuario (requiere token) |

### 📈 Mercados (`/api/v1/markets`)
| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/{market_type}/overview` | Overview del mercado | ✅ Requerida |
| GET | `/{market_type}/assets` | Lista de activos (con query params) | ✅ Requerida |
| GET | `/assets/{symbol}` | Detalles de un activo | ✅ Requerida |
| GET | `/search` | Buscar activos por query | ✅ Requerida |

**Query Parameters para `/{market_type}/assets`:**
- `limit` (opcional): 1-100 (default: 50)

**Query Parameters para `/search`:**
- `q` (requerido): Query de búsqueda (mínimo 2 caracteres)
- `market_type` (opcional): `stocks` (default: todos)
- `limit` (opcional): 1-50 (default: 20)

### 🗄️ Gestión de Caché

**Nota:** Los endpoints de caché actualmente no están implementados en la API. El sistema usa caché en memoria (`MemoryMarketCache`) internamente para optimizar respuestas.

### ❤️ Health Check
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado general de la API |

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

Ejemplos con endpoints de mercado (requieren autenticación):

```bash
# Obtener overview del mercado
curl -X GET "http://localhost:8000/api/v1/markets/stocks/overview" \
  -H "Authorization: Bearer $TOKEN"

# Listar activos
curl -X GET "http://localhost:8000/api/v1/markets/stocks/assets?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Buscar activos
curl -X GET "http://localhost:8000/api/v1/markets/search?q=AAPL&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Detalles de un activo
curl -X GET "http://localhost:8000/api/v1/markets/assets/AAPL" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Configuración del Entorno

### 1. Variables de Entorno

Copia `.env.example` a `.env` y configura las siguientes variables:

```bash
# Entorno
cp .env.example .env
```

**Variables requeridas:**

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno de ejecución | `development`/`testing`/`production` |
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Clave para JWT | `your-super-secret-key-here` |
| `POLYGON_API_KEY` | API Key de Polygon.io | `your-polygon-api-key-here` |

**Variables opcionales:**

| Variable | Descripción | Default |
|----------|-------------|---------|
| `TEST_DATABASE_URL` | DB para testing | `postgresql://postgres:postgres@localhost/test_trading_app` |
| `MASSIVE_API_KEY` | API Key alternativa (Massive) | - |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración token (minutos) | `1440` |
| `ECHO_SQL` | Mostrar queries SQL | `false` |
| `DEBUG` | Modo debug | `false` |
| `RELOAD` | Auto-reload en desarrollo | `false` |
| `PROJECT_NAME` | Nombre del proyecto | `Trading App API` |
| `PROJECT_DESCRIPTION` | Descripción del proyecto | `API para la aplicación de trading` |
| `PROJECT_VERSION` | Versión del proyecto | `0.1.0` |
| `CORS_ORIGINS` | Orígenes permitidos (comma-separated) | `*` |
| `CORS_ALLOW_CREDENTIALS` | Permitir credenciales CORS | `true` |
| `CORS_ALLOW_METHODS` | Métodos HTTP permitidos | `*` |
| `CORS_ALLOW_HEADERS` | Headers permitidos | `*` |

### 2. Prioridad de APIs Externas

El sistema usa:
1. **`MASSIVE_API_KEY`** si está configurada
2. **`POLYGON_API_KEY`** como fallback

## 🚀 Inicio Rápido

### Opción 1: Docker (Recomendado)

**Requisitos:** Docker + Docker Compose

```bash
# Clonar el repositorio
git clone <repository-url>
cd trading-app-backend

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar servicios
docker compose up --build
```

**Accesos:**
- API: `http://localhost:8000`
- Postgres: `localhost:5432`
- API Docs: `http://localhost:8000/docs`

### Opción 2: Desarrollo Local

**Requisitos:** Python 3.9+

```bash
# Instalar dependencias
pip install -r requirements.txt -r requirements-dev.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar servidor de desarrollo
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Accesos:**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 🧪 Testing

### Tests Locales

```bash
# Ejecutar todos los tests
python -m pytest

# Con coverage
python -m pytest --cov=app --cov-report=html

# Tests específicos
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_markets.py -v
```

### Tests en CI/CD

Para replicar el entorno de GitHub Actions localmente:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api
```

**Estructura de Tests:**
- `conftest.py`: Configuración de pytest y fixtures
- `test_auth.py`: Tests de autenticación y registro
- `test_health.py`: Tests de health check
- `test_integration.py`: Tests de integración
- `test_markets.py`: Tests de endpoints de mercado
- `test_models.py`: Tests de modelos de datos
- `README.md`: Documentación de tests

## 🗄️ Migraciones de Base de Datos

### Entornos

- **Development/Testing**: Las tablas se crean automáticamente al iniciar
- **Production**: **NO** se crean tablas automáticamente. Se requieren migraciones

### Comandos Principales

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Ver estado actual
alembic current

# Ver historial completo
alembic history

# Revertir última migración
alembic downgrade -1
```

### Troubleshooting

**Error común:** `No module named 'app.models'`

**Solución:** Asegúrate que `alembic/env.py` importe desde la ruta correcta:
```python
from app.infrastructure.database.models import UserSQLModel
```

📖 **Guía completa:** Ver `MIGRATIONS.md` para más detalles.

## 🚀 Producción (Render)

### 1. Configuración en Render

**Variables de Entorno requeridas:**
- `DATABASE_URL` (URL de PostgreSQL de Render)
- `SECRET_KEY` (clave segura para JWT)
- `POLYGON_API_KEY` (API key para datos de mercado)
- `ENVIRONMENT=production`

### 2. Comandos de Deploy

**Build Command:**
```bash
pip install -r requirements.txt
python scripts/render_migrate.py
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. Flujo de Deploy

1. **Push a master** → GitHub Actions crea imagen Docker
2. **Deploy automático** → Render ejecuta build y start commands
3. **Migraciones** → Se aplican automáticamente durante el build
4. **API Live** → Disponible en la URL de Render

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**Archivo:** `.github/workflows/python-app.yml`

**Jobs:**

| Job | Trigger | Descripción |
|-----|---------|-------------|
| `test` | Push/PR a cualquier branch | Ejecuta tests con Docker Compose |
| `build-and-push` | Push a `master` | Build y push imagen a GHCR |

### Flujo de CI/CD

1. **Development:**
   - Push a feature branch → Tests automáticos
   - PR → Tests completos + validación

2. **Producción:**
   - Merge a `master` → Tests + Build imagen
   - Deploy automático a Render

### Imagen Docker

**Registry:** GitHub Container Registry (GHCR)
**Tag:** `latest` para el último build de `master`

---

## 📚 Documentación Adicional

- [📖 Guía de Migraciones](MIGRATIONS.md)
- [🔧 API Documentation](http://localhost:8000/docs) (cuando está corriendo)
- [🐳 Docker Configuration](docker-compose.yml)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 🆘 Soporte

Si encuentras algún problema:

1. Revisa los [issues existentes](../../issues)
2. Crea un nuevo issue con descripción detallada
3. Incluye logs y pasos para reproducir

---

**Happy Trading! 🚀📈**
