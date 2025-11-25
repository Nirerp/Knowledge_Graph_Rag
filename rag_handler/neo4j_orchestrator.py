from neo4j import GraphDatabase
from typing import Tuple
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jOrchestrator:
    def __init__(
        self, neo4j_url: str, auth: Tuple[str, str], neo4j_key: str | None = None
    ):
        self.neo4j_client = GraphDatabase.driver(neo4j_url, auth=auth)

    def ingest_to_neo4j(self, nodes, relationships, chunk_node_mapping=None):
        """
        Ingest nodes, relationships, and chunks into Neo4j.

        Args:
            nodes: Dict of entity names to UUIDs
            relationships: List of relationships between entities
            chunk_node_mapping: Dict mapping chunk UUIDs to their content and entities
        """

        with self.neo4j_client.session() as session:
            # 1. Create Entity nodes (EXISTING)
            for name, node_id in nodes.items():
                session.run(
                    "CREATE (n:Entity {id: $id, name: $name})", id=node_id, name=name
                )

            # 2. Create Chunk nodes (NEW)
            if chunk_node_mapping:
                for chunk_id, chunk_data in chunk_node_mapping.items():
                    session.run(
                        "CREATE (c:Chunk {id: $id, text: $text, source_file: $source_file, chunk_index: $chunk_index})",
                        id=chunk_id,
                        text=chunk_data["text"],
                        source_file=chunk_data["source_file"],
                        chunk_index=chunk_data["chunk_index"],
                    )

                    # 3. Create MENTIONS relationships from Chunk to Entity (NEW)
                    for entity_id in set(
                        chunk_data["entity_ids"]
                    ):  # Use set to avoid duplicates
                        session.run(
                            "MATCH (c:Chunk {id: $chunk_id}), (e:Entity {id: $entity_id}) "
                            "CREATE (c)-[:MENTIONS]->(e)",
                            chunk_id=chunk_id,
                            entity_id=entity_id,
                        )

            # 4. Create Entity relationships (EXISTING)
            # Note: Neo4j relationship types must be valid identifiers (alphanumeric + underscore)
            # We'll sanitize the relationship type and use it as the actual relationship type
            for relationship in relationships:
                rel_type = relationship["type"]
                # Sanitize relationship type for Neo4j (remove spaces, special chars, make uppercase)
                # Keep it readable but valid as a Neo4j relationship type
                sanitized_type = (
                    rel_type.replace(" ", "_").replace("-", "_").replace(".", "_")
                )
                sanitized_type = "".join(
                    c for c in sanitized_type if c.isalnum() or c == "_"
                )
                if not sanitized_type:
                    sanitized_type = (
                        "RELATES_TO"  # Fallback if sanitization results in empty string
                    )

                # Use dynamic relationship type with additional metadata
                query = (
                    f"MATCH (a:Entity {{id: $source_id}}), (b:Entity {{id: $target_id}}) "
                    f"CREATE (a)-[:{sanitized_type} {{original_type: $type, source_file: $source_file}}]->(b)"
                )

                session.run(
                    query,
                    source_id=relationship["source"],
                    target_id=relationship["target"],
                    type=rel_type,
                    source_file=relationship.get("source_file", None),
                )

        return nodes


if __name__ == "__main__":
    NEO4J_URI = f"{os.getenv('NEO4J_URL')}:{os.getenv('NEO4J_BOLT_PORT')}"
    NEO4J_USERNAME, NEO4J_PASSWORD = os.getenv("NEO4J_AUTH").split("/")
    neo4j_orchestrator = Neo4jOrchestrator(
        neo4j_url=NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
