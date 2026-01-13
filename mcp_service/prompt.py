from mcp.server.fastmcp.prompts import base

from mcp_factory import get_mcp

mcp = get_mcp()


@mcp.prompt(name="爬取网页内容助手", description="根据用户的需求，爬取指定网页的内容，并提取其中的主要信息，返回给用户。")
def crawl_web(url: str) -> list[base.Message]:
    return [
        base.UserMessage("这是网页链接:\n\n"),
        base.UserMessage("<URL>"),
        base.UserMessage(url),
        base.UserMessage("</URL>"),
        base.AssistantMessage("请帮我爬取这个网页的内容，并提取其中的主要信息，返回给我。")
    ]


@mcp.prompt(name="Retrieve information from Doc Knowledge Base",
            description="根据用户的查询在文档知识库中找到最匹配的内容)，并返回结果及出处。")
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


# ----------------- Generated prompts for tools without exact prompt names -----------------

@mcp.prompt(name="Provide-URL-based-web-content-crawling", description="Prompt wrapper for crawling one or multiple URLs and extracting main content and metadata.")
def prompt_provide_url_based_web_content_crawling(urls: list[str]) -> list[base.Message]:
    """Ask the assistant to crawl given URLs and return structured content for each URL."""
    return [
        base.UserMessage("Please crawl the following URLs and extract their main content and metadata."),
        base.UserMessage("URLs:"),
        base.UserMessage("\n".join(urls) if urls else ""),
        base.AssistantMessage(
            "For each URL return a JSON object with fields: url, title, main_text (cleaned), summary (3-5 sentences), language, links (list), and last_modified if available. Do not fabricate content; if the page cannot be reached, return an object with an error field."
        ),
    ]


@mcp.prompt(name="search-the-content-from-the-web", description="Prompt wrapper for performing web search across multiple engines and returning aggregated content snippets.")
def prompt_search_the_content_from_the_web(web_content: str) -> list[base.Message]:
    return [
        base.UserMessage("Search the web using multiple search engines for the following query or content:"),
        base.UserMessage(web_content),
        base.AssistantMessage("Return a ranked list of short excerpts (2-3 sentences) with source URLs and a brief summary of why each result is relevant."),
    ]


@mcp.prompt(name="Search-Github-repositories", description="Prompt helper to search GitHub repositories with optional language and star filters. / 搜索 GitHub 仓库，支持语言和星标过滤。")
def prompt_search_github_repositories(query: str, first: int = 10, language: str = "", min_stars: int = 0) -> list[base.Message]:
    return [
        base.UserMessage("Search GitHub for repositories matching this query:"),
        base.UserMessage(f"Query: {query}, Limit: {first}"),
        base.UserMessage(f"Language filter: {language}" if language else ""),
        base.UserMessage(f"Minimum stars: {min_stars}" if min_stars > 0 else ""),
        base.AssistantMessage("Return repositories with fields: name, description, url, stargazerCount, forkCount, primaryLanguage, updatedAt, and owner.")
    ]


@mcp.prompt(name="Search-Github-issues", description="Prompt helper to search GitHub issues with optional state filter. / 搜索 GitHub Issue，支持状态过滤。")
def prompt_search_github_issues(query: str, first: int = 10, state: str = "") -> list[base.Message]:
    return [
        base.UserMessage("Search GitHub issues matching this query:"),
        base.UserMessage(f"Query: {query}, Limit: {first}"),
        base.UserMessage(f"State filter: {state}" if state else ""),
        base.AssistantMessage("Return issues with fields: title, url, state, createdAt, author, and repository nameWithOwner.")
    ]


@mcp.prompt(name="Search-Github-Code", description="Prompt helper to search GitHub code snippets. / 搜索 GitHub 代码片段。")
def prompt_search_github_code(query: str, first: int = 10) -> list[base.Message]:
    return [
        base.UserMessage("Search GitHub code for this query:"),
        base.UserMessage(f"Query: {query}, Limit: {first}"),
        base.AssistantMessage("Return code matches with fields: path, repository nameWithOwner and url, textMatches fragments.")
    ]


@mcp.prompt(name="get-Github-repository-details", description="Prompt helper to fetch repository details via GraphQL API. / 通过 GraphQL API 获取仓库详情。")
def prompt_get_github_repository_details(owner: str, repo_name: str) -> list[base.Message]:
    return [
        base.UserMessage("Fetch detailed information for this GitHub repository:"),
        base.UserMessage(f"Owner: {owner}, Repository: {repo_name}"),
        base.AssistantMessage("Return repository details: name, description, url, stargazerCount, forkCount, primaryLanguage, updatedAt, and owner login.")
    ]


@mcp.prompt(name="retrieve_qa_kb", description="Prompt helper to search the QA memory and return results with QA_REF anchors for tracking.")
def prompt_retrieve_qa_kb(query: str, namespace: str, top_k: int = 8) -> list[base.Message]:
    return [
        base.UserMessage("Search the QA memory for the query and return up to top_k results with anchor lines [QA_REF qa-xxxx]:"),
        base.UserMessage("Query:"),
        base.UserMessage(query),
        base.UserMessage(f"Namespace: {namespace}, top_k: {top_k}"),
        base.AssistantMessage("Return results as a list of renderable items including qa_id, anchor, question, answer, confidence, and source metadata.")
    ]


@mcp.prompt(name="qa_record_hit", description="Prompt helper describing when to call qa_record_hit and what payload to send (used/shown).")
def prompt_qa_record_hit(qa_id: str, namespace: str, used: bool = True, shown: bool = True) -> list[base.Message]:
    return [
        base.UserMessage("Record a hit for QA item when it was shown/used in the final answer."),
        base.UserMessage(f"qa_id: {qa_id}"),
        base.UserMessage(f"namespace: {namespace}"),
        base.UserMessage(f"used: {used}, shown: {shown}"),
        base.AssistantMessage("Call qa_record_hit with the above payload when the QA item was actually included in the model's final response (used=true).")
    ]


@mcp.prompt(name="qa_upsert_candidate", description="Prompt helper for creating candidate QA entries to be upserted into the QA memory.")
def prompt_qa_upsert_candidate(question_raw: str, answer_raw: str, namespace: str) -> list[base.Message]:
    return [
        base.UserMessage("Create a QA candidate entry with the following question and answer. Include brief tags and a scope if available."),
        base.UserMessage("Question:"),
        base.UserMessage(question_raw),
        base.UserMessage("Answer:"),
        base.UserMessage(answer_raw),
        base.UserMessage(f"Namespace: {namespace}"),
        base.AssistantMessage("Return a compact candidate object with fields: question_raw, answer_raw, tags (optional), scope (optional), time_sensitivity (low/medium/high), evidence_refs (optional).")
    ]


@mcp.prompt(name="qa_validate_and_update", description="Prompt helper for validating QA entries after execution and updating their state.")
def prompt_qa_validate_and_update(qa_id: str, namespace: str, result: str, reason: str = "") -> list[base.Message]:
    return [
        base.UserMessage("Provide validation outcome for a QA item after executing or testing the suggested solution."),
        base.UserMessage(f"qa_id: {qa_id}"),
        base.UserMessage(f"namespace: {namespace}"),
        base.UserMessage(f"result: {result}"),
        base.UserMessage(f"reason: {reason}"),
        base.AssistantMessage("Return an object indicating the updated validation status and any evidence refs or notes to store alongside the QA entry.")
    ]


@mcp.prompt(name="get-Github-pull-requests", description="Prompt helper to fetch pull requests from a GitHub repository with optional state filtering.")
def prompt_get_github_pull_requests(owner: str, repo_name: str, first: int = 10, states: str = "") -> list[base.Message]:
    return [
        base.UserMessage("Fetch pull requests from this GitHub repository:"),
        base.UserMessage(f"Owner: {owner}, Repository: {repo_name}"),
        base.UserMessage(f"Limit: {first}" + (f", States filter: {states}" if states else "")),
        base.AssistantMessage("Return PR list with fields: number, title, url, state, author, created_at, updated_at, additions, deletions, changed_files, and mergeable status.")
    ]


@mcp.prompt(name="get-Github-commits", description="Prompt helper to fetch recent commits from a GitHub repository's default branch.")
def prompt_get_github_commits(owner: str, repo_name: str, first: int = 10) -> list[base.Message]:
    return [
        base.UserMessage("Fetch recent commits from this GitHub repository:"),
        base.UserMessage(f"Owner: {owner}, Repository: {repo_name}, Limit: {first}"),
        base.AssistantMessage("Return commit list with fields: oid (SHA), message_headline, message, author_name, author_email, committed_date, and commit_url.")
    ]


@mcp.prompt(name="get-Github-releases", description="Prompt helper to fetch releases from a GitHub repository.")
def prompt_get_github_releases(owner: str, repo_name: str, first: int = 10) -> list[base.Message]:
    return [
        base.UserMessage("Fetch releases from this GitHub repository:"),
        base.UserMessage(f"Owner: {owner}, Repository: {repo_name}, Limit: {first}"),
        base.AssistantMessage("Return release list with fields: name, tag_name, url, published_at, description, is_prerelease, is_draft, and author.")
    ]


@mcp.prompt(name="get-Github-readme", description="Prompt helper to fetch README content from a GitHub repository.")
def prompt_get_github_readme(owner: str, repo_name: str, path: str = "README.md") -> list[base.Message]:
    return [
        base.UserMessage("Fetch README content from this GitHub repository:"),
        base.UserMessage(f"Owner: {owner}, Repository: {repo_name}, Path: {path}"),
        base.AssistantMessage("Return the full README content as markdown text. If the file doesn't exist, indicate that clearly.")
    ]
