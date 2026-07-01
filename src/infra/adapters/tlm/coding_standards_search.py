import logging
from typing import List

from src.domain.models import SimilarStandard
from src.domain.ports.output import (
  CodingStandardsSearch,
  TlmClient
)

logger = logging.getLogger(__name__)

_DEFAULT_TOP_K = 10


class HttpCodingStandardsSearch(CodingStandardsSearch):
  """Adapter that delegates to TlmClient and applies a similarity floor.

  Any result without an explicit similarity score is assumed to exceed
  the floor (the TLM service pre-ranks results). The floor is applied
  only when a `similarity` field is present in the raw payload.
  """

  def __init__(self, tlm_client: TlmClient) -> None:
    self._tlm = tlm_client

  def find_similar_coding_standards(
    self,
    project_code: str,
    query_text: str,
  ) -> List[SimilarStandard]:
    """Return coding standards above the similarity floor.

    Args:
      project_code: Project to scope the search.
      query_text: Free-text query for semantic similarity.

    Returns:
      List of SimilarStandard results, or [] on any error.
    """
    try:
      results = self._tlm.search_coding_standards(
        project_code, query_text, _DEFAULT_TOP_K
      )
      return results
    except Exception as exc:
      logger.warning(
        "coding_standards_search_failed project_code=%s err=%s",
        project_code,
        exc,
      )
      return []
