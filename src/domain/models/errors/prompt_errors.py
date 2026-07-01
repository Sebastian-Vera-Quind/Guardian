from src.domain.models import AgenticError


class PromptBuilderError(AgenticError):
  """Error base de construcción de prompts."""
  pass


class UnknownPromptScopeError(PromptBuilderError):
  """Scope no reconocido por PromptScope."""
  pass


class PromptRenderError(PromptBuilderError):
  """Fallo al renderizar la plantilla Jinja2."""
  pass
