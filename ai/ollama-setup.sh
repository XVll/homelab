#!/bin/bash
# ============================================================================
# OLLAMA MODEL SETUP SCRIPT
# ============================================================================
# Helper script to pull and manage Ollama models
# Run this after deploying Ollama to download CPU-optimized models
# ============================================================================

set -e

echo "🤖 Ollama Model Setup"
echo "===================="
echo ""

# Check if Ollama is running
if ! docker ps | grep -q ollama; then
    echo "❌ Error: Ollama container is not running"
    echo "   Please deploy Ollama first: docker compose up -d ollama"
    exit 1
fi

echo "✓ Ollama is running"
echo ""

# Function to pull model
pull_model() {
    local model=$1
    local size=$2
    echo "📦 Pulling $model ($size)..."
    docker exec ollama ollama pull "$model"
    echo "✓ $model downloaded"
    echo ""
}

echo "This script will download the following CPU-optimized models:"
echo "  1. llama3.2:1b (~1.3GB)   - Fastest, great for testing"
echo "  2. llama3.2:3b (~2.0GB)   - Balanced speed/quality"
echo "  3. phi3:mini (~2.3GB)     - Microsoft's efficient model"
echo "  4. qwen2.5:3b (~2.0GB)    - Good general-purpose model"
echo ""
echo "Total download size: ~7.6GB"
echo ""

read -p "Download all models? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    pull_model "llama3.2:1b" "1.3GB"
    pull_model "llama3.2:3b" "2.0GB"
    pull_model "phi3:mini" "2.3GB"
    pull_model "qwen2.5:3b" "2.0GB"

    echo "✅ All models downloaded!"
    echo ""
    echo "You can now use these models via:"
    echo "  - LiteLLM API: http://10.10.10.115:4000"
    echo "  - Open WebUI: https://chat.onurx.com"
    echo ""
    echo "Model names in LiteLLM:"
    echo "  - llama3.2:1b"
    echo "  - llama3.2:3b"
    echo "  - phi3:mini"
    echo "  - qwen2.5:3b"
else
    echo ""
    echo "To pull models manually:"
    echo "  docker exec ollama ollama pull llama3.2:1b"
    echo "  docker exec ollama ollama pull llama3.2:3b"
    echo "  docker exec ollama ollama pull phi3:mini"
    echo "  docker exec ollama ollama pull qwen2.5:3b"
fi

echo ""
echo "📋 Useful Ollama commands:"
echo "  List models:    docker exec ollama ollama list"
echo "  Remove model:   docker exec ollama ollama rm <model>"
echo "  Test model:     docker exec ollama ollama run llama3.2:1b"
echo ""
