#!/bin/bash
# Script to setup Redis locally for development

echo "🚀 Setting up Redis locally for development..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install it first."
    exit 1
fi

# Check if Redis is installed
if ! brew list redis &> /dev/null; then
    echo "📦 Installing Redis..."
    brew install redis
fi

# Start Redis
echo "🔄 Starting Redis..."
brew services start redis

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 2

# Test Redis connection
if redis-cli ping &> /dev/null; then
    echo "✅ Redis is running successfully!"
    echo "📊 Redis connection: redis://localhost:6379/0"
    echo "🧪 Test with: redis-cli ping"
else
    echo "❌ Redis failed to start"
    echo "🔧 Try manually: brew services restart redis"
    exit 1
fi

echo "✅ Redis setup completed!"
echo "🔧 To stop Redis: brew services stop redis"
echo "🔧 To restart Redis: brew services restart redis"
