import asyncio

from agent_framework import Message
from agent_framework.foundry import FoundryChatClient
from dotenv import load_dotenv
from agent_utils import build_chat_client

load_dotenv()

async def main() -> None:
    client = build_chat_client()

    try:
        task = asyncio.create_task(
            client.get_response(messages= [Message(role = "user", contents = ["tell me a fantency story"])])
        )
        await asyncio.sleep(1)
        task.cancel()
        await task
    except asyncio.CancelledError:
        print("Request was cancelled")


if __name__ == "__main__":
    asyncio.run(main())

