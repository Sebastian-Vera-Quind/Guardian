from langgraph.graph import StateGraph

from src.domain.models import WorkflowState
from .nodes import node_start, node_process, node_end


class WorkflowBuilder:
  """Construye un StateGraph con nodos y transiciones."""

  def build(self) -> StateGraph:
    """Retorna StateGraph completamente configurado."""
    graph = StateGraph(WorkflowState)

    graph.add_node("start", node_start)
    graph.add_node("process", node_process)
    graph.add_node("end", node_end)

    graph.add_edge("start", "process")
    graph.add_edge("process", "end")

    graph.set_entry_point("start")
    graph.set_finish_point("end")

    return graph.compile()
