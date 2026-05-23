# pip install agent-framework
# Use `az login` to authenticate with Azure CLI
import os
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async def main():
    agent = Agent(
        client= FoundryChatClient(
            credential=AzureCliCredential(),
            project_endpoint= os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            ),
            name= "HikuAgent",
            instructions= "You are an upbeat assistant that writes beautifully",
    )

    print(await agent.run("Write a hiku about Microsoft agent framework."))

if __name__ == "__main__":
    asyncio.run(main())