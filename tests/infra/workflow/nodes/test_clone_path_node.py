import pytest
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.domain.models import AgentState, ClonePathError, DiffGenerationError
from src.infra.adapters.workflow.nodes.clone_path import node_clone_task


@pytest.mark.asyncio
class TestClonePathNode:
  """Tests para node_clone_task."""

  def setup_method(self):
    """Configura directorios temporales."""
    self.test_dir = tempfile.TemporaryDirectory()

  def teardown_method(self):
    """Limpia directorios temporales."""
    self.test_dir.cleanup()

  async def test_node_clone_task_requires_load_to_clone(self):
    """Test: nodo requiere load_to='clone'."""
    state = AgentState(
      load_to="simple",
      repository={"url": "https://github.com/user/repo.git"},
    )

    with pytest.raises(ClonePathError):
      await node_clone_task(state)

  async def test_node_clone_task_calls_clone_service(self):
    """Test: nodo inyecta y llama CloneService."""
    state = AgentState(
      load_to="clone",
      repository={
        "url": "https://github.com/user/repo.git",
        "commit_sha": "abc123",
        "installation": "token"
      }
    )

    mock_service = MagicMock()
    mock_service.clone.return_value = {
      "clone_path": "/tmp/guardian/uuid",
      "project_tree": {"name": "root", "type": "directory"}
    }

    with patch("src.infra.adapters.workflow.nodes.clone_path.inject") as mock_inject:
      mock_inject.return_value = mock_service

      result = await node_clone_task(state)

      assert "clone_path" in result
      assert "project_tree" in result
      mock_service.clone.assert_called_once()

  async def test_node_clone_task_returns_expected_state(self):
    """Test: nodo retorna estado con clone_path, project_tree y diff."""
    state = AgentState(
      load_to="clone",
      repository={
        "url": "https://github.com/user/repo.git",
        "commit_sha": "abc123",
        "target": "def456"
      }
    )

    mock_service = MagicMock()
    mock_service.clone.return_value = {
      "clone_path": "/tmp/guardian/uuid",
      "project_tree": {"name": "root", "type": "directory"},
      "diff": {
        "file.py": {
          "is_new": False,
          "is_deleted": False,
          "additions": 1,
          "deletions": 0,
          "content": []
        }
      }
    }

    with patch("src.infra.adapters.workflow.nodes.clone_path.inject") as mock_inject:
      mock_inject.return_value = mock_service

      result = await node_clone_task(state)

      assert "clone_path" in result
      assert "project_tree" in result
      assert "diff" in result

  async def test_node_clone_task_logs_operations(self):
    """Test: nodo registra operaciones."""
    state = AgentState(
      load_to="clone",
      repository={
        "url": "https://github.com/user/repo.git",
        "commit_sha": "abc123",
        "target": "def456"
      }
    )

    mock_service = MagicMock()
    mock_service.clone.return_value = {
      "clone_path": "/tmp/guardian/uuid",
      "project_tree": {"name": "root", "type": "directory"},
      "diff": {}
    }

    with patch("src.infra.adapters.workflow.nodes.clone_path.inject") as mock_inject:
      with patch("src.infra.adapters.workflow.nodes.clone_path.logger") as mock_logger:
        mock_inject.return_value = mock_service

        await node_clone_task(state)

        assert mock_logger.info.call_count > 0

  async def test_node_clone_task_raises_clone_path_error_on_failure(self):
    """Test: nodo propaga ClonePathError."""
    state = AgentState(
      load_to="clone",
      repository={
        "url": "https://github.com/user/repo.git",
        "commit_sha": "abc123"
      }
    )

    mock_service = MagicMock()
    mock_service.clone.side_effect = ClonePathError("Clone failed")

    with patch("src.infra.adapters.workflow.nodes.clone_path.inject") as mock_inject:
      mock_inject.return_value = mock_service

      with pytest.raises(ClonePathError):
        await node_clone_task(state)

  async def test_node_clone_task_raises_diff_error_on_diff_failure(self):
    """Test: nodo propaga DiffGenerationError."""
    state = AgentState(
      load_to="clone",
      repository={
        "url": "https://github.com/user/repo.git",
        "commit_sha": "abc123",
        "target": "def456"
      }
    )

    mock_service = MagicMock()
    mock_service.clone.side_effect = DiffGenerationError("Diff failed")

    with patch("src.infra.adapters.workflow.nodes.clone_path.inject") as mock_inject:
      mock_inject.return_value = mock_service

      with pytest.raises(DiffGenerationError):
        await node_clone_task(state)
