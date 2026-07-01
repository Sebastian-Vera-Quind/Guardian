import unittest
from unittest.mock import MagicMock, patch

from src.infra.adapters.db.pgvector_arch_doc_repository import (
  PgVectorArchDocRepository,
  _SIMILARITY_FLOOR,
)


class TestPgVectorArchDocRepository(unittest.TestCase):

  def _make_repo(self, ai_provider=None, tlm_client=None):
    ai_provider = ai_provider or MagicMock()
    tlm_client = tlm_client or MagicMock()
    return PgVectorArchDocRepository(
      ai_provider=ai_provider, tlm_client=tlm_client
    )

  def test_search_returns_chunks_above_floor(self):
    ai = MagicMock()
    ai.embed.return_value = [0.1, 0.2, 0.3]
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = {"id": "uuid-1"}

    # distance = 1 - similarity; similarity 0.90 → distance 0.10
    row_above = (
      "arch chunk above floor",
      0.10,
    )
    row_below = (
      "arch chunk below floor",
      0.80,
    )

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
      row_above, row_below
    ]
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
    mock_engine.connect.return_value.__exit__ = MagicMock(
      return_value=False
    )

    repo = self._make_repo(ai_provider=ai, tlm_client=tlm)

    with patch(
      "src.infra.adapters.db.pgvector_arch_doc_repository"
      ".EngineManager"
    ) as mock_em_cls:
      mock_em_cls.return_value.get_engine.return_value = mock_engine
      result = repo.search_similar_chunks("PROJ", "query text")

    self.assertIn("arch chunk above floor", result)
    self.assertNotIn("arch chunk below floor", result)

  def test_search_returns_empty_when_project_not_found(self):
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = None
    repo = self._make_repo(tlm_client=tlm)
    result = repo.search_similar_chunks("PROJ", "query")
    self.assertEqual(result, [])

  def test_search_returns_empty_on_embed_error(self):
    ai = MagicMock()
    ai.embed.side_effect = RuntimeError("embed failed")
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = {"id": "uuid-1"}
    repo = self._make_repo(ai_provider=ai, tlm_client=tlm)
    result = repo.search_similar_chunks("PROJ", "query")
    self.assertEqual(result, [])

  def test_search_returns_empty_on_db_error(self):
    ai = MagicMock()
    ai.embed.return_value = [0.1, 0.2]
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = {"id": "uuid-1"}
    repo = self._make_repo(ai_provider=ai, tlm_client=tlm)

    with patch(
      "src.infra.adapters.db.pgvector_arch_doc_repository"
      ".EngineManager"
    ) as mock_em_cls:
      mock_em_cls.return_value.get_engine.side_effect = RuntimeError(
        "db down"
      )
      result = repo.search_similar_chunks("PROJ", "query")

    self.assertEqual(result, [])


if __name__ == "__main__":
  unittest.main()
