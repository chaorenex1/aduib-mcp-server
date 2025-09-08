from mcp.server.fastmcp.prompts import base

from libs import mcp_context

mcp= mcp_context.get()

# @mcp.prompt(name="Code Review")
# def review_code(code: str) -> str:
#     return f"Please review this code:\n\n{code}"


@mcp.prompt(name="爬取网页内容助手")
def crawl_web(url: str,query:str) -> list[base.Message]:
    return [
        base.UserMessage("这是网页链接:\n\n"),
        base.UserMessage("<URL>"),
        base.UserMessage(url),
        base.UserMessage("</URL>"),
        base.UserMessage(f"请根据以下需求进行爬取:\n\n{query}"),
        base.AssistantMessage("请帮我爬取这个网页的内容，并提取其中的主要信息，返回给我。")
    ]