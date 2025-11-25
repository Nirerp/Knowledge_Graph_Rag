from neo4j_graphrag.retrievers import QdrantNeo4jRetriever


def retriever_search(neo4j_driver, qdrant_client, collection_name, embedded_query):
    retriever = QdrantNeo4jRetriever(
        driver=neo4j_driver,
        client=qdrant_client,
        collection_name=collection_name,
        id_property_external="id",
        id_property_neo4j="id",
    )

    results = retriever.search(query_vector=embedded_query, top_k=5)

    return results


def main():
    print("Hello from graph-rag!")


if __name__ == "__main__":
    main()
