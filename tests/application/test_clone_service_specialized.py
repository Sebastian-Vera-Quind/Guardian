import unittest
from unittest.mock import MagicMock, patch

from src.application.clone.clone_service import CloneService
from src.domain.models import ClonePathError, DiffGenerationError


class TestCloneServiceSpecializedMethods(unittest.TestCase):
  """Tests para los métodos especializados de CloneService."""

  def setUp(self):
    """Crear mock del RepositoryCloner."""
    self.mock_repo_cloner = MagicMock()
    self.service = CloneService(self.mock_repo_cloner)

  def test_clone_repository_success(self):
    """T2: clone_repository retorna ruta."""
    self.mock_repo_cloner.clone = MagicMock(
      return_value="/tmp/guardian/uuid-123"
    )

    result = self.service.clone_repository(
      "https://github.com/user/repo.git",
      None
    )

    assert result == "/tmp/guardian/uuid-123"
    self.mock_repo_cloner.clone.assert_called_once()

  def test_clone_repository_with_token(self):
    """T2: clone_repository pasa token al cloner."""
    self.mock_repo_cloner.clone = MagicMock(
      return_value="/tmp/guardian/uuid-456"
    )

    result = self.service.clone_repository(
      "https://github.com/user/repo.git",
      "ghu_token123"
    )

    assert result == "/tmp/guardian/uuid-456"
    self.mock_repo_cloner.clone.assert_called_once_with(
      "https://github.com/user/repo.git",
      "ghu_token123"
    )

  def test_clone_repository_propagates_error(self):
    """T2: clone_repository propaga ClonePathError."""
    self.mock_repo_cloner.clone = MagicMock(
      side_effect=ClonePathError("Clone failed")
    )

    with self.assertRaises(ClonePathError):
      self.service.clone_repository(
        "https://github.com/user/repo.git",
        None
      )

  def test_checkout_commit_success(self):
    """T2: checkout_commit llama al cloner."""
    self.mock_repo_cloner.checkout = MagicMock(return_value=None)

    self.service.checkout_commit("/tmp/guardian/uuid-123", "abc123")

    self.mock_repo_cloner.checkout.assert_called_once_with(
      "/tmp/guardian/uuid-123",
      "abc123"
    )

  def test_checkout_commit_propagates_error(self):
    """T2: checkout_commit propaga error."""
    self.mock_repo_cloner.checkout = MagicMock(
      side_effect=Exception("Checkout failed")
    )

    with self.assertRaises(Exception):
      self.service.checkout_commit("/tmp/guardian/uuid-123", "abc123")

  @patch("src.application.clone.clone_service.FileReplacer")
  def test_replace_files_content_success(self, mock_replacer):
    """T2: replace_files_content retorna set de archivos."""
    mock_replacer.replace_files = MagicMock(
      return_value={"src/main.py", "utils.py"}
    )

    files_content = [
      {"path": "src/main.py", "content": "print('hello')"},
      {"path": "utils.py", "content": "def helper(): pass"}
    ]

    result = self.service.replace_files_content(
      "/tmp/guardian/uuid-123",
      files_content
    )

    assert result == {"src/main.py", "utils.py"}
    mock_replacer.replace_files.assert_called_once()

  @patch("src.application.clone.clone_service.FileReplacer")
  def test_replace_files_content_error(self, mock_replacer):
    """T2: replace_files_content propaga error."""
    mock_replacer.replace_files = MagicMock(
      side_effect=OSError("Write failed")
    )

    with self.assertRaises(ClonePathError):
      self.service.replace_files_content(
        "/tmp/guardian/uuid-123",
        [{"path": "file.py", "content": "content"}]
      )

  @patch("src.application.clone.clone_service.TreeBuilder")
  def test_generate_diff_and_tree_success(self, mock_tree_builder):
    """T2: generate_diff_and_tree retorna dict completo."""
    def mock_get_diff(repo_path, base_commit, target_commit, callback):
      callback("file.py", {
        "additions": 5,
        "deletions": 2,
        "is_new": False,
        "is_deleted": False,
        "content": []
      })

    self.mock_repo_cloner.get_diff = MagicMock(side_effect=mock_get_diff)
    mock_tree_builder.build_tree = MagicMock(
      return_value={"name": "root", "type": "directory"}
    )

    result = self.service.generate_diff_and_tree(
      repo_path="/tmp/guardian/uuid-123",
      base_commit="abc123",
      target_commit="def456"
    )

    assert "diff" in result
    assert "project_tree" in result
    assert "added_files" in result
    assert isinstance(result["added_files"], set)

  @patch("src.application.clone.clone_service.TreeBuilder")
  def test_generate_diff_and_tree_without_target(self, mock_tree_builder):
    """T2: generate_diff_and_tree sin target no llama get_diff."""
    mock_tree_builder.build_tree = MagicMock(
      return_value={"name": "root", "type": "directory"}
    )

    result = self.service.generate_diff_and_tree(
      repo_path="/tmp/guardian/uuid-123",
      base_commit=None,
      target_commit=None
    )

    # No debe llamar get_diff sin target_commit
    self.mock_repo_cloner.get_diff.assert_not_called()
    assert "diff" not in result
    assert "project_tree" in result

  @patch("src.application.clone.clone_service.TreeBuilder")
  def test_generate_diff_and_tree_with_replaced_files(self, mock_tree_builder):
    """T2: generate_diff_and_tree incluye archivos reemplazados."""
    def mock_get_diff(repo_path, base_commit, target_commit, callback):
      callback("existing.py", {
        "additions": 1,
        "deletions": 0,
        "is_new": False,
        "is_deleted": False,
        "content": []
      })

    self.mock_repo_cloner.get_diff = MagicMock(side_effect=mock_get_diff)
    mock_tree_builder.build_tree = MagicMock(
      return_value={"name": "root", "type": "directory"}
    )

    result = self.service.generate_diff_and_tree(
      repo_path="/tmp/guardian/uuid-123",
      base_commit="abc123",
      target_commit="def456",
      files_modified_by_replacement={"new_file.py"}
    )

    # Verificar que TreeBuilder fue llamado con archivos reemplazados
    call_args = mock_tree_builder.build_tree.call_args
    modified_set = call_args[1].get("modified_files_set")
    assert "new_file.py" in modified_set

  @patch("src.application.clone.clone_service.TreeBuilder")
  def test_generate_diff_and_tree_with_replaced_files_no_target(self, mock_tree_builder):
    """BUGFIX: generate_diff_and_tree genera diff cuando hay replaced_files y target=None.

    Caso de uso: commit_sha + files_content sin target.
    El diff debe comparar base_commit contra el working directory.
    """
    def mock_get_diff(repo_path, base_commit, target_commit, callback):
      # Simular que se comparó base_commit contra HEAD
      callback("src/modified.py", {
        "additions": 3,
        "deletions": 1,
        "is_new": False,
        "is_deleted": False,
        "content": [
          {"status": "added", "line_number": 5, "content": "new line"},
          {"status": "deleted", "line_number": 10, "content": "old line"}
        ]
      })
      callback("src/new.py", {
        "additions": 10,
        "deletions": 0,
        "is_new": True,
        "is_deleted": False,
        "content": [
          {"status": "added", "line_number": 1, "content": "def function():"}
        ]
      })

    self.mock_repo_cloner.get_diff = MagicMock(side_effect=mock_get_diff)
    mock_tree_builder.build_tree = MagicMock(
      return_value={"name": "root", "type": "directory", "files": []}
    )

    result = self.service.generate_diff_and_tree(
      repo_path="/tmp/guardian/uuid-123",
      base_commit="abc123",
      target_commit=None,  # SIN target explícito
      files_modified_by_replacement={"src/modified.py", "src/new.py"}
    )

    # BR1: Debe generar diff
    assert "diff" in result
    assert len(result["diff"]) > 0

    # BR2: Diff contiene adiciones/deletions
    assert "src/modified.py" in result["diff"]
    assert result["diff"]["src/modified.py"]["additions"] == 3
    assert result["diff"]["src/modified.py"]["deletions"] == 1

    # BR4: Archivo nuevo tiene is_new=true
    assert result["diff"]["src/new.py"]["is_new"] is True

    # BR5: Estructura JSON correcta
    assert "content" in result["diff"]["src/modified.py"]
    for item in result["diff"]["src/modified.py"]["content"]:
      assert "status" in item
      assert "line_number" in item
      assert "content" in item

    # Verificar que get_diff fue llamado con target_commit=None
    call_args = self.mock_repo_cloner.get_diff.call_args
    assert call_args[1]["target_commit"] is None

    # Archivos reemplazados deben estar en modified_files para TreeBuilder
    tree_call_args = mock_tree_builder.build_tree.call_args
    modified_set = tree_call_args[1].get("modified_files_set")
    assert "src/modified.py" in modified_set
    assert "src/new.py" in modified_set

  @patch("src.application.clone.clone_service.TreeBuilder")
  def test_generate_diff_and_tree_error(self, mock_tree_builder):
    """T2: generate_diff_and_tree propaga error."""
    self.mock_repo_cloner.get_diff = MagicMock(
      side_effect=DiffGenerationError("Diff failed")
    )

    with self.assertRaises(DiffGenerationError):
      self.service.generate_diff_and_tree(
        repo_path="/tmp/guardian/uuid-123",
        base_commit="abc123",
        target_commit="def456"
      )

if __name__ == "__main__":
  unittest.main()
