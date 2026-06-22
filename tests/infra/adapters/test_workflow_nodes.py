import unittest
import asyncio

from src.domain.models import WorkflowState
from src.infra.adapters.workflow.nodes import (
    node_start, node_process, node_end
)


class TestWorkflowNodes(unittest.TestCase):
  """Test suite para nodos del workflow."""

  def setUp(self):
    """Configura estado inicial para las pruebas."""
    self.initial_state: WorkflowState = {
        "user_input": "test input",
        "processing_state": "pending",
        "current_node": "",
        "result": None,
        "errors": []
    }

  def test_node_start_returns_dict(self):
    """Valida que node_start retorna un diccionario."""
    result = asyncio.run(node_start(self.initial_state))
    self.assertIsInstance(result, dict)

  def test_node_start_updates_processing_state(self):
    """Valida que node_start actualiza processing_state a processing."""
    result = asyncio.run(node_start(self.initial_state))
    self.assertIn("processing_state", result)
    self.assertEqual(result["processing_state"], "processing")

  def test_node_start_sets_current_node(self):
    """Valida que node_start establece current_node a start."""
    result = asyncio.run(node_start(self.initial_state))
    self.assertIn("current_node", result)
    self.assertEqual(result["current_node"], "start")

  def test_node_process_returns_dict(self):
    """Valida que node_process retorna un diccionario."""
    result = asyncio.run(node_process(self.initial_state))
    self.assertIsInstance(result, dict)

  def test_node_process_sets_current_node(self):
    """Valida que node_process establece current_node a process."""
    result = asyncio.run(node_process(self.initial_state))
    self.assertIn("current_node", result)
    self.assertEqual(result["current_node"], "process")

  def test_node_process_sets_result(self):
    """Valida que node_process establece un resultado."""
    result = asyncio.run(node_process(self.initial_state))
    self.assertIn("result", result)
    self.assertIsNotNone(result["result"])
    self.assertIsInstance(result["result"], dict)

  def test_node_process_updates_processing_state_to_done(self):
    """Valida que node_process actualiza processing_state a done."""
    result = asyncio.run(node_process(self.initial_state))
    self.assertIn("processing_state", result)
    self.assertEqual(result["processing_state"], "done")

  def test_node_end_returns_dict(self):
    """Valida que node_end retorna un diccionario."""
    result = asyncio.run(node_end(self.initial_state))
    self.assertIsInstance(result, dict)

  def test_node_end_sets_current_node(self):
    """Valida que node_end establece current_node a end."""
    result = asyncio.run(node_end(self.initial_state))
    self.assertIn("current_node", result)
    self.assertEqual(result["current_node"], "end")

  def test_nodes_are_async_functions(self):
    """Valida que los nodos son funciones asincrónicas."""
    import asyncio
    self.assertTrue(asyncio.iscoroutinefunction(node_start))
    self.assertTrue(asyncio.iscoroutinefunction(node_process))
    self.assertTrue(asyncio.iscoroutinefunction(node_end))


if __name__ == "__main__":
  unittest.main()
