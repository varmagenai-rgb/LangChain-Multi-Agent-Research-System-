from typing import Any

from agent_framework import Agent
from agent_framework.azure import AgentFunctionApp
from agent_framework.foundry import FoundryChatClient
from agent_utils import build_chat_client

def _create_agent() -> Any:
    return Agent(
        client= build_chat_client(),
        name= "HostedAgent",
        instructions="You are a helpful assistant hosted in azure Functions.",
    )

app = AgentFunctionApp(agents=[_create_agent()], enable_health_check=True, max_poll_retries=50)

if __name__ == "__main__":
    print("start function host with: func start")
    print("Then call: POST /api/agents/HostedAgent/run")
