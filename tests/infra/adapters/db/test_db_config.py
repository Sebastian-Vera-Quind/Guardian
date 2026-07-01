import os
import unittest
from unittest.mock import MagicMock, patch


class TestDatabaseLabel(unittest.TestCase):

  def test_guardian_label_reads_env(self):
    from src.infra.adapters.db.config import DatabaseLabel, _LABEL_ENV
    self.assertIn(DatabaseLabel.GUARDIAN, [
      DatabaseLabel.GUARDIAN, DatabaseLabel.TML
    ])
    self.assertEqual(
      _LABEL_ENV[DatabaseLabel.GUARDIAN.value], "GUARDIAN_DATABASE_URL"
    )

  def test_tml_label_reads_env(self):
    from src.infra.adapters.db.config import DatabaseLabel, _LABEL_ENV
    self.assertEqual(
      _LABEL_ENV[DatabaseLabel.TML.value], "TLM_DATABASE_URL"
    )


class TestEngineManager(unittest.TestCase):

  def test_get_engine_calls_safe_create(self):
    with patch.dict(
      os.environ, {"GUARDIAN_DATABASE_URL": "sqlite:///:memory:"}
    ):
      from src.infra.adapters.db.config import DatabaseLabel, EngineManager
      manager = EngineManager()
      manager._engines.clear()

      with patch.object(
        manager, "_safe_create_engine", wraps=manager._safe_create_engine
      ) as mock_safe:
        manager.get_engine(DatabaseLabel.GUARDIAN)
        mock_safe.assert_called_once()

  def test_get_engine_returns_cached_engine(self):
    with patch.dict(
      os.environ, {"GUARDIAN_DATABASE_URL": "sqlite:///:memory:"}
    ):
      from src.infra.adapters.db.config import DatabaseLabel, EngineManager
      manager = EngineManager()
      manager._engines.clear()

      e1 = manager.get_engine(DatabaseLabel.GUARDIAN)
      e2 = manager.get_engine(DatabaseLabel.GUARDIAN)
      self.assertIs(e1, e2)


if __name__ == "__main__":
  unittest.main()
