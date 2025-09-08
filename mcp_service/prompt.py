from mcp.server.fastmcp.prompts import base

from libs import mcp_context

mcp= mcp_context.get()

# @mcp.prompt(name="Code Review")
# def review_code(code: str) -> str:
#     return f"Please review this code:\n\n{code}"


@mcp.prompt(name="爬取网页内容助手", description="根据用户的需求，爬取指定网页的内容，并提取其中的主要信息，返回给用户。")
def crawl_web(url: str) -> list[base.Message]:
    return [
        base.UserMessage("这是网页链接:\n\n"),
        base.UserMessage("<URL>"),
        base.UserMessage(url),
        base.UserMessage("</URL>"),
        base.AssistantMessage("请帮我爬取这个网页的内容，并提取其中的主要信息，返回给我。")
    ]