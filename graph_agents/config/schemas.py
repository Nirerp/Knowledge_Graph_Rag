from pydantic import BaseModel, Field
from typing import List


class AgentResponse(BaseModel):
    """Structured response format for the agent"""

    answer: str = Field(
        description="The main answer to the user's question, without inline citations"
    )
    sources: List[str] = Field(
        description="List of sources cited, in format 'filename, Chunk N'"
    )
    chunks_retrieved: int = Field(
        description="Number of text chunks retrieved from Qdrant vector search"
    )
    relationships_found: int = Field(
        description="Number of entity relationships found in Neo4j graph"
    )
