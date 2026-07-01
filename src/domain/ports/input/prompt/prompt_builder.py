from abc import ABC, abstractmethod
from typing import Dict

from src.domain.models import PromptScope, JsonValue

PromptAttributes = Dict[str, JsonValue]


class PromptBuilder(ABC):
  """Input port (use case) for building agent prompts.

  Builds prompts either from a known PromptScope template or from a
  raw template string, sanitizing string attributes beforehand.
  """

  @abstractmethod
  def build_for_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str:
    """Build a prompt from the template associated with a scope.

    Args:
      scope: A valid PromptScope member.
      attributes: Attribute mapping injected into the template.

    Returns:
      The rendered prompt string.

    Raises:
      UnknownPromptScopeError: If scope is not a PromptScope member.
      PromptRenderError: If the template cannot be rendered.
    """
    ...

  @abstractmethod
  def build_from_template(
    self, template: str, attributes: PromptAttributes
  ) -> str:
    """Build a prompt from a raw template string.

    Args:
      template: A Jinja2 template string.
      attributes: Attribute mapping injected into the template.

    Returns:
      The rendered prompt string.

    Raises:
      PromptRenderError: If the template cannot be rendered.
    """
    ...

  @abstractmethod
  def sanitize(self, content: str) -> str:
    """Sanitize a string removing control characters and blank lines.

    Args:
      content: Raw string content.

    Returns:
      The sanitized string.
    """
    ...
