from src.domain.models import AgenticError


class APIKeyMissingError(AgenticError):
  pass


class APIKeyInvalidError(AgenticError):
  pass


class WorkflowValidationError(AgenticError):
  pass


class WorkflowExecutionError(AgenticError):
  pass
