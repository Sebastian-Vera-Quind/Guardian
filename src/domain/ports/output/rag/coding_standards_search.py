from abc import ABC, abstractmethod
from typing import List

from src.domain.models.retrieved_context import SimilarStandard


class CodingStandardsSearch(ABC):
  """Output port for cross-tenant coding standards semantic search."""

  @abstractmethod
  def find_similar_coding_standards(
    self,
    project_code: str,
    query_text: str,
  ) -> List[SimilarStandard]:
    """Find coding standards similar to the query.

    Args:
      project_code: Project code to scope the search.
      query_text: Free-text query for semantic similarity.

    Returns:
      List of SimilarStandard results above the similarity floor.
    """
    ...
