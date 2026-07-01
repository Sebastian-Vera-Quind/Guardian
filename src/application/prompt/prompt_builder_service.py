import logging

from src.domain.models import PromptScope, UnknownPromptScopeError
from src.domain.ports.input import PromptBuilder
from src.domain.ports.input.prompt import PromptAttributes
from src.domain.ports.output import PromptRenderer
from src.application.security.prompt_guard import sanitize_file_content
from src.application.loader.sanitizer import CodeSanitizer

logger = logging.getLogger(__name__)


class PromptBuilderService(PromptBuilder):
  """Builds agent prompts by sanitizing string attributes and
  delegating rendering to a PromptRenderer output port.

  This service contains no template-engine logic; all rendering is
  delegated to the injected PromptRenderer.
  """

  def __init__(self, renderer: PromptRenderer) -> None:
    self._renderer = renderer

  def sanitize(self, content: str) -> str:
    without_control = sanitize_file_content(content)
    return CodeSanitizer.remove_blank_lines(without_control)

  def _sanitize_attributes(
    self, attributes: PromptAttributes
  ) -> PromptAttributes:
    sanitized: PromptAttributes = {}
    for key, value in attributes.items():
      if isinstance(value, str):
        sanitized[key] = self.sanitize(value)
      else:
        sanitized[key] = value
    return sanitized

  def build_for_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str:
    if not isinstance(scope, PromptScope):
      logger.warning("Unknown prompt scope received: %s", scope)
      raise UnknownPromptScopeError(f"Unknown prompt scope: {scope}")
    logger.debug("Building prompt for scope: %s", scope.value)
    sanitized = self._sanitize_attributes(attributes)
    return self._renderer.render_scope(scope, sanitized)

  def build_from_template(
    self, template: str, attributes: PromptAttributes
  ) -> str:
    logger.debug("Building prompt from raw template")
    sanitized = self._sanitize_attributes(attributes)
    return self._renderer.render_template(template, sanitized)
