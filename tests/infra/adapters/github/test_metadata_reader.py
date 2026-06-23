import unittest
from src.infra.adapters.github.metadata_reader import GithubMetadataReader
from domain.models.util import RepositoryMetadata


class TestGithubMetadataReaderExtractFromRepository(unittest.TestCase):

    def _make_repo_data(self, **kwargs) -> dict:
        base = {
            "url": "https://github.com/acme/my-repo.git",
            "installation": "inst-123",
            "commit_sha": "abc123def456",
            "target": "main",
        }
        base.update(kwargs)
        return base

    def test_extract_from_repository_parses_owner_from_url(self):
        repo_data = self._make_repo_data(url="https://github.com/acme-org/my-repo.git")
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.owner, "acme-org")

    def test_extract_from_repository_parses_repo_name_from_url(self):
        repo_data = self._make_repo_data(url="https://github.com/acme/my-repo.git")
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.repo_name, "my-repo")

    def test_extract_from_repository_maps_target_to_branch(self):
        repo_data = self._make_repo_data(target="feature/loader")
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.branch, "feature/loader")

    def test_extract_from_repository_copies_commit_sha(self):
        repo_data = self._make_repo_data(commit_sha="deadbeef1234")
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.commit_sha, "deadbeef1234")

    def test_extract_from_repository_uses_default_author_name(self):
        repo_data = self._make_repo_data()
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.author_name, "Unknown Author")

    def test_extract_from_repository_uses_provided_author_name(self):
        repo_data = self._make_repo_data(author_name="Jane Doe")
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertEqual(result.author_name, "Jane Doe")

    def test_extract_from_repository_returns_repository_metadata_instance(self):
        repo_data = self._make_repo_data()
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertIsInstance(result, RepositoryMetadata)

    def test_extract_from_repository_commit_message_is_none(self):
        repo_data = self._make_repo_data()
        result = GithubMetadataReader().extract_from_repository(repo_data)
        self.assertIsNone(result.commit_message)


class TestGithubMetadataReaderSpecNames(unittest.TestCase):
    """Tests named per spec requirements using the canonical URL from the spec."""

    _URL = "https://github.com/myorg/myrepo.git"

    def _repo_data(self, **kwargs) -> dict:
        base = {"url": self._URL, "commit_sha": "sha1", "target": "main"}
        base.update(kwargs)
        return base

    def test_extract_owner_from_github_url(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data())
        self.assertEqual(result.owner, "myorg")

    def test_extract_repo_name_from_github_url(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data())
        self.assertEqual(result.repo_name, "myrepo")

    def test_maps_target_to_branch(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data(target="develop"))
        self.assertEqual(result.branch, "develop")

    def test_commit_sha_is_copied(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data(commit_sha="cafebabe"))
        self.assertEqual(result.commit_sha, "cafebabe")

    def test_default_author_name_when_missing(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data())
        self.assertEqual(result.author_name, "Unknown Author")

    def test_uses_provided_author_name(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data(author_name="Alice"))
        self.assertEqual(result.author_name, "Alice")

    def test_returns_repository_metadata_instance(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data())
        self.assertIsInstance(result, RepositoryMetadata)

    def test_commit_message_is_none(self):
        result = GithubMetadataReader().extract_from_repository(self._repo_data())
        self.assertIsNone(result.commit_message)


if __name__ == "__main__":
    unittest.main()
