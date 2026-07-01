from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from src.domain.models import SimilarStandard, JsonValue


class TlmClient(ABC):
  """Output port for the TLM (Tenant Lifecycle Management) service."""

  @abstractmethod
  def get_project_by_code(
    self, code: str
  ) -> Optional[Dict[str, JsonValue]]:
    """Resolve a project by its code.

    Args:
      code: Unique project code.

    Returns:
      Dict with project fields or None if not found.
    """
    ...

  @abstractmethod
  def search_coding_standards(
    self,
    project_code: str,
    query: str,
    top_k: int,
  ) -> List[SimilarStandard]:
    """Find coding standards similar to the query text.

    Args:
      project_code: Project to scope the search to.
      query: Free-text query for semantic search.
      top_k: Maximum number of results to return.

    Returns:
      List of SimilarStandard results.
    """
    ...
