#!/bin/bash

# Model names are passed from Helm values.yaml via environment variables
LLM_MODEL="${OLLAMA_LLM_MODEL:-llama3.2:3b}"
EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-mxbai-embed-large:335m}"

# Start Ollama server in background
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "Ollama is ready!"

# Pull required models
echo "Pulling LLM model: ${LLM_MODEL}..."
ollama pull "${LLM_MODEL}"

echo "Pulling embedding model: ${EMBEDDING_MODEL}..."
ollama pull "${EMBEDDING_MODEL}"

echo "All models pulled successfully!"

# Keep the container running
wait
