"""Multi-turn REPL driver for StoryAutomationAgent.

Run with:
    PYTHONIOENCODING=utf-8 python -m story_tools
"""

import asyncio

from dotenv import load_dotenv

load_dotenv()

from ._agent import build_agent  # noqa: E402  (env must load first)


async def main() -> None:
    agent = build_agent()
    session = agent.create_session()

    print("StoryAutomationAgent ready.")
    print("Tell me which xlsx file to upload, or type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            break

        try:
            result = await agent.run(user_input, session=session)
        except Exception as e:
            print(f"\n[error] {type(e).__name__}: {e}\n")
            continue

        print(f"\nagent> {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
