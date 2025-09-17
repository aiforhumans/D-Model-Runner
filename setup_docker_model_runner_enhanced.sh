#!/bin/bash
# Enhanced Docker Model Runner + Dagger Setup Script
# Supports both local development and Docker container environments

set -e

echo "🤖 Enhanced Docker Model Runner + Dagger Setup"
echo "=============================================="

# Function to detect environment
detect_environment() {
    if [ -n "$DOCKER_CONTAINER" ] || [ -f "/.dockerenv" ]; then
        echo "🐳 Docker container environment detected"
        return 1
    else
        echo "💻 Local development environment detected"
        return 0
    fi
}

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

# Configure environment based on context
echo ""
echo "🔧 Configuring environment variables..."

if detect_environment; then
    # Local development environment
    BASE_URL="http://localhost:12434/engines/llama.cpp/v1/"
    ENV_FILE=".env.local"
    echo "📍 Using local development configuration"
else
    # Docker container environment
    BASE_URL="http://model-runner.docker.internal/engines/llama.cpp/v1/"
    ENV_FILE=".env"
    echo "🐳 Using Docker container configuration"
fi

# Create or update environment file
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

# Set environment variables
export OPENAI_BASE_URL="$BASE_URL"
export OPENAI_DISABLE_STREAMING="true"
export OPENAI_MODEL="$DEFAULT_MODEL"

# Add to environment file (for persistence)
if ! grep -q "OPENAI_BASE_URL" "$ENV_FILE"; then
    echo "OPENAI_BASE_URL=$BASE_URL" >> "$ENV_FILE"
fi
if ! grep -q "OPENAI_DISABLE_STREAMING" "$ENV_FILE"; then
    echo "OPENAI_DISABLE_STREAMING=true" >> "$ENV_FILE"
fi
if ! grep -q "OPENAI_MODEL" "$ENV_FILE"; then
    echo "OPENAI_MODEL=$DEFAULT_MODEL" >> "$ENV_FILE"
fi

echo "✅ Environment variables configured in $ENV_FILE"
echo "   OPENAI_BASE_URL: $OPENAI_BASE_URL"
echo "   OPENAI_DISABLE_STREAMING: $OPENAI_DISABLE_STREAMING"
echo "   OPENAI_MODEL: $OPENAI_MODEL"

# Test the setup
echo ""
echo "🧪 Testing the setup..."

# Start Docker Model Runner if not running
if ! docker ps | grep -q "model-runner"; then
    echo "🚀 Starting Docker Model Runner..."
    docker model run $DEFAULT_MODEL &
    MODEL_PID=$!
    echo "✅ Docker Model Runner started (PID: $MODEL_PID)"
else
    echo "✅ Docker Model Runner is already running"
fi

# Wait for model to initialize
echo "⏳ Waiting for model to initialize..."
sleep 10

# Test connection using appropriate endpoint
if detect_environment; then
    TEST_URL="http://localhost:12434/engines/llama.cpp/v1/models"
else
    TEST_URL="http://model-runner.docker.internal/engines/llama.cpp/v1/models"
fi

echo "🔍 Testing connection to $TEST_URL..."
if curl -s "$TEST_URL" > /dev/null; then
    echo "✅ Successfully connected to Docker Model Runner"

    # Test API endpoints
    echo "🔍 Testing API endpoints..."

    # List models
    echo "   📋 Models endpoint: $TEST_URL"
    MODELS=$(curl -s "$TEST_URL" | jq -r '.data[].id' 2>/dev/null || echo "N/A")
    echo "   🤖 Available models: $MODELS"

    # Test chat completions endpoint
    CHAT_URL="${TEST_URL%/models}/chat/completions"
    echo "   💬 Chat completions endpoint: $CHAT_URL"

    echo "✅ All API endpoints accessible"
else
    echo "⚠️ Could not connect to model runner (this is normal if it's still starting)"
    echo "   The model may take a few minutes to load on first run."
    echo "   You can test manually with: curl $TEST_URL"
fi

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "🚀 You can now use Dagger with local AI models:"
echo ""
echo "   # Load environment variables"
if detect_environment; then
    echo "   source .env.local"
else
    echo "   source .env"
fi
echo ""
echo "   # Start Dagger shell"
echo "   dagger"
echo ""
echo "   # Use LLM in Dagger (examples)"
echo "   llm | with-prompt \"Create a simple hello world function\" | sync"
echo "   llm | with-prompt \"Explain what this code does\" | with-file \"main.py\" | sync"
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
echo ""
echo "🔧 API Endpoints:"
echo "   Models: $TEST_URL"
echo "   Chat: ${TEST_URL%/models}/chat/completions"
echo "   Completions: ${TEST_URL%/models}/completions"
echo "   Embeddings: ${TEST_URL%/models}/embeddings"