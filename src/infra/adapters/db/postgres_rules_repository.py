import json
import logging
import re
from typing import Dict, Optional, Union

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .config import DatabaseLabel, EngineManager
from src.domain.models.errors import (
  InvalidScopeError,
  ProjectContextNotFoundError,
)
from src.domain.models import ProjectContext, JsonValue

from src.domain.ports.output import RulesRepository

logger = logging.getLogger(__name__)

_SAFE_FIELDS_RE = re.compile(r"^[a-z_,\s*]+$")

_JSONB_FIELDS = {
  "coding_standards",
  "checklist",
  "patrones_diseno",
  "reglas_dominio",
  "lista_casos_uso",
  "specs_infraestructura",
  "db_engines",
  "api_types",
  "messaging",
}

_FIELDS_MAP = {
  "structure": [
    "stack_tecnologico",
    "estructura_directorios",
    "project_name",
  ],
  "domain": [
    "reglas_dominio",
    "lista_casos_uso",
  ],
  "infrastructure": [
    "specs_infraestructura",
    "db_engines",
    "api_types",
    "messaging",
    "patrones_diseno",
  ],
  "review": [
    "checklist",
    "coding_standards",
  ],
  "master": [
    "stack_tecnologico",
    "estructura_directorios",
    "project_name",
    "reglas_dominio",
    "lista_casos_uso",
    "specs_infraestructura",
    "db_engines",
    "api_types",
    "messaging",
    "patrones_diseno",
    "checklist",
    "coding_standards",
  ],
}


def _parse_json_field(value: Union[str, dict, list, None]) -> JsonValue:
  """
  Parsear campo JSONB a objeto Python.

  Si es string JSON válido, lo parsea. Si es None o inválido, retorna [].

  Args:
    value: Valor a parsear (str, dict, list, None).

  Returns:
    Valor parseado o [] por defecto.
  """
  if value is None:
    return []

  if isinstance(value, (dict, list)):
    return value

  if isinstance(value, str):
    try:
      parsed = json.loads(value)
      return parsed if parsed is not None else []
    except (json.JSONDecodeError, TypeError):
      logger.warning(f"No se pudo parsear JSON: {value}")
      return []

  return []


class PostgresRulesRepositoryAdapter(RulesRepository):
  """
  Adaptador PostgreSQL para repositorio de reglas.

  Implementa RulesRepository usando SQLAlchemy Core.
  """

  def __init__(self, engine: Optional[Engine] = None):
    """
    Inicializar adaptador.

    Args:
      engine: Engine SQLAlchemy para guardian_db.

    Raises:
      MissingViewError: Si vista view_project_rules no existe.
    """
    self._engine = engine if engine is not None else EngineManager().get_engine(DatabaseLabel.TML)

  def get_project_context(
    self, project_code: str, scope: str
  ) -> ProjectContext:
    """
    Recuperar contexto del proyecto por scope.

    Args:
      project_code: Código único del proyecto.
      scope: Uno de: structure, domain, infrastructure, review, master.

    Returns:
      ProjectContext con los campos del scope solicitado.

    Raises:
      InvalidScopeError: Si scope no es válido.
      ProjectContextNotFoundError: Si no hay contexto.
      MissingViewError: Si vista no existe.
    """
    # Validar scope contra allow-list
    if scope not in _FIELDS_MAP:
      logger.warning(f"Scope inválido: {scope}")
      raise InvalidScopeError(
        f"Scope '{scope}' no es válido. "
        f"Válidos: {', '.join(_FIELDS_MAP.keys())}"
      )

    # Validar regex defense-in-depth
    if not _SAFE_FIELDS_RE.match(scope):
      logger.warning(f"Scope rechazado por regex: {scope}")
      raise InvalidScopeError(
        f"Scope '{scope}' contiene caracteres inválidos"
      )

    # Construir lista de campos a seleccionar
    fields_to_select = _FIELDS_MAP[scope]
    fields_list = ", ".join(fields_to_select)

    # Construir query SQL con parámetros nombrados
    query_str = f"""
      SELECT {fields_list}
      FROM view_project_master_context
      WHERE project_code = :project_code
    """

    try:
      query = text(query_str)
      with self._engine.connect() as conn:
        result = conn.execute(
          query, {"project_code": project_code}
        ).first()

        if result is None:
          logger.warning(
            f"No hay contexto para proyecto {project_code}"
          )
          raise ProjectContextNotFoundError(
            f"No hay contexto para proyecto '{project_code}'"
          )

        # Mapear resultado a diccionario mutable
        row_dict: Dict[str, JsonValue] = dict(
          result._mapping if hasattr(result, "_mapping") else dict(
            zip(fields_to_select, result)
          )
        )

        # Parsear campos JSONB
        for field in fields_to_select:
          if field in _JSONB_FIELDS:
            row_dict[field] = _parse_json_field(row_dict.get(field))

        return ProjectContext(
          project_code=project_code,
          scope=scope,
          data=row_dict,
        )

    except (InvalidScopeError, ProjectContextNotFoundError):
      raise
    except Exception as e:
      logger.error(
        f"Error recuperando contexto para {project_code}: {e}"
      )
      raise ProjectContextNotFoundError(
        f"Error recuperando contexto: {e}"
      ) from e
