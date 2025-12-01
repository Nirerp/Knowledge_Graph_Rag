"""
Ingestion endpoint for processing and ingesting documents.
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class IngestResponse(BaseModel):
    success: bool
    files_processed: int
    nodes_created: int
    relationships_created: int
    chunks_embedded: int


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    """
    Process all files in raw_data/ folder and ingest them into Qdrant and Neo4j.
    
    This endpoint:
    1. Reads all files from raw_data/
    2. Chunks and embeds the content
    3. Extracts entities and relationships using LLM
    4. Stores vectors in Qdrant
    5. Stores graph in Neo4j
    """
    try:
        from services.rag_api.src.ingestion.file_reader import FileReader
        from services.rag_api.src.ingestion.chunker_embedder import ChunkerEmbedder
        from services.rag_api.src.ingestion.orchestration import Orchestrator
        from services.rag_api.src.storage.neo4j_client import Neo4jOrchestrator
        from services.rag_api.src.storage.qdrant_client import QdrantOrchestrator
        
        # Get configuration
        raw_data_folder = os.getenv("RAW_DATA_FOLDER", "./raw_data")
        llm_model = os.getenv("LLM_MODEL")
        llm_api_key = os.getenv("LLM_API_KEY")
        qdrant_url = f"{os.getenv('QDRANT_URL')}:{os.getenv('QDRANT_HTTP_PORT', '6333')}"
        neo4j_url = f"{os.getenv('NEO4J_URL')}:{os.getenv('NEO4J_BOLT_PORT')}"
        neo4j_auth = tuple(os.getenv("NEO4J_AUTH").split("/"))
        
        # 1. Read files
        file_reader = FileReader(raw_data_folder)
        all_files = file_reader.read_files()
        
        total_files = sum(len(v) for v in all_files.values())
        if total_files == 0:
            raise HTTPException(status_code=400, detail="No files found in raw_data/ folder")
        
        # 2. Chunk and embed
        chunker = ChunkerEmbedder(
            all_files=all_files,
            chunk_size=int(os.getenv("CHUNK_SIZE", 512)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 100))
        )
        
        # Process all file types
        chunked_data = []
        chunked_data.extend(chunker.chunk_pdf())
        chunked_data.extend(chunker.chunk_text())
        chunked_data.extend(chunker.chunk_markdown())
        
        embedded_data = chunker.embed_chunks(chunked_data)
        
        # 3. Extract graph components
        orchestrator = Orchestrator(llm_model=llm_model, llm_api_key=llm_api_key)
        nodes, relationships, chunk_node_mapping = orchestrator.extract_graph_components(chunked_data)
        
        # 4. Ingest to Qdrant
        qdrant_client = QdrantOrchestrator(qdrant_url=qdrant_url)
        qdrant_client.create_collection()
        qdrant_client.ingest_to_qdrant("QdrantRagCollection", embedded_data, chunk_node_mapping)
        
        # 5. Ingest to Neo4j
        neo4j_client = Neo4jOrchestrator(neo4j_url=neo4j_url, auth=neo4j_auth)
        neo4j_client.ingest_to_neo4j(nodes, relationships, chunk_node_mapping)
        
        return IngestResponse(
            success=True,
            files_processed=total_files,
            nodes_created=len(nodes),
            relationships_created=len(relationships),
            chunks_embedded=len(chunk_node_mapping)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

