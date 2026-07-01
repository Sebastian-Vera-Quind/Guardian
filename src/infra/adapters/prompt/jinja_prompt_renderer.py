import logging

import jinja2

from src.domain.models import (
  PromptScope,
  PromptRenderError,
  UnknownPromptScopeError,
)
from src.domain.ports.output import PromptRenderer
from src.domain.ports.output.prompt import PromptAttributes
from .templates import SCOPE_TEMPLATES

logger = logging.getLogger(__name__)


class JinjaPromptRenderer(PromptRenderer):
  """Renders prompt templates using Jinja2.

  Resolves scope templates from SCOPE_TEMPLATES (a mapping of scope to
  the template file path), reads the template file and renders it.
  Jinja2 errors and file read errors are wrapped in PromptRenderError so
  that the underlying exception never leaks to application/domain.
  """

  def __init__(self) -> None:
    self._env = jinja2.Environment(autoescape=False)

  def render_template(
    self, template: str, attributes: PromptAttributes
  ) -> str:
    try:
      compiled = self._env.from_string(template)
      return compiled.render(**attributes)
    except jinja2.TemplateError as error:
      logger.error("Failed to render Jinja2 template: %s", error)
      raise PromptRenderError(
        f"Failed to render prompt template: {error}"
      ) from error

  def render_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str:
    template_path = SCOPE_TEMPLATES.get(scope)
    if template_path is None:
      logger.warning("No template registered for scope: %s", scope)
      raise UnknownPromptScopeError(
        f"No template registered for scope: {scope}"
      )
    try:
      template = template_path.read_text(encoding="utf-8")
    except OSError as error:
      logger.error(
        "Failed to read prompt template file %s: %s", template_path, error
      )
      raise PromptRenderError(
        f"Failed to read prompt template for scope {scope}: {error}"
      ) from error
    return self.render_template(template, attributes)
