from abc import ABC, abstractmethod

from src.domain.models import ProjectFields


class ProjectFieldsRepository(ABC):
  """Output port for retrieving project configuration fields."""

  @abstractmethod
  def get_project_fields(
    self, project_code: str
  ) -> ProjectFields:
    """Retrieve quality_gates, constraints, nfr_definition and
    fitness_functions for the given project.

    Args:
      project_code: Unique project identifier.

    Returns:
      ProjectFields instance (never raises — fail-open with None fields).
    """
    ...
