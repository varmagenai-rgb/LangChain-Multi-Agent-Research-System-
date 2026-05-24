import asyncio

from agent_framework import Agent

from agent_utils import build_chat_client

"""
Hello Agent — Simplest possible agent

This sample creates a minimal agent using FoundryChatClient via an
Azure AI Foundry project endpoint, and runs it in both non-streaming and streaming modes.

There are XML tags in all of the get started samples, those are used to display the same code in the docs repo.
"""

async def main() -> None:
    # <Create Agent>
    agent = Agent(
        client=build_chat_client(),
        name="HelloAgent",
        instructions="You are a friendly assistant. Keep answers brief.",
    )

    #</create agent>

    #<run_agent>
    #non-streaming: get the complete response at a time
    result = await agent.run("what is the capital of INDIA?")
    print(f"Agent: {result}")
    #</run_agent>


    #<run_agent_streaming>
    # streaming : receive the tokens as per they generated
    print("Agent (streaming): ", end="", flush=True)
    async for chunk in agent.run("Tell me 10 sentance fun fact.", stream=True):
        if chunk.text:
            print(chunk.text,end="", flush=True)
    print()
    #</run_agent_streaming>


if __name__ == "__main__":
    asyncio.run(main())