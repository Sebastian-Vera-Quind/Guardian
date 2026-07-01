import os
import unittest
from unittest.mock import MagicMock, patch

from src.domain.models.project_fields import ProjectFields
from src.infra.adapters.db.project_fields_repository import (
  ProjectFieldsRepositoryAdapter,
)


class TestProjectFieldsRepositoryAdapter(unittest.TestCase):

  def _make_adapter(self, tlm_client=None):
    tlm_client = tlm_client or MagicMock()
    return ProjectFieldsRepositoryAdapter(tlm_client=tlm_client)

  @patch.dict(os.environ, {"GUARDIAN_USE_TLM_HTTP": "true"})
  def test_get_fields_http_path_happy(self):
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = {
      "id": "uuid-1",
      "quality_gates": {"threshold": 90},
      "constraints": None,
      "nfr_definition": None,
      "fitness_functions": ["f1"],
    }
    adapter = self._make_adapter(tlm_client=tlm)
    result = adapter.get_project_fields("PROJ")

    self.assertIsInstance(result, ProjectFields)
    self.assertEqual(result.quality_gates, {"threshold": 90})
    self.assertEqual(result.fitness_functions, ["f1"])

  @patch.dict(os.environ, {"GUARDIAN_USE_TLM_HTTP": "true"})
  def test_get_fields_falls_back_to_sql_when_http_none(self):
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = None
    adapter = self._make_adapter(tlm_client=tlm)

    mock_row = {
      "quality_gates": {"q": 1},
      "constraints": None,
      "nfr_definition": None,
      "fitness_functions": None,
    }
    mock_conn = MagicMock()
    mock_conn.execute.return_value.mappings.return_value.first.return_value = (
      mock_row
    )
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
    mock_engine.connect.return_value.__exit__ = MagicMock(
      return_value=False
    )

    with patch(
      "src.infra.adapters.db.project_fields_repository.EngineManager"
    ) as mock_em_cls:
      mock_em_cls.return_value.get_engine.return_value = mock_engine
      result = adapter.get_project_fields("PROJ")

    self.assertIsInstance(result, ProjectFields)
    self.assertEqual(result.quality_gates, {"q": 1})

  @patch.dict(os.environ, {"GUARDIAN_USE_TLM_HTTP": "false"})
  def test_get_fields_falls_back_to_sql_when_http_disabled(self):
    tlm = MagicMock()
    adapter = self._make_adapter(tlm_client=tlm)

    mock_row = {
      "quality_gates": None,
      "constraints": None,
      "nfr_definition": None,
      "fitness_functions": None,
    }
    mock_conn = MagicMock()
    mock_conn.execute.return_value.mappings.return_value.first.return_value = (
      mock_row
    )
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
    mock_engine.connect.return_value.__exit__ = MagicMock(
      return_value=False
    )

    with patch(
      "src.infra.adapters.db.project_fields_repository.EngineManager"
    ) as mock_em_cls:
      mock_em_cls.return_value.get_engine.return_value = mock_engine
      result = adapter.get_project_fields("PROJ")

    tlm.get_project_by_code.assert_not_called()
    self.assertIsInstance(result, ProjectFields)

  @patch.dict(os.environ, {"GUARDIAN_USE_TLM_HTTP": "true"})
  def test_get_fields_returns_none_fields_on_sql_error(self):
    tlm = MagicMock()
    tlm.get_project_by_code.return_value = None
    adapter = self._make_adapter(tlm_client=tlm)

    with patch(
      "src.infra.adapters.db.project_fields_repository.EngineManager"
    ) as mock_em_cls:
      mock_em_cls.return_value.get_engine.side_effect = RuntimeError(
        "db down"
      )
      result = adapter.get_project_fields("PROJ")

    self.assertIsInstance(result, ProjectFields)
    self.assertIsNone(result.quality_gates)
    self.assertIsNone(result.constraints)
    self.assertIsNone(result.nfr_definition)
    self.assertIsNone(result.fitness_functions)


if __name__ == "__main__":
  unittest.main()
