from src.domain.models import AgenticError


class RulesRepositoryError(AgenticError):
  """Error base para repositorio de reglas."""
  pass


class InvalidScopeError(RulesRepositoryError):
  """Error cuando scope no es válido."""
  pass

class ProjectContextNotFoundError(RulesRepositoryError):
  """Error cuando no hay contexto para el proyecto."""
  pass
