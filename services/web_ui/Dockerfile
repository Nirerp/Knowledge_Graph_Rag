# Graph RAG Web UI Dockerfile
# Uses uv for dependency management

FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set working directory
WORKDIR /app

# Copy service-specific dependency file (lightweight: Flask + dotenv)
COPY services/web_ui/pyproject.toml ./pyproject.toml

# Install dependencies only for web_ui service
RUN uv sync --no-dev

# Copy source code (web UI and the agent it calls)
COPY services/web_ui/src/ ./services/web_ui/src/
COPY services/rag_api/src/ ./services/rag_api/src/
COPY services/__init__.py ./services/
COPY services/web_ui/__init__.py ./services/web_ui/
COPY services/rag_api/__init__.py ./services/rag_api/

# Expose port
EXPOSE 5000

# Run the Flask app
CMD ["uv", "run", "python", "-m", "flask", "--app", "services.web_ui.src.app:app", "run", "--host", "0.0.0.0", "--port", "5000"]

