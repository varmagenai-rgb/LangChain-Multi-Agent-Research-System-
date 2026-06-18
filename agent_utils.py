"""Shared helpers for the lesson scripts."""

import os

from dotenv import load_dotenv

from agent_framework.foundry import FoundryChatClient
from agent_framework_anthropic import AnthropicClient
from azure.identity import AzureCliCredential

load_dotenv()


def build_chat_client() -> FoundryChatClient:
    """Return a FoundryChatClient configured from environment variables."""
    return FoundryChatClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )


def build_anthropic_chat_client(
    model: str = "claude-haiku-4-5-20251001",
) -> AnthropicClient:
    """Return an AnthropicClient with the API key pulled from Azure Key Vault."""
    from story_tools._secrets import get_anthropic_api_key  # local import to avoid azure-keyvault dep for Foundry users

    return AnthropicClient(
        api_key=get_anthropic_api_key(),
        model=model,
    )
