"""
FastAPI backend for the Graph RAG system.
"""

import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.rag_api.src.core.config import AGENT_SYSTEM_PROMPT
from services.rag_api.src.models.responses import AgentResponse
from services.rag_api.src.core.retrieval import retrieve_knowledge
from services.rag_api.src.api.v1.ingest import router as ingest_router

from agents import Agent, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

# Disable tracing
set_tracing_disabled(True)
os.environ["LITELLM_TELEMETRY"] = "False"

load_dotenv()

# Global agent instance
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    global agent
    
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")
    
    agent = Agent(
        name="Answering_Agent",
        instructions=AGENT_SYSTEM_PROMPT,
        model=LitellmModel(model=model, api_key=api_key),
        tools=[retrieve_knowledge],
    )
    
    print(f"RAG API initialized with model: {model}")
    yield
    print("RAG API shutting down")


app = FastAPI(
    title="Graph RAG API",
    description="Hybrid RAG system combining vector search and knowledge graphs",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest_router, prefix="/api/v1", tags=["ingestion"])


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    success: bool
    answer: str
    sources: list[str]
    chunks_retrieved: int
    relationships_found: int


class HealthResponse(BaseModel):
    status: str
    service: str
    model: str


def parse_agent_response(output_str: str) -> dict:
    """Parse the agent's JSON response into structured data."""
    import json
    
    try:
        json_start = output_str.find("{")
        json_end = output_str.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = output_str[json_start:json_end]
            response_data = json.loads(json_str)
            response = AgentResponse(**response_data)
            return {
                "success": True,
                "answer": response.answer,
                "sources": response.sources,
                "chunks_retrieved": response.chunks_retrieved,
                "relationships_found": response.relationships_found
            }
    except (json.JSONDecodeError, KeyError, TypeError, Exception):
        pass
    
    return {
        "success": True,
        "answer": output_str,
        "sources": [],
        "chunks_retrieved": 0,
        "relationships_found": 0
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="rag-api",
        model=os.getenv("LLM_MODEL", "unknown")
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - send a message and get a response."""
    global agent
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await Runner.run(agent, request.message)
        response = parse_agent_response(str(result.final_output))
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Graph RAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

