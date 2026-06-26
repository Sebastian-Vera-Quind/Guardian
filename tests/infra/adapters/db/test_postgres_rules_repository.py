import unittest
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

from src.domain.models import ProjectContext
from src.domain.models.errors import (
  InvalidScopeError,
  ProjectContextNotFoundError,
)
from src.infra.adapters.db.postgres_rules_repository import (
  PostgresRulesRepositoryAdapter,
)


class _FakeRow:
  """Fila de resultado con interfaz _mapping como la de SQLAlchemy."""

  def __init__(self, mapping: Dict[str, object]) -> None:
    self._mapping = mapping


def _build_engine(row: Optional[_FakeRow]) -> MagicMock:
  """Construye un engine mock cuyo connect() es un context manager."""
  engine = MagicMock()
  conn = engine.connect.return_value.__enter__.return_value
  conn.execute.return_value.first.return_value = row
  return engine


def _executed_sql(engine: MagicMock) -> str:
  """Devuelve el SQL textual ejecutado contra la conexión."""
  conn = engine.connect.return_value.__enter__.return_value
  query = conn.execute.call_args[0][0]
  return query.text

def _executed_params(engine: MagicMock) -> Dict[str, object]:
  """Devuelve los parámetros nombrados pasados a execute()."""
  conn = engine.connect.return_value.__enter__.return_value
  return conn.execute.call_args[0][1]


class TestPostgresRulesRepositoryAdapterInit(unittest.TestCase):
  """Tests para la construcción del adaptador."""

  def test_init_uses_provided_engine(self) -> None:
    """Validar que el engine inyectado se conserva."""
    engine = MagicMock()
    adapter = PostgresRulesRepositoryAdapter(engine=engine)
    self.assertIs(adapter._engine, engine)

  @patch(
    "src.infra.adapters.db.postgres_rules_repository.EngineManager"
  )
  def test_init_falls_back_to_engine_manager(
    self, mock_manager: MagicMock
  ) -> None:
    """Validar que sin engine se resuelve vía EngineManager."""
    resolved = MagicMock()
    mock_manager.return_value.get_engine.return_value = resolved

    adapter = PostgresRulesRepositoryAdapter()

    self.assertIs(adapter._engine, resolved)
    mock_manager.return_value.get_engine.assert_called_once()


class TestPostgresRulesRepositoryAdapterGetContext(unittest.TestCase):
  """Tests para get_project_context()."""

  def test_invalid_scope_raises_invalid_scope_error(self) -> None:
    """Validar que un scope desconocido lanza InvalidScopeError."""
    adapter = PostgresRulesRepositoryAdapter(engine=MagicMock())

    with self.assertRaises(InvalidScopeError):
      adapter.get_project_context("proj-1", "unknown")

  def test_invalid_scope_does_not_touch_engine(self) -> None:
    """Validar que un scope inválido no abre conexión."""
    engine = MagicMock()
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    with self.assertRaises(InvalidScopeError):
      adapter.get_project_context("proj-1", "; DROP TABLE")

    engine.connect.assert_not_called()

  def test_missing_context_raises_not_found_error(self) -> None:
    """Validar que sin filas se lanza ProjectContextNotFoundError."""
    engine = _build_engine(row=None)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    with self.assertRaises(ProjectContextNotFoundError):
      adapter.get_project_context("missing", "review")

  def test_returns_project_context_for_review_scope(self) -> None:
    """Validar el mapeo a ProjectContext para scope review."""
    row = _FakeRow(
      {
        "checklist": '["c1", "c2"]',
        "coding_standards": '{"max_line": 79}',
      }
    )
    engine = _build_engine(row=row)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    context = adapter.get_project_context("proj-1", "review")

    self.assertIsInstance(context, ProjectContext)
    self.assertEqual(context.project_code, "proj-1")
    self.assertEqual(context.scope, "review")
    self.assertEqual(context.data["checklist"], ["c1", "c2"])
    self.assertEqual(
      context.data["coding_standards"], {"max_line": 79}
    )

  def test_structure_plain_fields_kept_unparsed(self) -> None:
    """Validar que los campos no-JSONB de structure quedan intactos."""
    row = _FakeRow(
      {
        "stack_tecnologico": "python",
        "estructura_directorios": "src/",
        "project_name": "guardian",
      }
    )
    engine = _build_engine(row=row)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    context = adapter.get_project_context("proj-1", "structure")

    self.assertEqual(context.data["stack_tecnologico"], "python")
    self.assertEqual(context.data["estructura_directorios"], "src/")
    self.assertEqual(context.data["project_name"], "guardian")

  def test_jsonb_field_parsed_for_infrastructure_scope(self) -> None:
    """Validar parseo de un campo JSONB en scope infrastructure."""
    row = _FakeRow(
      {
        "specs_infraestructura": '["spec1"]',
        "db_engines": '["postgres"]',
        "api_types": '["rest"]',
        "messaging": "[]",
        "patrones_diseno": '{"hex": true}',
      }
    )
    engine = _build_engine(row=row)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    context = adapter.get_project_context("proj-1", "infrastructure")

    self.assertEqual(context.data["specs_infraestructura"], ["spec1"])
    self.assertEqual(context.data["db_engines"], ["postgres"])
    self.assertEqual(context.data["patrones_diseno"], {"hex": True})

  def test_none_jsonb_field_defaults_to_empty_list(self) -> None:
    """Validar que un JSONB nulo se normaliza a []."""
    row = _FakeRow(
      {
        "reglas_dominio": None,
        "lista_casos_uso": '["uc1"]',
      }
    )
    engine = _build_engine(row=row)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    context = adapter.get_project_context("proj-1", "domain")

    self.assertEqual(context.data["reglas_dominio"], [])
    self.assertEqual(context.data["lista_casos_uso"], ["uc1"])

  def test_query_uses_named_parameter_and_scope_fields(self) -> None:
    """Validar que la query usa parámetro nombrado y campos del scope."""
    row = _FakeRow({"checklist": "[]", "coding_standards": "[]"})
    engine = _build_engine(row=row)
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    adapter.get_project_context("proj-42", "review")

    sql = _executed_sql(engine)
    self.assertIn("checklist", sql)
    self.assertIn("coding_standards", sql)
    self.assertIn(":project_code", sql)
    self.assertNotIn("proj-42", sql)
    self.assertEqual(
      _executed_params(engine), {"project_code": "proj-42"}
    )

  def test_master_scope_selects_all_fields(self) -> None:
    """Validar que el scope master selecciona todos los campos."""
    mapping = {
      "stack_tecnologico": "[]",
      "estructura_directorios": "src/",
      "project_name": "guardian",
      "reglas_dominio": "[]",
      "lista_casos_uso": "[]",
      "specs_infraestructura": "[]",
      "db_engines": "[]",
      "api_types": "[]",
      "messaging": "[]",
      "patrones_diseno": "[]",
      "checklist": "[]",
      "coding_standards": "[]",
    }
    engine = _build_engine(row=_FakeRow(mapping))
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    adapter.get_project_context("proj-1", "master")

    sql = _executed_sql(engine)
    for field in mapping:
      self.assertIn(field, sql)

  def test_db_error_wrapped_as_not_found_error(self) -> None:
    """Validar que un error de conexión se envuelve como not found."""
    engine = MagicMock()
    engine.connect.side_effect = RuntimeError("connection refused")
    adapter = PostgresRulesRepositoryAdapter(engine=engine)

    with self.assertRaises(ProjectContextNotFoundError):
      adapter.get_project_context("proj-1", "review")


if __name__ == "__main__":
  unittest.main()
