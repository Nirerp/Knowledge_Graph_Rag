from graph_agents.config.const import SYSTEM_PROMPT
from graph_agents.config.schemas import AgentResponse

from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
import asyncio
import os
from dotenv import load_dotenv

from graph_agents.tools.retrieve_answer import retrieve_knowledge


# Disable openai-agents tracing to suppress "OPENAI_API_KEY is not set" warning
set_tracing_disabled(True)

# Disable LiteLLM telemetry to suppress "OPENAI_API_KEY is not set" warning
os.environ["LITELLM_TELEMETRY"] = "False"

load_dotenv()

## SETTING UP LLM ENV VARIABLES ##
model = os.getenv("LLM_MODEL")
api_key = os.getenv("LLM_API_KEY")
##################################


async def main():
    agent = Agent(
        name="Answering_Agent",
        instructions=SYSTEM_PROMPT,
        model=LitellmModel(model=model, api_key=api_key),
        tools=[retrieve_knowledge],
    )

    print("Hybrid RAG Agent Initialized. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            # Run the agent with the user's input
            result = await Runner.run(agent, user_input)

            # Try to parse JSON response into AgentResponse
            try:
                import json

                # Extract JSON from response (in case there's extra text)
                output_str = str(result.final_output)

                # Find JSON object in the string
                json_start = output_str.find("{")
                json_end = output_str.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_str = output_str[json_start:json_end]
                    response_data = json.loads(json_str)
                    response = AgentResponse(**response_data)

                    # Format structured output with emojis
                    print("\n💬 Answer:")
                    print(f"   {response.answer}\n")
                    print("📚 Sources:")
                    for source in response.sources:
                        print(f"   • {source}")
                    print("\n🔍 Retrieval Info:")
                    print(
                        f"   Qdrant: {response.chunks_retrieved} chunks  |  Neo4j: {response.relationships_found} relationships\n"
                    )
                else:
                    # No JSON found, print as-is
                    print(f"\nAgent: {result.final_output}\n")

            except (json.JSONDecodeError, KeyError, TypeError):
                # Fallback for non-JSON or malformed responses
                print(f"\nAgent: {result.final_output}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
