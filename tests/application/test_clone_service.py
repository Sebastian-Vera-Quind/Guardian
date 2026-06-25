import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

from src.application.clone import CloneService
from src.domain.models import ClonePathError, DiffGenerationError, DiffFile


class TestCloneService(unittest.TestCase):
  """Tests para CloneService."""

  def setUp(self):
    """Configura mocks de dependencias."""
    self.mock_cloner = MagicMock()
    self.service = CloneService(self.mock_cloner)

  def test_clone_orchestrates_all_steps(self):
    """Test: clone() orquesta clonación, checkout, diff y tree."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      # Simula que el callback se llama con un archivo modificado
      callback("file.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 1,
        "deletions": 0,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        installation_token="token",
        commit_sha="abc123",
        target="def456"
      )

      self.assertIn("clone_path", result)
      self.assertIn("project_tree", result)
      self.assertIn("diff", result)
      self.assertEqual(result["clone_path"], clone_dir)
      self.mock_cloner.clone.assert_called_once()
      self.mock_cloner.checkout.assert_called_once()
      self.mock_cloner.get_diff.assert_called_once()

  def test_clone_with_target_calls_get_diff(self):
    """Test: clone con target llama get_diff con callback."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    callback_called = []

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback_called.append(True)
      callback("file.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 1,
        "deletions": 0,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      self.assertTrue(callback_called)
      self.assertIn("diff", result)
      self.mock_cloner.get_diff.assert_called_once()

  def test_clone_accumulates_diff_in_callback(self):
    """Test: clone acumula diff en dict mediante callback."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback("file1.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 1,
        "deletions": 0,
        "content": []
      })
      callback("file2.py", {
        "is_new": True,
        "is_deleted": False,
        "additions": 5,
        "deletions": 0,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      self.assertIn("diff", result)
      self.assertEqual(len(result["diff"]), 2)
      self.assertIn("file1.py", result["diff"])
      self.assertIn("file2.py", result["diff"])

  def test_clone_respects_installation_token(self):
    """Test: token de instalación se pasa a cloner."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      with patch("src.application.clone.clone_service.FileExcluder"):
        mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

        token = "ghs_install_token_123"
        self.service.clone(
          "https://github.com/user/repo.git",
          installation_token=token,
          commit_sha="abc123"
        )

        call_args = self.mock_cloner.clone.call_args
        self.assertEqual(call_args[0][1], token)

  def test_clone_handles_clone_error(self):
    """Test: ClonePathError se propaga."""
    self.mock_cloner.clone.side_effect = ClonePathError("Clone failed")

    with self.assertRaises(ClonePathError):
      self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123"
      )

  def test_clone_handles_diff_generation_error(self):
    """Test: DiffGenerationError se propaga."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir
    self.mock_cloner.get_diff.side_effect = DiffGenerationError("Diff failed")

    with patch("src.application.clone.clone_service.TreeBuilder"):
      with self.assertRaises(DiffGenerationError):
        self.service.clone(
          "https://github.com/user/repo.git",
          commit_sha="abc123",
          target="def456"
        )

  def test_clone_identifies_added_files_from_diff(self):
    """Test: clone identifica archivos nuevos del diff."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback("newfile.py", {
        "is_new": True,
        "is_deleted": False,
        "additions": 10,
        "deletions": 0,
        "content": []
      })
      callback("existing.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 2,
        "deletions": 1,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      # Verificar que TreeBuilder fue llamado con added_files_set
      tree_call_args = mock_tb.build_tree.call_args
      self.assertIsNotNone(tree_call_args[1].get("added_files_set"))

  def test_clone_identifies_modified_files_from_diff(self):
    """Test: clone identifica archivos modificados del diff."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback("modified.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 2,
        "deletions": 1,
        "content": []
      })
      callback("newfile.py", {
        "is_new": True,
        "is_deleted": False,
        "additions": 10,
        "deletions": 0,
        "content": []
      })
      callback("deleted.py", {
        "is_new": False,
        "is_deleted": True,
        "additions": 0,
        "deletions": 5,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      # Verificar que TreeBuilder fue llamado con modified_files_set
      tree_call_args = mock_tb.build_tree.call_args
      modified_files = tree_call_args[1].get("modified_files_set")
      self.assertIsNotNone(modified_files)
      self.assertIn("modified.py", modified_files)
      self.assertNotIn("newfile.py", modified_files)
      self.assertNotIn("deleted.py", modified_files)

  def test_clone_distinguishes_new_and_modified_files(self):
    """Test: clone distingue archivos nuevos de modificados."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback("new.py", {
        "is_new": True,
        "is_deleted": False,
        "additions": 10,
        "deletions": 0,
        "content": []
      })
      callback("modified.py", {
        "is_new": False,
        "is_deleted": False,
        "additions": 2,
        "deletions": 1,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      tree_call_args = mock_tb.build_tree.call_args
      added_files = tree_call_args[1].get("added_files_set")
      modified_files = tree_call_args[1].get("modified_files_set")

      self.assertIn("new.py", added_files)
      self.assertNotIn("new.py", modified_files)
      self.assertIn("modified.py", modified_files)
      self.assertNotIn("modified.py", added_files)

  def test_clone_ignores_deleted_files_from_modified(self):
    """Test: archivos eliminados no se consideran modificados."""
    clone_dir = "/tmp/guardian/test-uuid"
    self.mock_cloner.clone.return_value = clone_dir

    def get_diff_side_effect(base_commit, target_commit, repo_path, callback):
      callback("deleted.py", {
        "is_new": False,
        "is_deleted": True,
        "additions": 0,
        "deletions": 5,
        "content": []
      })

    self.mock_cloner.get_diff.side_effect = get_diff_side_effect

    with patch("src.application.clone.clone_service.TreeBuilder") as mock_tb:
      mock_tb.build_tree.return_value = {"name": "root", "type": "directory"}

      result = self.service.clone(
        "https://github.com/user/repo.git",
        commit_sha="abc123",
        target="def456"
      )

      tree_call_args = mock_tb.build_tree.call_args
      modified_files = tree_call_args[1].get("modified_files_set")

      # modified_files puede ser None o un set vacío
      if modified_files is not None:
        self.assertNotIn("deleted.py", modified_files)
      else:
        # Si es None, significa que no hay archivos modificados, lo cual es correcto
        self.assertIsNone(modified_files)


if __name__ == "__main__":
  unittest.main()
