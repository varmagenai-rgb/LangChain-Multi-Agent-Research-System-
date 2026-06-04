import asyncio

from agent_framework import(
    executor,
    WorkflowBuilder,
    WorkflowContext,
    Executor,
    handler,
)

from typing_extensions import Never

class UpperCase(Executor):
    def __init__(self, id:str):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text:str, ctx: WorkflowContext[str]) -> None:
        await ctx.send_message(text.upper())

@executor(id="reverse_text")
async def reverse_text(text:str, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(text[::-1])

def create_workflow():
    upper = UpperCase(id="upper_case")
    return WorkflowBuilder(start_executor=upper).add_edge(upper, reverse_text).build()

async def main() -> None:
    workflow = create_workflow()

    events = await workflow.run("hello world")
    outputs = events.get_outputs()
    print(f"Output: {outputs[0] if outputs else None}")
    print(f"Final state: {events.get_final_state()}")

if __name__ == "__main__":
    asyncio.run(main())