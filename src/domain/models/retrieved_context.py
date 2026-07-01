from typing import List, Optional

from pydantic import BaseModel

from src.domain.models.project_context import JsonValue


class SimilarStandard(BaseModel):
  """A coding standard result returned by CodingStandardsSearch."""

  name: str
  description: Optional[str] = None


class RetrievedContext(BaseModel):
  """Aggregated retrieval result produced by ContextRetrievalService."""

  active_rules: List[str]
  quality_gates: Optional[JsonValue] = None
  constraints: Optional[JsonValue] = None
  nfr_definition: Optional[JsonValue] = None
  fitness_functions: Optional[JsonValue] = None
