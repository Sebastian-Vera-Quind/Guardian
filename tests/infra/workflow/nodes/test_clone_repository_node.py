import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.models import AgentState, ClonePathError
from src.infra.adapters.workflow.nodes.clone_repository import (
  node_clone_repository
)


class TestCloneRepositoryNode(unittest.TestCase):
  """Tests para el nodo clone_repository."""

  def setUp(self):
    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "repository": {
        "url": "https://github.com/user/repo.git",
        "installation": None
      }
    }

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_success(self, mock_inject):
    """T5: Clonar repositorio exitosamente."""
    mock_service = MagicMock()
    mock_service.clone_repository = MagicMock(
      return_value="/tmp/guardian/uuid-123"
    )
    mock_inject.return_value = mock_service

    result = await node_clone_repository(self.state)

    assert result["clone_path"] == "/tmp/guardian/uuid-123"
    mock_service.clone_repository.assert_called_once_with(
      "https://github.com/user/repo.git",
      None
    )

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_with_token(self, mock_inject):
    """T5: Clonar repositorio con token de autenticación."""
    self.state["repository"]["installation"] = "ghu_token123"
    mock_service = MagicMock()
    mock_service.clone_repository = MagicMock(
      return_value="/tmp/guardian/uuid-456"
    )
    mock_inject.return_value = mock_service

    result = await node_clone_repository(self.state)

    assert result["clone_path"] == "/tmp/guardian/uuid-456"
    mock_service.clone_repository.assert_called_once_with(
      "https://github.com/user/repo.git",
      "ghu_token123"
    )

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_missing_url(self, mock_inject):
    """T5: Lanzar error si falta URL del repositorio."""
    self.state["repository"] = {"installation": "token"}
    mock_inject.return_value = MagicMock()

    with self.assertRaises(ClonePathError) as ctx:
      await node_clone_repository(self.state)

    assert "url" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_service_error(self, mock_inject):
    """T5: Propagar error de clonación."""
    mock_service = MagicMock()
    mock_service.clone_repository = MagicMock(
      side_effect=ClonePathError("Clone failed")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(ClonePathError) as ctx:
      await node_clone_repository(self.state)

    assert "Clone failed" in str(ctx.exception)

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_unexpected_error(self, mock_inject):
    """T5: Capturar error inesperado y lanzar ClonePathError."""
    mock_service = MagicMock()
    mock_service.clone_repository = MagicMock(
      side_effect=RuntimeError("Unexpected")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(ClonePathError) as ctx:
      await node_clone_repository(self.state)

    assert "Unexpected" in str(ctx.exception)


class TestCloneRepositoryNodeWithObjectRepository(unittest.TestCase):
  """Tests con repository como objeto (no dict)."""

  def setUp(self):
    repo_obj = MagicMock()
    repo_obj.url = "https://github.com/user/repo.git"
    repo_obj.installation = None

    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "repository": repo_obj
    }

  @patch("src.infra.adapters.workflow.nodes.clone_repository.inject")
  async def test_clone_repository_with_object(self, mock_inject):
    """T5: Clonar con repository como objeto."""
    mock_service = MagicMock()
    mock_service.clone_repository = MagicMock(
      return_value="/tmp/guardian/uuid-789"
    )
    mock_inject.return_value = mock_service

    result = await node_clone_repository(self.state)

    assert result["clone_path"] == "/tmp/guardian/uuid-789"
    mock_service.clone_repository.assert_called_once()


if __name__ == "__main__":
  unittest.main()
