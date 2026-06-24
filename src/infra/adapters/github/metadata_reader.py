import os
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.domain.models import RepositoryMetadata, RepositoryInput
from src.domain.ports.output import MetadataReader

logger = logging.getLogger(__name__)


class GithubMetadataReader(MetadataReader):

  def __init__(self, github_token: Optional[str] = None):
    self.github_token = github_token

  def extract_from_repository(
      self, repo_data: RepositoryInput
  ) -> RepositoryMetadata:
    url = repo_data.get("url", "") if isinstance(repo_data, dict) else repo_data.url
    parts = url.rstrip("/").replace(".git", "").split("/")
    owner = parts[-2] if len(parts) >= 2 else "Unknown"
    repo_name = parts[-1] if len(parts) >= 1 and parts[-1] else "Unknown"

    branch = repo_data.get("target", "main") if isinstance(repo_data, dict) else repo_data.target
    commit_sha = repo_data.get("commit_sha") if isinstance(repo_data, dict) else repo_data.commit_sha
    author_name = repo_data.get("author_name", "Unknown Author") if isinstance(repo_data, dict) else getattr(repo_data, "author_name", "Unknown Author")
    author_email = repo_data.get("author_email") if isinstance(repo_data, dict) else getattr(repo_data, "author_email", None)

    try:
      api_data = self._fetch_commit_from_api(owner, repo_name, branch)
      if api_data:
        commit_sha = api_data.get("sha", commit_sha)
        author_name = api_data.get("commit", {}).get("author", {}).get("name", author_name)
        author_email = api_data.get("commit", {}).get("author", {}).get("email", author_email)
    except Exception as e:
      logger.error(f"Failed to fetch commit from GitHub API: {e}")

    return RepositoryMetadata(
      owner=owner,
      repo_name=repo_name,
      branch=branch,
      commit_sha=commit_sha,
      author_name=author_name,
      author_email=author_email,
      commit_message=None,
      timestamp=datetime.now(timezone.utc),
    )

  def _fetch_commit_from_api(
    self, owner: str, repo_name: str, branch: Optional[str] = None
  ) -> Optional[dict]:
    if not branch:
      return None

    url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{branch}"
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
      headers["Authorization"] = f"Bearer {token}"

    try:
      with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=headers)
        if response.status_code == 404:
          logger.warning(
              f"Repository commit not found at {url}"
          )
          return None
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
      logger.error(
          f"HTTP error fetching commit from {url}: {e.status_code}"
      )
      raise
    except Exception as e:
      logger.error(f"Unexpected error fetching commit from API: {e}")
      raise
