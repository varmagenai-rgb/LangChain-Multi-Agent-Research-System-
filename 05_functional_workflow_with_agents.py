import asyncio
from agent_framework import Agent, workflow
from agent_framework.foundry import FoundryChatClient
from agent_utils import build_chat_client

client = build_chat_client()

writer = Agent(
    name= "WriterAgent",
    instructions="Write a short poem (4 lines Max) about given topic",
    client=client,
)

reviewer = Agent(
    name= "ReviewerAgent",
    instructions= "Review the given poem in one sentance. is it good?",
    client=client,
)

@workflow
async def poem_workflow(topic:str) -> str:
    poem = (await writer.run(f"Write a poem about {topic}")).text
    review = (await reviewer.run(f"Review this poem :{poem}")).text
    return f"poem:\n{poem}\n\nReview:{review}"

async def main() -> None:
    result = await poem_workflow.run("a cat learning to code")
    print(result.get_outputs()[0])

if __name__ == "__main__":
    asyncio.run(main())