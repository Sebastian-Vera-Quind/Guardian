import logging
from typing import AsyncGenerator

from langgraph.graph import StateGraph

from src.domain.ports.input import WorkflowExecutor
from src.infra.adapters.workflow.nodes import node_end, node_process, node_start
from src.domain.models import WorkflowState, WorkflowEvent

logger = logging.getLogger(__name__)



class WorkflowEngine(WorkflowExecutor):
  _instance = None
  _graph: StateGraph = None

  def __init__(self):
    """Inicializa el engine y construye el grafo."""
    self._build()

  def _build(self):
    if self._graph is not None:
      logger.warning("Graph already built, skipping rebuild.")
      return
    
    graph = StateGraph(WorkflowState)

    graph.add_node("start", node_start)
    graph.add_node("process", node_process)
    graph.add_node("end", node_end)

    graph.add_edge("start", "process")
    graph.add_edge("process", "end")

    graph.set_entry_point("start")
    graph.set_finish_point("end")

    self._graph = graph.compile()
    
  async def execute_and_stream(
      self, input_data: WorkflowState
  ) -> AsyncGenerator[WorkflowEvent, None]:
    """Ejecuta grafo e itera eventos con astream()."""
    try:
      async for output in self._graph.astream(input_data):
        if isinstance(output, dict):
          for node_id, node_output in output.items():
            logger.info(f"Node {node_id} completed")
            event: WorkflowEvent = {
                "event_type": "node_updated",
                "node": node_id,
                "data": node_output
            }
            yield event
        else:
          logger.info(f"Stream output: {output}")
    except Exception as e:
      logger.error(f"Workflow execution failed: {str(e)}")
      event: WorkflowEvent = {
          "event_type": "error",
          "node": "unknown",
          "data": {"error": str(e)}
      }
      yield event
