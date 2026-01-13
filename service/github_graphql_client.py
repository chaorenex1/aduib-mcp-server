import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubGraphQLError(Exception):
    pass


class RateLimitError(GitHubGraphQLError):
    pass


class AuthenticationError(GitHubGraphQLError):
    pass


class NetworkTimeoutError(GitHubGraphQLError):
    pass


class GitHubGraphQLClient:
    _SEARCH_REPOSITORIES_QUERY = """
    query SearchRepositories($query: String!, $first: Int!) {
      search(query: $query, type: REPOSITORY, first: $first) {
        nodes {
          ... on Repository {
            name
            description
            url
            stargazerCount
            forkCount
            primaryLanguage { name }
            updatedAt
            owner { login }
          }
        }
      }
    }
    """

    _SEARCH_ISSUES_QUERY = """
    query SearchIssues($query: String!, $first: Int!) {
      search(query: $query, type: ISSUE, first: $first) {
        nodes {
          ... on Issue {
            title
            url
            state
            createdAt
            author { login }
            repository { nameWithOwner }
          }
        }
      }
    }
    """

    _SEARCH_CODE_QUERY = """
    query SearchCode($query: String!, $first: Int!) {
      search(query: $query, type: CODE, first: $first) {
        nodes {
          ... on Code {
            path
            repository { nameWithOwner, url }
            textMatches { fragment }
          }
        }
      }
    }
    """

    _GET_REPOSITORY_QUERY = """
    query GetRepository($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        description
        url
        stargazerCount
        forkCount
        primaryLanguage { name }
        updatedAt
        owner { login }
      }
    }
    """

    _GET_PULL_REQUESTS_QUERY = """
    query GetPullRequests($owner: String!, $name: String!, $first: Int!, $states: [PullRequestState!]) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: $first, states: $states, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            number
            title
            url
            state
            createdAt
            updatedAt
            author { login }
            mergeable
            additions
            deletions
            changedFiles
          }
        }
      }
    }
    """

    _GET_COMMITS_QUERY = """
    query GetCommits($owner: String!, $name: String!, $first: Int!) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: $first) {
                nodes {
                  oid
                  messageHeadline
                  message
                  committedDate
                  author { name email user { login } }
                  url
                }
              }
            }
          }
        }
      }
    }
    """

    _GET_RELEASES_QUERY = """
    query GetReleases($owner: String!, $name: String!, $first: Int!) {
      repository(owner: $owner, name: $name) {
        releases(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            name
            tagName
            url
            publishedAt
            description
            isPrerelease
            isDraft
            author { login }
          }
        }
      }
    }
    """

    _GET_README_QUERY = """
    query GetReadme($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        object(expression: "HEAD:README.md") {
          ... on Blob {
            text
          }
        }
      }
    }
    """

    def __init__(self, token: str, timeout: int = 30) -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self._endpoint = "https://api.github.com/graphql"
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json, application/vnd.github.text-match+json",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    async def __aenter__(self) -> "GitHubGraphQLClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_repositories(
        self,
        query: str,
        first: int = 10,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        search_query = self._build_repository_search_query(query, language, min_stars)
        variables = {"query": search_query, "first": first}
        data = await self._execute(self._SEARCH_REPOSITORIES_QUERY, variables, "search_repositories")
        search_result = data.get("search", {})
        nodes = search_result.get("nodes") or []
        return [node for node in nodes if node]

    async def search_issues(
        self,
        query: str,
        first: int = 10,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        search_query = self._build_issue_search_query(query, state)
        variables = {"query": search_query, "first": first}
        data = await self._execute(self._SEARCH_ISSUES_QUERY, variables, "search_issues")
        search_result = data.get("search", {})
        nodes = search_result.get("nodes") or []
        return [node for node in nodes if node]

    async def search_code(
        self,
        query: str,
        first: int = 10,
    ) -> List[Dict[str, Any]]:
        search_query = query.strip()
        variables = {"query": search_query, "first": first}
        data = await self._execute(self._SEARCH_CODE_QUERY, variables, "search_code")
        search_result = data.get("search", {})
        nodes = search_result.get("nodes") or []
        return [node for node in nodes if node]

    async def get_repository(self, owner: str, name: str) -> Dict[str, Any]:
        variables = {"owner": owner, "name": name}
        data = await self._execute(self._GET_REPOSITORY_QUERY, variables, "get_repository")
        return data.get("repository") or {}

    async def get_pull_requests(
        self, owner: str, name: str, first: int = 10, states: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        states_upper = [state.upper() for state in states] if states else None
        variables = {"owner": owner, "name": name, "first": first, "states": states_upper}
        data = await self._execute(self._GET_PULL_REQUESTS_QUERY, variables, "get_pull_requests")
        repository = data.get("repository") or {}
        pull_requests = repository.get("pullRequests") or {}
        nodes = pull_requests.get("nodes") or []
        return [node for node in nodes if node]

    async def get_commits(self, owner: str, name: str, first: int = 10) -> List[Dict[str, Any]]:
        variables = {"owner": owner, "name": name, "first": first}
        data = await self._execute(self._GET_COMMITS_QUERY, variables, "get_commits")
        repository = data.get("repository") or {}
        default_branch = repository.get("defaultBranchRef") or {}
        target = default_branch.get("target") or {}
        history = target.get("history") or {}
        nodes = history.get("nodes") or []
        return [node for node in nodes if node]

    async def get_releases(self, owner: str, name: str, first: int = 10) -> List[Dict[str, Any]]:
        variables = {"owner": owner, "name": name, "first": first}
        data = await self._execute(self._GET_RELEASES_QUERY, variables, "get_releases")
        repository = data.get("repository") or {}
        releases = repository.get("releases") or {}
        nodes = releases.get("nodes") or []
        return [node for node in nodes if node]

    async def get_readme(self, owner: str, name: str, path: str = "README.md") -> str:
        readme_query = self._GET_README_QUERY.replace("HEAD:README.md", f"HEAD:{path}")
        variables = {"owner": owner, "name": name}
        data = await self._execute(readme_query, variables, "get_readme")
        repository = data.get("repository") or {}
        obj = repository.get("object") or {}
        return obj.get("text") or ""

    async def _execute(self, query: str, variables: Dict[str, Any], operation: str) -> Dict[str, Any]:
        payload = {"query": query, "variables": variables}
        logger.info("GitHub GraphQL request: %s", operation)
        logger.debug("GitHub GraphQL variables for %s: %s", operation, variables)
        try:
            response = await self._client.post(self._endpoint, json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.error("GitHub GraphQL request timed out for %s", operation)
            raise NetworkTimeoutError("GitHub GraphQL request timed out") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                logger.error("GitHub authentication failed for %s", operation)
                raise AuthenticationError("GitHub authentication failed") from exc
            if status == 403 and self._is_rate_limited(exc.response, None):
                logger.warning("GitHub rate limit exceeded for %s", operation)
                raise RateLimitError("GitHub API rate limit exceeded") from exc
            logger.error("GitHub HTTP error %s for %s", status, operation)
            raise GitHubGraphQLError(f"GitHub HTTP error: {status}") from exc
        except httpx.RequestError as exc:
            logger.error("Network error during GitHub GraphQL request %s: %s", operation, exc)
            raise GitHubGraphQLError(f"Network error while requesting GitHub: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("Invalid JSON received from GitHub for %s: %s", operation, exc)
            raise GitHubGraphQLError("Invalid JSON response from GitHub") from exc

        if self._is_rate_limited(response, payload):
            logger.warning("GitHub rate limit detected for %s", operation)
            raise RateLimitError("GitHub API rate limit exceeded")

        errors = payload.get("errors") or []
        if errors:
            if self._contains_auth_error(errors):
                logger.error("GitHub authentication/authorization error during %s: %s", operation, errors)
                message = errors[0].get("message", "Authentication failed")
                raise AuthenticationError(message)
            messages = "; ".join(err.get("message", "Unknown error") for err in errors)
            logger.error("GitHub GraphQL error during %s: %s", operation, messages)
            raise GitHubGraphQLError(f"GitHub GraphQL error(s): {messages}")

        data = payload.get("data")
        if data is None:
            logger.error("GitHub GraphQL response missing data during %s", operation)
            raise GitHubGraphQLError("GitHub GraphQL response missing data")
        return data

    @staticmethod
    def _build_repository_search_query(
        query: str,
        language: Optional[str],
        min_stars: Optional[int],
    ) -> str:
        parts: List[str] = []
        if query:
            parts.append(query.strip())
        if language:
            parts.append(f"language:{language}")
        if min_stars is not None:
            parts.append(f"stars:>={min_stars}")
        return " ".join(part for part in parts if part).strip()

    @staticmethod
    def _build_issue_search_query(query: str, state: Optional[str]) -> str:
        parts: List[str] = ["is:issue"]
        if query:
            parts.insert(0, query.strip())
        if state:
            parts.append(f"state:{state.lower()}")
        return " ".join(part for part in parts if part).strip()

    @staticmethod
    def _is_rate_limited(response: httpx.Response, payload: Optional[Dict[str, Any]]) -> bool:
        header_value = response.headers.get("X-RateLimit-Remaining")
        try:
            if header_value is not None and int(header_value) == 0:
                return True
        except ValueError:
            pass
        if payload:
            for err in payload.get("errors", []):
                message = (err.get("message") or "").lower()
                if "rate limit" in message or "rate-limit" in message:
                    return True
                if err.get("type") == "RATE_LIMITED":
                    return True
        return False

    @staticmethod
    def _contains_auth_error(errors: List[Dict[str, Any]]) -> bool:
        for err in errors:
            message = (err.get("message") or "").lower()
            if "bad credentials" in message or "authentication" in message:
                return True
            if "requires authentication" in message or "must have" in message:
                return True
            if err.get("type") in {"FORBIDDEN", "INSUFFICIENT_SCOPES"}:
                return True
        return False
