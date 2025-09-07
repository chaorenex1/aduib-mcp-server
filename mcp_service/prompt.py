from mcp.server.fastmcp.prompts import base

from libs import mcp_context

mcp= mcp_context.get()

@mcp.prompt(name="Code Review")
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"


@mcp.prompt(name="Debug Assistant")
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]