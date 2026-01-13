from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

from mcp_factory import get_mcp

mcp = get_mcp()


def _extract_owner_and_repo(owner: str, repo_name: str) -> Tuple[str, str]:
    """
    Allow callers to pass either explicit owner/repo or a GitHub URL in one of the arguments.
    """

    def parse_from_url(value: str) -> Optional[Tuple[str, str]]:
        parsed = urlparse(value)
        if "github.com" not in parsed.netloc:
            return None
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) < 2:
            return None
        repo = path_parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return path_parts[0], repo

    parsed_owner_repo = parse_from_url(owner) or parse_from_url(repo_name)
    if parsed_owner_repo:
        return parsed_owner_repo

    return owner, repo_name


@mcp.tool(
    name="Search-Github-repositories",
    description="Search GitHub repositories by query with optional language and star filters. / 通过查询搜索 GitHub 仓库，可选过滤语言和星标数。",
)
async def search_github_repositories(
    query: str,
    first: int = 10,
    language: Optional[str] = None,
    min_stars: Optional[int] = None,
) -> Any:
    from service.github_service import GitHubService

    return await GitHubService.search_repositories(query, first, language, min_stars)


@mcp.tool(
    name="Search-Github-issues",
    description="Search GitHub issues by query with optional state filter. / 通过查询搜索 GitHub Issue，可选指定状态过滤。",
)
async def search_github_issues(
    query: str,
    first: int = 10,
    state: Optional[str] = None,
) -> Any:
    from service.github_service import GitHubService

    return await GitHubService.search_issues(query, first, state)


@mcp.tool(
    name="Search-Github-Code",
    description="Search GitHub code snippets by query. / 通过查询搜索 GitHub 代码片段。",
)
async def search_github_code(
    query: str,
    first: int = 10,
) -> Any:
    from service.github_service import GitHubService

    return await GitHubService.search_code(query, first)


@mcp.tool(
    name="get-Github-repository-details",
    description="Fetch repository details via GitHub GraphQL API using owner and repo name. / 使用 GitHub GraphQL API 通过仓库所属者和名称获取仓库详情。",
)
async def get_github_repository_details(
    owner: str,
    repo_name: str,
) -> Any:
    from service.github_service import GitHubService

    parsed_owner, parsed_repo = _extract_owner_and_repo(owner, repo_name)
    return await GitHubService.get_repository(parsed_owner, parsed_repo)


@mcp.tool(
    name="get-Github-pull-requests",
    description="Get pull requests from a GitHub repository with optional state filter. / 获取 GitHub 仓库的 Pull Request 列表，可选状态过滤（OPEN, CLOSED, MERGED）。",
)
async def get_github_pull_requests(
    owner: str,
    repo_name: str,
    first: int = 10,
    states: Optional[List[str]] = None,
) -> Any:
    from service.github_service import GitHubService

    parsed_owner, parsed_repo = _extract_owner_and_repo(owner, repo_name)
    return await GitHubService.get_pull_requests(parsed_owner, parsed_repo, first, states)


@mcp.tool(
    name="get-Github-commits",
    description="Get recent commits from a GitHub repository's default branch. / 获取 GitHub 仓库默认分支的最近提交记录。",
)
async def get_github_commits(
    owner: str,
    repo_name: str,
    first: int = 10,
) -> Any:
    from service.github_service import GitHubService

    parsed_owner, parsed_repo = _extract_owner_and_repo(owner, repo_name)
    return await GitHubService.get_commits(parsed_owner, parsed_repo, first)


@mcp.tool(
    name="get-Github-releases",
    description="Get releases from a GitHub repository. / 获取 GitHub 仓库的发布版本列表。",
)
async def get_github_releases(
    owner: str,
    repo_name: str,
    first: int = 10,
) -> Any:
    from service.github_service import GitHubService

    parsed_owner, parsed_repo = _extract_owner_and_repo(owner, repo_name)
    return await GitHubService.get_releases(parsed_owner, parsed_repo, first)


@mcp.tool(
    name="get-Github-readme",
    description="Get README content from a GitHub repository. / 获取 GitHub 仓库的 README 文件内容。",
)
async def get_github_readme(
    owner: str,
    repo_name: str,
    path: str = "README.md",
) -> Any:
    from service.github_service import GitHubService

    parsed_owner, parsed_repo = _extract_owner_and_repo(owner, repo_name)
    return await GitHubService.get_readme(parsed_owner, parsed_repo, path)
