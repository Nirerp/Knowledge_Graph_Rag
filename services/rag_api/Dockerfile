# Graph RAG API Dockerfile
# Uses uv for dependency management

FROM python:3.13-slim

# Install system dependencies for PDF processing (docling/OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set working directory
WORKDIR /app

# Copy service-specific dependency file (avoid pulling heavy root deps like torch/easyocr)
COPY services/rag_api/pyproject.toml ./pyproject.toml

# Install dependencies only for rag_api service
RUN uv sync --no-dev

# Copy source code (only what this service needs)
COPY services/rag_api/src/ ./services/rag_api/src/
COPY services/__init__.py ./services/
COPY services/rag_api/__init__.py ./services/rag_api/

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uv", "run", "uvicorn", "services.rag_api.src.main:app", "--host", "0.0.0.0", "--port", "8000"]

