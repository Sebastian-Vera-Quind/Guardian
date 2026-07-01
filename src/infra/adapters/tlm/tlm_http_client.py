import logging
import os
from typing import Dict, List, Optional

import httpx

from src.domain.models import SimilarStandard, JsonValue
from src.domain.ports.output import TlmClient

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10.0


class TlmHttpClient(TlmClient):
  """HTTP adapter for the TLM internal API.

  Reads TLM_BASE_URL from environment. Fail-open on all network errors:
  get_project_by_code returns None and search_coding_standards returns [].
  """

  def __init__(self) -> None:
    self._base_url = os.getenv("TLM_BASE_URL", "").rstrip("/")
    self._timeout = _DEFAULT_TIMEOUT

  def get_project_by_code(
    self, code: str
  ) -> Optional[Dict[str, JsonValue]]:
    """GET /api/v1/internal/projects/{code}.

    Args:
      code: Unique project code.

    Returns:
      Project dict or None when not found or on any error.
    """
    if not self._base_url:
      return None
    url = f"{self._base_url}/api/v1/internal/projects/{code}"
    try:
      response = httpx.get(url, timeout=self._timeout)
      if response.status_code == 404:
        return None
      response.raise_for_status()
      body = response.json().get("body")
      return body if isinstance(body, dict) else None
    except Exception as exc:
      logger.warning(
        "tlm_get_project_failed code=%s err=%s", code, exc
      )
      return None

  def search_coding_standards(
    self,
    project_code: str,
    query: str,
    top_k: int,
  ) -> List[SimilarStandard]:
    """GET /api/v1/internal/coding-standards/search.

    Args:
      project_code: Project to scope the search.
      query: Free-text query.
      top_k: Maximum results requested.

    Returns:
      List of SimilarStandard or [] on any error.
    """
    if not self._base_url:
      return []
    url = f"{self._base_url}/api/v1/internal/coding-standards/search"
    params = {
      "project_code": project_code,
      "query": query,
      "top_k": top_k,
    }
    try:
      response = httpx.get(
        url, params=params, timeout=self._timeout
      )
      response.raise_for_status()
      items = response.json().get("body") or []
      result: List[SimilarStandard] = []
      for item in items:
        if isinstance(item, dict):
          result.append(
            SimilarStandard(
              name=item.get("name", ""),
              description=item.get("description"),
            )
          )
      return result
    except Exception as exc:
      logger.warning(
        "tlm_search_standards_failed project_code=%s err=%s",
        project_code,
        exc,
      )
      return []
