from src.domain.models import AgenticError


class ClonePathError(AgenticError):
  """Error general durante ejecución del nodo clone_path."""
  pass


class CheckoutError(ClonePathError):
  """Error durante checkout a commit específico."""
  pass


class DiffGenerationError(ClonePathError):
  """Error durante generación de diff."""
  pass


class GitOperationError(ClonePathError):
  """Error en operación git genérica."""
  pass
