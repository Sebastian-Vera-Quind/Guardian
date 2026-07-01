import asyncio
import unittest
from unittest.mock import MagicMock, patch

from src.domain.models.project_fields import ProjectFields
from src.domain.models.retrieved_context import RetrievedContext
from src.infra.adapters.workflow.nodes.rag_context import (
  _extract_contents,
  node_rag_context,
)


def _run(coro):
  return asyncio.run(coro)


def _make_ctx(active_rules=None, quality_gates=None,
              constraints=None, nfr_definition=None,
              fitness_functions=None):
  return RetrievedContext(
    active_rules=active_rules or ["default rule"],
    quality_gates=quality_gates,
    constraints=constraints,
    nfr_definition=nfr_definition,
    fitness_functions=fitness_functions,
  )


class TestNodeRaisesWhenProjectCodeMissing(unittest.TestCase):

  def test_node_raises_when_project_code_missing(self):
    state = {}
    with self.assertRaises(ValueError):
      _run(node_rag_context(state))

  def test_node_raises_when_project_code_empty(self):
    state = {"project_code": ""}
    with self.assertRaises(ValueError):
      _run(node_rag_context(state))


class TestExtractContents(unittest.TestCase):

  def test_node_extracts_contents_simple_path(self):
    state = {
      "load_to": "simple",
      "files_content": [
        {"path": "a.py", "content": "def foo(): pass"},
        {"path": "b.py", "content": "x = 1"},
      ],
    }
    result = _extract_contents(state)
    self.assertIn("def foo(): pass", result)
    self.assertIn("x = 1", result)

  def test_node_extracts_contents_clone_path(self):
    state = {
      "load_to": "clone",
      "diff": {
        "a.py": {
          "content": [
            {"status": "added", "content": "new line", "line_number": 1},
            {"status": "deleted", "content": "old line", "line_number": 2},
            {"status": "modified", "content": "mod line", "line_number": 3},
          ]
        }
      },
    }
    result = _extract_contents(state)
    self.assertIn("new line", result)
    self.assertIn("mod line", result)
    self.assertNotIn("old line", result)

  def test_node_extracts_empty_contents_when_no_data(self):
    state = {"load_to": "simple", "files_content": []}
    result = _extract_contents(state)
    self.assertEqual(result, [])


class TestNodeWritesAllStateFields(unittest.TestCase):

  def test_node_writes_all_state_fields(self):
    mock_service = MagicMock()
    mock_service.retrieve.return_value = _make_ctx(
      active_rules=["rule1"],
      quality_gates={"min": 80},
      constraints=None,
      nfr_definition=None,
      fitness_functions=["f1"],
    )

    state = {
      "project_code": "PROJ",
      "load_to": "simple",
      "files_content": [{"path": "a.py", "content": "code"}],
    }

    with patch(
      "src.infra.adapters.workflow.nodes.rag_context.inject",
      return_value=mock_service,
    ):
      result = _run(node_rag_context(state))

    self.assertEqual(result["active_rules"], ["rule1"])
    self.assertEqual(result["quality_gates"], {"min": 80})
    self.assertIsNone(result["constraints"])
    self.assertIsNone(result["nfr_definition"])
    self.assertEqual(result["active_fitness_functions"], ["f1"])


if __name__ == "__main__":
  unittest.main()
