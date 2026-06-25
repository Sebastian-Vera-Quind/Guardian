import logging
from typing import AsyncGenerator

from langgraph.graph import END, START, StateGraph

from src.domain.ports.input import WorkflowExecutor
from src.infra.adapters.workflow.nodes import node_loader_task, node_clone_task
from src.domain.models import AgentState, WorkflowEvent, WorkflowInput

logger = logging.getLogger(__name__)

class WorkflowEngine(WorkflowExecutor):
  _instance = None
  _graph: StateGraph = None

  def __init__(self):
    self._build()

  def _build(self):
    if self._graph is not None:
      logger.warning("Graph already built, skipping rebuild.")
      return

    graph = StateGraph(AgentState)

    graph.add_node("loader", node_loader_task)
    graph.add_node("clone_path", node_clone_task)

    graph.add_edge(START, "loader")
    graph.add_edge("loader", "clone_path")
    graph.add_edge("clone_path", END)

    self._graph = graph.compile()

  async def execute_and_stream(
      self, input_data: WorkflowInput
  ) -> AsyncGenerator[WorkflowEvent, None]:
    state: AgentState = {
      "project_code": input_data.project_code or "",
      "project_id": input_data.project_id,
      "repository": input_data.repository or None,
      "files_content": input_data.files_content or None,
    }

    if not state["project_code"] or not state["project_id"]:
      raise ValueError("Missing required fields: project_code and project_id")

    final_state = None
    try:
      async for output in self._graph.astream(state):
        if isinstance(output, dict):
          final_state = output
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

      if final_state is not None:
        logger.info("Workflow completed successfully, emitting final state")
        event: WorkflowEvent = {
            "event_type": "complete",
            "node": "workflow",
            "data": final_state
        }
        yield event
    except Exception as e:
      logger.error(f"Workflow execution failed: {str(e)}")
      event: WorkflowEvent = {
          "event_type": "error",
          "node": "unknown",
          "data": {"error": str(e)}
      }
      yield event
