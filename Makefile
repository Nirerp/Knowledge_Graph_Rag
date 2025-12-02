.PHONY: help start stop clean build dev logs logs-ollama logs-api logs-ui test-imports

# Use a disk-backed temp directory for Kind image loading (avoids /tmp tmpfs limits)
KIND_TMPDIR ?= ~/.kind-tmp

# Default target
help:
	@echo "Graph RAG - Makefile Commands"
	@echo ""
	@echo "Development (Docker Compose):"
	@echo "  make dev          - Start Qdrant and Neo4j for local development"
	@echo "  make dev-all      - Start all services with Docker Compose"
	@echo "  make dev-stop     - Stop all Docker Compose services"
	@echo ""
	@echo "Kubernetes (Kind + Helm):"
	@echo "  make start        - Create Kind cluster and deploy all services"
	@echo "  make stop         - Stop and delete Kind cluster"
	@echo "  make build        - Build Docker images for all services"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs         - View RAG API logs"
	@echo "  make logs-ollama  - View Ollama logs"
	@echo "  make logs-ui      - View Web UI logs"
	@echo "  make clean        - Remove all containers, images, and Kind cluster"
	@echo "  make test-imports - Test Python imports work correctly"
	@echo ""
	@echo "URLs (after start):"
	@echo "  Web UI:      http://localhost:5000"
	@echo "  RAG API:     http://localhost:8000"
	@echo "  Qdrant:      http://localhost:6333/dashboard"
	@echo "  Neo4j:       http://localhost:7474"
	@echo "  Ollama:      http://localhost:11434"

# ==================== Development (Docker Compose) ====================

dev:
	@echo "Starting Qdrant and Neo4j for development..."
	docker compose up -d qdrant neo4j
	@echo ""
	@echo "Services ready:"
	@echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
	@echo "  Neo4j Browser:    http://localhost:7474"
	@echo ""
	@echo "Run the agent locally with: uv run python -m services.rag_api.src.core.agent"
	@echo "Run the Flask UI with: uv run python -m flask --app services.web_ui.src.app:app run"

dev-all:
	@echo "Building and starting all services..."
	docker compose up --build -d
	@echo ""
	@echo "Services starting..."
	@echo "Note: Ollama will pull models on first start (may take several minutes)"
	@echo ""
	@echo "Check status with: docker compose ps"
	@echo "View logs with: docker compose logs -f"

dev-stop:
	@echo "Stopping all services..."
	docker compose down

# ==================== Kubernetes (Kind + Helm) ====================

start:
	@echo "========================================="
	@echo "Starting Graph RAG on Kubernetes (Kind)"
	@echo "========================================="
	@echo ""
	@echo "Using temporary directory for Kind image load: $(KIND_TMPDIR)"
	mkdir -p $(KIND_TMPDIR)
	@echo "Step 1: Creating Kind cluster..."
	kind create cluster --config deploy/kind-config.yaml 2>/dev/null || echo "Cluster already exists"
	@echo ""
	@echo "Step 2: Building Docker images..."
	$(MAKE) build
	@echo ""
	@echo "Step 3: Loading images into Kind..."
	TMPDIR=$(KIND_TMPDIR) kind load docker-image graph-rag/rag-api:latest --name graph-rag
	TMPDIR=$(KIND_TMPDIR) kind load docker-image graph-rag/web-ui:latest --name graph-rag
	TMPDIR=$(KIND_TMPDIR) kind load docker-image graph-rag/ollama:latest --name graph-rag
	@echo ""
	@echo "Step 4: Installing Helm chart..."
	helm upgrade --install graph-rag deploy/charts/graph-rag/ --wait --timeout 20m
	@echo ""
	@echo "========================================="
	@echo "Graph RAG is ready!"
	@echo "========================================="
	@echo ""
	@echo "Services:"
	@echo "  Web UI:      http://localhost:5000"
	@echo "  RAG API:     http://localhost:8000/docs"
	@echo "  Qdrant:      http://localhost:6333/dashboard"
	@echo "  Neo4j:       http://localhost:7474"
	@echo "  Ollama:      http://localhost:11434"
	@echo ""
	@echo "Note: Ollama is pulling models. Check status with: make logs-ollama"

stop:
	@echo "Stopping Graph RAG..."
	helm uninstall graph-rag 2>/dev/null || true
	kind delete cluster --name graph-rag 2>/dev/null || true
	@echo "Stopped."

build:
	@echo "Building Docker images..."
	docker build -t graph-rag/rag-api:latest -f services/rag_api/Dockerfile .
	docker build -t graph-rag/web-ui:latest -f services/web_ui/Dockerfile .
	docker build -t graph-rag/ollama:latest -f services/ollama/Dockerfile .
	@echo "Images built successfully."

# ==================== Logs ====================

logs:
	kubectl logs -f -l app=rag-api

logs-ollama:
	kubectl logs -f -l app=ollama

logs-ui:
	kubectl logs -f -l app=web-ui

logs-all:
	docker compose logs -f

# ==================== Cleanup ====================

clean:
	@echo "Cleaning up..."
	helm uninstall graph-rag 2>/dev/null || true
	kind delete cluster --name graph-rag 2>/dev/null || true
	docker compose down -v 2>/dev/null || true
	docker rmi graph-rag/rag-api:latest graph-rag/web-ui:latest graph-rag/ollama:latest 2>/dev/null || true
	@echo "Cleanup complete."

# ==================== Testing ====================

test-imports:
	@echo "Testing Python imports..."
	uv run python -c "\
from services.rag_api.src.core.config import AGENT_SYSTEM_PROMPT, GRAPH_EXTRACTION_PROMPT; \
from services.rag_api.src.models.responses import AgentResponse; \
from services.rag_api.src.models.schemas import GraphComponents; \
from services.rag_api.src.core.retrieval import retrieve_knowledge; \
print('All imports successful!')"

