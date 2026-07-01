from abc import ABC, abstractmethod

from src.domain.models import ProjectContext


class RulesRepository(ABC):
  """
  Puerto para repositorio de reglas del proyecto.

  Define contrato para recuperar contexto de proyectos desde base de datos.
  """

  @abstractmethod
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
      ProjectContextNotFoundError: Si no hay contexto para el proyecto.
      MissingViewError: Si view_project_rules no existe.
    """
    ...
