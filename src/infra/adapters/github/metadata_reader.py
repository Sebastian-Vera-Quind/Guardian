from datetime import datetime, timezone

from src.domain.models.state.repository import RepositoryMetadata
from src.domain.ports.output.metadata.metadata_reader import MetadataReader


class GithubMetadataReader(MetadataReader):

    def extract_from_repository(self, repo_data: dict) -> RepositoryMetadata:
        url = repo_data.get("url", "")
        parts = url.rstrip('/').replace('.git', '').split('/')
        owner = parts[-2] if len(parts) >= 2 else "Unknown"
        repo_name = parts[-1] if len(parts) >= 1 and parts[-1] else "Unknown"

        return RepositoryMetadata(
            owner=owner,
            repo_name=repo_name,
            branch=repo_data.get("target", "main"),
            commit_sha=repo_data.get("commit_sha"),
            author_name=repo_data.get("author_name", "Unknown Author"),
            author_email=repo_data.get("author_email"),
            commit_message=None,
            timestamp=datetime.now(timezone.utc),
        )
