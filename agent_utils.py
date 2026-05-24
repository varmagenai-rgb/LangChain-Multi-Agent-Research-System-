"""Shared helpers for the lesson scripts."""

import os

from dotenv import load_dotenv

from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

load_dotenv()


def build_chat_client() -> FoundryChatClient:
    """Return a FoundryChatClient configured from environment variables."""
    return FoundryChatClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )
