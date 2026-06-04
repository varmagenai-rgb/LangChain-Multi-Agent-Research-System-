import asyncio
import os
from random import randint
from typing import Annotated, Any, Literal

from agent_framework import Message, SupportsChatGetResponse, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient

from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

ClientName = Literal[
    "openai_chat",
    "openai_chat_completion",
    "anthropic",
    "ollama",
    "bedrock",
    "azure_openai_chat",
    "azure_openai_chat_completion",
    "foundry_chat"
]

@tool(approval_mode="never_require")
# def get_weather(
#     location: Annotated[str, Field]
# )