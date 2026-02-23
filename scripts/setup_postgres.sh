#!/bin/bash
# Script para configurar PostgreSQL local para testing

echo "🚀 Configurando PostgreSQL local para testing..."

# Verificar si PostgreSQL está instalado
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew no está instalado. Por favor instálalo primero."
    exit 1
fi

if ! brew list postgresql@15 &> /dev/null; then
    echo "📦 Instalando PostgreSQL..."
    brew install postgresql@15
fi

# Iniciar PostgreSQL
echo "🔄 Iniciando PostgreSQL..."
brew services start postgresql@15

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 3

# Crear usuario y base de datos
echo "🗄️ Creando usuario y base de datos..."
/usr/local/Cellar/postgresql@15/15.15_1/bin/psql -U leo postgres -c "CREATE USER postgres WITH SUPERUSER;" 2>/dev/null || echo "✅ Usuario postgres ya existe"
/usr/local/Cellar/postgresql@15/15.15_1/bin/psql -U postgres -c "CREATE DATABASE trading_app;" 2>/dev/null || echo "✅ Base de datos trading_app ya existe"

echo "✅ PostgreSQL configurado exitosamente!"
echo "📊 Base de datos: postgresql://postgres:postgres@localhost:5432/trading_app"
echo "🧪 Ejecuta los tests con: python -m pytest tests/test_auth.py -v"
