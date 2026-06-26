import logging
from typing import AsyncGenerator, Literal

from langgraph.graph import END, START, StateGraph

from src.domain.ports.input import WorkflowExecutor
from src.infra.adapters.workflow.nodes import (
  node_loader_task,
  node_clone_repository,
  node_checkout_commit,
  node_replace_files_content,
  node_generate_diff
)
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

    # Agregar todos los nodos
    graph.add_node("loader", node_loader_task)
    graph.add_node("clone_repository", node_clone_repository)
    graph.add_node("checkout_commit", node_checkout_commit)
    graph.add_node("replace_files_content", node_replace_files_content)
    graph.add_node("generate_diff", node_generate_diff)

    # Aristas y condicionales
    graph.add_edge(START, "loader")

    # Después de loader, decidir ruta (simple o clone)
    def router_from_loader(state: AgentState):
      load_to = state.get("load_to")
      if load_to == "simple":
        return END
      else:  # clone
        return "clone_repository"

    graph.add_conditional_edges("loader", router_from_loader)

    # Después de clone_repository, decidir si hacer checkout
    def router_after_clone(
      state: AgentState
    ) -> Literal["checkout_commit", "replace_files_content", "generate_diff"]:
      has_commit_sha = state.get("has_commit_sha", False)
      has_files_content = state.get("has_files_content", False)

      if has_commit_sha:
        return "checkout_commit"
      elif has_files_content:
        return "replace_files_content"
      else:
        return "generate_diff"

    graph.add_conditional_edges("clone_repository", router_after_clone)

    # Después de checkout_commit, decidir si reemplazar archivos
    def router_after_checkout(
      state: AgentState
    ) -> Literal["replace_files_content", "generate_diff"]:
      has_files_content = state.get("has_files_content", False)
      if has_files_content:
        return "replace_files_content"
      else:
        return "generate_diff"

    graph.add_conditional_edges("checkout_commit", router_after_checkout)

    # Después de replace_files_content, siempre generar diff
    graph.add_edge("replace_files_content", "generate_diff")

    # Después de generate_diff, terminar
    graph.add_edge("generate_diff", END)

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
