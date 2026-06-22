from typing import Protocol, AsyncGenerator

from langgraph.graph import StateGraph

from src.domain.models import WorkflowInput, WorkflowEvent


class WorkflowExecutor(Protocol):
  """Protocolo para ejecutar workflows (StateGraph)."""

  graph: StateGraph

  async def execute_and_stream(
      self, input_data: WorkflowInput
  ) -> AsyncGenerator[WorkflowEvent, None]:
    """Ejecuta grafo e itera eventos."""
    ...
