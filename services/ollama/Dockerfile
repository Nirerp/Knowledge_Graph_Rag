# Ollama Dockerfile with auto-pull models
FROM ollama/ollama:latest

# Install curl for the startup script
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the startup script (path relative to build context which is project root)
COPY services/ollama/start.sh /start.sh
RUN chmod +x /start.sh

# Expose Ollama port
EXPOSE 11434

# Use the startup script as entrypoint
ENTRYPOINT ["/start.sh"]

