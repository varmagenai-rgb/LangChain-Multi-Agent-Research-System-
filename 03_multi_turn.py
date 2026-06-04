import asyncio

from agent_framework import Agent
from agent_utils import build_chat_client

async def main() -> str:
    agent = Agent(
        client=build_chat_client(),
        name= "ConversationAgent",
        instructions= "You are a friendly Assistant. Keep your answers breaf",
    )

    session = agent.create_session()

    #First turn
    result = await agent.run("My name is Chaitanya And I love hiking.", session=session)
    print(f"Agent: {result}\n")

    #Second Turn
    result =  await agent.run("what do you reememeber about me?",session=session)
    print(f"Agent: {result}")

if __name__ == "__main__":
    asyncio.run(main())
