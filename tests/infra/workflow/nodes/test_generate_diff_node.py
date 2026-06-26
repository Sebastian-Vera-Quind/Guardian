import unittest
from unittest.mock import MagicMock, patch

from src.domain.models import AgentState, DiffGenerationError
from src.infra.adapters.workflow.nodes.generate_diff import (
  node_generate_diff
)


class TestGenerateDiffNode(unittest.TestCase):
  """Tests para el nodo generate_diff."""

  def setUp(self):
    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "clone_path": "/tmp/guardian/uuid-123",
      "repository": {
        "commit_sha": "abc1234567890",
        "target": "def5678901234"
      }
    }

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_success(self, mock_inject):
    """T8: Generar diff exitosamente."""
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      return_value={
        "diff": {"file.py": {"additions": 5, "deletions": 2}},
        "project_tree": {"name": "root", "type": "directory"},
        "added_files": set()
      }
    )
    mock_inject.return_value = mock_service

    result = await node_generate_diff(self.state)

    assert "diff" in result
    assert "project_tree" in result
    assert "modified_lines" in result
    assert result["modified_lines"] == 7  # 5 + 2
    # _replaced_files debe ser limpiado
    assert "_replaced_files" not in result

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_with_replaced_files(self, mock_inject):
    """T8: Generar diff con archivos reemplazados."""
    self.state["_replaced_files"] = {"src/new.py"}
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      return_value={
        "diff": {},
        "project_tree": {"name": "root", "type": "directory"},
        "added_files": set()
      }
    )
    mock_inject.return_value = mock_service

    result = await node_generate_diff(self.state)

    # Verificar que files_modified_by_replacement fue pasado
    call_args = mock_service.generate_diff_and_tree.call_args
    assert call_args[1]["files_modified_by_replacement"] == {"src/new.py"}
    # _replaced_files debe ser limpiado
    assert "_replaced_files" not in result

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_missing_clone_path(self, mock_inject):
    """T8: Lanzar error si falta clone_path."""
    self.state.pop("clone_path")
    mock_inject.return_value = MagicMock()

    with self.assertRaises(DiffGenerationError) as ctx:
      await node_generate_diff(self.state)

    assert "clone_path" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_without_target(self, mock_inject):
    """T8: Generar diff sin target (HEAD como base)."""
    self.state["repository"] = {"commit_sha": "abc1234567890"}
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      return_value={
        "diff": {},
        "project_tree": {"name": "root", "type": "directory"},
        "added_files": set()
      }
    )
    mock_inject.return_value = mock_service

    result = await node_generate_diff(self.state)

    # Verificar que target_commit es None
    call_args = mock_service.generate_diff_and_tree.call_args
    assert call_args[1]["target_commit"] is None

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_service_error(self, mock_inject):
    """T8: Propagar error del servicio."""
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      side_effect=DiffGenerationError("Diff failed")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(DiffGenerationError) as ctx:
      await node_generate_diff(self.state)

    assert "Diff failed" in str(ctx.exception)

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_unexpected_error(self, mock_inject):
    """T8: Capturar error inesperado."""
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      side_effect=RuntimeError("Unexpected")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(DiffGenerationError) as ctx:
      await node_generate_diff(self.state)

    assert "Unexpected" in str(ctx.exception)

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_without_diff_in_result(self, mock_inject):
    """T8: Resultado sin diff (solo tree)."""
    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      return_value={
        "project_tree": {"name": "root", "type": "directory"},
        "added_files": set()
      }
    )
    mock_inject.return_value = mock_service

    result = await node_generate_diff(self.state)

    assert "diff" not in result
    assert "project_tree" in result
    # modified_lines no debe incluirse si no hay diff
    assert "modified_lines" not in result or result.get("modified_lines") == 0

  @patch("src.infra.adapters.workflow.nodes.generate_diff.inject")
  async def test_generate_diff_with_commit_sha_and_replaced_files_no_target(self, mock_inject):
    """BUGFIX: Generar diff para commit_sha + files_content sin target.

    Caso: Se recibe commit_sha (base) y files_content reemplazados,
    pero NO se recibe target. El diff debe comparar base contra
    working directory.
    """
    self.state["repository"] = {"commit_sha": "abc1234567890"}
    self.state["_replaced_files"] = {"src/new.py", "src/modified.py"}

    mock_service = MagicMock()
    mock_service.generate_diff_and_tree = MagicMock(
      return_value={
        "diff": {
          "src/new.py": {
            "additions": 10,
            "deletions": 0,
            "is_new": True,
            "is_deleted": False,
            "content": [
              {"status": "added", "line_number": 1, "content": "def func():"}
            ]
          },
          "src/modified.py": {
            "additions": 5,
            "deletions": 2,
            "is_new": False,
            "is_deleted": False,
            "content": [
              {"status": "added", "line_number": 10, "content": "new code"},
              {"status": "deleted", "line_number": 15, "content": "old code"}
            ]
          }
        },
        "project_tree": {"name": "root", "type": "directory"},
        "added_files": {"src/new.py"}
      }
    )
    mock_inject.return_value = mock_service

    result = await node_generate_diff(self.state)

    # Verificar que se generó diff
    assert "diff" in result
    assert len(result["diff"]) == 2

    # Verificar que target_commit es None (comparó contra HEAD)
    call_args = mock_service.generate_diff_and_tree.call_args
    assert call_args[1]["target_commit"] is None
    assert call_args[1]["base_commit"] == "abc1234567890"

    # Verificar que se pasaron los archivos reemplazados
    assert call_args[1]["files_modified_by_replacement"] == {"src/new.py", "src/modified.py"}

    # Verificar estructura del diff
    assert result["diff"]["src/new.py"]["is_new"] is True
    assert result["diff"]["src/modified.py"]["additions"] == 5
    assert result["diff"]["src/modified.py"]["deletions"] == 2

    # modified_lines debe ser suma de adiciones+deletions
    assert result["modified_lines"] == 17  # 10+0 + 5+2

    # _replaced_files debe ser limpiado
    assert "_replaced_files" not in result


if __name__ == "__main__":
  unittest.main()
