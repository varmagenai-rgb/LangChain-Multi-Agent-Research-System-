import asyncio
from typing import Any

from agent_framework import Agent, AgentSession, ContextProvider, SessionContext
from agent_utils import build_chat_client

class UserMemoryProvider(ContextProvider):
    DEFAULT_SOURCE_ID = "user_memory"

    def __init__(self):
        super().__init__(self.DEFAULT_SOURCE_ID)

    async def before_run(
            self,
            *,
            agent: Any,
            session: AgentSession | None,
            context: SessionContext,
            state: dict[str, Any],
        ) -> None:
            user_name = state.get("user_name")
            if user_name:
                 context.extend_instructions(
                      self.source_id,
                      f"The user's name is {user_name}. Always address them by name."
                 )
            else:
                 context.extend_instructions(
                      self.source_id,
                      "You don't know the user's name yet. Ask for it politely."
                 )

    async def after_run(
            self,
            *,
            agent: Any,
            session: AgentSession | None,
            context: SessionContext,
            state: dict[str, Any],
        ) -> None:
         for msg in context.input_messages:
              text = msg.text if hasattr(msg, "text") else ""
              if isinstance(text, str) and "my name is" in text.lower():
                   state["user_name"] = text.lower().split("my name is")[-1].strip().split()[0].capitalize()

async def main() -> None:
     agent = Agent(
          client=build_chat_client(),
          name = "MemoryAgent",
          instructions= "you are a friendly assistant",
          context_providers= [UserMemoryProvider()],
     )

     session = agent.create_session()

     result = await agent.run("What is the squire root of 9?", session=session)
     print(f"Agent:{result}\n")

     result = await agent.run("My name is Chaitanya", session=session)
     print(f"Agent:{result}\n")

     result = await agent.run("what is 2+2?", session=session)
     print(f"Agent:{result}\n")

     provider_state = session.state.get("user_memory", {})
     print(f"[Session State] stored user name: {provider_state.get('user_name')}")


if __name__ == "__main__":
     asyncio.run(main())
