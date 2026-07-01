import logging
from typing import List

from src.domain.models import (
  RetrievedContext,
  RulesRepositoryError,
  SimilarStandard,
  ProjectFields,
)
from src.domain.ports.input import ContextRetriever
from src.domain.ports.output import (
  CodingStandardsSearch,
  VectorSearchRepository,
  ProjectFieldsRepository,
  RulesRepository,
)
from src.application.security.prompt_guard import wrap_user_content

logger = logging.getLogger(__name__)

_DEFAULT_RULE = (
  "Follow the project's established coding conventions, "
  "design patterns, and quality standards."
)


class ContextRetrievalService(ContextRetriever):
  """Orchestrates retrieval of rules, vector chunks, coding standards
  and project fields into a single RetrievedContext.

  All remote calls are wrapped in fail-open try/except blocks so that a
  partial outage never blocks the analysis flow.
  """

  def __init__(
    self,
    rules: RulesRepository,
    vector: VectorSearchRepository,
    standards: CodingStandardsSearch,
    fields: ProjectFieldsRepository,
  ) -> None:
    self._rules = rules
    self._vector = vector
    self._standards = standards
    self._fields = fields

  def retrieve(
    self,
    project_code: str,
    query_text: str,
    scope: str = "review",
  ) -> RetrievedContext:
    """Retrieve all contextual data for a project.

    Args:
      project_code: Unique project identifier.
      query_text: Text used to drive similarity searches.
      scope: Rules scope forwarded to RulesRepository.

    Returns:
      Populated RetrievedContext.
    """
    active_rules = self._load_rules(project_code, scope)

    if query_text.strip():
      active_rules = self._append_vector_chunks(
        project_code, query_text, active_rules
      )
      active_rules = self._append_similar_standards(
        project_code, query_text, active_rules
      )

    project_fields = self._load_project_fields(project_code)

    return RetrievedContext(
      active_rules=active_rules,
      quality_gates=project_fields.quality_gates,
      constraints=project_fields.constraints,
      nfr_definition=project_fields.nfr_definition,
      fitness_functions=project_fields.fitness_functions,
    )

  # ------------------------------------------------------------------
  # Private helpers
  # ------------------------------------------------------------------

  def _load_rules(
    self, project_code: str, scope: str
  ) -> List[str]:
    try:
      ctx = self._rules.get_project_context(project_code, scope)
      coding_standards = ctx.data.get("coding_standards", [])
      if isinstance(coding_standards, list):
        return [str(r) for r in coding_standards]
      return []
    except RulesRepositoryError as exc:
      logger.warning(
        "rules_load_failed project_code=%s err=%s — using default rule",
        project_code,
        exc,
      )
    except Exception as exc:
      logger.warning(
        "rules_load_unexpected_error project_code=%s err=%s "
        "— using default rule",
        project_code,
        exc,
      )
    return self._create_default_rule()

  def _append_vector_chunks(
    self,
    project_code: str,
    query_text: str,
    active_rules: List[str],
  ) -> List[str]:
    try:
      chunks = self._vector.search_similar_chunks(
        project_code, query_text
      )
      wrapped = [wrap_user_content(chunk) for chunk in chunks]
      return active_rules + wrapped
    except Exception as exc:
      logger.warning(
        "vector_search_failed project_code=%s err=%s — skipping chunks",
        project_code,
        exc,
      )
    return active_rules

  def _append_similar_standards(
    self,
    project_code: str,
    query_text: str,
    active_rules: List[str],
  ) -> List[str]:
    try:
      similar: List[SimilarStandard] = (
        self._standards.find_similar_coding_standards(
          project_code, query_text
        )
      )
      formatted = [
        wrap_user_content(
          f"[Similar Standard] {std.name}: {std.description or ''}"
        )
        for std in similar
      ]
      return active_rules + formatted
    except Exception as exc:
      logger.warning(
        "standards_search_failed project_code=%s err=%s "
        "— skipping similar standards",
        project_code,
        exc,
      )
    return active_rules

  def _load_project_fields(
    self, project_code: str
  ) -> ProjectFields:
    try:
      return self._fields.get_project_fields(project_code)
    except Exception as exc:
      logger.warning(
        "project_fields_load_failed project_code=%s err=%s "
        "— returning empty fields",
        project_code,
        exc,
      )
    return ProjectFields()

  def _create_default_rule(self) -> List[str]:
    """Return a minimal in-memory rule list used when the DB is unavailable."""
    return [_DEFAULT_RULE]
