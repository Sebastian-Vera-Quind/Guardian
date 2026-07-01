import logging
import os
from typing import Optional

from sqlalchemy import text

from src.domain.models.project_fields import ProjectFields
from src.domain.ports.output.repository.project_fields_repository import (
  ProjectFieldsRepository,
)
from src.domain.ports.output.tlm.tlm_client import TlmClient
from src.infra.adapters.db.config import DatabaseLabel, EngineManager

logger = logging.getLogger(__name__)

_USE_TLM_HTTP_DEFAULT = "true"

_SQL_QUERY = text(
  "SELECT quality_gates, constraints, nfr_definition, fitness_functions"
  " FROM projects WHERE code = :code"
)


class ProjectFieldsRepositoryAdapter(ProjectFieldsRepository):
  """Retrieves project fields via HTTP-first with SQL fallback.

  HTTP path uses TlmClient; SQL fallback reads the TLM database directly
  via EngineManager. Each fallback emits a structured warning.
  """

  def __init__(self, tlm_client: TlmClient) -> None:
    self._tlm = tlm_client

  def get_project_fields(
    self, project_code: str
  ) -> ProjectFields:
    """Load quality_gates, constraints, nfr_definition, fitness_functions.

    Args:
      project_code: Unique project identifier.

    Returns:
      ProjectFields instance; all fields are None on full failure.
    """
    if self._http_enabled():
      fields = self._load_from_http(project_code)
      if fields is not None:
        return fields
      logger.warning(
        "project_fields_http_fallback project_code=%s "
        "— falling back to SQL",
        project_code,
      )

    return self._load_from_sql(project_code)

  def _http_enabled(self) -> bool:
    return os.getenv(
      "GUARDIAN_USE_TLM_HTTP", _USE_TLM_HTTP_DEFAULT
    ).strip().lower() in {"1", "true", "yes", "on"}

  def _load_from_http(
    self, project_code: str
  ) -> Optional[ProjectFields]:
    try:
      project = self._tlm.get_project_by_code(project_code)
      if project is None:
        return None
      return ProjectFields(
        quality_gates=project.get("quality_gates"),
        constraints=project.get("constraints"),
        nfr_definition=project.get("nfr_definition"),
        fitness_functions=project.get("fitness_functions"),
      )
    except Exception as exc:
      logger.warning(
        "project_fields_http_error project_code=%s err=%s",
        project_code,
        exc,
      )
      return None

  def _load_from_sql(
    self, project_code: str
  ) -> ProjectFields:
    logger.warning(
      "project_fields_sql_path project_code=%s "
      "— reading directly from TLM database",
      project_code,
    )
    try:
      engine = EngineManager().get_engine(DatabaseLabel.TML)
      with engine.connect() as conn:
        row = conn.execute(
          _SQL_QUERY, {"code": project_code}
        ).mappings().first()
        if row is None:
          logger.warning(
            "project_fields_not_found project_code=%s",
            project_code,
          )
          return ProjectFields()
        return ProjectFields(
          quality_gates=row.get("quality_gates"),
          constraints=row.get("constraints"),
          nfr_definition=row.get("nfr_definition"),
          fitness_functions=row.get("fitness_functions"),
        )
    except Exception as exc:
      logger.warning(
        "project_fields_sql_error project_code=%s err=%s",
        project_code,
        exc,
      )
      return ProjectFields()
