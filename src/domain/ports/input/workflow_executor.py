from abc import abstractmethod
from typing import Protocol, AsyncGenerator


from src.domain.models import WorkflowInput, WorkflowEvent


class WorkflowExecutor(Protocol):
  @abstractmethod
  async def execute_and_stream(
      self, input_data: WorkflowInput
  ) -> AsyncGenerator[WorkflowEvent, None]:
    """Ejecuta grafo e itera eventos."""
    pass
