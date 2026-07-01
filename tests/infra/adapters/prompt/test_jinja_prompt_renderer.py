import unittest
from unittest.mock import patch, MagicMock

from src.infra.adapters.prompt import JinjaPromptRenderer
from src.domain.models import (
  PromptScope,
  PromptRenderError,
  UnknownPromptScopeError,
)


def _mock_template(content: str) -> MagicMock:
  """Build a mock template path whose read_text returns a plain string."""
  mock_path = MagicMock()
  mock_path.read_text.return_value = content
  return mock_path


class TestJinjaPromptRenderer(unittest.TestCase):

  def setUp(self):
    self.renderer = JinjaPromptRenderer()

  def test_render_template_renders_attributes(self):
    result = self.renderer.render_template(
      "Hello {{ name }}", {"name": "Guardian"}
    )
    self.assertEqual(result, "Hello Guardian")

  def test_render_scope_resolves_scope_template(self):
    template = _mock_template(
      "Checklist:\n{{ checklist }}\n\nCode:\n{{ code }}"
    )
    with patch(
      "src.infra.adapters.prompt.jinja_prompt_renderer.SCOPE_TEMPLATES",
      {PromptScope.CHECKLIST: template},
    ):
      result = self.renderer.render_scope(
        PromptScope.CHECKLIST,
        {"checklist": "rule A", "code": "x = 1"},
      )
    self.assertIn("rule A", result)
    self.assertIn("x = 1", result)
    template.read_text.assert_called_once_with(encoding="utf-8")

  def test_render_scope_architecture(self):
    template = _mock_template(
      "Architecture:\n{{ architecture }}\n\nCode:\n{{ code }}"
    )
    with patch(
      "src.infra.adapters.prompt.jinja_prompt_renderer.SCOPE_TEMPLATES",
      {PromptScope.ARCHITECTURE: template},
    ):
      result = self.renderer.render_scope(
        PromptScope.ARCHITECTURE,
        {"architecture": "hexagonal layers", "code": "x = 1"},
      )
    self.assertIn("hexagonal layers", result)
    self.assertIn("x = 1", result)
    template.read_text.assert_called_once_with(encoding="utf-8")

  def test_render_scope_business_rules(self):
    template = _mock_template(
      "Business rules:\n{{ business_rules }}\n\nCode:\n{{ code }}"
    )
    with patch(
      "src.infra.adapters.prompt.jinja_prompt_renderer.SCOPE_TEMPLATES",
      {PromptScope.BUSINESS_RULES: template},
    ):
      result = self.renderer.render_scope(
        PromptScope.BUSINESS_RULES,
        {"business_rules": "no negative balance", "code": "x = 1"},
      )
    self.assertIn("no negative balance", result)
    self.assertIn("x = 1", result)
    template.read_text.assert_called_once_with(encoding="utf-8")

  def test_invalid_template_raises_prompt_render_error(self):
    with self.assertRaises(PromptRenderError):
      self.renderer.render_template("{{ unclosed", {})

  def test_scope_without_template_raises_named_error(self):
    with patch(
      "src.infra.adapters.prompt.jinja_prompt_renderer.SCOPE_TEMPLATES",
      {},
    ):
      with self.assertRaises(UnknownPromptScopeError):
        self.renderer.render_scope(PromptScope.CHECKLIST, {})


if __name__ == "__main__":
  unittest.main()
