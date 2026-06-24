from typing import Optional
from uuid import UUID

from typing_extensions import TypedDict
from pydantic import BaseModel, ConfigDict

from src.domain.models.util import FileContent, RepositoryInput

class WorkflowInput(BaseModel):
  """Contrato base para entrada del workflow."""
  model_config = ConfigDict(extra="forbid")

  project_id: Optional[UUID] = None
  project_code: Optional[str] = None
  repository: Optional[RepositoryInput] = None
  files_content: Optional[list[FileContent]] = None

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
  data: Optional[dict] = None
