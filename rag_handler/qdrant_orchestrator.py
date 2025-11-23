"""
This module handles everything related to Qdrant.
"""

import os
import uuid
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv

load_dotenv()


class QdrantOrchestrator:
    """
    This class is responsible for orchestrating the Qdrant pipeline.
    It is responsible for:
    - Creating a collection in Qdrant if it does not exist.
    - Adding vectors to the collection.
    - Querying the collection.
    - Returning the collection.
    - etc
    """

    def __init__(self, qdrant_url: str, qdrant_key: str | None = None):
        """
        Initialize Qdrant client.

        Args:
            qdrant_url: Qdrant server URL (e.g., http://localhost:6333)
            qdrant_key: API key (optional, None if no authentication)
        """
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        self.collection_name: str = "QdrantRagCollection"

    def create_collection(self):
        """
        This function creates a collection in Qdrant if it does not exist.
        """
        # Try to fetch the collection status
        try:
            self.qdrant_client.get_collection(self.collection_name)
            print(
                f"Skipping creating collection; '{self.collection_name}' already exists."
            )
        except UnexpectedResponse as exc:
            # If collection does not exist, an error will be thrown, so we create the collection
            if exc.status_code == 404:
                print(
                    f"Collection '{self.collection_name}' not found. Creating it now..."
                )

                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=os.getenv("EMBEDDING_DIMENSION"),
                        distance=models.Distance.COSINE,
                    ),
                )

                print(f"Collection '{self.collection_name}' created successfully.")
            else:
                print(f"Error while checking collection: {exc}")

    def ingest_to_qdrant(self, collection_name, embedded_data):
        """
        This function ingests the data to Qdrant, as in embedded data -> Vector in Qdrant.

        Args:
            collection_name: Name of the collection to ingest to.
            embedded_data: List of dictionaries containing file info, chunks, and embeddings.
                           Format: [{"file": "name", "chunks": [...], "embeddings": [...]}, ...]
        """
        points = []
        for file_entry in embedded_data:
            file_name = file_entry["file"]
            chunks = file_entry["chunks"]
            embeddings = file_entry["embeddings"]

            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk,
                            "source_file": file_name,
                            "chunk_index": i,
                        },
                    )
                )

        self.qdrant_client.upsert(collection_name=collection_name, points=points)


if __name__ == "__main__":
    # Get Qdrant URL from env or use default
    qdrant_port = os.getenv("QDRANT_HTTP_PORT", "6333")
    qdrant_host = os.getenv("QDRANT_URL", "http://localhost")
    qdrant_url = f"{qdrant_host}:{qdrant_port}"

    # API key is optional (None if not set)
    qdrant_key = os.getenv("QDRANT_API_KEY")  # Returns None if not set

    qdrant_orchestrator = QdrantOrchestrator(
        qdrant_url=qdrant_url, qdrant_key=qdrant_key
    )
    qdrant_orchestrator.create_collection()
