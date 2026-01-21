# Migraciones de Base de Datos con Alembic

## 🎯 Overview

Este proyecto utiliza **Alembic** para manejar migraciones de base de datos. Las migraciones aseguran que la estructura de la base de datos sea consistente y versionada.

## 📋 Entornos

### Desarrollo/Testing
- **Creación automática**: Las tablas se crean automáticamente al iniciar la app
- **No requiere migraciones**: Ideal para desarrollo rápido

### Producción
- **Sin creación automática**: Las tablas NO se crean automáticamente
- **Requiere migraciones**: Se debe ejecutar `alembic upgrade head`

## 🚀 Comandos Básicos

### Crear nueva migración
```bash
# Generar migración basada en cambios en modelos
alembic revision --autogenerate -m "Descripción del cambio"

# Crear migración manual (vacía)
alembic revision -m "Descripción del cambio"
```

### Aplicar migraciones
```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Aplicar migración específica
alembic upgrade +1
alembic upgrade <revision_id>
```

### Revertir migraciones
```bash
# Revertir última migración
alembic downgrade -1

# Revertir a migración específica
alembic downgrade <revision_id>

# Revertir todo (base vacía)
alembic downgrade base
```

### Ver estado
```bash
# Ver migraciones aplicadas
alembic current

# Ver historial de migraciones
alembic history

# Ver migraciones pendientes
alembic heads
```

## 🐳 Docker - Producción

### Render PostgreSQL (Recomendado)
Render hace el despliegue automático después del CI. Solo necesitas configurar:

#### Build Command en Render:
```bash
pip install -r requirements.txt
python scripts/render_migrate.py
```

#### Start Command en Render:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Variables de Entorno en Render:
```bash
DATABASE_URL=postgresql://...
SECRET_KEY=...
POLYGON_API_KEY=...
ENVIRONMENT=production
```

### Docker Local (Opcional)
Para desarrollo local o testing:
```bash
docker-compose -f docker-compose.prod.yml up --build
```

## 🔧 Configuración

### Variables de Entorno
- `ENVIRONMENT=production`: Deshabilita creación automática de tablas
- `DATABASE_URL`: URL de conexión a la base de datos

### Archivos Importantes
- `alembic.ini`: Configuración de Alembic
- `alembic/env.py`: Entorno de ejecución de migraciones
- `alembic/versions/`: Archivos de migración

## 📝 Flujo de Trabajo

### 1. Desarrollo
```bash
# Modificar modelos en app/models/
# Generar migración
alembic revision --autogenerate -m "Add new field to User"

# Aplicar localmente (opcional, se crea automáticamente)
alembic upgrade head
```

### 2. Producción
```bash
# Desplegar con migraciones
docker-compose --profile migrate up --build
```

### 3. Revertir si es necesario
```bash
# Si algo sale mal
alembic downgrade -1
# Fix the issue
alembic revision --autogenerate -m "Fix issue"
alembic upgrade head
```

## ⚠️ Importante

- **Nunca** modificar migraciones existentes que ya fueron aplicadas
- **Siempre** revisar migraciones autogeneradas antes de aplicar
- **Backup** de base de datos antes de migraciones grandes
- **Testing** en desarrollo antes de producción

## 🆘 Troubleshooting

### Error: "target_metadata is None"
```bash
# Asegúrate de importar todos los modelos en alembic/env.py
from app.models.user import User
# ... otros modelos
```

### Error: "No such table"
```bash
# Ejecuta migraciones
alembic upgrade head
```

### Error: "Can't import module"
```bash
# Verifica PYTHONPATH y sys.path en alembic/env.py
sys.path.append(str(Path(__file__).parent.parent))
```
