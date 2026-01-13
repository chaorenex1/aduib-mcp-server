import logging
from typing import Any, Dict, List, Optional

from configs.github import GitHubConfig
from service.github_graphql_client import GitHubGraphQLClient

logger = logging.getLogger(__name__)


class GitHubService:
    _config: Optional[GitHubConfig] = None

    @classmethod
    def _get_config(cls) -> GitHubConfig:
        if cls._config is None:
            cls._config = GitHubConfig()
        return cls._config

    @classmethod
    async def search_repositories(
        cls,
        query: str,
        first: int = 10,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.search_repositories(query, first, language, min_stars)

    @classmethod
    async def search_issues(
        cls,
        query: str,
        first: int = 10,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.search_issues(query, first, state)

    @classmethod
    async def search_code(cls, query: str, first: int = 10) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.search_code(query, first)

    @classmethod
    async def get_repository(cls, owner: str, name: str) -> Dict[str, Any]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.get_repository(owner, name)

    @classmethod
    async def get_pull_requests(
        cls, owner: str, name: str, first: int = 10, states: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.get_pull_requests(owner, name, first, states)

    @classmethod
    async def get_commits(cls, owner: str, name: str, first: int = 10) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.get_commits(owner, name, first)

    @classmethod
    async def get_releases(cls, owner: str, name: str, first: int = 10) -> List[Dict[str, Any]]:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.get_releases(owner, name, first)

    @classmethod
    async def get_readme(cls, owner: str, name: str, path: str = "README.md") -> str:
        config = cls._get_config()
        async with GitHubGraphQLClient(config.GITHUB_TOKEN, config.GITHUB_API_TIMEOUT) as client:
            return await client.get_readme(owner, name, path)
