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


@mcp.prompt(name="Retrieve information from Doc Knowledge Base")
def retrieval_from_paragraph(query: str) -> list[base.Message]:
    return [
        base.UserMessage("请从文档知识库中检索相关内容，回答用户的问题。"),
        base.UserMessage("查询内容:\n\n"),
        base.UserMessage(query)
    ]


@mcp.prompt(
    name="Retrieve information from QA Knowledge Base",
    description="根据用户的查询在QA知识库中找到最匹配的问答，并返回结果及出处。",
)
def retrieval_from_qa(query: str) -> list[base.Message]:
    return [
        base.UserMessage("请从QA知识库中检索与下面请求最相关的问答对，并提供其来源信息。"),
        base.UserMessage("查询内容:\n\n"),
        base.UserMessage(query),
        base.AssistantMessage("输出时给出匹配的问答内容，说明相关性，并附上qa_id、数据集、URL以及时间戳。"),
    ]


@mcp.prompt(
    name="Retrieve information from My Browser History",
    description="在本地浏览器历史记录中搜索匹配的URL或标题，可选按时间范围过滤，确保隐私最小化。",
)
def retrieval_from_browser_history(
    query: str,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[base.Message]:
    messages: list[base.Message] = [
        base.UserMessage("请在本地浏览器历史记录中查找与请求相关的条目，仅返回真实存在的记录。"),
        base.UserMessage("查询内容:\n\n"),
        base.UserMessage(query),
    ]
    if start_time:
        messages.append(base.UserMessage(f"开始时间过滤: {start_time}"))
    if end_time:
        messages.append(base.UserMessage(f"结束时间过滤: {end_time}"))
    messages.append(
        base.AssistantMessage(
            "请返回匹配的历史记录，包含标题、URL、时间戳、浏览器来源以及数据库标识，避免暴露无关链接。"
        )
    )
    return messages
