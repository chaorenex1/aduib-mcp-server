from typing import Any

from pydantic import HttpUrl

from mcp_factory import get_mcp

mcp = get_mcp()

@mcp.tool(name="Search-Github-repositories", description="Search GitHub repositories using a specific repo name and return relevant information about the repositories found.")
async def search_github_repositories(
        repo_name: str
) -> Any:
    from service.github_service import GitHubService
    results = await GitHubService.search_repositories(repo_name=repo_name)
    return results


@mcp.tool(name="Search-Github-issues", description="Search GitHub issues using a specific issue snippet and return relevant information about the issues found.")
async def search_github_issues(
        issue_snippet: str
) -> Any:
    from service.github_service import GitHubService
    results = await GitHubService.search_repositories(issue_snippet=issue_snippet)
    return results


@mcp.tool(name="Search-Github-Code", description="Search GitHub code using a specific code snippet and return relevant information about the code found.")
async def search_github_code(
        code_snippet: str
) -> Any:
    from service.github_service import GitHubService
    results = await GitHubService.search_repositories(code_snippet=code_snippet)
    return results


@mcp.tool(name="get-Github-repository-details", description="Get detailed information about a specific GitHub repository using its URL.")
async def get_github_repository_details(
        repo_url: HttpUrl
) -> Any:
    from mcp_service.crawl_tools import crawl_web
    results = await crawl_web(urls=[repo_url])
    return results
