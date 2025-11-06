"""
Runtime configuration via pydantic-settings.
Centralizes endpoints and tokens for external services,
plus logging level and simple token validation helpers.
"""

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration for bridge."""

    model_config = SettingsConfigDict(env_file=".env")

    # GitHub
    github_token: str | None = None
    github_api_url: HttpUrl = "https://api.github.com"

    # bio.tools
    biotools_api_url: HttpUrl = "https://bio.tools/api/"

    # Hugging Face
    huggingface_token: str | None = None
    huggingface_api_url: HttpUrl = "https://api-inference.huggingface.co"

    # Europe PMC
    europe_pmc_api_url: HttpUrl = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    # Logging
    log_level: str = "INFO"

    @property
    def github_api_base(self) -> str:
        """Base URL for GitHub API as a string"""
        return self._api_base(self.github_api_url)

    @property
    def biotools_api_base(self) -> str:
        """Base URL for bio.tools API as a string"""
        return self._api_base(self.biotools_api_url)

    @property
    def huggingface_api_base(self) -> str:
        """Base URL for Hugging Face API as a string"""
        return self._api_base(self.huggingface_api_url)

    @property
    def europepmc_api_base(self) -> str:
        """Base URL for Europe PMC API as a string"""
        return self._api_base(self.europe_pmc_api_url)

    @staticmethod
    def _api_base(url: HttpUrl) -> str:
        """Get base URL without trailing slash."""
        return str(url).rstrip("/")

    def require_github_token(self):
        """Raise error if GitHub token is not set or invalid."""
        if self.github_token is None:
            raise ValueError("GitHub token is required but not set.")
        if not self.github_token.startswith("ghp_"):
            raise ValueError("Invalid GitHub token format.")

    def require_huggingface_token(self):
        """Raise error if Hugging Face token is not set or invalid."""
        if self.huggingface_token is None:
            raise ValueError("Hugging Face token is required but not set.")
        if not self.huggingface_token.startswith("hf_"):
            raise ValueError("Invalid Hugging Face token format.")


settings = Settings()
