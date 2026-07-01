import logging
from typing import List

from sqlalchemy import text

from src.domain.ports.output.ai.ai_provider import AIProvider
from src.domain.ports.output.rag.vector_search_repository import (
  VectorSearchRepository,
)
from src.domain.ports.output.tlm.tlm_client import TlmClient
from src.infra.adapters.db.config import DatabaseLabel, EngineManager

logger = logging.getLogger(__name__)

_TOP_K = 5
_SIMILARITY_FLOOR = 0.30

_COSINE_QUERY = text(
  "SELECT chunk_text, (embedding <=> CAST(:embedding AS vector)) AS distance"
  " FROM arch_doc_embeddings"
  " WHERE project_id = :project_id"
  " ORDER BY distance"
  " LIMIT :top_k"
)


class PgVectorArchDocRepository(VectorSearchRepository):
  """Searches architecture document embeddings using pgvector cosine
  similarity.

  Dependencies are injected; the SQLAlchemy engine is resolved from
  EngineManager at call time so tests can swap the singleton.
  """

  def __init__(
    self,
    ai_provider: AIProvider,
    tlm_client: TlmClient,
  ) -> None:
    self._ai = ai_provider
    self._tlm = tlm_client

  def search_similar_chunks(
    self,
    project_code: str,
    query_text: str,
  ) -> List[str]:
    """Return architecture doc chunks above the similarity floor.

    Args:
      project_code: Used to resolve the project UUID.
      query_text: Query embedded and used for cosine search.

    Returns:
      List of chunk text strings, or [] on any error.
    """
    try:
      project = self._tlm.get_project_by_code(project_code)
      if not project:
        logger.warning(
          "pgvector_project_not_found project_code=%s", project_code
        )
        return []

      project_id = project.get("id")
      if not project_id:
        logger.warning(
          "pgvector_missing_project_id project_code=%s", project_code
        )
        return []

      embedding = self._ai.embed(query_text)
      embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

      engine = EngineManager().get_engine(DatabaseLabel.GUARDIAN)
      with engine.connect() as conn:
        rows = conn.execute(
          _COSINE_QUERY,
          {
            "embedding": embedding_str,
            "project_id": str(project_id),
            "top_k": _TOP_K,
          },
        ).fetchall()

      chunks: List[str] = []
      for row in rows:
        distance = float(row[1])
        similarity = 1.0 - distance
        if similarity >= _SIMILARITY_FLOOR:
          chunks.append(str(row[0]))

      logger.info(
        "pgvector_search project_code=%s returned=%d",
        project_code,
        len(chunks),
      )
      return chunks

    except Exception as exc:
      logger.warning(
        "pgvector_search_failed project_code=%s err=%s",
        project_code,
        exc,
      )
      return []
