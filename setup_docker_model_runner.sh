#!/bin/bash
# Docker Model Runner + Dagger Setup Script
# Based on: https://dagger.io/blog/docker-model-runner

set -e

echo "🤖 Setting up Docker Model Runner + Dagger Integration"
echo "======================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check Docker Desktop version (needs 4.40+)
DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [[ "$(printf '%s\n' "$DOCKER_VERSION" "4.40" | sort -V | head -n1)" != "4.40" ]]; then
    echo "⚠️ Docker Desktop version $DOCKER_VERSION detected."
    echo "💡 Docker Model Runner requires Docker Desktop 4.40 or later."
    echo "   Please update Docker Desktop and enable Model Runner in Settings > Features in development."
fi

echo "✅ Docker is running (version: $DOCKER_VERSION)"

# Check if Model Runner is available
if ! docker model version > /dev/null 2>&1; then
    echo "❌ Docker Model Runner is not available."
    echo "💡 Please enable Model Runner in Docker Desktop Settings > Features in development."
    exit 1
fi

echo "✅ Docker Model Runner is available"

# Pull a default model
DEFAULT_MODEL="index.docker.io/ai/qwen2.5:7B-F16"
echo ""
echo "📥 Pulling default model: $DEFAULT_MODEL"
echo "   (This may take a while - model is ~14GB)"

if docker model ls | grep -q "qwen2.5"; then
    echo "✅ Model already available locally"
else
    docker model pull $DEFAULT_MODEL
    echo "✅ Model pulled successfully"
fi

# Set up environment variables
echo ""
echo "🔧 Configuring environment variables..."

# Create or update .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

# Set environment variables
export OPENAI_BASE_URL="http://model-runner.docker.internal/engines/llama.cpp/v1/"
export OPENAI_DISABLE_STREAMING="true"
export OPENAI_MODEL="$DEFAULT_MODEL"

# Add to .env file (for persistence)
if ! grep -q "OPENAI_BASE_URL" "$ENV_FILE"; then
    echo "OPENAI_BASE_URL=http://model-runner.docker.internal/engines/llama.cpp/v1/" >> "$ENV_FILE"
fi
if ! grep -q "OPENAI_DISABLE_STREAMING" "$ENV_FILE"; then
    echo "OPENAI_DISABLE_STREAMING=true" >> "$ENV_FILE"
fi
if ! grep -q "OPENAI_MODEL" "$ENV_FILE"; then
    echo "OPENAI_MODEL=$DEFAULT_MODEL" >> "$ENV_FILE"
fi

echo "✅ Environment variables configured"
echo "   OPENAI_BASE_URL: $OPENAI_BASE_URL"
echo "   OPENAI_DISABLE_STREAMING: $OPENAI_DISABLE_STREAMING"
echo "   OPENAI_MODEL: $OPENAI_MODEL"

# Test the setup
echo ""
echo "🧪 Testing the setup..."

# Start Docker Model Runner if not running
if ! docker ps | grep -q "model-runner"; then
    echo "🚀 Starting Docker Model Runner..."
    docker model run $DEFAULT_MODEL
    echo "✅ Docker Model Runner started"
else
    echo "✅ Docker Model Runner is already running"
fi

# Wait a moment for the model to load
echo "⏳ Waiting for model to initialize..."
sleep 5

# Test connection
echo "🔍 Testing connection to model..."
if curl -s "http://model-runner.docker.internal/engines/llama.cpp/v1/models" > /dev/null; then
    echo "✅ Successfully connected to Docker Model Runner"
else
    echo "⚠️ Could not connect to model runner (this is normal if it's still starting)"
    echo "   The model may take a few minutes to load on first run."
fi

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "🚀 You can now use Dagger with local AI models:"
echo ""
echo "   # Start Dagger shell"
echo "   dagger"
echo ""
echo "   # Use LLM in Dagger (example)"
echo "   llm | with-prompt \"Create a simple hello world function\" | sync"
echo ""
echo "   # Or use our custom integration"
echo "   cd dagger-integration"
echo "   dagger call analyze-codebase --source=. --task=review"
echo ""
echo "📚 For more examples, see:"
echo "   - dagger-integration/examples.py"
echo "   - dagger-integration/ci_pipeline.sh"
echo "   - https://docs.dagger.io/quickstart/agent"
echo ""
echo "💡 Available models:"
docker model ls
echo ""
echo "🔄 To pull additional models:"
echo "   docker model pull index.docker.io/ai/gemma3:4B-F16"
echo "   docker model pull index.docker.io/ai/llama3.2:3B-F16"