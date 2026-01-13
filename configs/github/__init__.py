from pydantic import Field
from pydantic_settings import BaseSettings


class GitHubConfig(BaseSettings):
    GITHUB_TOKEN: str = Field(
        ..., description="GitHub Personal Access Token used for authenticated requests"
    )
    GITHUB_GRAPHQL_URL: str = Field(
        default="https://api.github.com/graphql",
        description="GitHub GraphQL API endpoint",
    )
    GITHUB_API_TIMEOUT: int = Field(
        default=30, description="GitHub API request timeout in seconds"
    )
