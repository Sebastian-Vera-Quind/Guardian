from pydantic import BaseModel
from typing_extensions import TypedDict


class WorkflowInput(BaseModel):
  """Contrato base para entrada del workflow."""

  class Config:
    extra = "forbid"


class WorkflowState(TypedDict):
  """Estado del StateGraph. Tipado estrictamente."""
  user_input: str
  processing_state: str
  current_node: str
  result: dict | None
  errors: list[str]


class WorkflowEvent(TypedDict):
  """Evento emitido durante ejecución del grafo."""
  event_type: str
  node: str
  data: dict
