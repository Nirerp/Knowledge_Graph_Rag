"""This module has the orchestrator class, in charge of parsing, ingesting and returning the graph data.
Also, this module contains embedding functions, chunking functions and any other functions necessary for raw text input.

"""

import uuid
from litellm import completion
from config.config import LLM_INGESTION_PROMPT
from config.datasets import GraphComponents


class Orchestrator:
    """
    Orchestrator class for the graph-rag project.
    This class is responsible for orchestrating the graph-rag pipeline.
    It is responsible for:
    - Ingesting the graph data
    - Querying the graph data
    - Retrieving the graph data
    - Returning the graph data
    - Returning the graph data
    """

    def __init__(self, llm_model: str, llm_api_key: str):
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

    def _test_response(self, prompt: str) -> str:  # for testing purposes ONLY
        response_test = completion(
            model=self.llm_model,
            api_key=self.llm_api_key,
            messages=[{"role": "user", "content": prompt}],
        )
        return response_test.choices[0].message.content

    def llm_parser(self, prompt):
        """
        This function sends a prompt to the LLM and returns the parsed graph components.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            GraphComponents: The parsed graph components.
            Example:
            {
                "graph": [
                    {"node": "Jeff Bezoz", "target_node": "Amazon", "relationship": "CEO of"},
                ]
            }
        """

        response = completion(
            model=self.llm_model,
            api_key=self.llm_api_key,
            response_format=GraphComponents,  # notice that this is a json_object, not a json_schema
            # some models require "response_format" to be a json_schema, not a json_schema - check LITELLM docs for more details
            messages=[
                {"role": "system", "content": LLM_INGESTION_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        return GraphComponents.model_validate_json(response.choices[0].message.content)

    def extract_graph_components(self, raw_text) -> tuple[dict, list, dict]:
        """
        This function extracts the graph components from the raw text.

        Args:
            raw_text: The raw text to extract the graph components from.

        Returns:
            nodes: A dictionary of nodes.
            relationships: A list of relationships.
            chunk_node_mapping: A dictionary mapping chunk UUIDs to chunk data and entity IDs.
        """
        nodes = {}
        relationships = []
        chunk_node_mapping = {}  # NEW: Track which entities appear in which chunks

        # Normalize input into iterable chunks
        chunks_to_process = []

        if isinstance(raw_text, str):
            chunks_to_process.append({"text": raw_text, "source": None})
        elif isinstance(raw_text, list):
            for entry in raw_text:
                if isinstance(entry, dict) and "chunks" in entry:
                    for chunk in entry["chunks"]:
                        chunks_to_process.append(
                            {"text": chunk, "source": entry.get("file")}
                        )
                else:
                    chunks_to_process.append({"text": entry, "source": None})
        else:
            raise ValueError("raw_text must be a string or list of chunks.")

        for idx, chunk in enumerate(chunks_to_process):
            chunk_id = str(uuid.uuid4())  # NEW: Generate UUID for this chunk
            chunk_node_mapping[chunk_id] = {
                "text": chunk["text"],
                "source_file": chunk["source"],
                "chunk_index": idx,
                "entity_ids": [],  # NEW: Track entities mentioned in this chunk
            }

            system_prompt = (
                "Extract nodes and relationships from the following text:\n"
                f"{chunk['text']}"
            )

            parsed_response = self.llm_parser(system_prompt).graph

            for entry in parsed_response:
                node = entry.node
                target_node = entry.target_node
                relationship = entry.relationship

                if node and node not in nodes:
                    nodes[node] = str(uuid.uuid4())

                # NEW: Add entity to this chunk's entity list
                if node:
                    chunk_node_mapping[chunk_id]["entity_ids"].append(nodes[node])

                if target_node and target_node not in nodes:
                    nodes[target_node] = str(uuid.uuid4())

                # NEW: Add target entity to this chunk's entity list
                if target_node:
                    chunk_node_mapping[chunk_id]["entity_ids"].append(
                        nodes[target_node]
                    )

                if target_node and relationship:
                    relationships.append(
                        {
                            "source": nodes[node],
                            "target": nodes[target_node],
                            "type": relationship,
                            "source_file": chunk.get("source"),
                        }
                    )

        return nodes, relationships, chunk_node_mapping  # NEW: Return 3 values


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    orchestrator = Orchestrator(
        llm_model=os.getenv("LLM_MODEL"), llm_api_key=os.getenv("LLM_API_KEY")
    )
    resp = orchestrator._test_response("Make a sentence out of three words.")

    print(f"LLM_MODEL: {os.getenv('LLM_MODEL')}")
    print(f"LLM_API_KEY: {os.getenv('LLM_API_KEY')}")
    print(
        f"Orchestrator initialized with these credentials: {orchestrator.llm_model} and {orchestrator.llm_api_key}"
    )
    print(resp)
