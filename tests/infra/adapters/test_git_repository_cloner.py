import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from git import Repo
from git.exc import GitCommandError

from src.infra.adapters.git import GitRepositoryCloner
from src.domain.models import ClonePathError, CheckoutError, DiffGenerationError


class TestGitRepositoryCloner(unittest.TestCase):
  """Tests para GitRepositoryCloner."""

  def setUp(self):
    """Configura directorios temporales."""
    self.test_dir = tempfile.TemporaryDirectory()
    self.addCleanup(self.test_dir.cleanup)

  def test_clone_public_repo_creates_directory(self):
    """Test: clonar repositorio público crea directorio en /tmp/guardian."""
    cloner = GitRepositoryCloner()

    with patch("git.Repo.clone_from") as mock_clone:
      clone_path = cloner.clone("https://github.com/user/repo.git")

      self.assertIsNotNone(clone_path)
      self.assertTrue(clone_path.startswith("/tmp/guardian/"))
      mock_clone.assert_called_once()

  def test_clone_private_repo_with_token(self):
    """Test: clonar repositorio privado usa token en URL."""
    cloner = GitRepositoryCloner()

    with patch("git.Repo.clone_from") as mock_clone:
      token = "github-token-12345"
      clone_path = cloner.clone(
        "https://github.com/user/repo.git",
        installation_token=token
      )

      call_args = mock_clone.call_args
      called_url = call_args[0][0]

      self.assertIn("x-access-token", called_url)
      self.assertIn(token, called_url)
      self.assertFalse(called_url.startswith("https://github.com/"))

  def test_clone_invalid_url_raises_error(self):
    """Test: clonar URL inválida lanza ClonePathError."""
    cloner = GitRepositoryCloner()

    with patch("git.Repo.clone_from") as mock_clone:
      mock_clone.side_effect = GitCommandError("git", 1, "Repository not found")

      with self.assertRaises(ClonePathError):
        cloner.clone("https://github.com/invalid/repo.git")

  def test_checkout_valid_commit(self):
    """Test: checkout a commit válido ejecuta correctamente."""
    cloner = GitRepositoryCloner()

    with tempfile.TemporaryDirectory() as repo_dir:
      repo = Repo.init(repo_dir)

      repo.index.commit("Initial commit")
      commit_sha = repo.head.commit.hexsha

      with patch.object(Repo, "__init__", return_value=None) as mock_init:
        with patch.object(Repo, "git") as mock_git:
          cloner.checkout(repo_dir, commit_sha)
          mock_git.checkout.assert_called_once_with(commit_sha)

  def test_checkout_invalid_commit_raises_error(self):
    """Test: checkout a commit inválido lanza CheckoutError."""
    cloner = GitRepositoryCloner()

    with patch("git.Repo") as mock_repo_class:
      mock_repo = MagicMock()
      mock_repo.git.checkout.side_effect = GitCommandError(
        "git", 1, "Invalid commit"
      )
      mock_repo_class.return_value = mock_repo

      with self.assertRaises(CheckoutError):
        cloner.checkout("/tmp/repo", "invalid-commit-sha")

  def test_get_diff_uses_callback_pattern(self):
    """Test: get_diff() usa pattern de callback en lugar de retornar."""
    cloner = GitRepositoryCloner()
    callback = MagicMock()

    with tempfile.TemporaryDirectory() as repo_dir:
      # Crea un repo git real para testear
      repo = Repo.init(repo_dir)

      # Crea un archivo y hace commit
      file_path = os.path.join(repo_dir, "test.py")
      with open(file_path, "w") as f:
        f.write("line 1\nline 2\n")
      repo.index.add(["test.py"])
      base_commit = repo.index.commit("Initial commit")

      # Modifica el archivo
      with open(file_path, "w") as f:
        f.write("line 1\nmodified line\nline 3\n")
      repo.index.add(["test.py"])
      target_commit = repo.index.commit("Modified file")

      # Llama get_diff con un callback
      cloner.get_diff(
        repo_path=repo_dir,
        target_commit=target_commit.hexsha,
        callback=callback,
        base_commit=base_commit.hexsha
      )

      # Verifica que callback fue llamado
      callback.assert_called()

      # Verifica que callback recibe file_path y DiffFile
      call_args = callback.call_args_list[0]
      file_name = call_args[0][0]
      diff_file = call_args[0][1]

      self.assertEqual(file_name, "test.py")
      self.assertIsInstance(diff_file, dict)
      self.assertIn("is_new", diff_file)
      self.assertIn("is_deleted", diff_file)
      self.assertIn("additions", diff_file)
      self.assertIn("deletions", diff_file)
      self.assertIn("content", diff_file)

  def test_get_diff_callback_structure(self):
    """Test: callback recibe estructuras DiffFile con todos los campos requeridos."""
    cloner = GitRepositoryCloner()
    callback_data = []

    def capture_callback(file_path, diff_file):
      callback_data.append((file_path, diff_file))

    with tempfile.TemporaryDirectory() as repo_dir:
      repo = Repo.init(repo_dir)

      # Commit inicial
      file1 = os.path.join(repo_dir, "file1.py")
      with open(file1, "w") as f:
        f.write("original content\n")
      repo.index.add(["file1.py"])
      base_commit = repo.index.commit("Initial")

      # Modifica archivo1
      with open(file1, "w") as f:
        f.write("original content\nmodified line\n")
      repo.index.add(["file1.py"])
      target_commit = repo.index.commit("Modify file1")

      cloner.get_diff(
        repo_path=repo_dir,
        target_commit=target_commit.hexsha,
        callback=capture_callback,
        base_commit=base_commit.hexsha
      )

      # Verifica que callback fue invocado
      self.assertGreater(len(callback_data), 0)

      # Verifica estructura de cada DiffFile
      for file_path, diff_file in callback_data:
        self.assertIsInstance(file_path, str)
        self.assertIsInstance(diff_file, dict)

        # Verifica que todos los campos requeridos existen
        required_fields = ["is_new", "is_deleted", "additions", "deletions", "content"]
        for field in required_fields:
          self.assertIn(field, diff_file)

        # Verifica tipos de datos
        self.assertIsInstance(diff_file["is_new"], bool)
        self.assertIsInstance(diff_file["is_deleted"], bool)
        self.assertIsInstance(diff_file["additions"], int)
        self.assertIsInstance(diff_file["deletions"], int)
        self.assertIsInstance(diff_file["content"], list)

  def test_get_diff_raises_error_on_invalid_commit(self):
    """Test: get_diff() lanza DiffGenerationError si commit es inválido."""
    cloner = GitRepositoryCloner()
    callback = MagicMock()

    with patch("git.Repo") as mock_repo_class:
      mock_repo = MagicMock()
      mock_repo.commit.side_effect = GitCommandError("git", 1, "Invalid commit")
      mock_repo_class.return_value = mock_repo

      with self.assertRaises(DiffGenerationError):
        cloner.get_diff(
          repo_path="/tmp/repo",
          target_commit="invalid-target",
          callback=callback,
          base_commit="invalid-base"
        )


if __name__ == "__main__":
  unittest.main()
