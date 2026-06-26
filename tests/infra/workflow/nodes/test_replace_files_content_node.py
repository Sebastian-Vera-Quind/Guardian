import unittest
from unittest.mock import MagicMock, patch

from src.domain.models import AgentState, ClonePathError, FileContent
from src.infra.adapters.workflow.nodes.replace_files_content import (
  node_replace_files_content
)


class TestReplaceFilesContentNode(unittest.TestCase):
  """Tests para el nodo replace_files_content."""

  def setUp(self):
    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "clone_path": "/tmp/guardian/uuid-123",
      "files_content": [
        {"path": "src/main.py", "content": "print('hello')"},
        {"path": "src/utils.py", "content": "def helper(): pass"}
      ]
    }

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_success(self, mock_inject):
    """T7: Reemplazar archivos exitosamente."""
    mock_service = MagicMock()
    mock_service.replace_files_content = MagicMock(
      return_value={"src/main.py", "src/utils.py"}
    )
    mock_inject.return_value = mock_service

    result = await node_replace_files_content(self.state)

    assert result["_replaced_files"] == {"src/main.py", "src/utils.py"}
    mock_service.replace_files_content.assert_called_once()

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_empty_files(self, mock_inject):
    """T7: Manejo de files_content vacío."""
    self.state["files_content"] = []
    mock_inject.return_value = MagicMock()

    result = await node_replace_files_content(self.state)

    assert result["_replaced_files"] == set()

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_missing_clone_path(self, mock_inject):
    """T7: Lanzar error si falta clone_path."""
    self.state.pop("clone_path")
    mock_inject.return_value = MagicMock()

    with self.assertRaises(ClonePathError) as ctx:
      await node_replace_files_content(self.state)

    assert "clone_path" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_service_error(self, mock_inject):
    """T7: Propagar error del servicio."""
    mock_service = MagicMock()
    mock_service.replace_files_content = MagicMock(
      side_effect=ClonePathError("Write failed")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(ClonePathError) as ctx:
      await node_replace_files_content(self.state)

    assert "Write failed" in str(ctx.exception)

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_unexpected_error(self, mock_inject):
    """T7: Capturar error inesperado."""
    mock_service = MagicMock()
    mock_service.replace_files_content = MagicMock(
      side_effect=RuntimeError("Unexpected")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(ClonePathError) as ctx:
      await node_replace_files_content(self.state)

    assert "Unexpected" in str(ctx.exception)

  @patch("src.infra.adapters.workflow.nodes.replace_files_content.inject")
  async def test_replace_files_content_removes_replaced_files_flag(
    self,
    mock_inject
  ):
    """T7: Flag _replaced_files se mantiene en estado."""
    mock_service = MagicMock()
    replaced = {"file1.py", "file2.py"}
    mock_service.replace_files_content = MagicMock(return_value=replaced)
    mock_inject.return_value = mock_service

    result = await node_replace_files_content(self.state)

    assert "_replaced_files" in result
    assert result["_replaced_files"] == replaced


if __name__ == "__main__":
  unittest.main()
