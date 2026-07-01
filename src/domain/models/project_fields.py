from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.domain.models.project_context import JsonValue


class ProjectFields(BaseModel):
  """Project-level configuration fields loaded from TLM."""

  model_config = ConfigDict(frozen=True)

  quality_gates: Optional[JsonValue] = None
  constraints: Optional[JsonValue] = None
  nfr_definition: Optional[JsonValue] = None
  fitness_functions: Optional[JsonValue] = None
