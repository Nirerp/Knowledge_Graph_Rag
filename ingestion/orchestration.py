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
            response_format=GraphComponents, # notice that this is a json_object, not a json_schema
            # some models require "response_format" to be a json_schema, not a json_schema - check LITELLM docs for more details
            messages=[
                {"role": "system", "content": LLM_INGESTION_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        return GraphComponents.model_validate_json(response.choices[0].message.content)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    

    orchestrator = Orchestrator(
        llm_model=os.getenv("LLM_MODEL"), llm_api_key=os.getenv("LLM_API_KEY")
    )
    resp = orchestrator._test_response("Make a sentence out of three words.")

    print(f"LLM_MODEL: {os.getenv("LLM_MODEL")}")
    print(f"LLM_API_KEY: {os.getenv("LLM_API_KEY")}")
    print(f"Orchestrator initialized with these credentials: {orchestrator.llm_model} and {orchestrator.llm_api_key}")
    print(resp)