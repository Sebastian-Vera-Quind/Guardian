import unittest
import asyncio

from src.domain.models import WorkflowState, WorkflowEvent
from src.infra.adapters.workflow import WorkflowBuilder, WorkflowEngine


class TestWorkflowEngine(unittest.TestCase):
  """Test suite para WorkflowEngine."""

  def setUp(self):
    """Configura builder y engine para las pruebas."""
    builder = WorkflowBuilder()
    self.graph = builder.build()
    self.engine = WorkflowEngine(self.graph)
    self.initial_state: WorkflowState = {
        "user_input": "test input",
        "processing_state": "pending",
        "current_node": "",
        "result": None,
        "errors": []
    }

  def test_engine_initializes_with_graph(self):
    """Valida que el engine se inicializa con un grafo."""
    self.assertIsNotNone(self.engine.graph)

  def test_engine_execute_and_stream_is_async_generator(self):
    """Valida que execute_and_stream es un generador asincrónico."""
    import asyncio
    gen = self.engine.execute_and_stream(self.initial_state)
    self.assertTrue(asyncio.iscoroutine(gen.__aiter__()) or hasattr(gen, "__anext__"))

  async def _collect_events(self):
    """Colecta todos los eventos del stream."""
    events = []
    async for event in self.engine.execute_and_stream(self.initial_state):
      events.append(event)
    return events

  def test_engine_emits_events(self):
    """Valida que el engine emite eventos durante ejecución."""
    events = asyncio.run(self._collect_events())
    self.assertGreater(len(events), 0)

  def test_engine_events_have_required_structure(self):
    """Valida que los eventos tienen estructura {event_type, node, data}."""
    events = asyncio.run(self._collect_events())
    for event in events:
      self.assertIsInstance(event, dict)
      self.assertIn("event_type", event)
      self.assertIn("node", event)
      self.assertIn("data", event)

  def test_engine_events_have_node_updated_type(self):
    """Valida que los eventos tienen event_type node_updated."""
    events = asyncio.run(self._collect_events())
    for event in events:
      self.assertIn(event["event_type"], ["node_updated", "error"])

  def test_engine_events_contain_node_id(self):
    """Valida que los eventos contienen identificador del nodo."""
    events = asyncio.run(self._collect_events())
    for event in events:
      self.assertIsNotNone(event["node"])
      self.assertIsInstance(event["node"], str)

  def test_engine_events_contain_data_dict(self):
    """Valida que los eventos contienen data como diccionario."""
    events = asyncio.run(self._collect_events())
    for event in events:
      self.assertIsInstance(event["data"], dict)

  def test_engine_executes_workflow(self):
    """Valida que el engine ejecuta el workflow sin excepciones."""
    try:
      events = asyncio.run(self._collect_events())
      self.assertGreater(len(events), 0)
    except Exception as e:
      self.fail(f"Engine execution raised {type(e).__name__}: {str(e)}")

  def test_engine_emits_at_least_3_events(self):
    """Valida que el engine emite al menos 3 eventos (start, process, end)."""
    events = asyncio.run(self._collect_events())
    self.assertGreaterEqual(len(events), 3)


if __name__ == "__main__":
  unittest.main()
