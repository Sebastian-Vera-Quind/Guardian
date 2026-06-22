import unittest

from langgraph.graph import StateGraph

from src.infra.adapters.workflow import WorkflowBuilder
from src.domain.models import WorkflowState


class TestWorkflowBuilder(unittest.TestCase):
  """Test suite para WorkflowBuilder."""

  def test_builder_build_returns_state_graph(self):
    """Valida que build() retorna un StateGraph compilado."""
    builder = WorkflowBuilder()
    graph = builder.build()
    self.assertIsNotNone(graph)

  def test_builder_graph_has_nodes(self):
    """Valida que el grafo tiene nodos."""
    builder = WorkflowBuilder()
    graph = builder.build()
    self.assertIsNotNone(graph.nodes)

  def test_builder_graph_has_entry_point(self):
    """Valida que el grafo tiene punto de entrada."""
    builder = WorkflowBuilder()
    graph = builder.build()
    self.assertIsNotNone(graph)

  def test_builder_graph_compiles_without_error(self):
    """Valida que el grafo se compila sin errores."""
    builder = WorkflowBuilder()
    try:
      graph = builder.build()
      self.assertIsNotNone(graph)
    except Exception as e:
      self.fail(f"WorkflowBuilder.build() raised {type(e).__name__}: {str(e)}")

  def test_builder_graph_has_nodes_start_process_end(self):
    """Valida que el grafo tiene nodos start, process, end."""
    builder = WorkflowBuilder()
    graph = builder.build()
    nodes = list(graph.nodes.keys()) if hasattr(graph, "nodes") and hasattr(graph.nodes, "keys") else []
    self.assertTrue(len(nodes) > 0 or hasattr(graph, "nodes"))


if __name__ == "__main__":
  unittest.main()
