import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.models import AgentState, ClonePathError, CheckoutError
from src.infra.adapters.workflow.nodes.checkout_commit import (
  node_checkout_commit
)


class TestCheckoutCommitNode(unittest.TestCase):
  """Tests para el nodo checkout_commit."""

  def setUp(self):
    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "clone_path": "/tmp/guardian/uuid-123",
      "repository": {
        "commit_sha": "abc1234567890"
      }
    }

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_success(self, mock_inject):
    """T6: Hacer checkout exitosamente."""
    mock_service = MagicMock()
    mock_service.checkout_commit = MagicMock(return_value=None)
    mock_inject.return_value = mock_service

    result = await node_checkout_commit(self.state)

    assert result is self.state
    mock_service.checkout_commit.assert_called_once_with(
      "/tmp/guardian/uuid-123",
      "abc1234567890"
    )

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_missing_clone_path(self, mock_inject):
    """T6: Lanzar error si falta clone_path."""
    self.state.pop("clone_path")
    mock_inject.return_value = MagicMock()

    with self.assertRaises(ClonePathError) as ctx:
      await node_checkout_commit(self.state)

    assert "clone_path" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_missing_commit_sha(self, mock_inject):
    """T6: Lanzar error si falta commit_sha."""
    self.state["repository"] = {}
    mock_inject.return_value = MagicMock()

    with self.assertRaises(ClonePathError) as ctx:
      await node_checkout_commit(self.state)

    assert "commit_sha" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_invalid_commit(self, mock_inject):
    """T6: Lanzar CheckoutError si commit no existe."""
    mock_service = MagicMock()
    mock_service.checkout_commit = MagicMock(
      side_effect=CheckoutError("Commit not found")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(CheckoutError) as ctx:
      await node_checkout_commit(self.state)

    assert "not found" in str(ctx.exception).lower()

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_unexpected_error(self, mock_inject):
    """T6: Capturar error inesperado."""
    mock_service = MagicMock()
    mock_service.checkout_commit = MagicMock(
      side_effect=RuntimeError("Unexpected")
    )
    mock_inject.return_value = mock_service

    with self.assertRaises(CheckoutError) as ctx:
      await node_checkout_commit(self.state)

    assert "Unexpected" in str(ctx.exception)


class TestCheckoutCommitNodeWithObjectRepository(unittest.TestCase):
  """Tests con repository como objeto."""

  def setUp(self):
    repo_obj = MagicMock()
    repo_obj.commit_sha = "def5678901234"

    self.state: AgentState = {
      "project_code": "test-project",
      "project_id": "12345678-1234-1234-1234-123456789012",
      "clone_path": "/tmp/guardian/uuid-456",
      "repository": repo_obj
    }

  @patch("src.infra.adapters.workflow.nodes.checkout_commit.inject")
  async def test_checkout_commit_with_object(self, mock_inject):
    """T6: Checkout con repository como objeto."""
    mock_service = MagicMock()
    mock_service.checkout_commit = MagicMock(return_value=None)
    mock_inject.return_value = mock_service

    result = await node_checkout_commit(self.state)

    assert result is self.state
    mock_service.checkout_commit.assert_called_once_with(
      "/tmp/guardian/uuid-456",
      "def5678901234"
    )


if __name__ == "__main__":
  unittest.main()
