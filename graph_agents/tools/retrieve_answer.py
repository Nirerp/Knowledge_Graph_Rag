from agents import function_tool
import os
from dotenv import load_dotenv
import warnings
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from neo4j_graphrag.retrievers import QdrantNeo4jRetriever
from litellm import embedding

# Suppress Qdrant insecure connection warning
warnings.filterwarnings("ignore", message="Api key is used with an insecure connection")

load_dotenv()

# --- Configuration ---
NEO4J_URI = f"{os.getenv('NEO4J_URL')}:{os.getenv('NEO4J_BOLT_PORT')}"
NEO4J_AUTH = tuple(os.getenv("NEO4J_AUTH").split("/"))
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "QdrantRagCollection"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# --- Helper Functions (The Pipeline) ---


def get_embedding(text: str):
    """Step 1: Embed the query"""
    response = embedding(model=EMBEDDING_MODEL, input=[text])
    return response.data[0]["embedding"]


def search_qdrant(neo4j_driver, qdrant_client, query_vector, top_k=5):
    """Step 2: Search Qdrant for relevant chunks"""
    retriever = QdrantNeo4jRetriever(
        driver=neo4j_driver,
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        id_property_external="id",
        id_property_neo4j="id",
    )
    return retriever.search(query_vector=query_vector, top_k=top_k)


def parse_retriever_results(retriever_result):
    """Step 3: Extract Text and IDs from Retriever Results"""
    chunks = []
    chunk_ids = []

    for item in retriever_result.items:
        content = item.content
        try:
            # Extract text
            text_start = content.find("'text': '") + len("'text': '")
            text_end = content.find("'", text_start)
            chunk_text = content[text_start:text_end]

            # Extract ID
            id_start = content.find("'id': '") + len("'id': '")
            id_end = content.find("'", id_start)
            chunk_id = content[id_start:id_end]

            chunks.append(chunk_text)
            chunk_ids.append(chunk_id)
        except Exception:
            continue

    return chunks, chunk_ids


def fetch_graph_context(neo4j_driver, chunk_ids):
    """Step 4: Fetch related graph context using Chunk IDs"""
    if not chunk_ids:
        return []

    with neo4j_driver.session() as session:
        query_cypher = """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
        WHERE c.id IN $chunk_ids
        OPTIONAL MATCH (e)-[r]-(related:Entity)
        RETURN e.name as entity, type(r) as rel, related.name as related_node
        LIMIT 50
        """
        result = session.run(query_cypher, chunk_ids=chunk_ids)

        relationships = set()
        for record in result:
            if record["rel"] and record["related_node"]:
                rel_str = f"({record['entity']}) -[{record['rel']}]-> ({record['related_node']})"
                relationships.add(rel_str)
        return list(relationships)


def format_context(chunks, relationships):
    """Step 5: Format everything into a context string"""
    chunks_str = "\n\n".join(
        [f"Chunk {i + 1}:\n{text}" for i, text in enumerate(chunks)]
    )
    graph_str = "\n".join(relationships)

    return f"""
=== RELEVANT TEXT CHUNKS ===
{chunks_str}

=== KNOWLEDGE GRAPH CONTEXT ===
{graph_str}
"""


# --- The Main Tool ---


@function_tool
def retrieve_knowledge(query: str) -> str:
    """
    Retrieves relevant information from the knowledge base using Hybrid RAG.
    Uses vector search to find text chunks and graph traversal to find related entities.
    """
    # 1. Init Clients
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    try:
        # Step 1: Embed
        query_vector = get_embedding(query)

        # Step 2: Vector Search
        retriever_result = search_qdrant(neo4j_driver, qdrant_client, query_vector)

        # Step 3: Parse Results
        chunks, chunk_ids = parse_retriever_results(retriever_result)

        # Step 4: Graph Search
        relationships = fetch_graph_context(neo4j_driver, chunk_ids)

        # Step 5: Format Output
        final_context = format_context(chunks, relationships)

        return final_context

    except Exception as e:
        return f"Error retrieving knowledge: {str(e)}"

    finally:
        neo4j_driver.close()
