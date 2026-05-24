import asyncio
from random import randint
from typing import Annotated

from agent_framework import Agent, tool
from pydantic import Field

from agent_utils import build_chat_client


@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="The Location to get weather for.")],
) -> str:
    conditions = ["sunny", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 2)]} with a high of {randint(20, 30)}°C."

async def main() ->None:
    agent = Agent(
        client=build_chat_client(),
        name= "WeatherAgent",
        instructions= "You are a healpful weather agent. use the get_weather tool to answer questions.",
        tools=[get_weather],
    )


    result = await agent.run("what is the weather like in New Delhi?")
    print(f"Agent :{result}")


if __name__ == "__main__":
    asyncio.run(main())