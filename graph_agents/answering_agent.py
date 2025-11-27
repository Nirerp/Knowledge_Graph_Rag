from graph_agents.config.const import SYSTEM_PROMPT

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
            print(f"\nAgent: {result.final_output}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
