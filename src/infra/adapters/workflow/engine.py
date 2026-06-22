import logging
from typing import AsyncGenerator

from langgraph.graph import StateGraph

from src.domain.models import WorkflowState, WorkflowEvent

logger = logging.getLogger(__name__)


class WorkflowEngine:
  """Motor que ejecuta StateGraph con streaming."""

  def __init__(self, graph: StateGraph):
    self.graph = graph

  async def execute_and_stream(
      self, input_data: WorkflowState
  ) -> AsyncGenerator[WorkflowEvent, None]:
    """Ejecuta grafo e itera eventos con astream()."""
    try:
      async for output in self.graph.astream(input_data):
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
