import asyncio
from agent_framework import workflow

async def to_upper_case(text:str) -> str:
    return text.upper()


async def reverse_text(text:str) -> str:
    return text[::-1]

@workflow
async def text_workflow(text:str) -> str:
    upper = await to_upper_case(text)
    return await reverse_text(upper)


async def main() -> None:
    result = await text_workflow.run("hello world")
    print(f"Output: {result.get_outputs()}")
    print(f"final state: {result.get_final_state()}")

if __name__ == "__main__":
    asyncio.run(main())