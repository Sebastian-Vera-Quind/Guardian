from abc import ABC, abstractmethod
from typing import Dict

from src.domain.models import PromptScope, JsonValue

PromptAttributes = Dict[str, JsonValue]


class PromptRenderer(ABC):
  """Output port for rendering prompt templates.

  Implemented by an infrastructure adapter that resolves scope
  templates and renders them with a template engine.
  """

  @abstractmethod
  def render_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str:
    """Resolve the template for a scope and render it.

    Args:
      scope: A valid PromptScope member.
      attributes: Attribute mapping injected into the template.

    Returns:
      The rendered prompt string.

    Raises:
      PromptRenderError: If the template cannot be rendered.
    """
    ...

  @abstractmethod
  def render_template(
    self, template: str, attributes: PromptAttributes
  ) -> str:
    """Render a raw template string with the given attributes.

    Args:
      template: A template string.
      attributes: Attribute mapping injected into the template.

    Returns:
      The rendered prompt string.

    Raises:
      PromptRenderError: If the template cannot be rendered.
    """
    ...
